import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { BrainCircuit } from 'lucide-react';
import { useAuth } from './useAuth';

export function ProtectedRoute() {
  const location = useLocation();
  const { initializing, isAuthenticated } = useAuth();

  if (initializing) {
    return (
      <div className="auth-loading-screen">
        <BrainCircuit size={32} className="text-gradient" />
        <span>학습 세션을 확인하는 중...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
