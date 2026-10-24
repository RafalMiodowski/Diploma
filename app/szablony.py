# Gotowe polecenia dla asystenta: (nazwa przycisku, ikona, treść polecenia)
# Fragmenty w [nawiasach kwadratowych] student uzupełnia przed wysłaniem.

SZABLONY = [
    (
        "Recenzja rozdziału",
        "rate_review",
        "Wciel się w wymagającego, ale życzliwego promotora i zrecenzuj załączony rozdział mojej pracy. Oceń:\n"
        "1. zgodność z tematem, celem i zakresem pracy,\n"
        "2. logikę wywodu i strukturę,\n"
        "3. poprawność merytoryczną i braki,\n"
        "4. wykorzystanie i poprawność źródeł,\n"
        "5. styl akademicki i język.\n"
        "Na końcu podaj listę konkretnych poprawek, od najważniejszej.",
    ),
    (
        "Zgodność z wymogami",
        "rule",
        "Sprawdź załączony tekst pod kątem zgodności z wymaganiami uczelni: struktura, styl, cytowanie i bibliografia, "
        "podpisy rysunków i tabel, inne wymogi z karty wymagań. Każdą niezgodność wypisz w formie: "
        "problem → wymaganie (źródło) → propozycja poprawki. "
        "Formatowanie (czcionka, marginesy) nie jest widoczne w załączniku, więc tego nie oceniaj.",
    ),
    (
        "Korekta językowa",
        "spellcheck",
        "Popraw załączony tekst pod względem językowym: ortografia, interpunkcja, gramatyka i styl akademicki. "
        "Nie zmieniaj treści merytorycznej. Najpierw podaj poprawioną wersję, "
        "potem listę najważniejszych zmian z krótkim uzasadnieniem.",
    ),
    (
        "Pomoc z kodem",
        "code",
        "Pomóż mi z kodem z części praktycznej mojej pracy. Problem: [opisz, co ma robić, co nie działa, treść błędu]\n\n"
        "Wyjaśnij przyczynę, zaproponuj poprawkę z pełnym fragmentem kodu "
        "i krótko podpowiedz, jak to rozwiązanie opisać w pracy.",
    ),
    (
        "Plan rozdziału",
        "list_alt",
        "Zaproponuj szczegółowy plan rozdziału [numer i tytuł] mojej pracy: podrozdziały, co opisać w każdym "
        "i z których moich materiałów źródłowych skorzystać. Pilnuj zakresu pracy i wymagań uczelni co do struktury.",
    ),
    (
        "Szukaj w źródłach",
        "travel_explore",
        "Znajdź w moich materiałach źródłowych wszystko na temat: [temat]. "
        "Dla każdego wątku podaj krótkie streszczenie po polsku i źródło (plik, strona).",
    ),
]