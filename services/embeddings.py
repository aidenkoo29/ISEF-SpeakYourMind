from __future__ import annotations

import os
import pickle
from typing import Literal

import fasttext
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from config import AAC_LIBRARY_PATH, EMBEDDING_PKL_PATH, MODEL_PATH, OPENAI_API_KEY
from services.openai_client import get_client

EmbeddingModel = Literal["fasttext", "openai"]
DEFAULT_EMBEDDING_MODEL: EmbeddingModel = os.getenv(
    "EMBEDDING_MODEL",
    "openai" if OPENAI_API_KEY else "fasttext",
)

_fasttext_model = fasttext.load_model(str(MODEL_PATH))


def get_embedding(
    text: str,
    model: EmbeddingModel = DEFAULT_EMBEDDING_MODEL,
    openai_model: str = "text-embedding-3-small",
):
    if model == "fasttext":
        return _fasttext_model.get_word_vector(text)
    if model == "openai":
        client = get_client()
        text = text.replace("\n", " ")
        return client.embeddings.create(input=[text], model=openai_model).data[0].embedding
    raise ValueError(f"Unknown embedding model: {model}")


def load_library() -> pd.DataFrame:
    library = pd.read_csv(AAC_LIBRARY_PATH)
    library["categoryAndWord"] = library["category"] + "-" + library["word"]

    if os.path.exists(EMBEDDING_PKL_PATH):
        with open(EMBEDDING_PKL_PATH, "rb") as f:
            library["vector"] = pickle.load(f)
    else:
        library["vector"] = library["word"].apply(lambda x: get_embedding(x))
        with open(EMBEDDING_PKL_PATH, "wb") as f:
            pickle.dump(library["vector"].tolist(), f)

    return library


def rebuild_library_vectors(library: pd.DataFrame) -> pd.DataFrame:
    library = library.copy()
    library["categoryAndWord"] = library["category"] + "-" + library["word"]
    library["vector"] = library["word"].apply(lambda x: get_embedding(x))
    return library


def top_similar_items(library: pd.DataFrame, keyword: str, top_k: int) -> pd.DataFrame:
    emb = get_embedding(keyword)
    emb_np = np.array(emb).reshape(1, -1)
    matrix = np.vstack(library["vector"].to_numpy())
    sims = cosine_similarity(emb_np, matrix)[0]
    top_indices = sims.argsort()[-top_k:][::-1]

    subset = library.iloc[top_indices][["category", "word", "categoryAndWord"]].copy()
    subset["similarity"] = sims[top_indices]
    subset["source_suggestion"] = keyword
    return subset
