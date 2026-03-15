from __future__ import annotations

import os
import pprint
import shutil
from typing import List, Optional
from uuid import uuid4

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    AAC_LIBRARY_PATH,
    AAC_AUDIOS_DIR,
    AAC_IMAGES_DIR,
    EMBEDDING_PKL_PATH,
    ORIGINAL_AAC_LIBRARY_PATH,
    UPLOAD_DIR,
)
from services.auth import change_password, create_user, get_user_from_token, issue_token, verify_user
from services.audio import create_audio, transcript
from services.augmentation import (
    CATEGORY_ALIASES,
    VALID_CATEGORIES,
    generate_image,
    is_english_word,
    suggest_missing_words,
)
from services.embeddings import load_library, rebuild_library_vectors
from services.suggestion import suggestion_logic
from services.community import copy_to_library, get_card, search_cards, share_card

app = FastAPI()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

current_aac_selection = []
conversation_history = []
generation_jobs = {}


class Card(BaseModel):
    category: str
    word: str
    image: str


class SelectionUpdate(BaseModel):
    selection: List[Card]


class GenerateCardRequest(BaseModel):
    category: str
    word: str


class CommunityShareRequest(BaseModel):
    name: str
    category: str
    tags: List[str] = []
    context_time: str = ""
    context_place: str = ""
    context_occasion: str = ""
    image: str = ""
    audio: str = ""
    creator_id: str = ""
    visibility: str = "public"


class CommunityCopyRequest(BaseModel):
    id: str


class SignupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _is_english_or_empty(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    return is_english_word(cleaned)


def _token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix) :].strip()
    return None


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

library = load_library()


@app.post("/update-selection")
async def update_selection(data: SelectionUpdate):
    global current_aac_selection
    current_aac_selection = [card.dict() for card in data.selection]
    print("Updated AAC Selection:", current_aac_selection)
    return {"status": "success", "updated_selection": current_aac_selection}


@app.post("/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    global conversation_history
    file_path = UPLOAD_DIR / "speech.mp3"
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await audio.read())
    except Exception as e:
        return {"error": "Failed to save file", "details": str(e)}

    transcription = transcript(file_path)
    print("Transcription: ", transcription)

    conversation_history += [
        {"User AAC": [card["word"] for card in current_aac_selection]},
        {"Counterpart": transcription},
    ]
    print(conversation_history)

    return {"status": "ok", "transcription": transcription}


@app.get("/suggest-cards")
async def suggest_cards():
    global conversation_history
    global current_aac_selection

    suggestions = suggestion_logic(
        conversation_history + [{"User AAC": current_aac_selection}], library
    )
    pprint.pprint(suggestions)
    suggestions = suggestions["top_similar_aac_items"]

    cards = []
    for s in suggestions:
        cards.append(
            {
                "category": s["category"],
                "word": s["word"],
                "image": f"aac_images/{s['category']}/{s['word']}.png",
            }
        )

    return cards


@app.post("/augment-cards")
async def augment_cards():
    global library
    global conversation_history
    global current_aac_selection

    suggestions = suggest_missing_words(
        conversation_history + [{"User AAC": current_aac_selection}], library
    )

    return {"new_cards": suggestions}


@app.post("/suggest-new-cards")
async def suggest_new_cards():
    global conversation_history
    global current_aac_selection

    suggestions = suggest_missing_words(
        conversation_history + [{"User AAC": current_aac_selection}], library
    )
    return {"suggestions": suggestions}


def _generate_card_task(job_id: str, category: str, word: str):
    global library
    try:
        if ((library["category"] == category) & (library["word"] == word)).any():
            generation_jobs[job_id] = {"status": "done", "card": {"category": category, "word": word}}
            return

        image_path = AAC_IMAGES_DIR / category / f"{word}.png"
        audio_path = AAC_AUDIOS_DIR / category / f"{word}.mp3"
        generate_image(word, image_path)
        create_audio(category, word, audio_path)

        with open(AAC_LIBRARY_PATH, "a", newline="", encoding="utf-8") as f:
            f.write(f"{category},{word}\n")

        library = pd.read_csv(AAC_LIBRARY_PATH)
        library = rebuild_library_vectors(library)

        generation_jobs[job_id] = {
            "status": "done",
            "card": {"category": category, "word": word, "image": f"aac_images/{category}/{word}.png"},
        }
    except Exception as e:
        generation_jobs[job_id] = {"status": "error", "error": str(e)}


