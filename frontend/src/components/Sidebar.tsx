import { NavLink } from 'react-router-dom';
import { BrainCircuit, BookOpen, CalendarClock, LogOut, MessageSquareText, User } from 'lucide-react';
import { useAuth } from '../auth/useAuth';
import './Sidebar.css';

export const Sidebar = () => {
  const { logout, user } = useAuth();

  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <BrainCircuit className="logo-icon text-gradient" size={32} />
        <h2 className="text-gradient">Brain-Sync</h2>
      </div>
      <nav className="sidebar-nav">
        <NavLink to="/" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <BrainCircuit size={20} />
          <span>학습 대시보드</span>
        </NavLink>
        <NavLink to="/study" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <BookOpen size={20} />
          <span>학습실</span>
        </NavLink>
        <NavLink to="/chat" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <MessageSquareText size={20} />
          <span>튜터 채팅</span>
        </NavLink>
        <NavLink to="/review" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <CalendarClock size={20} />
          <span>오늘 복습</span>
        </NavLink>
        <NavLink to="/profile" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <User size={20} />
          <span>프로필</span>
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        {user && (
          <div className="sidebar-user">
            <span>{user.display_name}</span>
            <small>{user.email}</small>
          </div>
        )}
        <button className="nav-item" onClick={logout}>
          <LogOut size={20} />
          <span>로그아웃</span>
        </button>
      </div>
    </aside>
  );
};
