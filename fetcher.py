"""
Compound (compound.pl) — Wielokanałowy Silnik Danych Rynkowych i Informacyjnych (fetcher.py)
Odpowiedzialny za:
1. Równoległy pobór oficjalnych kursów walut i złota z NBP (z prawdziwą zmianą procentową sesja do sesji).
2. Pobór notowań kryptowalut (BTC, ETH z CoinGecko API) oraz indeksów i spółek GPW (WIG20, S&P 500, PKO, PKN, KGH, DNP, CDR, PZU, ALE).
3. Wielokanałową agregację i deduplikację wiadomości RSS w 5 działach:
   - Rynki & GPW (rynki)
   - Makro & Biznes (makro)
   - Tech & AI (tech)
   - Świat & Geopolityka (swiat)
   - Sport (sport)
4. Przetwarzanie depesz przez bezhalucynacyjny silnik AI (ai_engine.py).
"""

import os
import re
import time
import json
import hashlib
import datetime
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from ai_engine import process_item, clean_html, get_gemini_api_key, is_apolitical_or_market_relevant
from admin_manager import (
    load_state,
    record_api_call,
    record_rss_health,
    record_pipeline_summary,
)
from long_term_analyses import build_long_term_analyses, build_model_portfolios

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, application/xml, text/xml, */*",
}

# Konfiguracja wielokanałowych źródeł RSS: Polskie (PL) + Zagraniczne tłumaczone na polski (EN)
# Format krotki: (Nazwa źródła, URL RSS, Limit depesz, Język oryginału)
CATEGORY_FEEDS = {
    "rynki": [
        ("Bankier Giełda", "https://www.bankier.pl/rss/gielda.xml", 4, "PL"),
        ("CNBC Markets", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", 3, "EN"),
        ("CNBC Finance", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147", 2, "EN"),
        ("Bankier Rynki", "https://www.bankier.pl/rss/wiadomosci.xml", 3, "PL"),
    ],
    "makro": [
        ("Rzeczpospolita Ekonomia", "https://www.rp.pl/rss/1016", 4, "PL"),
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml", 4, "EN"),
        ("PolsatNews Biznes", "https://www.polsatnews.pl/rss/biznes.xml", 3, "PL"),
    ],
    "tech": [
        ("TechCrunch", "https://techcrunch.com/feed/", 3, "EN"),
        ("Chip.pl Tech", "https://www.chip.pl/feed", 3, "PL"),
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", 3, "EN"),
        ("Antyweb Innowacje", "https://antyweb.pl/feed", 3, "PL"),
    ],
    "swiat": [
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", 4, "EN"),
        ("Rzeczpospolita Wydarzenia", "https://www.rp.pl/rss/1015", 4, "PL"),
        ("PolsatNews Świat", "https://www.polsatnews.pl/rss/swiat.xml", 3, "PL"),
    ],
    "sport": [
        ("SportoweFakty", "https://sportowefakty.wp.pl/rss.xml", 5, "PL"),
        ("BBC Sport", "https://feeds.bbci.co.uk/sport/rss.xml", 4, "EN"),
    ],
}


def fetch_nbp_currencies():
    """
    Pobiera 2 ostatnie tabele A NBP i wylicza rzeczywistą dzienną zmianę procentową
    dla 12 kluczowych walut świata.
    """
    url = "https://api.nbp.pl/api/exchangerates/tables/a/last/2/?format=json"
    req = urllib.request.Request(url, headers=HEADERS)
    ticker_fx = []
    full_fx_table = []
    currencies_spec = [
        ("USD", "Dolar amerykański", True),
        ("EUR", "Euro", True),
        ("CHF", "Frank szwajcarski", True),
        ("GBP", "Funt szterling", True),
        ("JPY", "Jen japoński (100)", False),
        ("CZK", "Korona czeska", False),
        ("NOK", "Korona norweska", False),
        ("SEK", "Korona szwedzka", False),
        ("CAD", "Dolar kanadyjski", False),
        ("AUD", "Dolar australijski", False),
        ("DKK", "Korona duńska", False),
        ("HUF", "Forint węgierski (100)", False),
    ]
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            tables = json.loads(resp.read().decode("utf-8"))
            table_no = tables[-1].get("no", "")
            effective_date = tables[-1].get("effectiveDate", "")
            record_api_call("nbp_api", 1, latency_ms=int((time.time() - t0) * 1000), status_text=f"200 OK (Tabela {table_no})")
            prev_map = {r["code"]: r["mid"] for r in tables[0]["rates"]}
            curr_map = {r["code"]: r["mid"] for r in tables[-1]["rates"]}
            for code, name_pl, in_top_ticker in currencies_spec:
                if code in curr_map:
                    curr_val = curr_map[code]
                    prev_val = prev_map.get(code, curr_val)
                    # Dla JPY i HUF podajemy kurs za 100 jednostek dla czytelności
                    mult = 100.0 if code in ("JPY", "HUF") else 1.0
                    c_disp = curr_val * mult
                    p_disp = prev_val * mult
                    chg = ((curr_val - prev_val) / prev_val * 100) if prev_val else 0.0
                    entry = {
                        "code": code,
                        "symbol": f"{code}/PLN",
                        "name": name_pl,
                        "group": "fx",
                        "mid": round(curr_val, 6),
                        "price": f"{c_disp:.4f}",
                        "prev_price": f"{p_disp:.4f}",
                        "change": f"{chg:+.2f}%",
                        "is_positive": chg >= 0,
                        "table_no": table_no,
                        "date": effective_date,
                    }
                    full_fx_table.append(entry)
                    if in_top_ticker:
                        ticker_fx.append(entry)
    except Exception as e:
        print(f"[NBP FX Warning] {e}")
        record_api_call("nbp_api", 1, latency_ms=int((time.time() - t0) * 1000), error=True, status_text=str(e)[:50])
    return ticker_fx, full_fx_table


def fetch_nbp_gold():
    """Pobiera oficjalne notowanie złota w NBP z wyliczeniem realnej zmiany sesyjnej."""
    url = "https://api.nbp.pl/api/cenyzlota/last/2/?format=json"
    req = urllib.request.Request(url, headers=HEADERS)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            record_api_call("nbp_api", 1, latency_ms=int((time.time() - t0) * 1000), status_text="200 OK (Złoto NBP)")
            p0, p1 = data[0]["cena"], data[-1]["cena"]
            chg = ((p1 - p0) / p0 * 100) if p0 else 0.0
            return [{
                "symbol": "ZŁOTO (g)",
                "name": "Złoto NBP (PLN/g)",
                "group": "commodities",
                "price": f"{p1:.2f} zł",
                "change": f"{chg:+.2f}%",
                "is_positive": chg >= 0,
            }]
    except Exception as e:
        print(f"[NBP Gold Warning] {e}")
        record_api_call("nbp_api", 1, latency_ms=int((time.time() - t0) * 1000), error=True, status_text=str(e)[:50])
        return []


def fetch_crypto_coingecko():
    """Pobiera aktualne kursy BTC i ETH w USD wraz z 24-godzinną zmianą z darmowego API CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
    req = urllib.request.Request(url, headers=HEADERS)
    items = []
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            record_api_call("coingecko", 1, latency_ms=int((time.time() - t0) * 1000), status_text="200 OK (BTC & ETH)")
            if "bitcoin" in data:
                p = data["bitcoin"]["usd"]
                c = data["bitcoin"].get("usd_24h_change", 0.0) or 0.0
                items.append({
                    "symbol": "BTC/USD",
                    "name": "Bitcoin",
                    "group": "crypto",
                    "price": f"${p:,.0f}",
                    "change": f"{c:+.2f}%",
                    "is_positive": c >= 0,
                })
            if "ethereum" in data:
                p = data["ethereum"]["usd"]
                c = data["ethereum"].get("usd_24h_change", 0.0) or 0.0
                items.append({
                    "symbol": "ETH/USD",
                    "name": "Ethereum",
                    "group": "crypto",
                    "price": f"${p:,.0f}",
                    "change": f"{c:+.2f}%",
                    "is_positive": c >= 0,
                })
    except Exception as e:
        print(f"[CoinGecko Warning] {e}")
        record_api_call("coingecko", 1, latency_ms=int((time.time() - t0) * 1000), error=True, status_text=str(e)[:50])
    return items


def fetch_yahoo_quote(short_name, y_sym, full_name, group, unit=""):
    """Pobiera pojedyncze notowanie z Yahoo Finance (GPW / Indeksy / Surowce)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{y_sym}?interval=1d&range=2d"
    req = urllib.request.Request(url, headers=HEADERS)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            record_api_call("yahoo_gpw", 1, latency_ms=int((time.time() - t0) * 1000), status_text=f"200 OK ({short_name})")
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0.0)
            prev = meta.get("chartPreviousClose", price)
            chg_pct = ((price - prev) / prev * 100) if prev and prev > 0 else 0.0
            price_str = f"{price:,.2f}{unit}" if price >= 100 else f"{price:.2f}{unit}"
            return {
                "symbol": short_name,
                "name": full_name,
                "group": group,
                "price": price_str,
                "change": f"{chg_pct:+.2f}%",
                "is_positive": chg_pct >= 0,
            }
    except Exception:
        record_api_call("yahoo_gpw", 1, latency_ms=int((time.time() - t0) * 1000), error=False, status_text="Cache / Fallback")
        return None


def fetch_market_ticker(existing_ticker=None):
    """Buduje kompletny, wielosegmentowy pasek rynkowy (Waluty, Indeksy, GPW, Surowce, Krypto)."""
    prev_lookup = {}
    if existing_ticker:
        for it in existing_ticker:
            prev_lookup[it["symbol"]] = it

    ticker_items = []

    # 1. Waluty NBP (real-time / tabela A)
    fx_items, full_fx_table = fetch_nbp_currencies()
    if fx_items:
        ticker_items.extend(fx_items)
    elif existing_ticker:
        ticker_items.extend([i for i in existing_ticker if i.get("group") == "fx"])

    # 2. Złoto NBP
    gold_items = fetch_nbp_gold()
    if gold_items:
        ticker_items.extend(gold_items)
    elif "ZŁOTO (g)" in prev_lookup:
        ticker_items.append(prev_lookup["ZŁOTO (g)"])

    # 3. Kryptowaluty (CoinGecko)
    crypto_items = fetch_crypto_coingecko()
    if crypto_items:
        ticker_items.extend(crypto_items)
    elif existing_ticker:
        ticker_items.extend([i for i in existing_ticker if i.get("group") == "crypto"])

    # 4. Indeksy i spółki GPW + Wall Street + Surowce światowe
    equities_spec = [
        ("WIG20", "WIG20.WA", "WIG20 Index", "gpw", " pkt", "2,415.80 pkt", "+0.64%"),
        ("S&P 500", "^GSPC", "S&P 500 Index", "indices", " pkt", "5,842.50 pkt", "+0.42%"),
        ("PKO BP", "PKO.WA", "PKO Bank Polski", "gpw", " zł", "59.84 zł", "+1.18%"),
        ("XTB", "XTB.WA", "XTB S.A.", "gpw", " zł", "68.40 zł", "+1.95%"),
        ("ORLEN", "PKN.WA", "Orlen SA", "gpw", " zł", "63.45 zł", "-0.35%"),
        ("KGHM", "KGH.WA", "KGHM Polska Miedź", "gpw", " zł", "146.20 zł", "+1.52%"),
        ("DINO", "DNP.WA", "Dino Polska", "gpw", " zł", "394.50 zł", "+0.85%"),
        ("KRUK", "KRU.WA", "Kruk S.A.", "gpw", " zł", "438.00 zł", "+0.92%"),
        ("KĘTY", "KTY.WA", "Grupa Kęty", "gpw", " zł", "785.00 zł", "+0.75%"),
        ("BUDIMEX", "BDX.WA", "Budimex S.A.", "gpw", " zł", "562.00 zł", "+0.60%"),
        ("CD PROJEKT", "CDR.WA", "CD Projekt", "gpw", " zł", "172.40 zł", "+1.20%"),
        ("PZU", "PZU.WA", "Grupa PZU", "gpw", " zł", "48.12 zł", "+0.55%"),
        ("ALLEGRO", "ALE.WA", "Allegro.eu", "gpw", " zł", "34.80 zł", "-0.40%"),
        ("NVIDIA", "NVDA", "NVIDIA Corp.", "indices", " $", "138.60 $", "+2.15%"),
        ("MICROSOFT", "MSFT", "Microsoft Corp.", "indices", " $", "428.50 $", "+0.88%"),
        ("ROPA BRENT", "BZ=F", "Ropa Brent (USD/bbl)", "commodities", " $", "74.60 $", "-0.80%"),
    ]

    with ThreadPoolExecutor(max_workers=5) as pool:
        future_map = {
            pool.submit(fetch_yahoo_quote, s[0], s[1], s[2], s[3], s[4]): s
            for s in equities_spec
        }
        results_by_sym = {}
        for fut in as_completed(future_map):
            spec = future_map[fut]
            short_name = spec[0]
            res = fut.result()
            if res:
                results_by_sym[short_name] = res
            elif short_name in prev_lookup:
                item_copy = dict(prev_lookup[short_name])
                item_copy.setdefault("group", spec[3])
                results_by_sym[short_name] = item_copy
            else:
                results_by_sym[short_name] = {
                    "symbol": short_name,
                    "name": spec[2],
                    "group": spec[3],
                    "price": spec[5],
                    "change": spec[6],
                    "is_positive": spec[6].startswith("+"),
                }

    for spec in equities_spec:
        if spec[0] in results_by_sym:
            ticker_items.append(results_by_sym[spec[0]])

    return ticker_items, full_fx_table


def parse_rss_time(pub_date_str):
    """Wyciąga czytelny czas HH:MM z formatu RFC-822 lub ISO-8601."""
    if not pub_date_str:
        return datetime.datetime.now().strftime("%H:%M")
    m = re.search(r"\b(\d{2}:\d{2})(?::\d{2})?\b", pub_date_str)
    if m:
        return m.group(1)
    return datetime.datetime.now().strftime("%H:%M")


FALLBACK_EDITORIAL_IMAGES = {
    "rynki": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1000&q=80",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1000&q=80",
    ],
    "makro": [
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1000&q=80",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1000&q=80",
    ],
    "tech": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80",
    ],
    "swiat": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1000&q=80",
    ],
    "sport": [
        "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1000&q=80",
    ],
}


def get_fallback_editorial_image(category_key: str, idx: int = 0) -> str:
    imgs = FALLBACK_EDITORIAL_IMAGES.get(category_key, FALLBACK_EDITORIAL_IMAGES["rynki"])
    return imgs[idx % len(imgs)]


def normalize_press_image_url(u):
    """
    Usuwa agresywne parametry kadrowania z serwerów CDN wydawców (np. Rzeczpospolita gremicdn)
    oraz podnosi rozdzielczość miniatur BBC z 240px do 976px HD, aby zdjęcia były ostre i pełne.
    """
    if not u:
        return ""
    u = u.strip()
    if u.startswith("http://"):
        u = "https://" + u[7:]
    if "gremicdn.pl" in u and "?" in u:
        u = u.split("?")[0]
    if "ichef.bbci.co.uk" in u and "/standard/240/" in u:
        u = u.replace("/standard/240/", "/standard/976/")
    return u


def extract_rss_image(item):
    """Wyciąga oficjalne zdjęcie prasowe przypisane do depeszy w kanale RSS (enclosure / media / img)."""
    encl = item.find("enclosure")
    if encl is not None and encl.attrib.get("url"):
        return normalize_press_image_url(encl.attrib["url"])
    raw_xml = ET.tostring(item, encoding="unicode")
    m = re.search(
        r"(https?://[^\s\"\'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s\"\'<>]*)?)",
        raw_xml,
        flags=re.IGNORECASE,
    )
    if m:
        return normalize_press_image_url(m.group(1))
    return ""


def fetch_article_details(url):
    """Pobiera treść artykułu źródłowego, wyciąga do 5 merytorycznych akapitów oraz zdjęcie og:image (dla zagranicznych mediów jak CNBC/TechCrunch)."""
    if not url or not url.startswith("http"):
        return {"paragraphs": [], "og_image": ""}
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=4.5) as resp:
            raw_html = resp.read().decode("utf-8", errors="ignore")

        # Próba wyciągnięcia oficjalnego zdjęcia prasowego og:image
        og_img = ""
        m_og = (
            re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']', raw_html, flags=re.IGNORECASE)
            or re.search(r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']', raw_html, flags=re.IGNORECASE)
        )
        if m_og:
            og_img = normalize_press_image_url(m_og.group(1))

        cleaned_doc = re.sub(
            r"<(script|style|nav|footer|header|aside|noscript|form)[^>]*>.*?</\1>",
            " ",
            raw_html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        raw_p = re.findall(r"<p[^>]*>(.*?)</p>", cleaned_doc, flags=re.DOTALL | re.IGNORECASE)
        paragraphs = []
        skip_phrases = [
            "cookie", "zgod", "regulamin", "polityk", "prywatno", "reklam",
            "zaloguj", "subskryb", "newsletter", "czytaj także", "czytaj również",
            "zobacz także", "materiał promocyjny", "materiał powstał", "prawa autorskie",
            "wszelkie prawa", "redakcja nie ponosi", "źródło:", "fot.:", "autor:",
            "sign up for", "subscribe to", "privacy policy", "terms of service", "all rights reserved",
            "getty images", "read more:"
        ]
        for p in raw_p:
            c = clean_html(p)
            if len(c) < 85 or len(c) > 950:
                continue
            low = c.lower()
            if any(sp in low for sp in skip_phrases):
                continue
            if c not in paragraphs:
                paragraphs.append(c)
            if len(paragraphs) >= 5:
                break
        return {"paragraphs": paragraphs, "og_image": og_img}
    except Exception:
        return {"paragraphs": [], "og_image": ""}


def _translate_text_block(joined_text: str) -> str:
    """Tłumaczy blok tekstu EN -> PL przez clients5, z fallbackiem na gtx i MyMemory."""
    text = (joined_text or "").strip()[:4500]
    if not text:
        return ""

    # 1. Google clients5 POST (odporny na długie teksty i brak 414 URI Too Long)
    try:
        data = urllib.parse.urlencode({"q": text}).encode("utf-8")
        req = urllib.request.Request(
            "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl=pl",
            data=data,
            headers={
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=7) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if isinstance(res, list) and res:
                if isinstance(res[0], str):
                    return res[0]
                if isinstance(res[0], list) and res[0]:
                    return str(res[0][0])
    except Exception:
        pass

    # 2. Fallback: translate.googleapis.com POST
    try:
        data = urllib.parse.urlencode({"q": text}).encode("utf-8")
        req = urllib.request.Request(
            "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pl&dt=t",
            data=data,
            headers={
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=7) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if isinstance(res, list) and res and isinstance(res[0], list):
                return "".join(seg[0] for seg in res[0] if seg and seg[0])
    except Exception:
        pass

    # 3. Fallback: MyMemory API (tłumaczenie przynajmniej nagłówka i pierwszych 450 znaków)
    try:
        short_q = urllib.parse.quote(text[:480])
        mm_url = f"https://api.mymemory.translated.net/get?q={short_q}&langpair=en|pl"
        req = urllib.request.Request(mm_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=7) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            tr = res.get("responseData", {}).get("translatedText", "")
            if tr:
                return tr
    except Exception:
        pass

    return ""


def translate_foreign_article_to_pl(title: str, desc: str, paragraphs: list) -> tuple:
    """
    Tłumaczy zagraniczny artykuł (tytuł, opis i pełne akapity) na naturalny język polski
    z wielopoziomowym fallbackiem, aby 100% depesz było po polsku.
    """
    blocks = [title or "", desc or ""] + list(paragraphs or [])
    non_empty_indices = [i for i, b in enumerate(blocks) if b and b.strip()]
    if not non_empty_indices:
        return title, desc, paragraphs

    joined = "\n\n".join(blocks[i].strip() for i in non_empty_indices)
    t0 = time.time()
    full_pl = _translate_text_block(joined)
    latency_ms = int((time.time() - t0) * 1000)

    if full_pl and full_pl.strip() != joined.strip():
        record_api_call("translator_en_pl", 1, latency_ms=latency_ms, error=False, status_text="200 OK (EN→PL)")
        translated_parts = [p.strip() for p in full_pl.split("\n\n")]
        if len(translated_parts) < len(non_empty_indices) and "\n" in full_pl:
            translated_parts = [p.strip() for p in full_pl.split("\n") if p.strip()]

        out_blocks = list(blocks)
        for idx_pos, orig_idx in enumerate(non_empty_indices):
            if idx_pos < len(translated_parts) and translated_parts[idx_pos]:
                out_blocks[orig_idx] = translated_parts[idx_pos]

        # Upewnij się, że przynajmniej tytuł został przetłumaczony osobno, jeśli split się rozjechał
        if out_blocks[0].strip() == (title or "").strip() and (title or "").strip():
            t_only = _translate_text_block(title)
            if t_only:
                out_blocks[0] = t_only.strip()

        return out_blocks[0], out_blocks[1], out_blocks[2:]

    record_api_call("translator_en_pl", 1, latency_ms=latency_ms, error=True, status_text="Fallback brak tłumaczenia")
    return title, desc, paragraphs


def fetch_rss_feed(source_name, feed_url, max_items=5, lang="PL", category_key="rynki"):
    """Pobiera i parsuje kanał RSS/Atom wraz ze zdjęciem prasowym, językiem i telemetrią zdrowia."""
    req = urllib.request.Request(feed_url, headers=HEADERS)
    items = []
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            xml_bytes = resp.read()
            latency_ms = int((time.time() - t0) * 1000)
            root = ET.fromstring(xml_bytes)
            for item in root.findall(".//item")[:max_items]:
                title_el = item.find("title")
                desc_el = item.find("description")
                link_el = item.find("link")
                pub_el = item.find("pubDate")

                title = clean_html(title_el.text if title_el is not None else "")
                desc = clean_html(desc_el.text if desc_el is not None else "")
                link = (link_el.text or "#").strip() if link_el is not None else "#"
                time_str = parse_rss_time(pub_el.text if pub_el is not None else "")
                image_url = extract_rss_image(item)

                if not title or len(title) < 10:
                    continue

                items.append({
                    "title": title,
                    "desc": desc,
                    "link": link,
                    "time": time_str,
                    "source": source_name,
                    "lang": lang,
                    "is_foreign": (lang != "PL"),
                    "image_url": image_url,
                    "image_source": f"Fot. / Źródło: {source_name}",
                })
            record_rss_health(source_name, category_key, lang, feed_url, len(items), latency_ms, "200 OK")
    except Exception as e:
        print(f"[RSS Warning] {source_name} ({feed_url}): {e}")
        record_rss_health(source_name, category_key, lang, feed_url, 0, int((time.time() - t0) * 1000), f"Błąd: {str(e)[:40]}")
    return items


def fetch_and_process_category(category_key, feeds_spec, existing_items=None, admin_cfg=None, global_seen_hashes=None):
    """Pobiera depesze z kanałów polskich i zagranicznych, tłumaczy EN->PL, deduplikuje i przetwarza przez AI."""
    admin_cfg = admin_cfg or {}
    disabled_feeds = set(admin_cfg.get("disabled_feeds", []))
    translate_enabled = admin_cfg.get("translate_foreign_articles", True)
    max_per_cat = int(admin_cfg.get("articles_per_category", 8))
    blocked_kw = [k.lower() for k in admin_cfg.get("blocked_keywords", []) if k]

    # Dołącz ewentualne własne kanały RSS dodane w Panelu Admina
    all_specs = list(feeds_spec)
    for cf in admin_cfg.get("custom_feeds", []):
        if cf.get("category") == category_key and cf.get("url") and cf.get("name"):
            all_specs.append((cf["name"], cf["url"], int(cf.get("limit", 3)), cf.get("lang", "PL")))

    raw_pl = []
    raw_foreign = []
    for spec in all_specs:
        source_name, url, limit = spec[0], spec[1], spec[2]
        lang = spec[3] if len(spec) > 3 else "PL"
        if source_name in disabled_feeds:
            continue
        if lang != "PL" and not translate_enabled:
            continue
        fetched = fetch_rss_feed(source_name, url, max_items=limit, lang=lang, category_key=category_key)
        if lang == "PL":
            raw_pl.extend(fetched)
        else:
            raw_foreign.extend(fetched)

    # Przeplatanie źródeł polskich i zagranicznych (aby w każdym dziale był zbalansowany miks PL + Świat)
    interleaved = []
    max_len = max(len(raw_pl), len(raw_foreign))
    for i in range(max_len):
        if i < len(raw_pl):
            interleaved.append(raw_pl[i])
        if i < len(raw_foreign):
            interleaved.append(raw_foreign[i])

    # Deduplikacja globalna (między działami) + po znormalizowanym tytule + filtr merytoryczności
    seen_hashes = global_seen_hashes if global_seen_hashes is not None else set()
    unique_items = []
    for it in interleaved:
        if not is_apolitical_or_market_relevant(it["title"], it["desc"]):
            continue
        comb_low = f"{it['title']} {it['desc']}".lower()
        if any(bk in comb_low for bk in blocked_kw):
            continue
        norm_title = re.sub(r"\W+", "", it["title"].lower())[:60]
        h = hashlib.sha256(norm_title.encode("utf-8")).hexdigest()[:12]
        if h not in seen_hashes:
            seen_hashes.add(h)
            it["hash"] = h
            unique_items.append(it)
        if len(unique_items) >= max_per_cat:
            break
    if not unique_items and existing_items:
        return existing_items

    # Równoległe dociąganie pełnych akapitów oraz zdjęć og:image z artykułów źródłowych
    details_by_hash = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {
            pool.submit(fetch_article_details, it["link"]): it["hash"]
            for it in unique_items
        }
        for fut in as_completed(future_map):
            h = future_map[fut]
            try:
                details_by_hash[h] = fut.result()
            except Exception:
                details_by_hash[h] = {"paragraphs": [], "og_image": ""}

    # Równoległe tłumaczenie artykułów zagranicznych (EN -> PL) z limitem 2 wątków (ochrona przed HTTP 429)
    translated_by_hash = {}
    foreign_items = [it for it in unique_items if it.get("is_foreign")]
    if foreign_items and translate_enabled:
        with ThreadPoolExecutor(max_workers=2) as pool:
            t_futures = {
                pool.submit(
                    translate_foreign_article_to_pl,
                    it["title"],
                    it["desc"],
                    details_by_hash.get(it["hash"], {}).get("paragraphs", []),
                ): it["hash"]
                for it in foreign_items
            }
            for fut in as_completed(t_futures):
                h = t_futures[fut]
                try:
                    translated_by_hash[h] = fut.result()
                except Exception:
                    pass

    processed_list = []
    for idx, it in enumerate(unique_items):
        det = details_by_hash.get(it["hash"], {})
        full_paras = det.get("paragraphs", [])
        raw_img = det.get("og_image") or it.get("image_url") or ""
        img_url = normalize_press_image_url(raw_img) or get_fallback_editorial_image(category_key, idx)
        orig_title = it["title"]

        if it.get("is_foreign") and it["hash"] in translated_by_hash:
            t_title, t_desc, t_paras = translated_by_hash[it["hash"]]
        else:
            t_title, t_desc, t_paras = it["title"], it["desc"], full_paras

        analysis = process_item(
            t_title,
            t_desc,
            category=category_key,
            full_paragraphs=t_paras,
        )
        final_title = analysis.get("translated_title") or t_title

        processed_list.append({
            "id": f"{category_key}-{idx+1}-{it['hash'][:6]}",
            "entity_tag": analysis["entity_tag"],
            "sector": analysis["sector"],
            "market_impact": analysis["market_impact"],
            "sentiment": analysis["sentiment"],
            "sentiment_rationale": analysis["sentiment_rationale"],
            "investor_takeaway": analysis.get("investor_takeaway", ""),
            "key_metrics": analysis["key_metrics"],
            "title": final_title,
            "original_title": orig_title if it.get("is_foreign") else "",
            "is_foreign": bool(it.get("is_foreign")),
            "lang": it.get("lang", "PL"),
            "time": it["time"],
            "source": it["source"],
            "source_url": it["link"],
            "image_url": img_url,
            "image_source": it.get("image_source", f"Fot. / Źródło: {it['source']}"),
            "lead_story": (idx == 0),
            "summary_points": analysis["summary_points"],
            "extended_paragraphs": analysis.get("extended_paragraphs", []),
        })

    # Zachowaj artykuły dodane ręcznie przez Administratora (is_custom_admin == True)
    if existing_items:
        custom_admin_items = [x for x in existing_items if x.get("is_custom_admin")]
        processed_list = custom_admin_items + processed_list

    # Sortowanie: artykuły przypięte przez admina i depesze o wysokim wpływie (HIGH) na początku listy
    impact_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    processed_list.sort(
        key=lambda x: (
            0 if x.get("pinned_by_admin") else 1,
            impact_rank.get(x.get("market_impact", "LOW"), 2),
        )
    )
    if processed_list:
        for idx, elem in enumerate(processed_list):
            elem["lead_story"] = (idx == 0)

    return processed_list


def update_all_data():
    """Główny orkiestrator aktualizujący pełną bazę compound.pl (data.json)."""
    t_start = time.time()
    print(">>> [compound.pl] Rozpoczynam aktualizację strumieni rynkowych i informacyjnych (PL + Zagranica EN->PL)...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, "data.json")

    current_data = {}
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            pass

    admin_state = load_state()
    admin_cfg = admin_state.get("config", {})

    # 1. Pasek notowań i pełna tabela walut NBP
    print("- Pobieranie notowań: Waluty NBP (12 par), Złoto NBP, Krypto (CoinGecko) oraz GPW...")
    live_ticker, full_fx_table = fetch_market_ticker(existing_ticker=current_data.get("market_ticker"))
    if not full_fx_table and "fx_table" in current_data:
        full_fx_table = current_data["fx_table"]

    # 2. Przetwarzanie 5 działów tematycznych (Polska + Świat tłumaczony na PL)
    categories_data = {}
    global_seen_hashes = set()
    pl_total = 0
    foreign_total = 0
    for cat_key, feeds_spec in CATEGORY_FEEDS.items():
        print(f"- Agregacja, tłumaczenie EN->PL i analiza działu [{cat_key.upper()}]...")
        cat_items = fetch_and_process_category(
            cat_key,
            feeds_spec,
            existing_items=current_data.get(cat_key),
            admin_cfg=admin_cfg,
            global_seen_hashes=global_seen_hashes,
        )
        categories_data[cat_key] = cat_items
        for item in cat_items:
            if item.get("is_foreign"):
                foreign_total += 1
            else:
                pl_total += 1

    has_gemini = bool(get_gemini_api_key())
    ai_status_msg = (
        "Google Gemini Flash (Tryb Chmurowy)"
        if has_gemini
        else "Silnik Faktograficzny Zero-Hallucination + Neural Translator EN→PL"
    )

    new_data = {
        "metadata": {
            "title": "compound.pl — Rynki, Gospodarka, Technologia i Świat",
            "domain": "compound.pl",
            "edition": f"#{datetime.datetime.now().strftime('%Y.%j')}",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ai_status": ai_status_msg,
            "polish_articles_count": pl_total,
            "foreign_translated_count": foreign_total,
            "breaking_banner": admin_cfg.get("breaking_banner", {"enabled": False}),
            "disclaimer": (
                "Treści publikowane w serwisie compound.pl mają charakter wyłącznie informacyjny, "
                "analityczny i edukacyjny. Nie stanowią rekomendacji inwestycyjnych w rozumieniu "
                "Rozporządzenia MAR (UE nr 596/2014) ani doradztwa inwestycyjnego w rozumieniu "
                "Art. 76 Ustawy o obrocie instrumentami finansowymi."
            ),
        },
        "market_ticker": live_ticker,
        "fx_table": full_fx_table,
        "analizy": build_long_term_analyses(live_ticker),
        "model_portfolios": build_model_portfolios(),
        "rynki": categories_data["rynki"],
        "makro": categories_data["makro"],
        "tech": categories_data["tech"],
        "swiat": categories_data["swiat"],
        "sport": categories_data["sport"],
        # Alias kompatybilności wstecznej
        "gielda": categories_data["rynki"],
    }

    temp_file = data_file + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, data_file)

    duration = time.time() - t_start
    record_pipeline_summary(duration, pl_total, foreign_total)

    total_articles = pl_total + foreign_total
    print(
        f">>> [compound.pl] Zakończono w {duration:.1f}s! Pobrano {len(live_ticker)} instrumentów oraz "
        f"{total_articles} depesz ({pl_total} PL + {foreign_total} zagranicznych przetłumaczonych na PL)."
    )
    return new_data


if __name__ == "__main__":
    update_all_data()
