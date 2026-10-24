import sqlite3
from datetime import datetime
from app.sciezki import FOLDER_DANYCH

BAZA = FOLDER_DANYCH / "diploma.db"


def _polacz():
    polaczenie = sqlite3.connect(BAZA)
    polaczenie.row_factory = sqlite3.Row  # wiersze dostępne po nazwach kolumn
    return polaczenie


def _teraz():
    return datetime.now().isoformat(timespec="seconds")


def przygotuj():
    """Tworzy tabele, jeśli jeszcze nie istnieją."""
    with _polacz() as baza:
        baza.executescript("""
            CREATE TABLE IF NOT EXISTS rozmowy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tytul TEXT NOT NULL,
                utworzono TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wiadomosci (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rozmowa_id INTEGER NOT NULL,
                rola TEXT NOT NULL,
                tresc TEXT NOT NULL,
                utworzono TEXT NOT NULL
            );
        """)


def nowa_rozmowa(tytul):
    with _polacz() as baza:
        kursor = baza.execute(
            "INSERT INTO rozmowy (tytul, utworzono) VALUES (?, ?)",
            (tytul, _teraz()),
        )
        return kursor.lastrowid


def lista_rozmow():
    with _polacz() as baza:
        return baza.execute("SELECT id, tytul FROM rozmowy ORDER BY id DESC").fetchall()


def dodaj_wiadomosc(rozmowa_id, rola, tresc):
    with _polacz() as baza:
        baza.execute(
            "INSERT INTO wiadomosci (rozmowa_id, rola, tresc, utworzono) VALUES (?, ?, ?, ?)",
            (rozmowa_id, rola, tresc, _teraz()),
        )


def wiadomosci(rozmowa_id):
    """Zwraca wiadomości rozmowy w formacie, który rozumie Claude."""
    with _polacz() as baza:
        wiersze = baza.execute(
            "SELECT rola, tresc FROM wiadomosci WHERE rozmowa_id = ? ORDER BY id",
            (rozmowa_id,),
        ).fetchall()
    return [{"role": w["rola"], "content": w["tresc"]} for w in wiersze]


def usun_rozmowe(rozmowa_id):
    with _polacz() as baza:
        baza.execute("DELETE FROM wiadomosci WHERE rozmowa_id = ?", (rozmowa_id,))
        baza.execute("DELETE FROM rozmowy WHERE id = ?", (rozmowa_id,))


# Przy pierwszym imporcie upewnij się, że tabele istnieją
przygotuj()