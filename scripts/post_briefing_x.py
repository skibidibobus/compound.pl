"""
compound.pl — Automatyczna publikacja dziennego briefingu na platformie X (scripts/post_briefing_x.py)

Skrypt buduje zwięzły, merytoryczny briefing rynkowy mieszczący się w limicie 280 znaków X
na podstawie aktualnego pliku data.json i publikuje go przez oficjalne X API v2 (OAuth 1.0a).

Wymagane zmienne środowiskowe (GitHub Secrets):
  - X_API_KEY
  - X_API_SECRET
  - X_ACCESS_TOKEN
  - X_ACCESS_TOKEN_SECRET

Uruchomienie testowe (bez publikacji):
  python3 scripts/post_briefing_x.py --dry-run
"""

import os
import sys
import json
import time
import hmac
import base64
import hashlib
import secrets
import datetime
import urllib.parse
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
PORTAL_URL = "https://skibidibobus.github.io/compound.pl/"
X_TWEET_ENDPOINT = "https://api.x.com/2/tweets"


def build_briefing_text(data: dict, max_len: int = 280) -> str:
    """Buduje profesjonalny, zwięzły wpis dzienny dopasowany do limitu 280 znaków na X."""
    today = datetime.datetime.now().strftime("%d.%m.%Y")
    ticker = data.get("market_ticker", [])

    # Wybrane kluczowe notowania
    wanted = ("USD/PLN", "EUR/PLN", "WIG20", "BTC/USD")
    rates = []
    for sym in wanted:
        match = next((t for t in ticker if t.get("symbol") == sym), None)
        if match:
            short_sym = sym.replace("/PLN", "").replace("/USD", "")
            rates.append(f"{short_sym} {match['price']} ({match['change']})")
    rates_line = " | ".join(rates[:3])

    # Wybór 2-3 najważniejszych depesz (preferencja HIGH impact)
    articles = []
    for cat in ("rynki", "makro", "tech", "swiat"):
        articles.extend(data.get(cat, []))
    high_impact = [a for a in articles if a.get("market_impact") == "HIGH"]
    selected = high_impact if len(high_impact) >= 2 else articles

    header = f"Briefing rynkowy {today}\n{rates_line}\n\n"
    footer = f"\n{PORTAL_URL}"

    # Na X każdy link URL liczy się jako 23 znaki (skracacz t.co)
    x_effective_overhead = len(header) + 23 + 1
    body_lines = []
    for art in selected[:3]:
        title = (art.get("title") or "").strip()
        if not title:
            continue
        if len(title) > 54:
            title = title[:51].rstrip() + "..."
        candidate_lines = body_lines + [f"- {title}"]
        effective_len = x_effective_overhead + len("\n".join(candidate_lines))
        if effective_len <= max_len:
            body_lines = candidate_lines
        else:
            break

    if not body_lines and selected:
        avail = max_len - x_effective_overhead - 5
        if avail > 20:
            t = (selected[0].get("title") or "")[:avail].rstrip() + "..."
            body_lines.append(f"- {t}")

    return (header + "\n".join(body_lines) + footer).strip()


def _pct_encode(val: str) -> str:
    return urllib.parse.quote(str(val), safe="~")


def _build_oauth1_header(
    method: str,
    url: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_secret: str,
) -> str:
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }

    sorted_params = sorted((_pct_encode(k), _pct_encode(v)) for k, v in oauth_params.items())
    param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
    base_str = f"{method.upper()}&{_pct_encode(url)}&{_pct_encode(param_str)}"
    signing_key = f"{_pct_encode(api_secret)}&{_pct_encode(access_secret)}"

    digest = hmac.new(
        signing_key.encode("utf-8"),
        base_str.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    oauth_params["oauth_signature"] = base64.b64encode(digest).decode("utf-8")

    header_parts = [f'{_pct_encode(k)}="{_pct_encode(v)}"' for k, v in sorted(oauth_params.items())]
    return "OAuth " + ", ".join(header_parts)


def post_to_x(text: str) -> dict:
    api_key = os.getenv("X_API_KEY", "").strip()
    api_secret = os.getenv("X_API_SECRET", "").strip()
    access_token = os.getenv("X_ACCESS_TOKEN", "").strip()
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET", "").strip()

    if not all([api_key, api_secret, access_token, access_secret]):
        raise RuntimeError(
            "Brak kompletu kluczy X API (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)."
        )

    auth_header = _build_oauth1_header(
        "POST",
        X_TWEET_ENDPOINT,
        api_key,
        api_secret,
        access_token,
        access_secret,
    )

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        X_TWEET_ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "User-Agent": "compound.pl-bot/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    dry_run = "--dry-run" in sys.argv
    if not os.path.exists(DATA_FILE):
        print(f"Błąd: brak pliku {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = build_briefing_text(data)
    print(f"--- Podgląd wpisu ({len(text)}/280 znaków) ---")
    print(text)
    print("------------------------------------------")

    if dry_run:
        print("Tryb --dry-run: wpis nie został wysłany.")
        return

    try:
        res = post_to_x(text)
        print("Opublikowano pomyślnie na X:", json.dumps(res, ensure_ascii=False))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"Błąd HTTP X API ({e.code}): {err_body}")
        sys.exit(1)
    except Exception as e:
        print(f"Błąd publikacji na X: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
