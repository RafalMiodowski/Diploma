from nicegui import ui, run
from app import klucz_api, projekt, asystent, historia, baza_wiedzy, wymagania
from app.sciezki import FOLDER_DANYCH

# Pozycje menu: (nazwa, ikona, adres, czy_gotowe)
MENU = [
    ("Asystent", "chat", "/", True),
    ("Mój projekt", "school", "/projekt", True),
    ("Wymagania uczelni", "rule", "/wymagania", True),
    ("Źródła", "menu_book", "/zrodla", False),
    ("Ustawienia", "settings", "/klucz", True),
]


def uklad(tytul):
    """Wspólny wygląd każdej strony: górny pasek + boczne menu."""
    with ui.header().classes("items-center"):
        ui.label("Diploma").classes("text-h6")
        ui.label("·").classes("opacity-60")
        ui.label(tytul).classes("opacity-90")

    with ui.left_drawer(value=True).classes("bg-grey-1"):
        for nazwa, ikona, adres, gotowe in MENU:
            przycisk = ui.button(
                nazwa, icon=ikona,
                on_click=lambda a=adres: ui.navigate.to(a),
            ).props("flat align=left").classes("w-full")
            if not gotowe:
                przycisk.disable()
                przycisk.tooltip("Wkrótce")


def jest_klucz():
    """Jeśli nie ma klucza, odeślij na ekran klucza."""
    if not klucz_api.wczytaj_klucz():
        ui.navigate.to("/klucz")
        return False
    return True


