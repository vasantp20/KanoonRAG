import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import './DashboardLayout.css';
import logo from '../../assets/logo.png';
import { authService } from '../../api/authService';

const withDashboardLayout = (WrappedComponent) => {
  return function DashboardLayout(props) {
    const navigate = useNavigate();

    const handleLogout = () => {
      authService.logout();
      navigate('/login');
    };

    return (
      <div className="dashboard-layout">
        {/* Left Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <img src={logo} alt="KanoonRAG Logo" />
            <h2>KanoonRAG</h2>
          </div>
          
          <nav className="sidebar-nav">
            <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <span className="material-symbols-outlined">dashboard</span>
              Dashboard
            </NavLink>
            <NavLink to="/cases" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <span className="material-symbols-outlined">gavel</span>
              Cases
            </NavLink>
            <NavLink to="/clients" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <span className="material-symbols-outlined">groups</span>
              Clients
            </NavLink>
            <NavLink to="/documents" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <span className="material-symbols-outlined">description</span>
              Documents
            </NavLink>
            <NavLink to="/search" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <span className="material-symbols-outlined">search</span>
              Global Search
            </NavLink>
          </nav>

          <div className="sidebar-footer">
            <div className="user-profile">
              <div className="user-avatar">AD</div>
              <div className="user-info">
                <span className="user-name">Attorney Doe</span>
                <span className="user-role">Senior Partner</span>
              </div>
              <button 
                onClick={handleLogout}
                style={{ background: 'transparent', border: 'none', color: 'var(--color-outline)', cursor: 'pointer', marginLeft: 'auto' }}
                title="Logout"
              >
                <span className="material-symbols-outlined">logout</span>
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          <div className="main-glow"></div>
          <div style={{ position: 'relative', zIndex: 1, padding: 'var(--space-lg)' }}>
            <WrappedComponent {...props} />
          </div>
        </main>
      </div>
    );
  };
};

export default withDashboardLayout;
