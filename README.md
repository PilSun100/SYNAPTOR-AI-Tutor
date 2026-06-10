# Brain-Sync AI Tutor

Brain-Sync는 업로드한 학습 자료를 근거로 질문하고, 답변을 평가하고, 오개념을 교정하고, 사용자 상태에 맞는 다음 학습법과 복습 시점을 추천하는 **뇌과학 기반 개인화 AI 튜터**입니다.

단순히 PDF를 요약하거나 문제를 생성하는 앱이 아니라, 사용자가 실제로 기억에서 꺼낼 수 있는지 확인하고 이해한 것 같은 착각을 줄이는 학습 코치로 설계했습니다.

## 핵심 요약

| 구분 | 내용 |
| --- | --- |
| 제품 형태 | React 웹 앱 + FastAPI 백엔드 API |
| 핵심 가치 | 능동 회상, 오개념 탐지, 단계적 힌트, 자기 설명, 간격 반복 |
| AI 방식 | Gemini API + 로컬 fallback provider |
| RAG 방식 | PDF page-aware text chunk + image/diagram description chunk + lexical/embedding hybrid retrieval |
| 개인화 | 회상 점수, 자기 설명 품질, 힌트 의존도, 오개념 빈도, 숙련도 기반 추천 |
| 데이터베이스 | PostgreSQL + Alembic, SQLite 테스트 fallback |
| 시연 흐름 | PDF 업로드 → 멀티모달 chunking → 개념 추출 → 질문 → 답변 평가 → 힌트 → 자기 설명 → 튜터 채팅 → 복습/대시보드 |

## 왜 Brain-Sync인가

기존 AI 학습 도구는 요약, 정답 제공, 단순 문제 생성에 치우치는 경우가 많습니다. Brain-Sync는 다음 질문에 집중합니다.

- 사용자가 방금 본 내용을 실제로 기억에서 꺼낼 수 있는가?
- 답변이 자료의 근거와 어디서 어긋나는가?
- 사용자가 어떤 개념에서 반복적으로 착각하는가?
- 지금은 더 어려운 질문으로 넘어가야 하는가, 더 쉬운 발판이 필요한가?
- 어떤 개념을 오늘 다시 복습해야 장기 기억에 유리한가?

## 주요 기능

### 학습 자료 처리

- PDF 업로드
- 파일 타입과 크기 검증
- PDF 텍스트 추출
- 페이지 번호를 보존한 material chunk 저장
- chunk별 문자 위치와 embedding 저장
- 이미지/도표가 포함된 PDF 페이지를 감지하고 설명 chunk 저장

### RAG 기반 AI 튜터링

- 업로드 자료에서 관련 chunk 검색
- lexical score와 embedding cosine score를 결합한 hybrid retrieval
- 답변 평가, 힌트, 자기 설명에 PDF evidence snippet 제공
- 튜터 채팅에서 사용자의 자유 질문에도 자료 근거 기반 답변 제공
- 텍스트 근거와 이미지/도표 근거를 구분해 표시
- EvidenceLog로 어떤 근거가 사용됐는지 기록

### Neuro-Learning Loop

- Cognitive Chunking: 자료를 개념 단위로 분해
- Active Recall: 설명보다 질문을 먼저 제시
- Prediction Error: 답변과 근거의 차이를 피드백
- Adaptive Scaffolding: Level 1~5 힌트 ladder 제공
- Self-Explanation: 자기 언어 설명을 평가
- Spaced Reinforcement: 숙련도와 망각 위험 기반 복습 추천

### 개인화 학습

- 사용자별 자료, 세션, 숙련도 데이터 격리
- 답변 정확도, 응답 시간, 오개념, 힌트 사용량 반영
- 개념별 숙련도와 다음 복습 시점 업데이트
- 사용자 학습 프로필 생성
- Daily Review 추천
- 개인화 Dashboard 제공

## 전체 아키텍처

