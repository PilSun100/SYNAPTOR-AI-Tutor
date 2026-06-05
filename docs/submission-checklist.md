# Submission Checklist

과제 제출 전 확인용 체크리스트입니다.

## 기능 체크

- [x] PDF 업로드
- [x] PDF 텍스트 추출
- [x] 핵심 개념 추출
- [x] Active Recall 질문 생성
- [x] 사용자 답변 평가
- [x] 누락 개념 및 오개념 표시
- [x] Level 1~5 단계별 힌트
- [x] 자기 설명 평가
- [x] 개념 숙련도와 다음 복습 시점 업데이트
- [x] 세션 리포트
- [x] Study Room 웹 화면

## 실행 체크

Backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

접속:

- Web: `http://localhost:5173/study`
- API Docs: `http://localhost:8000/docs`

## 검증 체크

Backend:

```bash
cd backend
.venv/bin/python -m pytest tests
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## 발표 핵심 문장

Brain-Sync는 요약해주는 AI가 아니라, 사용자가 진짜 알고 있는지 검증하고 이해 착각을 깨는 뇌과학 기반 학습 코치입니다.

## Git 히스토리 체크

기능별 브랜치:

- `feature/project-setup`
- `feature/backend-foundation`
- `feature/pdf-upload`
- `feature/concept-extraction`
- `feature/question-generation`
- `feature/answer-evaluation`
- `feature/adaptive-hinting`
- `feature/self-explanation`
- `feature/session-report`
- `feature/frontend-study-flow`
- `feature/submission-polish`

모든 커밋 메시지는 한글로 작성합니다.
