from __future__ import annotations

import base64
import csv
import re
import time
from io import BytesIO
from pathlib import Path
from typing import List

import pandas as pd
from PIL import Image
from pydantic import BaseModel

from config import AAC_AUDIOS_DIR, AAC_IMAGES_DIR, AAC_LIBRARY_PATH
from services.audio import create_audio
from services.openai_client import get_client

VALID_CATEGORIES = ["People", "Feelings", "Food", "Places", "Actions", "Objects", "Questions", "Time"]
CATEGORY_ALIASES = {
    "사람": "People",
    "감정": "Feelings",
    "음식": "Food",
    "장소": "Places",
    "행동": "Actions",
    "물건": "Objects",
    "질문": "Questions",
    "시간": "Time",
}
ENGLISH_WORD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\s\-']*$")


class AACAugmentation(BaseModel):
    context_summary: str
    missing_words: List[str]
    missing_from_library: List[bool]


def is_english_word(text: str) -> bool:
    candidate = (text or "").strip()
    return bool(candidate and ENGLISH_WORD_RE.match(candidate))


def generate_image(target_word: str, filename: Path) -> None:
    print(f"▶ Generating image for '{target_word}' in ARASAAC style…")
    client = get_client()
    result = client.images.generate(
        model="gpt-image-1",
        prompt=f'Draw an image of "{target_word}" in ARASAAC card style without any text on it.',
        size="1024x1024",
    )

    b64 = result.data[0].b64_json.split(",")[-1]
    b64 += "=" * (-len(b64) % 4)
    image = Image.open(BytesIO(base64.b64decode(b64)))
    filename.parent.mkdir(parents=True, exist_ok=True)
    image.save(filename)
    print("Image saved done:", filename)


def _request_missing_words(conversation_history, aac_library_df: pd.DataFrame, min_count: int) -> AACAugmentation:
    client = get_client()
    response = client.responses.parse(
        model="gpt-4.1-2025-04-14",
        input=[
            {
                "role": "system",
                "content": (
                    "You are an AAC support assistant. Your job is to help expand an AAC word library.\n\n"
                    "Given a conversation history between a nonverbal AAC user and a counterpart, and a list of available AAC cards "
                    "in 'category-word' format, extract:\n"
                    "1. A sentence summarizing the time/place/occasion of the conversation.\n"
                    "2. A list of important English words or short phrases that were likely needed but do not exist in the AAC library, in 'category-word' format.\n\n"
                    "Think step-by-step about what the user tried to express and what vocabulary was needed, then check what's missing.\n\n"
                    f"Valid categories are: {VALID_CATEGORIES}. Avoid duplicates or similar words already in the AAC library. "
                    f"Only include words that are important and missing from aac_library. "
                    f"You must return at least {min_count} missing words."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Conversation history:{conversation_history} "
                    f"AAC library: {aac_library_df['category']+'-'+aac_library_df['word']} "
                    "YOU should double check to ensure new words not in this aac library."
                ),
            },
        ],
        text_format=AACAugmentation,
    )
    return response.output_parsed


def suggest_missing_words(conversation_history, aac_library_df: pd.DataFrame, min_count: int = 3, max_attempts: int = 3):
    suggestions = []
    attempts = 0

    while attempts < max_attempts and len(suggestions) < min_count:
        attempts += 1
        output = _request_missing_words(conversation_history, aac_library_df, min_count)
        print("New cards suggested by model: ", output.missing_words)

        for word_pair in output.missing_words:
            try:
                c, w = word_pair.split("-")
            except ValueError:
                print(f"Invalid format for missing word '{word_pair}'. Skipping.")
                continue
            c = CATEGORY_ALIASES.get(c, c)
            if c not in VALID_CATEGORIES:
                print(f"Invalid category '{c}' for word '{w}'. Skipping.")
                continue
            if not is_english_word(w):
                print(f"Invalid non-English word '{w}'. Skipping.")
                continue
            if ((aac_library_df["category"] == c) & (aac_library_df["word"] == w)).any():
                print(f"Word '{w}' in category '{c}' already exists. Skipping.")
                continue
            if not any(s["category"] == c and s["word"] == w for s in suggestions):
                suggestions.append({"category": c, "word": w})

    return suggestions[:max(min_count, len(suggestions))]


def augmentation_logic(conversation_history, aac_library_df: pd.DataFrame):
    start_time = time.time()
    output = _request_missing_words(conversation_history, aac_library_df, min_count=3)
    print("New cards suggested by model: ", output.missing_words)

    new_cards_added = []
    with open(AAC_LIBRARY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for word_pair in output.missing_words:
            try:
                c, w = word_pair.split("-")
                c = CATEGORY_ALIASES.get(c, c)
                if c in VALID_CATEGORIES:
                    if not is_english_word(w):
                        print(f"Invalid non-English word '{w}'. Skipping.")
                        continue
                    if not ((aac_library_df["category"] == c) & (aac_library_df["word"] == w)).any():
                        image_path = AAC_IMAGES_DIR / c / f"{w}.png"
                        audio_path = AAC_AUDIOS_DIR / c / f"{w}.mp3"
                        generate_image(w, image_path)
                        create_audio(c, w, audio_path)
                        writer.writerow([c, w])
                        new_cards_added.append({"category": c, "word": w, "image": str(image_path)})
                    else:
                        print(f"Word '{w}' in category '{c}' already exists. Skipping.")
                else:
                    print(f"Invalid category '{c}' for word '{w}'. Skipping.")
            except ValueError:
                print(f"Invalid format for missing word '{word_pair}'. Skipping.")

    end_time = time.time()
    print("Augmentation Time:", round(end_time - start_time, 2))
    return new_cards_added
