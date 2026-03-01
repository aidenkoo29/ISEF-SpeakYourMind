from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from config import AAC_AUDIOS_DIR, AAC_IMAGES_DIR, AAC_LIBRARY_PATH

COMMUNITY_LIBRARY_PATH = Path("community_library.json")


def _load_library() -> List[Dict[str, Any]]:
    if not COMMUNITY_LIBRARY_PATH.exists():
        return []
    try:
        return json.loads(COMMUNITY_LIBRARY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_library(items: List[Dict[str, Any]]) -> None:
    COMMUNITY_LIBRARY_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def share_card(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = _load_library()
    card = {
        "id": str(uuid4()),
        "name": payload["name"],
        "category": payload["category"],
        "tags": payload.get("tags", []),
        "context_time": payload.get("context_time", ""),
        "context_place": payload.get("context_place", ""),
        "context_occasion": payload.get("context_occasion", ""),
        "image": payload.get("image", ""),
        "audio": payload.get("audio", ""),
        "creator_id": payload.get("creator_id", ""),
        "visibility": payload.get("visibility", "public"),
        "created_at": payload.get("created_at"),
    }
    items.append(card)
    _save_library(items)
    return card


def search_cards(query: str) -> List[Dict[str, Any]]:
    items = _load_library()
    q = (query or "").strip().lower()
    if not q:
        return items

    def score(item: Dict[str, Any]) -> int:
        hay = " ".join(
            [
                item.get("name", ""),
                item.get("category", ""),
                " ".join(item.get("tags", []) or []),
                item.get("context_time", ""),
                item.get("context_place", ""),
                item.get("context_occasion", ""),
            ]
        ).lower()
        return 1 if q in hay else 0

    ranked = sorted(items, key=score, reverse=True)
    return [item for item in ranked if score(item) > 0] or items


def get_card(card_id: str) -> Optional[Dict[str, Any]]:
    items = _load_library()
    for item in items:
        if item.get("id") == card_id:
            return item
    return None


def copy_to_library(card: Dict[str, Any]) -> Dict[str, Any]:
    category = card["category"]
    word = card["name"]

    img_src = Path(card.get("image") or AAC_IMAGES_DIR / category / f"{word}.png")
    audio_src = Path(card.get("audio") or AAC_AUDIOS_DIR / category / f"{word}.mp3")

    img_dst = AAC_IMAGES_DIR / category / f"{word}.png"
    audio_dst = AAC_AUDIOS_DIR / category / f"{word}.mp3"

    img_dst.parent.mkdir(parents=True, exist_ok=True)
    audio_dst.parent.mkdir(parents=True, exist_ok=True)

    if img_src.exists() and not img_dst.exists():
        shutil.copyfile(img_src, img_dst)
    if audio_src.exists() and not audio_dst.exists():
        shutil.copyfile(audio_src, audio_dst)

    with open(AAC_LIBRARY_PATH, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()[1:]
    exists = any(line.split(",")[0] == category and line.split(",")[1] == word for line in lines)

    if not exists:
        with open(AAC_LIBRARY_PATH, "a", encoding="utf-8") as f:
            f.write(f"{category},{word}\n")

    return {
        "category": category,
        "word": word,
        "image": f"aac_images/{category}/{word}.png",
    }
