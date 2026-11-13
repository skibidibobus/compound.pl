# Historia zmian (Changelog)

Wszystkie istotne zmiany w projekcie **compound.pl** są dokumentowane w tym pliku.

## [1.2.0] - 2026-11-12

### Dodano
- Dział **Analizy Long-Term** (`long_term_analyses.py`) z analizą fundamentalną 12 spółek (GPW i Wall Street) oraz 3 modelowymi koszykami alokacji.
- Wsparcie dla statycznego hostingu na **GitHub Pages** (relatywne ścieżki zasobów i danych w `index.html`).
- Skrypt `scripts/post_briefing_x.py` oraz harmonogram `.github/workflows/daily_briefing_x.yml` do automatycznej publikacji briefingu na X.
- Osobny przycisk kopiowania briefingu skróconego pod limit 280 znaków na platformie X.
- Dokumentację techniczną w katalogu `docs/`, politykę bezpieczeństwa `SECURITY.md`, licencję MIT oraz szablony zgłoszeń.

### Poprawiono
- Globalna deduplikacja depesz pomiędzy działami w `fetcher.py` oraz dokładne dopasowanie nazw spółek z granicami słów w `ai_engine.py`.
- Przebudowany moduł tłumaczeń EN -> PL oparty na metodzie POST (`clients5`) z podwójnym mechanizmem zapasowym (`googleapis`, `MyMemory`), eliminujący błędy `HTTP 429`.
- Dodatkowa blokada dostępu HTTP (`403 Forbidden`) do wszystkich plików źródłowych `.py`, `.git` oraz wewnętrznych plików `.json` w `server.py`.

## [1.1.0] - 2026-11-04

### Dodano
- Zabezpieczony panel administratora (`/admin`) z uwierzytelnianiem `PBKDF2-HMAC-SHA256`, ochroną brute-force, podglądem limitów API, statystykami ruchu i edytorem CMS.
- Wbudowany czytnik artykułów z rozszerzoną treścią i kontekstem dla portfela.
- Moduł `Briefing 60s` oraz szybkie filtry portfelowe.
- Inteligentne odświeżanie danych co 10 minut aktywne wyłącznie podczas obecności użytkownika na karcie.

## [1.0.0] - 2026-11-03

### Dodano
- Pierwsza wersja portalu: pasek notowań NBP/GPW/krypto, 5 działów wiadomości, tabele kursowe, kalkulator walutowy oraz symulator procentu składanego (IKE vs podatek Belki).
- Pakiet identyfikacji wizualnej marki (`assets/brand/`).
