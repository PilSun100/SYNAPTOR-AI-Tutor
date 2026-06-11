# SYNAPTOR 백엔드

SYNAPTOR AI Tutor의 FastAPI 백엔드입니다. PDF 처리, RAG 근거 검색, AI 튜터링 로직, 사용자 인증, 학습 상태 저장, 개인화 추천 API를 담당합니다.

전체 서비스 아키텍처와 시연 흐름은 루트 [README.md](../README.md)를 참고하세요.

## 역할

백엔드는 다음 흐름을 처리합니다.

1. 사용자가 업로드한 PDF를 검증하고 텍스트를 추출합니다.
2. 추출된 텍스트를 페이지 단위 chunk로 저장합니다.
3. 텍스트 chunk와 이미지/도표 설명 chunk를 함께 저장해 멀티모달 RAG 근거로 사용합니다.
4. 개념 추출, 질문 생성, 답변 평가, 힌트 생성, 자기 설명 평가, 튜터 채팅에 필요한 근거 chunk를 검색합니다.
5. Gemini API 또는 로컬 fallback provider를 통해 튜터링 응답을 생성합니다.
6. 답변 점수, 오개념, 힌트 사용량, 자기 설명 품질을 저장합니다.
7. 개념별 숙련도와 다음 복습 시점을 갱신합니다.
8. 사용자 학습 프로필, 일일 복습, 개인화 대시보드 데이터를 제공합니다.

## 핵심 기능

- **사용자 인증**
  - 이메일/비밀번호 회원가입
  - JWT access token
  - refresh token
  - 로그인 사용자 기준 데이터 격리

- **PDF 처리**
  - 파일 타입 검증
  - PDF 텍스트 추출
  - page-aware material chunk 저장
  - 이미지/도표 페이지 감지
  - Gemini Vision 기반 image description chunk 저장

- **RAG 검색**
  - lexical scoring
  - embedding cosine scoring
  - hybrid retrieval
  - text chunk와 image_description chunk 통합 검색
  - evidence snippet 반환
  - evidence log 저장

- **AI 튜터링**
  - 핵심 개념 추출
  - Active Recall 질문 생성
  - 답변 평가
  - 오개념 탐지
  - Level 1~5 힌트 생성
  - 자기 설명 평가
  - 업로드 자료 기반 Tutor Chat

- **개인화 학습**
  - 개념별 숙련도 추적
  - 인지 부하와 힌트 의존도 반영
  - 다음 난이도와 질문 유형 추천
  - 사용자 학습 프로필 집계
  - Daily Review
  - 대시보드 요약 API

## 실행 준비

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 환경변수

루트 `.env` 또는 백엔드 실행 환경에 다음 값을 설정합니다.

```env
DATABASE_URL=sqlite:///./data/synaptor.db
AUTO_CREATE_TABLES=true
JWT_SECRET_KEY=change-this-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
GEMINI_API_KEY=
CORS_ORIGINS=http://localhost:5173
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_MB=20
```

서비스형 개발 환경에서는 PostgreSQL을 기본으로 사용하고, 빠른 로컬 테스트에서는 SQLite fallback을 사용할 수 있습니다.

## 데이터베이스

PostgreSQL 환경에서는 Alembic migration을 적용합니다.

```bash
alembic upgrade head
```

Docker Compose로 실행할 경우 백엔드 컨테이너가 시작 전에 migration을 적용합니다.

테스트 환경에서는 `AUTO_CREATE_TABLES=true`로 SQLite 테이블을 자동 생성할 수 있습니다.

## 실행

```bash
uvicorn app.main:app --reload
```

API 문서는 다음 주소에서 확인합니다.

```text
http://localhost:8000/docs
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
| POST | `/api/questions/{question_id}/answer` | 사용자 답변 평가 |
| POST | `/api/answers/{answer_id}/hint` | 단계별 힌트 생성 |
| POST | `/api/concepts/{concept_id}/self-explanation` | 자기 설명 평가 |
| GET | `/api/profile/learning` | 사용자 학습 프로필 조회 |
| GET | `/api/reviews/daily` | 오늘의 복습 추천 조회 |
| GET | `/api/dashboard/summary` | 개인화 대시보드 요약 조회 |
| GET | `/api/sessions/{session_id}/report` | 세션 리포트 조회 |

대부분의 학습 API는 다음 인증 헤더가 필요합니다.

```text
Authorization: Bearer <access_token>
```

사용자 소유가 아닌 자료나 세션에 접근하면 `404`를 반환해 다른 사용자의 데이터 존재 여부가 노출되지 않도록 했습니다.

## 테스트

```bash
python -m pytest
```

## 폴더 구조

```text
backend/
  app/
    api/        # FastAPI 라우트
    core/       # 설정과 보안 유틸
    db/         # DB 세션, base, migration helper
    models/     # SQLAlchemy 모델
    schemas/    # Pydantic 요청/응답 스키마
    services/   # PDF, RAG, AI, 개인화 학습 서비스
  alembic/      # DB migration
  tests/        # pytest 테스트
```

## 검증 기준

백엔드 변경 후에는 최소한 다음 명령을 실행합니다.

```bash
cd backend
.venv/bin/python -m pytest
```
