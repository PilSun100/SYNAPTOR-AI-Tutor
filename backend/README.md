# Backend

FastAPI backend for Brain-Sync AI Tutor.

The backend now includes an Adaptive Learning Engine. It updates each
concept mastery record from answer quality, response time, misconception
signals, and hint use, then returns a personalized learning state with the
next difficulty, next question type, learner level, and tailored explanation.

It also includes a RAG-lite foundation. Uploaded PDFs are stored as page-aware
material chunks, retrieval selects the most relevant chunks for questions,
answers, hints, and self-explanations, and answer/hint responses return PDF
evidence snippets.

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
- `POST /api/materials/{material_id}/concepts/extract`
- `POST /api/concepts/{concept_id}/questions/generate`
- `POST /api/questions/{question_id}/answer`
- `POST /api/answers/{answer_id}/hint`
- `POST /api/concepts/{concept_id}/self-explanation`
- `GET /api/sessions/{session_id}/report`

Answer, self-explanation, and report responses include `adaptive_state` or
`adaptive_summary` fields for personalized learning guidance.

## Test

```bash
pytest
```
