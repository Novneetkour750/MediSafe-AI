# MediSafe AI

AI-powered travel medicine regulation checker. Upload a photo of a medicine
(or type its name) and get country-by-country legal status, backed by a
FAISS semantic search over a regulations dataset and Gemini for OCR + explanations.

This is a two-process app: a **FastAPI backend** (owns the data, the AI
calls, and all business logic) and a **Streamlit frontend** (pure UI, talks
to the backend over HTTP). See `ARCHITECTURE.md` for the full design writeup.

## Project layout

```
medisafe-ai/
├── backend/        # FastAPI service — routes, services, database, models
├── frontend/        # Streamlit UI — views, components, api_client
├── dataset/          # medicine_travel_regulations.csv (shared, read by backend only)
├── models/            # medisafe.index (FAISS index, generated — shared, read by backend only)
└── ARCHITECTURE.md   # full architecture review + refactor plan
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and set GEMINI_API_KEY
python scripts/build_index.py   # only needed if models/medisafe.index doesn't exist yet
uvicorn app:app --reload --port 8000
```

Visit `http://localhost:8000/docs` to see the live API docs and try every endpoint directly.

### 2. Frontend (separate terminal)

```bash
cd frontend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # defaults to http://localhost:8000, edit if needed
streamlit run app.py
```

Visit `http://localhost:8501`.



I don't have network/package-install access in this sandbox, so I could not
`pip install fastapi/streamlit/faiss/sentence-transformers` and actually
boot the servers here. Every file has been **syntax-checked** (`py_compile`)
and the import graph was checked by hand, and the logic is a structural
port of your original, working code — but please run it locally and let me
know if anything surfaces; I'm glad to fix it live.
