import sqlite3
from datetime import date, datetime

from app.sciezki import FOLDER_DANYCH

# Ta sama baza co historia rozmów, osobna tabela
BAZA = FOLDER_DANYCH / "diploma.db"

# Ceny w USD za MILION tokenów.
# Źródło: https://platform.claude.com/docs/en/about-claude/pricing (stan na 24.10.2026).
# Gdy Anthropic zmieni ceny, wystarczy poprawić liczby tutaj.
CENNIK = {
    "claude-sonnet-5-5": {"wejscie": 2.00, "wyjscie": 10.00, "cache_zapis": 2.50, "cache_odczyt": 0.10},
    "claude-opus-5-5": {"wejscie": 4.00, "wyjscie": 20.00, "cache_zapis": 5.00, "cache_odczyt": 0.20},
}

# Krótkie nazwy do wyświetlania w aplikacji
NAZWY_MODELI = {
    "claude-sonnet-5-5": "Sonnet",
    "claude-opus-5-5": "Opus",
}


def _polacz():
    polaczenie = sqlite3.connect(BAZA, timeout=30)
    polaczenie.row_factory = sqlite3.Row
    return polaczenie


def _przygotuj():
    with _polacz() as baza:
        baza.execute("""
            CREATE TABLE IF NOT EXISTS zuzycie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kiedy TEXT NOT NULL,
                rodzaj TEXT NOT NULL,
                model TEXT NOT NULL,
                wejscie INTEGER NOT NULL,
                cache_zapis INTEGER NOT NULL,
                cache_odczyt INTEGER NOT NULL,
                wyjscie INTEGER NOT NULL,
                koszt REAL NOT NULL
            )
        """)


_przygotuj()


def policz(model, usage):
    """Zamienia zużycie tokenów z odpowiedzi API na koszt w USD."""
    ceny = CENNIK.get(model, CENNIK["claude-sonnet-5-5"])
    tokeny = {
        "wejscie": getattr(usage, "input_tokens", 0) or 0,
        "cache_zapis": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        "cache_odczyt": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "wyjscie": getattr(usage, "output_tokens", 0) or 0,
    }
    koszt = sum(tokeny[k] * ceny[k] for k in tokeny) / 1_000_000
    return tokeny, koszt


def zapisz(rodzaj, model, usage):
    """Zapisuje jedno wywołanie API. Zwraca (tokeny, koszt)."""
    tokeny, koszt = policz(model, usage)
    with _polacz() as baza:
        baza.execute(
            """INSERT INTO zuzycie (kiedy, rodzaj, model, wejscie, cache_zapis, cache_odczyt, wyjscie, koszt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(timespec="seconds"), rodzaj, model,
             tokeny["wejscie"], tokeny["cache_zapis"], tokeny["cache_odczyt"], tokeny["wyjscie"], koszt),
        )
    return tokeny, koszt


def _suma_od(poczatek):
    with _polacz() as baza:
        return baza.execute(
            "SELECT COALESCE(SUM(koszt), 0) FROM zuzycie WHERE kiedy >= ?", (poczatek,)
        ).fetchone()[0]


def suma_dzis():
    return _suma_od(date.today().isoformat())


def suma_miesiac():
    return _suma_od(date.today().replace(day=1).isoformat())


def suma_lacznie():
    return _suma_od("0000")


def szczegoly_miesiaca():
    """Koszty w tym miesiącu z podziałem na rodzaj i model."""
    with _polacz() as baza:
        return baza.execute("""
            SELECT rodzaj, model, COUNT(*) AS wywolan, SUM(koszt) AS koszt
            FROM zuzycie WHERE kiedy >= ?
            GROUP BY rodzaj, model ORDER BY koszt DESC
        """, (date.today().replace(day=1).isoformat(),)).fetchall()