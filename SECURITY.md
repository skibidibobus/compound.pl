# Polityka bezpieczeństwa (Security Policy)

## Wersje wspierane

Aktualizacje bezpieczeństwa wydawane są wyłącznie dla bieżącej gałęzi `main`.

| Gałąź | Status wsparcia |
| --- | --- |
| `main` | Aktywnie wspierana |

## Zgłaszanie podatności

W przypadku wykrycia potencjalnej luki bezpieczeństwa (np. w obsłudze sesji panelu administratora, serwera HTTP lub walidacji danych wejściowych):

1. Prosimy **nie publikować** szczegółów błędu w publicznych zgłoszeniach (*Issues*).
2. Należy opisać podatność oraz kroki prowadzące do jej odtworzenia w wiadomości prywatnej do autora repozytorium.
3. Po weryfikacji poprawka zostanie przygotowana i wdrożona w pierwszej kolejności na gałąź `main`.

## Dobre praktyki wdrożeniowe

- W środowiskach publicznych panel administratora (`/admin`) powinien pracować za serwerem odwrotnego proxy (HTTPS / TLS) oraz mieć zmienione domyślne hasło poprzez zmienną `COMPOUND_ADMIN_PASSWORD` lub ustawienia panelu.
- Klucze API (`GEMINI_API_KEY`, klucze X API) należy przechowywać wyłącznie w pliku `.env` (lokalnie) lub w `GitHub Actions Secrets`.
