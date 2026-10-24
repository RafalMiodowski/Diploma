import json

from app import koszty
from app.sciezki import FOLDER_DANYCH

PLIK = FOLDER_DANYCH / "ustawienia.json"

DOMYSLNE = {
    "model": "claude-sonnet-5-5",
    "limit_miesieczny": 5.0,  # USD; 0 = bez limitu
}


def wczytaj():
    dane = dict(DOMYSLNE)
    if PLIK.exists():
        dane.update(json.loads(PLIK.read_text(encoding="utf-8")))
    return dane


def ustaw(klucz, wartosc):
    dane = wczytaj()
    dane[klucz] = wartosc
    PLIK.write_text(json.dumps(dane, ensure_ascii=False, indent=2), encoding="utf-8")


def model():
    wybrany = wczytaj()["model"]
    return wybrany if wybrany in koszty.CENNIK else DOMYSLNE["model"]


def limit():
    return float(wczytaj()["limit_miesieczny"] or 0)


def limit_przekroczony():
    return limit() > 0 and koszty.suma_miesiac() >= limit()


class LimitPrzekroczony(Exception):
    """Wydatki w tym miesiącu osiągnęły limit ustawiony przez użytkownika."""


def sprawdz_limit():
    """Wywołaj przed każdym zapytaniem do API. Rzuca wyjątek, gdy limit jest osiągnięty."""
    if limit_przekroczony():
        raise LimitPrzekroczony()