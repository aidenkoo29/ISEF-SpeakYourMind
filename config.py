from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MODEL_PATH = Path(os.getenv("FASTTEXT_MODEL_PATH", BASE_DIR / "model" / "cc.ko.300.bin"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
AAC_LIBRARY_PATH = Path(os.getenv("AAC_LIBRARY_PATH", DATA_DIR / "aac_library.csv"))
ORIGINAL_AAC_LIBRARY_PATH = Path(
    os.getenv("ORIGINAL_AAC_LIBRARY_PATH", DATA_DIR / "original_aac_library.csv")
)
EMBEDDING_PKL_PATH = Path(os.getenv("EMBEDDING_PKL_PATH", DATA_DIR / "library_vectors.pkl"))

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))

AAC_IMAGES_DIR = Path(os.getenv("AAC_IMAGES_DIR", BASE_DIR / "aac_images"))
AAC_AUDIOS_DIR = Path(os.getenv("AAC_AUDIOS_DIR", BASE_DIR / "aac_audios"))
