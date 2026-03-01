from __future__ import annotations

import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from services.openai_client import get_client
from config import AAC_IMAGES_DIR, AAC_AUDIOS_DIR, AAC_LIBRARY_PATH, ORIGINAL_AAC_LIBRARY_PATH, DATA_DIR

COMMUNITY_LIBRARY_PATH = Path(os.getenv("COMMUNITY_LIBRARY_PATH", DATA_DIR / "community_library.json"))
TRANSLATION_MAP_PATH = DATA_DIR / "translation_map.json"

CATEGORY_MAP = {
    "사람": "People",
    "감정": "Feelings",
    "음식": "Food",
    "장소": "Places",
    "행동": "Actions",
    "물건": "Objects",
    "질문": "Questions",
    "시간": "Time",
}

ASCII_ALLOWED_RE = re.compile(r"[^A-Za-z0-9\-\s']+")
SPACE_RE = re.compile(r"\s+")


def normalize_word(text: str) -> str:
    text = text.strip()
    text = ASCII_ALLOWED_RE.sub("", text)
    text = SPACE_RE.sub(" ", text)
    return text.strip()


def response_text(resp) -> str:
    if hasattr(resp, "output_text") and resp.output_text:
        return resp.output_text
    if hasattr(resp, "output") and resp.output:
        parts = []
        for item in resp.output:
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
        return "\n".join(parts).strip()
    return ""


def extract_json(text: str):
    text = text.strip()
    if text.startswith("["):
        return json.loads(text)
    # Try to find first JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("No JSON array found in response")


