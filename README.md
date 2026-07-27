# MediSafe AI

MediSafe AI is a travel medicine regulation checker. A traveller can upload a
photo of a medicine, or simply type its name, and the system tells them
whether that medicine is allowed, restricted, or banned in different
countries, along with the reason, the relevant authority, travel advice, and
a safe alternative if one exists. There is also an AI chat assistant for
open-ended questions, and a "Know More" option that lets a user ask a
follow-up question about a specific result without losing that context.

This document explains how the project is built, why it is structured the
way it is, and how to run it. It is written for anyone picking up the
codebase for the first time.

## 1. The problem this solves

Medicine regulations are not the same everywhere. A common painkiller or
cold medicine in one country can be restricted or completely banned in
another, and travellers usually have no easy way to check this before they
pack their bags. MediSafe AI gives a traveller a quick, country-by-country
answer, grounded in an actual regulation dataset rather than a generic
web search, and adds an AI layer on top so the user can ask questions in
plain language and get a simple, jargon-free explanation.

## 2. My approach

I treated this as two separate concerns from the start: the part that talks
to the user, and the part that owns the data and the AI calls. That split
is the single most important decision in this project, and everything else
follows from it.

- The **backend** (FastAPI) owns the regulation dataset, the semantic
  search index, and every call to the Gemini API. It is the only part of
  the system that knows about the data or the AI model.
- The **frontend** (Streamlit) only renders pages and calls the backend
  over plain HTTP. It never touches the dataset, the search index, or the
  Gemini API key directly.

The reason for this split is straightforward: the two halves can be run,
restarted, redeployed, or even replaced independently. If the UI needs to
change to a different framework later, the backend does not need to be
touched at all, because the contract between them is just JSON over HTTP.

Within the backend, I broke the work down further by responsibility rather
than by feature, so that each file has exactly one job:

- reading an image and turning it into a medicine name (OCR)
- turning a text query into a ranked list of matching rows (semantic
  search)
- deciding what counts as a good match, attaching flags and a confidence
  score, and working out alternatives (regulation logic)
- talking to the Gemini model and building prompts (the LLM layer)
- coordinating all of the above for each user action (the orchestrator)

One rule I kept throughout: the AI model is only used for the two things it
is actually needed for — reading text off a photo, and answering
open-ended questions. Whenever the answer already exists as structured data
in the dataset (for example, the Scan Medicine results), the app returns
that data directly instead of asking the model to reformat something it
already has. This keeps the core lookup fast, predictable, and cheap to
run, and reserves the AI calls for the parts that genuinely need language
understanding.

## 3. Architecture

```
medisafe-ai/
├── backend/          FastAPI service — owns data, AI calls, business logic
├── frontend/          Streamlit UI — pure presentation, talks to the backend over HTTP
├── dataset/            medicine_travel_regulations.csv — the regulation data
├── models/              medisafe.index — the FAISS semantic search index
└── ARCHITECTURE.md   detailed design notes
```

### Backend layout

```
backend/
├── app.py                        Creates the FastAPI app, sets up CORS and error
│                                  handling, and mounts the routers. No business logic here.
├── config.py                     One place for paths, environment variables, and tuning
│                                  values such as the minimum match score.
├── dependencies.py                Builds every service once and hands it to routes
│                                  through FastAPI's dependency injection.
├── routes/
│   ├── scan.py                   Endpoints for the Scan Medicine page: image upload,
│   │                             manual search, and alternatives.
│   ├── chat.py                   Endpoints for the AI chat and follow-up questions.
│   ├── reference.py                Read-only endpoints: list of countries, list of
│   │                             medicines, and platform statistics.
│   └── health.py                    Health check endpoint.
├── services/
│   ├── medicine_service.py       The orchestrator. Every route calls this, and this is
│   │                             the only service that talks to more than one other
│   │                             service.
│   ├── ocr_service.py             Turns an uploaded image into a medicine name using
│   │                             Gemini Vision.
│   ├── search_service.py          Owns the embedding model and the FAISS index; turns a
│   │                             text query into ranked matching rows.
│   ├── regulation_service.py     Applies the match threshold, attaches country flags,
│   │                             computes a confidence percentage, and resolves
│   │                             alternatives.
│   └── llm_service.py             The only file that calls the Gemini API. Holds the
│                                  prompt templates and parses the model's responses.
├── database/
│   └── regulation_repository.py   Loads the CSV once and exposes read-only access to it.
├── models/schemas.py               Pydantic models that define the exact shape of every
│                                  request and response.
├── utils/
│   ├── logger.py                   Shared logging setup.
│   └── exceptions.py                Custom error types that get converted into proper
│                                  HTTP status codes.
└── scripts/build_index.py           Rebuilds the FAISS index from the CSV whenever the
                                    dataset changes.
```

### Frontend layout

```
frontend/
├── app.py               Entry point: page setup, loads the CSS, sets up session state,
│                         and routes to the current page. No business logic here either.
├── config.py             Backend URL and asset paths.
├── api_client.py          The only file in the frontend that knows the backend's URL or
│                         the shape of its responses. Every backend call goes through here.
├── state.py               Sets up Streamlit's session state in one place.
├── views/
│   ├── home.py            Landing page with a hero section and live platform stats.
│   ├── scan.py             Scan Medicine page — photo upload or manual text search.
│   ├── chat.py              AI Chat page.
│   ├── about.py             About page.
│   └── history.py            Shows the user's past scans and searches for the current
│                            session.
└── components/
    ├── navbar.py, footer.py    Shared page chrome.
    ├── country_card.py          Renders each country's result card, including the
    │                            "Suggest Alternative" and "Know More" buttons.
    └── illustration.py, icons.py   Small presentational helpers.
```

