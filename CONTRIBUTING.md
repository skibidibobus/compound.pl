# Zasady współtworzenia projektu (Contributing)

Dziękujemy za zainteresowanie rozwojem projektu **compound.pl**.

## Zgłaszanie błędów i propozycji

- Przed utworzeniem nowego zgłoszenia sprawdź, czy podobny temat nie został już opisany w zakładce **Issues**.
- Korzystaj z przygotowanych szablonów zgłoszeń (`Zgłoszenie błędu` lub `Propozycja funkcji`).

## Standardy kodu

1. **Python (`fetcher.py`, `server.py`, `ai_engine.py`, `admin_manager.py`, `scripts/`)**:
   - Kod zgodny z konwencją PEP 8.
   - Nowe funkcje i klasy powinny posiadać zwięzłe docstringi w języku polskim.
   - Zabrania się umieszczania kluczy API, haseł lub tokenów bezpośrednio w kodzie źródłowym.
2. **Frontend (`index.html`, `admin.html`)**:
   - Interfejs utrzymywany jest w spójnej, minimalistycznej stylistyce terminala finansowego bez zbędnych zewnętrznych bibliotek JS.
   - Wszystkie elementy dynamiczne wstrzykiwane do DOM muszą przechodzić przez funkcję `esc()` w celu ochrony przed XSS.
3. **Zgodność prawna**:
   - Wszelkie treści analityczne muszą zachowywać charakter edukacyjny i informacyjny, bez formułowania rekomendacji inwestycyjnych w rozumieniu KNF/MAR.

## Przebieg pracy (Pull Request)

1. Utwórz rozgałęzienie (*branch*) od gałęzi `main`.
2. Wprowadź zmiany i zweryfikuj poprawność działania lokalnie (`python3 run.py` oraz kompilację plików `.py`).
3. Opisz dokładnie zakres zmian w treści Pull Requesta.