def translate_words(pairs: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    client = get_client()
    items = [{"category_ko": c, "word_ko": w} for c, w in pairs]

    prompt = (
        "Translate the following Korean AAC words into concise, natural English words or short phrases.\n"
        "Constraints:\n"
        "- Output JSON array in the SAME ORDER as input.\n"
        "- Each item must include: category_ko, word_ko, word_en.\n"
        "- Use ASCII letters, numbers, spaces, hyphens, and apostrophes only.\n"
        "- Avoid punctuation and extra commentary.\n"
        "- Keep it short (1-3 words).\n"
    )

    resp = client.responses.create(
        model="gpt-4.1-2025-04-14",
        input=[
            {"role": "system", "content": "You are a translation engine for AAC vocabulary."},
            {"role": "user", "content": prompt + "\n" + json.dumps(items, ensure_ascii=False)},
        ],
        temperature=0,
    )

    text = response_text(resp)
    data = extract_json(text)
    return data


def translate_community(cards: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not cards:
        return []
    client = get_client()

    prompt = (
        "Translate the following Korean fields into English.\n"
        "Return JSON array in the SAME ORDER with fields:\n"
        "name_en, category_en, tags_en, context_time_en, context_place_en, context_occasion_en.\n"
        "Rules:\n"
        "- tags_en must be a list of strings.\n"
        "- Use concise natural English.\n"
        "- ASCII letters, numbers, spaces, hyphens, and apostrophes only.\n"
        "- Keep each field short.\n"
    )

    payload = []
    for card in cards:
        payload.append(
            {
                "name": card.get("name", ""),
                "category": card.get("category", ""),
                "tags": card.get("tags", []) or [],
                "context_time": card.get("context_time", ""),
                "context_place": card.get("context_place", ""),
                "context_occasion": card.get("context_occasion", ""),
            }
        )

    resp = client.responses.create(
        model="gpt-4.1-2025-04-14",
        input=[
            {"role": "system", "content": "You are a translation engine for AAC community metadata."},
            {"role": "user", "content": prompt + "\n" + json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0,
    )

    text = response_text(resp)
    data = extract_json(text)
    return data


def ensure_unique(words: List[str]) -> List[str]:
    seen = defaultdict(int)
    result = []
    for word in words:
        base = word
        if not base:
            base = "Unknown"
        count = seen[base]
        if count == 0:
            result.append(base)
        else:
            result.append(f"{base} {count + 1}")
        seen[base] += 1
    return result


def main(execute: bool = False) -> None:
    if not AAC_LIBRARY_PATH.exists():
        raise SystemExit(f"AAC library not found: {AAC_LIBRARY_PATH}")

    df = pd.read_csv(AAC_LIBRARY_PATH)
    pairs = list(zip(df["category"].tolist(), df["word"].tolist()))

    translated = translate_words(pairs)
    if len(translated) != len(pairs):
        raise SystemExit("Translation count mismatch")

    category_en_list = []
    word_en_list = []
    for item in translated:
        cat_ko = item.get("category_ko")
        word_en = normalize_word(item.get("word_en", ""))
        category_en_list.append(CATEGORY_MAP.get(cat_ko, "Other"))
        word_en_list.append(word_en)

    # Ensure uniqueness per category
    new_words = []
    grouped = defaultdict(list)
    for cat_en, word_en in zip(category_en_list, word_en_list):
        grouped[cat_en].append(word_en)
    unique_map = {}
    for cat_en, words in grouped.items():
        unique_words = ensure_unique(words)
        for original, unique in zip(words, unique_words):
            unique_map[(cat_en, original, unique_words.index(unique))] = unique

    # Rebuild with per-row uniqueness
    per_category_seen = defaultdict(int)
    final_words = []
    for cat_en, word_en in zip(category_en_list, word_en_list):
        idx = per_category_seen[cat_en]
        unique = ensure_unique(grouped[cat_en])[idx]
        per_category_seen[cat_en] += 1
        final_words.append(unique)

    # Build rename mappings
    image_moves = []
    audio_moves = []
    for (cat_ko, word_ko), cat_en, word_en in zip(pairs, category_en_list, final_words):
        src_img = AAC_IMAGES_DIR / cat_ko / f"{word_ko}.png"
        src_audio = AAC_AUDIOS_DIR / cat_ko / f"{word_ko}.mp3"
        dst_img = AAC_IMAGES_DIR / cat_en / f"{word_en}.png"
        dst_audio = AAC_AUDIOS_DIR / cat_en / f"{word_en}.mp3"
        image_moves.append((src_img, dst_img))
        audio_moves.append((src_audio, dst_audio))

    # Community translations
    community_cards = []
    if COMMUNITY_LIBRARY_PATH.exists():
        community_cards = json.loads(COMMUNITY_LIBRARY_PATH.read_text(encoding="utf-8"))
        community_translations = translate_community(community_cards)
    else:
        community_translations = []

    # Save translation map
    map_rows = []
    for (cat_ko, word_ko), cat_en, word_en in zip(pairs, category_en_list, final_words):
        map_rows.append({"category_ko": cat_ko, "word_ko": word_ko, "category_en": cat_en, "word_en": word_en})
    TRANSLATION_MAP_PATH.write_text(json.dumps(map_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    if not execute:
        print("Dry run complete. Translation map saved to", TRANSLATION_MAP_PATH)
        print("Run with --execute to apply changes.")
        return

    # Move assets
    for src, dst in image_moves:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    for src, dst in audio_moves:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

    # Remove empty old category dirs
    for cat_ko in set(df["category"].tolist()):
        img_dir = AAC_IMAGES_DIR / cat_ko
        audio_dir = AAC_AUDIOS_DIR / cat_ko
        if img_dir.exists() and not any(img_dir.iterdir()):
            img_dir.rmdir()
        if audio_dir.exists() and not any(audio_dir.iterdir()):
            audio_dir.rmdir()

    # Update CSVs
    df["category"] = category_en_list
    df["word"] = final_words
    df.to_csv(AAC_LIBRARY_PATH, index=False)
    df.to_csv(ORIGINAL_AAC_LIBRARY_PATH, index=False)

    # Update community library
    if community_cards:
        updated_cards = []
        for card, translated_card in zip(community_cards, community_translations):
            name_en = normalize_word(translated_card.get("name_en", ""))
            category_en = CATEGORY_MAP.get(card.get("category", ""), translated_card.get("category_en", "Other"))
            tags_en = [normalize_word(tag) for tag in translated_card.get("tags_en", []) if normalize_word(tag)]
            context_time_en = normalize_word(translated_card.get("context_time_en", ""))
            context_place_en = normalize_word(translated_card.get("context_place_en", ""))
            context_occasion_en = normalize_word(translated_card.get("context_occasion_en", ""))

            card["name"] = name_en or card.get("name", "")
            card["category"] = category_en
            card["tags"] = tags_en
            card["context_time"] = context_time_en
            card["context_place"] = context_place_en
            card["context_occasion"] = context_occasion_en
            card["image"] = f"aac_images/{category_en}/{card['name']}.png"
            card["audio"] = f"aac_audios/{category_en}/{card['name']}.mp3"
            updated_cards.append(card)

        COMMUNITY_LIBRARY_PATH.write_text(json.dumps(updated_cards, ensure_ascii=False, indent=2), encoding="utf-8")

    # Remove old embedding cache
    embedding_path = DATA_DIR / "library_vectors.pkl"
    if embedding_path.exists():
        embedding_path.unlink()

    print("Translation complete.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Apply translations and rename assets")
    args = parser.parse_args()

    main(execute=args.execute)
