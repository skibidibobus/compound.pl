# Architektura systemu compound.pl

## Przegląd ogólny

System **compound.pl** został zaprojektowany w architekturze hybrydowej typu *Static-First + On-Demand API*, co pozwala na utrzymanie niskich kosztów infrastruktury (hostowanie frontendu i migawki danych na GitHub Pages oraz cykliczne odświeżanie w GitHub Actions) przy jednoczesnym zachowaniu pełnej funkcjonalności serwerowej w środowisku lokalnym lub chmurowym.

```text
Źródła zewnętrzne (NBP, Yahoo Finance, CoinGecko, RSS PL/EN)
        │
        ▼
[ fetcher.py ] ──► [ ai_engine.py ] (Google Gemini API / silnik regułowy)
        │
        ├──► [ long_term_analyses.py ] (analizy fundamentalne + koszyki)
        │
        ▼
   [ data.json ] ──► Statyczny frontend (index.html na GitHub Pages)
        │
        └──► [ scripts/post_briefing_x.py ] (automatyczny wpis na X)
```

## Warstwy aplikacji

### 1. Warstwa pozyskiwania danych (`fetcher.py`)
- Pobiera tabele kursów średnich walut NBP (Tabela A) oraz ceny złota NBP.
- Równolegle odpytuje notowania giełdowe (GPW, S&P 500, spółki technologiczne z USA, surowce) oraz kryptowaluty (CoinGecko).
- Agreguje kanały RSS w pięciu działach (`rynki`, `makro`, `tech`, `swiat`, `sport`), przeprowadza globalną deduplikację pomiędzy działami i tłumaczy materiały zagraniczne na język polski z wykorzystaniem potrójnego mechanizmu zapasowego (`clients5`, `googleapis`, `MyMemory`).

### 2. Warstwa analityczna (`ai_engine.py` i `long_term_analyses.py`)
- Wyciąga z treści wyłącznie rzeczywiste wskaźniki liczbowe (przychody, marże, stopy zwrotu, poziomy stóp procentowych).
- Przypisuje wpływ rynkowy (`HIGH`, `MEDIUM`, `LOW`), wydźwięk oraz podsumowanie.
- Moduł `long_term_analyses.py` łączy bieżące notowania z opracowaniami fundamentalnymi 12 spółek oraz trzema modelami alokacji długoterminowej.

### 3. Warstwa serwerowa i administracyjna (`server.py`, `admin_manager.py`, `admin.html`)
- Udostępnia lokalny serwer HTTP, endpointy REST (`/api/status`, `/api/refresh`, `/api/telemetry`) oraz chroniony panel administratora (`/admin`).
- Przechowuje telemetrię wykorzystania limitów API, stan kanałów RSS oraz logi audytowe w pliku `admin_state.json` (wyłączonym z kontroli wersji w `.gitignore`).

### 4. Warstwa prezentacji (`index.html`)
- Interfejs zbudowany w konwencji terminala finansowego przy użyciu Tailwind CSS i czystego JavaScriptu bez ciężkich zależności frontendowych.
- Obsługuje zarówno ścieżki lokalne (`http://localhost:8000`), jak i hosting pod ścieżką podkatalogu w GitHub Pages (`/compound.pl/`).
