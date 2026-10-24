from pathlib import Path
from platformdirs import user_data_dir

# Folder na dane aplikacji, właściwy dla danego systemu
FOLDER_DANYCH = Path(user_data_dir("Diploma", appauthor=False))

# Utwórz folder, jeśli jeszcze nie istnieje
FOLDER_DANYCH.mkdir(parents=True, exist_ok=True)