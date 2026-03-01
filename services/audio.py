from __future__ import annotations

from pathlib import Path

from services.openai_client import get_client


def transcript(audio_path: Path) -> str:
    client = get_client()
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    return transcription.text


def create_audio(category: str, word: str, target_path: Path) -> None:
    client = get_client()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="fable",
        input=word,
    ) as response:
        response.stream_to_file(str(target_path))
