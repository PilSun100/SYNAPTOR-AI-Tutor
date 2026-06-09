import { Link } from 'react-router-dom';
import { PlayCircle, Activity, Award, BrainCircuit } from 'lucide-react';
import { useAuth } from '../auth/useAuth';
import './Dashboard.css';

export const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Welcome back, <span className="text-gradient">{user?.display_name ?? 'Learner'}</span></h1>
          <p className="subtitle">오늘의 자료 기반 회상 훈련을 시작하세요.</p>
        </div>
        <Link className="glow-btn dashboard-start-link" to="/study">
          <PlayCircle size={20} />
          Start Session
        </Link>
      </header>

      <section className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: 'var(--primary)' }}>
            <Activity size={24} />
          </div>
          <div className="stat-info">
            <h3>Synapse Count</h3>
            <p className="glow-text">14,230</p>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ color: 'var(--secondary)' }}>
            <Award size={24} />
          </div>
          <div className="stat-info">
            <h3>Active Streak</h3>
            <p className="glow-text">12 Days</p>
          </div>
        </div>
      </section>

      <section className="content-area glass-panel">
        <h2>Recent Neural Pathways</h2>
        <div className="empty-state">
          <BrainCircuit size={48} className="text-gradient mb-3" style={{ opacity: 0.5 }} />
          <p>No active sessions found. Start a session to build pathways.</p>
        </div>
      </section>
    </div>
  );
};
