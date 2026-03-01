from __future__ import annotations

import csv
from pathlib import Path

from config import AAC_AUDIOS_DIR, AAC_LIBRARY_PATH
from services.audio import create_audio


def main() -> None:
    with open(AAC_LIBRARY_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    print(f"Regenerating TTS for {total} cards...")

    for i, row in enumerate(rows, start=1):
        category = row["category"].strip()
        word = row["word"].strip()
        target = AAC_AUDIOS_DIR / category / f"{word}.mp3"
        create_audio(category, word, target)
        print(f"[{i}/{total}] {category} - {word}")

    print("Done.")


if __name__ == "__main__":
    main()
