import { useState } from 'react';
import type { FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { LockKeyhole, Mail, UserPlus } from 'lucide-react';
import { useAuth } from '../auth/useAuth';
import './AuthPage.css';

type AuthMode = 'login' | 'register';

type LocationState = {
  from?: {
    pathname?: string;
  };
};

export function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { initializing, isAuthenticated, login, register } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const redirectTo = (location.state as LocationState | null)?.from?.pathname ?? '/';

  if (!initializing && isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password, displayName);
      }
      navigate(redirectTo, { replace: true });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '인증 요청을 처리하지 못했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-product-panel">
        <div className="auth-brand">
          <img alt="SYNAPTOR" src="/synaptor-mark.png" />
          <span>SYNAPTOR</span>
        </div>
        <div>
          <h1>개인 자료와 학습 기록을 분리해 추적하는 AI 튜터</h1>
          <p>
            로그인 후 업로드한 PDF, 답변 평가, 힌트 사용량, 복습 시점이 사용자별로 저장됩니다.
            SYNAPTOR는 같은 자료라도 사용자의 이해 상태에 맞춰 질문과 설명 난이도를 조정합니다.
          </p>
        </div>
        <div className="auth-feature-grid">
          <div>
            <strong>자료 소유권</strong>
            <span>업로드 자료와 세션은 로그인 사용자 기준으로만 조회됩니다.</span>
          </div>
          <div>
            <strong>근거 기반 평가</strong>
            <span>답변과 힌트는 PDF chunk evidence를 기준으로 생성됩니다.</span>
          </div>
          <div>
            <strong>개인화 확장</strong>
            <span>프로필, 적응형 난이도, 일일 복습으로 이어지는 기반입니다.</span>
          </div>
        </div>
      </section>

      <section className="auth-form-panel glass-panel">
        <div className="auth-mode-toggle" role="tablist" aria-label="인증 모드">
          <button className={mode === 'login' ? 'active' : ''} type="button" onClick={() => setMode('login')}>
            로그인
          </button>
          <button
            className={mode === 'register' ? 'active' : ''}
            type="button"
            onClick={() => setMode('register')}
          >
            회원가입
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div>
            <h2>{mode === 'login' ? '계정으로 시작하기' : '새 학습 계정 만들기'}</h2>
            <p>{mode === 'login' ? '저장된 학습 세션으로 돌아갑니다.' : '자료와 학습 기록을 안전하게 분리합니다.'}</p>
          </div>

          {mode === 'register' && (
            <label>
              <span>이름</span>
              <div className="auth-input-wrap">
                <UserPlus size={18} />
                <input
                  autoComplete="name"
                  minLength={1}
                  maxLength={100}
                  required
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  placeholder="표시 이름"
                />
              </div>
            </label>
          )}

          <label>
            <span>이메일</span>
            <div className="auth-input-wrap">
              <Mail size={18} />
              <input
                autoComplete="email"
                required
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </div>
          </label>

          <label>
            <span>비밀번호</span>
            <div className="auth-input-wrap">
              <LockKeyhole size={18} />
              <input
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                minLength={mode === 'register' ? 8 : 1}
                maxLength={128}
                required
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === 'register' ? '8자 이상' : '비밀번호'}
              />
            </div>
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button className="glow-btn auth-submit" disabled={submitting || initializing} type="submit">
            {submitting ? '처리 중...' : mode === 'login' ? '로그인' : '회원가입'}
          </button>
        </form>
      </section>
    </main>
  );
}
