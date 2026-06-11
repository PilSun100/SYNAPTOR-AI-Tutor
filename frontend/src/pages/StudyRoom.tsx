import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FileText,
  FileUp,
  HelpCircle,
  Loader2,
  MessageSquareText,
  Send,
  Sparkles,
} from 'lucide-react';
import {
  getMaterials,
  requestQuestionHint,
  startMaterialStudy,
  submitAnswer,
  uploadMaterial,
} from '../api/client';
import type {
  AnswerEvaluationResponse,
  HintResponse,
  MaterialMasterySummary,
  MaterialSummary,
  StudyConceptItem,
} from '../types/api';
import './StudyRoom.css';

const difficultyLabels: Record<string, string> = {
  easy: '쉬움',
  medium: '보통',
  hard: '어려움',
};

const tierDescriptions: Record<string, string> = {
  초심자: '개념의 윤곽을 잡는 중입니다.',
  견습생: '힌트를 통해 핵심을 떠올릴 수 있습니다.',
  숙련자: '개념을 자기 말로 설명할 수 있습니다.',
  탐구자: '개념 간 관계를 연결하고 비교할 수 있습니다.',
  현자: '힌트 없이 깊이 있게 설명할 수 있습니다.',
};

const stuckOptions = [
  { label: '단어가 기억나지 않아요', reason: 'forgot_word' },
  { label: '개념은 아는데 설명이 안 돼요', reason: 'cannot_explain' },
  { label: '질문이 이해되지 않아요', reason: 'question_unclear' },
  { label: '두 개념이 헷갈려요', reason: 'confusing_concepts' },
];

const formatPercent = (value: number) => `${Math.round(value)}점`;

function materialProgress(items: StudyConceptItem[]) {
  const completed = items.filter((item) => item.completed).length;
  return `${completed} / ${items.length}`;
}