@ui.page("/")
def strona_asystenta():
    if not jest_klucz():
        return
    uklad("Asystent")

    with ui.column().classes("w-full max-w-3xl mx-auto p-4 gap-2 h-[calc(100vh-70px)] no-wrap"):
        # Wybór rozmowy + przyciski
        with ui.row().classes("w-full items-center no-wrap"):
            wybor = ui.select({}, label="Rozmowa").classes("flex-grow")
            ui.button(icon="add_comment", on_click=lambda: nowa()).props("flat").tooltip("Nowa rozmowa")
            ui.button(icon="delete", on_click=lambda: potwierdz_usuniecie()).props("flat").tooltip("Usuń rozmowę")

        with ui.expansion("Co asystent wie o Twojej pracy", icon="school").classes("w-full"):
            ui.markdown(projekt.jako_tekst() or "_Karta projektu jest pusta._")
            ui.separator()
            ui.markdown(wymagania.wczytaj() or "_Karta wymagań jest pusta._")

        with ui.scroll_area().classes("w-full flex-grow border rounded") as obszar:
            wiadomosci = ui.column().classes("w-full gap-3 p-2")

        info = ui.label().classes("text-caption text-grey-6")

        with ui.row().classes("w-full items-end no-wrap"):
            pole = ui.textarea(placeholder="Napisz wiadomość... (Enter wysyła, Shift+Enter nowa linia)").props("autogrow outlined").classes("flex-grow")
            przycisk = ui.button(icon="send")

    # ---------- funkcje pomocnicze ----------

    def dymek(rola, tekst):
        with wiadomosci:
            if rola == "user":
                with ui.row().classes("w-full justify-end"):
                    with ui.card().classes("bg-blue-1 max-w-[80%]"):
                        return ui.markdown(tekst)
            else:
                with ui.card().classes("w-full"):
                    return ui.markdown(tekst)

    def odswiez_liste():
        wybor.options = {r["id"]: r["tytul"] for r in historia.lista_rozmow()}
        wybor.value = asystent.aktywna_rozmowa
        wybor.update()

    def pokaz_rozmowe():
        wiadomosci.clear()
        info.text = ""
        if asystent.aktywna_rozmowa:
            for w in historia.wiadomosci(asystent.aktywna_rozmowa):
                dymek(w["role"], w["content"])
        obszar.scroll_to(percent=1.0)

    def zmiana_rozmowy(e):
        if e.value != asystent.aktywna_rozmowa:
            asystent.aktywna_rozmowa = e.value
            pokaz_rozmowe()

    def nowa():
        asystent.aktywna_rozmowa = None
        wybor.value = None
        pokaz_rozmowe()

    def potwierdz_usuniecie():
        if not asystent.aktywna_rozmowa:
            return
        with ui.dialog() as okno, ui.card():
            ui.label("Usunąć tę rozmowę? Tego nie da się cofnąć.")
            with ui.row():
                ui.button("Anuluj", on_click=okno.close).props("flat")

                def usun():
                    historia.usun_rozmowe(asystent.aktywna_rozmowa)
                    okno.close()
                    nowa()
                    odswiez_liste()

                ui.button("Usuń", color="negative", on_click=usun)
        okno.open()

    async def wyslij():
        tekst = (pole.value or "").strip()
        if not tekst:
            return
        pole.value = ""
        przycisk.disable()
        wybor.disable()

        id_rozmowy = asystent.aktywna_rozmowa
        dotychczas = historia.wiadomosci(id_rozmowy) if id_rozmowy else []
        do_wyslania = dotychczas + [{"role": "user", "content": tekst}]

        dymek("user", tekst)
        odp = dymek("assistant", "_Asystent myśli..._")
        obszar.scroll_to(percent=1.0)
        zebrane = []

        def przy_kawalku(kawalek):
            zebrane.append(kawalek)
            odp.content = "".join(zebrane)
            obszar.scroll_to(percent=1.0)

        try:
            wiadomosc = await asystent.odpowiedz(do_wyslania, przy_kawalku)

            # Zapis dopiero po udanej odpowiedzi
            if not id_rozmowy:
                id_rozmowy = historia.nowa_rozmowa(tekst[:60])
                asystent.aktywna_rozmowa = id_rozmowy
                odswiez_liste()
            historia.dodaj_wiadomosc(id_rozmowy, "user", tekst)
            historia.dodaj_wiadomosc(id_rozmowy, "assistant", "".join(zebrane))

            u = wiadomosc.usage
            info.text = (
                f"Ostatnia odpowiedź: wejście {u.input_tokens} tok. "
                f"(z cache: {u.cache_read_input_tokens or 0}), "
                f"wyjście {u.output_tokens} tok."
            )
            if len(do_wyslania) > asystent.MAKS_WIADOMOSCI:
                info.text += f" · wysłano tylko ostatnie {asystent.MAKS_WIADOMOSCI} wiadomości"
        except Exception as e:
            odp.content = f"⚠️ {asystent.przyjazny_blad(e)} (Ta wymiana nie została zapisana.)"
        finally:
            przycisk.enable()
            wybor.enable()

    # ---------- podpięcie zdarzeń i start ----------

    wybor.on_value_change(zmiana_rozmowy)
    przycisk.on_click(wyslij)
    pole.on("keydown.enter.exact.prevent", wyslij)

    odswiez_liste()
    pokaz_rozmowe()

@ui.page("/projekt")
def strona_projektu():
    if not jest_klucz():
        return
    uklad("Mój projekt")

    dane = projekt.wczytaj()
    pola = {}

    with ui.column().classes("w-full max-w-3xl mx-auto p-4 gap-3"):
        ui.label("Karta projektu").classes("text-h5")
        ui.label("Asystent będzie miał te informacje zawsze przed oczami. Im konkretniej, tym lepsze odpowiedzi.").classes("text-grey-7")

        for klucz, nazwa in projekt.POLA.items():
            if klucz in ("temat", "kierunek", "promotor"):
                pola[klucz] = ui.input(nazwa, value=dane[klucz]).classes("w-full")
            else:
                pola[klucz] = ui.textarea(nazwa, value=dane[klucz]).props("autogrow").classes("w-full")

        def zapisz():
            projekt.zapisz({klucz: pole.value for klucz, pole in pola.items()})
            ui.notify("Zapisano kartę projektu", type="positive")

        ui.button("Zapisz", icon="save", on_click=zapisz)
        ui.label(f"Dane zapisywane w: {FOLDER_DANYCH}").classes("text-caption text-grey-6")

