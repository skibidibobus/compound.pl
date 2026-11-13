# Automatyzacja i integracje API

## Harmonogramy GitHub Actions

Repozytorium wykorzystuje dwa niezależne przepływy pracy w `.github/workflows/`:

1. **`update_data.yml`**
   - Uruchamiany cyklicznie co 30 minut (`*/30 * * * *`) oraz ręcznie (`workflow_dispatch`).
   - Wykonuje `python3 fetcher.py` i aktualizuje migawkę `data.json` w repozytorium, co automatycznie odświeża stronę opublikowaną na GitHub Pages.

2. **`daily_briefing_x.yml`**
   - Uruchamiany codziennie rano o `07:00 UTC` (tylko wtedy, gdy w repozytorium skonfigurowane są sekrety X API).
   - Odświeża dane rynkowe i publikuje zwięzły briefing na platformie X poprzez skrypt `scripts/post_briefing_x.py`.

## Wykorzystywane źródła danych

| Obszar | Źródło | Uwagi |
| --- | --- | --- |
| Kursy walut i złoto | API Narodowego Banku Polskiego (`api.nbp.pl`) | Tabela A + oficjalne ceny złota NBP |
| Akcje GPW, USA, surowce | Yahoo Finance Chart API | Notowania opóźnione / dzienne |
| Kryptowaluty | CoinGecko Simple Price API | Kursy BTC i ETH w USD ze zmianą 24h |
| Wiadomości PL | Bankier.pl, Rzeczpospolita, PolsatNews, Chip.pl, Antyweb, SportoweFakty | Kanały RSS |
| Wiadomości zagraniczne | CNBC, BBC, TechCrunch, Ars Technica | Tłumaczone automatycznie na język polski |
| Analiza AI (opcjonalnie) | Google Gemini API (`GEMINI_API_KEY`) | W przypadku braku klucza działa lokalny silnik regułowy |

## Publikacja na platformie X (`scripts/post_briefing_x.py`)

- Skrypt wykorzystuje autoryzację OAuth 1.0a (HMAC-SHA1) zaimplementowaną w standardowej bibliotece Pythona bez zewnętrznych zależności.
- Formatuje treść z uwzględnieniem limitu 280 znaków (oraz skracacza linków `t.co`, który traktuje każdy adres URL jako 23 znaki).
- Dostępny jest tryb testowy bez wysyłania wpisu:
  ```bash
  python3 scripts/post_briefing_x.py --dry-run
  ```
