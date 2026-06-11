# Submission Checklist

과제 제출 전 확인용 체크리스트입니다.

## 기능 체크

- [x] 이메일/비밀번호 회원가입 및 로그인
- [x] JWT access token, refresh token 기반 세션 유지
- [x] 사용자별 자료와 학습 세션 격리
- [x] PDF 업로드
- [x] PDF 텍스트 추출
- [x] 페이지 기반 material chunk 저장
- [x] Hybrid RAG 기반 evidence retrieval
- [x] 핵심 개념 추출
- [x] Active Recall 질문 생성
- [x] 사용자 답변 평가
- [x] PDF 근거 snippet 표시
- [x] 누락 개념 및 오개념 표시
- [x] Level 1~5 단계별 hint ladder
- [x] 자기 설명 평가
- [x] 개념 숙련도와 다음 복습 시점 업데이트
- [x] 사용자 학습 프로필
- [x] 적응형 난이도와 다음 질문 유형 추천
- [x] Daily Review
- [x] 개인화 Dashboard
- [x] 세션 리포트
- [x] Study Room 웹 화면

## 시연 체크

- [ ] 새 사용자로 회원가입이 되는지 확인
- [ ] PDF 업로드 후 preview가 표시되는지 확인
- [ ] 개념 추출 결과가 1개 이상 표시되는지 확인
- [ ] 질문 생성 후 질문 유형/난이도/학습 모드가 표시되는지 확인
- [ ] 답변 평가 후 정확도, 오개념 여부, PDF 근거가 표시되는지 확인
- [ ] 힌트 요청 시 hint ladder가 단계별로 활성화되는지 확인
- [ ] 자기 설명 제출 후 평가 점수와 숙련도가 표시되는지 확인
- [ ] Daily Review에 복습 추천이 표시되는지 확인
- [ ] Dashboard에 학습 프로필, 약한 개념, 오개념 노트, 최근 세션이 표시되는지 확인

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

- Web: `http://localhost:5173`
- Study Room: `http://localhost:5173/study`
- Daily Review: `http://localhost:5173/review`
- API Docs: `http://localhost:8000/docs`

## 검증 체크

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

## 발표 핵심 문장

SYNAPTOR는 요약해주는 AI가 아니라, 사용자가 진짜 알고 있는지 검증하고 이해 착각을 깨는 뇌과학 기반 개인화 학습 코치입니다.

## Git 히스토리 체크

최근 기능별 브랜치:

- `기능/근거검색기반`
- `기반/서비스인프라`
- `기능/사용자인증`
- `기능/벡터검색고도화`
- `기능/학습프로필`
- `기능/일일복습`
- `화면/개인화대시보드`
- `화면/학습룸개인화`
- `문서/제출시연정리`

모든 커밋 메시지는 한글로 작성합니다.

## 제출 전 리스크 체크

- [ ] Gemini API 키를 사용할 경우 `.env`에만 넣고 Git에 올리지 않기
- [ ] 발표 전 샘플 PDF를 미리 준비하기
- [ ] 인터넷 또는 API 장애를 대비해 fallback 동작 확인하기
- [ ] PR/브랜치 히스토리 캡처 준비하기
- [ ] 발표 중 보여줄 사용자 계정과 비밀번호를 미리 정하기
