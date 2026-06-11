import { NavLink } from 'react-router-dom';
import { BookOpen, LogOut, MessageSquareText, User } from 'lucide-react';
import { useAuth } from '../auth/useAuth';
import './Sidebar.css';

export const Sidebar = () => {
  const { logout, user } = useAuth();

  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <img alt="SYNAPTOR" className="brand-logo" src="/synaptor-mark.png" />
        <h2>SYNAPTOR</h2>
      </div>
      <nav className="sidebar-nav">
        <NavLink to="/study" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <BookOpen size={20} />
          <span>Study</span>
        </NavLink>
        <NavLink to="/chat" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <MessageSquareText size={20} />
          <span>AI Chat</span>
        </NavLink>
        <NavLink to="/profile" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <User size={20} />
          <span>Profile</span>
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
