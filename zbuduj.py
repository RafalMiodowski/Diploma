"""
Buduje aplikację Diploma i pakuje ją w ZIP gotowy do wysłania.

Uruchomienie (z głównego folderu projektu, z włączonym .venv):
    python zbuduj.py              -> wersja do rozsyłania (bez okna konsoli)
    python zbuduj.py --konsola    -> wersja testowa z oknem konsoli (widać błędy)

Wynik: folder dist/Diploma oraz plik dist/Diploma-<wersja>-<system>.zip
"""
import importlib.metadata
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import nicegui

NAZWA = "Diploma"
WERSJA = "1.0"

KATALOG = Path(__file__).resolve().parent
KONSOLA = "--konsola" in sys.argv
SYSTEM = {"Windows": "windows", "Darwin": "macos"}.get(platform.system(), "linux")
SEP = os.pathsep  # ";" na Windowsie, ":" na macOS/Linuksie

# Biblioteki z plikami binarnymi/danymi, które PyInstaller musi zabrać w całości
ZABIERZ_W_CALOSCI = [
    "fastembed", "onnxruntime", "tokenizers", "py_rust_stemmers",
    "pymupdf", "pymupdf4llm", "docx",
]

# Biblioteki, które przy starcie sprawdzają swoje "metadane" (wersję itp.)
METADANE = ["keyring", "fastembed", "huggingface-hub", "anthropic", "nicegui", "tokenizers"]


def main():
    polecenie = [
        sys.executable, "-m", "PyInstaller", "main.py",
        "--name", NAZWA,
        "--onedir",
        "--noconfirm",
        "--clean",
        "--add-data", f"{Path(nicegui.__file__).parent}{SEP}nicegui",
        "--add-data", f"static{SEP}static",
        "--collect-submodules", "keyring",
        "--icon", "static/ikona.ico" if SYSTEM == "windows" else "static/ikona.png",
    ]
    if not KONSOLA:
        polecenie.append("--windowed")

    for pakiet in ZABIERZ_W_CALOSCI:
        if importlib.util.find_spec(pakiet):
            polecenie += ["--collect-all", pakiet]

    for pakiet in METADANE:
        try:
            importlib.metadata.distribution(pakiet)
            polecenie += ["--copy-metadata", pakiet]
        except importlib.metadata.PackageNotFoundError:
            pass

    print("Buduję aplikację. To potrwa kilka minut...\n")
    subprocess.run(polecenie, check=True, cwd=KATALOG)

    dist = KATALOG / "dist"
    folder_aplikacji = dist / (f"{NAZWA}.app" if SYSTEM == "macos" and not KONSOLA else NAZWA)

    # Instrukcja dla użytkownika obok programu
    instrukcja = KATALOG / "INSTRUKCJA.txt"
    if instrukcja.exists() and folder_aplikacji.is_dir() and SYSTEM != "macos":
        shutil.copy(instrukcja, folder_aplikacji / "INSTRUKCJA.txt")

    # Stała nazwa pliku (bez numeru wersji), żeby link "najnowsza wersja" na stronie zawsze działał.
    # Numer wersji podajesz w GitHub Releases jako tag, np. v1.0
    dopisek = "-test" if KONSOLA else ""
    archiwum = shutil.make_archive(
        str(dist / f"{NAZWA}-{SYSTEM}{dopisek}"), "zip",
        root_dir=dist, base_dir=folder_aplikacji.name,
    )
    rozmiar = Path(archiwum).stat().st_size / 1024 / 1024
    print(f"\nGotowe!\n  Program: {folder_aplikacji}\n  Paczka:  {archiwum} ({rozmiar:.0f} MB)")


if __name__ == "__main__":
    main()