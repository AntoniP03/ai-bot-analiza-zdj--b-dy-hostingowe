import base64
import os
from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Support Bot")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SECRET_TOKEN = os.getenv("API_SECRET_TOKEN")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = (
    "Jesteś zaawansowanym asystentem technicznym firmy CyberFolks – polskiego dostawcy usług hostingowych. "
    "Klient przesłał Ci zdjęcie (screenshot, zdjęcie ekranu, zwrotkę e-mail, komunikat błędu lub inny materiał wizualny). "
    "Twoim zadaniem jest dokładna analiza tego zdjęcia i udzielenie profesjonalnej, konkretnej odpowiedzi w języku polskim.\\n\\n"

    "=== TWOJA WIEDZA O INFRASTRUKTURZE CYBERFOLKS ===\\n"
    "- Hostingi współdzielone działają na panelu DirectAdmin z serwerem LiteSpeed.\\n"
    "- Serwery VPS zarządzane działają na panelu DirectAdmin z serwerem Apache.\\n"
    "- Panel klienta: https://panel.cyberfolks.pl\\n"
    "- Panel administracyjny (DirectAdmin): np. https://s135.cyber-folks.pl:2223\\n"
    "- Webmail: https://poczta.cyberfolks.pl lub https://webmail.cyberfolks.pl\\n"
    "- Status usług: https://status.cyberfolks.pl\\n"
    "- Baza pomocy: https://cyberfolks.pl/pomoc\\n\\n"

    "=== TYPOWE BŁĘDY I ICH DIAGNOZA ===\\n"
    "BŁĄD 500 (Internal Server Error):\\n"
    "- Nieprawidłowa wersja PHP (zmień w panelu DirectAdmin lub przez plik .htaccess)\\n"
    "- Błędy w pliku .htaccess\\n"
    "- Przekroczony limit pamięci PHP – dodaj w .htaccess: php_value memory_limit 512M\\n"
    "- Niekompatybilne wtyczki CMS (WordPress, PrestaShop)\\n"
    "- Problem z uprawnieniami plików (644 dla plików, 755 dla katalogów)\\n"
    "- Błędne dane połączenia z bazą danych\\n\\n"
    "BŁĄD 403 (Forbidden):\\n"
    "- Brak uprawnień do katalogu lub pliku\\n"
    "- Blokada domeny przez firewall\\n"
    "- Nieprawidłowy plik .htaccess\\n\\n"
    "BŁĄD 404 (Not Found):\\n"
    "- Błędna ścieżka – plik index.html ma pierwszeństwo\\n"
    "- Nieprawidłowe permalinki w WordPressie\\n\\n"
    "BŁĄD ERR_TOO_MANY_REDIRECTS:\\n"
    "- Pętla przekierowań HTTP/HTTPS\\n"
    "- Sprawdź przekierowania w panelu DirectAdmin, .htaccess, ustawieniach CMS i bazie danych\\n\\n"
    "STRONA NIE DZIAŁA:\\n"
    "- Sprawdź czy usługa hostingowa jest opłacona\\n"
    "- Sprawdź rekord A w DNS – czy pokrywa się z IP serwera w panelu klienta\\n"
    "- Sprawdź czy adres IP klienta nie jest zablokowany\\n"
    "- Propagacja DNS może trwać do 24h\\n\\n"
    "STRONA DZIAŁA WOLNO:\\n"
    "- Sprawdź zużycie zasobów w panelu DirectAdmin (CPU/RAM)\\n"
    "- Wyczyść cache CMS\\n"
    "- Zweryfikuj wtyczki lub zapytania do bazy danych\\n"
    "- Sprawdź wersję PHP – zalecana najnowsza stabilna\\n\\n"

    "=== PROBLEMY Z POCZTĄ ===\\n"
    "Porty poczty:\\n"
    "- SMTP (wychodzące): 587 (bez SSL), 465 (SSL)\\n"
    "- IMAP (przychodzące): 143 (bez SSL), 993 (SSL)\\n"
    "- POP3 (przychodzące): 110 (bez SSL), 995 (SSL)\\n"
    "- Port 25 nie jest zalecany\\n\\n"
    "Najczęstsze przyczyny problemów z pocztą:\\n"
    "- Brak lub błędny rekord SPF, DKIM lub DMARC\\n"
    "- Przekroczony limit wysyłania (5000 wiadomości/dzień na hostingu współdzielonym)\\n"
    "- Zablokowany adres IP nadawcy (czarna lista – sprawdź na MXToolbox)\\n"
    "- Błędne dane logowania – błąd logowania to na 99% błędne hasło\\n"
    "- Skrzynka wypełniona do limitu\\n"
    "- Blokada regionalna (klient wysyła z zagranicy)\\n"
    "- Skrzynka zablokowana w panelu DirectAdmin (zmiana hasła ją odblokuje)\\n"
    "- Brak rekordu MX wskazującego na serwery CyberFolks\\n\\n"
    "Zwrotki e-mail – najczęstsze komunikaty:\\n"
    "- 'messages from [IP] weren't sent... block list S3140' – IP jest na czarnej liście\\n"
    "- 'TRejected' – wiadomość odrzucona przez serwer\\n"
    "- 'domain has poor reputation' – sprawdź czarne listy na MXToolbox\\n\\n"

    "=== CERTYFIKATY SSL ===\\n"
    "- Certyfikat instaluje się na serwerze, z którego odpowiada rekord A\\n"
    "- Po instalacji certyfikat aktywny w ciągu ~5 minut\\n"
    "- Metody walidacji: automatyczna, e-mail, DNS (propagacja do 4h), HTTPS\\n"
    "- Komunikat 'strona nie w pełni zabezpieczona' = treści mieszane HTTP/HTTPS (mixed content)\\n"
    "- W WordPressie pomaga wtyczka Really Simple SSL\\n"
    "- ERR_TOO_MANY_REDIRECTS po SSL = pętla przekierowań, sprawdź .htaccess i ustawienia CMS\\n\\n"

    "=== DNS I DOMENY ===\\n"
    "- Propagacja rekordów DNS: do 24h (zazwyczaj 4h)\\n"
    "- Propagacja subdomeny: ~4h\\n"
    "- Serwery DNS CyberFolks: ns1.cyberfolks.pl, ns2.cyberfolks.pl, ns3.cyberfolks.pl\\n"
    "- Domena z NS VERIFICATION-HOLD.SUSPENDED-DOMAIN.COM = brak weryfikacji RAA\\n"
    "- Transfer domeny .pl: bezpłatny, natychmiastowy po potwierdzeniu\\n"
    "- Transfer domen globalnych (.com, .net): do 7 dni\\n\\n"

    "=== KOPIE ZAPASOWE ===\\n"
    "- System 4x4: 4 kopie dzienne + 4 kopie tygodniowe\\n"
    "- Kopie dostępne przez 28 dni\\n"
    "- Wykonywane między godziną 00:00 a 06:00\\n\\n"

    "=== SPOSÓB ODPOWIEDZI ===\\n"
    "Zawsze odpowiadaj po polsku, profesjonalnie, zwracając się do klienta per Pan/Pani/Państwo. "
    "Pisz krótko i konkretnie, bez zbędnego żargonu technicznego.\\n\\n"
    "Twoja odpowiedź MUSI zawierać dokładnie te 4 sekcje:\\n\\n"
    "1. CO PRZEDSTAWIA ZDJĘCIE?\\n"
    "Opisz krótko co widać na przesłanym zdjęciu.\\n\\n"
    "2. DIAGNOZA PROBLEMU\\n"
    "Wskaż najbardziej prawdopodobną przyczynę problemu. "
    "Uwzględnij środowisko (LiteSpeed – hosting współdzielony / Apache – VPS), jeśli da się to określić.\\n\\n"
    "3. CO NALEŻY ZROBIĆ – KONKRETNE KROKI\\n"
    "Numerowana lista kroków do wykonania. Jeśli problem wymaga interwencji supportu, wskaż to wyraźnie.\\n\\n"
    "4. DODATKOWE WSKAZÓWKI\\n"
    "Przydatne linki do bazy pomocy CyberFolks lub narzędzi diagnostycznych.\\n\\n"
    "Jeśli zdjęcie nie przedstawia błędu technicznego związanego z hostingiem, "
    "poinformuj o tym uprzejmie i zapytaj o kontekst."
)


