import base64
import os
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Support Bot")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SECRET_TOKEN = os.getenv("API_SECRET_TOKEN")
def verify_token(authorization: str = Header(None)):
    if authorization != f"Bearer {SECRET_TOKEN}":
        raise HTTPException(status_code=401, detail="Nieautoryzowany dostep")
    return True

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
    _: bool = Depends(verify_token)
):
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
import json
from pydantic import BaseModel
from fastapi import Form

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
async def list_posts(per_page: int = 10, _: bool = Depends(verify_token)):
    """Pobiera listę ostatnich postów z WordPressa."""
    async with httpx.AsyncClient() as http:
        r = await http.get(
            f"{WP_URL}/posts",
            params={"per_page": per_page, "context": "edit"},
            auth=(WP_USER, WP_APP_PASSWORD)
        )
    return r.json()


@app.post("/tools/create_post")
async def create_post(post: PostCreate, _: bool = Depends(verify_token)):
    """Tworzy nowy post w WordPressie."""
    async with httpx.AsyncClient() as http:
        r = await http.post(
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
async def update_post(post: PostUpdate, _: bool = Depends(verify_token)):
    """Edytuje istniejący post w WordPressie."""
    payload = {k: v for k, v in post.dict().items() if v is not None and k != "post_id"}
    async with httpx.AsyncClient() as http:
        r = await http.post(
            f"{WP_URL}/posts/{post.post_id}",
            json=payload,
            auth=(WP_USER, WP_APP_PASSWORD)
        )
    return r.json()


@app.delete("/tools/delete_post/{post_id}")
async def delete_post(post_id: int, _: bool = Depends(verify_token)):
    """Usuwa post z WordPressa (przenosi do kosza)."""
    async with httpx.AsyncClient() as http:
        r = await http.delete(
            f"{WP_URL}/posts/{post_id}",
            auth=(WP_USER, WP_APP_PASSWORD)
        )
    return {"status": r.status_code, "post_id": post_id}


# ─── VISION TO POST ───────────────────────────────────────────

VISION_TO_POST_PROMPT = """Przeanalizuj przesłany obraz i zwróć WYŁĄCZNIE obiekt JSON.
Żadnego tekstu przed ani po — tylko czysty JSON.

Struktura którą MUSISZ zwrócić:
{
  "title": "krótki, konkretny tytuł posta (max 10 słów)",
  "content": "treść posta w HTML, minimum 3 akapity, użyj tagów <p>, <ul>, <li>, <strong>",
  "tags": ["tag1", "tag2", "tag3"],
  "excerpt": "jedno zdanie podsumowania (max 160 znaków)"
}

Język: polski. Ton: profesjonalny, pomocny."""


@app.post("/api/vision-to-post")
async def vision_to_post(
    file: UploadFile = File(...),
    status: str = Form("draft"),
    _: bool = Depends(verify_token)
):
    """Analizuje zdjęcie przez GPT-4o i tworzy posta w WordPress."""

    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        raise HTTPException(status_code=400, detail=f"Nieobsługiwany format pliku: {file.content_type}")

    image_data = await file.read()

    if len(image_data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Plik za duży. Maksymalny rozmiar to 20MB.")

    image_base64 = base64.b64encode(image_data).decode("utf-8")
    mime_type = file.content_type

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": VISION_TO_POST_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Przeanalizuj ten obraz i zwróć JSON zgodnie z instrukcją."
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
        max_tokens=2000
    )

    try:
        post_data = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="GPT-4o zwrócił nieprawidłowy JSON.")

    async with httpx.AsyncClient() as http:
        wp_response = await http.post(
            f"{WP_URL}/posts",
            json={
                "title":   post_data.get("title", "Post bez tytułu"),
                "content": post_data.get("content", ""),
                "excerpt": post_data.get("excerpt", "")[:160],
                "status":  status
            },
            auth=(WP_USER, WP_APP_PASSWORD),
            timeout=30.0
        )

    if wp_response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=502,
            detail=f"WordPress zwrócił błąd: {wp_response.status_code}"
        )

    wp_data = wp_response.json()

    return {
        "success": True,
        "action": "vision_to_post",
        "data": {
            "post_id":  wp_data.get("id"),
            "post_url": wp_data.get("link"),
            "status":   status,
            "preview":  post_data
        }
    }


# ─── MCP SERVER ───────────────────────────────────────────────
mcp = FastApiMCP(app)
mcp.mount()


# ─── TEXT COMMAND ─────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel

