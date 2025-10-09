
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf
import os
import csv
import random
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64
import requests

# brew install cmake
# brew install gcc
# pip install git+https://github.com/facebookresearch/fastText.git

# model link: https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ko.300.bin.gz

# if error....
# brew install libomp
# export CFLAGS="-Xpreprocessor -fopenmp -I/opt/homebrew/include"
# export LDFLAGS="-L/opt/homebrew/lib -lomp"

import fasttext
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import pprint

import time

# Load the pretrained model
fasttext_model = fasttext.load_model("./model/cc.ko.300.bin")
client = OpenAI()

# Transcription ------------------------------------------------------------------------------------------

def transcript(audio_path="./uploads/speech.mp3"):
    audio_file = open(audio_path, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcription.text

def create_audio(category, word):
     with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="fable",
        input=word,
    ) as response:
        response.stream_to_file(f'./aac_audios/{category}/{word}.mp3')


# Embedding ------------------------------------------------------------------------------------------

K = 2

def get_embedding(text, model='fasttext', openai_model="text-embedding-3-small"):
    
    if model == 'fasttext':
        vector = fasttext_model.get_word_vector(text)
    elif model == 'openai':
        text = text.replace("\n", " ")
        text = f'"{text}" 라는 말을 하고 싶어요.'
        vector = client.embeddings.create(input=[text], model=openai_model).data[0].embedding
    
    return vector

# Load library
library = pd.read_csv('./aac_library.csv')
library['categoryAndWord'] = library['category'] + '-' + library['word']

# File to store/load embeddings
embedding_pkl_path = 'library_vectors.pkl'

# Check if pickle file exists
if os.path.exists(embedding_pkl_path):
    print("Loading existing vector pickle...")
    with open(embedding_pkl_path, 'rb') as f:
        library['vector'] = pickle.load(f)
else:
    print("Creating embeddings and saving to pickle...")
    library['vector'] = library['word'].apply(lambda x: get_embedding(x))
    
    with open(embedding_pkl_path, 'wb') as f:
        pickle.dump(library['vector'].tolist(), f)

# Suggestion ------------------------------------------------------------------------------------------

# Define the expected response format
class AACSuggestion(BaseModel):
    context_time: str  # full sentence
    context_place: str  # full sentence
    context_occasion: str  # full sentence
    suggestion: List[str]

# suggestion main logic
def suggestion_logic(conversation_history, library, top_k=8):
    start_time = time.time()
    response = client.responses.parse(
        model="gpt-4.1-2025-04-14",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a reasoning assistant in an AAC (Augmentative and Alternative Communication) system. "
                    "Your task is to understand the context from a conversation history between a nonverbal user and a speaking counterpart.\n\n"
                    "Please return:\n"
                    "- context_time: a full sentence describing the current time context (e.g., 'It seems to be around lunchtime.')\n"
                    "- context_place: a full sentence describing where the conversation likely takes place (e.g., 'They are probably at home.')\n"
                    "- context_occasion: a sentence describing the social or functional occasion (e.g., 'They are getting ready to eat a meal.')\n"
                    f"- suggestion: a list of 5 Korean AAC words from {library['word']} the user might want to say next, based on the conversation.\n\n"
                    "Be thoughtful and concise."
                )
            },
            {
                "role": "user",
                "content": f"Here is the conversation history:\n{conversation_history}"
            },
        ],
        text_format=AACSuggestion,
    )

    parsed = response.output_parsed

    results = []

    # Prepare matrix of AAC library vectors
    matrix = np.vstack(library['vector'].to_numpy())

    for keyword in parsed.suggestion:
        # Get embedding of each suggested word
        emb = get_embedding(keyword)
        emb_np = np.array(emb).reshape(1, -1)

        # Cosine similarity to all AAC cards
        sims = cosine_similarity(emb_np, matrix)[0]

        # Top N for this keyword
        top_indices = sims.argsort()[-K:][::-1]
        subset = library.iloc[top_indices][['category', 'word', 'categoryAndWord']].copy()
        subset['similarity'] = sims[top_indices]
        subset['source_suggestion'] = keyword

        results.append(subset)

    # Concatenate all top results and sort globally
    all_results = pd.concat(results).sort_values(by='similarity', ascending=False).reset_index(drop=True)
    end_time = time.time()
    print('Suggestion time: ', round(end_time-start_time, 2))

    return {
        "context": {
            "context_time": parsed.context_time,
            "context_place": parsed.context_place,
            "context_occasion": parsed.context_occasion,
        },
        "suggestion_from_model": parsed.suggestion,
        "top_similar_aac_items": all_results.to_dict(orient='records')
    }

# Augmentation ------------------------------------------------------------------------------------------

