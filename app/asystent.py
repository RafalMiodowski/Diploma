import asyncio

import anthropic
from app import klucz_api, projekt, wymagania, baza_wiedzy, koszty, ustawienia

# Ile ostatnich wiadomości wysyłamy do modelu (sufit kosztów jednego pytania)
MAKS_WIADOMOSCI = 20

# Ile razy z rzędu asystent może użyć narzędzi przy jednym pytaniu (bezpiecznik)
MAKS_KROKOW = 6

# Ile fragmentów zwraca jedno wyszukiwanie
ILE_FRAGMENTOW = 5

# Id rozmowy otwartej na ekranie (None = nowa, jeszcze niezapisana)
aktywna_rozmowa = None

INSTRUKCJE = """Jesteś osobistym asystentem studenta piszącego pracę inżynierską.

Zasady ogólne:
- Trzymaj się tematu, celu i zakresu pracy z karty projektu poniżej. Jeśli prośba wykracza poza zakres pracy, zwróć na to uwagę.
- Zawsze odpowiadaj po polsku, także gdy źródła są po angielsku. Treści do pracy pisz stylem akademickim, chyba że student poprosi inaczej.
- Pomagaj tak, żeby student rozumiał i rozwijał swoją pracę: wyjaśniaj, proponuj, poprawiaj, zadawaj pytania, gdy czegoś brakuje.
- Jeśli w rozmowie zapadnie ważna decyzja dotycząca pracy, zasugeruj studentowi dopisanie jej do karty projektu.

Wymagania uczelni:
- Pytania o wymogi formalne (formatowanie, terminy, struktura, cytowanie) opieraj najpierw na sekcji "Wymagania uczelni".
- Jeśli karta wymagań nie zawiera odpowiedzi albo potrzebne jest dokładne brzmienie przepisu, użyj narzędzia szukaj_w_wymaganiach.
- Gdy piszesz lub poprawiasz treści do pracy, pilnuj zgodności z wymaganiami uczelni.

Materiały źródłowe:
- Gdy pytanie dotyczy treści merytorycznych, które mogą być w materiałach studenta, użyj narzędzia szukaj_w_zrodlach.
- Możesz szukać kilka razy, różnymi słowami. Materiały bywają po angielsku, więc przy terminach fachowych szukaj też angielskimi słowami.
- Źródła podawaj wyłącznie na podstawie wyników narzędzi, w formacie (nazwa_pliku, str. N) albo (nazwa_pliku, sekcja).
- Gdy przytaczasz treść z angielskiego źródła, zaznacz, że to tłumaczenie, dopisując "(tłum.)". Na prośbę podaj oryginalne brzmienie.
- Jeśli wyniki wyszukiwania nie zawierają odpowiedzi, powiedz to wprost. Nie uzupełniaj braków wymyślonymi źródłami.

Załączniki i kod:
- Treść w znacznikach <zalacznik> to plik dołączony przez studenta (np. jego rozdział albo kod). Formatowanie (czcionki, marginesy) nie jest w nim widoczne, więc go nie oceniaj.
- Przy kodzie: wyjaśniaj przyczynę problemu, podawaj kompletne fragmenty kodu i opisuj, co zmieniłeś. Pamiętaj, że kod jest częścią pracy inżynierskiej.

Nigdy nie wymyślaj źródeł, cytatów, danych ani wymagań uczelni.
"""

NARZEDZIA = [
    {
        "name": "szukaj_w_wymaganiach",
        "description": (
            "Przeszukuje dokumenty uczelni dotyczące pracy dyplomowej (regulaminy, zarządzenia, wytyczne redakcyjne). "
            "Zwraca najbardziej pasujące fragmenty z nazwą pliku i stroną."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "zapytanie": {
                    "type": "string",
                    "description": "Czego szukać: konkretne pytanie albo fraza, np. 'marginesy i interlinia'.",
                }
            },
            "required": ["zapytanie"],
        },
    },
    {
        "name": "szukaj_w_zrodlach",
        "description": (
            "Przeszukuje materiały źródłowe studenta: przykładowe prace dyplomowe, artykuły naukowe, notatki. "
            "Materiały mogą być po polsku lub po angielsku. Zwraca najbardziej pasujące fragmenty z nazwą pliku i miejscem."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "zapytanie": {
                    "type": "string",
                    "description": "Czego szukać: konkretne pytanie albo fraza. Przy terminach fachowych warto użyć angielskich słów.",
                }
            },
            "required": ["zapytanie"],
        },
    },
]

# Które narzędzie przeszukuje którą kolekcję
KOLEKCJE = {
    "szukaj_w_wymaganiach": "uczelnia",
    "szukaj_w_zrodlach": "zrodla",
}


def _spis(kolekcja):
    dokumenty = baza_wiedzy.lista_dokumentow(kolekcja)
    return "\n".join(f"- {d['plik']}" for d in dokumenty) or "(brak dokumentów)"


def prompt_systemowy():
    karta = projekt.jako_tekst() or "(Student nie uzupełnił jeszcze karty projektu.)"
    wym = wymagania.wczytaj() or "(Student nie przygotował jeszcze karty wymagań uczelni.)"
    tekst = (
        INSTRUKCJE
        + "\n\n# Karta projektu\n\n" + karta
        + "\n\n# Wymagania uczelni (zweryfikowane przez studenta)\n\n" + wym
        + "\n\n# Dostępne dokumenty uczelni\n\n" + _spis("uczelnia")
        + "\n\n# Dostępne materiały źródłowe\n\n" + _spis("zrodla")
    )
    return [{"type": "text", "text": tekst, "cache_control": {"type": "ephemeral"}}]


