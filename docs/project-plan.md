# Project Plan

## Goal

SYNAPTOR AI Tutor는 PDF 학습 자료를 기반으로 사용자가 능동적으로 기억을 인출하고, 오개념을 교정하고, 자기 설명을 통해 개념을 재구성하도록 돕는 뇌과학 기반 개인화 AI 튜터입니다.

이 프로젝트는 단순 문제 생성기가 아니라 다음 질문에 답하는 서비스입니다.

- 사용자가 실제로 기억에서 꺼낼 수 있는가?
- 답변이 자료의 근거와 어디서 어긋나는가?
- 현재 사용자에게 가장 효율적인 다음 학습법은 무엇인가?
- 어떤 개념을 언제 다시 복습해야 장기 기억에 유리한가?

## Recommended Product Shape

대학교 과제 제출과 실제 서비스 확장 모두를 고려해 웹 앱 + FastAPI API 서버 구조를 선택합니다.

- React 웹 UI는 학습 흐름과 개인화 결과를 직관적으로 보여줍니다.
- FastAPI는 PDF 처리, RAG, AI 호출, 학습 데이터 저장, 인증 구조를 명확히 분리합니다.
- Swagger 문서(`/docs`)를 통해 API 기반 서비스 구조도 시연할 수 있습니다.
- 이후 모바일 앱, 결제, 팀 학습 기능을 붙이더라도 API 서버 중심 구조를 유지할 수 있습니다.

## Current Implemented Scope

현재 구현된 핵심 기능은 다음과 같습니다.

- 회원가입/로그인
- JWT access token, refresh token
- 사용자별 학습 자료와 세션 데이터 격리
- PDF 업로드와 텍스트 추출
- PDF page-aware chunk 저장
- lexical + embedding 기반 hybrid RAG
- 핵심 개념 추출
- Active Recall 질문 생성
- 답변 평가
- PDF evidence snippet 반환
- 오개념 탐지
- Level 1~5 힌트 ladder
- 자기 설명 평가
- 개념별 숙련도 업데이트
- 학습 프로필 집계
- 적응형 난이도와 다음 질문 유형 추천
- Daily Review
- 개인화 Dashboard
- 세션 리포트

## Neuro-Learning Loop

| Step | Principle | Implementation |
| --- | --- | --- |
| 1 | Cognitive Chunking | PDF를 page-aware chunk와 개념 단위로 분해 |
| 2 | Active Recall | 설명보다 질문을 먼저 제시 |
| 3 | Prediction Error | 답변과 PDF evidence의 차이를 분석 |
| 4 | Adaptive Scaffolding | Level 1~5 힌트 ladder 제공 |
| 5 | Self-Explanation | 자기 언어 설명을 정확성/완전성/논리성으로 평가 |
| 6 | Spaced Reinforcement | 숙련도와 망각 위험 기반 Daily Review 생성 |

## Architecture

```text
React + TypeScript + Vite
  ├─ AuthPage
  ├─ Dashboard
  ├─ StudyRoom
  └─ DailyReview

FastAPI
  ├─ auth API
  ├─ materials API
  ├─ concepts/questions API
  ├─ answers/hints/self-explanations API
  ├─ profile/reviews/dashboard API
  └─ reports API

Services
  ├─ pdf_service
  ├─ material_chunk_service
  ├─ retrieval_service
  ├─ llm_provider
  ├─ adaptive_learning_service
  ├─ learning_profile_service
  ├─ review_service
  └─ dashboard_service

Database
  ├─ PostgreSQL + Alembic
  ├─ pgvector-ready embedding column
  └─ SQLite fallback for tests
```

## Development Strategy

한 번에 전체 기능을 구현하지 않고, 기능별 브랜치와 커밋을 남깁니다.

| Order | Branch | Main Work |
| --- | --- | --- |
| 1 | `기능/근거검색기반` | RAG foundation, material chunks, evidence logging |
| 2 | `기반/서비스인프라` | PostgreSQL, Alembic, Docker, CI |
| 3 | `기능/사용자인증` | User, JWT, refresh token, data ownership |
| 4 | `기능/벡터검색고도화` | embedding storage, hybrid retrieval |
| 5 | `기능/학습프로필` | user learning profile and recommendation |
| 6 | `기능/일일복습` | daily review API and page |
| 7 | `화면/개인화대시보드` | real dashboard summary API and UI |
| 8 | `화면/학습룸개인화` | personalized StudyRoom flow |
| 9 | `문서/제출시연정리` | demo scenario, checklist, report outline |

## Acceptance Criteria

- A user can register and log in.
- A user can upload a PDF.
- The server extracts text and stores chunks.
- The system retrieves evidence from the uploaded material.
- The system extracts concepts from the material.
- The system generates active recall questions.
- The user can submit an answer.
- The system evaluates the answer with score, feedback, missing points, misconception status, and evidence.
- The user can request progressive hints.
- The user can submit a self explanation.
- Concept mastery and profile metrics update after learning events.
- Daily Review recommends due or risky concepts.
- Dashboard shows personalized learning state and next actions.
- The Study Room UI can demonstrate the full flow without using Swagger directly.

## Remaining Service Roadmap

After assignment submission, the most valuable next steps are:

1. Production deployment
   - Render/Fly.io/Railway or AWS deployment
   - managed PostgreSQL
   - secure environment variable management
2. RAG quality
   - heading-aware chunking
   - stronger hybrid ranking
   - evidence sufficiency threshold
3. Learning analytics
   - mastery trend graph
   - forgetting curve visualization
   - concept map visualization
4. Product readiness
   - rate limiting
   - file upload malware and MIME validation hardening
   - Sentry/logging
   - better empty/error states
5. Scale features
   - paid plans
   - class/team workspace
   - teacher dashboard
   - mobile app
