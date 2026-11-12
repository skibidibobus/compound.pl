"""
Compound (compound.pl) — Serwer Aplikacji, Telemetrii i Zabezpieczonego Panelu Admina (server.py)
Odpowiedzialny za:
1. Serwowanie interfejsu compound.pl, zasobów statycznych oraz Panelu Administratora (/admin).
2. Inteligentną ochronę limitów API (Rate-Limit / Cooldown Guard).
3. Zabezpieczone API Administratora (PBKDF2-SHA256, tokeny sesyjne 256-bit, ochrona Brute-Force, nagłówki bezpieczeństwa).
4. Zbieranie statystyk ruchu, użycia limitów API oraz zarządzanie treścią (CMS) w czasie rzeczywistym.
"""

import os
import time
import json
import hashlib
import datetime
import threading
from http.cookies import SimpleCookie
from http.server import HTTPServer, SimpleHTTPRequestHandler
from fetcher import update_all_data, CATEGORY_FEEDS
from ai_engine import get_gemini_api_key
from admin_manager import (
    API_QUOTA_SPECS,
    load_state,
    save_state,
    append_audit_log,
    authenticate_admin,
    verify_session_token,
    logout_session,
    change_admin_password,
    record_page_view,
    get_gemini_key_masked,
    update_gemini_api_key,
)

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_START_TS = time.time()

is_refreshing = False


def get_data_age_seconds():
    """Zwraca wiek pliku data.json w sekundach."""
    data_file = os.path.join(BASE_DIR, "data.json")
    if not os.path.exists(data_file):
        return 999999
    try:
        return max(0, int(time.time() - os.path.getmtime(data_file)))
    except Exception:
        return 999999


def load_data_json():
    data_file = os.path.join(BASE_DIR, "data.json")
    if not os.path.exists(data_file):
        return {}
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_data_json(data_obj):
    data_file = os.path.join(BASE_DIR, "data.json")
    tmp = data_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data_obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, data_file)


class CompoundHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def _client_ip(self) -> str:
        xff = self.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "127.0.0.1"

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2_000_000:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)
        except Exception:
            return {}

    def _send_json(self, payload: dict, status_code: int = 200, extra_headers: dict = None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _extract_admin_token(self) -> str:
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            return auth_hdr[7:].strip()
        cookie_hdr = self.headers.get("Cookie", "")
        if cookie_hdr:
            c = SimpleCookie()
            try:
                c.load(cookie_hdr)
                if "compound_admin_session" in c:
                    return c["compound_admin_session"].value
            except Exception:
                pass
        return ""

    def _require_admin(self) -> bool:
        token = self._extract_admin_token()
        if not verify_session_token(token):
            self._send_json({"ok": False, "error": "Brak autoryzacji. Zaloguj się do Panelu Administratora."}, status_code=401)
            return False
        return True

    def do_GET(self):
        clean_path = self.path.split("?")[0]
        ip = self._client_ip()
        ua = self.headers.get("User-Agent", "")

        # Blokada bezpośredniego pobierania wrażliwych plików źródłowych, konfiguracji i danych systemowych
        normalized_clean = os.path.normpath(clean_path).replace("\\", "/")
        blocked_exact = (
            "/admin_state.json", "/.env", "/.env.example", "/.gitignore",
            "/server.py", "/admin_manager.py", "/fetcher.py", "/ai_engine.py",
            "/long_term_analyses.py", "/run.py", "/requirements.txt"
        )
        if (
            normalized_clean in blocked_exact
            or normalized_clean.startswith("/.git")
            or normalized_clean.endswith(".py")
            or normalized_clean.endswith(".json") and normalized_clean != "/data.json"
        ):
            self.send_error(403, "Forbidden")
            return

        if clean_path == "/" or clean_path == "/index.html":
            record_page_view(ip, ua, event_type="page_view")
            self.path = "/index.html"
            return super().do_GET()

        elif clean_path in ("/admin", "/admin/", "/admin.html"):
            self.path = "/admin.html"
            return super().do_GET()

        elif clean_path == "/data.json":
            record_page_view(ip, ua, event_type="data_load")
            data_file = os.path.join(BASE_DIR, "data.json")
            if os.path.exists(data_file):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                with open(data_file, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "data.json not found")
                return

        elif clean_path == "/api/status":
            st = load_state()
            cfg = st.get("config", {})
            self._send_json({
                "server": "online",
                "gemini_api_active": bool(get_gemini_api_key()),
                "is_refreshing": is_refreshing,
                "data_age_seconds": get_data_age_seconds(),
                "auto_refresh_cooldown_sec": cfg.get("auto_refresh_cooldown_sec", 540),
                "breaking_banner": cfg.get("breaking_banner", {"enabled": False}),
            })
            return

        elif clean_path == "/api/admin/overview":
            if not self._require_admin():
                return
            st = load_state()
            data_obj = load_data_json()
            all_Configured_feeds = []
            disabled_set = set(st.get("config", {}).get("disabled_feeds", []))
            rss_health_map = st.get("api_usage", {}).get("rss_health", {})

            for cat_key, specs in CATEGORY_FEEDS.items():
                for sp in specs:
                    sname, surl, slim = sp[0], sp[1], sp[2]
                    slang = sp[3] if len(sp) > 3 else "PL"
                    h_info = rss_health_map.get(sname, {})
                    all_Configured_feeds.append({
                        "name": sname,
                        "url": surl,
                        "limit": slim,
                        "lang": slang,
                        "category": cat_key,
                        "enabled": sname not in disabled_set,
                        "is_custom": False,
                        "items_count": h_info.get("items_count", 0),
                        "latency_ms": h_info.get("latency_ms", 0),
                        "status": h_info.get("status", "Oczekuje"),
                        "last_checked": h_info.get("last_checked", "—"),
                    })

            for cf in st.get("config", {}).get("custom_feeds", []):
                sname = cf.get("name", "Custom RSS")
                h_info = rss_health_map.get(sname, {})
                all_Configured_feeds.append({
                    "name": sname,
                    "url": cf.get("url", ""),
                    "limit": cf.get("limit", 3),
                    "lang": cf.get("lang", "PL"),
                    "category": cf.get("category", "rynki"),
                    "enabled": sname not in disabled_set,
                    "is_custom": True,
                    "items_count": h_info.get("items_count", 0),
                    "latency_ms": h_info.get("latency_ms", 0),
                    "status": h_info.get("status", "Oczekuje"),
                    "last_checked": h_info.get("last_checked", "—"),
                })

            self._send_json({
                "ok": True,
                "server_uptime_sec": int(time.time() - SERVER_START_TS),
                "data_age_seconds": get_data_age_seconds(),
                "is_refreshing": is_refreshing,
                "gemini_api_active": bool(get_gemini_api_key()),
                "gemini_key_masked": get_gemini_key_masked(),
                "quota_specs": API_QUOTA_SPECS,
                "api_usage": st.get("api_usage", {}),
                "traffic": st.get("traffic", {}),
                "config": st.get("config", {}),
                "feeds": all_Configured_feeds,
                "audit_log": st.get("audit_log", [])[:60],
                "articles": {
                    cat: data_obj.get(cat, [])
                    for cat in ["rynki", "makro", "tech", "swiat", "sport"]
                },
                "metadata": data_obj.get("metadata", {}),
            })
            return

        return super().do_GET()

    def do_POST(self):
        global is_refreshing
        clean_path = self.path.split("?")[0]
        ip = self._client_ip()
        ua = self.headers.get("User-Agent", "")

        # 1. Telemetria kliknięć zakładek i otwieranych artykułów
        if clean_path == "/api/telemetry":
            body = self._read_json_body()
            ev = body.get("event", "")
            if ev in ("tab_switch", "article_open"):
                record_page_view(
                    ip,
                    ua,
                    event_type=ev,
                    category=body.get("category"),
                    article_id=body.get("article_id"),
                    article_title=body.get("article_title"),
                )
            self._send_json({"ok": True})
            return

        # 2. Publiczny endpoint odświeżania z ochroną Cooldown Guard
        if clean_path == "/api/refresh":
            is_auto = "mode=auto" in self.path
            if is_refreshing:
                self._send_json({"status": "busy", "message": "Odświeżanie już trwa w tle"})
                return

            st = load_state()
            cfg = st.get("config", {})
            auto_cd = int(cfg.get("auto_refresh_cooldown_sec", 540))
            man_cd = int(cfg.get("manual_refresh_cooldown_sec", 20))

            age = get_data_age_seconds()
            cooldown = auto_cd if is_auto else man_cd
            if age < cooldown:
                record_page_view(ip, ua, event_type="refresh_cached")
                self._send_json({
                    "status": "cached",
                    "age_seconds": age,
                    "message": f"Dane są aktualne (pobrane {age} s temu) — oszczędzanie limitów API.",
                })
                return

            record_page_view(ip, ua, event_type="refresh_auto" if is_auto else "refresh_manual")

            def worker():
                global is_refreshing
                is_refreshing = True
                try:
                    update_all_data()
                except Exception as e:
                    print(f"[Server Refresh Error] {e}")
                finally:
                    is_refreshing = False

            threading.Thread(target=worker, daemon=True).start()
            self._send_json({"status": "accepted", "message": "Rozpoczęto odświeżanie w tle"})
            return

        # 3. Logowanie do Panelu Admina
        if clean_path == "/api/admin/login":
            body = self._read_json_body()
            password = body.get("password", "")
            res = authenticate_admin(password, ip)
            if not res.get("ok"):
                self._send_json(res, status_code=401)
                return
            cookie_val = f"compound_admin_session={res['token']}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400"
            self._send_json(res, status_code=200, extra_headers={"Set-Cookie": cookie_val})
            return

        # 4. Wylogowanie z Panelu Admina
        if clean_path == "/api/admin/logout":
            token = self._extract_admin_token()
            body = self._read_json_body()
            logout_session(token, ip=ip, all_sessions=bool(body.get("all_sessions")))
            clear_cookie = "compound_admin_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"
            self._send_json({"ok": True}, extra_headers={"Set-Cookie": clear_cookie})
            return

        # Wszystkie poniższe endpointy wymagają ważnej sesji administratora
        if clean_path.startswith("/api/admin/"):
            if not self._require_admin():
                return

            # Wymuszone odświeżenie potoku przez Admina (omija Cooldown)
            if clean_path == "/api/admin/force-refresh":
                if is_refreshing:
                    self._send_json({"ok": True, "status": "busy", "message": "Potok danych już pracuje w tle."})
                    return

                append_audit_log("ADMIN_FORCE_REFRESH", ip, "Administrator wymusił pełne odświeżenie potoku danych i tłumaczeń")

                def admin_worker():
                    global is_refreshing
                    is_refreshing = True
                    try:
                        update_all_data()
                    finally:
                        is_refreshing = False

                threading.Thread(target=admin_worker, daemon=True).start()
                self._send_json({"ok": True, "status": "accepted", "message": "Uruchomiono pełne odświeżenie danych."})
                return

            # Aktualizacja konfiguracji portalu, limitów Cooldown, paska Breaking News, źródeł RSS i klucza Gemini
            if clean_path == "/api/admin/config":
                body = self._read_json_body()
                st = load_state()
                cfg = st.setdefault("config", {})

                if "auto_refresh_cooldown_sec" in body:
                    cfg["auto_refresh_cooldown_sec"] = max(60, int(body["auto_refresh_cooldown_sec"]))
                if "manual_refresh_cooldown_sec" in body:
                    cfg["manual_refresh_cooldown_sec"] = max(5, int(body["manual_refresh_cooldown_sec"]))
                if "articles_per_category" in body:
                    cfg["articles_per_category"] = max(3, min(16, int(body["articles_per_category"])))
                if "translate_foreign_articles" in body:
                    cfg["translate_foreign_articles"] = bool(body["translate_foreign_articles"])
                if "blocked_keywords" in body and isinstance(body["blocked_keywords"], list):
                    cfg["blocked_keywords"] = [str(x).strip() for x in body["blocked_keywords"] if str(x).strip()]
                if "breaking_banner" in body and isinstance(body["breaking_banner"], dict):
                    bb = body["breaking_banner"]
                    cfg["breaking_banner"] = {
                        "enabled": bool(bb.get("enabled")),
                        "label": str(bb.get("label", "PILNE")).strip() or "PILNE",
                        "text": str(bb.get("text", "")).strip(),
                        "link": str(bb.get("link", "")).strip(),
                        "style": str(bb.get("style", "amber")),
                    }
                    # Natychmiast zapisz też w data.json, aby strona główna od razu widziała pasek
                    d_obj = load_data_json()
                    if d_obj:
                        d_obj.setdefault("metadata", {})["breaking_banner"] = cfg["breaking_banner"]
                        save_data_json(d_obj)

                if "toggle_feed" in body:
                    fname = str(body["toggle_feed"])
                    dis = set(cfg.get("disabled_feeds", []))
                    if fname in dis:
                        dis.remove(fname)
                        action_str = f"Włączono źródło RSS: {fname}"
                    else:
                        dis.add(fname)
                        action_str = f"Wyłączono źródło RSS: {fname}"
                    cfg["disabled_feeds"] = list(dis)
                    append_audit_log("FEED_TOGGLED", ip, action_str)

                if "add_custom_feed" in body and isinstance(body["add_custom_feed"], dict):
                    nf = body["add_custom_feed"]
                    if nf.get("name") and nf.get("url"):
                        c_list = cfg.setdefault("custom_feeds", [])
                        c_list.append({
                            "name": str(nf["name"]).strip(),
                            "url": str(nf["url"]).strip(),
                            "category": str(nf.get("category", "rynki")),
                            "lang": str(nf.get("lang", "EN")),
                            "limit": int(nf.get("limit", 3)),
                        })
                        append_audit_log("FEED_ADDED", ip, f"Dodano nowe źródło RSS: {nf['name']} ({nf.get('lang', 'EN')})")

                if "remove_custom_feed" in body:
                    rname = str(body["remove_custom_feed"])
                    cfg["custom_feeds"] = [f for f in cfg.get("custom_feeds", []) if f.get("name") != rname]
                    append_audit_log("FEED_REMOVED", ip, f"Usunięto własne źródło RSS: {rname}")

                if "gemini_api_key" in body:
                    update_gemini_api_key(body["gemini_api_key"], ip=ip)

                save_state(st)
                append_audit_log("CONFIG_UPDATED", ip, "Zapisano zmiany w konfiguracji systemu compound.pl")
                self._send_json({"ok": True, "config": cfg, "gemini_key_masked": get_gemini_key_masked()})
                return

            # Edycja / Dodawanie / Usuwanie / Przypinanie artykułów w CMS
            if clean_path == "/api/admin/article":
                body = self._read_json_body()
                action = body.get("action", "update")
                d_obj = load_data_json()
                if not d_obj:
                    self._send_json({"ok": False, "error": "Brak pliku data.json"}, status_code=400)
                    return

                if action == "delete":
                    art_id = body.get("id", "")
                    removed = False
                    for cat in ["rynki", "makro", "tech", "swiat", "sport"]:
                        before = len(d_obj.get(cat, []))
                        d_obj[cat] = [a for a in d_obj.get(cat, []) if a.get("id") != art_id]
                        if len(d_obj[cat]) < before:
                            removed = True
                    d_obj["gielda"] = d_obj.get("rynki", [])
                    save_data_json(d_obj)
                    append_audit_log("CMS_DELETE_ARTICLE", ip, f"Usunięto artykuł o ID: {art_id}")
                    self._send_json({"ok": True, "removed": removed})
                    return

                elif action == "create":
                    cat = body.get("category", "rynki")
                    title = str(body.get("title", "")).strip()
                    if not title:
                        self._send_json({"ok": False, "error": "Tytuł artykułu jest wymagany."}, status_code=400)
                        return
                    h = hashlib.sha256(f"{title}{time.time()}".encode("utf-8")).hexdigest()[:6]
                    pts = [p.strip() for p in body.get("summary_points", []) if str(p).strip()]
                    ext = [p.strip() for p in body.get("extended_paragraphs", []) if str(p).strip()]
                    if not pts:
                        pts = [title]
                    if not ext:
                        ext = pts
                    new_art = {
                        "id": f"{cat}-admin-{h}",
                        "entity_tag": str(body.get("entity_tag", "Komunikat Redakcyjny")).strip(),
                        "sector": str(body.get("sector", "Redakcja compound.pl")).strip(),
                        "market_impact": body.get("market_impact", "HIGH"),
                        "sentiment": body.get("sentiment", "neutral"),
                        "sentiment_rationale": str(body.get("sentiment_rationale", "Opracowanie własne redakcji compound.pl.")),
                        "key_metrics": [str(m).strip() for m in body.get("key_metrics", []) if str(m).strip()][:3],
                        "title": title,
                        "original_title": "",
                        "is_foreign": False,
                        "is_custom_admin": True,
                        "pinned_by_admin": bool(body.get("pinned_by_admin", True)),
                        "lang": "PL",
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "source": str(body.get("source", "Redakcja compound.pl")).strip(),
                        "source_url": str(body.get("source_url", "#")).strip() or "#",
                        "image_url": str(body.get("image_url", "")).strip(),
                        "image_source": str(body.get("image_source", "Fot.: Redakcja compound.pl")).strip(),
                        "lead_story": True,
                        "summary_points": pts[:3],
                        "extended_paragraphs": ext[:6],
                    }
                    cat_list = d_obj.setdefault(cat, [])
                    for a in cat_list:
                        a["lead_story"] = False
                    cat_list.insert(0, new_art)
                    d_obj["gielda"] = d_obj.get("rynki", [])
                    save_data_json(d_obj)
                    append_audit_log("CMS_CREATE_ARTICLE", ip, f"Opublikowano artykuł redakcyjny w dziale [{cat.upper()}]: {title[:50]}")
                    self._send_json({"ok": True, "article": new_art})
                    return

                elif action == "update":
                    art_id = body.get("id", "")
                    updated_art = None
                    for cat in ["rynki", "makro", "tech", "swiat", "sport"]:
                        cat_list = d_obj.get(cat, [])
                        for a in cat_list:
                            if a.get("id") == art_id:
                                if "title" in body:
                                    a["title"] = str(body["title"]).strip()
                                if "entity_tag" in body:
                                    a["entity_tag"] = str(body["entity_tag"]).strip()
                                if "sector" in body:
                                    a["sector"] = str(body["sector"]).strip()
                                if "market_impact" in body and body["market_impact"] in ("HIGH", "MEDIUM", "LOW"):
                                    a["market_impact"] = body["market_impact"]
                                if "sentiment" in body and body["sentiment"] in ("positive", "neutral", "negative"):
                                    a["sentiment"] = body["sentiment"]
                                if "image_url" in body:
                                    a["image_url"] = str(body["image_url"]).strip()
                                if "summary_points" in body and isinstance(body["summary_points"], list):
                                    a["summary_points"] = [str(x).strip() for x in body["summary_points"] if str(x).strip()][:3]
                                if "extended_paragraphs" in body and isinstance(body["extended_paragraphs"], list):
                                    a["extended_paragraphs"] = [str(x).strip() for x in body["extended_paragraphs"] if str(x).strip()][:6]
                                if "pinned_by_admin" in body:
                                    a["pinned_by_admin"] = bool(body["pinned_by_admin"])
                                    if a["pinned_by_admin"]:
                                        for other in cat_list:
                                            other["lead_story"] = (other is a)
                                        cat_list.remove(a)
                                        cat_list.insert(0, a)
                                updated_art = a
                                break
                    d_obj["gielda"] = d_obj.get("rynki", [])
                    save_data_json(d_obj)
                    append_audit_log("CMS_EDIT_ARTICLE", ip, f"Zaktualizowano treść artykułu: {art_id}")
                    self._send_json({"ok": True, "article": updated_art})
                    return

            # Zmiana hasła administratora
            if clean_path == "/api/admin/password":
                body = self._read_json_body()
                res = change_admin_password(
                    body.get("current_password", ""),
                    body.get("new_password", ""),
                    ip=ip,
                )
                self._send_json(res, status_code=200 if res.get("ok") else 400)
                return

        self.send_error(404, "Endpoint not found")


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def start_server(port=PORT):
    try:
        server = ReusableHTTPServer(("127.0.0.1", port), CompoundHandler)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print("============================================================")
            print(f" INFO: Serwer compound.pl JUŻ DZIAŁA w tle!")
            print(f" Adres strony:            http://localhost:{port}")
            print(f" Panel Administratora:    http://localhost:{port}/admin")
            print("============================================================")
            print("Nie musisz uruchamiać go ponownie. Wystarczy otworzyć przeglądarkę.")
            return
        raise e
    print("============================================================")
    print(f" compound.pl — Serwer aktywny: http://localhost:{port}")
    print(f" Panel Administratora:         http://localhost:{port}/admin")
    print("============================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")
        server.server_close()


if __name__ == "__main__":
    start_server()
