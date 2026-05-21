# Project Plan

## Goal

Brain-Sync AI Tutor는 PDF 또는 텍스트 학습 자료를 기반으로 사용자가 능동적으로 기억을 인출하고, 오개념을 교정하고, 자기 설명을 통해 개념을 재구성하도록 돕는 AI 튜터입니다.

## Recommended Submission Format

대학교 과제 제출에는 웹 앱과 백엔드 API를 함께 구현하는 방식이 가장 적합합니다.

- 웹 UI는 교수자와 동료가 학습 흐름을 쉽게 확인할 수 있습니다.
- FastAPI 서버는 PDF 처리, DB 저장, AI API 호출 구조를 명확히 보여줍니다.
- Swagger 문서(`/docs`)를 통해 API 자체도 시연할 수 있습니다.

## Development Strategy

한 번에 전체 기능을 구현하지 않고, 기능별 브랜치와 커밋을 남깁니다.

| Order | Branch | Main Work |
| --- | --- | --- |
| 1 | `feature/project-setup` | README, docs, env example, gitignore |
| 2 | `feature/backend-foundation` | FastAPI, SQLite, health check |
| 3 | `feature/pdf-upload` | PDF upload, validation, extraction |
| 4 | `feature/concept-extraction` | Gemini concept extraction |
| 5 | `feature/question-generation` | Active Recall questions |
| 6 | `feature/answer-evaluation` | Answer scoring and misconception detection |
| 7 | `feature/adaptive-hinting` | Level 1~5 scaffolding hints |
| 8 | `feature/self-explanation` | Self explanation evaluation |
| 9 | `feature/session-report` | Report API and UI |
| 10 | `feature/submission-polish` | Demo, screenshots, final README |

## MVP Acceptance Criteria

- A user can upload a PDF.
- The server extracts text and stores it.
- The system extracts concepts from the material.
- The system generates at least one question per concept.
- The user can submit an answer.
- The system evaluates the answer and returns feedback.
- The user can request progressive hints.
- The user can submit a self explanation.
- A final report summarizes weak concepts and next review targets.

## Scope Control

SQLite is used for the MVP. PostgreSQL, pgvector, advanced Knowledge Map visualization, mobile app support, and authentication are intentionally deferred until the core learning loop works end to end.
