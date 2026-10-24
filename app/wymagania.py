import anthropic
from app import klucz_api, koszty, ustawienia
from app.sciezki import FOLDER_DANYCH

PLIK = FOLDER_DANYCH / "wymagania.md"

# Kartę wymagań zawsze robi Sonnet: zadanie jest proste (wyciąganie faktów), a dokumentów dużo
MODEL = "claude-sonnet-5-5"

# Bezpiecznik: ok. 100 tys. tokenów. Wystarczy na ok. 10 typowych dokumentów uczelni.
MAKS_ZNAKOW = 400_000

POLECENIE = """Powyżej są dokumenty uczelni dotyczące pracy dyplomowej (regulaminy, zarządzenia, wytyczne).
Każda strona jest oznaczona nagłówkiem "=== plik, str. N ===".

Przygotuj zwięzłą KARTĘ WYMAGAŃ dla studenta piszącego pracę inżynierską. Użyj formatu Markdown i poniższych sekcji:

## Terminy
## Formatowanie (czcionka, rozmiar, interlinia, marginesy, wyrównanie, numeracja stron, nagłówki)
## Struktura pracy (obowiązkowe elementy i ich kolejność)
## Strona tytułowa
## Bibliografia i cytowanie
## Rysunki, tabele, wzory
## Objętość pracy
## Złożenie pracy (forma, pliki, system antyplagiatowy, oświadczenia)
## Zasady korzystania z narzędzi AI
## Egzamin dyplomowy
## Inne ważne wymagania

Zasady:
- Każdy punkt to krótka, konkretna informacja (np. "Czcionka: Times New Roman, 12 pt").
- Przy KAŻDYM punkcie podaj źródło w nawiasie, np. (Regulamin.pdf, str. 4).
- Używaj wyłącznie informacji z dokumentów. Niczego nie dopowiadaj z ogólnej wiedzy.
- Jeśli dla danej sekcji dokumenty nic nie mówią, napisz: "Brak informacji w dokumentach."
- Jeśli dokumenty są ze sobą sprzeczne, podaj obie wersje ze źródłami i oznacz to słowem "SPRZECZNOŚĆ".
- Nie dodawaj wstępu ani podsumowania. Zacznij od pierwszej sekcji.
"""


def wczytaj():
    return PLIK.read_text(encoding="utf-8") if PLIK.exists() else ""


def zapisz(tekst):
    PLIK.write_text(tekst, encoding="utf-8")


async def generuj(tekst_dokumentow, przy_kawalku):
    """Wysyła dokumenty do Claude i strumieniuje kartę wymagań. Zwraca (wiadomość, koszt)."""
    ustawienia.sprawdz_limit()
    client = anthropic.AsyncAnthropic(api_key=klucz_api.wczytaj_klucz())
    tresc = f"<dokumenty>\n{tekst_dokumentow}\n</dokumenty>\n\n{POLECENIE}"
    async with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": tresc}],
    ) as strumien:
        async for kawalek in strumien.text_stream:
            przy_kawalku(kawalek)
        wiadomosc = await strumien.get_final_message()
    _, koszt = koszty.zapisz("karta wymagań", MODEL, wiadomosc.usage)
    return wiadomosc, koszt