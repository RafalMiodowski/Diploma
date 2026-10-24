import tempfile
from pathlib import Path

from app import baza_wiedzy

# Pliki tekstowe i z kodem, które czytamy wprost jako tekst
TEKSTOWE = {
    ".txt", ".md", ".tex", ".bib", ".csv", ".json", ".xml", ".yml", ".yaml", ".sql",
    ".py", ".ipynb", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
    ".java", ".kt", ".c", ".h", ".cpp", ".hpp", ".cs", ".go", ".rs", ".php", ".rb", ".m", ".r",
}

# Bezpiecznik: ok. 15 tys. tokenów na jeden załącznik
MAKS_ZNAKOW = 60_000


def tekst_z_pliku(nazwa, dane):
    """Zamienia załączony plik na tekst, który zrozumie asystent."""
    rozszerzenie = Path(nazwa).suffix.lower()

    if rozszerzenie in (".pdf", ".docx"):
        # Korzystamy z tego samego odczytu co baza wiedzy (strony PDF / sekcje DOCX)
        with tempfile.TemporaryDirectory() as folder:
            sciezka = Path(folder) / nazwa
            sciezka.write_bytes(dane)
            czesci = baza_wiedzy._wyciagnij(sciezka)
        tekst = "\n\n".join(f"[{miejsce}]\n{tresc.strip()}" for _, miejsce, tresc in czesci if tresc.strip())
    elif rozszerzenie in TEKSTOWE:
        tekst = dane.decode("utf-8", errors="replace")
    else:
        raise ValueError("Nieobsługiwany format. Załącz PDF, DOCX albo plik tekstowy / z kodem.")

    if not tekst.strip():
        raise ValueError("Plik nie zawiera tekstu do odczytania.")
    if len(tekst) > MAKS_ZNAKOW:
        tekst = tekst[:MAKS_ZNAKOW] + "\n\n[...dalsza część pliku została ucięta, bo plik jest bardzo długi...]"
    return tekst