# AI WordPress Agent

Autonomiczny agent AI oparty o FastAPI + GPT-4o, który rozumie polecenia w języku naturalnym i wykonuje operacje na WordPressie — z systemem podglądu przed zapisem. Projekt składa się z backendu FastAPI oraz wtyczki WordPress (PHP).

## Architektura

```text
Użytkownik (przeglądarka)
        ↓
Wtyczka WordPress v5.0 (PHP)
  - panel admina z 3 trybami
  - proxy AJAX + autoryzacja Bearer Token
  - system podglądu z przyciskami Zatwierdź/Odrzuć
        ↓ HTTP + Bearer Token
FastAPI Backend (port 8020)
        ↓                    ↓                      ↓
  /api/vision        /api/vision-to-post     /api/text-command
  Analiza obrazu     Zdjęcie → Post WP       Router intencji LLM
                                                      ↓
                                              GPT-4o decyduje
                                              co wykonać
                                                      ↓
                                         pending_actions (podgląd)
                                                      ↓
                                    /api/confirm-action | /api/discard-action
                                                      ↓
                                             WordPress REST API
```

## Co potrafi agent

### Tryb 1 — Analiza zdjęcia (wsparcie techniczne)
Użytkownik wgrywa screenshot błędu lub komunikat — GPT-4o analizuje i zwraca diagnozę techniczną (specjalizacja: hosting CyberFolks).

### Tryb 2 — Zdjęcie → Post WordPress
Użytkownik wgrywa zdjęcie — GPT-4o Vision generuje tytuł, treść HTML, tagi i excerpt, tworzy szkic posta w WordPress.

### Tryb 3 — Polecenie tekstowe (agent AI z podglądem)
Użytkownik wpisuje polecenie naturalnym językiem — LLM jako router intencji decyduje co wykonać. Przed każdą zmianą agent generuje **podgląd wizualny** i czeka na zatwierdzenie.

| Przykład polecenia | Akcja | Podgląd |
|---|---|---|
| `Napisz post o Dockerze` | `create_post` | Wygenerowany HTML posta |
| `Utwórz podstronę Portfolio` | `create_page` | HTML nowej strony |
| `Dodaj sekcję hero na stronie o-nas` | `append_section` | Wizualny podgląd sekcji |
| `Przepisz stronę o-nas profesjonalnie` | `update_content` | Pełny HTML po zmianie |
| `Przenieś sekcję X nad sekcję Y` | `move_section` | Strona z nową kolejnością |
| `Usuń sekcję kontakt ze strony X` | `delete_section` | Strona po usunięciu |
| `Zamień miejscami sekcje A i B` | `swap_sections` | Strona po zamianie |

## System podglądu (Pending Actions)

Każda operacja modyfikująca treść WordPress przechodzi przez system podglądu:

1. Agent oblicza zmiany i generuje `preview_html`
2. Wtyczka wyświetla podgląd wizualny w panelu admina
3. Użytkownik klika **Zatwierdź i zapisz** lub **Odrzuć zmiany**
4. Podgląd wygasa automatycznie po 20 minutach
5. Cofnięcie ostatniej akcji dostępne przez przycisk **Cofnij**

## Endpointy

| Endpoint | Metoda | Opis |
|---|---|---|
| `/health` | GET | Status serwisu |
| `/api/vision` | POST | Analiza obrazu przez GPT-4o |
| `/api/vision-to-post` | POST | Zdjęcie → szkic posta w WP |
| `/api/text-command` | POST | Router intencji LLM → podgląd operacji |
| `/api/confirm-action` | POST | Zatwierdź i zapisz do WordPress |
| `/api/discard-action` | POST | Odrzuć podgląd bez zapisu |
| `/api/undo-last` | POST | Cofnij ostatnią zatwierdzoną akcję |
| `/tools/list_posts` | GET | Pobiera listę postów z WP |
| `/tools/create_post` | POST | Tworzy nowy post w WP |
| `/tools/update_post` | POST | Edytuje istniejący post w WP |
| `/tools/delete_post/{id}` | DELETE | Usuwa post z WP |
| `/mcp` | GET | Serwer MCP (SSE stream) |
| `/docs` | GET | Swagger UI |

## Struktura projektu

