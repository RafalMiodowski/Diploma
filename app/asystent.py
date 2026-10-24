import anthropic
from app import klucz_api, projekt

MODEL = "claude-sonnet-5-5"

# Rozmowa trzymana w pamięci, dopóki aplikacja jest włączona.
# (W kroku 6 nauczymy ją zapisywać na dysku.)
ROZMOWA = []

INSTRUKCJE = """Jesteś osobistym asystentem studenta piszącego pracę inżynierską.

Zasady:
- Trzymaj się tematu, celu i zakresu pracy z karty projektu poniżej. Jeśli prośba wykracza poza zakres pracy, zwróć na to uwagę.
- Odpowiadaj po polsku. Treści do pracy pisz stylem akademickim, chyba że student poprosi inaczej.
- Nie wymyślaj źródeł, cytatów, danych ani wymagań uczelni. Jeśli czegoś nie wiesz, powiedz to wprost.
- Pomagaj tak, żeby student rozumiał i rozwijał swoją pracę: wyjaśniaj, proponuj, poprawiaj, zadawaj pytania, gdy czegoś brakuje.
"""


def prompt_systemowy():
    karta = projekt.jako_tekst() or "(Student nie uzupełnił jeszcze karty projektu.)"
    return [
        {
            "type": "text",
            "text": INSTRUKCJE + "\n\n# Karta projektu\n\n" + karta,
            "cache_control": {"type": "ephemeral"},
        }
    ]


async def odpowiedz(historia, przy_kawalku):
    """Wysyła rozmowę do Claude i przekazuje odpowiedź kawałek po kawałku."""
    client = anthropic.AsyncAnthropic(api_key=klucz_api.wczytaj_klucz())
    async with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        system=prompt_systemowy(),
        messages=historia,
    ) as strumien:
        async for kawalek in strumien.text_stream:
            przy_kawalku(kawalek)
        return await strumien.get_final_message()


def przyjazny_blad(e):
    """Zamienia techniczny błąd na komunikat zrozumiały dla użytkownika."""
    tekst = str(e).lower()
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