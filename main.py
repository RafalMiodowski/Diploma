from nicegui import ui, run
from app import klucz_api


@ui.page("/")
def strona_glowna():
    # Brak klucza? Przekieruj na ekran podłączania
    if not klucz_api.wczytaj_klucz():
        ui.navigate.to("/klucz")
        return

    with ui.column().classes("absolute-center items-center"):
        ui.label("Diploma").classes("text-h3")
        ui.label("Połączono z Claude ✅").classes("text-h6")
        # ZMIANA 1: przycisk tylko przełącza ekran, NIE usuwa klucza
        ui.button("Zmień klucz API", on_click=lambda: ui.navigate.to("/klucz")).props("flat")


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
                # Nowy klucz nadpisuje stary dopiero po pomyślnym sprawdzeniu
                klucz_api.zapisz_klucz(klucz)
                ui.notify("Połączono z Claude!", type="positive")
                ui.navigate.to("/")
            else:
                status.text = komunikat

        przycisk = ui.button("Połącz", on_click=polacz).classes("w-full")

        # ZMIANA 2: "Anuluj" widoczne tylko, gdy jakiś klucz jest już zapisany
        if klucz_api.wczytaj_klucz():
            ui.button("Anuluj", on_click=lambda: ui.navigate.to("/")).props("flat").classes("w-full")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Diploma", native=True, window_size=(1000, 700), reload=False)