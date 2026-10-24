import keyring
import anthropic

# Pod tą nazwą klucz będzie widoczny w systemowym sejfie haseł
SERWIS = "Diploma"
NAZWA = "anthropic_api_key"


def wczytaj_klucz():
    """Zwraca zapisany klucz albo None, jeśli go nie ma."""
    try:
        return keyring.get_password(SERWIS, NAZWA)
    except Exception:
        return None


def zapisz_klucz(klucz):
    keyring.set_password(SERWIS, NAZWA, klucz)


def usun_klucz():
    try:
        keyring.delete_password(SERWIS, NAZWA)
    except Exception:
        pass


def sprawdz_klucz(klucz):
    """Sprawdza klucz u Anthropic. Zwraca (czy_ok, komunikat)."""
    if not klucz.startswith("sk-ant-"):
        return False, "To nie wygląda na klucz Claude. Powinien zaczynać się od sk-ant-"
    try:
        # Pobranie listy modeli nic nie kosztuje, a wymaga poprawnego klucza
        anthropic.Anthropic(api_key=klucz).models.list(limit=1)
        return True, "Połączono"
    except anthropic.AuthenticationError:
        return False, "Klucz jest nieprawidłowy albo został usunięty."
    except anthropic.APIConnectionError:
        return False, "Brak połączenia z internetem."
    except Exception as e:
        return False, f"Nieoczekiwany błąd: {e}"