class TextCommand(_BaseModel):
    prompt: str


WEBMASTER_PROMPT = """
Jesteś profesjonalnym webmasterem i web designerem z 10-letnim doświadczeniem,
specjalizującym się w WordPress. Tworzysz nowoczesne, w pełni responsywne
komponenty HTML+CSS dla stron WordPress na podstawie poleceń użytkownika.

=== ŚRODOWISKO PRACY ===
- Pracujesz wewnątrz edytora WordPress (Gutenberg lub Classic Editor)
- Kod będzie wklejany bezpośrednio do bloku "Własny HTML" (Custom HTML)
- Strona może mieć już załadowany motyw z własnymi stylami - unikaj konfliktów
- NIE używaj: <?php ?>, shortcode'ów, zewnętrznych skryptów jQuery (już załadowany w WP)
- Jeśli potrzebujesz JS - używaj vanilla JS lub window.jQuery (nie $())
- Każda sekcja musi być self-contained (działać bez zależności zewnętrznych)
- NIE nadpisuj globalnych zmiennych CSS motywu - używaj własnych z prefiksem --wm-

=== ZASADY PROJEKTOWANIA ===
- Mobile-first: breakpointy @media (max-width: 768px) i @media (max-width: 480px)
- CSS custom properties z prefiksem --wm- (np. --wm-primary, --wm-bg)
- Unikalne klasy CSS z prefiksem (np. .wm-hero, .wm-card) - zapobiega konfliktom z motywem
- Animacje przez @keyframes i transition (płynne, nie przesadzone, respektuj prefers-reduced-motion)
- Semantyczny HTML5: <section>, <article>, <header>, <nav>, <footer>
- Wszystkie style jako <style> na początku bloku HTML
- Obrazki: zawsze loading="lazy", alt="" wypełniony opisem, width i height podane
- Dostępność (a11y): role ARIA gdzie potrzeba, kontrast min. 4.5:1, focus-visible

=== DOBÓR STYLU DO KONTEKSTU ===
Nie stosujesz trendów "na siłę" - dobierasz styl do treści i celu sekcji:
- Landing / hero: gradient mesh + animacje wejścia
- Blog / artykuł: czysta typografia, dużo białej przestrzeni
- Portfolio: glassmorphism, ciemne tło, efekty hover
- Sklep / oferta: karty produktów, CTA wyraźne, zaufanie (ikony, liczby)
- Kontakt / formularz: minimalizm, czytelność, walidacja inline

Gdy stosujesz:
- Glassmorphism: backdrop-filter: blur(10px); background: rgba(255,255,255,0.1); tylko na ciemnych tłach
- Gradienty: linear-gradient lub mesh, spójne z paletą strony
- Animacje wejścia: fadeInUp, slideInLeft - tylko raz przy ładowaniu (IntersectionObserver)
- Micro-interactions: transform: translateY(-4px); box-shadow na hover
- Typografia: Google Fonts (Inter, Poppins, Plus Jakarta Sans) - ładuj tylko potrzebne wagi
- Dark mode: @media (prefers-color-scheme: dark)
- Layout: CSS Grid dla siatek, Flexbox dla komponentów
- Karty: border-radius: 16px-24px, box-shadow: 0 8px 32px rgba(0,0,0,0.12)

=== OBSŁUGA POLECEŃ ===
- Jeśli polecenie jest niejasne: zrealizuj najbardziej prawdopodobną interpretację
  i dodaj krótki komentarz HTML na początku kodu
- Jeśli brakuje treści (np. "dodaj sekcję z zespołem" bez nazwisk): użyj realistycznych
  danych placeholder, które użytkownik łatwo zastąpi (oznacz je: <!-- PLACEHOLDER -->)
- Jeśli polecenie dotyczy funkcji niemożliwej w czystym HTML/CSS: zaproponuj
  alternatywę i wyjaśnij w komentarzu HTML

=== FORMAT ODPOWIEDZI ===
Zwracasz WYŁĄCZNIE czysty HTML gotowy do wklejenia w WordPress.
- Żadnego markdownu, żadnych bloków ```html - tylko surowy kod
- Żadnych wyjaśnień poza komentarzami HTML wewnątrz kodu
- Kod musi działać standalone z wbudowanymi stylami
- Struktura: najpierw <style>, potem HTML, opcjonalnie <script> na końcu
- Skrypty tylko gdy niezbędne; używaj defer lub umieszczaj na końcu bloku
"""

