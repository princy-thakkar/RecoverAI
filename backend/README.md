# RecoverAI Backend

FastAPI backend for RecoverAI. This is **Stage 1**: application bootstrap,
CORS, and a health endpoint only. No database, ML, or LLM integration yet.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- API root: http://localhost:8000/
- Health check: http://localhost:8000/api/health
- Interactive docs: http://localhost:8000/docs

CORS is configured to allow the Vite frontend dev server at
`http://localhost:5173` (see `CORS_ORIGINS` in `.env`).

## Test

```bash
pytest tests/ -v
```

## Structure
backend/
├── app/
│ ├── main.py # FastAPI app instance, CORS, router mounting
│ ├── api/ # Route modules (health.py so far)
│ ├── models/ # Pydantic schemas (added in later stages)
│ ├── core/ # Settings/config
│ └── db/ # Database layer (added in Stage 2 — MongoDB)
├── tests/
├── requirements.txt
├── .env.example
└── .env # local only, gitignored