```mermaid
flowchart LR
  User[사용자] --> Frontend[React Frontend]
  Frontend --> API[FastAPI Backend]

  API --> Auth[Auth Service<br/>JWT + Refresh Token]
  API --> Material[Material Service<br/>PDF Upload + Text Extraction]
  API --> Retrieval[RAG Retrieval Service<br/>Text + Visual Chunks<br/>Lexical + Embedding]
  API --> Chat[Tutor Chat Service<br/>Evidence-grounded Coaching]
  API --> Tutor[Tutor Services<br/>Concept / Question / Answer / Hint]
  API --> Adaptive[Adaptive Learning Engine]
  API --> Review[Review & Dashboard Services]

  Material --> Storage[(Uploaded Files)]
  Material --> DB[(PostgreSQL + pgvector)]
  Retrieval --> DB
  Tutor --> LLM[Gemini API<br/>or Local Fallback]
  Chat --> Retrieval
  Chat --> LLM
  Adaptive --> DB
  Review --> DB
```

## 학습 흐름

```mermaid
sequenceDiagram
  actor Learner as 학습자
  participant UI as React Study Room
  participant API as FastAPI
  participant RAG as Retrieval Service
  participant LLM as LLM Provider
  participant DB as Database

  Learner->>UI: PDF 업로드
  UI->>API: POST /api/materials/upload
  API->>DB: 자료와 page-aware chunks 저장
  Learner->>UI: 개념 추출 요청
  UI->>API: POST /api/materials/{id}/concepts/extract
  API->>RAG: 자료 근거 검색
  API->>LLM: 근거 기반 개념 추출
  API->>DB: Concept 저장
  Learner->>UI: 질문 생성
  UI->>API: POST /api/concepts/{id}/questions/generate
  API->>DB: Question 저장
  Learner->>UI: 답변 제출
  UI->>API: POST /api/questions/{id}/answer
  API->>RAG: 답변 평가용 evidence 검색
  API->>LLM: 근거 기반 평가
  API->>DB: UserAnswer, EvidenceLog, ConceptMastery 저장
  API-->>UI: 점수, 오개념, 누락 개념, PDF 근거 반환
  Learner->>UI: 자료 기반 자유 질문
  UI->>API: POST /api/materials/{id}/chat
  API->>RAG: 질문 관련 text/image evidence 검색
  API->>LLM: 근거 기반 튜터 코칭 생성
  API-->>UI: 답변, 추천 학습 모드, 다음 행동, 근거 반환
```

## 개인화 엔진

```mermaid
flowchart TD
  A[사용자 답변] --> B[정확도 점수]
  A --> C[응답 시간]
  A --> D[오개념 여부]
  H[힌트 사용량] --> E[힌트 의존도]
  S[자기 설명 평가] --> F[설명 품질]

  B --> M[ConceptMastery]
  C --> M
  D --> M
  E --> M
  F --> M

  M --> P[UserLearningProfile]
  P --> R1[추천 난이도]
  P --> R2[추천 학습법]
  P --> R3[다음 행동]
  M --> R4[Daily Review]
```

## 데이터 모델 개요

```mermaid
erDiagram
  User ||--o{ LearningMaterial : owns
  User ||--o{ LearningSession : starts
  User ||--o{ ConceptMastery : tracks
  User ||--|| UserLearningProfile : has
  User ||--o{ RefreshToken : has

  LearningMaterial ||--o{ MaterialChunk : contains
  LearningMaterial ||--o{ Concept : extracts
  LearningMaterial ||--o{ LearningSession : uses

  Concept ||--o{ Question : generates
  Concept ||--o| ConceptMastery : measures
  Concept ||--o{ SelfExplanation : evaluates

  LearningSession ||--o{ UserAnswer : records
  Question ||--o{ UserAnswer : answered_by
  UserAnswer ||--o{ HintLog : uses
  MaterialChunk ||--o{ EvidenceLog : supports
```

## 화면 구성

