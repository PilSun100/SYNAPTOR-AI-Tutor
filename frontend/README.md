# SYNAPTOR 프론트엔드

SYNAPTOR AI Tutor의 React 프론트엔드입니다. 사용자가 PDF 강의자료를 업로드하고, AI Chat에서 자료를 이해한 뒤, Study Room에서 직접 개념을 설명하며 점수와 티어를 확인하는 화면을 제공합니다.

전체 서비스 개요와 실행 방법은 루트 [README.md](../README.md)를 참고하세요.

## 화면 구성

프론트엔드는 제출용 제품 표면을 다음 세 화면으로 단순화했습니다.

| 화면 | 역할 |
| --- | --- |
| Study | PDF 업로드/삭제, 기존 자료 선택, 개념별 설명 제출, 단계형 힌트, 점수와 티어 확인 |
| AI Chat | 선택한 자료 기반 짧은 설명, 핵심 키워드, 이해 확인 질문, Study Room 유도 |
| Profile | Recall Strength, Explanation Quality, Hint Dependency, Misconception Risk 요약 |

Dashboard, Daily Review, 리포트 생성, 수동 개념 추출/질문 생성 화면은 제출용 UI에서 노출하지 않습니다. 관련 API와 내부 기능은 백엔드 테스트와 확장용으로 남아 있습니다.

## Study

Study는 기본 진입 화면입니다.

1. PDF를 업로드하거나 기존 자료를 선택합니다.
2. 백엔드 `study/start` API가 개념과 질문을 자동 준비합니다.
3. 사용자는 자료를 보지 않고 개념을 자신의 말로 설명합니다.
4. `Hint` 버튼으로 자료 근거 기반 단계형 힌트를 받습니다.
5. 답변 제출 후 정확도, 힌트 사용량, 개념 점수, 티어를 확인합니다.
6. 학습 중 `다른 자료 선택` 또는 `학습 종료`로 자료 선택 화면에 돌아갈 수 있습니다.
7. 기존 자료 목록에서 자료를 삭제할 수 있습니다.

현재 Study 화면은 별도 `Stuck` 패널 없이 `Hint` 버튼 하나만 사용합니다.

## AI Chat

AI Chat은 시험 공간이 아니라 자료 이해를 돕는 설명 공간입니다.

- 자료가 없으면 Study에서 PDF를 먼저 업로드하라는 안내와 이동 버튼을 보여줍니다.
- 자료를 선택하면 현재 자료명이 명확히 보입니다.
- 질문을 보내면 업로드 자료 evidence를 기준으로 짧게 설명합니다.
- 답변 하단에는 후속 질문 버튼과 `Study Room에서 연습하기` CTA를 보여줍니다.
- 오류가 발생하면 기술 메시지 대신 사용자가 할 수 있는 행동을 안내합니다.

## Profile

Profile은 복잡한 차트 대신 네 가지 학습 지표만 보여줍니다.

- Recall Strength
- Explanation Quality
- Hint Dependency
- Misconception Risk

## 기술 스택

- React
- TypeScript
- Vite
- React Router
- Lucide React

## 실행 준비

```bash
cd frontend
npm install
```

## 환경변수

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

설정하지 않으면 기본값으로 `http://localhost:8000/api`를 사용합니다.

## 개발 서버 실행

```bash
npm run dev -- --host 127.0.0.1
```

기본 접속 주소:

```text
http://127.0.0.1:5173
```

## 빌드

```bash
npm run build
```

## API 연동

API 요청은 `src/api/client.ts`에서 관리합니다.

주요 함수:

- `registerUser`
- `loginUser`
- `getCurrentUser`
- `getMaterials`
- `uploadMaterial`
- `deleteMaterial`
- `startMaterialStudy`
- `requestQuestionHint`
- `submitAnswer`
- `getLearningProfile`
- `sendTutorChatMessage`

내부 테스트와 확장용 함수로 `extractConcepts`, `generateQuestions`, `requestHint`, `submitSelfExplanation`, `getSessionReport`도 남아 있습니다.

## 폴더 구조

```text
frontend/
  src/
    api/          # 백엔드 API client
    auth/         # 인증 context와 protected route
    components/   # 공통 UI 컴포넌트
    layouts/      # 앱 레이아웃
    pages/        # Study, AI Chat, Profile, Auth
    types/        # API 응답 타입
```

## 검증 기준

프론트엔드 변경 후에는 최소한 다음 명령을 실행합니다.

```bash
cd frontend
npm run build
```
