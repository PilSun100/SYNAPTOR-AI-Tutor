# Report Outline

이 문서는 과제 보고서에 사용할 수 있는 구조입니다.

## 1. 프로젝트 개요

SYNAPTOR AI Tutor는 사용자가 업로드한 학습 자료를 기반으로 질문, 답변 평가, 힌트, 자기 설명, 복습 추천을 제공하는 뇌과학 기반 개인화 AI 학습 서비스입니다.

핵심 주장은 다음과 같습니다.

> 단순히 정답을 알려주는 AI가 아니라, 사용자가 실제로 이해했는지 검증하고 가장 효율적인 다음 학습 행동을 추천하는 AI 튜터를 구현했다.

## 2. 문제 정의

기존 AI 학습 도구는 다음 한계가 있습니다.

- 요약이나 정답 제공에 치우침
- 사용자가 스스로 기억에서 꺼내는 과정이 부족함
- 틀린 이유와 오개념을 체계적으로 추적하지 않음
- 사용자의 수준 변화에 맞춘 난이도 조절이 약함
- 복습 시점과 망각 위험을 개인화하지 않음

## 3. 핵심 학습 원리

| 원리 | 서비스 적용 |
| --- | --- |
| 인지 부하 조절 | PDF를 개념 단위로 나누고 난이도를 조절 |
| 능동적 회상 | 설명보다 질문을 먼저 제시 |
| 예측 오류 | 사용자 답변과 자료 근거의 차이를 피드백 |
| 오개념 탐지 | 답변 평가에서 오개념 여부를 별도 저장 |
| 단계적 힌트 | Level 1~5 hint ladder 제공 |
| 자기 설명 | 정확성, 완전성, 논리 연결성 평가 |
| 간격 반복 | next_review_at과 Daily Review 제공 |

## 4. 시스템 아키텍처

- Frontend: React, TypeScript, Vite
- Backend: FastAPI, SQLAlchemy
- Database: PostgreSQL, Alembic, SQLite fallback
- RAG: material chunk, lexical retrieval, embedding retrieval
- AI Provider: Gemini API, local fallback provider
- Auth: email/password, JWT access token, refresh token

## 5. 주요 기능

### PDF 기반 학습 자료 처리

PDF를 업로드하면 서버가 텍스트를 추출하고 page-aware chunk로 저장합니다.

### RAG 기반 근거 검색

답변 평가와 힌트 생성은 업로드 자료에서 검색된 evidence chunk를 근거로 수행됩니다. 프론트에서는 page number와 snippet을 보여줍니다.

### Active Recall 질문

AI가 먼저 설명하지 않고 사용자가 기억에서 답을 꺼내도록 질문을 생성합니다.

### 답변 평가와 오개념 탐지

답변은 정확도, 누락 개념, 오개념 여부, 피드백, PDF 근거로 평가됩니다.

### Hint Ladder

힌트는 Level 1부터 Level 5까지 단계적으로 제공되며, 정답을 너무 빨리 공개하지 않도록 설계했습니다.

### Self-Explanation

사용자가 자기 언어로 개념을 다시 설명하면 정확성, 완전성, 논리 연결성으로 평가합니다.

### 개인화 학습 프로필

사용자의 회상 점수, 자기 설명 품질, 힌트 의존도, 오개념 빈도, frustration risk를 집계해 추천 학습법을 계산합니다.

### Daily Review

숙련도, 오개념, 힌트 의존도, 다음 복습 시점을 바탕으로 오늘 복습할 개념을 추천합니다.

### Dashboard

학습 프로필, 약한 개념, 오개념 노트, 복습 일정, 최근 세션을 한 화면에서 보여줍니다.

## 6. 데이터 모델

주요 테이블은 다음과 같습니다.

- `users`
- `refresh_tokens`
- `learning_materials`
- `material_chunks`
- `concepts`
- `questions`
- `learning_sessions`
- `user_answers`
- `hint_logs`
- `evidence_logs`
- `self_explanations`
- `concept_mastery`
- `user_learning_profiles`

## 7. API 설계

주요 API:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/materials/upload`
- `POST /api/materials/{material_id}/concepts/extract`
- `POST /api/concepts/{concept_id}/questions/generate`
- `POST /api/questions/{question_id}/answer`
- `POST /api/answers/{answer_id}/hint`
- `POST /api/concepts/{concept_id}/self-explanation`
- `GET /api/profile/learning`
- `GET /api/reviews/daily`
- `GET /api/dashboard/summary`
- `GET /api/sessions/{session_id}/report`

## 8. 구현 결과

현재 구현 결과는 다음 흐름으로 시연할 수 있습니다.

```text
회원가입/로그인
→ PDF 업로드
→ chunk 기반 RAG 준비
→ 개념 추출
→ 질문 생성
→ 답변 평가 with evidence
→ 힌트 ladder
→ 자기 설명 평가
→ 숙련도 업데이트
→ Daily Review
→ Dashboard 개인화 요약
```

## 9. 검증

Backend:

```bash
cd backend
.venv/bin/python -m pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## 10. 한계와 개선 방향

현재 한계:

- embedding 품질과 chunking 전략은 더 개선할 수 있음
- 복습 알고리즘은 초기 규칙 기반이며 장기 사용 데이터로 고도화 필요
- 실제 운영을 위해 rate limit, logging, monitoring 강화 필요
- 모바일 앱과 결제 기능은 아직 제외

개선 방향:

- heading-aware chunking
- evidence sufficiency threshold
- forgetting curve visualization
- teacher dashboard
- 실제 배포 환경 구성

## 11. 결론

SYNAPTOR는 단순한 AI 문제 생성기가 아니라, 뇌과학 기반 학습 원리를 실제 서비스 흐름에 반영한 개인화 AI 튜터입니다. 업로드 자료를 근거로 질문하고, 사용자의 답변을 평가하고, 오개념과 힌트 의존도를 추적하며, 다음 학습 방법과 복습 시점을 추천한다는 점에서 기존 요약형 학습 도구와 차별화됩니다.