async def odczytaj_plik(e):
    """Różne wersje NiceGUI przekazują wgrany plik trochę inaczej. Obsługujemy obie."""
    if hasattr(e, "file"):
        return e.file.name, await e.file.read()
    return e.name, e.content.read()


def strona_kolekcji(kolekcja, tytul, opis):
    """Wspólny ekran dla bazy wiedzy: wgrywanie PDF-ów, lista, test wyszukiwania."""

    # ---------- funkcje ----------

    def odswiez_liste():
        lista.clear()
        dokumenty = baza_wiedzy.lista_dokumentow(kolekcja)
        with lista:
            if not dokumenty:
                ui.label("Brak dokumentów.").classes("text-grey-6")
            for d in dokumenty:
                with ui.row().classes("w-full items-center no-wrap"):
                    ui.icon("description").classes("text-grey-7")
                    ui.label(f"{d['plik']}  ·  {d['stron']} str., {d['fragmentow']} fragm.").classes("flex-grow")
                    ui.button(icon="delete", on_click=lambda i=d["id"]: usun(i)).props("flat dense")

    def usun(dokument_id):
        baza_wiedzy.usun_dokument(dokument_id)
        ui.notify("Usunięto dokument")
        odswiez_liste()

    async def przy_wgraniu(e):
        nazwa, dane = await odczytaj_plik(e)
        status.text = f"Przetwarzam {nazwa}... (za pierwszym razem dłużej: pobieranie modelu ~220 MB)"
        try:
            stron, fragm = await run.io_bound(baza_wiedzy.dodaj_pdf, kolekcja, nazwa, dane)
            ui.notify(f"{nazwa}: {stron} stron, {fragm} fragmentów", type="positive")
        except Exception as ex:
            ui.notify(f"{nazwa}: {ex}", type="negative", multi_line=True)
        status.text = ""
        odswiez_liste()

    async def szukaj():
        if not (pytanie.value or "").strip():
            return
        wyniki.clear()
        trafienia = await run.io_bound(baza_wiedzy.szukaj, kolekcja, pytanie.value, 5)
        with wyniki:
            if not trafienia:
                ui.label("Baza jest pusta. Najpierw wgraj dokumenty.")
            for t in trafienia:
                with ui.card().classes("w-full"):
                    ui.label(f"{t['plik']}, str. {t['strona']}  ·  podobieństwo {t['wynik']:.2f}").classes("text-caption text-grey-7")
                    ui.markdown(t["tresc"])

    # ---------- ekran ----------

    with ui.column().classes("w-full max-w-3xl mx-auto p-4 gap-3"):
        ui.label(tytul).classes("text-h5")
        ui.label(opis).classes("text-grey-7")

        ui.upload(
            label="Przeciągnij PDF-y albo kliknij +",
            multiple=True, auto_upload=True, on_upload=przy_wgraniu,
        ).props('accept=".pdf"').classes("w-full")
        status = ui.label().classes("text-primary")

        ui.label("Wgrane dokumenty").classes("text-h6")
        lista = ui.column().classes("w-full gap-1")

        ui.separator()
        ui.label("Test wyszukiwania").classes("text-h6")
        ui.label("Wpisz pytanie i zobacz, jakie fragmenty asystent dostałby z tej bazy.").classes("text-grey-7")
        with ui.row().classes("w-full items-center no-wrap"):
            pytanie = ui.input("Pytanie, np. jaka czcionka obowiązuje w pracy?").classes("flex-grow")
            pytanie.on("keydown.enter", szukaj)
            ui.button("Szukaj", icon="search", on_click=szukaj)
        wyniki = ui.column().classes("w-full gap-2")

    odswiez_liste()


