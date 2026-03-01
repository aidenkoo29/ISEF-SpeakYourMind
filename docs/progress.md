# Progress Report — Social Computing Feature (SpeakYourMind)

Date: 2026-02-22

This document captures current progress and exact steps to resume. It includes what was implemented, where files live, how to run and verify, and the exact missing pieces.

---

## 1) What’s Already Implemented

### Backend: Community Feature (JSON storage, no DB)
**New file:** `services/community.py`
- JSON storage file: `community_library.json`
- Functions implemented:
  - `share_card(payload)` → append a card to community library
  - `search_cards(query)` → naive search (substring) over name/category/tags/context
  - `get_card(card_id)` → return full card by id
  - `copy_to_library(card)` → copy card assets into local AAC library and append to `aac_library.csv`

**New endpoints in `server.py`:**
- `POST /community/share`
  - Input: `CommunityShareRequest` JSON
  - Output: `{ card: { ... } }`
- `GET /community/search?q=...`
  - Output: `{ results: [...] }`
- `GET /community/card/{card_id}`
  - Output: `{ card: {...} }`
- `POST /community/copy`
  - Input: `{ id: "..." }`
  - Output: `{ copied: { category, word, image } }`

### Frontend: UI Containers (HTML + CSS)
**Updated `index.html`:**
- Added community floating button: `#community-btn`
- Added community modal: `#community-popup`
- Added community detail modal: `#community-detail-popup`
- Added share modal: `#community-share-popup`
- Added inputs for share flow:
  - `#share-card-select`
  - `#share-time`, `#share-place`, `#share-occasion`, `#share-tags`, `#share-visibility`
  - `#share-submit-btn`

**Updated `style.css`:**
- Added styles for:
  - `.community-btn`
  - `.community-search`
  - `.community-results`
  - `.community-card`
  - `.community-detail-actions`
  - `.share-form`

---

## 2) What’s NOT Implemented (Critical Missing Piece)

**`script.js` still does NOT include the new community logic.**

The following is missing and must be added:

1. **Open/close community modal**
   - `#community-btn` → show `#community-popup`
   - `#community-close-btn` → hide it

2. **Search community cards**
   - `#community-search-btn` + Enter key on `#community-search-input`
   - Call `GET /community/search?q=...`
   - Render list in `#community-results`

3. **View card detail**
   - “자세히” button in results → call `GET /community/card/{id}`
   - Show modal `#community-detail-popup`
   - Fill `#community-detail-title`, `#community-detail-body`
   - Hook `#community-detail-audio-btn` to play audio
   - Hook `#community-detail-copy-btn` to POST `/community/copy`

4. **Share to community**
   - `#open-share-btn` opens `#community-share-popup`
   - Populate `#share-card-select` with cards from `aacData`
   - `#share-submit-btn` POST `/community/share`
   - On success, close modal and refresh results

5. **Update local library after copy**
   - On success of `/community/copy`, push to `aacData`
   - Re-render tabs/cards

---

## 3) How to Run the Project (Current State)

### Backend
```bash
uvicorn app:app --reload
```

### Frontend
Open `index.html` in the browser.

---

## 4) How to Verify Community Endpoints (API only)

### Share card
```bash
curl -X POST http://127.0.0.1:8000/community/share \
  -H "Content-Type: application/json" \
  -d '{
    "name": "김치",
    "category": "음식",
    "tags": ["korean", "food"],
    "context_time": "점심",
    "context_place": "집",
    "context_occasion": "식사",
    "image": "aac_images/음식/김치.png",
    "audio": "aac_audios/음식/김치.mp3",
    "visibility": "public"
  }'
```

### Search
```bash
curl "http://127.0.0.1:8000/community/search?q=food"
```

### Get detail
```bash
curl "http://127.0.0.1:8000/community/card/{id}"
```

### Copy to library
```bash
curl -X POST http://127.0.0.1:8000/community/copy \
  -H "Content-Type: application/json" \
  -d '{"id": "<card-id>"}'
```

---

## 5) Files Changed So Far

- `services/community.py` (new)
- `server.py` (new endpoints)
- `index.html` (community UI containers)
- `style.css` (community UI styles)

No changes have been made to `script.js` for community feature yet.

---

## 6) Suggested Next Implementation Steps (JS)

1. Add DOM references in `script.js`:
   - `#community-btn`, `#community-popup`, `#community-search-input`, `#community-search-btn`
   - `#community-results`
   - `#community-detail-popup`, `#community-detail-*`
   - `#community-share-popup`, `#share-*` fields

2. Implement functions:
   - `loadCommunityResults(query)`
   - `renderCommunityResults(cards)`
   - `openCommunityDetail(id)`
   - `openSharePopup()`

3. Update `aacData` on copy:
   - Push new card
   - Re-render tabs and current category

---

## 7) Notes
- This is JSON-based community storage for now (`community_library.json`).
- No user accounts or privacy enforcement yet.
- It’s a mock “community” flow for testing.

---

## 8) Resume Instructions for Codex
Tell Codex:

“Finish the community feature by wiring the new UI in `script.js` to the `/community/*` endpoints. Use the existing HTML elements and add open/close behavior, search, detail view, and share flow. After copy, update `aacData` and re-render.”
