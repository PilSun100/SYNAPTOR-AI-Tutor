import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  BrainCircuit,
  CalendarClock,
  Gauge,
  Lightbulb,
  PlayCircle,
  RefreshCcw,
  ShieldAlert,
  Target,
} from 'lucide-react';
import { getDashboardSummary } from '../api/client';
import { useAuth } from '../auth/useAuth';
import type { DashboardSummaryResponse } from '../types/api';
import './Dashboard.css';

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

const formatDate = (value: string | null) => {
  if (!value) {
    return '일정 없음';
  }
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
};

const methodLabels: Record<string, string> = {
  active_recall: 'Active Recall',
  feynman_check: 'Feynman Check',
  misconception_repair: 'Misconception Repair',
  example_first: 'Example First',
  hint_ladder: 'Hint Ladder',
  spaced_review: 'Spaced Review',
  mixed_practice: 'Mixed Practice',
  definition: 'Definition Recall',
};

export const Dashboard = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      setLoading(true);
      setError('');
      try {
        const response = await getDashboardSummary();
        if (mounted) {
          setSummary(response);
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : '대시보드를 불러오지 못했습니다.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  const profile = summary?.profile;
  const memory = summary?.memory_summary;
  const topReview = summary?.daily_review.review_items[0];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Welcome back, <span className="text-gradient">{user?.display_name ?? 'Learner'}</span></h1>
          <p className="subtitle">Brain-Sync가 회상 점수, 오개념, 망각 위험을 합쳐 오늘의 학습 경로를 계산합니다.</p>
        </div>
        <div className="dashboard-actions">
          <Link className="ghost-link" to="/review">
            <CalendarClock size={18} />
            Daily Review
          </Link>
          <Link className="glow-btn dashboard-start-link" to="/study">
            <PlayCircle size={20} />
            Start Session
          </Link>
        </div>
      </header>

      {error && (
        <div className="dashboard-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="today-sync glass-panel">
        <div className="section-heading">
          <BrainCircuit size={22} />
          <div>
            <h2>Today’s Brain-Sync</h2>
            <p>{loading ? '개인화 학습 경로를 계산하는 중입니다.' : profile?.recommendation_reason}</p>
          </div>
        </div>
        <div className="today-cards">
          <div className="method-card">
            <span>추천 학습법</span>
            <strong>{profile ? methodLabels[profile.best_intervention_type] ?? profile.best_intervention_type : '...'}</strong>
            <p>{profile?.next_action ?? '자료를 업로드하고 첫 회상 질문에 답하면 개인화 추천이 시작됩니다.'}</p>
          </div>
          <div className="method-card review-focus-card">
            <span>오늘 최우선 복습</span>
            <strong>{topReview?.concept_title ?? '복습 대기 없음'}</strong>
            <p>{topReview?.reason ?? '새 학습 이벤트가 생기면 망각 위험 기반 복습 큐가 생성됩니다.'}</p>
          </div>
        </div>
      </section>

      <section className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: 'var(--accent)' }}>
            <Target size={24} />
          </div>
          <div className="stat-info">
            <h3>Recall Score</h3>
            <p className="glow-text">{profile ? formatPercent(profile.average_recall_score) : '--'}</p>
            <span>답변 기반 회상 정확도</span>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: 'var(--primary)' }}>
            <Lightbulb size={24} />
          </div>
          <div className="stat-info">
            <h3>Self Explanation</h3>
            <p className="glow-text">{profile ? formatPercent(profile.explanation_quality) : '--'}</p>
            <span>자기 설명 품질</span>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: 'var(--secondary)' }}>
            <Gauge size={24} />
          </div>
          <div className="stat-info">
            <h3>Memory Strength</h3>
            <p className="glow-text">{memory ? formatPercent(memory.average_mastery) : '--'}</p>
            <span>{memory?.total_concepts ?? 0}개 개념 추적 중</span>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: '#f59e0b' }}>
            <ShieldAlert size={24} />
          </div>
          <div className="stat-info">
            <h3>High Risk</h3>
            <p className="glow-text">{memory?.high_priority_count ?? '--'}</p>
            <span>오늘 우선순위 높음</span>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="glass-panel dashboard-panel">
          <div className="section-heading compact">
            <RefreshCcw size={20} />
            <div>
              <h2>Weak Concepts</h2>
              <p>숙련도, 힌트 의존도, 오개념 기록을 함께 봅니다.</p>
            </div>
          </div>
          <div className="weak-list">
            {profile?.weak_concepts.length === 0 && (
              <div className="empty-state">
                <BrainCircuit size={40} className="text-gradient" style={{ opacity: 0.5 }} />
                <p>아직 취약 개념 데이터가 없습니다. Study Room에서 첫 세션을 시작하세요.</p>
              </div>
            )}
            {profile?.weak_concepts.map((concept) => (
              <div className="weak-item" key={concept.concept_id}>
                <div>
                  <strong>{concept.title}</strong>
                  <p>{concept.reason}</p>
                </div>
                <span>{formatPercent(concept.mastery_level)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel dashboard-panel profile-panel">
          <div className="section-heading compact">
            <Gauge size={20} />
            <div>
              <h2>Your Learning Profile</h2>
              <p>개인화 엔진이 다음 난이도와 학습 방식을 고릅니다.</p>
            </div>
          </div>
          <div className="profile-facts">
            <div>
              <span>권장 난이도</span>
              <strong>{profile?.preferred_difficulty_level ?? '--'}</strong>
            </div>
            <div>
              <span>오개념 빈도</span>
              <strong>{profile ? formatPercent(profile.misconception_frequency) : '--'}</strong>
            </div>
            <div>
              <span>힌트 의존도</span>
              <strong>{profile ? formatPercent(profile.hint_dependency) : '--'}</strong>
            </div>
            <div>
              <span>답변 수</span>
              <strong>{profile?.total_answers ?? 0}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="dashboard-grid lower-grid">
        <div className="glass-panel dashboard-panel">
          <div className="section-heading compact">
            <ShieldAlert size={20} />
            <div>
              <h2>Misconception Notes</h2>
              <p>정답처럼 보이지만 근거와 어긋난 개념을 우선 교정합니다.</p>
            </div>
          </div>
          <div className="note-list">
            {summary?.misconception_notes.length === 0 && <p className="soft-empty">반복 오개념 기록이 아직 없습니다.</p>}
            {summary?.misconception_notes.map((note) => (
              <div className="note-item" key={note.concept_id}>
                <strong>{note.concept_title}</strong>
                <p>{note.reason}</p>
                <span>오개념 {note.misconception_count}회 · 힌트 {formatPercent(note.hint_dependency)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel dashboard-panel">
          <div className="section-heading compact">
            <CalendarClock size={20} />
            <div>
              <h2>Review Schedule</h2>
              <p>망각 위험과 다음 복습 시점을 기준으로 정렬됩니다.</p>
            </div>
          </div>
          <div className="schedule-list">
            {summary?.review_schedule.length === 0 && <p className="soft-empty">예정된 복습 일정이 없습니다.</p>}
            {summary?.review_schedule.map((item) => (
              <div className="schedule-item" key={`${item.concept_id}-${item.priority}`}>
                <div>
                  <strong>{item.concept_title}</strong>
                  <p>{item.reason}</p>
                </div>
                <span>{formatDate(item.next_review_at)}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="glass-panel dashboard-panel">
        <div className="section-heading compact">
          <Target size={20} />
          <div>
            <h2>Recent Sessions</h2>
            <p>최근 세션의 답변 품질과 오개념 발생을 추적합니다.</p>
          </div>
        </div>
        <div className="session-list">
          {summary?.recent_sessions.length === 0 && <p className="soft-empty">아직 학습 세션이 없습니다.</p>}
          {summary?.recent_sessions.map((session) => (
            <div className="session-item" key={session.session_id}>
              <div>
                <strong>{session.material_title}</strong>
                <p>{formatDate(session.started_at)} · 답변 {session.total_answers}개</p>
              </div>
              <div>
                <span>평균 {formatPercent(session.average_score)}</span>
                <span>오개념 {session.misconception_count}회</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