| 화면 | 역할 |
| --- | --- |
| Auth Page | 회원가입, 로그인, token 저장 |
| 학습 대시보드 | 추천 학습법, 메모리 강도, 약한 개념, 오개념 노트, 복습 일정, 최근 세션 |
| 학습실 | PDF 업로드부터 질문, 답변 평가, 힌트, 자기 설명, 리포트까지 진행 |
| 튜터 채팅 | 업로드 자료에 대해 RAG 근거 기반으로 질문하고 학습 행동 추천 |
| 오늘 복습 | 오늘 복습할 개념과 추천 이유 표시 |
| Swagger Docs | 백엔드 API 직접 시연 |

## 기술 스택

### 프론트엔드

- React
- TypeScript
- Vite
- React Router
- Lucide React

### 백엔드

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- SQLite fallback
- PyMuPDF
- Gemini API

### 개발/운영 도구

- Docker Compose
- GitHub Actions
- pytest
- ESLint
- Vite build

## 폴더 구조

```text
Brain-Sync-AI-Tutor/
  README.md
  .env.example
  docker-compose.yml
  frontend/
    src/
      api/
      auth/
      components/
      layouts/
      pages/
      types/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
    alembic/
    tests/
  data/
    uploads/
  docs/
    demo-scenario.md
    project-plan.md
    report-outline.md
    submission-checklist.md
```

## 실행 방법

### 1. 환경변수 준비

```bash
cp .env.example .env
```

기본 `.env.example`은 Docker Compose 기준 PostgreSQL을 사용합니다.

```env
GEMINI_API_KEY=
ENVIRONMENT=development
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_DIMENSIONS=768
DATABASE_URL=postgresql+psycopg://brain_sync:brain_sync_password@localhost:5432/brain_sync
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_MB=20
CORS_ORIGINS=http://localhost:5173
JWT_SECRET_KEY=change-this-development-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
AUTO_CREATE_TABLES=false
VITE_API_BASE_URL=http://localhost:8000/api
```

Gemini API 키가 없으면 로컬 fallback 로직으로 동작합니다. 실제 AI 응답 품질을 확인하려면 `GEMINI_API_KEY`를 설정하세요.

운영 환경에서는 반드시 다음 값을 변경해야 합니다.

- `ENVIRONMENT=production`
- 32자 이상의 고유한 `JWT_SECRET_KEY`
- 실제 운영 DB `DATABASE_URL`
- 허용할 프론트엔드 도메인 `CORS_ORIGINS`

### 2. Docker Compose로 전체 실행

```bash
docker compose up --build
```

컨테이너가 올라오면 다음 주소로 접속합니다.

| 대상 | 주소 |
| --- | --- |
| 프론트엔드 | `http://localhost:5173` |
| 백엔드 API | `http://localhost:8000/api` |
| Swagger 문서 | `http://localhost:8000/docs` |

백엔드 컨테이너는 시작 시 자동으로 Alembic migration을 실행합니다. migration만 수동으로 적용하려면 다음 명령을 사용합니다.

```bash
docker compose exec backend alembic upgrade head
```

### 3. 로컬에서 따로 실행

백엔드:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

프론트엔드:

```bash
cd frontend
npm install
npm run dev
```

### 4. 빠른 SQLite 테스트

PostgreSQL 없이 빠르게 백엔드 테스트를 돌리고 싶다면 `.env` 또는 실행 환경에서 다음 값을 사용합니다.

```env
DATABASE_URL=sqlite:///./data/brain_sync.db
AUTO_CREATE_TABLES=true
```

## 주요 API

