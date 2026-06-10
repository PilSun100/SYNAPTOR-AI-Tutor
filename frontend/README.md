# Brain-Sync 프론트엔드

Brain-Sync AI Tutor의 React 프론트엔드입니다. 사용자가 PDF를 업로드하고, 능동 회상 질문에 답하고, 근거 기반 피드백과 개인화 학습 추천을 확인하는 웹 화면을 제공합니다.

## 역할

프론트엔드는 다음 화면을 제공합니다.

- 로그인/회원가입
- 개인화 Dashboard
- Study Room
- Daily Review

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

프론트엔드 실행 환경에 다음 값을 설정합니다.

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

설정하지 않으면 기본값으로 `http://localhost:8000/api`를 사용합니다.

## 개발 서버 실행

```bash
npm run dev
```

기본 접속 주소:

```text
http://localhost:5173
```

## 빌드

```bash
npm run build
```

## 린트

```bash
npm run lint
```

## 주요 화면

### Auth Page

사용자 회원가입과 로그인을 처리합니다. 로그인 후 access token과 refresh token을 저장하고, 보호된 라우트에 접근할 수 있게 합니다.

### Dashboard

사용자의 학습 상태를 한 화면에 보여줍니다.

- 추천 학습법
- 오늘 최우선 복습
- 회상 점수
- 자기 설명 품질
- 메모리 강도
- 약한 개념
- 반복 오개념
- 복습 일정
- 최근 세션

### Study Room

핵심 학습 흐름을 시연하는 화면입니다.

1. PDF 업로드
2. 핵심 개념 추출
3. 질문 생성
4. 답변 제출
5. 근거 기반 답변 평가
6. Level 1~5 hint ladder
7. 자기 설명 평가
8. 세션 리포트 조회

상단에는 현재 학습 모드, 권장 난이도, 오늘 복습 포커스를 표시해 개인화가 학습 중에도 보이도록 구성했습니다.

### Daily Review

망각 위험, 오개념, 힌트 의존도, 다음 복습 시점을 바탕으로 오늘 복습할 개념을 우선순위 카드로 보여줍니다.

## API 연동

API 요청은 `src/api/client.ts`에서 관리합니다.

주요 함수:

- `registerUser`
- `loginUser`
- `getCurrentUser`
- `getDashboardSummary`
- `getDailyReview`
- `uploadMaterial`
- `extractConcepts`
- `generateQuestions`
- `submitAnswer`
- `requestHint`
- `submitSelfExplanation`
- `getSessionReport`

## 폴더 구조

```text
frontend/
  src/
    api/          # 백엔드 API client
    auth/         # 인증 context와 protected route
    components/   # 공통 UI 컴포넌트
    layouts/      # 앱 레이아웃
    pages/        # 주요 화면
    types/        # API 응답 타입
```

## 검증 기준

프론트엔드 변경 후에는 최소한 다음 명령을 실행합니다.

```bash
cd frontend
npm run lint
npm run build
```
