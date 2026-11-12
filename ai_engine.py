"""
Compound (compound.pl) — Instytucjonalny Moduł Analityki AI (ai_engine.py)
Architektura: Zero-Hallucination Financial & News Intelligence
Odpowiedzialny za:
1. Analizę depesz w oparciu o rygorystyczny System Prompt (standard Bloomberg / FT).
2. Ekstrakcję wyłącznie prawdziwych danych liczbowych z tekstu (key_metrics) — zero zmyślania wskaźników.
3. Rozpoznawanie podmiotu/sektora (entity_tag, sector) oraz siły wpływu na rynek (market_impact: HIGH / MEDIUM / LOW).
4. Obsługę Google Gemini API (gemini-2.5-flash / gemini-2.0-flash) z zaawansowanym silnikiem lokalnym jako fallback.
"""

import os
import re
import html
import json
import urllib.request
import urllib.error

# Mapowanie znanych podmiotów i pojęć rynkowych (do precyzyjnego tagowania bez zgadywania)
ENTITY_LEXICON = [
    # Spółki GPW
    (["pko bp", "pko bank", "pkobp"], "PKO BP (GPW: PKO)", "Bankowość"),
    (["orlen", "pkn orlen"], "Orlen (GPW: PKN)", "Energetyka & Paliwa"),
    (["kghm", "polska miedź"], "KGHM (GPW: KGH)", "Surowce & Górnictwo"),
    (["dino", "dino polska"], "Dino Polska (GPW: DNP)", "Handel Detaliczny"),
    (["cd projekt", "cdprojekt", "wiedźmin", "cyberpunk"], "CD Projekt (GPW: CDR)", "Gaming & Tech"),
    (["pzu", "powszechny zakład"], "PZU (GPW: PZU)", "Ubezpieczenia"),
    (["allegro"], "Allegro (GPW: ALE)", "E-commerce"),
    (["pekao", "bank pekao"], "Bank Pekao (GPW: PEO)", "Bankowość"),
    (["santander"], "Santander BP (GPW: SPL)", "Bankowość"),
    (["mbank"], "mBank (GPW: MBK)", "Bankowość"),
    (["ing bank", "ing bsk"], "ING BSK (GPW: ING)", "Bankowość"),
    (["alior"], "Alior Bank (GPW: ALR)", "Bankowość"),
    (["lpp", "reserved", "sinsay"], "LPP (GPW: LPP)", "Odzież & Retail"),
    (["pge", "polska grupa energetyczna"], "PGE (GPW: PGE)", "Energetyka"),
    (["tauron"], "Tauron (GPW: TPE)", "Energetyka"),
    (["enea"], "Enea (GPW: ENA)", "Energetyka"),
    (["jsw", "jastrzębska spółka"], "JSW (GPW: JSW)", "Górnictwo"),
    (["kruk"], "Kruk (GPW: KRU)", "Wierzytelności"),
    (["xtb", "x-trade"], "XTB (GPW: XTB)", "Fintech & Brokerzy"),
    (["budimex"], "Budimex (GPW: BDX)", "Budownictwo"),
    (["asbis"], "Asbis (GPW: ASB)", "Dystrybucja IT"),
    (["asseco"], "Asseco Poland (GPW: ACP)", "IT & Software"),
    (["cyfrowy polsat", "polsat"], "Cyfrowy Polsat (GPW: CPS)", "Telekomunikacja & Media"),
    (["orange polska", "orange"], "Orange Polska (GPW: OPL)", "Telekomunikacja"),
    (["inpost", "paczkomat"], "InPost (EUR: INPST)", "Logistyka & E-commerce"),
    (["żabka", "zabka"], "Grupa Żabka (GPW: ZAB)", "Handel Detaliczny"),
    (["ccc", "halfprice", "modivo"], "Grupa CCC (GPW: CCC)", "Handel & E-commerce"),
    (["kety", "grupa kęty"], "Grupa Kęty (GPW: KTY)", "Przemysł"),
    (["pepco"], "Pepco Group (GPW: PCO)", "Handel Detaliczny"),
    # Instytucje i Makro
    (["nbp", "rpp", "rada polityki pieniężnej", "glapiński", "stopy procentowe", "stopa referencyjna"], "NBP / RPP", "Polityka Pieniężna"),
    (["gus", "inflacj", "cpi", "pkb", "bezroboci", "wynagrodze"], "GUS / Makro Polska", "Makroekonomia"),
    (["kpo", "fundusze europejskie", "komisja europejska", "unia europejska"], "Unia Europejska", "Gospodarka & Regulacje"),
    (["fed", "rezerwa federalna", "powell", "fomc"], "Fed (USA)", "Banki Centralne"),
    (["ebc", "europejski bank centralny", "lagarde"], "EBC (Strefa Euro)", "Banki Centralne"),
    (["knf", "komisja nadzoru finansowego"], "KNF", "Nadzór Finansowy"),
    (["gpw", "wig20", "mwig40", "swig80", "giełd", "warszawski parkiet"], "GPW w Warszawie", "Rynek Kapitałowy"),
    (["obligacj", "skarbow", "dług publiczny", "ministerstwo finansów"], "Rynek Długu / MF", "Obligacje & Budżet"),
    (["nieruchomośc", "mieszkan", "kredyt hipoteczn", "deweloper"], "Rynek Nieruchomości", "Nieruchomości"),
    # Surowce i Krypto
    (["złoto", "złota", "gold", "uncj"], "Złoto (XAU/USD)", "Surowce Szlachetne"),
    (["ropa", "ropy", "brent", "wti", "opec"], "Ropa Naftowa", "Surowce Energetyczne"),
    (["miedź", "miedzi", "copper"], "Miedź (LME)", "Surowce Przemysłowe"),
    (["bitcoin", "btc", "kryptowalut", "ethereum", "eth"], "Rynek Krypto", "Aktywa Cyfrowe"),
    # Global Tech
    (["nvidia", "układy gpu", "blackwell"], "NVIDIA (NASDAQ: NVDA)", "Półprzewodniki & AI"),
    (["openai", "chatgpt", "gpt-", "anthropic", "claude", "gemini", "sztuczna inteligencja", "model ai"], "Sektor AI", "Sztuczna Inteligencja"),
    (["apple", "iphone", "macbook"], "Apple (NASDAQ: AAPL)", "Big Tech"),
    (["microsoft", "azure"], "Microsoft (NASDAQ: MSFT)", "Chmura & AI"),
    (["google", "alphabet"], "Alphabet (NASDAQ: GOOGL)", "Big Tech"),
    (["meta", "zuckerberg"], "Meta Platforms (NASDAQ: META)", "Big Tech"),
    (["tesla", "musk", "spacex"], "Tesla / SpaceX", "Motoryzacja & Tech"),
    (["tsmc", "intel", "amd", "procesor", "chip", "broadcom"], "Półprzewodniki", "Hardware & Chipy"),
    (["amazon", "aws", "bezos"], "Amazon (NASDAQ: AMZN)", "E-commerce & Chmura"),
    (["palantir"], "Palantir (NYSE: PLTR)", "AI & Obronność"),
    (["goldman sachs", "jpmorgan", "morgan stanley", "blackrock", "wall street", "s&p 500", "nasdaq", "dow jones"], "Wall Street (USA)", "Rynki Globalne"),
    (["mfw", "imf", "międzynarodowy fundusz walutowy", "bank światowy"], "MFW / Bank Światowy", "Makroekonomia Globalna"),
    (["nato", "pentagon", "biały dom", "waszyngton", "kongres usa"], "USA & Bezpieczeństwo", "Geopolityka"),
    (["chiny", "pekin", "azja", "japonia", "tokio"], "Azja & Pacyfik", "Gospodarka Światowa"),
    (["premier league", "liga mistrzów", "champions league", "uefa", "fifa", "la liga", "bundesliga"], "Piłka Nożna", "Sport Międzynarodowy"),
    (["formuła 1", "f1", "verstappen", "ferrari", "mclaren", "red bull racing"], "Formuła 1", "Motorsport"),
    (["nba", "nhl", "atp", "wta", "iga świątek", "świątek", "lewandowski"], "Sport Światowy", "Wydarzenia Sportowe"),
]


