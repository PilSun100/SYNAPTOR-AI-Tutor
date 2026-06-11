<img src="https://github.com/user-attachments/assets/ab117c9f-7cbf-4b70-915c-8bbe8da3fc37" alt="SYNAPTOR Logo" width="800" />

# SYNAPTOR AI Tutor

SYNAPTOR는 사용자가 업로드한 강의자료를 바탕으로 개념을 정리하고, 사용자가 직접 설명하도록 유도하는 자료 기반 AI 튜터입니다.

앱의 목표는 정답을 바로 보여주는 것이 아니라, 사용자가 기억에서 개념을 꺼내 설명하고 필요한 만큼만 힌트를 받아 이해도를 높이는 것입니다.

## 핵심 흐름

1. PDF 강의자료를 업로드하거나 기존 자료를 선택합니다.
2. SYNAPTOR가 자료에서 학습할 개념을 자동으로 준비합니다.
3. 사용자는 개념을 하나씩 자신의 말로 설명합니다.
4. 막히면 자료 근거 기반 힌트를 단계적으로 받습니다.
5. 답변 정확도와 힌트 사용량으로 개념 점수와 자료 티어를 계산합니다.

## 화면 구성

| 화면 | 역할 |
| --- | --- |
| Study | 자료 업로드, 개념 설명, 자료 기반 힌트, 답변 평가, 티어 확인 |
| AI Chat | 선택한 자료를 바탕으로 짧은 소크라틱 코칭 제공 |
| Profile | 회상력, 설명 품질, 힌트 의존도, 오개념 위험 요약 |

## Study Room

Study Room은 자료를 여러 개념으로 나누고, 각 개념에 대해 사용자가 직접 설명하도록 요구합니다.

- `/api/materials/{material_id}/study/start`가 자료의 개념과 질문을 자동 준비합니다.
- 같은 개념이 `(1)`, `(2)`처럼 여러 슬라이드로 나뉘면 하나의 개념으로 묶어 보여줍니다.
- 번호만 다른 개념을 그대로 묻지 않고, 하나의 통합 개념으로 설명하게 하거나 실제 하위 주제가 드러나도록 정리합니다.
- 쉬운 개념은 3개, 보통 개념은 4개, 어려운 개념은 5개의 힌트 예산을 가집니다.

## 자료 기반 힌트

힌트는 일반적인 방향 제시가 아니라 업로드한 강의자료의 관련 chunk를 검색한 뒤, 이해를 돕는 발판을 단계적으로 제공합니다.

예를 들어 자료에 다음 내용이 있다면:

```text
Persistent 볼륨
- 클러스터가 관리하는 스토리지(볼륨) 자원
- Pod와 별개의 생명 주기를 가짐
- Pod에 직접 할당하지 않고 중간에 PVC를 거쳐 사용할 수 있게 함
```

힌트는 다음처럼 점점 구체화됩니다.

| 단계 | 예시 |
| --- | --- |
| Hint 1 | `Persistent 볼륨은 무엇을 다루고, Pod와 어떤 관계가 있나요?`처럼 스스로 떠올릴 질문을 제시 |
| Hint 2 | 자료 근거를 바탕으로 관련 개념을 짧게 설명 |
| Hint 3 | `Persistent 볼륨은 ...와 관련된 개념이다. 특히 자료에서는 ...를 강조한다.` 같은 문장 틀 제공 |
| Hint 4 | 핵심 키워드: 스토리지, 볼륨, 생명 주기, PVC |
| Hint 5 | 자료의 핵심 구조를 거의 완성된 형태로 제시하되, 사용자가 직접 문장화하도록 유도 |

`Stuck` 버튼도 같은 힌트 예산을 사용합니다.

| Stuck 유형 | 코칭 방향 |
| --- | --- |
| 단어가 기억나지 않아요 | 자료 문장의 핵심 키워드 단서 |
| 개념은 아는데 설명이 안 돼요 | 문장 틀과 설명 순서 |
| 질문이 이해되지 않아요 | 더 작은 하위 질문 |
| 두 개념이 헷갈려요 | 관리 주체, 생명 주기, 연결 방식 같은 비교 기준 |

## 티어

자료 이해도는 답변 정확도와 힌트 사용량을 함께 반영합니다.

| 티어 | 의미 |
| --- | --- |
| 초심자 | 개념의 윤곽을 잡는 단계 |
| 견습생 | 힌트를 통해 핵심을 떠올릴 수 있는 단계 |
| 숙련자 | 개념을 자신의 말로 설명할 수 있는 단계 |
| 탐구자 | 개념 간 관계를 연결하고 비교할 수 있는 단계 |
| 현자 | 힌트 없이 깊이 있게 설명할 수 있는 단계 |

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
- Alembic
- SQLite local fallback
- PostgreSQL 지원
- PyMuPDF
- Gemini API + local fallback provider

## 주요 API

| 메서드 | 엔드포인트 | 설명 |
| --- | --- | --- |
| GET | `/api/health` | 서버 상태 확인 |
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |
| GET | `/api/materials` | 자료 목록 |
| POST | `/api/materials/upload` | PDF 업로드 |
| POST | `/api/materials/{material_id}/study/start` | 자료 학습 시작 |
| POST | `/api/questions/{question_id}/hint` | 답변 전 자료 기반 힌트 |
| POST | `/api/questions/{question_id}/answer` | 답변 제출 및 평가 |
| POST | `/api/materials/{material_id}/chat` | 자료 기반 AI Chat |
| GET | `/api/profile/learning` | 학습 프로필 |

대부분의 API는 다음 인증 헤더가 필요합니다.

```text
Authorization: Bearer <access_token>
```

## 실행 방법

### 환경변수

```bash
cp .env.example .env
```

주요 값:

```env
GEMINI_API_KEY=
ENVIRONMENT=development
DATABASE_URL=sqlite:///./data/synaptor.db
AUTO_CREATE_TABLES=true
VITE_API_BASE_URL=http://localhost:8000/api
```

Gemini API가 실패하거나 키가 없으면 local fallback provider가 동작합니다.

### 백엔드

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

접속 주소:

```text
http://127.0.0.1:5173
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
npm run build
```
