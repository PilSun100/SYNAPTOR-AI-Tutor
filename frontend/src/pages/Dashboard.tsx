import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  BrainCircuit,
  Gauge,
  Lightbulb,
  PlayCircle,
  RefreshCcw,
  ShieldAlert,
  Target,
} from 'lucide-react';
import { getLearningProfile } from '../api/client';
import { useAuth } from '../auth/useAuth';
import type { LearningProfileResponse } from '../types/api';
import './Dashboard.css';

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

const methodLabels: Record<string, string> = {
  active_recall: 'Active Recall',
  feynman_check: 'Feynman Check',
  misconception_repair: 'Misconception Repair',
  example_first: 'Example First',
  hint_ladder: 'Hint Ladder',
  spaced_review: 'Spaced Review',
  mixed_practice: 'Mixed Practice',
};

export const Dashboard = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<LearningProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function loadProfile() {
      setLoading(true);
      setError('');
      try {
        const response = await getLearningProfile();
        if (mounted) {
          setProfile(response);
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : '학습 프로필을 불러오지 못했습니다.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadProfile();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Welcome back, <span className="text-gradient">{user?.display_name ?? 'Learner'}</span></h1>
          <p className="subtitle">Brain-Sync가 오늘 필요한 학습 방식을 사용자 기록에서 계산합니다.</p>
        </div>
        <Link className="glow-btn dashboard-start-link" to="/study">
          <PlayCircle size={20} />
          Start Session
        </Link>
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
            <p>{loading ? '학습 프로필을 분석하는 중입니다.' : profile?.recommendation_reason}</p>
          </div>
        </div>
        <div className="method-card">
          <span>추천 학습법</span>
          <strong>{profile ? methodLabels[profile.best_intervention_type] ?? profile.best_intervention_type : '...'}</strong>
          <p>{profile?.next_action ?? '자료를 업로드하고 첫 회상 질문에 답하면 개인화 추천이 시작됩니다.'}</p>
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
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: 'var(--primary)' }}>
            <Lightbulb size={24} />
          </div>
          <div className="stat-info">
            <h3>Self Explanation</h3>
            <p className="glow-text">{profile ? formatPercent(profile.explanation_quality) : '--'}</p>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: 'var(--secondary)' }}>
            <Gauge size={24} />
          </div>
          <div className="stat-info">
            <h3>Hint Dependency</h3>
            <p className="glow-text">{profile ? formatPercent(profile.hint_dependency) : '--'}</p>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: '#f59e0b' }}>
            <ShieldAlert size={24} />
          </div>
          <div className="stat-info">
            <h3>Frustration Risk</h3>
            <p className="glow-text">{profile ? formatPercent(profile.frustration_risk) : '--'}</p>
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
              <span>답변 수</span>
              <strong>{profile?.total_answers ?? 0}</strong>
            </div>
            <div>
              <span>자기 설명</span>
              <strong>{profile?.total_self_explanations ?? 0}</strong>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