@ui.page("/wymagania")
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

            w = await wymagania.generuj(tekst, przy_kawalku)
            status.text = (
                f"Gotowe ({w.usage.input_tokens} tok. wejścia, {w.usage.output_tokens} tok. wyjścia). "
                "Sprawdź kartę, popraw, co trzeba, i kliknij Zapisz."
            )
        except Exception as e:
            status.text = f"⚠️ {asystent.przyjazny_blad(e)}"
        finally:
            przycisk_gen.enable()
            przycisk_zapisz.enable()

    async def klik_generuj():
        if (pole.value or "").strip():
            with ui.dialog() as okno, ui.card():
                ui.label("Wygenerować kartę od nowa? Treść w edytorze zostanie zastąpiona. "
                         "Zapisana wersja zostaje, dopóki nie klikniesz Zapisz.")
                with ui.row():
                    ui.button("Anuluj", on_click=lambda: okno.submit(False)).props("flat")
                    ui.button("Generuj", on_click=lambda: okno.submit(True))
            if not await okno:
                return
        await generuj()

    def zapisz():
        wymagania.zapisz(pole.value or "")
        ui.notify("Zapisano kartę wymagań. Asystent będzie z niej korzystał.", type="positive")

    with ui.column().classes("w-full max-w-3xl mx-auto p-4 gap-3"):
        ui.separator()
        ui.label("Karta wymagań").classes("text-h5")
        ui.label(
            "Zwięzłe podsumowanie wymogów uczelni. Asystent ma ją zawsze przed oczami. "
            "Sprawdź ją uważnie z dokumentami: to Twoje źródło prawdy."
        ).classes("text-grey-7")
        with ui.row():
            przycisk_gen = ui.button("Wygeneruj z dokumentów", icon="auto_awesome", on_click=klik_generuj)
            przycisk_zapisz = ui.button("Zapisz", icon="save", on_click=zapisz)
        status = ui.label().classes("text-primary")
        pole = ui.textarea(value=wymagania.wczytaj()).props("autogrow outlined").classes("w-full")


@ui.page("/wymagania")
def strona_wymagan():
    if not jest_klucz():
        return
    uklad("Wymagania uczelni")
    strona_kolekcji(
        "uczelnia",
        "Wymagania uczelni",
        "Wgraj regulaminy, zarządzenia i wytyczne dotyczące pracy dyplomowej: formatowanie, terminy, struktura, zasady cytowania.",
    )
    karta_wymagan()

@ui.page("/klucz")
def strona_klucza():
    with ui.card().classes("absolute-center w-[440px] p-6"):
        ui.label("Połącz z Claude").classes("text-h5")
        ui.label("Aplikacja potrzebuje Twojego klucza API Claude:")
        ui.label("1. Zaloguj się na platform.claude.com")
        ui.label("2. W Billing doładuj konto")
        ui.label("3. Wejdź w Settings → API keys i kliknij Create key")
        ui.label("4. Skopiuj klucz (zaczyna się od sk-ant-) i wklej poniżej")

        pole = ui.input("Klucz API", password=True, password_toggle_button=True).classes("w-full")
        status = ui.label().classes("text-negative")

        async def polacz():
            klucz = (pole.value or "").strip()
            status.text = "Sprawdzam klucz..."
            przycisk.disable()
            ok, komunikat = await run.io_bound(klucz_api.sprawdz_klucz, klucz)
            przycisk.enable()
            if ok:
                klucz_api.zapisz_klucz(klucz)
                ui.notify("Połączono z Claude!", type="positive")
                ui.navigate.to("/")
            else:
                status.text = komunikat

        przycisk = ui.button("Połącz", on_click=polacz).classes("w-full")

        if klucz_api.wczytaj_klucz():
            ui.button("Anuluj", on_click=lambda: ui.navigate.to("/")).props("flat").classes("w-full")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Diploma", native=True, window_size=(1100, 750), reload=False)