<img src="https://github.com/user-attachments/assets/ab117c9f-7cbf-4b70-915c-8bbe8da3fc37" alt="SYNAPTOR Logo" width="800" />

# SYNAPTOR AI Tutor

SYNAPTOR는 사용자가 업로드한 강의자료를 바탕으로 개념을 정리하고, 사용자가 직접 설명하도록 유도하는 자료 기반 AI 튜터입니다.

앱의 목표는 정답을 바로 보여주는 것이 아니라, 사용자가 기억에서 개념을 꺼내 설명하고 필요한 만큼만 힌트를 받아 이해도를 높이는 것입니다.

## 핵심 흐름

1. PDF 강의자료를 업로드하거나 기존 자료를 선택합니다.
2. SYNAPTOR가 자료에서 학습할 개념과 질문을 자동으로 준비합니다.
3. 사용자는 개념을 하나씩 자신의 말로 설명합니다.
4. 막히면 자료 근거 기반 힌트를 단계적으로 받습니다.
5. 답변 정확도와 힌트 사용량으로 개념 점수와 자료 티어를 계산합니다.

## 화면 구성

| 화면 | 역할 |
| --- | --- |
| Study | 자료 업로드/삭제, 개념 설명, 자료 기반 힌트, 답변 평가, 티어 확인 |
| AI Chat | 선택한 자료를 바탕으로 짧은 설명, 핵심 키워드, 이해 확인 질문 제공 |
| Profile | 회상력, 설명 품질, 힌트 의존도, 오개념 위험 요약 |

## Study Room

Study Room은 자료를 여러 개념으로 나누고, 각 개념에 대해 사용자가 직접 설명하도록 요구합니다.

- `/api/materials/{material_id}/study/start`가 자료의 개념과 질문을 자동 준비합니다.
- 같은 개념이 `(1)`, `(2)`처럼 여러 슬라이드로 나뉘면 하나의 개념으로 묶어 보여줍니다.
- 번호만 다른 개념을 그대로 묻지 않고, 하나의 통합 개념으로 설명하게 하거나 실제 하위 주제가 드러나도록 정리합니다.
- 쉬운 개념은 3개, 보통 개념은 4개, 어려운 개념은 5개의 힌트 예산을 가집니다.
- 학습 중에는 다른 자료 선택 또는 학습 종료로 자료 선택 화면으로 돌아갈 수 있습니다.
- 업로드한 자료는 기존 자료 목록에서 삭제할 수 있으며, 관련 개념/질문/세션/힌트 기록도 함께 정리됩니다.

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

현재 제출용 Study 화면은 별도 `Stuck` 패널 없이 `Hint` 버튼 하나로 단계형 힌트를 제공합니다.

## AI Chat

AI Chat은 시험을 보는 공간이 아니라, 업로드한 강의자료를 이해하기 위한 자료 기반 설명 공간입니다.

- 자료를 선택한 뒤 질문을 입력하면 RAG 검색으로 관련 chunk를 찾습니다.
- Gemini는 해당 evidence 안에서 한국어로 짧고 명확하게 설명합니다.
- 답변은 핵심 설명, 키워드 2~4개, 이해 확인 질문, Study Room으로 이어지는 다음 행동을 포함하도록 조정되어 있습니다.
- 근거가 없으면 아는 척하지 않고 자료에서 확인되지 않는다고 안내합니다.
- Gemini가 JSON 형식에서 벗어나도 앱이 깨지지 않도록 안전한 fallback 응답을 제공합니다.

## 티어

자료 이해도는 답변 정확도와 힌트 사용량을 함께 반영합니다. 의미 없는 답변, 너무 짧은 답변, 반복 문자, placeholder 답변은 0점으로 처리합니다.

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
| DELETE | `/api/materials/{material_id}` | 자료와 관련 학습 기록 삭제 |
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