VALID_CATEGORIES = ["사람", "감정", "음식", "장소", "행동", "물건", "질문", "시간"]

class AACAugmentation(BaseModel):
    context_summary: str
    missing_words: List[str]
    missing_from_library: List[bool]

def generate_image(target_word, filename):
    print(f"▶ Generating image for '{target_word}' in ARASAAC style…")
    result = client.images.generate(
        model="gpt-image-1",
        prompt=f'Draw an image of "{target_word}" in ARASAAC card style without any text on it.',
        size="1024x1024",
    )
    # Decode base64 → PIL.Image
    b64 = result.data[0].b64_json.split(",")[-1]
    b64 += "=" * (-len(b64) % 4)  # fix padding
    image = Image.open(BytesIO(base64.b64decode(b64)))
    image.save(filename)
    print("Image saved done:", filename)

def augmentation_logic(conversation_history, aac_library_df):
    start_time = time.time()

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
                    "2. A list of important Korean words or short phrases that were likely needed but do not exist in the AAC library, in 'category-word' format.\n\n"
                    "Think step-by-step about what the user tried to express and what vocabulary was needed, then check what's missing.\n\n"
                    f"Valid categories are: {VALID_CATEGORIES}. Avoid duplicates or similar words already in the AAC library. Only include words that are important and missing from aac_library."
                )
            },
            {
                "role": "user",
                "content": f"Conversation history:{conversation_history} AAC library: {aac_library_df['category']+'-'+aac_library_df['word']} YOU should double check to ensure new words not in this aac library."
            }
        ],
        text_format=AACAugmentation
    )

    output = response.output_parsed
    print("New cards suggested by model: ", output.missing_words)

    new_cards_added = []
    with open('aac_library.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for word_pair in output.missing_words:
            try:
                c, w = word_pair.split('-')
                if c in VALID_CATEGORIES:
                    if not ((aac_library_df['category'] == c) & (aac_library_df['word'] == w)).any():
                        filename = f"./aac_images/{c}/{w}.png"
                        generate_image(w, filename)
                        create_audio(c, w)
                        writer.writerow([c, w])
                        new_cards_added.append({'category': c, 'word': w, "image": filename})
                    else:
                        print(f"Word '{w}' in category '{c}' already exists. Skipping.")
                else:
                    print(f"Invalid category '{c}' for word '{w}'. Skipping.")
            except ValueError:
                print(f"Invalid format for missing word '{word_pair}'. Skipping.")

    end_time = time.time()
    print("Augmentation Time:", round(end_time-start_time, 2))
    return new_cards_added 

# Server ----------------------------------------------------------------------------------------------

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

current_aac_selection = []
conversation_history = []

class Card(BaseModel):
    category: str
    word: str
    image: str

class SelectionUpdate(BaseModel):
    selection: List[Card]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for security in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/update-selection")
async def update_selection(data: SelectionUpdate):
    global current_aac_selection
    current_aac_selection = [card.dict() for card in data.selection]
    print("Updated AAC Selection:", current_aac_selection)
    return {"status": "success", "updated_selection": current_aac_selection}


@app.post("/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    global conversation_history
    file_path = "./uploads/speech.mp3"
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await audio.read())
    except Exception as e:
        return {"error": "Failed to save file", "details": str(e)}
    
    transcription = transcript()
    print("Transcription: ", transcription)

    conversation_history += [{'User AAC': [card['word'] for card in current_aac_selection]}, {'Counterpart': transcription}]
    print(conversation_history)

    return


@app.get("/suggest-cards")
async def suggest_cards():
    global conversation_history
    global current_aac_selection

    suggestions = suggestion_logic(conversation_history + [{'User AAC': current_aac_selection}], library)
    pprint.pprint(suggestions)
    suggestions = suggestions['top_similar_aac_items']

    cards = []
    for s in suggestions:
        cards.append({"category": s['category'], "word": s['word'], "image": f"aac_images/{s['category']}/{s['word']}.png"})

    return cards

@app.post("/augment-cards")
async def augment_cards():
    global library
    global conversation_history
    global current_aac_selection
    newly_added_cards = augmentation_logic(conversation_history + [{'User AAC': current_aac_selection}], library)
    
    # Re-load the library to include the new cards
    library = pd.read_csv('./aac_library.csv')
    library['categoryAndWord'] = library['category'] + '-' + library['word']
    library['vector'] = library['word'].apply(lambda x: get_embedding(x))

    return {"new_cards": newly_added_cards}

import shutil

@app.on_event("shutdown")
def shutdown_event():
    try:
        if os.path.exists(embedding_pkl_path):
            os.remove(embedding_pkl_path)

        shutil.copyfile("original_aac_library.csv", "aac_library.csv")

    except Exception as e:
        print("Error during shutdown cleanup:", str(e))
