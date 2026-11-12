"""
Compound (compound.pl) — Moduł Zarządzania, Bezpieczeństwa, Telemetrii i Limitów API (admin_manager.py)
Odpowiedzialny za:
1. Bezpieczne uwierzytelnianie administratora (PBKDF2-HMAC-SHA256, tokeny sesyjne 256-bit, ochrona Brute-Force).
2. Śledzenie zużycia limitów API (Gemini AI, Google Translate EN->PL, Yahoo Finance, CoinGecko, NBP) oraz zdrowia kanałów RSS.
3. Statystyki ruchu na stronie (odsłony, unikalni czytelnicy, popularność działów i artykułów).
4. Konfigurację portalu w czasie rzeczywistym (pasek Breaking News, włączanie/wyłączanie źródeł RSS, edycja CMS, limity Cooldown).
"""

import os
import json
import time
import hmac
import hashlib
import secrets
import datetime
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_STATE_FILE = os.path.join(BASE_DIR, "admin_state.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

_state_lock = threading.Lock()

# Domyślne hasło przy pierwszym uruchomieniu (można zmienić w panelu lub przez zmienną COMPOUND_ADMIN_PASSWORD)
DEFAULT_ADMIN_PASSWORD = os.getenv("COMPOUND_ADMIN_PASSWORD", "CompoundAdmin2026!")

# Sesje w pamięci: token -> {"created_at": ts, "expires_at": ts, "ip": str, "user": "admin"}
ACTIVE_SESSIONS = {}

# Ochrona przed atakami Brute-Force: ip -> [timestamps nieudanych prób]
FAILED_LOGINS = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SEC = 600  # 10 minut blokady po 5 błędnych hasłach

# Definicje limitów darmowych warstw API
API_QUOTA_SPECS = {
    "gemini_ai": {
        "name": "Google Gemini AI (Synteza & Analiza)",
        "daily_limit": 1500,
        "rpm_limit": 15,
        "unit": "zapytań / dzień",
        "tier": "Free Tier (1500 RPD)",
    },
    "translator_en_pl": {
        "name": "Tłumacz Neural EN → PL (Zagraniczne Media)",
        "daily_limit": 1000,
        "rpm_limit": 60,
        "unit": "artykułów / dzień",
        "tier": "GTX Neural Endpoint",
    },
    "yahoo_gpw": {
        "name": "Yahoo Finance Chart API (GPW & Indeksy)",
        "daily_limit": 2000,
        "rpm_limit": 60,
        "unit": "zapytań / dzień",
        "tier": "Public Market Feed",
    },
    "coingecko": {
        "name": "CoinGecko API (Bitcoin & Ethereum)",
        "daily_limit": 500,
        "rpm_limit": 30,
        "unit": "zapytań / dzień",
        "tier": "Public Demo Tier",
    },
    "nbp_api": {
        "name": "Narodowy Bank Polski (Tabela A & Złoto)",
        "daily_limit": 2000,
        "rpm_limit": 100,
        "unit": "zapytań / dzień",
        "tier": "Oficjalne API NBP",
    },
}


def _hash_password(password: str, salt: str = None) -> dict:
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return {"salt": salt, "hash": dk.hex(), "algo": "pbkdf2_sha256_120k"}


def verify_password(password: str, auth_record: dict) -> bool:
    if not auth_record or "salt" not in auth_record or "hash" not in auth_record:
        return False
    calc = _hash_password(password, auth_record["salt"])
    return hmac.compare_digest(calc["hash"], auth_record["hash"])


def _today_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _default_state() -> dict:
    today = _today_str()
    return {
        "auth": {
            "username": "admin",
            "password_record": _hash_password(DEFAULT_ADMIN_PASSWORD),
            "password_changed_at": _now_iso(),
        },
        "config": {
            "auto_refresh_cooldown_sec": 540,
            "manual_refresh_cooldown_sec": 20,
            "articles_per_category": 8,
            "translate_foreign_articles": True,
            "disabled_feeds": [],
            "custom_feeds": [],
            "blocked_keywords": [
                "aktywiści klimatyczni przykleili",
                "ostatnie pokolenie zablokowało",
                "mowa nienawiści",
                "zaimki",
                "ideologia gender",
            ],
            "breaking_banner": {
                "enabled": False,
                "label": "PILNE",
                "text": "",
                "link": "",
                "style": "amber",
            },
        },
        "traffic": {
            "date": today,
            "total_page_views": 24,
            "today_page_views": 24,
            "total_data_requests": 42,
            "unique_visitors_today": [],
            "hourly_views": {f"{h:02d}": 0 for h in range(24)},
            "category_views": {
                "rynki": 18,
                "makro": 11,
                "tech": 9,
                "swiat": 7,
                "sport": 5,
                "kursy": 14,
            },
            "article_reads": {},
            "manual_refreshes": 2,
            "auto_refreshes": 1,
            "cached_hits_saved": 6,
        },
        "api_usage": {
            "date": today,
            "counters": {
                "gemini_ai": {"calls_today": 0, "total_calls": 0, "errors": 0, "last_latency_ms": 0, "last_status": "Gotowy (Tryb Lokalny / Chmura)"},
                "translator_en_pl": {"calls_today": 0, "total_calls": 0, "errors": 0, "last_latency_ms": 0, "last_status": "OK"},
                "yahoo_gpw": {"calls_today": 0, "total_calls": 0, "errors": 0, "last_latency_ms": 0, "last_status": "OK"},
                "coingecko": {"calls_today": 0, "total_calls": 0, "errors": 0, "last_latency_ms": 0, "last_status": "OK"},
                "nbp_api": {"calls_today": 0, "total_calls": 0, "errors": 0, "last_latency_ms": 0, "last_status": "OK"},
            },
            "rss_health": {},
            "last_pipeline_duration_sec": 0.0,
            "last_pipeline_run": _now_iso(),
            "foreign_articles_translated_last_run": 0,
            "polish_articles_last_run": 0,
        },
        "audit_log": [
            {
                "time": _now_iso(),
                "event": "SYSTEM_INIT",
                "ip": "127.0.0.1",
                "details": "Zainicjalizowano moduł bezpieczeństwa i telemetrii compound.pl",
            }
        ],
    }


def load_state() -> dict:
    with _state_lock:
        if not os.path.exists(ADMIN_STATE_FILE):
            st = _default_state()
            _save_state_unlocked(st)
            return st
        try:
            with open(ADMIN_STATE_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
        except Exception:
            st = _default_state()

        # Reset dziennych liczników przy zmianie daty
        today = _today_str()
        if st.get("traffic", {}).get("date") != today:
            st.setdefault("traffic", {})["date"] = today
            st["traffic"]["today_page_views"] = 0
            st["traffic"]["unique_visitors_today"] = []
            st["traffic"]["hourly_views"] = {f"{h:02d}": 0 for h in range(24)}

        if st.get("api_usage", {}).get("date") != today:
            st.setdefault("api_usage", {})["date"] = today
            for k in st["api_usage"].get("counters", {}).values():
                k["calls_today"] = 0
            _save_state_unlocked(st)

        return st


def _save_state_unlocked(st: dict):
    tmp = ADMIN_STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ADMIN_STATE_FILE)


def save_state(st: dict):
    with _state_lock:
        _save_state_unlocked(st)


def append_audit_log(event_type: str, ip: str, details: str):
    st = load_state()
    with _state_lock:
        logs = st.setdefault("audit_log", [])
        logs.insert(0, {
            "time": _now_iso(),
            "event": event_type,
            "ip": ip or "127.0.0.1",
            "details": details,
        })
        st["audit_log"] = logs[:100]
        _save_state_unlocked(st)


# ---- Uwierzytelnianie i Ochrona Brute-Force ----

def is_ip_locked_out(ip: str) -> tuple:
    now = time.time()
    attempts = [t for t in FAILED_LOGINS.get(ip, []) if now - t < LOCKOUT_WINDOW_SEC]
    FAILED_LOGINS[ip] = attempts
    if len(attempts) >= MAX_FAILED_ATTEMPTS:
        remaining = int(LOCKOUT_WINDOW_SEC - (now - attempts[0]))
        return True, max(1, remaining)
    return False, 0


def authenticate_admin(password: str, ip: str) -> dict:
    locked, wait_sec = is_ip_locked_out(ip)
    if locked:
        append_audit_log("AUTH_LOCKED", ip, f"Zablokowana próba logowania (blokada jeszcze {wait_sec} s)")
        return {"ok": False, "error": f"Zbyt wiele nieudanych prób. Odczekaj {wait_sec} sekund."}

    st = load_state()
    env_override = os.getenv("COMPOUND_ADMIN_PASSWORD")
    auth_rec = st.get("auth", {}).get("password_record")

    valid = False
    if env_override and hmac.compare_digest(password, env_override):
        valid = True
    elif verify_password(password, auth_rec):
        valid = True

    if not valid:
        FAILED_LOGINS.setdefault(ip, []).append(time.time())
        left = max(0, MAX_FAILED_ATTEMPTS - len(FAILED_LOGINS[ip]))
        append_audit_log("AUTH_FAILED", ip, f"Nieudane logowanie do panelu admina (pozostało prób: {left})")
        return {"ok": False, "error": f"Nieprawidłowe hasło administratora. Pozostało prób: {left}."}

    FAILED_LOGINS.pop(ip, None)
    token = secrets.token_urlsafe(32)
    now = time.time()
    ACTIVE_SESSIONS[token] = {
        "user": "admin",
        "ip": ip,
        "created_at": now,
        "expires_at": now + 86400,  # 24h
    }
    append_audit_log("AUTH_SUCCESS", ip, "Zalogowano pomyślnie do Panelu Administratora")
    return {"ok": True, "token": token, "expires_in": 86400}


def verify_session_token(token: str) -> bool:
    if not token:
        return False
    sess = ACTIVE_SESSIONS.get(token)
    if not sess:
        return False
    if time.time() > sess["expires_at"]:
        ACTIVE_SESSIONS.pop(token, None)
        return False
    return True


def logout_session(token: str, ip: str = "127.0.0.1", all_sessions: bool = False):
    if all_sessions:
        ACTIVE_SESSIONS.clear()
        append_audit_log("AUTH_LOGOUT_ALL", ip, "Wylogowano wszystkie aktywne sesje administratora")
    elif token in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.pop(token, None)
        append_audit_log("AUTH_LOGOUT", ip, "Wylogowano sesję administratora")


def change_admin_password(current_password: str, new_password: str, ip: str = "127.0.0.1") -> dict:
    if not new_password or len(new_password) < 8:
        return {"ok": False, "error": "Nowe hasło musi mieć co najmniej 8 znaków."}
    st = load_state()
    if not verify_password(current_password, st.get("auth", {}).get("password_record")):
        append_audit_log("PASS_CHANGE_FAILED", ip, "Błędne obecne hasło podczas próby zmiany hasła")
        return {"ok": False, "error": "Obecne hasło jest nieprawidłowe."}

    st["auth"]["password_record"] = _hash_password(new_password)
    st["auth"]["password_changed_at"] = _now_iso()
    save_state(st)
    append_audit_log("PASS_CHANGED", ip, "Zmieniono hasło główne administratora (PBKDF2-SHA256)")
    return {"ok": True, "message": "Hasło zostało bezpiecznie zmienione."}


# ---- Telemetria API i Ruchu ----

def record_api_call(service_key: str, count: int = 1, latency_ms: int = 0, error: bool = False, status_text: str = "OK"):
    st = load_state()
    with _state_lock:
        counters = st.setdefault("api_usage", {}).setdefault("counters", {})
        c = counters.setdefault(service_key, {
            "calls_today": 0,
            "total_calls": 0,
            "errors": 0,
            "last_latency_ms": 0,
            "last_status": "OK",
        })
        c["calls_today"] = c.get("calls_today", 0) + count
        c["total_calls"] = c.get("total_calls", 0) + count
        if error:
            c["errors"] = c.get("errors", 0) + 1
        if latency_ms > 0:
            c["last_latency_ms"] = int(latency_ms)
        if status_text:
            c["last_status"] = status_text
        _save_state_unlocked(st)


def record_rss_health(source_name: str, category: str, lang: str, url: str, items_count: int, latency_ms: int, status: str = "200 OK"):
    st = load_state()
    with _state_lock:
        rss_map = st.setdefault("api_usage", {}).setdefault("rss_health", {})
        rss_map[source_name] = {
            "source": source_name,
            "category": category,
            "lang": lang,
            "url": url,
            "items_count": items_count,
            "latency_ms": int(latency_ms),
            "status": status,
            "last_checked": _now_iso(),
        }
        _save_state_unlocked(st)


def record_pipeline_summary(duration_sec: float, pl_count: int, foreign_count: int):
    st = load_state()
    with _state_lock:
        au = st.setdefault("api_usage", {})
        au["last_pipeline_duration_sec"] = round(duration_sec, 2)
        au["last_pipeline_run"] = _now_iso()
        au["polish_articles_last_run"] = pl_count
        au["foreign_articles_translated_last_run"] = foreign_count
        _save_state_unlocked(st)


def record_page_view(ip: str, user_agent: str = "", event_type: str = "page_view", category: str = None, article_id: str = None, article_title: str = None):
    st = load_state()
    with _state_lock:
        tr = st.setdefault("traffic", {})
        visitor_hash = hashlib.sha256(f"{ip}|{user_agent}|{_today_str()}".encode("utf-8")).hexdigest()[:12]
        uv = tr.setdefault("unique_visitors_today", [])
        if visitor_hash not in uv:
            uv.append(visitor_hash)

        hour_key = datetime.datetime.now().strftime("%H")
        hv = tr.setdefault("hourly_views", {f"{h:02d}": 0 for h in range(24)})

        if event_type == "page_view":
            tr["total_page_views"] = tr.get("total_page_views", 0) + 1
            tr["today_page_views"] = tr.get("today_page_views", 0) + 1
            hv[hour_key] = hv.get(hour_key, 0) + 1
        elif event_type == "data_load":
            tr["total_data_requests"] = tr.get("total_data_requests", 0) + 1
        elif event_type == "tab_switch" and category:
            cv = tr.setdefault("category_views", {})
            cv[category] = cv.get(category, 0) + 1
        elif event_type == "article_open" and article_id:
            ar = tr.setdefault("article_reads", {})
            entry = ar.get(article_id, {"id": article_id, "title": article_title or article_id, "reads": 0})
            if article_title:
                entry["title"] = article_title
            entry["reads"] = entry.get("reads", 0) + 1
            ar[article_id] = entry
        elif event_type == "refresh_manual":
            tr["manual_refreshes"] = tr.get("manual_refreshes", 0) + 1
        elif event_type == "refresh_auto":
            tr["auto_refreshes"] = tr.get("auto_refreshes", 0) + 1
        elif event_type == "refresh_cached":
            tr["cached_hits_saved"] = tr.get("cached_hits_saved", 0) + 1

        _save_state_unlocked(st)


def get_gemini_key_masked() -> str:
    from ai_engine import get_gemini_api_key
    k = get_gemini_api_key()
    if not k:
        return ""
    if len(k) <= 8:
        return "********"
    return k[:4] + "•" * (len(k) - 8) + k[-4:]


def update_gemini_api_key(new_key: str, ip: str = "127.0.0.1"):
    new_key = (new_key or "").strip()
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.readlines() if not ln.strip().startswith("GEMINI_API_KEY=")]
    if new_key:
        lines.append(f"GEMINI_API_KEY={new_key}\n")
        os.environ["GEMINI_API_KEY"] = new_key
    else:
        os.environ.pop("GEMINI_API_KEY", None)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    append_audit_log("API_KEY_UPDATED", ip, "Zaktualizowano klucz GEMINI_API_KEY w pliku środowiskowym .env")
