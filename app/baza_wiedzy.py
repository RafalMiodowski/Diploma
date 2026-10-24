import sqlite3
from datetime import datetime

import docx
import numpy as np
import pymupdf4llm
from fastembed import TextEmbedding

from app.sciezki import FOLDER_DANYCH

BAZA = FOLDER_DANYCH / "wiedza.db"
FOLDER_PLIKOW = FOLDER_DANYCH / "pliki"
FOLDER_MODELI = FOLDER_DANYCH / "modele"

# Mały wielojęzyczny model (dobrze radzi sobie z polskim), ok. 220 MB, pobiera się raz
MODEL_EMBEDDINGOW = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

OBSLUGIWANE = (".pdf", ".docx")

DLUGOSC_FRAGMENTU = 1200  # znaków
ZAKLADKA = 200            # tyle znaków powtarza się między sąsiednimi fragmentami
MIN_DLUGOSC = 80          # krótsze fragmenty (np. sam tytuł slajdu) pomijamy


# ---------- baza ----------

def _polacz():
    polaczenie = sqlite3.connect(BAZA, timeout=30)
    polaczenie.row_factory = sqlite3.Row
    return polaczenie


def _przygotuj():
    with _polacz() as baza:
        baza.executescript("""
            CREATE TABLE IF NOT EXISTS dokumenty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kolekcja TEXT NOT NULL,
                plik TEXT NOT NULL,
                stron INTEGER NOT NULL,
                dodano TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fragmenty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dokument_id INTEGER NOT NULL,
                strona INTEGER NOT NULL,
                miejsce TEXT,
                tresc TEXT NOT NULL,
                wektor BLOB NOT NULL
            );
        """)
        # Migracja: bazy z kroku 7 nie mają kolumny "miejsce"
        kolumny = [k["name"] for k in baza.execute("PRAGMA table_info(fragmenty)")]
        if "miejsce" not in kolumny:
            baza.execute("ALTER TABLE fragmenty ADD COLUMN miejsce TEXT")
            baza.execute("UPDATE fragmenty SET miejsce = 'str. ' || strona")


_przygotuj()


# ---------- embeddingi ----------

_model = None


def _model_embeddingow():
    """Ładuje model tylko raz (przy pierwszym użyciu), potem korzysta z gotowego."""
    global _model
    if _model is None:
        _model = TextEmbedding(MODEL_EMBEDDINGOW, cache_dir=str(FOLDER_MODELI))
    return _model


def _wektory(teksty):
    return np.array(list(_model_embeddingow().embed(teksty)), dtype=np.float32)


# ---------- odczyt plików ----------

def _wyciagnij(sciezka):
    """Zwraca listę trójek (numer, miejsce, tekst): strony PDF-a albo sekcje DOCX-a."""
    rozszerzenie = sciezka.suffix.lower()

    if rozszerzenie == ".pdf":
        wynik = []
        for i, strona in enumerate(pymupdf4llm.to_markdown(str(sciezka), page_chunks=True)):
            numer = strona.get("metadata", {}).get("page_number", i + 1)
            wynik.append((numer, f"str. {numer}", strona.get("text", "")))
        return wynik

    if rozszerzenie == ".docx":
        sekcje = []
        naglowek = "początek dokumentu"
        bufor = []
        for akapit in docx.Document(str(sciezka)).paragraphs:
            tekst = akapit.text.strip()
            if not tekst:
                continue
            styl = (akapit.style.name or "").lower()
            if styl.startswith(("heading", "nagłówek", "title", "tytuł")):
                if bufor:
                    sekcje.append((naglowek, "\n\n".join(bufor)))
                    bufor = []
                naglowek = tekst
            else:
                bufor.append(tekst)
        if bufor:
            sekcje.append((naglowek, "\n\n".join(bufor)))
        return [(i + 1, nag, tekst) for i, (nag, tekst) in enumerate(sekcje)]

    raise ValueError("Obsługiwane formaty: PDF i DOCX.")


# ---------- cięcie tekstu ----------

def _podziel(tekst):
    """Tnie tekst na fragmenty, starając się ciąć na końcu akapitu albo zdania."""
    fragmenty = []
    start = 0
    while start < len(tekst):
        koniec = start + DLUGOSC_FRAGMENTU
        if koniec < len(tekst):
            polowa = start + DLUGOSC_FRAGMENTU // 2
            ciecie = tekst.rfind("\n\n", polowa, koniec)
            if ciecie == -1:
                ciecie = tekst.rfind(". ", polowa, koniec)
            if ciecie != -1:
                koniec = ciecie + 1
        fragment = tekst[start:koniec].strip()
        if fragment:
            fragmenty.append(fragment)
        if koniec >= len(tekst):
            break
        start = koniec - ZAKLADKA
    return fragmenty


# ---------- operacje na dokumentach ----------

