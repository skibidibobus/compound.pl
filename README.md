# compound.pl — Financial & Market Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![AI-Powered](https://img.shields.io/badge/AI-Google_Gemini-orange?style=for-the-badge&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Nowoczesny, instytucjonalny portal informacyjno-analityczny nowej generacji dla inwestorów, przedsiębiorców i analityków rynków finansowych. Zero clickbaitu, zaawansowana synteza faktograficzna AI (*Zero-Hallucination*), twarde dane z NBP, GPW, Wall Street i surowców oraz wbudowane narzędzia analityczne i kalkulatory inwestora.

---

## 🌟 Kluczowe Funkcjonalności (Features)

- **📈 Wielokanałowy Silnik Danych Rynkowych (Market Stream)**:
  - Automatyczny pobór oficjalnych tabel walut A i złota z NBP wraz z rzeczywistą zmianą sesja do sesji.
  - Notowania GPW (WIG20, PKO BP, XTB, Dino, Kruk, Grupa Kęty, Budimex, CD Projekt, PZU, Orlen, KGHM), rynków USA (S&P 500, NVIDIA, Microsoft), surowców (Ropa Brent, Złoto) i krypto (BTC, ETH).
- **📊 Dział Analiz Długoterminowych („Na Longa”)**:
  - Szczegółowe, obiektywne analizy fundamentalne 360° dla 12 liderów rynkowych (fosa ekonomiczna, wskaźniki ROE, P/E, stopa dywidendy, katalizatory rynkowe oraz realne czynniki ryzyka — w 100% zgodne z KNF/MAR).
  - 3 modelowe koszyki alokacji kapitału na horyzont 5–10 lat.
- **🤖 Instytucjonalny Silnik AI (Gemini Flash & Natural Translator)**:
  - Automatyczne streszczenia depesz, wyciąganie twardych wskaźników finansowych (EBITDA, r/r, marże), tagowanie wpływu rynkowego (*High / Medium / Low*) oraz ocena sentymentu.
  - Tłumaczenie zagranicznych źródeł (CNBC, BBC, TechCrunch, Ars Technica) na naturalny język polski.
- **⚡ Briefing 60s & Smart Auto-Refresh**:
  - Błyskawiczna pigułka 5 najważniejszych wydarzeń dnia z generatorem gotowych postów na platformy X, Telegram i LinkedIn.
  - Inteligentne odświeżanie danych co 10 minut działające wyłącznie wtedy, gdy użytkownik jest aktywny na karcie (ochrona limitów API).
- **🔒 Zabezpieczony Panel Administratora (`/admin`)**:
  - Logowanie z hashowaniem PBKDF2-HMAC-SHA256 (120k iteracji + sól kryptograficzna).
  - Monitorowanie limitów i zużycia API, telemetria zdrowia kanałów RSS, CMS do zarządzania komunikatami PILNE (Breaking News) oraz logi audytowe.
- **🧮 Narzędzia Inwestora**:
  - Kalkulator walutowy NBP na żywo.
  - Symulator procentu składanego (Compound) z porównaniem konta zwykłego (podatek Belki 19%) vs IKE/IKZE (0% podatku).

---

## 🚀 Szybkie Uruchomienie Lokalne

### Wymagania
- Python 3.9+
- Przeglądarka internetowa

### Krok po kroku:
```bash
# 1. Klonowanie repozytorium
git clone https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/compound.pl.git
cd compound.pl

# 2. (Opcjonalnie) Konfiguracja klucza Gemini AI
cp .env.example .env
# Wpisz swój klucz GEMINI_API_KEY w pliku .env (w przypadku braku klucza działa wbudowany silnik regułowy)

# 3. Uruchomienie aplikacji
python3 run.py
```

Aplikacja automatycznie wystartuje pod adresem **http://localhost:8000**, a panel administracyjny pod **http://localhost:8000/admin**.

---

## 🏗️ Architektura i Struktura Projektu

```text
compound.pl/
├── index.html               # Główny interfejs (Terminal finansowy, siatka newsów, modal czytnika, analizy)
├── admin.html               # Dashboard panelu administratora (metryki, limity API, CMS)
├── data.json                # Snapshot danych rynkowych, kursów i przeanalizowanych depesz
├── server.py                # Asynchroniczny serwer HTTP i REST API (/api/refresh, /api/status, /api/auth)
├── fetcher.py               # Wielowątkowy agregator NBP, Yahoo Finance, CoinGecko i RSS
├── ai_engine.py             # Silnik analityczny AI (Gemini API + regułowy Zero-Hallucination)
├── long_term_analyses.py    # Moduł analiz fundamentalnych spółek i modelowych portfeli
├── admin_manager.py         # Moduł bezpieczeństwa PBKDF2, telemetryki i zarządzania stanem
├── run.py                   # Skrypt startowy uruchamiający serwer i przeglądarkę
├── requirements.txt         # Zależności biblioteczne
├── .github/workflows/       # Automatyzacja GitHub Actions (odświeżanie danych w chmurze)
└── assets/brand/            # Kompletny pakiet wektorowej i rastrowej identyfikacji wizualnej
```

---

## ⚖️ Nota Prawna & Compliance (KNF / MAR)

Treści publikowane w projekcie mają charakter wyłącznie informacyjny, badawczy i edukacyjny. Nie stanowią porad inwestycyjnych ani rekomendacji w rozumieniu Rozporządzenia MAR (UE nr 596/2014) oraz Art. 76 Ustawy o obrocie instrumentami finansowymi.
