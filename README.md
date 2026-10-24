# Diploma

Agent AI do pisania prac dyplomowych. Zamiast ogólnego czatu, któremu przy każdej rozmowie tłumaczysz wszystko od nowa, Diploma od początku zna Twój temat, wymagania uczelni i Twoje źródła.

**Pobierz:** https://rafalmiodowski.github.io/Diploma/

Wersja 1.0, projekt rozwojowy. Na razie tylko Windows.

## Co potrafi

- pamięta temat, cel i zakres Twojej pracy w każdej rozmowie
- zbiera wymagania uczelni i Twoje materiały w jednym miejscu
- sam przeszukuje Twoje dokumenty i podaje, skąd wziął informacje
- recenzuje rozdziały, sprawdza zgodność z wymogami, pomaga z kodem
- pokazuje koszty i pilnuje miesięcznego limitu
- trzyma wszystkie dane lokalnie, na Twoim komputerze

## Jak zacząć

1. Pobierz i rozpakuj `Diploma-windows.zip`, uruchom `Diploma.exe`.
2. Utwórz klucz API na [platform.claude.com](https://platform.claude.com) i wklej go w aplikacji.
3. Uzupełnij kartę projektu, wgraj dokumenty i pytaj.

Program jest darmowy, płacisz tylko za użycie Claude z własnego konta. Szczegóły w [INSTRUKCJA.txt](INSTRUKCJA.txt).

## Z kodu

```
pip install -r requirements.txt
python main.py        # uruchomienie
python zbuduj.py      # budowanie .exe
```

Zbudowane w Pythonie z NiceGUI, Claude API, lokalnym RAG (fastembed + SQLite) i PyInstallerem.

Pomysły i błędy: [Issues](../../issues). Licencja: [AGPL-3.0](LICENSE). Autor: Rafał Miodowski.
