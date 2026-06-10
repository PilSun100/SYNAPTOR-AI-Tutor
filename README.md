# Brain-Sync AI Tutor

뇌과학 기반 능동적 학습 AI 튜터입니다. 강의 자료를 분석하여 사용자에게 정답 대신 역질문과 단계별 힌트를 제공하고, 스스로 답을 찾게 유도하여 장기 기억 형성을 돕는 학습 지원 시스템입니다.

이 프로젝트는 AI 모델을 직접 학습시키기보다, Gemini API를 활용해 뇌과학 및 인지과학 기반 튜터링 로직을 구현하는 데 초점을 둡니다.

## 현재 구현 상태

현재 MVP는 웹 화면과 백엔드 API를 통해 아래 흐름을 끝까지 시연할 수 있습니다.

```text
회원가입/로그인
→ PDF 업로드
→ 텍스트 추출
→ 핵심 개념 추출
→ Active Recall 질문 생성
→ 사용자 답변 평가
→ 사용자 수준 추정 및 맞춤 설명
→ Level 1~5 힌트 요청
→ 자기 설명 평가
→ 세션 리포트 조회
```

Gemini API 키가 없으면 로컬 fallback 로직으로 동작하므로, API 키 없이도 과제 시연과 테스트가 가능합니다.

## 프로젝트 목적

기존 AI 학습 도구는 요약, 정답 제공, 단순 문제 생성에 치우치는 경우가 많습니다. Brain-Sync AI Tutor는 학습자가 스스로 기억을 인출하고, 오개념을 발견하고, 단계적 힌트를 통해 정답에 접근하고, 자신의 언어로 다시 설명하도록 돕습니다.

이 서비스의 차별점은 **이해한 것 같은 착각을 깨는 학습 코치**라는 점입니다. 사용자가 답을 바로 보지 않고, 자신의 답변이 왜 부족한지 확인한 뒤 다시 설명하도록 설계했습니다.

핵심 학습 원리는 다음과 같습니다.

- 인지 부하 조절
- 능동적 회상
- 예측 오류 기반 학습
- 오개념 탐지
- 단계적 힌트 제공
- 자기 설명
- 간격 반복 복습

## 제출 형태

대학교 과제 제출용으로는 **웹 앱 + 백엔드 API 서버** 구조를 사용합니다.

- 웹 앱만 만들면 AI 처리 구조와 API 설계를 보여주기 어렵습니다.
- API만 만들면 교수자나 동료가 시연 흐름을 직관적으로 보기 어렵습니다.
- 모바일 앱은 개발 범위가 커지고 PDF 처리, AI 연동, 데이터 저장 로직을 설명하기 어렵습니다.

따라서 React 웹 화면에서 학습 흐름을 시연하고, FastAPI 서버가 PDF 처리와 AI 튜터 API를 제공하는 형태가 가장 적합합니다.

## Neuro-Learning Loop

서비스의 핵심 학습 루프는 다음 6단계입니다.

1. **Cognitive Chunking**
   - 학습 자료를 작업 기억이 처리하기 쉬운 개념 단위로 분해합니다.
2. **Active Recall Prompting**
   - AI가 먼저 설명하지 않고, 사용자가 기억에서 답을 꺼내도록 질문합니다.
3. **Prediction Error Trigger**
   - 오답이나 불완전한 답변이 나오면 정답을 바로 제공하지 않고 오류를 인식하도록 역질문합니다.
4. **Adaptive Scaffolding**
   - 사용자의 답변 품질, 응답 시간, 반복 오답 여부를 바탕으로 Level 1~5 힌트를 제공합니다.
5. **Self-Explanation & Reconstruction**
   - 정답 도달 후 사용자가 개념을 자기 언어로 다시 설명하고, AI가 설명 품질을 평가합니다.
6. **Spaced Reinforcement**
   - 개념별 숙련도를 저장하고 취약 개념을 적절한 시점에 다시 복습하게 합니다.

## 핵심 구현 로직

