import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { MainLayout } from './layouts/MainLayout';
import { AuthPage } from './pages/AuthPage';
import { DailyReview } from './pages/DailyReview';
import { Dashboard } from './pages/Dashboard';
import { StudyRoom } from './pages/StudyRoom';
import { TutorChat } from './pages/TutorChat';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/auth" element={<AuthPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="study" element={<StudyRoom />} />
              <Route path="chat" element={<TutorChat />} />
              <Route path="review" element={<DailyReview />} />
              <Route path="profile" element={<div style={{padding: 32}}><h2>Profile</h2><p className="subtitle">Coming soon...</p></div>} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
