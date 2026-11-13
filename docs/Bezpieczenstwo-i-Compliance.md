# Bezpieczeństwo i zgodność regulacyjna (KNF / MAR)

## 1. Zabezpieczenia warstwy serwerowej (`server.py`, `admin_manager.py`)

### Uwierzytelnianie i sesje
- Hasło administratora nie jest przechowywane w postaci jawnej. System generuje indywidualną sól kryptograficzną i wylicza skrót przy użyciu funkcji **`PBKDF2-HMAC-SHA256`** (120 000 iteracji).
- Porównywanie skrótów i kluczy odbywa się w czasie stałym (`hmac.compare_digest`), co chroni przed atakami czasowymi (*timing attacks*).
- Tokeny sesyjne generowane są z kryptograficznego generatora liczb losowych (`secrets.token_hex(32)` — 256 bitów entropii).

### Ochrona przed atakami brute-force
- Po pięciu nieudanych próbach logowania z danego adresu IP dostęp do endpointu logowania dla tego adresu zostaje czasowo zablokowany na 10 minut (600 sekund).

### Izolacja plików wrażliwych
- Serwer HTTP w `server.py` blokuje (`403 Forbidden`) bezpośrednie pobieranie plików źródłowych Pythona (`*.py`), plików konfiguracyjnych (`.env`, `.env.example`, `.gitignore`), katalogu `.git` oraz wewnętrznych plików `.json` innych niż publiczny `data.json` (w tym `admin_state.json`).
- Wszystkie odpowiedzi serwera zawierają nagłówki bezpieczeństwa:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `Referrer-Policy: strict-origin-when-cross-origin`

## 2. Zarządzanie kluczami API

- Żadne klucze prywatne (`GEMINI_API_KEY`, `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`) nie są zapisywane w kodzie repozytorium.
- W środowisku produkcyjnym GitHub Actions klucze przechowywane są wyłącznie jako zaszyfrowane **GitHub Repository Secrets**.

## 3. Zgodność regulacyjna (Compliance KNF / MAR)

- Wszystkie treści publikowane w serwisie (w tym dział `Analizy Long-Term` i oceny sentymentu) mają charakter wyłącznie informacyjny, badawczy i edukacyjny.
- Portal nie świadczy usług doradztwa inwestycyjnego w rozumieniu Art. 76 Ustawy o obrocie instrumentami finansowymi oraz nie wydaje rekomendacji w rozumieniu Rozporządzenia MAR (UE nr 596/2014).
- Każde opracowanie spółki zawiera zarówno analizę przewag konkurencyjnych, jak i wykaz głównych czynników ryzyka.