| 메서드 | 엔드포인트 | 설명 |
| --- | --- | --- |
| GET | `/api/health` | 서버 상태 확인 |
| POST | `/api/auth/register` | 회원가입 및 token 발급 |
| POST | `/api/auth/login` | 로그인 및 token 발급 |
| POST | `/api/auth/refresh` | refresh token으로 access token 재발급 |
| GET | `/api/auth/me` | 현재 로그인 사용자 조회 |
| GET | `/api/materials` | 로그인 사용자의 업로드 자료 목록 조회 |
| POST | `/api/materials/upload` | PDF 업로드 및 텍스트 추출 |
| POST | `/api/materials/{material_id}/chat` | 자료 근거 기반 튜터 채팅 |
| POST | `/api/materials/{material_id}/concepts/extract` | 핵심 개념 추출 |
| POST | `/api/concepts/{concept_id}/questions/generate` | Active Recall 질문 생성 |
| POST | `/api/questions/{question_id}/answer` | 답변 평가, 오개념 탐지, evidence 반환 |
| POST | `/api/answers/{answer_id}/hint` | 단계별 힌트 생성 |
| POST | `/api/concepts/{concept_id}/self-explanation` | 자기 설명 평가 |
| GET | `/api/profile/learning` | 사용자 학습 프로필 조회 |
| GET | `/api/reviews/daily` | 오늘의 복습 추천 조회 |
| GET | `/api/dashboard/summary` | 개인화 대시보드 요약 조회 |
| GET | `/api/sessions/{session_id}/report` | 세션 리포트 조회 |

대부분의 학습 API는 인증이 필요합니다.

```text
Authorization: Bearer <access_token>
```

## 검증

백엔드:

```bash
cd backend
.venv/bin/python -m pytest
```

프론트엔드:

```bash
cd frontend
npm run lint
npm run build
```

CI에서는 백엔드 테스트, 프론트엔드 lint, 프론트엔드 build를 실행합니다.

## 데모 시나리오

짧은 발표에서는 다음 흐름만 보여줘도 Brain-Sync의 차별점이 드러납니다.

1. 회원가입 또는 로그인
2. PDF 업로드
3. 핵심 개념 추출
4. 질문 생성
5. 일부러 불완전한 답변 제출
6. 정확도, 누락 개념, 오개념, PDF 근거 확인
7. Level 1~5 hint ladder 확인
8. 자기 설명 평가
9. 튜터 채팅에서 같은 자료에 대해 자유 질문하고 근거 snippet 확인
10. 오늘 복습과 학습 대시보드에서 개인화 결과 확인

상세 시연 대본은 [docs/demo-scenario.md](docs/demo-scenario.md)를 참고하세요.

## 제출/문서 자료

| 문서 | 용도 |
| --- | --- |
| [docs/demo-scenario.md](docs/demo-scenario.md) | 발표 시연 순서 |
| [docs/project-plan.md](docs/project-plan.md) | 프로젝트 계획과 아키텍처 |
| [docs/report-outline.md](docs/report-outline.md) | 과제 보고서 목차 초안 |
| [docs/submission-checklist.md](docs/submission-checklist.md) | 제출 전 점검 목록 |
| [backend/README.md](backend/README.md) | 백엔드 상세 실행/구조 |
| [frontend/README.md](frontend/README.md) | 프론트엔드 상세 실행/구조 |

## 현재 완성도와 남은 작업

과제 시연 기준으로는 핵심 기능이 거의 완성되어 있습니다.

- 과제 시연용 완성도: 약 95%
- 실제 서비스 MVP 완성도: 약 60%
- 상용 SaaS 완성도: 약 35~40%

실제 서비스로 확장하려면 다음 작업이 남아 있습니다.

- 운영 배포 환경 구성
- 파일 업로드 보안 강화
- rate limit과 logging/Sentry 추가
- evidence 부족 시 답변 보류 정책 강화
- heading-aware chunking
- 이미지/도표 설명 품질 평가와 figure-level region extraction
- 장기 학습 데이터 기반 forgetting curve
- mastery trend graph
- 교사용/관리자 대시보드
- 결제와 구독 기능

## 개발 원칙

- 기능별 브랜치와 한글 커밋 메시지를 유지합니다.
- 정답 제공보다 능동 회상과 자기 설명을 우선합니다.
- 답변 평가와 힌트는 업로드 자료의 evidence를 근거로 합니다.
- 데모용 임시 구현보다 실제 서비스 확장이 가능한 구조를 우선합니다.
