import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  BrainCircuit,
  CalendarClock,
  CheckCircle2,
  FileText,
  FileUp,
  Gauge,
  HelpCircle,
  ListChecks,
  MessageSquareText,
  PlayCircle,
  RefreshCcw,
  Send,
} from 'lucide-react';
import {
  extractConcepts,
  getDashboardSummary,
  generateQuestions,
  getSessionReport,
  requestHint,
  submitAnswer,
  submitSelfExplanation,
  uploadMaterial,
} from '../api/client';
import type {
  AnswerEvaluationResponse,
  Concept,
  DashboardSummaryResponse,
  EvidenceSnippet,
  HintResponse,
  MaterialUploadResponse,
  Question,
  SelfExplanationResponse,
  SessionReportResponse,
} from '../types/api';
import './StudyRoom.css';

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

const questionTypeLabels: Record<string, string> = {
  definition: '정의형',
  cause_effect: '원인-결과형',
  example: '예시 생성형',
  application: '적용형',
  misconception_check: '오개념 점검형',
};

const methodLabels: Record<string, string> = {
  active_recall: 'Active Recall',
  feynman_check: 'Feynman Check',
  misconception_repair: 'Misconception Repair',
  example_first: 'Example First',
  hint_ladder: 'Hint Ladder',
  spaced_review: 'Spaced Review',
  mixed_practice: 'Mixed Practice',
};

const hintLevelLabels: Record<number, string> = {
  1: '방향만 제시',
  2: '관련 개념 연결',
  3: '답변 구조 잡기',
  4: '강한 발판 제공',
  5: '정답 직전 설명',
};

const normalizeQuestionType = (type: string) => type.toLowerCase().replaceAll('-', '_').replaceAll(' ', '_');

const matchesRecommendedType = (questionType: string, recommendedType: string) => {
  const normalizedQuestion = normalizeQuestionType(questionType);
  const normalizedRecommended = normalizeQuestionType(recommendedType);

  if (normalizedRecommended === 'example') {
    return normalizedQuestion.includes('example') || normalizedQuestion.includes('application');
  }
  if (normalizedRecommended === 'misconception_check') {
    return normalizedQuestion.includes('definition') || normalizedQuestion.includes('compare');
  }
  return normalizedQuestion.includes(normalizedRecommended);
};