## 4. How a request flows through the system

**Scanning a medicine (photo or typed name):**

1. The user uploads a photo, or types a medicine name, on the Scan Medicine
   page.
2. The frontend sends this to the backend through `api_client.py`.
3. If it was a photo, `OCRService` sends the image to Gemini Vision with a
   prompt that asks it to read only the medicine name off the packaging,
   nothing else.
4. `SearchService` encodes the medicine name (and destination country, if
   given) into an embedding and searches the FAISS index for the closest
   matching rows in the dataset.
5. `RegulationService` takes those raw matches, keeps only the best match
   per country, drops anything below the minimum match score, and attaches
   a flag emoji and a confidence percentage to each result.
6. The results are returned to the frontend as structured JSON and
   rendered as one card per country, with a status badge (allowed,
   restricted, prescription required, or banned).
7. If a result is restricted or banned, the user can tap "Suggest
   Alternative". The backend first checks whether the dataset itself lists
   an alternative for that row; if not, it searches for another medicine
   that is marked "Allowed" for the same country and treated for a similar
   reason. It never invents a substitute that is not backed by the data.
8. The user can also tap "Know More" on any card, which carries that
   specific result over to the AI Chat page as context for a follow-up
   question.

**Asking the AI assistant a question:**

1. The question is sent to the backend.
2. `SearchService` retrieves the handful of dataset rows most relevant to
   the question.
3. `LLMService` builds a prompt that includes only those retrieved rows as
   context, and asks Gemini to answer using that context only, in plain,
   non-technical language.
4. The answer is returned as plain text and shown in the chat window.

**Follow-up ("Know More") questions:**

These skip the search step entirely. The specific card the user was
already looking at is passed straight to `LLMService` as the context, so
the answer stays grounded in exactly what was already shown to the user
instead of triggering a fresh, potentially different search.

## 5. The dataset and the search index

The data lives in `dataset/medicine_travel_regulations.csv`. Each row
represents one medicine's regulatory status in one country, and includes
the medicine name, brand name, generic name, country, status (allowed,
restricted, prescription required, or banned), the regulation type, the
governing authority, the reason for that status, any listed alternative,
travel advice for that medicine, the source of the information, and when
it was last updated. The dataset currently covers 10 countries (Australia,
Canada, France, Germany, India, Japan, Singapore, UAE, UK, and USA) and 55
distinct medicines.

Each row also has a `document` column, a single sentence that summarises
the whole row. `scripts/build_index.py` encodes every one of these
sentences into a vector using the `all-MiniLM-L6-v2` sentence-transformer
model, and stores the vectors in a FAISS index (`models/medisafe.index`).
At query time, the user's question is encoded with the same model, and
FAISS returns the rows whose vectors are closest to it. This is what
allows the search to understand a query like "medicine for headache in
Japan" even if it does not exactly match the wording in the dataset, since
the match is based on meaning rather than exact keywords.

## 6. Technology used

- **Backend:** FastAPI, Pydantic, pandas, FAISS, sentence-transformers,
  the `google-genai` SDK, Pillow, python-dotenv.
- **Frontend:** Streamlit, requests, python-dotenv.
- **AI model:** Google Gemini, used for two purposes only — reading a
  medicine name off a photo, and answering natural-language questions.
- **Search:** FAISS with the `all-MiniLM-L6-v2` embedding model for
  semantic (meaning-based) search over the dataset.

## 7. Running the project

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder with:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
CORS_ORIGINS=*
```

If `models/medisafe.index` does not already exist, build it once from the
dataset:

```bash
python scripts/build_index.py
```

Then start the server:

```bash
uvicorn app:app --reload --port 8000
```

The interactive API docs are available at `http://localhost:8000/docs`,
where every endpoint can be tried directly.

### Frontend (in a separate terminal)

```bash
cd frontend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

By default the frontend looks for the backend at `http://localhost:8000`.
This can be changed by setting a `BACKEND_URL` environment variable if the
backend is running somewhere else.

Visit `http://localhost:8501` to use the app.

## 8. A note on the Gemini API key

The `.env` file used during development has a live `GEMINI_API_KEY` inside
it. Treat that key as compromised if it has ever left a private machine,
and rotate it in Google AI Studio before relying on it further. `.env`
should never be committed to version control.

## 9. Design decisions worth calling out

- **One card per country, always.** The regulation lookup deliberately
  keeps only the single best-scoring match for each country, so a user
  never sees two conflicting cards for the same destination.
- **A minimum match score.** Any match below a configured threshold is
  discarded rather than shown, so the app does not present a low-confidence
  guess as if it were a confirmed answer.
- **Alternatives are never invented.** The alternative suggested to a user
  either comes directly from the dataset's own alternative column, or from
  another medicine already marked "Allowed" in the same country for a
  similar reason. The AI model is never asked to guess a substitute.
- **Errors are typed, not ad hoc.** Failures such as "no medicine could be
  read from that photo" or "the AI call failed" are raised as specific
  exceptions in the backend and translated into proper HTTP status codes
  in one place, instead of being handled differently in every function
  that might fail.
- **The frontend never sees the dataset or the model.** All of it goes
  through `api_client.py`, so the presentation layer can be changed later
  without touching how the data or the AI model are handled.

## 10. Known limitations

- The regulation data and the FAISS index are both local files. This is
  fine at the current scale, but a production deployment serving multiple
  instances would need a proper database and vector store instead.
- There is no automated test suite yet.
- The dataset currently covers 10 countries and 55 medicines; expanding
  coverage means adding rows to the CSV and rebuilding the index.

See `ARCHITECTURE.md` for the full design write-up, including the earlier
state of the project and the reasoning behind each structural change.