@app.post("/generate-card")
async def generate_card(req: GenerateCardRequest, background_tasks: BackgroundTasks):
    normalized_category = CATEGORY_ALIASES.get(req.category, req.category)
    normalized_word = req.word.strip()

    if normalized_category not in VALID_CATEGORIES:
        return {"error": "invalid_category"}
    if not is_english_word(normalized_word):
        return {"error": "invalid_word"}

    job_id = str(uuid4())
    generation_jobs[job_id] = {"status": "pending", "card": {"category": normalized_category, "word": normalized_word}}
    background_tasks.add_task(_generate_card_task, job_id, normalized_category, normalized_word)
    return {"job_id": job_id}


@app.get("/job-status/{job_id}")
async def job_status(job_id: str):
    job = generation_jobs.get(job_id)
    if not job:
        return {"status": "not_found"}
    return job


@app.post("/community/share")
async def community_share(req: CommunityShareRequest, authorization: Optional[str] = Header(default=None)):
    normalized_category = CATEGORY_ALIASES.get(req.category, req.category)
    normalized_name = req.name.strip()

    if normalized_category not in VALID_CATEGORIES:
        return {"error": "invalid_category"}
    if not is_english_word(normalized_name):
        return {"error": "invalid_name"}
    if not all(_is_english_or_empty(tag) for tag in req.tags):
        return {"error": "invalid_tags"}
    if not _is_english_or_empty(req.context_time):
        return {"error": "invalid_context_time"}
    if not _is_english_or_empty(req.context_place):
        return {"error": "invalid_context_place"}
    if not _is_english_or_empty(req.context_occasion):
        return {"error": "invalid_context_occasion"}

    payload = req.dict()
    payload["category"] = normalized_category
    payload["name"] = normalized_name
    token = _token_from_header(authorization)
    user = get_user_from_token(token)
    if user:
        payload["creator_id"] = user
    card = share_card(payload)
    return {"card": card}


@app.post("/auth/signup")
async def auth_signup(req: SignupRequest):
    user, error = create_user(req.username, req.password)
    if error:
        return {"error": error}
    token = issue_token(user["username"])
    return {"user": user, "token": token}


@app.post("/auth/login")
async def auth_login(req: LoginRequest):
    if not verify_user(req.username, req.password):
        return {"error": "invalid_credentials"}
    token = issue_token(req.username.strip())
    return {"user": {"username": req.username.strip()}, "token": token}


@app.get("/auth/me")
async def auth_me(authorization: Optional[str] = Header(default=None)):
    token = _token_from_header(authorization)
    user = get_user_from_token(token)
    if not user:
        return {"user": None}
    return {"user": {"username": user}}


@app.post("/auth/change-password")
async def auth_change_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(default=None)):
    token = _token_from_header(authorization)
    user = get_user_from_token(token)
    if not user:
        return {"error": "unauthorized"}
    error = change_password(user, req.current_password, req.new_password)
    if error:
        return {"error": error}
    return {"status": "ok"}


@app.get("/community/search")
async def community_search(q: str = ""):
    results = search_cards(q)
    return {"results": results}


@app.get("/community/card/{card_id}")
async def community_card(card_id: str):
    card = get_card(card_id)
    if not card:
        return {"error": "not_found"}
    return {"card": card}


@app.post("/community/copy")
async def community_copy(req: CommunityCopyRequest):
    card = get_card(req.id)
    if not card:
        return {"error": "not_found"}
    copied = copy_to_library(card)
    return {"copied": copied}


@app.on_event("shutdown")
def shutdown_event():
    try:
        if os.path.exists(EMBEDDING_PKL_PATH):
            os.remove(EMBEDDING_PKL_PATH)

        shutil.copyfile(ORIGINAL_AAC_LIBRARY_PATH, AAC_LIBRARY_PATH)

    except Exception as e:
        print("Error during shutdown cleanup:", str(e))
