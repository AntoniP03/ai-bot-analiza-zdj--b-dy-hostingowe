# AI Bot Backend

Backend API oparty o FastAPI z serwerem MCP, używany jako zaplecze dla integracji z WordPressem. Projekt umożliwia analizę obrazów przez Vision AI (GPT-4o) oraz bezpośrednie operacje na treści WordPress przez REST API.

## Architektura

```text
Wtyczka WordPress (PHP)
        ↓ HTTP + Bearer Token
FastAPI Backend (port 8020)
        ↓                    ↓
GPT-4o Vision API     MCP Server (/mcp)
        ↓                    ↓
   Analiza obrazu    Narzędzia WordPress
                          ↓
                 WordPress REST API
                 (przez sieć Docker)
```

## Co robi ten projekt

- Odbiera zdjęcia z wtyczki WordPress i analizuje je przez GPT-4o Vision
- Specjalizuje się w diagnozowaniu problemów hostingowych CyberFolks
- Udostępnia serwer MCP z narzędziami do zarządzania treścią WordPress
- Autoryzuje żądania przez Bearer Token

## Endpointy

| Endpoint | Metoda | Opis |
|---|---|---|
| `/health` | GET | Status serwisu |
| `/api/vision` | POST | Analiza obrazu przez GPT-4o |
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
    ├── main.py
    └── requirements.txt
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
2. Zjedź do sekcji "Application Passwords"
3. Wpisz nazwę `ai-bot` → kliknij "Add New Application Password"
4. Skopiuj wygenerowane hasło do `.env`

### Wymagana konfiguracja WordPress

Dodaj do `wp-config.php` przed linią `/* That's all */`:

```php
define('WP_ENVIRONMENT_TYPE', 'local');
```

Wymagane gdy WordPress działa przez HTTP (bez SSL) — np. w środowisku Docker.

## Uruchomienie

```bash
# Sklonuj repo i wejdź do katalogu
git clone <repo-url>
cd ai-bot

# Skonfiguruj zmienne
cp .env.example .env
nano .env

# Uruchom
docker compose up -d --build

# Sprawdź logi
docker compose logs -f
```

## Sprawdź czy działa

```bash
# Health check
curl http://localhost:8020/health

# Test tworzenia posta
curl -X POST http://localhost:8020/tools/create_post \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Treść", "status": "draft"}'

# MCP server
curl http://localhost:8020/mcp
```

## Bezpieczeństwo

- Nie commituj `.env` do repozytorium
- Token API generuj przez `openssl rand -hex 32`
- `WP_APP_PASSWORD` to hasło aplikacji WordPress — nie główne hasło admina
- Jeśli sekret wycieknie, zmień go natychmiast w `.env` i `wp-config.php`

## Stack technologiczny

- **FastAPI** — framework API (Python)
- **fastapi-mcp** — serwer MCP eksponujący endpointy jako narzędzia AI
- **OpenAI GPT-4o** — Vision API do analizy obrazów
- **httpx** — async HTTP client do komunikacji z WordPress
- **Docker Compose** — konteneryzacja i sieć między serwisami
- **WordPress REST API** — backend CMS

## Status projektu

Projekt w aktywnym rozwoju. Aktualnie zaimplementowane: Vision AI, MCP server, narzędzia CRUD dla postów WordPress.
