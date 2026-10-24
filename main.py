# Wymagane przez spakowaną aplikację (.exe): okno aplikacji działa w osobnym procesie
from multiprocessing import freeze_support  # noqa: E402
freeze_support()

import re  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

from app.sciezki import FOLDER_DANYCH  # noqa: E402

# Spakowana aplikacja bez konsoli nie ma gdzie wypisywać komunikatów,
# więc kierujemy je do pliku diploma.log w folderze danych (przydaje się przy szukaniu błędów)
if sys.stdout is None or sys.stderr is None:
    _log = open(FOLDER_DANYCH / "diploma.log", "w", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log

from nicegui import ui, run, native, app as aplikacja  # noqa: E402
from app import klucz_api, projekt, asystent, historia, baza_wiedzy, wymagania, szablony, zalaczniki, koszty, ustawienia  # noqa: E402

# Folder z ikoną: przy pisaniu leży obok main.py, w spakowanej aplikacji w folderze PyInstallera
FOLDER_APLIKACJI = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
FOLDER_STATIC = FOLDER_APLIKACJI / "static"
aplikacja.add_static_files("/static", FOLDER_STATIC)

# Pozycje menu: (nazwa, ikona, adres)
MENU = [
    ("Asystent", "chat_bubble_outline", "/"),
    ("Mój projekt", "school", "/projekt"),
    ("Wymagania uczelni", "rule", "/wymagania"),
    ("Źródła", "menu_book", "/zrodla"),
]

# =====================================================================
# WYGLĄD: kolory, czcionki, animacje
# =====================================================================

KOLOR_GLOWNY = "#2B4C7E"   # granat (przyciski, akcenty)
KOLOR_AKCENTU = "#C9A227"  # złoty

TRYBY = {  # nazwa trybu: (wartość dla ui.dark_mode, ikona, podpowiedź)
    "auto": (None, "brightness_auto", "Motyw: jak w systemie"),
    "jasny": (False, "light_mode", "Motyw: jasny"),
    "ciemny": (True, "dark_mode", "Motyw: ciemny"),
}

CSS = """
/* ---------- kolory dla trybu jasnego i ciemnego ---------- */
:root { --akcent: #2B4C7E; }
.body--light {
  --bg: #FFFFFF; --bg-boczny: #F9F9F9; --tekst: #0D0D0D; --tekst-2: #6B6B6B;
  --linia: #E8E8E8; --pole: #F4F4F4; --dymek: #F1F1F1; --hover: #ECECEC;
  --cien: 0 8px 32px rgba(0,0,0,.08);
}
.body--dark {
  --bg: #212121; --bg-boczny: #171717; --tekst: #ECECEC; --tekst-2: #A3A3A3;
  --linia: #303030; --pole: #2F2F2F; --dymek: #2F2F2F; --hover: #2A2A2A;
  --cien: 0 8px 32px rgba(0,0,0,.45);
}

/* ---------- podstawy ---------- */
body {
  background: var(--bg) !important; color: var(--tekst);
  font-family: "Segoe UI Variable", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
body, .q-drawer, .naglowek, .q-card, .pasek-wiadomosci {
  transition: background-color .3s ease, color .3s ease, border-color .3s ease;
}
.nicegui-content { padding: 0 !important; }
.przytlumiony { color: var(--tekst-2); }
.q-card { background: var(--bg) !important; color: var(--tekst); border: 1px solid var(--linia);
          border-radius: 16px !important; box-shadow: none !important; }
.q-btn { transition: transform .15s ease, background-color .15s ease, opacity .2s ease; }
.q-btn:active { transform: scale(.96); }

/* ---------- pasek boczny ---------- */
.q-drawer { background: var(--bg-boczny) !important; }
.q-drawer--left.q-drawer--bordered { border-right: 1px solid var(--linia) !important; }
.pozycja {
  display: flex; align-items: center; gap: 10px; width: 100%;
  padding: 8px 10px; border-radius: 10px; cursor: pointer; font-size: 14px;
  color: var(--tekst); transition: background-color .15s ease;
}
.pozycja:hover { background: var(--hover); }
.pozycja.aktywna { background: var(--hover); font-weight: 600; }
.pozycja .usun { opacity: 0; transition: opacity .15s ease; }
.pozycja:hover .usun { opacity: .65; }
.pozycja .usun:hover { opacity: 1; }
.tytul-rozmowy { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.etykieta-sekcji { font-size: 12px; font-weight: 600; color: var(--tekst-2); padding: 14px 10px 4px; }
.przycisk-nowa { border: 1px solid var(--linia); border-radius: 12px; }

/* ---------- nagłówek ze "szklanym" efektem ---------- */
.naglowek {
  background: color-mix(in srgb, var(--bg) 80%, transparent) !important;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  color: var(--tekst) !important; border-bottom: 1px solid var(--linia);
}

/* ---------- animacje ---------- */
@keyframes wejscie { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.wejscie { animation: wejscie .35s cubic-bezier(.2,.7,.3,1) both; }

@keyframes kropka { 0%, 80%, 100% { opacity: .25; transform: scale(.75); } 40% { opacity: 1; transform: scale(1); } }
.kropki { display: flex; gap: 5px; padding: 8px 0; }
.kropki span { width: 8px; height: 8px; border-radius: 50%; background: var(--tekst-2);
               animation: kropka 1.4s infinite ease-in-out; }
.kropki span:nth-child(2) { animation-delay: .2s; }
.kropki span:nth-child(3) { animation-delay: .4s; }

@keyframes puls { 0%, 100% { opacity: .45; } 50% { opacity: 1; } }
.krok { font-size: 12.5px; color: var(--tekst-2); display: flex; align-items: center; gap: 6px; }
.krok .q-icon { animation: puls 1.5s infinite; }

/* ---------- czat ---------- */
.dymek-uzytkownika { background: var(--dymek); color: var(--tekst); border-radius: 22px;
                     padding: 10px 18px; max-width: 75%; }
.wiadomosc-asystenta { font-size: 15px; line-height: 1.7; }
.wiadomosc-asystenta .akcje { opacity: 0; transition: opacity .2s ease; }
.wiadomosc-asystenta:hover .akcje { opacity: 1; }
.nicegui-markdown p:last-child { margin-bottom: 0; }
.nicegui-markdown pre { background: var(--pole); border-radius: 12px; padding: 14px 16px;
                        overflow-x: auto; font-size: 13px; }
.nicegui-markdown code { font-family: "Cascadia Code", "SF Mono", Consolas, monospace; }
.nicegui-markdown table { border-collapse: collapse; }
.nicegui-markdown th, .nicegui-markdown td { border: 1px solid var(--linia); padding: 6px 10px; }

/* ---------- pole wiadomości ---------- */
.pasek-wiadomosci {
  background: var(--pole); border: 1px solid var(--linia); border-radius: 28px;
  box-shadow: var(--cien); padding: 6px 8px 6px 6px; transition: box-shadow .2s ease;
}
.pasek-wiadomosci:focus-within {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--akcent) 45%, transparent), var(--cien);
}
.pasek-wiadomosci textarea { font-size: 15px !important; color: var(--tekst) !important; }
.przycisk-wyslij { background: var(--tekst) !important; color: var(--bg) !important; }
.przycisk-wyslij:hover { transform: scale(1.07); }
.etykieta { background: color-mix(in srgb, var(--akcent) 14%, transparent); border-radius: 999px; }

/* ---------- ekran powitalny ---------- */
.gradient {
  background: linear-gradient(92deg, #2B4C7E 0%, #6D5BD0 50%, #C9A227 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.karta-propozycji {
  border: 1px solid var(--linia); border-radius: 16px; padding: 14px 16px; cursor: pointer;
  background: var(--bg); transition: transform .18s ease, box-shadow .18s ease, background-color .18s ease;
}
.karta-propozycji:hover { transform: translateY(-3px); box-shadow: var(--cien); background: var(--hover); }

/* ---------- pozostałe strony ---------- */
.strona { max-width: 860px; margin: 0 auto; padding: 28px 20px 48px; }

/* ---------- cienki pasek przewijania ---------- */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: var(--linia); border-radius: 8px; }
::-webkit-scrollbar-track { background: transparent; }
"""


def motyw():
    """Kolory, CSS i tryb jasny/ciemny. Wywoływane na każdej stronie."""
    ui.colors(primary=KOLOR_GLOWNY, secondary="#5B7DB1", accent=KOLOR_AKCENTU,
              positive="#2E7D32", negative="#C62828", warning="#D97706")
    ui.add_css(CSS)
    tryb = ustawienia.wczytaj().get("motyw", "auto")
    return ui.dark_mode(TRYBY.get(tryb, TRYBY["auto"])[0]), tryb


def uklad(tytul, adres_strony, w_naglowku=None):
    """Wspólny wygląd każdej strony: pasek boczny z rozmowami + nagłówek."""
    ciemny, tryb = motyw()

    # ---------- funkcje paska bocznego ----------

    def nowa_rozmowa():
        asystent.aktywna_rozmowa = None
        ui.navigate.to("/")

    def otworz_rozmowe(id_rozmowy):
        asystent.aktywna_rozmowa = id_rozmowy
        ui.navigate.to("/")

    def usun_rozmowe(id_rozmowy, tytul_rozmowy):
        with ui.dialog() as okno, ui.card().classes("q-pa-lg"):
            ui.label("Usunąć rozmowę?").classes("text-h6")
            ui.label(f"„{tytul_rozmowy}” zostanie usunięta na zawsze.").classes("przytlumiony")
            with ui.row().classes("w-full justify-end q-mt-md"):
                ui.button("Anuluj", on_click=okno.close, color=None).props("flat no-caps")

                def potwierdz():
                    historia.usun_rozmowe(id_rozmowy)
                    if asystent.aktywna_rozmowa == id_rozmowy:
                        asystent.aktywna_rozmowa = None
                    okno.close()
                    ui.navigate.to(adres_strony)

                ui.button("Usuń", on_click=potwierdz, color="negative").props("unelevated no-caps")
        okno.open()

    def zmien_tryb():
        kolejnosc = list(TRYBY)
        nowy = kolejnosc[(kolejnosc.index(stan["tryb"]) + 1) % len(kolejnosc)]
        stan["tryb"] = nowy
        ustawienia.ustaw("motyw", nowy)
        wartosc, ikona, podpowiedz = TRYBY[nowy]
        ciemny.value = wartosc
        przycisk_trybu.props(f"icon={ikona}")
        ui.notify(podpowiedz)

    stan = {"tryb": tryb}

    # ---------- pasek boczny ----------

    with ui.left_drawer(value=True, bordered=True).props("width=272") as menu:
        with ui.column().classes("w-full h-full no-wrap gap-1 q-pa-sm"):
            with ui.row().classes("w-full items-center no-wrap gap-3 q-px-xs q-pt-xs q-pb-sm"):
                ui.image("/static/ikona.png").classes("w-8 h-8 rounded-lg")
                ui.label("Diploma").classes("text-subtitle1 text-weight-bold")
                ui.space()
                ui.button(icon="menu_open", on_click=menu.hide, color=None).props("flat round dense").tooltip("Ukryj panel")

            ui.button("Nowa rozmowa", icon="edit_note", on_click=nowa_rozmowa, color=None) \
                .props("flat no-caps align=left").classes("w-full przycisk-nowa q-mb-sm")

            for nazwa, ikona, adres in MENU:
                klasy = "pozycja aktywna" if adres == adres_strony else "pozycja"
                with ui.element("div").classes(klasy).on("click", lambda a=adres: ui.navigate.to(a)):
                    ui.icon(ikona, size="20px")
                    ui.label(nazwa)

            ui.label("Rozmowy").classes("etykieta-sekcji")

            @ui.refreshable
            def lista_rozmow():
                rozmowy = historia.lista_rozmow()
                if not rozmowy:
                    ui.label("Tu pojawią się Twoje rozmowy.").classes("text-caption przytlumiony q-px-sm")
                for r in rozmowy:
                    aktywna = adres_strony == "/" and r["id"] == asystent.aktywna_rozmowa
                    with ui.element("div").classes("pozycja aktywna wejscie" if aktywna else "pozycja") \
                            .on("click", lambda i=r["id"]: otworz_rozmowe(i)):
                        ui.label(r["tytul"]).classes("tytul-rozmowy")
                        ui.icon("delete_outline", size="18px").classes("usun") \
                            .on("click.stop", lambda i=r["id"], t=r["tytul"]: usun_rozmowe(i, t)) \
                            .tooltip("Usuń rozmowę")

            with ui.column().classes("w-full col scroll no-wrap gap-0"):
                lista_rozmow()

            ui.separator().classes("q-my-xs")
            with ui.row().classes("w-full items-center no-wrap gap-1"):
                klasy = "pozycja aktywna" if adres_strony == "/ustawienia" else "pozycja"
                with ui.element("div").classes(klasy).on("click", lambda: ui.navigate.to("/ustawienia")):
                    ui.icon("settings", size="20px")
                    ui.label("Ustawienia")
                przycisk_trybu = ui.button(icon=TRYBY[tryb][1], on_click=zmien_tryb, color=None) \
                    .props("flat round dense").tooltip("Zmień motyw: auto / jasny / ciemny")
            limit = ustawienia.limit()
            ui.label(
                f"Ten miesiąc: ${koszty.suma_miesiac():.2f}" + (f" / ${limit:.2f}" if limit else "")
            ).classes("text-caption przytlumiony q-px-sm")

    # ---------- nagłówek ----------

    with ui.header(elevated=False).classes("naglowek items-center q-py-xs q-px-md no-wrap"):
        ui.button(icon="menu", on_click=menu.toggle, color=None).props("flat round dense").tooltip("Pokaż / ukryj panel")
        etykieta_tytulu = ui.label(tytul).classes("text-subtitle1 text-weight-medium ellipsis")
        ui.space()
        if w_naglowku:
            w_naglowku()

    # Strona może potem odświeżyć listę rozmów i zmienić tytuł w nagłówku
    return lista_rozmow.refresh, etykieta_tytulu


def jest_klucz():
    """Jeśli nie ma klucza, odeślij na ekran klucza."""
    if not klucz_api.wczytaj_klucz():
        ui.navigate.to("/klucz")
        return False
    return True


# Załącznik w wiadomości wygląda tak: <zalacznik nazwa="plik">...treść...</zalacznik>
WZOR_ZALACZNIKA = re.compile(r'\s*<zalacznik nazwa="([^"]+)">.*?</zalacznik>', re.S)


def do_wyswietlenia(tresc):
    """Na ekranie zamiast całej treści załącznika pokazujemy tylko jego nazwę."""
    nazwy = WZOR_ZALACZNIKA.findall(tresc)
    tekst = WZOR_ZALACZNIKA.sub("", tresc).strip()
    if nazwy:
        tekst += "\n\n" + "  ".join(f"📎 {n}" for n in nazwy)
    return tekst


# Karty na ekranie powitalnym: (ikona, tytuł, opis, treść wstawiana do pola)
PROPOZYCJE = [
    ("lightbulb", "Co dalej?", "Plan kolejnych kroków w pracy",
     "Przypomnij mi, o czym jest moja praca, i zaproponuj, co powinienem zrobić w następnej kolejności."),
    ("rule", "Wymogi formatowania", "Czcionka, marginesy, cytowanie",
     "Jakie są wymogi formatowania i cytowania w mojej pracy? Podaj źródła."),
    ("travel_explore", "Przeszukaj źródła", "Co mówią moje materiały",
     "Co moje materiały źródłowe mówią na temat: [temat]? Podaj źródła."),
    ("rate_review", "Recenzja rozdziału", "Załącz rozdział przez + i oceń go",
     szablony.SZABLONY[0][2]),
]


# =====================================================================
# ASYSTENT (czat)
# =====================================================================

@ui.page("/")
def strona_asystenta():
    if not jest_klucz():
        return

    rozmowy = {r["id"]: r["tytul"] for r in historia.lista_rozmow()}
    if asystent.aktywna_rozmowa not in rozmowy:
        asystent.aktywna_rozmowa = None

    def naglowek_czatu():
        ui.select(
            koszty.NAZWY_MODELI, value=ustawienia.model(),
            on_change=lambda e: ustawienia.ustaw("model", e.value),
        ).props("dense borderless options-dense").classes("w-24") \
            .tooltip("Model: Sonnet na co dzień, Opus do trudnych zadań (2× droższy)")
        ui.button(icon="info", on_click=lambda: okno_wiedzy.open(), color=None) \
            .props("flat round dense").tooltip("Co asystent wie o Twojej pracy")

    odswiez_panel, etykieta_tytulu = uklad(rozmowy.get(asystent.aktywna_rozmowa, "Nowa rozmowa"), "/", naglowek_czatu)

    with ui.column().classes("w-full h-[calc(100vh-52px)] no-wrap items-center gap-0"):
        with ui.scroll_area().classes("w-full col") as obszar:
            wiadomosci = ui.column().classes("w-full max-w-3xl mx-auto gap-6 q-px-md q-py-lg")

        with ui.column().classes("w-full max-w-3xl q-px-md q-pb-md gap-1"):
            # Załączone pliki, czekające na wysłanie
            wiersz_zalacznikow = ui.row().classes("w-full gap-2 q-px-sm")

            with ui.row().classes("pasek-wiadomosci w-full items-end no-wrap gap-1"):
                with ui.button(icon="add", color=None).props("flat round dense").tooltip("Załącz plik albo użyj szablonu"):
                    with ui.menu():
                        ui.menu_item("Załącz plik (rozdział, kod...)", on_click=lambda: okno_zalacznika.open())
                        ui.separator()
                        for nazwa, _ikona, tresc in szablony.SZABLONY:
                            ui.menu_item(nazwa, on_click=lambda t=tresc: wstaw_szablon(t))
                pole = ui.textarea(placeholder="Zapytaj o swoją pracę...") \
                    .props('borderless autogrow input-style="max-height: 200px"').classes("col q-px-sm")
                przycisk = ui.button(icon="arrow_upward").props("round unelevated dense").classes("przycisk-wyslij")

            info = ui.label("Enter wysyła · Shift+Enter nowa linia").classes("text-caption przytlumiony text-center w-full")

    # Pliki załączone do następnej wiadomości: lista {"nazwa": ..., "tekst": ...}
    dolaczone = []

    # ---------- wiadomości ----------

    def dodaj_akcje(akcje, tekst):
        """Przycisk kopiowania pod odpowiedzią (widoczny po najechaniu myszką)."""
        with akcje:
            def kopiuj():
                ui.clipboard.write(tekst)
                ui.notify("Skopiowano do schowka")
            ui.button(icon="content_copy", on_click=kopiuj, color=None) \
                .props("flat round dense size=sm").tooltip("Kopiuj odpowiedź")

    def dymek_asystenta():
        """Tworzy pustą wiadomość asystenta. Zwraca jej części do wypełnienia."""
        with wiadomosci:
            with ui.row().classes("w-full no-wrap items-start gap-3 wejscie wiadomosc-asystenta"):
                ui.image("/static/ikona.png").classes("w-7 h-7 rounded-full q-mt-xs")
                with ui.column().classes("col gap-1 min-w-0"):
                    kroki = ui.column().classes("gap-1")
                    with ui.element("div").classes("kropki") as kropki:
                        for _ in range(3):
                            ui.element("span")
                    odp = ui.markdown().classes("w-full")
                    miejsce_na_zrodla = ui.column().classes("w-full")
                    akcje = ui.row().classes("akcje gap-0")
        return kroki, kropki, odp, miejsce_na_zrodla, akcje

    def dymek_uzytkownika(tekst):
        with wiadomosci:
            with ui.row().classes("w-full justify-end wejscie"):
                with ui.element("div").classes("dymek-uzytkownika"):
                    ui.markdown(do_wyswietlenia(tekst))

    def ekran_powitalny():
        with wiadomosci:
            with ui.column().classes("w-full items-center gap-2 q-pt-xl wejscie"):
                ui.image("/static/ikona.png").classes("w-14 h-14 rounded-xl q-mb-sm")
                ui.label("W czym mogę pomóc?").classes("gradient text-h4 text-weight-bold text-center")
                ui.label("Znam Twój projekt, wymagania uczelni i materiały źródłowe.").classes("przytlumiony text-center")
                with ui.grid(columns=2).classes("w-full gap-3 q-mt-lg"):
                    for ikona, tytul_karty, opis, tresc in PROPOZYCJE:
                        with ui.element("div").classes("karta-propozycji").on("click", lambda t=tresc: wstaw_szablon(t)):
                            ui.icon(ikona, size="22px").classes("text-primary")
                            ui.label(tytul_karty).classes("text-weight-medium q-mt-xs")
                            ui.label(opis).classes("text-caption przytlumiony")

    def pokaz_rozmowe():
        wiadomosci.clear()
        if asystent.aktywna_rozmowa:
            for w in historia.wiadomosci(asystent.aktywna_rozmowa):
                if w["role"] == "user":
                    dymek_uzytkownika(w["content"])
                else:
                    _, kropki, odp, _, akcje = dymek_asystenta()
                    kropki.set_visibility(False)
                    odp.content = w["content"]
                    dodaj_akcje(akcje, w["content"])
        else:
            ekran_powitalny()
        obszar.scroll_to(percent=1.0)

    # ---------- szablony i załączniki ----------

    def wstaw_szablon(tresc):
        obecny = (pole.value or "").strip()
        pole.value = tresc + ("\n\n" + obecny if obecny else "")
        pole.run_method("focus")

    def pokaz_zalaczniki():
        wiersz_zalacznikow.clear()
        with wiersz_zalacznikow:
            for z in dolaczone:
                with ui.row().classes("items-center gap-1 etykieta q-pl-sm wejscie"):
                    ui.icon("description", size="16px")
                    ui.label(z["nazwa"]).classes("text-caption")
                    ui.button(icon="close", on_click=lambda zz=z: usun_zalacznik(zz), color=None) \
                        .props("flat dense round size=xs")

    def usun_zalacznik(z):
        dolaczone.remove(z)
        pokaz_zalaczniki()

    async def przy_zalaczniku(e):
        nazwa, dane = await odczytaj_plik(e)
        try:
            tekst = await run.io_bound(zalaczniki.tekst_z_pliku, nazwa, dane)
            dolaczone.append({"nazwa": nazwa, "tekst": tekst})
            pokaz_zalaczniki()
            ui.notify(f"Załączono {nazwa} ({len(tekst)} znaków)", type="positive")
        except Exception as ex:
            ui.notify(f"{nazwa}: {ex}", type="negative", multi_line=True)

    # ---------- wysyłanie ----------

    async def wyslij():
        tekst = (pole.value or "").strip()
        if not tekst and not dolaczone:
            return
        if not tekst:
            tekst = "Przeanalizuj załączony plik."

        # Treść wiadomości = polecenie + załączniki w znacznikach
        tresc = tekst + "".join(
            f'\n\n<zalacznik nazwa="{z["nazwa"]}">\n{z["tekst"]}\n</zalacznik>' for z in dolaczone
        )

        pole.value = ""
        przycisk.disable()

        id_rozmowy = asystent.aktywna_rozmowa
        dotychczas = historia.wiadomosci(id_rozmowy) if id_rozmowy else []
        do_wyslania = dotychczas + [{"role": "user", "content": tresc}]

        if not id_rozmowy:
            wiadomosci.clear()  # usuń ekran powitalny

        dymek_uzytkownika(tresc)
        kroki, kropki, odp, miejsce_na_zrodla, akcje = dymek_asystenta()
        obszar.scroll_to(percent=1.0)
        zebrane = []

        def przy_kawalku(kawalek):
            if not zebrane:
                kropki.set_visibility(False)
            zebrane.append(kawalek)
            odp.content = "".join(zebrane)
            obszar.scroll_to(percent=1.0)

        def przy_narzedziu(nazwa, wejscie):
            gdzie = "wymaganiach uczelni" if nazwa == "szukaj_w_wymaganiach" else "źródłach"
            with kroki:
                with ui.row().classes("krok wejscie no-wrap"):
                    ui.icon("search", size="16px")
                    ui.label(f"Szukam w {gdzie}: „{wejscie.get('zapytanie', '')}”")
            obszar.scroll_to(percent=1.0)

        try:
            wynik = await asystent.odpowiedz(do_wyslania, przy_kawalku, przy_narzedziu)
            kropki.set_visibility(False)
            odpowiedz_tekst = "".join(zebrane)

            # Zapis dopiero po udanej odpowiedzi
            nowa = not id_rozmowy
            if nowa:
                id_rozmowy = historia.nowa_rozmowa(tekst[:60])
                asystent.aktywna_rozmowa = id_rozmowy
            historia.dodaj_wiadomosc(id_rozmowy, "user", tresc)
            historia.dodaj_wiadomosc(id_rozmowy, "assistant", odpowiedz_tekst)

            dolaczone.clear()
            pokaz_zalaczniki()
            dodaj_akcje(akcje, odpowiedz_tekst)

            # Fragmenty, które asystent przeczytał (do sprawdzenia przez studenta)
            if wynik["fragmenty"]:
                with miejsce_na_zrodla:
                    with ui.expansion(f"Przeczytane fragmenty ({len(wynik['fragmenty'])})", icon="find_in_page") \
                            .props("dense").classes("w-full text-caption przytlumiony"):
                        for f in wynik["fragmenty"]:
                            ui.label(f"{f['plik']}, {f['miejsce']}").classes("text-weight-medium")
                            ui.markdown(f["tresc"])
                            ui.separator()

            miesiac = koszty.suma_miesiac()
            limit = ustawienia.limit()
            info.text = (
                f"{koszty.NAZWY_MODELI[wynik['model']]} · ${wynik['koszt']:.4f} za odpowiedź"
                f" · ten miesiąc ${miesiac:.2f}" + (f" / ${limit:.2f}" if limit else "")
            )
            if wynik["kroki"]:
                info.text += f" · wyszukiwania: {wynik['kroki']}"
            if len(do_wyslania) > asystent.MAKS_WIADOMOSCI:
                info.text += f" · wysłano ostatnie {asystent.MAKS_WIADOMOSCI} wiadomości"

            if limit and miesiac >= 0.8 * limit:
                ui.notify(f"Wykorzystano {miesiac / limit:.0%} miesięcznego limitu wydatków.", type="warning")

            if nowa:
                # Nowa rozmowa pojawia się w panelu bocznym i w nagłówku, bez przeładowania strony
                odswiez_panel()
                etykieta_tytulu.text = tekst[:60]
        except Exception as e:
            kropki.set_visibility(False)
            odp.content = f"⚠️ {asystent.przyjazny_blad(e)} (Ta wymiana nie została zapisana.)"
            pole.value = tekst  # przywróć polecenie, żeby można było wysłać ponownie
        finally:
            przycisk.enable()

    # ---------- okna dialogowe ----------

    with ui.dialog() as okno_zalacznika, ui.card().classes("w-96 q-pa-lg"):
        ui.label("Załącz plik").classes("text-h6")
        ui.label("Swój rozdział (PDF, DOCX) albo plik z kodem lub tekstem (.py, .js, .tex, .md...).").classes("text-caption przytlumiony")
        ui.upload(multiple=True, auto_upload=True, on_upload=przy_zalaczniku).props("flat bordered").classes("w-full")
        ui.button("Gotowe", on_click=okno_zalacznika.close).props("unelevated no-caps").classes("self-end")

    with ui.dialog() as okno_wiedzy, ui.card().classes("w-[680px] max-w-full q-pa-lg"):
        ui.label("Co asystent wie o Twojej pracy").classes("text-h6")
        with ui.scroll_area().classes("h-[60vh] w-full"):
            ui.markdown(projekt.jako_tekst() or "_Karta projektu jest pusta._")
            ui.separator().classes("q-my-md")
            ui.markdown(wymagania.wczytaj() or "_Karta wymagań jest pusta._")
        ui.button("Zamknij", on_click=okno_wiedzy.close, color=None).props("flat no-caps").classes("self-end")

    # ---------- podpięcie zdarzeń i start ----------

    przycisk.on_click(wyslij)
    pole.on("keydown.enter.exact.prevent", wyslij)
    pokaz_rozmowe()


# =====================================================================
# MÓJ PROJEKT
# =====================================================================

@ui.page("/projekt")
def strona_projektu():
    if not jest_klucz():
        return
    uklad("Mój projekt", "/projekt")

    dane = projekt.wczytaj()
    pola = {}

    with ui.column().classes("strona w-full gap-3 wejscie"):
        ui.label("Karta projektu").classes("text-h5 text-weight-medium")
        ui.label("Asystent ma te informacje zawsze przed oczami. Im konkretniej, tym lepsze odpowiedzi.").classes("przytlumiony")

        for klucz, nazwa in projekt.POLA.items():
            if klucz in ("temat", "kierunek", "promotor"):
                pola[klucz] = ui.input(nazwa, value=dane[klucz]).props("outlined").classes("w-full")
            else:
                pola[klucz] = ui.textarea(nazwa, value=dane[klucz]).props("outlined autogrow").classes("w-full")

        def zapisz():
            projekt.zapisz({klucz: pole.value for klucz, pole in pola.items()})
            ui.notify("Zapisano kartę projektu", type="positive")

        ui.button("Zapisz", icon="save", on_click=zapisz).props("unelevated no-caps")
        ui.label(f"Dane zapisywane w: {FOLDER_DANYCH}").classes("text-caption przytlumiony")


# =====================================================================
# BAZY WIEDZY (wspólny szablon dla Wymagań i Źródeł)
# =====================================================================

async def odczytaj_plik(e):
    """Różne wersje NiceGUI przekazują wgrany plik trochę inaczej. Obsługujemy obie."""
    if hasattr(e, "file"):
        return e.file.name, await e.file.read()
    return e.name, e.content.read()


def strona_kolekcji(kolekcja, tytul, opis):
    """Wspólny ekran dla bazy wiedzy: wgrywanie plików, lista, test wyszukiwania."""

    # ---------- funkcje ----------

    def odswiez_liste():
        lista.clear()
        dokumenty = baza_wiedzy.lista_dokumentow(kolekcja)
        with lista:
            if not dokumenty:
                ui.label("Brak dokumentów.").classes("przytlumiony")
            for d in dokumenty:
                jednostka = "sekcji" if d["plik"].lower().endswith(".docx") else "str."
                with ui.row().classes("pozycja no-wrap wejscie"):
                    ui.icon("description", size="20px").classes("przytlumiony")
                    ui.label(f"{d['plik']}").classes("tytul-rozmowy")
                    ui.label(f"{d['stron']} {jednostka} · {d['fragmentow']} fragm.").classes("text-caption przytlumiony")
                    ui.icon("delete_outline", size="18px").classes("usun").on("click", lambda i=d["id"]: usun(i))

    def usun(dokument_id):
        baza_wiedzy.usun_dokument(dokument_id)
        ui.notify("Usunięto dokument")
        odswiez_liste()

    async def przy_wgraniu(e):
        nazwa, dane = await odczytaj_plik(e)
        status.text = f"Przetwarzam {nazwa}..."
        try:
            _, fragm = await run.io_bound(baza_wiedzy.dodaj_dokument, kolekcja, nazwa, dane)
            ui.notify(f"{nazwa}: {fragm} fragmentów", type="positive")
        except Exception as ex:
            ui.notify(f"{nazwa}: {ex}", type="negative", multi_line=True)
        status.text = ""
        odswiez_liste()

    async def przebuduj():
        if not baza_wiedzy.lista_dokumentow(kolekcja):
            return
        przycisk_przebuduj.disable()
        status.text = "Przebudowuję indeks: przetwarzam wszystkie dokumenty od nowa..."
        try:
            dok, fragm = await run.io_bound(baza_wiedzy.przebuduj, kolekcja)
            ui.notify(f"Przebudowano {dok} dokumentów, {fragm} fragmentów", type="positive")
        except Exception as ex:
            ui.notify(f"Błąd przebudowy: {ex}", type="negative", multi_line=True)
        status.text = ""
        przycisk_przebuduj.enable()
        odswiez_liste()

    async def szukaj():
        if not (pytanie.value or "").strip():
            return
        wyniki.clear()
        trafienia = await run.io_bound(baza_wiedzy.szukaj, kolekcja, pytanie.value, 5)
        with wyniki:
            if not trafienia:
                ui.label("Baza jest pusta. Najpierw wgraj dokumenty.").classes("przytlumiony")
            for t in trafienia:
                with ui.card().classes("w-full wejscie"):
                    ui.label(f"{t['plik']}, {t['miejsce']}  ·  podobieństwo {t['wynik']:.2f}").classes("text-caption przytlumiony")
                    ui.markdown(t["tresc"])

    # ---------- ekran ----------

    with ui.column().classes("strona w-full gap-3 wejscie"):
        ui.label(tytul).classes("text-h5 text-weight-medium")
        ui.label(opis).classes("przytlumiony")

        ui.upload(
            label="Przeciągnij pliki PDF lub DOCX albo kliknij +",
            multiple=True, auto_upload=True, on_upload=przy_wgraniu,
        ).props('accept=".pdf,.docx" flat bordered').classes("w-full")
        status = ui.label().classes("text-primary")

        with ui.row().classes("w-full items-center q-mt-md"):
            ui.label("Wgrane dokumenty").classes("text-h6 text-weight-medium col")
            przycisk_przebuduj = ui.button("Przebuduj indeks", icon="refresh", on_click=przebuduj, color=None) \
                .props("flat dense no-caps").tooltip("Przetwarza wszystkie dokumenty od nowa, np. po zmianie parametrów cięcia")
        lista = ui.column().classes("w-full gap-0")

        ui.separator().classes("q-my-md")
        ui.label("Test wyszukiwania").classes("text-h6 text-weight-medium")
        ui.label("Wpisz pytanie i zobacz, jakie fragmenty asystent dostałby z tej bazy.").classes("przytlumiony")
        with ui.row().classes("w-full items-center no-wrap"):
            pytanie = ui.input("Pytanie").props("outlined dense").classes("col")
            pytanie.on("keydown.enter", szukaj)
            ui.button("Szukaj", icon="search", on_click=szukaj).props("unelevated no-caps")
        wyniki = ui.column().classes("w-full gap-2")

    odswiez_liste()


# =====================================================================
# WYMAGANIA UCZELNI
# =====================================================================

def karta_wymagan():
    """Sekcja z kartą wymagań: generowanie, edycja, zapis."""

    async def generuj():
        if not baza_wiedzy.lista_dokumentow("uczelnia"):
            ui.notify("Najpierw wgraj dokumenty uczelni.", type="warning")
            return
        przycisk_gen.disable()
        przycisk_zapisz.disable()
        try:
            status.text = "Czytam dokumenty..."
            tekst = await run.io_bound(baza_wiedzy.tekst_dokumentow, "uczelnia")
            if len(tekst) > wymagania.MAKS_ZNAKOW:
                tekst = tekst[:wymagania.MAKS_ZNAKOW]
                ui.notify("Dokumenty są bardzo długie. Wzięto tylko ich początek.", type="warning")

            status.text = "Asystent czyta dokumenty i pisze kartę. To może potrwać 1–2 minuty..."
            pole.value = ""
            zebrane = []

            def przy_kawalku(kawalek):
                zebrane.append(kawalek)
                pole.value = "".join(zebrane)

            w, koszt = await wymagania.generuj(tekst, przy_kawalku)
            status.text = (
                f"Gotowe ({w.usage.input_tokens} tok. wejścia, {w.usage.output_tokens} tok. wyjścia, koszt ${koszt:.3f}). "
                "Sprawdź kartę, popraw, co trzeba, i kliknij Zapisz."
            )
        except Exception as e:
            status.text = f"⚠️ {asystent.przyjazny_blad(e)}"
        finally:
            przycisk_gen.enable()
            przycisk_zapisz.enable()

    async def klik_generuj():
        if (pole.value or "").strip():
            with ui.dialog() as okno, ui.card().classes("q-pa-lg"):
                ui.label("Wygenerować kartę od nowa?").classes("text-h6")
                ui.label("Treść w edytorze zostanie zastąpiona. Zapisana wersja zostaje, dopóki nie klikniesz Zapisz.").classes("przytlumiony")
                with ui.row().classes("w-full justify-end q-mt-md"):
                    ui.button("Anuluj", on_click=lambda: okno.submit(False), color=None).props("flat no-caps")
                    ui.button("Generuj", on_click=lambda: okno.submit(True)).props("unelevated no-caps")
            if not await okno:
                return
        await generuj()

    def zapisz():
        wymagania.zapisz(pole.value or "")
        ui.notify("Zapisano kartę wymagań. Asystent będzie z niej korzystał.", type="positive")

    with ui.column().classes("strona w-full gap-3 wejscie"):
        ui.separator()
        ui.label("Karta wymagań").classes("text-h5 text-weight-medium")
        ui.label(
            "Zwięzłe podsumowanie wymogów uczelni. Asystent ma ją zawsze przed oczami. "
            "Sprawdź ją uważnie z dokumentami: to Twoje źródło prawdy."
        ).classes("przytlumiony")
        with ui.row():
            przycisk_gen = ui.button("Wygeneruj z dokumentów", icon="auto_awesome", on_click=klik_generuj).props("unelevated no-caps")
            przycisk_zapisz = ui.button("Zapisz", icon="save", on_click=zapisz, color=None).props("outline no-caps")
        status = ui.label().classes("text-primary")
        pole = ui.textarea(value=wymagania.wczytaj()).props("autogrow outlined").classes("w-full")


@ui.page("/wymagania")
def strona_wymagan():
    if not jest_klucz():
        return
    uklad("Wymagania uczelni", "/wymagania")
    strona_kolekcji(
        "uczelnia",
        "Wymagania uczelni",
        "Wgraj regulaminy, zarządzenia i wytyczne dotyczące pracy dyplomowej: formatowanie, terminy, struktura, zasady cytowania.",
    )
    karta_wymagan()


# =====================================================================
# ŹRÓDŁA
# =====================================================================

@ui.page("/zrodla")
def strona_zrodel():
    if not jest_klucz():
        return
    uklad("Źródła", "/zrodla")
    strona_kolekcji(
        "zrodla",
        "Materiały źródłowe",
        "Wgraj przykładowe prace dyplomowe, artykuły, fragmenty książek i notatki. "
        "Asystent będzie z nich korzystał, podając plik i stronę.",
    )


# =====================================================================
# USTAWIENIA
# =====================================================================

@ui.page("/ustawienia")
def strona_ustawien():
    if not jest_klucz():
        return
    uklad("Ustawienia", "/ustawienia")

    with ui.column().classes("strona w-full gap-4 wejscie"):
        # ---------- model ----------
        ui.label("Model").classes("text-h5 text-weight-medium")
        ui.label(
            "Sonnet wystarcza do większości pracy. Opus jest mocniejszy przy trudnych analizach "
            "i recenzjach, ale 2× droższy. Model możesz też przełączać w nagłówku czatu."
        ).classes("przytlumiony")
        ui.radio(
            {k: f"{n}  (${c['wejscie']:.0f} / ${c['wyjscie']:.0f} za mln tokenów wej./wyj.)"
             for (k, n), c in zip(koszty.NAZWY_MODELI.items(), koszty.CENNIK.values())},
            value=ustawienia.model(),
            on_change=lambda e: (ustawienia.ustaw("model", e.value), ui.notify("Zapisano model")),
        )

        ui.separator()

        # ---------- limit ----------
        ui.label("Miesięczny limit wydatków").classes("text-h5 text-weight-medium")
        ui.label(
            "Po osiągnięciu limitu asystent przestanie odpowiadać do końca miesiąca (albo do zmiany limitu). "
            "0 = bez limitu. Niezależnie od tego warto ustawić limit także na koncie w Claude Console."
        ).classes("przytlumiony")
        with ui.row().classes("items-center"):
            pole_limitu = ui.number("Limit (USD)", value=ustawienia.limit(), min=0, step=1, format="%.2f") \
                .props("outlined dense").classes("w-40")

            def zapisz_limit():
                ustawienia.ustaw("limit_miesieczny", float(pole_limitu.value or 0))
                ui.notify("Zapisano limit", type="positive")

            ui.button("Zapisz", icon="save", on_click=zapisz_limit).props("unelevated no-caps")

        ui.separator()

        # ---------- zużycie ----------
        ui.label("Zużycie").classes("text-h5 text-weight-medium")
        with ui.row().classes("gap-4"):
            for opis, kwota in (
                ("Dziś", koszty.suma_dzis()),
                ("Ten miesiąc", koszty.suma_miesiac()),
                ("Łącznie", koszty.suma_lacznie()),
            ):
                with ui.card().classes("items-center q-px-xl q-py-md"):
                    ui.label(opis).classes("text-caption przytlumiony")
                    ui.label(f"${kwota:.2f}").classes("text-h5 text-weight-medium")

        wiersze = [
            {"rodzaj": w["rodzaj"], "model": koszty.NAZWY_MODELI.get(w["model"], w["model"]),
             "wywolan": w["wywolan"], "koszt": f"${w['koszt']:.3f}"}
            for w in koszty.szczegoly_miesiaca()
        ]
        if wiersze:
            ui.label("Ten miesiąc w szczegółach").classes("text-subtitle1 text-weight-medium")
            ui.table(
                columns=[
                    {"name": "rodzaj", "label": "Rodzaj", "field": "rodzaj", "align": "left"},
                    {"name": "model", "label": "Model", "field": "model", "align": "left"},
                    {"name": "wywolan", "label": "Wywołań API", "field": "wywolan"},
                    {"name": "koszt", "label": "Koszt", "field": "koszt"},
                ],
                rows=wiersze,
            ).props("flat bordered").classes("w-full")
        ui.label(
            "Koszty liczone przez aplikację na podstawie cennika z dnia 24.10.2026. "
            "Dokładne rozliczenie znajdziesz w Claude Console (platform.claude.com)."
        ).classes("text-caption przytlumiony")

        ui.separator()

        # ---------- klucz ----------
        ui.label("Klucz API").classes("text-h5 text-weight-medium")
        ui.button("Zmień klucz API", icon="key", on_click=lambda: ui.navigate.to("/klucz"), color=None).props("outline no-caps")


# =====================================================================
# KLUCZ API
# =====================================================================

@ui.page("/klucz")
def strona_klucza():
    motyw()
    with ui.card().classes("absolute-center w-[460px] max-w-full q-pa-lg gap-3 wejscie"):
        with ui.row().classes("items-center gap-3 no-wrap"):
            ui.image("/static/ikona.png").classes("w-12 h-12 rounded-xl")
            with ui.column().classes("gap-0"):
                ui.label("Połącz z Claude").classes("text-h5 text-weight-medium")
                ui.label("Diploma potrzebuje Twojego klucza API").classes("przytlumiony")
        ui.separator()
        for nr, krok in enumerate([
            "Zaloguj się na platform.claude.com",
            "W Billing doładuj konto",
            "Wejdź w Settings → API keys i kliknij Create key",
            "Skopiuj klucz (zaczyna się od sk-ant-) i wklej poniżej",
        ], start=1):
            with ui.row().classes("items-center gap-3 no-wrap"):
                ui.label(str(nr)).classes("etykieta text-primary text-weight-bold w-7 h-7 flex flex-center")
                ui.label(krok)

        pole = ui.input("Klucz API", password=True, password_toggle_button=True).props("outlined").classes("w-full")
        status = ui.label().classes("text-negative")

        async def polacz():
            klucz = (pole.value or "").strip()
            status.text = "Sprawdzam klucz..."
            przycisk.disable()
            ok, komunikat = await run.io_bound(klucz_api.sprawdz_klucz, klucz)
            przycisk.enable()
            if not ok:
                status.text = komunikat
                return
            try:
                klucz_api.zapisz_klucz(klucz)
            except Exception as e:
                status.text = f"Klucz działa, ale nie udało się go zapisać w sejfie haseł systemu: {e}"
                return
            ui.notify("Połączono z Claude!", type="positive")
            ui.navigate.to("/")

        przycisk = ui.button("Połącz", on_click=polacz).props("unelevated no-caps").classes("w-full")

        if klucz_api.wczytaj_klucz():
            ui.button("Anuluj", on_click=lambda: ui.navigate.to("/"), color=None).props("flat no-caps").classes("w-full")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Diploma",
        favicon=FOLDER_STATIC / "ikona.png",
        native=True,
        window_size=(1280, 820),
        reload=False,
        port=native.find_open_port(),  # wolny port, nawet gdy coś innego zajmuje domyślny
    )