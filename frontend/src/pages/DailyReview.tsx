import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, CalendarClock, Clock3, PlayCircle, RotateCcw, Sparkles } from 'lucide-react';
import { getDailyReview } from '../api/client';
import type { DailyReviewResponse } from '../types/api';
import './DailyReview.css';

const methodLabels: Record<string, string> = {
  active_recall: 'Active Recall',
  example_first: 'Example First',
  misconception_repair: 'Misconception Repair',
  mixed_practice: 'Mixed Practice',
  spaced_review: 'Spaced Review',
};

const priorityLabels: Record<string, string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

export function DailyReview() {
  const [review, setReview] = useState<DailyReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function loadReview() {
      setLoading(true);
      setError('');
      try {
        const response = await getDailyReview();
        if (mounted) {
          setReview(response);
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : '오늘의 복습을 불러오지 못했습니다.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadReview();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="daily-review-page">
      <header className="daily-review-header">
        <div>
          <h1>오늘의 복습 큐</h1>
          <p className="subtitle">망각 위험, 오개념, 힌트 의존도를 바탕으로 오늘 복습할 개념을 고릅니다.</p>
        </div>
        <Link className="glow-btn review-start-link" to="/study">
          <PlayCircle size={20} />
          학습실
        </Link>
      </header>

      {error && (
        <div className="review-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="review-summary glass-panel">
        <div>
          <CalendarClock size={24} />
          <span>복습 항목</span>
          <strong>{loading ? '--' : review?.review_items.length ?? 0}</strong>
        </div>
        <div>
          <Clock3 size={24} />
          <span>예상 시간</span>
          <strong>{loading ? '--' : `${review?.estimated_total_minutes ?? 0}분`}</strong>
        </div>
        <div>
          <RotateCcw size={24} />
          <span>추천 기준</span>
          <strong>Spaced + Adaptive</strong>
        </div>
      </section>

      <section className="review-list-section">
        {loading && <div className="glass-panel review-empty">오늘의 복습 일정을 계산하는 중입니다.</div>}
        {!loading && review?.review_items.length === 0 && (
          <div className="glass-panel review-empty">
            <Sparkles size={46} className="text-gradient" style={{ opacity: 0.55 }} />
            <strong>오늘 우선 복습할 취약 개념이 없습니다.</strong>
            <p>새 자료를 학습하거나 학습실에서 능동 회상 질문을 풀면 복습 일정이 생성됩니다.</p>
          </div>
        )}
        {review?.review_items.map((item) => (
          <article className={`glass-panel review-card priority-${item.priority}`} key={item.concept_id}>
            <div className="review-card-main">
              <div className="review-card-heading">
                <span>{priorityLabels[item.priority]}</span>
                <h2>{item.concept_title}</h2>
              </div>
              <p>{item.reason}</p>
              <div className="review-method">
                <span>추천 학습법</span>
                <strong>{methodLabels[item.recommended_method] ?? item.recommended_method}</strong>
              </div>
            </div>
            <div className="review-card-metrics">
              <div>
                <span>숙련도</span>
                <strong>{formatPercent(item.mastery_level)}</strong>
              </div>
              <div>
                <span>망각 위험</span>
                <strong>{formatPercent(item.forgetting_risk)}</strong>
              </div>
              <div>
                <span>시간</span>
                <strong>{item.estimated_minutes}분</strong>
              </div>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