export const StudyRoom = () => {
  const [materials, setMaterials] = useState<MaterialSummary[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [material, setMaterial] = useState<MaterialSummary | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [studyItems, setStudyItems] = useState<StudyConceptItem[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [answerText, setAnswerText] = useState('');
  const [answerStartedAt, setAnswerStartedAt] = useState<number | null>(null);
  const [answersByQuestion, setAnswersByQuestion] = useState<Record<number, AnswerEvaluationResponse>>({});
  const [hintsByQuestion, setHintsByQuestion] = useState<Record<number, HintResponse[]>>({});
  const [materialMastery, setMaterialMastery] = useState<MaterialMasterySummary | null>(null);
  const [loadingLabel, setLoadingLabel] = useState('');
  const [error, setError] = useState('');

  const activeItem = studyItems[activeIndex] ?? null;
  const activeQuestion = activeItem?.question ?? null;
  const activeHints = activeQuestion ? hintsByQuestion[activeQuestion.id] ?? [] : [];
  const activeAnswer = activeQuestion ? answersByQuestion[activeQuestion.id] ?? null : null;
  const completedCount = studyItems.filter((item) => item.completed).length;
  const sessionComplete = studyItems.length > 0 && completedCount === studyItems.length;
  const remainingHints = activeItem ? Math.max(0, activeItem.hint_budget - activeHints.length) : 0;
  const canUseHint = Boolean(activeItem && activeQuestion && sessionId && !activeAnswer && remainingHints > 0);
  const displayScore = materialMastery?.material_score ?? 0;
  const displayTier = materialMastery?.tier_name ?? '초심자';
  const nextTierLine = tierDescriptions[displayTier] ?? '자료 이해도를 계산하는 중입니다.';

  const groupedItems = useMemo(
    () => ({
      easy: studyItems.filter((item) => item.difficulty === 'easy'),
      medium: studyItems.filter((item) => item.difficulty === 'medium'),
      hard: studyItems.filter((item) => item.difficulty === 'hard'),
    }),
    [studyItems],
  );

  useEffect(() => {
    let mounted = true;

    async function loadMaterials() {
      try {
        const response = await getMaterials();
        if (mounted) {
          setMaterials(response.materials);
        }
      } catch {
        if (mounted) {
          setMaterials([]);
        }
      }
    }

    void loadMaterials();

    return () => {
      mounted = false;
    };
  }, []);

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

  const beginStudy = async (materialId: number) => {
    const response = await startMaterialStudy(materialId);
    setMaterial(response.material);
    setSessionId(response.session_id);
    setStudyItems(response.concepts.map((item) => ({ ...item, completed: false })));
    setActiveIndex(0);
    setAnswerText('');
    setAnswersByQuestion({});
    setHintsByQuestion({});
    setMaterialMastery(response.material_mastery);
    setAnswerStartedAt(Date.now());
  };

  const handleUploadAndStart = () =>
    runAction('자료 분석 중', async () => {
      if (!file) {
        throw new Error('PDF 파일을 먼저 선택하세요.');
      }

      const uploaded = await uploadMaterial(file);
      const summary: MaterialSummary = {
        id: uploaded.id,
        title: uploaded.title,
        extracted_text_length: uploaded.extracted_text_length,
        preview: uploaded.preview,
        created_at: uploaded.created_at,
      };
      setMaterials((current) => [summary, ...current.filter((item) => item.id !== summary.id)]);
      await beginStudy(uploaded.id);
    });

  const handleStartExisting = (materialId: number) =>
    runAction('학습 준비 중', async () => {
      await beginStudy(materialId);
    });

  const handleRequestHint = (stuckReason?: string) =>
    runAction(stuckReason ? '막힌 지점 분석 중' : '힌트 생성 중', async () => {
      if (!activeQuestion || !sessionId || !activeItem) {
        throw new Error('먼저 학습할 개념을 준비하세요.');
      }

      const hint = await requestQuestionHint(
        activeQuestion.id,
        sessionId,
        activeHints.length + 1,
        stuckReason,
      );
      setHintsByQuestion((current) => ({
        ...current,
        [activeQuestion.id]: [...(current[activeQuestion.id] ?? []), hint],
      }));
    });

  const handleSubmitAnswer = () =>
    runAction('답변 평가 중', async () => {
      if (!activeQuestion || !activeItem) {
        throw new Error('먼저 질문을 준비하세요.');
      }
      if (!answerText.trim()) {
        throw new Error('답변을 입력하세요.');
      }

      const responseTime = answerStartedAt ? (Date.now() - answerStartedAt) / 1000 : undefined;
      const evaluated = await submitAnswer(activeQuestion.id, answerText, responseTime, sessionId);
      setAnswersByQuestion((current) => ({ ...current, [activeQuestion.id]: evaluated }));
      setStudyItems((current) =>
        current.map((item) =>
          item.question.id === activeQuestion.id
            ? {
                ...item,
                completed: true,
                concept_score: evaluated.concept_score,
                tier_name: evaluated.concept_tier,
              }
            : item,
        ),
      );
      if (
        evaluated.material_score !== null &&
        evaluated.material_tier &&
        evaluated.material_completed_concepts !== null &&
        evaluated.material_total_concepts !== null
      ) {
        setMaterialMastery({
          material_score: evaluated.material_score,
          tier_name: evaluated.material_tier,
          completed_concepts: evaluated.material_completed_concepts,
          total_concepts: evaluated.material_total_concepts,
        });
      }
    });

  const moveNext = () => {
    const nextIndex = studyItems.findIndex((item, index) => index > activeIndex && !item.completed);
    if (nextIndex >= 0) {
      setActiveIndex(nextIndex);
      setAnswerText('');
      setAnswerStartedAt(Date.now());
      return;
    }

    const firstIncomplete = studyItems.findIndex((item) => !item.completed);
    if (firstIncomplete >= 0) {
      setActiveIndex(firstIncomplete);
      setAnswerText('');
      setAnswerStartedAt(Date.now());
    }
  };

  const selectConcept = (questionId: number) => {
    const index = studyItems.findIndex((item) => item.question.id === questionId);
    if (index >= 0) {
      setActiveIndex(index);
      setAnswerText('');
      setAnswerStartedAt(Date.now());
    }
  };

  return (
    <div className="study-room">
      <header className="study-header">
        <div>
          <h1>Study</h1>
          <p className="subtitle">강의자료의 모든 개념을 네 말로 설명하고, 힌트 사용량과 정확도로 티어를 올립니다.</p>
        </div>
        <div className="status-pill">
          {loadingLabel ? <Loader2 size={18} className="spin-icon" /> : <img alt="SYNAPTOR" className="status-brand-mark" src="/synaptor-mark.png" />}
          {loadingLabel || '준비됨'}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="study-shell glass-panel">
        <div className="study-topline">
          <div>
            <span>현재 자료</span>
            <strong>{material?.title ?? '자료를 선택하세요'}</strong>
          </div>
          <div>
            <span>자료 티어</span>
            <strong>{displayTier}</strong>
          </div>
          <div>
            <span>진행</span>
            <strong>{materialProgress(studyItems)}</strong>
          </div>
          <div>
            <span>자료 점수</span>
            <strong>{formatPercent(displayScore)}</strong>
          </div>
        </div>

        {!activeItem && (
          <div className="study-start-grid">
            <section className="study-start-panel">
              <div className="panel-title">
                <FileUp size={20} />
                <h2>PDF 업로드</h2>
              </div>
              <label className="upload-box">
                <input
                  accept="application/pdf"
                  type="file"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
                <span>{file ? file.name : 'PDF 파일 선택'}</span>
              </label>
              <button className="glow-btn full-button" disabled={!file || Boolean(loadingLabel)} onClick={handleUploadAndStart}>
                <FileUp size={18} />
                업로드하고 시작
              </button>
            </section>

            <section className="study-start-panel">
              <div className="panel-title">
                <FileText size={20} />
                <h2>기존 자료</h2>
              </div>
              <div className="material-list">
                {materials.length === 0 && <p className="muted">아직 업로드한 자료가 없습니다.</p>}
                {materials.map((item) => (
                  <button
                    className="material-item"
                    disabled={Boolean(loadingLabel)}
                    key={item.id}
                    onClick={() => handleStartExisting(item.id)}
                    type="button"
                  >
                    <strong>{item.title}</strong>
                    <span>{item.extracted_text_length.toLocaleString()}자</span>
                    <p>{item.preview || '미리보기가 없습니다.'}</p>
                  </button>
                ))}
              </div>
            </section>
          </div>
        )}

        {activeItem && !sessionComplete && (
          <div className="study-workspace">
            <aside className="concept-rail">
              {(['easy', 'medium', 'hard'] as const).map((difficulty) => (
                <div className="concept-group" key={difficulty}>
                  <h2>{difficultyLabels[difficulty]}</h2>
                  {groupedItems[difficulty].length === 0 && <p className="muted">개념 없음</p>}
                  {groupedItems[difficulty].map((item) => (
                    <button
                      className={`concept-rank-item ${item.question.id === activeQuestion?.id ? 'active' : ''} ${item.completed ? 'done' : ''}`}
                      key={item.question.id}
                      onClick={() => selectConcept(item.question.id)}
                      type="button"
                    >
                      <span>{item.concept.title}</span>
                      <strong>{item.tier_name}</strong>
                    </button>
                  ))}
                </div>
              ))}
            </aside>

            <div className="recall-flow">
              <section className="question-card">
                <div className="question-meta-row">
                  <span>{difficultyLabels[activeItem.difficulty] ?? activeItem.difficulty}</span>
                  <span>힌트 {remainingHints} / {activeItem.hint_budget}</span>
                  <span>{activeItem.tier_name}</span>
                </div>
                <h2>{activeItem.concept.title}</h2>
                <p>{activeQuestion?.question_text}</p>
              </section>

              <section className="answer-block">
                <textarea
                  className="answer-input"
                  disabled={Boolean(activeAnswer)}
                  placeholder="자료를 보지 않고, 이 개념을 네 말로 설명해보세요."
                  value={answerText}
                  onChange={(event) => setAnswerText(event.target.value)}
                />
                <div className="action-row">
                  <button
                    className="secondary-btn"
                    disabled={!canUseHint || Boolean(loadingLabel)}
                    onClick={() => handleRequestHint()}
                    type="button"
                  >
                    <HelpCircle size={18} />
                    Hint
                  </button>
                  <button
                    className="glow-btn"
                    disabled={!answerText.trim() || Boolean(activeAnswer) || Boolean(loadingLabel)}
                    onClick={handleSubmitAnswer}
                    type="button"
                  >
                    <Send size={18} />
                    설명 제출
                  </button>
                </div>
              </section>

              {!activeAnswer && (
                <section className="stuck-panel">
                  <div className="panel-title">
                    <MessageSquareText size={19} />
                    <h2>막혔나요?</h2>
                  </div>
                  <div className="stuck-grid">
                    {stuckOptions.map((option) => (
                      <button
                        className="stuck-option"
                        disabled={!canUseHint || Boolean(loadingLabel)}
                        key={option.reason}
                        onClick={() => handleRequestHint(option.reason)}
                        type="button"
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </section>
              )}

              {activeHints.length > 0 && (
                <section className="support-list">
                  {activeHints.map((hint) => (
                    <article className="support-card" key={hint.id}>
                      <span>힌트 {hint.hint_level}</span>
                      <p>{hint.hint_text}</p>
                    </article>
                  ))}
                </section>
              )}

              {activeAnswer && (
                <section className="feedback-panel">
                  <div className="feedback-summary">
                    <div>
                      <span>답변 정확도</span>
                      <strong>{Math.round(activeAnswer.correctness_score * 100)}%</strong>
                    </div>
                    <div>
                      <span>힌트 사용</span>
                      <strong>{activeAnswer.hints_used} / {activeAnswer.hint_budget}</strong>
                    </div>
                    <div>
                      <span>개념 점수</span>
                      <strong>{formatPercent(activeAnswer.concept_score)}</strong>
                    </div>
                    <div>
                      <span>개념 티어</span>
                      <strong>{activeAnswer.concept_tier}</strong>
                    </div>
                  </div>
                  <div className="short-feedback">
                    <CheckCircle2 size={20} />
                    <p>{activeAnswer.feedback}</p>
                  </div>
                  {activeAnswer.missing_points && (
                    <p className="missing-point">보완할 지점: {activeAnswer.missing_points}</p>
                  )}
                  <div className="action-row">
                    <button className="glow-btn" onClick={moveNext} type="button">
                      <ArrowRight size={18} />
                      다음 개념
                    </button>
                  </div>
                </section>
              )}
            </div>
          </div>
        )}

        {sessionComplete && (
          <section className="session-result">
            <Sparkles size={44} />
            <h2>{material?.title} 이해도 결과</h2>
            <p>{nextTierLine}</p>
            <div className="result-metrics">
              <div>
                <span>자료 티어</span>
                <strong>{displayTier}</strong>
              </div>
              <div>
                <span>자료 점수</span>
                <strong>{formatPercent(displayScore)}</strong>
              </div>
              <div>
                <span>완료 개념</span>
                <strong>{completedCount}</strong>
              </div>
              <div>
                <span>평균 힌트</span>
                <strong>
                  {(
                    studyItems.reduce((sum, item) => sum + (hintsByQuestion[item.question.id]?.length ?? 0), 0) /
                    Math.max(studyItems.length, 1)
                  ).toFixed(1)}
                </strong>
              </div>
            </div>
            <div className="concept-result-list">
              {studyItems.map((item) => (
                <div className="concept-result-item" key={item.question.id}>
                  <span>{item.concept.title}</span>
                  <strong>{item.tier_name}</strong>
                  <em>{formatPercent(item.concept_score)}</em>
                </div>
              ))}
            </div>
          </section>
        )}
      </section>
    </div>
  );
};
