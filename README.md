# AI WordPress Agent

Autonomiczny agent AI oparty o FastAPI + GPT-4o, ktory rozumie polecenia w jezyku naturalnym i wykonuje operacje na WordPressie. Projekt sklada sie z backendu FastAPI oraz wtyczki WordPress (PHP).

## Architektura

```text
Uzytkownik (przeglądarka)
        ↓
Wtyczka WordPress v3.0 (PHP)
  - formularz z 3 trybami
  - proxy AJAX + autoryzacja Bearer Token
        ↓ HTTP + Bearer Token
FastAPI Backend (port 8020)
        ↓              ↓              ↓
  /api/vision   /api/vision-to-post  /api/text-command
  Analiza        Zdjecie → Post      Router intencji LLM
  obrazu              ↓                     ↓
                 GPT-4o Vision         GPT-4o decyduje
                      ↓                co wykonac
                 WordPress         create_post / create_page
                 REST API          append_section / update_content
```

## Co potrafi agent

### Tryb 1 — Analiza zdjecia (wsparcie techniczne)
Uzytkownik wgrywa screenshot bledu lub komunikat — GPT-4o analizuje i zwraca diagnoza techniczna (specjalizacja: hosting CyberFolks).

### Tryb 2 — Zdjecie → Post WordPress
Uzytkownik wgrywa zdjecie — GPT-4o Vision generuje tytul, tresc HTML, tagi i excerpt, MCP tworzy szkic posta w WordPress.

### Tryb 3 — Polecenie tekstowe (agent AI)
Uzytkownik wpisuje polecenie naturalnym jezykiem — LLM jako router intencji decyduje co wykonac:

| Przyklad polecenia | Akcja |
|---|---|
| "Napisz post o Dockerze" | `create_post` |
| "Utworz podstrone Portfolio" | `create_page` |
| "Dodaj sekcje hero na stronie o-nas" | `append_section` |
| "Przepisz strone o-nas profesjonalnie" | `update_content` |
| "Dodaj animacje CSS do tej sekcji" | `update_content` |

## Endpointy

| Endpoint | Metoda | Opis |
|---|---|---|
| `/health` | GET | Status serwisu |
| `/api/vision` | POST | Analiza obrazu przez GPT-4o |
| `/api/vision-to-post` | POST | Zdjecie → szkic posta w WP |
| `/api/text-command` | POST | Router intencji LLM → operacja na WP |
| `/tools/list_posts` | GET | Pobiera liste postow z WP |
| `/tools/create_post` | POST | Tworzy nowy post w WP |
| `/tools/update_post` | POST | Edytuje istniejacy post w WP |
| `/tools/delete_post/{id}` | DELETE | Usuwa post z WP |
| `/mcp` | GET | Serwer MCP (SSE stream) |
| `/docs` | GET | Swagger UI |

## Struktura projektu

```text
.
├── docker-compose.yml
├── .env                  ← nie jest w repo (secrets)
├── .env.example          ← szablon zmiennych srodowiskowych
├── README.md
└── fastapi/
    ├── Dockerfile
    ├── main.py           ← caly backend: endpointy + router LLM
    └── requirements.txt
```

Wtyczka WordPress znajduje sie osobno w katalogu pluginow WP:
```text
wp-content/plugins/ai-support-bot/
└── ai-support-bot.php   ← formularz + proxy PHP + JS
```

## Wymagania

- Docker i Docker Compose
- VPS z Ubuntu Server
- WordPress z wlaczonym REST API i Application Passwords
- Klucz API OpenAI (GPT-4o)

## Konfiguracja

Utworz plik `.env` na podstawie `.env.example`:

```bash
cp .env.example .env
nano .env
```

Zmienne srodowiskowe:

```env
API_SECRET_TOKEN=wygeneruj_przez_openssl_rand_hex_32
OPENAI_API_KEY=sk-...
WP_USER=nazwa_uzytkownika_wordpress
WP_APP_PASSWORD=haslo_aplikacji_z_wp_admin
WP_URL=http://wordpress_app/wp-json/wp/v2
```

### WordPress Application Password

1. Zaloguj sie do WP Admin → Uzytkownicy → Twoj profil
2. Zjed do sekcji "Application Passwords"
3. Wpisz nazwe `ai-bot` → kliknij "Add New Application Password"
4. Skopiuj wygenerowane haslo do `.env`

### Wymagana konfiguracja WordPress

Dodaj do `wp-config.php` przed linia `/* That's all */`:

```php
define('WP_ENVIRONMENT_TYPE', 'local');
```

Wymagane gdy WordPress dziala przez HTTP (bez SSL) w srodowisku Docker.

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

# Sprawdz logi
docker compose logs -f fastapi
```

## Sprawdz czy dziala

```bash
# Health check
curl https://twoja-domena.duckdns.org/health

# Test analizy zdjecia
curl -X POST https://twoja-domena.duckdns.org/api/vision \
  -H "Authorization: Bearer TWOJ_TOKEN" \
  -F "file=@/tmp/screenshot.jpg"

# Test polecenia tekstowego
curl -X POST https://twoja-domena.duckdns.org/api/text-command \
  -H "Authorization: Bearer TWOJ_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Napisz post o bezpieczenstwie SSH"}'

# Test tworzenia posta ze zdjeciem
curl -X POST https://twoja-domena.duckdns.org/api/vision-to-post \
  -H "Authorization: Bearer TWOJ_TOKEN" \
  -F "file=@/tmp/zdjecie.jpg" \
  -F "status=draft"
```

## Bezpieczenstwo

- Nie commituj `.env` do repozytorium (jest w `.gitignore`)
- Token API generuj przez `openssl rand -hex 32`
- `WP_APP_PASSWORD` to haslo aplikacji WordPress — nie glowne haslo admina
- Jesli sekret wycieknie — zmien go w `.env` i zrestartuj kontener

## Stack technologiczny

- **FastAPI** — framework API (Python)
- **fastapi-mcp** — serwer MCP eksponujacy endpointy jako narzedzia AI
- **OpenAI GPT-4o** — Vision API + router intencji LLM
- **httpx** — async HTTP client do komunikacji z WordPress
- **Docker Compose** — konteneryzacja i siec miedzy serwisami
- **WordPress REST API** — backend CMS
- **PHP/WordPress Plugin** — frontend agenta (shortcode `[ai_support_bot]`)

## Roadmap

- [x] Vision AI — analiza zdjec
- [x] Vision to Post — zdjecie generuje posta
- [x] Text Command — router intencji LLM
- [x] create_post — tworzenie postow
- [x] create_page — tworzenie podstron
- [x] append_section — dodawanie sekcji HTML+CSS
- [x] update_content — edycja i stylowanie istniejacych tresci
- [ ] upload_media — dodawanie zdjec do biblioteki WP
- [ ] rate limiting — ochrona przed spamem
- [ ] settings page — strona ustawien wtyczki
- [ ] plugin distribution — wersja do dystrybucji (zip)
