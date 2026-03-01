from __future__ import annotations

import time
from typing import List

import pandas as pd
from pydantic import BaseModel

from services.embeddings import top_similar_items
from services.openai_client import get_client

K = 2


class AACSuggestion(BaseModel):
    context_time: str
    context_place: str
    context_occasion: str
    suggestion: List[str]


def suggestion_logic(conversation_history, library: pd.DataFrame, top_k: int = 8):
    start_time = time.time()
    client = get_client()

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
                ),
            },
            {
                "role": "user",
                "content": f"Here is the conversation history:\n{conversation_history}",
            },
        ],
        text_format=AACSuggestion,
    )

    parsed = response.output_parsed
    results = []

    for keyword in parsed.suggestion:
        results.append(top_similar_items(library, keyword, K))

    all_results = (
        pd.concat(results)
        .sort_values(by="similarity", ascending=False)
        .reset_index(drop=True)
    )

    end_time = time.time()
    print("Suggestion time: ", round(end_time - start_time, 2))

    return {
        "context": {
            "context_time": parsed.context_time,
            "context_place": parsed.context_place,
            "context_occasion": parsed.context_occasion,
        },
        "suggestion_from_model": parsed.suggestion,
        "top_similar_aac_items": all_results.to_dict(orient="records"),
    }