def przytnij(historia):
    """Zostawia tylko ostatnie wiadomości. Rozmowa musi zaczynać się od pytania użytkownika."""
    if len(historia) <= MAKS_WIADOMOSCI:
        return historia
    przyciete = historia[-MAKS_WIADOMOSCI:]
    while przyciete and przyciete[0]["role"] != "user":
        przyciete = przyciete[1:]
    return przyciete


def wykonaj_narzedzie(nazwa, wejscie):
    """Wykonuje narzędzie, o które poprosił model. Zwraca (tekst dla modelu, lista trafień)."""
    kolekcja = KOLEKCJE.get(nazwa)
    if not kolekcja:
        return f"Nieznane narzędzie: {nazwa}", []

    trafienia = baza_wiedzy.szukaj(kolekcja, wejscie.get("zapytanie", ""), ILE_FRAGMENTOW)
    if not trafienia:
        return "Brak wyników: baza jest pusta albo nic nie pasuje do zapytania.", []

    tekst = "\n\n".join(
        f"[{i}] {t['plik']}, {t['miejsce']}\n{t['tresc']}"
        for i, t in enumerate(trafienia, start=1)
    )
    return tekst, trafienia


async def odpowiedz(historia, przy_kawalku, przy_narzedziu):
    """
    Pętla agenta: model odpowiada albo prosi o narzędzie; my wykonujemy narzędzie
    i odsyłamy wyniki, aż model napisze końcową odpowiedź.
    Zwraca podsumowanie: zużycie tokenów i fragmenty, które asystent przeczytał.
    """
    ustawienia.sprawdz_limit()

    model = ustawienia.model()
    client = anthropic.AsyncAnthropic(api_key=klucz_api.wczytaj_klucz())
    wiadomosci = list(przytnij(historia))
    podsumowanie = {"wejscie": 0, "cache": 0, "wyjscie": 0, "koszt": 0.0,
                    "model": model, "fragmenty": [], "kroki": 0}

    for _ in range(MAKS_KROKOW):
        napisano_tekst = False
        async with client.messages.stream(
            model=model,
            max_tokens=4000,
            system=prompt_systemowy(),
            tools=NARZEDZIA,
            messages=wiadomosci,
        ) as strumien:
            async for kawalek in strumien.text_stream:
                napisano_tekst = True
                przy_kawalku(kawalek)
            odpowiedz_modelu = await strumien.get_final_message()

        # Każde wywołanie API od razu trafia do licznika kosztów
        tokeny, koszt = koszty.zapisz("czat", model, odpowiedz_modelu.usage)
        podsumowanie["wejscie"] += tokeny["wejscie"] + tokeny["cache_zapis"] + tokeny["cache_odczyt"]
        podsumowanie["cache"] += tokeny["cache_odczyt"]
        podsumowanie["wyjscie"] += tokeny["wyjscie"]
        podsumowanie["koszt"] += koszt

        # Model skończył: nie prosi o żadne narzędzie
        if odpowiedz_modelu.stop_reason != "tool_use":
            return podsumowanie

        # Model prosi o narzędzia: wykonujemy je i odsyłamy wyniki
        podsumowanie["kroki"] += 1
        if napisano_tekst:
            przy_kawalku("\n\n")
        wiadomosci.append({"role": "assistant", "content": odpowiedz_modelu.content})

        wyniki = []
        for blok in odpowiedz_modelu.content:
            if blok.type == "tool_use":
                przy_narzedziu(blok.name, blok.input)
                tekst, trafienia = await asyncio.to_thread(wykonaj_narzedzie, blok.name, blok.input)
                podsumowanie["fragmenty"].extend(trafienia)
                wyniki.append({"type": "tool_result", "tool_use_id": blok.id, "content": tekst})
        wiadomosci.append({"role": "user", "content": wyniki})

    przy_kawalku("\n\n_(Przerwano: asystent użył narzędzi zbyt wiele razy z rzędu.)_")
    return podsumowanie


def przyjazny_blad(e):
    """Zamienia techniczny błąd na komunikat zrozumiały dla użytkownika."""
    tekst = str(e).lower()
    if isinstance(e, ustawienia.LimitPrzekroczony):
        return (f"Osiągnięto miesięczny limit wydatków (${ustawienia.limit():.2f}). "
                "Możesz go zmienić w Ustawieniach.")
    if isinstance(e, anthropic.AuthenticationError):
        return "Klucz API jest nieprawidłowy. Zmień go w Ustawieniach."
    if "credit balance" in tekst:
        return "Brak środków na koncie API. Doładuj konto w Billing na platform.claude.com."
    if isinstance(e, anthropic.RateLimitError):
        return "Za dużo zapytań naraz. Odczekaj chwilę i spróbuj ponownie."
    if isinstance(e, anthropic.APIConnectionError):
        return "Brak połączenia z internetem."
    if isinstance(e, anthropic.APIStatusError) and e.status_code >= 500:
        return "Serwery Claude są chwilowo przeciążone. Spróbuj za moment."
    return f"Nieoczekiwany błąd: {e}"