def get_gemini_api_key():
    """Pobiera klucz API Gemini ze zmiennych środowiskowych lub pliku .env."""
    key = os.getenv("GEMINI_API_KEY")
    if key and key.strip() and key.strip() != "twoj_klucz_tutaj":
        return key.strip()

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and val != "twoj_klucz_tutaj":
                            return val
        except Exception:
            pass
    return None


def clean_html(raw_html):
    """Usuwa znaczniki HTML, skrypty, encje i nadmiarowe białe znaki."""
    if not raw_html:
        return ""
    clean = re.sub(r"<(script|style).*?>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<.*?>", " ", clean)
    clean = html.unescape(clean)
    return " ".join(clean.split())


# Słowa kluczowe czysto ideologiczne/aktywistyczne do odfiltrowania, aby portal pozostał
# merytoryczny, apolityczny i zorientowany na gospodarkę, własność prywatną i twarde dane.
IDEOLOGICAL_NOISE_PATTERNS = [
    "aktywiści klimatyczni przykleili",
    "ostatnie pokolenie zablokowało",
    "mowa nienawiści",
    "zaimki",
    "ideologia gender",
]


def is_apolitical_or_market_relevant(title, text):
    """
    Sprawdza, czy depesza trzyma standard merytoryczny i wolnorynkowy (bez lewicowego aktywizmu
    i tabloidowych wojenek partyjnych).
    """
    combined = f"{title} {text}".lower()
    for noise in IDEOLOGICAL_NOISE_PATTERNS:
        if noise in combined:
            return False
    return True