ROUTER_PROMPT = """
Jesteś routerem akcji dla agenta WordPress. Analizujesz polecenie użytkownika
i zwracasz WYŁĄCZNIE jeden obiekt JSON - zero tekstu poza nim.

=== DOSTĘPNE AKCJE ===

1. create_post
   Kiedy: "napisz post", "opublikuj artykuł", "dodaj wpis na blogu"
   {"action":"create_post","title":"tytuł","content":"HTML","excerpt":"opis SEO (max 160 znaków)","tags":["tag1","tag2"],"status":"publish lub draft"}

2. create_page
   Kiedy: "utwórz stronę", "zrób nową podstronę", "dodaj stronę O nas"
   {"action":"create_page","title":"tytuł","content":"HTML","excerpt":"opis","parent_slug":"slug-rodzica lub null"}

3. append_section
   Kiedy: "dodaj sekcję DO strony X", "dopisz baner na stronę X", "dodaj hero na stronę X"
   WYMAGA podania nazwy/sluga istniejącej strony w poleceniu.
   {"action":"append_section","page_slug":"slug-strony","design_description":"pełny opis co zaprojektować","position":"bottom lub top"}

4. update_content
   Kiedy: "zmień", "edytuj", "zaktualizuj", "popraw", "zastąp", "usuń fragment"
   {"action":"update_content","resource_type":"pages lub posts","resource_slug":"slug","edit_instruction":"precyzyjny opis zmiany"}

5. design_section
   Kiedy: polecenie dotyczy STWORZENIA komponentu bez wskazania konkretnej istniejącej strony,
   lub gdy użytkownik chce zobaczyć projekt przed opublikowaniem.
   Przykłady: "zaprojektuj sekcję hero", "stwórz nowoczesną kartę produktu", "zrób responsywny cennik"
   {"action":"design_section","description":"pełny opis do zaprojektowania","page_slug":"slug lub null"}

6. delete_content
   Kiedy: "usuń stronę", "skasuj post", "wyczyść treść strony X"
   {"action":"delete_content","resource_type":"pages lub posts","resource_slug":"slug","mode":"delete lub clear_content"}

7. unknown
   Kiedy: polecenie jest niezrozumiałe, zbyt ogólne lub nie dotyczy zarządzania stroną WP.
   {"action":"unknown","reason":"krótkie wyjaśnienie po polsku czego brakuje","suggestion":"co użytkownik powinien doprecyzować"}

=== ZASADY WYBORU AKCJI ===
- Jeśli polecenie zawiera "strona X" + "dodaj/dopisz" -> append_section (nie design_section)
- Jeśli brak wskazania konkretnej strony + "zaprojektuj/stwórz/zrób" -> design_section
- Jeśli polecenie zawiera "zmień/edytuj/popraw" -> update_content
- Jeśli nie jesteś pewien między dwiema akcjami -> wybierz bardziej bezpieczną (nie delete, nie publish)
- status domyślny dla nowych treści: "draft"
- Slug generuj z tytułu: małe litery, myślniki zamiast spacji, bez polskich znaków

=== OBSŁUGA PRZYPADKÓW GRANICZNYCH ===
Polecenie niejasne ale interpretowalne:
-> Wybierz najbardziej prawdopodobną akcję i dodaj pole "assumption": "krótki opis co założyłem"

Brak sluga strony przy append_section:
-> Zwróć unknown z prośbą o podanie nazwy strony

Polecenie dotyczy wielu akcji naraz:
-> Wybierz główną akcję, dodaj "note": "opis co wykonano jako jedna akcja"

=== PRZYKŁADY ===
"Dodaj sekcję z zespołem na stronę O nas"
-> {"action":"append_section","page_slug":"o-nas","design_description":"sekcja z zespołem, 3 osoby, karty z avatarem i opisem","position":"bottom"}

"Zaprojektuj nowoczesny cennik z trzema planami"
-> {"action":"design_section","description":"nowoczesny cennik z trzema planami cenowymi","page_slug":null}

"Napisz coś fajnego"
-> {"action":"unknown","reason":"Polecenie jest zbyt ogólne","suggestion":"Podaj typ treści (post/strona), temat oraz gdzie ma się pojawić"}

Zwróć TYLKO JSON. Zero tekstu przed ani po.
"""