- **Data Pipeline**: PDF 학습 자료를 파싱하여 텍스트를 추출하고, 개념 추출과 질문 생성을 위한 근거 자료로 저장합니다.
- **User Ownership**: 회원가입/로그인 후 사용자별 자료, 세션, 숙련도 데이터를 분리해 저장합니다.
- **Hybrid RAG**: PDF를 페이지별 chunk로 저장하고, lexical score와 embedding cosine score를 함께 사용해 질문/답변/힌트 평가 근거를 검색합니다.
- **Tutor Logic**: LLM API를 활용해 사용자의 답변을 분석하고, 뇌과학 로직에 따른 다음 질문이나 힌트를 생성합니다.
- **Socratic Interaction**: 정답을 바로 알려주지 않고 사용자의 오류 지점을 역질문과 단계별 힌트로 좁혀 갑니다.
- **Adaptive Learning Engine**: 답변 정확도, 응답 시간, 오개념, 힌트 의존도를 바탕으로 개념별 사용자 수준과 다음 난이도를 계산합니다.
- **Learning Profile**: 답변, 힌트, 자기 설명 기록을 사용자 단위로 집계해 추천 학습법과 취약 개념을 제공합니다.
- **Daily Review**: 개념별 숙련도, 오개념, 힌트 의존도, 다음 복습 시점을 바탕으로 오늘 복습할 항목을 추천합니다.
- **Personalized Dashboard**: 학습 프로필, 오늘의 복습, 약한 개념, 반복 오개념, 최근 세션을 한 화면에서 제공합니다.
- **Learning Report**: 세션 종료 후 오답 패턴, 취약 개념, 다음 복습 추천을 제공합니다.

## 차별화 포인트

- **정답 금지 모드**: 사용자가 틀려도 바로 정답을 제공하지 않고 단계별 힌트를 제공합니다.
- **이해 착각 탐지**: 답변 점수, 누락 개념, 오개념 여부를 분리해 보여줍니다.
- **자기 설명 평가**: 정답 여부만 보지 않고 정확성, 완전성, 논리 연결성을 평가합니다.
- **개인화 난이도 조절**: 사용자의 현재 수준을 Level 0~5로 판단하고, 다음 질문 유형과 맞춤 설명을 추천합니다.
- **근거 기반 평가**: 답변 평가와 힌트 생성 결과에 업로드 PDF의 page-aware evidence snippet을 함께 제공합니다.
- **학습 프로필 추천**: 회상 점수, 자기 설명 품질, 힌트 의존도, 오개념 빈도를 바탕으로 현재 사용자에게 맞는 학습법을 추천합니다.
- **복습 추천**: 자기 설명과 답변 결과를 바탕으로 다음 복습 개념을 추천합니다.
- **일일 복습 큐**: 망각 위험과 오개념 기록이 높은 개념을 우선순위 카드로 제시합니다.
- **설명 가능한 대시보드**: 추천 학습법, 복습 우선순위, 오개념 교정 이유를 사용자가 확인할 수 있습니다.

## MVP 기능

초기 MVP는 전체 아이디어를 작게 완성하는 데 집중합니다.

- PDF 업로드
- 텍스트 입력
- PDF 텍스트 추출
- 핵심 개념 추출
- 개념별 난이도 분류
- Active Recall 질문 생성
- 사용자 답변 입력
- 답변 평가
- 누락 개념 및 오개념 탐지
- Level 1~5 단계별 힌트
- 자기 설명 제출 및 평가
- 답변 기반 사용자 수준 추정
- 수준별 맞춤 설명과 다음 질문 추천
- 난이도 상승 또는 인지 부하 완화 전략 제공
- 학습 세션 저장
- 세션 리포트 표시
- 다음 복습 추천 개념 표시
- 이메일/비밀번호 회원가입 및 로그인
- JWT access token, refresh token 기반 세션 유지
- 로그인 사용자 기준 자료와 학습 세션 격리

## MVP 제외 기능

