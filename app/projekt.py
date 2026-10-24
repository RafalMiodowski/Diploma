import json
from app.sciezki import FOLDER_DANYCH

PLIK = FOLDER_DANYCH / "projekt.json"

# Pola karty: nazwa techniczna -> nazwa widoczna dla użytkownika
POLA = {
    "temat": "Temat pracy",
    "kierunek": "Kierunek i uczelnia",
    "promotor": "Promotor",
    "cel": "Cel pracy",
    "zakres": "Zakres pracy",
    "pytania": "Teza / pytania badawcze",
    "plan": "Plan rozdziałów",
    "uwagi": "Ustalenia z promotorem",
    "status": "Aktualny etap prac",
}


def wczytaj():
    """Zwraca kartę projektu jako słownik. Puste pola, jeśli jeszcze nic nie zapisano."""
    dane = {klucz: "" for klucz in POLA}
    if PLIK.exists():
        dane.update(json.loads(PLIK.read_text(encoding="utf-8")))
    return dane


def zapisz(dane):
    PLIK.write_text(json.dumps(dane, ensure_ascii=False, indent=2), encoding="utf-8")


def jako_tekst():
    """Karta projektu jako czytelny tekst. Właśnie to dostanie asystent."""
    dane = wczytaj()
    czesci = []
    for klucz, nazwa in POLA.items():
        wartosc = dane.get(klucz, "").strip()
        if wartosc:
            czesci.append(f"## {nazwa}\n{wartosc}")
    return "\n\n".join(czesci)