def detect_entity_and_sector(title, text, category="rynki"):
    """Rozpoznaje podmiot i sektor wyłącznie na podstawie rzeczywistej treści depeszy (najpierw tytuł, z granicami słów)."""
    title_low = (title or "").lower()
    text_low = (text or "").lower()

    def _matches(kw, haystack):
        # Krótkie słowa kluczowe i skrótowce wymagają dokładnych granic słów (\b),
        # aby np. "fed" nie pasowało do "offered", a "enea" do "athenean".
        if len(kw) <= 5 or kw.isalpha():
            return bool(re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", haystack))
        return kw in haystack

    # W dziale sport nie tagujemy drużyn nazwami spółek GPW (np. Orlen, Enea, Tauron jako sponsorzy)
    if category != "sport":
        for haystack in (title_low, text_low):
            for keywords, entity_tag, sector in ENTITY_LEXICON:
                for kw in keywords:
                    if _matches(kw, haystack):
                        return entity_tag, sector
    else:
        for haystack in (title_low, text_low):
            for keywords, entity_tag, sector in ENTITY_LEXICON:
                if "Sport" in sector or "Piłka" in entity_tag or "Formuła" in entity_tag:
                    for kw in keywords:
                        if _matches(kw, haystack):
                            return entity_tag, sector

    # Domyślne, prawdziwe etykiety kategorii (nigdy nie przypisujemy fałszywego tickera!)
    defaults = {
        "rynki": ("Rynek Kapitałowy", "Giełda & Inwestycje"),
        "makro": ("Gospodarka & Makro", "Makroekonomia"),
        "tech": ("Technologia & Innowacje", "Sektor Tech"),
        "swiat": ("Wydarzenia Globalne", "Geopolityka & Świat"),
        "sport": ("Sport & Biznes", "Wydarzenia Sportowe"),
    }
    return defaults.get(category, ("Puls Rynku", "Informacje"))


def extract_real_metrics(title, text):
    """
    Wyciąga wyłącznie prawdziwe dane liczbowe obecne w tekście (Zero-Hallucination).
    Szuka wartości procentowych, kwot w mln/mld zł/USD/EUR, punktów bazowych itp.
    """
    combined = f"{title}. {text}"
    metrics = []

    patterns = [
        # np. "2,4 mld zł", "150 mln USD", "6,3 miliarda dolarów", "450 tys. zł"
        r"\b\d+(?:[.,]\d+)?\s*(?:mld|mln|tys\.|miliard(?:a|ów|y)?|milion(?:a|ów|y)?)\s*(?:zł|PLN|USD|EUR|GBP|dolar(?:ów|a|y)?|euro|funt(?:ów|a|y)?)?\b",
        # np. "+14,2% r/r", "12,5 proc.", "-3.4%"
        r"[+-]?\b\d+(?:[.,]\d+)?\s*(?:%|proc\.)(?:\s*r/r|\s*k/k|\s*m/m)?",
        # np. "5,75 pkt proc.", "25 pb"
        r"\b\d+(?:[.,]\d+)?\s*(?:pkt\s*proc\.|pb|pkt)\b",
    ]

    seen = set()
    for pat in patterns:
        for match in re.finditer(pat, combined, flags=re.IGNORECASE):
            val = " ".join(match.group(0).split())
            # Normalizacja do deduplikacji (np. "+14,5% r/r" == "14,5 proc. r/r")
            val_norm = re.sub(r"\s+", "", val.lower().replace("proc.", "%").lstrip("+-"))
            if val_norm not in seen and len(val) <= 28:
                seen.add(val_norm)
                metrics.append(val)
                if len(metrics) >= 3:
                    return metrics
    return metrics


def evaluate_impact_and_sentiment(title, text, category="rynki"):
    """Ocenia wpływ na rynek (HIGH/MEDIUM/LOW) oraz sentyment na bazie słów kluczowych."""
    full_str = f"{title} {text}".lower()

    high_impact_triggers = [
        "wyniki", "zysk netto", "dywidend", "stopy procentowe", "rpp", "nbp",
        "fed", "ebc", "inflacj", "pkb", "przejęci", "fuzj", "rekord", "krach",
        "espi", "wezwanie", "kontrakt", "mld", "iliard", "cła", "sankcj", "pilne"
    ]
    medium_impact_triggers = [
        "prognoz", "analityc", "wzrost", "spadek", "inwestycj", "raport",
        "giełd", "kurs", "notowani", "przychod", "marż", "strategi"
    ]

    high_hits = sum(1 for w in high_impact_triggers if w in full_str)
    med_hits = sum(1 for w in medium_impact_triggers if w in full_str)

    if high_hits >= 1:
        market_impact = "HIGH"
    elif med_hits >= 1:
        market_impact = "MEDIUM"
    else:
        market_impact = "LOW"

    positive_words = [
        "wzrost", "zysk", "rekord", "sukces", "awans", "przewyższ", "wyżej",
        "zwycięstw", "dywidend", "popraw", "umocni", "hossa", "odbici", "zielon",
        "kontrakt", "przełom", "rośnie", "wzrosły", "optymizm"
    ]
    negative_words = [
        "spadek", "strata", "korekta", "załamanie", "niżej", "porażk", "kryzys",
        "redukcj", "obniż", "spadły", "bessa", "inflacja wzrosła", "ostrzeżenie",
        "ryzyk", "słabsz", "tracą", "traci", "sankcj", "konflikt", "podwyżk"
    ]

    pos_score = sum(full_str.count(w) for w in positive_words)
    neg_score = sum(full_str.count(w) for w in negative_words)

    if pos_score > neg_score and pos_score > 0:
        sentiment = "positive"
        rationale = "Przewaga czynników wzrostowych i pozytywnych danych w komunikacie."
    elif neg_score > pos_score and neg_score > 0:
        sentiment = "negative"
        rationale = "Czynniki ryzyka, presja podażowa lub słabsze odczyty w komunikacie."
    else:
        sentiment = "neutral"
        rationale = "Informacja o charakterze równoważnym lub sprawozdawczym."

    return market_impact, sentiment, rationale


def build_investor_takeaway(entity_tag, sector, sentiment, market_impact, category, key_metrics):
    """
    Generuje konkretny wniosek praktyczny ('Co to oznacza dla Twojego portfela / inwestora?'),
    który odróżnia compound.pl od zwykłych portali informacyjnych.
    """
    metrics_str = f" (kluczowe liczby: {', '.join(key_metrics)})" if key_metrics else ""
    if "Bankowość" in sector or "Polityka Pieniężna" in sector or "Banki Centralne" in sector:
        if sentiment == "positive":
            return f"Wpływ na kapitał: Korzystne otoczenie dla sektora bankowego i wyceny PLN{metrics_str}; stabilizuje oczekiwania dotyczące kosztu pieniądza."
        elif sentiment == "negative":
            return f"Wpływ na kapitał: Sygnał ostrożności dla ekspozycji na sektor finansowy i stopy procentowe{metrics_str}."
        return f"Wpływ na kapitał: Czynnik równowagi dla kosztu kredytu, rentowności obligacji skarbowych oraz wyceny {entity_tag}{metrics_str}."

    if category == "rynki":
        if sentiment == "positive":
            return f"Znaczenie dla portfela: Pozytywny impuls fundamentalny dla {entity_tag} ({sector}){metrics_str} — wspiera sentyment popytowy w sektorze."
        elif sentiment == "negative":
            return f"Znaczenie dla portfela: Czynnik ryzyka podażowego wokół {entity_tag} ({sector}){metrics_str} — wymaga obserwacji marż i wsparć cenowych."
        return f"Znaczenie dla portfela: Informacja sprawozdawcza dla obserwujących {entity_tag} ({sector}){metrics_str} bez bezpośredniego szoku wycenowego."

    if category == "makro":
        if sentiment == "positive":
            return f"Dla przedsiębiorców i oszczędzających: Pozytywny sygnał z obszaru „{sector}”{metrics_str} wspierający aktywność gospodarczą i siłę nabywczą."
        elif sentiment == "negative":
            return f"Dla przedsiębiorców i oszczędzających: Rosnąca presja regulacyjna lub kosztowa w obszarze „{sector}”{metrics_str} — istotne dla ochrony realnej wartości kapitału."
        return f"Dla przedsiębiorców i oszczędzających: Istotny punkt odniesienia w segmencie „{sector}” ({entity_tag}){metrics_str} przy planowaniu budżetu i inwestycji."

    if category == "tech":
        return f"Perspektywa Tech & AI: Wydarzenie wokół {entity_tag} ({sector}){metrics_str} kształtuje przewagi konkurencyjne oraz alokację kapitału w spółki technologiczne."

    if category == "swiat":
        return f"Kontekst geopolityczny: Czynnik z kategorii „{sector}” ({entity_tag}){metrics_str} wpływający na globalny apetyt na ryzyko (Risk-On / Risk-Off), surowce i łańcuchy dostaw."

    return f"Kontekst rynkowy ({sector}): Kluczowa informacja z obszaru {entity_tag}{metrics_str} o wpływie sklasyfikowanym jako {market_impact}."


def local_heuristic_summary(title, text, category="rynki", full_paragraphs=None):
    """
    Zaawansowany analizator lokalny (Zero-Hallucination, działa w <5 ms, 0 kosztów).
    Nie wymyśla fałszywych C/Z ani RSI — wyciąga wyłącznie fakty z tekstu oraz buduje
    pełne rozwinięcie (extended_paragraphs) do czytnika wewnątrz portalu.
    """
    title_clean = clean_html(title)
    text_clean = clean_html(text)
    extra_paras = [clean_html(p) for p in (full_paragraphs or []) if clean_html(p)]
    combined_corpus = text_clean + " " + " ".join(extra_paras)

    entity_tag, sector = detect_entity_and_sector(title_clean, combined_corpus, category)
    key_metrics = extract_real_metrics(title_clean, combined_corpus)
    market_impact, sentiment, rationale = evaluate_impact_and_sentiment(title_clean, combined_corpus, category)
    investor_takeaway = build_investor_takeaway(entity_tag, sector, sentiment, market_impact, category, key_metrics)

    # Podział opisu na zdania z ochroną polskich skrótów (proc., tys., tzw., m.in., r., kw., np., ok.)
    protected = re.sub(
        r"\b(proc|tys|mln|mld|ok|np|tzn|tzw|tj|pkt|kw|r|godz|min|ust|art|poz|fot|red|dr|prof|gen|płk|dyr|ws|dot|nt|ul|al)\.",
        r"\1<DOT>",
        combined_corpus.replace("m.in.", "m<DOT>in<DOT>"),
        flags=re.IGNORECASE,
    )
    raw_sentences = [
        s.replace("<DOT>", ".").strip()
        for s in re.split(r"(?<=[.!?])\s+", protected)
        if len(s.strip()) > 25
    ]

    points = []
    seen_s = set()
    for s in raw_sentences:
        if any(skip in s.lower() for skip in ["czytaj więcej", "zobacz także", "kliknij tutaj", "reklama", "preferowane źródło"]):
            continue
        if not s.endswith((".", "!", "?")):
            s += "."
        s_key = s[:50].lower()
        if s_key not in seen_s:
            seen_s.add(s_key)
            points.append(s)
        if len(points) == 3:
            break

    if len(points) == 0:
        points.append(f"Główny temat depeszy: {title_clean}.")
    if len(points) == 1:
        points.append(f"Obszar tematyczny: {sector} ({entity_tag}).")
    if len(points) == 2:
        if key_metrics:
            points.append(f"Kluczowe wartości wskazane w publikacji: {', '.join(key_metrics)}.")
        else:
            points.append(f"Wydarzenie sklasyfikowano w sektorze: {sector} (wpływ: {market_impact}).")

    # Budowa rozszerzonego opracowania (extended_paragraphs) wyświetlanego po kliknięciu w kartę
    extended_paragraphs = []
    seen_p = set()
    if text_clean and len(text_clean) > 40:
        seen_p.add(text_clean[:50].lower())
        extended_paragraphs.append(text_clean)

    for p in extra_paras:
        p_key = p[:50].lower()
        if p_key not in seen_p and len(p) > 55:
            seen_p.add(p_key)
            extended_paragraphs.append(p)
            if len(extended_paragraphs) >= 5:
                break

    if len(extended_paragraphs) < 2:
        extended_paragraphs.append(
            f"Kontekst sektorowy ({sector} — {entity_tag}): {rationale}"
            + (f" Kluczowe wskaźniki i liczby przytoczone w depeszy to: {', '.join(key_metrics)}." if key_metrics else "")
        )

    return {
        "entity_tag": entity_tag,
        "sector": sector,
        "market_impact": market_impact,
        "sentiment": sentiment,
        "sentiment_rationale": rationale,
        "investor_takeaway": investor_takeaway,
        "key_metrics": key_metrics,
        "summary_points": points[:3],
        "extended_paragraphs": extended_paragraphs[:5],
        "is_ai_powered": False,
    }


def summarize_with_gemini(title, text, category, api_key, full_paragraphs=None):
    """
    Instytucjonalna synteza za pomocą Google Gemini API (gemini-2.5-flash / gemini-2.0-flash).
    Rygor Zero-Hallucination oraz pełna zgodność z wymogami MAR / KNF.
    """
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    title_clean = clean_html(title)
    extra_text = "\n\n".join(clean_html(p) for p in (full_paragraphs or []) if clean_html(p))
    text_clean = (clean_html(text) + "\n\n" + extra_text).strip()[:4000]

    prompt = f"""Jesteś Głównym Analitykiem Rynkowym portalu informacyjnego "compound.pl" (standard Wall Street Journal / Rzeczpospolita / Financial Times).
Przeanalizuj poniższą depeszę z działu "{category}".

TYTUŁ: {title_clean}
TREŚĆ: {text_clean}

BEZWZGLĘDNE ZASADY (COMPLIANCE, LINIA REDAKCYJNA & ZERO-HALLUCINATION):
1. ZAKAZ HALUCYNACJI: W polu "key_metrics" umieść WYŁĄCZNIE liczby, procenty lub kwoty, które FIZYCZNIE występują w powyższym tekście (maksymalnie 3 najważniejsze, np. ["Zysk: 2,4 mld zł", "+12,4% r/r"]). Jeśli w tekście nie ma żadnych liczb, zwróć pustą tablicę []. Nigdy nie zgaduj wskaźników C/Z ani RSI.
2. LINIA REDAKCYJNA (APOLITYCZNY REALIZM & WOLNY RYNEK): Tekst ma być ściśle apolityczny, chłodny i oparty na faktach. Jeśli temat dotyczy polityki gospodarczej, regulacji lub państwa, prezentuj go z perspektywy wolnorynkowo-konserwatywnej (ochrona własności prywatnej, deregulacja, dyscyplina budżetowa, niskie podatki, suwerenność energetyczna i gospodarcza). Całkowicie odrzucaj lewicową publicystykę ideologiczną.
3. ZAKAZ REKOMENDACJI (KNF / MAR): Nigdy nie używaj słów nakazowych ("kupuj", "sprzedawaj", "warto zainwestować"). Pisz w 100% obiektywnym, sprawozdawczym tonie.
4. ZERO CLICKBAITU: Usuń emocjonalne przymiotniki i pytania retoryczne. Przetłumacz na język faktów po polsku.
5. STRUKTURA:
   - "summary_points": 3 zwięzłe punkty widoczne na karcie głównej.
   - "extended_paragraphs": 3 do 4 pełnych, rozbudowanych akapitów (po 3-4 zdania każdy) szczegółowo omawiających wydarzenie, tło operacyjne, dokładne dane i konsekwencje rynkowe, aby czytelnik po kliknięciu w artykuł dowiedział się wszystkiego bez konieczności opuszczania compound.pl.

Zwróć wynik WYŁĄCZNIE jako poprawny obiekt JSON:
{{
  "entity_tag": "Nazwa głównej spółki, instytucji lub rynku (np. 'PKO BP (GPW: PKO)', 'NBP / RPP', 'NVIDIA')",
  "sector": "Krótka nazwa sektora po polsku (np. 'Bankowość', 'Makroekonomia', 'Półprzewodniki & AI')",
  "market_impact": "HIGH" | "MEDIUM" | "LOW",
  "sentiment": "positive" | "neutral" | "negative",
  "sentiment_rationale": "Jedno krótkie zdanie wyjaśniające wydźwięk informacji.",
  "key_metrics": ["liczba/wskaźnik z tekstu 1", "liczba/wskaźnik z tekstu 2"],
  "summary_points": [
    "Punkt 1: Twardy fakt i kluczowe liczby z depeszy.",
    "Punkt 2: Kontekst operacyjny, przyczyna lub decyzja.",
    "Punkt 3: Obiektywne znaczenie dla rynku lub sektora."
  ],
  "extended_paragraphs": [
    "Akapit 1: Szczegółowy opis głównych faktów, danych liczbowych i uczestników wydarzenia.",
    "Akapit 2: Rozwinięcie przyczyn, otoczenia regulacyjnego lub sytuacji w branży.",
    "Akapit 3: Konsekwencje długoterminowe dla gospodarki, rynku kapitałowego lub przedsiębiorców."
  ],
  "translated_title": "Czysty, pozbawiony clickbaitu tytuł po polsku (jeśli oryginał był po polsku i jest merytoryczny, zachowaj go)"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }
    data_bytes = json.dumps(payload).encode("utf-8")

    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
        t0 = __import__("time").time()
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                latency_ms = int((__import__("time").time() - t0) * 1000)
                try:
                    from admin_manager import record_api_call
                    record_api_call("gemini_ai", 1, latency_ms=latency_ms, error=False, status_text=f"200 OK ({model_name})")
                except Exception:
                    pass
                candidate = resp_data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(candidate.strip())

                fallback = local_heuristic_summary(title, text, category, full_paragraphs=full_paragraphs)
                return {
                    "entity_tag": parsed.get("entity_tag") or fallback["entity_tag"],
                    "sector": parsed.get("sector") or fallback["sector"],
                    "market_impact": parsed.get("market_impact") if parsed.get("market_impact") in ("HIGH", "MEDIUM", "LOW") else fallback["market_impact"],
                    "sentiment": parsed.get("sentiment") if parsed.get("sentiment") in ("positive", "neutral", "negative") else fallback["sentiment"],
                    "sentiment_rationale": parsed.get("sentiment_rationale") or fallback["sentiment_rationale"],
                    "investor_takeaway": parsed.get("investor_takeaway") or fallback["investor_takeaway"],
                    "key_metrics": (parsed.get("key_metrics") or [])[:3],
                    "summary_points": (parsed.get("summary_points") or fallback["summary_points"])[:3],
                    "extended_paragraphs": (parsed.get("extended_paragraphs") or fallback["extended_paragraphs"])[:5],
                    "translated_title": parsed.get("translated_title") or title_clean,
                    "is_ai_powered": True,
                }
        except Exception as e:
            print(f"[Gemini API ({model_name}) Warning] {e}")
            try:
                from admin_manager import record_api_call
                record_api_call("gemini_ai", 1, latency_ms=int((__import__("time").time() - t0) * 1000), error=True, status_text=str(e)[:60])
            except Exception:
                pass
            continue

    return local_heuristic_summary(title, text, category, full_paragraphs=full_paragraphs)


def process_item(title, text, category="rynki", full_paragraphs=None):
    """Główny punkt wejściowy do analizy pojedynczej depeszy."""
    api_key = get_gemini_api_key()
    if api_key:
        return summarize_with_gemini(title, text, category, api_key, full_paragraphs=full_paragraphs)
    return local_heuristic_summary(title, text, category, full_paragraphs=full_paragraphs)


if __name__ == "__main__":
    print("Test instytucjonalnego silnika AI compound.pl:")
    sample = process_item(
        "PKO BP miało w III kw. 2,42 mld zł zysku netto, powyżej konsensusu (+14,5% r/r)",
        "Skonsolidowany zysk netto PKO Banku Polskiego w trzecim kwartale wzrósł o 14,5 proc. r/r do 2,42 mld zł. Wynik odsetkowy przekroczył oczekiwania rynkowe, a współczynnik ROE wyniósł 18,2 proc.",
        "rynki",
    )
    print(json.dumps(sample, indent=2, ensure_ascii=False))
