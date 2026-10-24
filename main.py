from nicegui import ui, run
from app import klucz_api, projekt
from app.sciezki import FOLDER_DANYCH

# Pozycje menu: (nazwa, ikona, adres, czy_gotowe)
MENU = [
    ("Asystent", "chat", "/", True),
    ("Mój projekt", "school", "/projekt", True),
    ("Wymagania uczelni", "rule", "/wymagania", False),
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

    with ui.column().classes("w-full max-w-3xl mx-auto p-4 gap-4"):
        ui.label("Asystent").classes("text-h5")
        ui.label("Czat pojawi się tu w kroku 5. Poniżej: to, co asystent będzie wiedział o Twojej pracy.").classes("text-grey-7")

        tekst = projekt.jako_tekst()
        with ui.card().classes("w-full"):
            if tekst:
                ui.markdown(tekst)
            else:
                ui.label("Karta projektu jest pusta. Uzupełnij ją w zakładce „Mój projekt”.")


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