# Backend

FastAPI backend for Brain-Sync AI Tutor.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs are available at `http://localhost:8000/docs`.

## Current endpoints

- `GET /api/health`
- `POST /api/materials/upload`

## Test

```bash
pytest
```