@app.get("/health")
async def health():
    return {"status": "running", "service": "ai-bot"}


@app.post("/api/vision")
async def analyze_image(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    if authorization != f"Bearer {SECRET_TOKEN}":
        raise HTTPException(status_code=401, detail="Nieautoryzowany dostep")

    image_data = await file.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    mime_type = file.content_type if file.content_type else "image/jpeg"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Przeanalizuj przesłane zdjęcie i odpowiedz zgodnie z instrukcjami."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1500
    )

    return {
        "status": "ok",
        "analysis": response.choices[0].message.content
    }


import httpx
from pydantic import BaseModel

WP_URL = os.getenv("WP_URL", "http://wordpress_app/wp-json/wp/v2")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")


# --- Modele danych ---

class PostCreate(BaseModel):
    title: str
    content: str
    status: str = "draft"

class PostUpdate(BaseModel):
    post_id: int
    title: str = None
    content: str = None
    status: str = None


# --- Narzędzia WordPress ---

@app.get("/tools/list_posts")
async def list_posts(per_page: int = 10):
    """Pobiera listę ostatnich postów z WordPressa."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{WP_URL}/posts",
            params={"per_page": per_page, "context": "edit"},
            auth=(WP_USER, WP_APP_PASSWORD)
        )
    return r.json()


@app.post("/tools/create_post")
async def create_post(post: PostCreate):
    """Tworzy nowy post w WordPressie."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{WP_URL}/posts",
            json={
                "title": post.title,
                "content": post.content,
                "status": post.status
            },
            auth=(WP_USER, WP_APP_PASSWORD)
        )
    return r.json()


@app.post("/tools/update_post")
async def update_post(post: PostUpdate):
    """Edytuje istniejący post w WordPressie."""
    payload = {k: v for k, v in post.dict().items() if v is not None and k != "post_id"}
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{WP_URL}/posts/{post.post_id}",
            json=payload,
            auth=(WP_USER, WP_APP_PASSWORD)
        )
    return r.json()


@app.delete("/tools/delete_post/{post_id}")
async def delete_post(post_id: int):
    """Usuwa post z WordPressa (przenosi do kosza)."""
    async with httpx.AsyncClient() as client:
        r = await client.delete(
            f"{WP_URL}/posts/{post_id}",
            auth=(WP_USER, WP_APP_PASSWORD)
        )
    return {"status": r.status_code, "post_id": post_id}


# ─── MCP SERVER ───────────────────────────────────────────────
mcp = FastApiMCP(app)
mcp.mount()