const EvidenceList = ({ evidence }: { evidence: EvidenceSnippet[] }) => {
  if (evidence.length === 0) {
    return null;
  }

  return (
    <div className="evidence-panel">
      <div className="evidence-title">
        <FileText size={16} />
        <span>PDF 근거</span>
      </div>
      <div className="evidence-list">
        {evidence.map((item) => (
          <div className="evidence-item" key={`${item.chunk_id}-${item.relevance_score}`}>
            <span>
              p.{item.page_number} · relevance {Math.round(item.relevance_score * 100)}%
            </span>
            <p>{item.snippet}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export const StudyRoom = () => {
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummaryResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [material, setMaterial] = useState<MaterialUploadResponse | null>(null);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [selectedConcept, setSelectedConcept] = useState<Concept | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [activeQuestion, setActiveQuestion] = useState<Question | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [answerText, setAnswerText] = useState('');
  const [answerStartedAt, setAnswerStartedAt] = useState<number | null>(null);
  const [answer, setAnswer] = useState<AnswerEvaluationResponse | null>(null);
  const [hints, setHints] = useState<HintResponse[]>([]);
  const [selfExplanationText, setSelfExplanationText] = useState('');
  const [selfExplanation, setSelfExplanation] = useState<SelfExplanationResponse | null>(null);
  const [report, setReport] = useState<SessionReportResponse | null>(null);
  const [loadingLabel, setLoadingLabel] = useState('');
  const [error, setError] = useState('');

  const canRequestHint = Boolean(answer && hints.length < 5);
  const currentHintLevel = hints.length + 1;
  const adaptiveState = selfExplanation?.adaptive_state ?? answer?.adaptive_state ?? report?.adaptive_summary[0] ?? null;
  const learningMode = answer?.misconception_detected
    ? 'misconception_repair'
    : adaptiveState?.next_question_type === 'example'
      ? 'example_first'
      : dashboardSummary?.profile.best_intervention_type ?? 'active_recall';
  const recommendedDifficulty = adaptiveState?.next_difficulty ?? dashboardSummary?.profile.preferred_difficulty_level ?? 'diagnostic';
  const topReview = dashboardSummary?.daily_review.review_items[0] ?? null;
  const coachReason = adaptiveState?.personalized_explanation
    ?? dashboardSummary?.profile.recommendation_reason
    ?? '첫 답변을 제출하면 Brain-Sync가 현재 수준과 다음 학습 방식을 계산합니다.';
  const nextAction = adaptiveState?.recommended_strategy
    ?? dashboardSummary?.profile.next_action
    ?? '자료를 업로드하고 기억에서 직접 답을 꺼내보세요.';

  const steps = useMemo(
    () => [
      { label: '자료', done: Boolean(material) },
      { label: '개념', done: concepts.length > 0 },
      { label: '질문', done: questions.length > 0 },
      { label: '답변', done: Boolean(answer) },
      { label: '힌트', done: hints.length > 0 },
      { label: '설명', done: Boolean(selfExplanation) },
      { label: '리포트', done: Boolean(report) },
    ],
    [answer, concepts.length, hints.length, material, questions.length, report, selfExplanation],
  );

  const runAction = async (label: string, action: () => Promise<void>) => {
    setError('');
    setLoadingLabel(label);
    try {
      await action();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '요청 처리 중 오류가 발생했습니다.');
    } finally {
      setLoadingLabel('');
    }
  };

  const refreshDashboardSummary = async () => {
    try {
      const response = await getDashboardSummary();
      setDashboardSummary(response);
    } catch {
      // Study flow should remain usable even when the dashboard summary is temporarily unavailable.
    }
  };

  useEffect(() => {
    void refreshDashboardSummary();
  }, []);

  const handleUpload = () =>
    runAction('자료 업로드 중', async () => {
      if (!file) {
        throw new Error('PDF 파일을 먼저 선택하세요.');
      }

      const uploaded = await uploadMaterial(file);
      setMaterial(uploaded);
      setConcepts([]);
      setSelectedConcept(null);
      setQuestions([]);
      setActiveQuestion(null);
      setSessionId(null);
      setAnswer(null);
      setHints([]);
      setSelfExplanation(null);
      setReport(null);
      setAnswerText('');
      setSelfExplanationText('');
    });

  const handleExtractConcepts = () =>
    runAction('핵심 개념 추출 중', async () => {
      if (!material) {
        throw new Error('먼저 자료를 업로드하세요.');
      }

      const extracted = await extractConcepts(material.id);
      setConcepts(extracted.concepts);
      setSelectedConcept(extracted.concepts[0] ?? null);
      setQuestions([]);
      setActiveQuestion(null);
      setSessionId(null);
      setAnswer(null);
      setHints([]);
      setSelfExplanation(null);
      setReport(null);
    });

  const handleGenerateQuestions = (concept: Concept) =>
    runAction('질문 생성 중', async () => {
      const generated = await generateQuestions(concept.id);
      setSelectedConcept(concept);
      setQuestions(generated.questions);
      setActiveQuestion(generated.questions[0] ?? null);
      setSessionId(null);
      setAnswerStartedAt(Date.now());
      setAnswer(null);
      setHints([]);
      setSelfExplanation(null);
      setReport(null);
      setAnswerText('');
      setSelfExplanationText('');
    });

  const handleSubmitAnswer = () =>
    runAction('답변 평가 중', async () => {
      if (!activeQuestion) {
        throw new Error('먼저 질문을 생성하세요.');
      }
      if (!answerText.trim()) {
        throw new Error('답변을 입력하세요.');
      }

      const responseTime = answerStartedAt ? (Date.now() - answerStartedAt) / 1000 : undefined;
      const evaluated = await submitAnswer(activeQuestion.id, answerText, responseTime, sessionId);
      setAnswer(evaluated);
      setSessionId(evaluated.session_id);
      setHints([]);
      setReport(null);
      void refreshDashboardSummary();
    });

  const handleRequestHint = () =>
    runAction(`Level ${currentHintLevel} 힌트 요청 중`, async () => {
      if (!answer) {
        throw new Error('답변 평가 후 힌트를 요청할 수 있습니다.');
      }

      const hint = await requestHint(answer.id, currentHintLevel);
      setHints((current) => [...current, hint]);
      void refreshDashboardSummary();
    });

  const handleSubmitSelfExplanation = () =>
    runAction('자기 설명 평가 중', async () => {
      if (!selectedConcept) {
        throw new Error('개념을 먼저 선택하세요.');
      }
      if (selfExplanationText.trim().length < 10) {
        throw new Error('자기 설명은 10자 이상 입력하세요.');
      }

      const evaluated = await submitSelfExplanation(selectedConcept.id, selfExplanationText);
      setSelfExplanation(evaluated);
      void refreshDashboardSummary();

      if (sessionId) {
        const sessionReport = await getSessionReport(sessionId);
        setReport(sessionReport);
      }
    });

  const handleLoadReport = () =>
    runAction('리포트 조회 중', async () => {
      if (!sessionId) {
        throw new Error('답변 평가 후 리포트를 조회할 수 있습니다.');
      }

      const sessionReport = await getSessionReport(sessionId);
      setReport(sessionReport);
    });

  const handleMoveToAdaptiveQuestion = () => {
    if (!adaptiveState || !activeQuestion || questions.length === 0) {
      return;
    }

    const currentIndex = questions.findIndex((question) => question.id === activeQuestion.id);
    const recommended = questions.find(
      (question) =>
        question.id !== activeQuestion.id &&
        matchesRecommendedType(question.question_type, adaptiveState.next_question_type),
    );
    const fallback = questions[(currentIndex + 1 + questions.length) % questions.length];
    const nextQuestion = recommended ?? fallback;

    if (!nextQuestion || nextQuestion.id === activeQuestion.id) {
      return;
    }

    setActiveQuestion(nextQuestion);
    setAnswerText('');
    setAnswer(null);
    setHints([]);
    setSelfExplanation(null);
    setReport(null);
    setAnswerStartedAt(Date.now());
  };

  return (
    <div className="study-room">
      <header className="study-header">
        <div>
          <h1>Brain Training Session</h1>
          <p className="subtitle">PDF에서 개념을 꺼내고, 답변과 힌트로 기억 회로를 훈련합니다.</p>
        </div>
        <div className="status-pill">
          <BrainCircuit size={18} />
          {loadingLabel || 'Ready'}
        </div>
      </header>

      <section className="step-strip glass-panel">
        {steps.map((step) => (
          <div className={`step-chip ${step.done ? 'done' : ''}`} key={step.label}>
            <CheckCircle2 size={16} />
            <span>{step.label}</span>
          </div>
        ))}
      </section>

      <section className="personalization-strip glass-panel">
        <div className="personalization-card primary">
          <BrainCircuit size={20} />
          <div>
            <span>현재 학습 모드</span>
            <strong>{methodLabels[learningMode] ?? learningMode}</strong>
            <p>{coachReason}</p>
          </div>
        </div>
        <div className="personalization-card">
          <Gauge size={20} />
          <div>
            <span>권장 난이도</span>
            <strong>{recommendedDifficulty}</strong>
            <p>{nextAction}</p>
          </div>
        </div>
        <div className="personalization-card">
          <CalendarClock size={20} />
          <div>
            <span>오늘 복습 포커스</span>
            <strong>{topReview?.concept_title ?? '복습 대기 없음'}</strong>
            <p>{topReview?.reason ?? '새 답변이 쌓이면 망각 위험 기반 복습이 생성됩니다.'}</p>
          </div>
        </div>
      </section>

      {error && (
        <div className="error-banner">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="study-grid">
        <section className="glass-panel workflow-panel">
          <div className="panel-title">
            <FileUp size={20} />
            <h2>자료 업로드</h2>
          </div>
          <label className="upload-box">
            <input
              accept="application/pdf"
              type="file"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <span>{file ? file.name : 'PDF 파일 선택'}</span>
          </label>
          <button className="glow-btn full-button" disabled={!file || Boolean(loadingLabel)} onClick={handleUpload}>
            <FileUp size={18} />
            업로드
          </button>

          {material && (
            <div className="result-box">
              <strong>{material.title}</strong>
              <span>{material.extracted_text_length.toLocaleString()}자 추출</span>
              <p>{material.preview}</p>
            </div>
          )}

          <button
            className="secondary-btn full-button"
            disabled={!material || Boolean(loadingLabel)}
            onClick={handleExtractConcepts}
          >
            <ListChecks size={18} />
            핵심 개념 추출
          </button>
        </section>

        <section className="glass-panel workflow-panel">
          <div className="panel-title">
            <ListChecks size={20} />
            <h2>개념 선택</h2>
          </div>
          <div className="concept-list">
            {concepts.length === 0 && <p className="muted">자료 업로드 후 핵심 개념을 추출하세요.</p>}
            {concepts.map((concept) => (
              <button
                className={`concept-item ${selectedConcept?.id === concept.id ? 'active' : ''}`}
                key={concept.id}
                onClick={() => setSelectedConcept(concept)}
              >
                <span>{concept.title}</span>
                <small>{concept.difficulty}</small>
              </button>
            ))}
          </div>
          {selectedConcept && (
            <div className="result-box compact">
              <strong>{selectedConcept.title}</strong>
              <p>{selectedConcept.description}</p>
              <button
                className="secondary-btn full-button"
                disabled={Boolean(loadingLabel)}
                onClick={() => handleGenerateQuestions(selectedConcept)}
              >
                <PlayCircle size={18} />
                질문 생성
              </button>
            </div>
          )}
        </section>

        <section className="glass-panel workflow-panel large-panel">
          <div className="panel-title">
            <MessageSquareText size={20} />
            <h2>능동 회상</h2>
          </div>
          {!activeQuestion && <p className="muted">개념을 선택하고 질문을 생성하세요.</p>}
          {activeQuestion && (
            <>
              <div className="question-box">
                <div className="question-meta-row">
                  <span>{questionTypeLabels[activeQuestion.question_type] ?? activeQuestion.question_type}</span>
                  <span>{selectedConcept?.difficulty ?? recommendedDifficulty}</span>
                  <span>{methodLabels[learningMode] ?? learningMode}</span>
                </div>
                <p>{activeQuestion.question_text}</p>
              </div>
              <textarea
                className="answer-input"
                placeholder="기억에서 직접 꺼낸 답변을 입력하세요."
                value={answerText}
                onChange={(event) => setAnswerText(event.target.value)}
              />
              <button
                className="glow-btn full-button"
                disabled={!answerText.trim() || Boolean(loadingLabel)}
                onClick={handleSubmitAnswer}
              >
                <Send size={18} />
                답변 평가
              </button>
            </>
          )}

          {answer && (
            <div className="evaluation-grid">
              <div className="metric-card">
                <span>정확도</span>
                <strong>{formatPercent(answer.correctness_score)}</strong>
              </div>
              <div className="metric-card">
                <span>오개념</span>
                <strong>{answer.misconception_detected ? '감지' : '없음'}</strong>
              </div>
              <div className="metric-card wide">
                <span>피드백</span>
                <p>{answer.feedback}</p>
              </div>
              {answer.missing_points && (
                <div className="metric-card wide warning">
                  <span>누락 개념</span>
                  <p>{answer.missing_points}</p>
                </div>
              )}
              <div className="metric-card wide">
                <span>개인화 다음 행동</span>
                <p>{nextAction}</p>
              </div>
              <div className="metric-card wide">
                <EvidenceList evidence={answer.evidence} />
              </div>
            </div>
          )}

          {adaptiveState && (
            <div className="adaptive-coach">
              <div className="panel-title">
                <Gauge size={19} />
                <h3>개인화 코치</h3>
              </div>
              <div className="adaptive-metrics">
                <div>
                  <span>현재 수준</span>
                  <strong>{adaptiveState.learner_level_label}</strong>
                </div>
                <div>
                  <span>숙련도</span>
                  <strong>{formatPercent(adaptiveState.mastery_level)}</strong>
                </div>
                <div>
                  <span>인지 부하</span>
                  <strong>{formatPercent(adaptiveState.cognitive_load_score)}</strong>
                </div>
              </div>
              <div className="adaptive-guidance">
                <span>
                  다음 질문: {adaptiveState.next_difficulty} ·{' '}
                  {questionTypeLabels[adaptiveState.next_question_type] ?? adaptiveState.next_question_type}
                </span>
                <p>{adaptiveState.personalized_explanation}</p>
                <p>{adaptiveState.recommended_strategy}</p>
              </div>
              <button
                className="secondary-btn full-button"
                disabled={!activeQuestion || questions.length < 2 || Boolean(loadingLabel)}
                onClick={handleMoveToAdaptiveQuestion}
              >
                <PlayCircle size={18} />
                추천 질문으로 진행
              </button>
            </div>
          )}
        </section>

        <section className="glass-panel workflow-panel">
          <div className="panel-title">
            <HelpCircle size={20} />
            <h2>힌트</h2>
          </div>
          <button className="secondary-btn full-button" disabled={!canRequestHint || Boolean(loadingLabel)} onClick={handleRequestHint}>
            <HelpCircle size={18} />
            Level {Math.min(currentHintLevel, 5)} 힌트
          </button>
          <div className="hint-ladder">
            {[1, 2, 3, 4, 5].map((level) => (
              <div
                className={`hint-step ${hints.length >= level ? 'done' : currentHintLevel === level && answer ? 'current' : ''}`}
                key={level}
              >
                <span>Hint {level}</span>
                <strong>{hintLevelLabels[level]}</strong>
              </div>
            ))}
          </div>
          <div className="hint-list">
            {hints.length === 0 && <p className="muted">답변 평가 후 단계별 힌트를 요청하세요.</p>}
            {hints.map((hint) => (
              <div className="hint-card" key={hint.id}>
                <span>Level {hint.hint_level}</span>
                <p>{hint.hint_text}</p>
                <EvidenceList evidence={hint.evidence} />
              </div>
            ))}
          </div>
        </section>

        <section className="glass-panel workflow-panel">
          <div className="panel-title">
            <RefreshCcw size={20} />
            <h2>자기 설명</h2>
          </div>
          <textarea
            className="answer-input small"
            placeholder="방금 개념을 자신의 언어로 다시 설명하세요."
            value={selfExplanationText}
            onChange={(event) => setSelfExplanationText(event.target.value)}
          />
          <button
            className="secondary-btn full-button"
            disabled={!selectedConcept || selfExplanationText.trim().length < 10 || Boolean(loadingLabel)}
            onClick={handleSubmitSelfExplanation}
          >
            <Send size={18} />
            설명 평가
          </button>
          {selfExplanation && (
            <div className="evaluation-grid compact-grid">
              <div className="metric-card">
                <span>정확성</span>
                <strong>{formatPercent(selfExplanation.accuracy_score)}</strong>
              </div>
              <div className="metric-card">
                <span>완전성</span>
                <strong>{formatPercent(selfExplanation.completeness_score)}</strong>
              </div>
              <div className="metric-card">
                <span>숙련도</span>
                <strong>{formatPercent(selfExplanation.mastery_level)}</strong>
              </div>
            </div>
          )}
        </section>

        <section className="glass-panel workflow-panel report-panel">
          <div className="panel-title">
            <BrainCircuit size={20} />
            <h2>세션 리포트</h2>
          </div>
          <button className="secondary-btn full-button" disabled={!sessionId || Boolean(loadingLabel)} onClick={handleLoadReport}>
            <RefreshCcw size={18} />
            리포트 조회
          </button>
          {!report && <p className="muted">답변 평가 후 리포트를 조회할 수 있습니다.</p>}
          {report && (
            <div className="report-content">
              <div className="report-metrics">
                <div>
                  <span>평균 점수</span>
                  <strong>{formatPercent(report.average_score)}</strong>
                </div>
                <div>
                  <span>오개념</span>
                  <strong>{report.misconception_count}</strong>
                </div>
                <div>
                  <span>복습 추천</span>
                  <strong>{report.next_review_concepts.length}</strong>
                </div>
              </div>
              <div className="review-list">
                {report.next_review_concepts.map((concept) => (
                  <div className="review-item" key={concept.concept_id}>
                    <strong>{concept.title}</strong>
                    <p>{concept.learner_level_label ?? concept.reason}</p>
                    <span>
                      다음: {concept.next_difficulty ?? 'adaptive'} ·{' '}
                      {concept.next_question_type
                        ? questionTypeLabels[concept.next_question_type] ?? concept.next_question_type
                        : '복습'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