다음 기능은 핵심 학습 루프가 안정화된 뒤 확장합니다.

- 복잡한 Knowledge Map 시각화
- 정교한 기억 유지도 그래프
- 모바일 앱
- 결제 기능
- 팀 학습 기능
- 음성 답변 기능
- 고급 관리자 페이지
- 복잡한 멀티 Agent 구조

## 기술 스택

### Frontend

- React
- TypeScript
- Vite
- React Router
- Lucide React

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- SQLite fallback
- Alembic
- PyMuPDF
- Gemini API

### Development

- Python virtual environment
- npm
- Git branch-based workflow
- pytest
- Vite build

## 아키텍처

```text
Brain-Sync-AI-Tutor/
  README.md
  .env.example
  frontend/
    src/
      api/
      components/
      pages/
      types/
  backend/
    app/
      main.py
      api/
      core/
      db/
      models/
      schemas/
      services/
    tests/
    requirements.txt
  data/
    uploads/
  docs/
    project-plan.md
    demo-scenario.md
```

## 주요 API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | 서버 상태 확인 |
| POST | `/api/auth/register` | 회원가입 및 token 발급 |
| POST | `/api/auth/login` | 로그인 및 token 발급 |
| POST | `/api/auth/refresh` | refresh token으로 access token 재발급 |
| GET | `/api/auth/me` | 현재 로그인 사용자 조회 |
| GET | `/api/profile/learning` | 사용자 학습 프로필과 추천 학습법 조회 |
| GET | `/api/reviews/daily` | 오늘의 복습 개념과 우선순위 조회 |
| GET | `/api/dashboard/summary` | 개인화 대시보드 요약 조회 |
| POST | `/api/materials/upload` | PDF 업로드 및 텍스트 추출 |
| POST | `/api/materials/{material_id}/concepts/extract` | 핵심 개념 추출 |
| POST | `/api/concepts/{concept_id}/questions/generate` | 개념별 질문 생성 |
| POST | `/api/questions/{question_id}/answer` | 사용자 답변 평가 |
| POST | `/api/answers/{answer_id}/hint` | 단계별 힌트 생성 |
| POST | `/api/concepts/{concept_id}/self-explanation` | 자기 설명 평가 |
| GET | `/api/sessions/{session_id}/report` | 세션 리포트 조회 |

## 데이터 모델 초안

- `User`: 이메일, 비밀번호 해시, 표시 이름, 계정 상태
- `RefreshToken`: refresh token 해시, 만료/폐기 상태
- `UserLearningProfile`: 사용자별 회상 점수, 자기 설명 품질, 힌트 의존도, 추천 학습법
- `LearningMaterial`: 사용자별 업로드 학습 자료와 추출 텍스트
- `MaterialChunk`: PDF 페이지별 검색 chunk와 문자 위치
- `MaterialChunk.embedding`: pgvector 기반 semantic retrieval을 위한 chunk embedding
- `Concept`: 자료에서 추출된 핵심 개념
- `Question`: 개념별 Active Recall 질문
- `LearningSession`: 사용자별 학습 세션
- `UserAnswer`: 사용자 답변과 평가 결과
- `HintLog`: 단계별 힌트 기록
- `EvidenceLog`: 질문, 답변 평가, 힌트, 자기 설명에 사용된 근거 chunk 기록
- `SelfExplanation`: 자기 설명과 평가 결과
- `ConceptMastery`: 개념별 숙련도, 인지 부하, 자신감, 힌트 의존도, 다음 난이도, 다음 복습 시점

## 개발 순서

기능별 브랜치와 커밋을 남기며 순차적으로 개발합니다.

1. `feature/project-setup`
   - README, 문서, 환경변수 예시, Git ignore 규칙 작성
2. `feature/backend-foundation`
   - FastAPI 앱, SQLite 연결, health check API 구현
3. `feature/pdf-upload`
   - PDF 업로드, 파일 검증, 텍스트 추출, DB 저장 구현
