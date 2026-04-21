# AI Bot Backend

Backend API oparty o FastAPI, używany jako zaplecze dla integracji z WordPressem.

Projekt odbiera żądania z wtyczki WordPress, weryfikuje token dostępu i zwraca odpowiedź z analizy przesłanego obrazu lub danych wejściowych.

## Jak to działa

Architektura projektu:

- WordPress plugin wysyła żądanie HTTP do backendu.
- Backend FastAPI sprawdza nagłówek autoryzacyjny lub token.
- Backend przetwarza dane wejściowe.
- API zwraca odpowiedź do WordPressa, która jest wyświetlana użytkownikowi.

## Struktura projektu

```text
.
├── docker-compose.yml
├── fastapi/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
└── README.md
```

## Wymagania

- Docker
- Docker Compose
- VPS lub inny serwer Linux
- Publiczny adres URL lub reverse proxy
- WordPress plugin skonfigurowany do komunikacji z API
