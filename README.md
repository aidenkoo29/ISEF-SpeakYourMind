Kor version

# SpeakYourMind

AI-powered AAC (Augmentative and Alternative Communication) web app that recommends conversation cards based on context inferred from prior selections and recorded speech.

## Structure Overview
The project is a simple full-stack app with:
- Backend: `FastAPI` in `server.py` (exported via `app.py`) for suggestions, augmentation, and audio upload/transcription.
- Frontend: static `index.html`, `script.js`, `style.css` rendering AAC cards and calling backend APIs.
- Data/Assets: CSV-based AAC library plus image/audio assets for each card.

## Project Layout
Key files and folders:
- `app.py`: Thin entrypoint that exports the FastAPI app from `server.py`.
- `server.py`: FastAPI server. Wires routes and global state.
- `config.py`: Centralized config for paths and environment variables.
- `services/`: Backend modules (embeddings, suggestion, augmentation, audio, OpenAI client).
- `main.py`: Streamlit prototype UI (separate from the HTML/JS frontend). Appears to be an earlier experiment or alternative UI.
- `index.html`: Web UI layout (selected cards, suggestions, tabs, popup).
- `script.js`: Frontend logic (load library, render cards, selection state, API calls, audio recording).
- `style.css`: Styling for the web UI.
- `aac_library.csv`: Current AAC card list in `category,word` format.
- `original_aac_library.csv`: Baseline library used to reset on shutdown.
- `library_vectors.pkl`: Cached FastText vectors for `aac_library.csv`.
- `aac_images/`: PNG images per card grouped by category.
- `aac_audios/`: MP3 audio per card grouped by category.
- `uploads/`: Temporary user audio (`speech.mp3`).
- `model/cc.ko.300.bin`: FastText Korean model file.

## Runtime Flow
End-to-end flow for the HTML/JS frontend:
1. `script.js` loads `aac_library.csv` and renders cards.
2. User selects cards, which are POSTed to `/update-selection`.
3. User records speech; audio is uploaded to `/upload-audio`.
4. Backend transcribes audio (Whisper) and updates `conversation_history`.
5. Clicking “카드 추천받기” calls `/suggest-cards`:
   - LLM infers context and suggests words.
   - Words are expanded to similar AAC cards using FastText + cosine similarity.
6. Clicking “카드 추가하기” calls `/augment-cards`:
   - LLM proposes missing words.
   - Images and audio are generated and appended to `aac_library.csv`.

## Backend Components
- Embedding: `fasttext` vectors (cached to `library_vectors.pkl`).
- Suggestion logic: `services/suggestion.py` uses an LLM + similarity search to pick AAC cards.
- Augmentation logic: `services/augmentation.py` generates new card candidates, images, and audio.
- API (`server.py`):
  - `POST /update-selection`
  - `POST /upload-audio`
  - `GET /suggest-cards`
  - `POST /augment-cards`

## Frontend Components
- `index.html` defines containers for selections, suggestions, and category tabs.
- `script.js` handles:
  - CSV load and rendering
  - selection state
  - API calls
  - audio recording
- `style.css` defines layout and visuals.

## Next Refactor Steps
Recommended follow-ups now that the core refactor is in place:
- Replace global mutable state (`current_aac_selection`, `conversation_history`) with per-session storage or a database.
- Add a build step for frontend assets and consider a lightweight framework or component system.
- Add tests:
  - Unit tests for suggestion/augmentation logic
  - Integration tests for API endpoints
- Add async task queue (e.g., Celery/RQ) for image/audio generation.
- Introduce model abstraction to switch between FastText/OpenAI embedding methods cleanly.

## Development Notes
- Install deps:
  ```bash
  pip install fastapi uvicorn openai fasttext pandas numpy scikit-learn soundfile pillow python-multipart python-dotenv
  ```
- Start server:
  ```bash
  uvicorn app:app --reload
  ```
- Open UI: `index.html` in a browser.
- `main.py` is an alternate Streamlit app and is not used by the HTML/JS frontend.

## Security Notes
- Do not commit API keys. Load them from environment variables or a local `.env` file.