4. `feature/concept-extraction`
   - Gemini 기반 핵심 개념 추출 구현
5. `feature/question-generation`
   - Active Recall 질문 생성 구현
6. `feature/answer-evaluation`
   - 답변 평가, 누락 개념, 오개념 탐지 구현
7. `feature/adaptive-hinting`
   - Level 1~5 힌트 생성 구현
8. `feature/self-explanation`
   - 자기 설명 평가와 숙련도 업데이트 구현
9. `feature/session-report`
   - 학습 리포트 API와 화면 구현
10. `feature/frontend-study-flow`
    - Study Room 화면과 백엔드 API 연결
11. `feature/submission-polish`
    - 데모 시나리오, README 보강, 최종 검증
12. `feature/adaptive-learning-engine`
    - 사용자 수준 추정, 맞춤 설명, 다음 질문 난이도 추천 구현

## 실행 방법

서비스형 개발 환경은 Docker Compose 기반 PostgreSQL을 기본으로 사용합니다. 빠른 테스트는 SQLite fallback으로도 실행할 수 있지만, 실제 서비스 개발 기준은 PostgreSQL입니다.

### Environment

```bash
cp .env.example .env
```

Gemini API 키가 없으면 로컬 fallback 로직으로 동작하지만, 실제 서비스 품질 검증은 API 키를 설정한 상태에서 진행합니다.

### Docker Compose

```bash
docker compose up --build
```

Backend 컨테이너는 시작 시 자동으로 DB migration을 적용합니다. 수동으로 migration만 실행해야 할 경우:

```bash
docker compose exec backend alembic upgrade head
```

접속 주소:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api`
- API Docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

기본 접속 주소는 `http://localhost:5173`입니다.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

인증 이후 대부분의 학습 API는 `Authorization: Bearer <access_token>` 헤더가 필요합니다. 프론트엔드는 로그인 후 access token을 자동으로 첨부하고, 만료 시 refresh token으로 한 번 재발급을 시도합니다.

운영 배포 시에는 `ENVIRONMENT=production`을 설정하고, `JWT_SECRET_KEY`를 32자 이상의 고유한 값으로 교체해야 합니다. 기본 개발용 secret을 그대로 두면 서버가 시작되지 않습니다.

PostgreSQL 환경에서는 Alembic migration이 `pgvector` extension과 `material_chunks.embedding` 컬럼을 준비합니다. Gemini API 키가 설정되면 `EMBEDDING_MODEL`로 chunk/query embedding을 생성하고, 로컬 개발에서는 deterministic local embedding으로 동일한 retrieval 흐름을 검증합니다.

## 검증 명령

### Backend

```bash
cd backend
.venv/bin/python -m pytest tests
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

## 데모 시나리오

1. 사용자가 회원가입 또는 로그인을 합니다.
2. 사용자가 PDF 학습 자료를 업로드합니다.
3. 서버가 로그인 사용자 기준으로 PDF 텍스트와 page-aware chunk를 저장합니다.
4. AI가 핵심 개념을 추출합니다.
5. 사용자가 개념별 질문에 답변합니다.
6. AI가 PDF 근거와 함께 답변을 평가하고 오개념을 탐지합니다.
7. 사용자가 막히면 단계별 힌트를 받습니다.
8. 정답에 도달하면 자기 설명을 제출합니다.
9. 세션 종료 후 취약 개념과 복습 추천을 확인합니다.

## 예상 리스크

- Gemini 응답이 항상 원하는 JSON 형식으로 오지 않을 수 있습니다.
- PDF 품질에 따라 텍스트 추출 정확도가 달라질 수 있습니다.
- 정답을 바로 알려주지 않는 힌트는 프롬프트 제어가 중요합니다.
- PostgreSQL/pgvector 운영 환경에서는 migration, backup, access control을 함께 관리해야 합니다.
- 실제 서비스 기준으로 기능을 작게 나누어 브랜치와 커밋 히스토리를 남기는 것이 중요합니다.
