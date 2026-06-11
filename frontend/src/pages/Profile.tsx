import { useEffect, useState } from 'react';
import { AlertTriangle, Gauge, HelpCircle, Lightbulb, ShieldAlert, Sparkles } from 'lucide-react';
import { getLearningProfile } from '../api/client';
import type { LearningProfileResponse } from '../types/api';
import './Profile.css';

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

const metricCopy = [
  {
    key: 'recall',
    title: 'Recall Strength',
    description: '도움 없이 기억에서 개념을 꺼내는 힘입니다.',
    icon: Sparkles,
    value: (profile: LearningProfileResponse) => profile.average_recall_score,
  },
  {
    key: 'explanation',
    title: 'Explanation Quality',
    description: '개념을 자신의 말로 분명하게 설명하는 정도입니다.',
    icon: Lightbulb,
    value: (profile: LearningProfileResponse) => profile.explanation_quality,
  },
  {
    key: 'hint',
    title: 'Hint Dependency',
    description: '답하기 전에 힌트가 얼마나 자주 필요한지 보여줍니다.',
    icon: HelpCircle,
    value: (profile: LearningProfileResponse) => profile.hint_dependency,
    inverted: true,
  },
  {
    key: 'misconception',
    title: 'Misconception Risk',
    description: '답변에서 반복적인 오해가 나타나는 빈도입니다.',
    icon: ShieldAlert,
    value: (profile: LearningProfileResponse) => profile.misconception_frequency,
    inverted: true,
  },
];

function statusLabel(value: number, inverted = false) {
  const score = inverted ? 1 - value : value;
  if (score >= 0.75) {
    return '좋음';
  }
  if (score >= 0.45) {
    return '연습 중';
  }
  return '주의 필요';
}

export function Profile() {
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
          setError(caught instanceof Error ? caught.message : '프로필을 불러오지 못했습니다.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="profile-page">
      <header className="profile-header">
        <div>
          <h1>Profile</h1>
          <p className="subtitle">답변, 힌트 사용, 자기 설명을 바탕으로 개인화 학습 상태를 요약합니다.</p>
        </div>
        <div className="profile-pill">
          <Gauge size={18} />
          {loading ? '계산 중' : '자동 업데이트'}
        </div>
      </header>

      {error && (
        <div className="profile-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="profile-grid">
        {metricCopy.map((metric) => {
          const Icon = metric.icon;
          const value = profile ? metric.value(profile) : 0;

          return (
            <article className="profile-metric glass-panel" key={metric.key}>
              <div className="metric-heading">
                <Icon size={22} />
                <h2>{metric.title}</h2>
              </div>
              <strong>{loading ? '--' : formatPercent(value)}</strong>
              <p>{metric.description}</p>
              <span>{loading ? '데이터 확인 중' : statusLabel(value, metric.inverted)}</span>
            </article>
          );
        })}
      </section>

      <section className="profile-note glass-panel">
        <h2>개인화 기준</h2>
        <p>
          SYNAPTOR는 정답률만 보지 않고 힌트 없이 떠올렸는지, 자기 말로 설명했는지,
          반복되는 오개념이 있는지를 함께 반영합니다.
        </p>
      </section>
    </div>
  );
}
