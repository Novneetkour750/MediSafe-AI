# MediSafe AI — Architecture Review & Refactor Plan

## 1. What I found across the four zips

| Archive | What it actually is |
|---|---|
| `MediSafe_8__2_.zip` | The **real, working product**. One 987-line Streamlit `main.py` + `services/` (llm.py, ai_service.py, rag_search.py, regulation_lookup.py, csv_services.py) + prebuilt FAISS index + dataset + assets. Gemini Vision does OCR, FAISS + sentence-transformers does semantic search, Gemini writes grounded answers. Fully functional. |
| `backend.zip` | An **abandoned FastAPI migration**, half-scaffolded. Route files (`chat.py`, `countries.py`, `health.py`, `search.py`), an older `llm.py` on the deprecated `google.generativeai` SDK, a duplicate FAISS search (`vector_search.py`), and a second OCR path built on EasyOCR. No working `app.py` entrypoint that imports cleanly (routes reference `services.csv_services`, `services.ai_service` that don't exist in this same zip). |
| `frontend.zip` | Misleadingly named — contains an **older Streamlit `main.py`** (calls a local `ocr.py` that doesn't exist here) *and* three more FastAPI route files (`medicines.py`, `stats.py`, `upload.py`) that belong with `backend.zip`, not the frontend. The files were simply split across two folders with no logic. |
| `script.zip` | `doc_emb.py` — a one-off REPL script that became `scripts/build_index.py`. Prototype, superseded, safe to delete. |

**Bottom line:** there is one working app and one abandoned, incoherently-split attempt at splitting it into a backend/frontend. I used the working app as the source of truth for all functionality and business logic, and used the abandoned attempt only to confirm the intended FastAPI direction.

**Security finding:** the shared `.env` contains a live `GEMINI_API_KEY`. Rotate it.

---

## 2. Root causes of the mess (why it felt tangled)

1. **No layering.** `main.py` (UI) directly imported `services/llm.py` (AI calls) and `services/rag_search.py` (data + ML), so the presentation layer, business logic, and infrastructure were one process with no boundary. This is why splitting into frontend/backend stalled — there was no seam to cut along.
2. **Two competing OCR implementations** (Gemini Vision vs EasyOCR) and **two competing search implementations** (`rag_search.py` vs `vector_search.py`), from two different points in the project's history, never reconciled.
3. **Two Gemini SDKs in play** (`google-genai` vs the older `google.generativeai`), because the FastAPI prototype was started before the main app was upgraded.
4. **Prompt construction, data fetching, and response formatting all lived in the same functions** (e.g. `regulation_lookup.py` mixed FAISS querying, score-thresholding, and country-flag formatting in one file).
5. **The route split (`backend.zip`/`frontend.zip`) was done by file location, not by responsibility** — hence route files ended up in "frontend.zip".

---

## 3. Final architecture

```
medisafe-ai/
├── backend/                        # FastAPI service (owns AI, data, business logic)
│   ├── app.py                      # App factory: CORS, exception handlers, router mounts. NO logic.
│   ├── config.py                   # Settings: paths, env vars, tuning constants.
│   ├── dependencies.py             # Composition root — builds the service graph once, exposes Depends() fns.
│   ├── routes/
│   │   ├── scan.py                 # POST /api/scan/image, GET /api/scan/search, POST /api/scan/alternatives
│   │   ├── chat.py                 # POST /api/chat, POST /api/chat/followup
│   │   ├── reference.py            # GET /api/countries, /api/medicines, /api/stats
│   │   └── health.py               # GET /api/health
│   ├── services/
│   │   ├── medicine_service.py     # ★ Central orchestrator — the only service routes call directly.
│   │   ├── ocr_service.py          # Image -> medicine name (Gemini Vision only).
│   │   ├── search_service.py       # Embedding + FAISS semantic search (merged the two duplicates).
│   │   ├── regulation_service.py   # Score thresholds, country flags, confidence %, alternatives.
│   │   └── llm_service.py          # Thin Gemini client wrapper + prompt templates + JSON parsing.
│   ├── database/
│   │   └── regulation_repository.py # Sole owner of the CSV — load once, expose read methods.
│   ├── models/
│   │   └── schemas.py              # Pydantic request/response contracts.
│   ├── utils/
│   │   ├── logger.py                # Centralized logging config.
│   │   └── exceptions.py           # Domain exceptions -> HTTP status codes.
│   └── scripts/
│       └── build_index.py          # One-off: rebuilds the FAISS index from the CSV.
│
├── frontend/                       # Streamlit UI (owns presentation only)
│   ├── app.py                      # Entrypoint: page config, CSS, session init, router. NO logic.
│   ├── config.py                   # BACKEND_URL, asset paths.
│   ├── api_client.py               # ★ The ONLY file that makes HTTP calls to the backend.
│   ├── state.py                    # st.session_state initialization + navigation helper.
│   ├── views/
│   │   ├── home.py, scan.py, chat.py, about.py, history.py   # One file per page.
│   ├── components/
│   │   ├── navbar.py, footer.py, country_card.py, illustration.py   # Reusable UI fragments.
│   └── assets/
│       ├── css/style.css
│       └── images/
│
├── dataset/medicine_travel_regulations.csv   # Shared data, read only by the backend
├── models/medisafe.index                      # Generated FAISS index, read only by the backend
└── ARCHITECTURE.md / README.md
```

---

## 4. Responsibility of every file

### Backend

| File | Responsibilities | Should NOT contain |
|---|---|---|
| `app.py` | Create the FastAPI app, register CORS + exception handlers, mount routers. | Any route logic, any service logic. |
| `config.py` | Read env vars, define paths and tuning constants. | Any I/O beyond `os.getenv`, any pandas/FAISS/Gemini code. |
| `dependencies.py` | Construct each service exactly once; expose `Depends()`-compatible functions. | Business logic — it only wires objects together. |
| `routes/*.py` | Parse the HTTP request, call **one** `MedicineService` (or repository) method, return a Pydantic model. | Prompt text, score thresholds, pandas/FAISS calls, try/except around AI calls (that's `MediSafeError` + the global handler's job). |
| `services/medicine_service.py` | Orchestrate OCR → search → regulation → LLM for each use case (scan, search, chat, follow-up, alternatives). | Low-level FAISS/embedding code, prompt text, CSV access. |
| `services/ocr_service.py` | Turn image bytes into a medicine name string (or `None`). | Regulation lookups, prompt templates unrelated to OCR. |
| `services/search_service.py` | Own the embedding model + FAISS index; return raw scored rows. | Deciding what's a "good" score (business decision, lives in `regulation_service.py`), formatting for the API. |
| `services/regulation_service.py` | Threshold matches, attach flags, compute confidence, resolve alternatives. | Calling FAISS directly (it's handed a `SearchService`), calling Gemini. |
| `services/llm_service.py` | Own the Gemini client; build prompts; parse JSON responses. | Fetching data itself — always receives pre-built context strings. |
| `database/regulation_repository.py` | Load the CSV once, expose `list_countries()`, `list_medicines()`, `summary_stats()`, and raw `dataframe` access. | Ranking, filtering by relevance, formatting for display. |
| `models/schemas.py` | Pydantic request/response shapes. | Any logic — pure data contracts. |
| `utils/logger.py`, `utils/exceptions.py` | Cross-cutting concerns used everywhere. | Anything domain-specific. |
| `scripts/build_index.py` | One-off CLI script to (re)build the FAISS index. | Anything imported by the running app. |

### Frontend

| File | Responsibilities | Should NOT contain |
|---|---|---|
| `app.py` | Page config, load CSS, init session state, route to the active view. | HTML markup, HTTP calls, business logic. |
| `api_client.py` | Every HTTP call to the backend, wrapped in typed functions; translate failures into `ApiError`. | Streamlit calls (`st.*`), rendering. |
| `state.py` | Define and initialize every `st.session_state` key; navigation helper. | Rendering, HTTP calls. |
| `views/*.py` | Render one page each, using `api_client` for data and `components/` for shared fragments. | Direct FAISS/Gemini/pandas access (that's a backend-layering violation), HTTP URL strings (those live only in `api_client.py`). |
| `components/*.py` | Reusable, stateless-ish UI fragments (navbar, footer, country cards, illustrations). | Page-specific business flow. |

---

## 5. Execution flow

```
User (browser)
   │
   ▼
Streamlit frontend (views/*.py)
   │  st.session_state for UI-only state (page, chat history, expanded cards)
   ▼
api_client.py  ── HTTP (JSON) ──▶  FastAPI backend (routes/*.py)
                                        │  validate request → call MedicineService
                                        ▼
                                 services/medicine_service.py (orchestrator)
                                    │        │            │
                                    ▼        ▼            ▼
                             ocr_service  search_service  llm_service
                                    │        │            │
                                    ▼        ▼            ▼
                              Gemini Vision  FAISS index  Gemini text
                                             (via regulation_service
                                              for scoring/flags/alts)
                                        │
                                        ▼
                              database/regulation_repository.py (CSV)
```

## 6. API request flow (example: photo scan)

1. `views/scan.py` reads the uploaded file's bytes and calls `api_client.scan_image(...)`.
2. `api_client.py` sends `POST /api/scan/image` (multipart) to the backend.
3. `routes/scan.py` receives the file, calls `MedicineService.scan_image(bytes, country)`.
4. `MedicineService` calls `OCRService.read_medicine_name()` → Gemini Vision → medicine name string.
5. `MedicineService` calls `RegulationService.get_country_results()` → `SearchService.search()` (FAISS) → scored rows → filtered/flagged/formatted country cards.
6. Route wraps the result in `ScanResponse` and FastAPI serializes it to JSON.
7. `api_client.py` returns the parsed dict; `views/scan.py` renders it via `components/country_card.py`.

## 7. AI pipeline flow

```
Image ──▶ OCRService (Gemini Vision, 1 prompt) ──▶ medicine name
                                                         │
Text query ─────────────────────────────────────────────┤
                                                         ▼
                                    SearchService (embed query → FAISS kNN)
                                                         │
                                                         ▼
                                RegulationService (score threshold, country
                                filter, flags, confidence %, alternatives)
                                                         │
                              ┌──────────────────────────┴─────────────────┐
                              ▼                                            ▼
                   Scan/Search page: return cards directly      Chat: build context text
                   (no LLM call needed — this is a case               │
                   where the earlier design was already right:        ▼
                   don't ask an LLM to reformat data you already   LLMService (prompt +
                   have structured and correct)                    Gemini call + JSON/text
                                                                     parsing)
```

This is actually the pipeline your working app already had, and it's the
right shape: **the LLM is only invoked for OCR and for open-ended
chat/explanation — never to reformat data you already have.** The
FastAPI prototype's `/chat` route ran a fresh Gemini call per medicine
lookup even though `search.py` already computed a fuzzy match; the
refactor keeps structured lookups (Scan Medicine page) fast and
deterministic, and reserves the LLM for the two things only it can do:
reading pixels, and free-form conversation.

---

## 8. Is FastAPI being used correctly?

**In the old prototype, no** — routes did nothing but forward to a service (fine), but the service graph was never assembled (`ai_service.py` imported `from ai.build import search`, a module that doesn't exist anywhere in either zip), there was no dependency injection, no Pydantic response models (raw dicts returned everywhere), and no centralized error handling (a failed Gemini call would 500 with a raw traceback).

**In this redesign:**
- `dependencies.py` is a proper composition root — every service is built once (`lru_cache`) and injected via `Depends()`, which also makes routes trivially testable (override a dependency in a test client).
- Every route declares a `response_model`, so FastAPI validates and documents the shape automatically (`/docs` is fully accurate).
- Domain errors (`MedicineNotDetectedError`, `LLMGenerationError`, etc.) are raised in services and translated to HTTP codes in one place (`app.py`'s exception handler), instead of scattered try/except blocks.
- **Frontend ↔ backend:** plain JSON over HTTP via `requests`, isolated entirely inside `frontend/api_client.py`. The Streamlit process never imports pandas, FAISS, or the Gemini SDK — it can be redeployed, restarted, or replaced with a different UI (e.g. a React app) without touching the backend at all.
- **Service ↔ service (internal):** plain Python function calls / constructor injection — no need for internal HTTP hops, since they run in the same process. `MedicineService` is the only class that talks to more than one other service, which is exactly what an orchestrator should do.

---

## 9. Was `llm.py` doing too much?

Yes, in the original — it mixed the Gemini client setup, prompt text, JSON parsing, *and* was called with data that other files (`rag_search.py`, `regulation_lookup.py`) had already fetched, so the boundary was blurry but not actually broken. My rule for the refactor:

- **Stays in `llm_service.py`:** the Gemini client itself, the three prompt templates (regulation answer / chat answer / follow-up answer), and JSON parsing of the model's response. Prompt text is model-facing and tightly coupled to the exact JSON shape being parsed right below it — splitting prompt-writing into a different file than the parser that depends on its exact output shape would be a false separation.
- **Moved to services:** all data fetching (`search_service.py`, `regulation_service.py`) and all orchestration/sequencing (`medicine_service.py`). `llm_service.py` never touches the CSV, FAISS, or an uploaded file directly — it only receives already-prepared strings/images.
- **How prompts are generated:** each `LLMService` method takes already-formatted context (a string or dict) as a parameter and interpolates it into an f-string template. No prompt is ever built outside this file.
- **How context is passed:** callers (in `medicine_service.py`) build the row-block text or pass the "Know More" card's dict straight through — `llm_service.py` never re-fetches or reshapes that data itself, it only formats it into the prompt.

---

## 10. AI-generated code smells removed

- **Duplicate implementations** collapsed to one: `rag_search.py` + `vector_search.py` → `search_service.py`; two OCR paths (Gemini + EasyOCR) → `ocr_service.py` (Gemini only, since it's already used elsewhere and reads stylized packaging better).
- **Two Gemini SDKs** (`google-genai` vs `google.generativeai`) → standardized on `google-genai`, the one already in production use.
- **Over-commenting / narrator comments** (e.g. "NOTE: The OCR / search analysis logic below is UNCHANGED from the original main.py") removed — comments now explain *why*, not narrate *what changed during a chat session*.
- **God functions**: the original `render_scan()` did UI, OCR calls, search calls, and history logging in one 90-line block; now split into `_handle_image_scan` / `_handle_text_search` / `_log_history`.
- **Ad-hoc error handling** (`except Exception as e: ... f"Error: {e}"`) replaced by a typed exception hierarchy (`utils/exceptions.py`) and one central handler.
- **Inconsistent naming**: `get_ai_response` vs `get_chat_reply` vs `get_followup_reply` (three verbs for "call the LLM") → consistently `answer_*` / `generate_*` based on what layer they're in.
- **Dead code removed**: `doc_emb.py`, `vector_search.py`'s `if __name__ == "__main__"` REPL loop, the unused `services/__init__.py` (was empty).

---

## 11. Files to delete / rename / merge

**Delete:**
- `script/doc_emb.py` — superseded prototype.
- `backend/vector_search.py` — duplicate of the FAISS search logic, merged into `search_service.py`.
- `backend/ocr.py` (EasyOCR path) — superseded by Gemini Vision OCR, already used everywhere else.
- `backend/llm.py` (old `google.generativeai` version) — superseded by the `google-genai` version.
- `backend/search.py` (rapidfuzz-based) — superseded by the FAISS semantic search, which already outperforms simple fuzzy string matching and is what the working app actually shipped with.
- `services/__init__.py` (was empty, no package-level exports needed).

**Rename:**
- `services/csv_services.py` → `database/regulation_repository.py` (it's a data-access layer, not a generic "service").
- `services/regulation_lookup.py` → `services/regulation_service.py` (consistent `*_service.py` naming).
- `services/rag_search.py` → `services/search_service.py`.
- `services/ai_service.py` → merged into `services/medicine_service.py` (see below) rather than renamed.
- Frontend `main.py` → `frontend/app.py` (entrypoint naming convention, avoids confusion with backend `app.py`).

**Merge:**
- `services/ai_service.py` + the OCR-triggering logic scattered in `main.py` → `services/medicine_service.py` (single orchestrator, as requested).
- The `backend.zip`/`frontend.zip` route files → `backend/routes/reference.py` (`countries.py` + `medicines.py` + `stats.py`, since they're all simple read-only reference-data endpoints with no reason to be three files).

---

## 12. Ratings

| | |
|---|---|
| **Original architecture rating** | **3.5/10** — one working monolith (good UI, good prompts) plus an abandoned, incoherently-split FastAPI attempt with duplicate/conflicting implementations and no working entrypoint. |
| **New architecture rating** | **8.5/10** — clear layering, single orchestrator, typed contracts, centralized error handling and DI. Docked from 10 because the CSV/FAISS index are still local files (fine for this scale, would need a real DB + vector store for multi-instance production), and there's no test suite yet. |
| **Refactor difficulty** | **Medium.** No functional/behavioral changes were needed — this was a pure restructuring of already-correct logic (I kept every prompt, every threshold, every UI string identical). The main cost is operational: you now run two processes instead of one, and need `BACKEND_URL`/`CORS_ORIGINS` configured correctly in each environment you deploy to. Budget half a day to stand it up locally, verify each page against the old app, and rotate the exposed API key. |