```text
.
├── docker-compose.yml
├── .env                  ← nie jest w repo (secrets)
├── .env.example          ← szablon zmiennych środowiskowych
├── README.md
└── fastapi/
    ├── Dockerfile
    ├── main.py           ← cały backend: endpointy + router LLM + pending actions
    └── requirements.txt
```

Wtyczka WordPress znajduje się osobno w katalogu pluginów WP:
```text
wp-content/plugins/ai-support-bot/
└── ai-support-bot.php   ← panel admina + proxy PHP + JS z systemem podglądu
```

## Wymagania

- Docker i Docker Compose
- VPS z Ubuntu Server
- WordPress z włączonym REST API i Application Passwords
- Klucz API OpenAI (GPT-4o)

## Konfiguracja

Utwórz plik `.env` na podstawie `.env.example`:

```bash
cp .env.example .env
nano .env
```

Zmienne środowiskowe:

```env
API_SECRET_TOKEN=wygeneruj_przez_openssl_rand_hex_32
OPENAI_API_KEY=sk-...
WP_USER=nazwa_uzytkownika_wordpress
WP_APP_PASSWORD=haslo_aplikacji_z_wp_admin
WP_URL=http://wordpress_app/wp-json/wp/v2
```

### WordPress Application Password

1. Zaloguj się do WP Admin → Użytkownicy → Twój profil
2. Zejdź do sekcji "Application Passwords"
3. Wpisz nazwę `ai-bot` → kliknij "Add New Application Password"
4. Skopiuj wygenerowane hasło do `.env`

### Wymagana konfiguracja WordPress

Dodaj do `wp-config.php` przed linią `/* That's all */`:

```php
define('WP_ENVIRONMENT_TYPE', 'local');
```

Wymagane gdy WordPress działa przez HTTP (bez SSL) w środowisku Docker.

## Uruchomienie

```bash
# Sklonuj repo
git clone <repo-url>
cd ai-bot

# Skonfiguruj zmienne
cp .env.example .env
nano .env

# Uruchom
docker compose up -d --build

# Sprawdź logi
docker compose logs -f fastapi
```

## Sprawdź czy działa

```bash
# Health check
curl https://twoja-domena.duckdns.org/health

# Test polecenia tekstowego
curl -X POST https://twoja-domena.duckdns.org/api/text-command \
  -H "Authorization: Bearer TWOJ_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Dodaj sekcję hero na stronę o-nas"}'

# Test analizy zdjęcia
curl -X POST https://twoja-domena.duckdns.org/api/vision \
  -H "Authorization: Bearer TWOJ_TOKEN" \
  -F "file=@/tmp/screenshot.jpg"
```

## Bezpieczeństwo

- Nie commituj `.env` do repozytorium (jest w `.gitignore`)
- Token API generuj przez `openssl rand -hex 32`
- `WP_APP_PASSWORD` to hasło aplikacji WordPress — nie główne hasło admina
- Jeśli sekret wycieknie — zmień go w `.env` i zrestartuj kontener
- Panel agenta dostępny tylko dla zalogowanych adminów WP (`manage_options`)

## Stack technologiczny

- **FastAPI** — framework API (Python)
- **fastapi-mcp** — serwer MCP eksponujący endpointy jako narzędzia AI
- **OpenAI GPT-4o** — Vision API + router intencji LLM + generowanie HTML
- **httpx** — async HTTP client do komunikacji z WordPress
- **Docker Compose** — konteneryzacja i sieć między serwisami
- **WordPress REST API** — backend CMS
- **PHP/WordPress Plugin v5.0** — panel admina z systemem podglądu

## Roadmap

- [x] Vision AI — analiza zdjęć
- [x] Vision to Post — zdjęcie generuje posta
- [x] Text Command — router intencji LLM
- [x] create_post / create_page — tworzenie treści
- [x] append_section — dodawanie sekcji HTML+CSS
- [x] update_content — edycja istniejących treści
- [x] move_section / delete_section / swap_sections — zarządzanie sekcjami
- [x] System podglądu (pending actions) — zatwierdź/odrzuć przed zapisem
- [x] Cofnij ostatnią akcję (undo)
- [x] Countdown wygasania podglądu
- [ ] upload_media — dodawanie zdjęć do biblioteki WP
- [ ] rate limiting — ochrona przed spamem
- [ ] settings page — strona ustawień wtyczki w WP Admin
- [ ] plugin distribution — wersja do dystrybucji (zip)