@app.post("/api/text-command")
async def text_command(
    command: TextCommand,
    _: bool = Depends(verify_token)
):
    router_response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user",   "content": command.prompt}
        ],
        max_tokens=2000
    )

    try:
        decision = json.loads(router_response.choices[0].message.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM zwrocil nieprawidlowy JSON.")

    action = decision.get("action")

    async with httpx.AsyncClient() as http:

        if action == "create_post":
            r = await http.post(
                f"{WP_URL}/posts",
                json={
                    "title":   decision.get("title", "Nowy post"),
                    "content": decision.get("content", ""),
                    "excerpt": decision.get("excerpt", "")[:160],
                    "status":  decision.get("status", "draft")
                },
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30.0
            )
            if r.status_code not in [200, 201]:
                raise HTTPException(status_code=502, detail=f"WordPress blad: {r.status_code}")
            wp = r.json()
            return {"success": True, "data": {
                "action": "create_post",
                "action_label": "Post utworzony!",
                "message": f"Utworzono szkic: {decision.get('title')}",
                "url": wp.get("link"),
                "post_id": wp.get("id")
            }}

        elif action == "create_page":
            r = await http.post(
                f"{WP_URL}/pages",
                json={
                    "title":   decision.get("title", "Nowa strona"),
                    "content": decision.get("content", ""),
                    "excerpt": decision.get("excerpt", "")[:160],
                    "status":  decision.get("status", "draft")
                },
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30.0
            )
            if r.status_code not in [200, 201]:
                raise HTTPException(status_code=502, detail=f"WordPress blad: {r.status_code}")
            wp = r.json()
            return {"success": True, "data": {
                "action": "create_page",
                "action_label": "Podstrona utworzona!",
                "message": f"Utworzono podstronę: {decision.get('title')}",
                "url": wp.get("link"),
                "page_id": wp.get("id")
            }}

        elif action == "append_section":
            page_slug   = decision.get("page_slug", "")
            design_desc = decision.get("design_description", "")
            position    = decision.get("position", "bottom")

            # Krok 1: WEBMASTER generuje HTML na podstawie opisu
            design_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": WEBMASTER_PROMPT},
                    {"role": "user",   "content": design_desc}
                ],
                max_tokens=4000
            )
            section_html = design_resp.choices[0].message.content.strip()

            # Krok 2: Pobierz istniejącą stronę z WP
            r = await http.get(
                f"{WP_URL}/pages",
                params={"slug": page_slug, "context": "edit"},
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30.0
            )
            pages = r.json()
            if not pages or not isinstance(pages, list) or len(pages) == 0:
                raise HTTPException(status_code=404, detail=f"Nie znaleziono strony: {page_slug}")

            page            = pages[0]
            page_id         = page.get("id")
            current_content = page.get("content", {}).get("raw", "")
            new_block       = f'\n<!-- wp:html -->\n{section_html}\n<!-- /wp:html -->'

            # Krok 3: top lub bottom
            if position == "top":
                updated_content = new_block + "\n" + current_content
            else:
                updated_content = current_content + new_block

            r2 = await http.post(
                f"{WP_URL}/pages/{page_id}",
                json={"content": updated_content},
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30.0
            )
            if r2.status_code not in [200, 201]:
                raise HTTPException(status_code=502, detail=f"WordPress blad: {r2.status_code}")
            wp = r2.json()
            return {"success": True, "data": {
                "action": "append_section",
                "action_label": "Sekcja dodana!",
                "message": f"Zaprojektowano i dodano sekcję do strony '{page_slug}' ({position}).",
                "url": wp.get("link"),
                "page_id": page_id
            }}

        elif action == "design_section":
            description = decision.get("description", "")
            page_slug   = decision.get("page_slug")

            # Webmaster generuje czysty HTML
            design_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": WEBMASTER_PROMPT},
                    {"role": "user",   "content": description}
                ],
                max_tokens=4000
            )
            generated_html = design_resp.choices[0].message.content.strip()

            # Jeśli podano stronę — dołącz do niej
            if page_slug:
                r = await http.get(
                    f"{WP_URL}/pages",
                    params={"slug": page_slug, "context": "edit"},
                    auth=(WP_USER, WP_APP_PASSWORD),
                    timeout=30.0
                )
                pages = r.json()
                if not pages:
                    raise HTTPException(status_code=404, detail=f"Strona '{page_slug}' nie istnieje.")
                page_id         = pages[0]["id"]
                current_content = pages[0]["content"]["raw"]
                new_block       = f'\n<!-- wp:html -->\n{generated_html}\n<!-- /wp:html -->'
                r2 = await http.post(
                    f"{WP_URL}/pages/{page_id}",
                    json={"content": current_content + new_block},
                    auth=(WP_USER, WP_APP_PASSWORD),
                    timeout=30.0
                )
                wp = r2.json()
                return {"success": True, "data": {
                    "action": "design_section",
                    "action_label": "Sekcja zaprojektowana i dodana!",
                    "message": f"Sekcja dodana do strony '{page_slug}'.",
                    "url": wp.get("link")
                }}

            # Jeśli nie podano strony — zwróć sam HTML
            return {"success": True, "data": {
                "action": "design_section",
                "action_label": "Projekt gotowy!",
                "message": "Nie podano strony docelowej — zwracam wygenerowany HTML.",
                "generated_html": generated_html
            }}

        elif action == "update_content":
            resource_type    = decision.get("resource_type", "pages")
            resource_slug    = decision.get("resource_slug", "")
            edit_instruction = decision.get("edit_instruction", "")

            r = await http.get(
                f"{WP_URL}/{resource_type}",
                params={"slug": resource_slug, "context": "edit"},
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30.0
            )
            resources = r.json()
            if not resources or not isinstance(resources, list) or len(resources) == 0:
                raise HTTPException(status_code=404, detail=f"Nie znaleziono zasobu: {resource_slug}")

            resource        = resources[0]
            resource_id     = resource.get("id")
            current_content = resource.get("content", {}).get("raw", "")
            current_title   = resource.get("title", {}).get("rendered", "")

            edit_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Jesteś edytorem treści WordPress. "
                            "Otrzymasz aktualną treść strony w HTML oraz instrukcję co zmienić. "
                            "Zwróć TYLKO poprawiony HTML - bez komentarzy, bez markdown, bez wyjaśnień. "
                            "Zachowaj istniejące bloki Gutenberga jeśli są. "
                            "Język: polski."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Instrukcja: {edit_instruction}\n\n"
                            f"Aktualna treść:\n{current_content}"
                        )
                    }
                ],
                max_tokens=3000
            )

            new_content = edit_response.choices[0].message.content

            r2 = await http.post(
                f"{WP_URL}/{resource_type}/{resource_id}",
                json={"content": new_content},
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30.0
            )
            if r2.status_code not in [200, 201]:
                raise HTTPException(status_code=502, detail=f"WordPress blad: {r2.status_code}")

            wp = r2.json()
            return {"success": True, "data": {
                "action": "update_content",
                "action_label": "Treść zaktualizowana!",
                "message": f"Zaktualizowano: {current_title}",
                "url": wp.get("link"),
                "resource_id": resource_id
            }}

        elif action == "delete_content":
            resource_type = decision.get("resource_type", "pages")
            resource_slug = decision.get("resource_slug", "")
            mode          = decision.get("mode", "clear_content")

            r = await http.get(
                f"{WP_URL}/{resource_type}",
                params={"slug": resource_slug, "context": "edit"},
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30.0
            )
            items = r.json()
            if not items or not isinstance(items, list):
                raise HTTPException(status_code=404, detail=f"Nie znaleziono: {resource_slug}")

            item_id = items[0]["id"]

            if mode == "clear_content":
                # Bezpieczny tryb: tylko czyści treść, nie usuwa strony/posta
                await http.post(
                    f"{WP_URL}/{resource_type}/{item_id}",
                    json={"content": ""},
                    auth=(WP_USER, WP_APP_PASSWORD),
                    timeout=30.0
                )
                return {"success": True, "data": {
                    "action": "delete_content",
                    "action_label": "Treść wyczyszczona",
                    "message": f"Wyczyszczono treść: {resource_slug} (strona/post nadal istnieje)."
                }}
            else:
                # Tryb delete: przenosi do kosza WP
                await http.delete(
                    f"{WP_URL}/{resource_type}/{item_id}",
                    auth=(WP_USER, WP_APP_PASSWORD),
                    timeout=30.0
                )
                return {"success": True, "data": {
                    "action": "delete_content",
                    "action_label": "Usunięto!",
                    "message": f"Przeniesiono do kosza: {resource_slug}."
                }}

        elif action == "unknown":
            return {"success": False, "data": {
                "action": "unknown",
                "action_label": "Nie rozumiem polecenia",
                "message": decision.get("reason", "Polecenie niezrozumiałe."),
                "suggestion": decision.get("suggestion", "Spróbuj sformułować polecenie bardziej precyzyjnie.")
            }}

        else:
            raise HTTPException(status_code=400, detail=f"Nieznana akcja: {action}")
