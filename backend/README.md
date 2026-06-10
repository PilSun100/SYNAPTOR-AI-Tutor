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

RAG retrieval now stores embeddings on `material_chunks` and combines lexical
matching with vector cosine similarity. PostgreSQL uses pgvector through
Alembic migrations, while local SQLite tests store embeddings as JSON text.

This branch adds production-oriented authentication. Users register or log in
with email/password, receive JWT access tokens and refresh tokens, and learning
materials, sessions, and mastery records are scoped to the authenticated user.

It also stores a user learning profile. The profile aggregates recall score,
self-explanation quality, hint dependency, misconception frequency, frustration
risk, weak concepts, and the recommended next learning method.

Daily review recommendations are available for spaced reinforcement. The API
prioritizes concepts by due review time, forgetting risk, misconceptions, weak
mastery, and hint dependency.

The dashboard summary API combines the learning profile, daily review queue,
misconception notes, review schedule, and recent sessions for the personalized
dashboard.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Database

Production-oriented development uses PostgreSQL with Alembic migrations.
The Docker backend container runs `alembic upgrade head` before starting the
API server.

```bash
alembic upgrade head
```

For fast local tests, SQLite can still be used with `AUTO_CREATE_TABLES=true`.

## Run

```bash
uvicorn app.main:app --reload
```

API docs are available at `http://localhost:8000/docs`.

## Current endpoints

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET /api/profile/learning`
- `GET /api/reviews/daily`
- `GET /api/dashboard/summary`
- `POST /api/materials/upload`
- `POST /api/materials/{material_id}/concepts/extract`
- `POST /api/concepts/{concept_id}/questions/generate`
- `POST /api/questions/{question_id}/answer`
- `POST /api/answers/{answer_id}/hint`
- `POST /api/concepts/{concept_id}/self-explanation`
- `GET /api/sessions/{session_id}/report`

Answer, self-explanation, and report responses include `adaptive_state` or
`adaptive_summary` fields for personalized learning guidance.

Most learning endpoints require:

```text
Authorization: Bearer <access_token>
```

Ownership checks return `404` for resources that do not belong to the current
user so the API does not leak the existence of another user's learning data.

## Test

```bash
python -m pytest tests
```