def dodaj_dokument(kolekcja, nazwa_pliku, dane):
    """Zapisuje plik, tnie na fragmenty, liczy embeddingi. Zwraca (stron/sekcji, fragmentów)."""
    from pathlib import Path
    if Path(nazwa_pliku).suffix.lower() not in OBSLUGIWANE:
        raise ValueError("Obsługiwane formaty: PDF i DOCX.")

    folder = FOLDER_PLIKOW / kolekcja
    folder.mkdir(parents=True, exist_ok=True)
    sciezka = folder / nazwa_pliku
    sciezka.write_bytes(dane)

    # Ten sam plik wgrany ponownie? Usuń starą wersję z bazy
    with _polacz() as baza:
        stare = baza.execute(
            "SELECT id FROM dokumenty WHERE kolekcja = ? AND plik = ?", (kolekcja, nazwa_pliku)
        ).fetchall()
    for s in stare:
        _usun_z_bazy(s["id"])

    jednostki = _wyciagnij(sciezka)
    fragmenty = []  # trójki (numer, miejsce, tekst)
    for numer, miejsce, tekst in jednostki:
        for f in _podziel(tekst):
            if len(f) >= MIN_DLUGOSC:
                fragmenty.append((numer, miejsce, f))

    if not fragmenty:
        sciezka.unlink(missing_ok=True)
        raise ValueError("Nie udało się odczytać tekstu. To może być skan (zdjęcie strony), a skanów v1 jeszcze nie obsługuje.")

    wektory = _wektory([tekst for _, _, tekst in fragmenty])

    with _polacz() as baza:
        kursor = baza.execute(
            "INSERT INTO dokumenty (kolekcja, plik, stron, dodano) VALUES (?, ?, ?, ?)",
            (kolekcja, nazwa_pliku, len(jednostki), datetime.now().isoformat(timespec="seconds")),
        )
        dokument_id = kursor.lastrowid
        baza.executemany(
            "INSERT INTO fragmenty (dokument_id, strona, miejsce, tresc, wektor) VALUES (?, ?, ?, ?, ?)",
            [(dokument_id, nr, miejsce, tekst, w.tobytes())
             for (nr, miejsce, tekst), w in zip(fragmenty, wektory)],
        )
    return len(jednostki), len(fragmenty)


def lista_dokumentow(kolekcja):
    with _polacz() as baza:
        return baza.execute("""
            SELECT d.id, d.plik, d.stron, COUNT(f.id) AS fragmentow
            FROM dokumenty d LEFT JOIN fragmenty f ON f.dokument_id = d.id
            WHERE d.kolekcja = ?
            GROUP BY d.id ORDER BY d.plik
        """, (kolekcja,)).fetchall()


def _usun_z_bazy(dokument_id):
    with _polacz() as baza:
        baza.execute("DELETE FROM fragmenty WHERE dokument_id = ?", (dokument_id,))
        baza.execute("DELETE FROM dokumenty WHERE id = ?", (dokument_id,))


def usun_dokument(dokument_id):
    with _polacz() as baza:
        wiersz = baza.execute("SELECT kolekcja, plik FROM dokumenty WHERE id = ?", (dokument_id,)).fetchone()
    if wiersz:
        (FOLDER_PLIKOW / wiersz["kolekcja"] / wiersz["plik"]).unlink(missing_ok=True)
    _usun_z_bazy(dokument_id)


# ---------- wyszukiwanie ----------

def szukaj(kolekcja, pytanie, ile=5):
    """Zwraca fragmenty najbardziej podobne znaczeniowo do pytania."""
    with _polacz() as baza:
        wiersze = baza.execute("""
            SELECT f.miejsce, f.tresc, f.wektor, d.plik
            FROM fragmenty f JOIN dokumenty d ON d.id = f.dokument_id
            WHERE d.kolekcja = ?
        """, (kolekcja,)).fetchall()
    if not wiersze:
        return []

    q = _wektory([pytanie])[0]
    macierz = np.stack([np.frombuffer(w["wektor"], dtype=np.float32) for w in wiersze])
    podobienstwo = macierz @ q / (np.linalg.norm(macierz, axis=1) * np.linalg.norm(q) + 1e-9)
    najlepsze = np.argsort(-podobienstwo)[:ile]

    return [
        {
            "plik": wiersze[i]["plik"],
            "miejsce": wiersze[i]["miejsce"],
            "tresc": wiersze[i]["tresc"],
            "wynik": float(podobienstwo[i]),
        }
        for i in najlepsze
    ]


# ---------- pełny tekst ----------

def tekst_dokumentow(kolekcja):
    """Cały tekst wszystkich dokumentów kolekcji, z oznaczeniem pliku i miejsca."""
    czesci = []
    for d in lista_dokumentow(kolekcja):
        sciezka = FOLDER_PLIKOW / kolekcja / d["plik"]
        if not sciezka.exists():
            continue
        for _, miejsce, tekst in _wyciagnij(sciezka):
            tekst = tekst.strip()
            if tekst:
                czesci.append(f"=== {d['plik']}, {miejsce} ===\n{tekst}")
    return "\n\n".join(czesci)