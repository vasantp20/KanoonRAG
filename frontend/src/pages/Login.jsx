import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../api/authService';
import './Login.css';
import logo from '../assets/logo.png';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    setErrorMsg('');
    try {
      // Attempt actual API login
      await authService.login(email, password);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      setErrorMsg(error.message || 'Invalid credentials. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page-wrapper">
      {/* Left Side: Visual & Brand Content */}
      <section className="login-brand-section">
        <div className="texture-overlay"></div>
        <div className="glow-orb-top"></div>
        <div className="glow-orb-bottom"></div>
        
        <div className="brand-content">
          <div className="brand-logo-container">
            <img 
              alt="KanoonRAG Logo" 
              className="brand-logo" 
              src={logo}
            />
          </div>
          
          <h1 className="brand-title">KanoonRAG</h1>
          <p className="brand-subtitle">Legal Intelligence System</p>
          
          <h2 className="brand-heading">
            Precision AI for <span>Supreme Court</span> Precedents.
          </h2>
          <p className="brand-description">
            Empowering the legal elite with high-performance computational jurisprudence and unwavering precision in case research.
          </p>
          
          <div className="trusted-by">
            <div className="avatar-stack">
              <div className="avatar" style={{ backgroundImage: "url('/assets/avatar1.png')" }}></div>
              <div className="avatar" style={{ backgroundImage: "url('/assets/avatar2.png')" }}></div>
              <div className="avatar" style={{ backgroundImage: "url('/assets/avatar3.png')" }}></div>
            </div>
            <p className="trusted-label">Trusted by 500+ Top Tier Law Firms</p>
          </div>
        </div>

        <div className="brand-footer">
          <span>© 2024 KANOONRAG</span>
        </div>
      </section>

      {/* Right Side: Login Form */}
      <section className="login-form-section">
        <div className="login-form-container">
          
          <div className="mobile-logo-section">
            <img 
              alt="KanoonRAG Logo" 
              src={logo}
            />
            <h1>KanoonRAG</h1>
          </div>

          <div className="login-greeting">
            <h3>Welcome Back</h3>
            <p>Sign in to your legal intelligence workspace.</p>
          </div>

          {errorMsg && (
            <div className="bg-error-container text-on-error-container p-3 rounded-lg text-sm mb-4 border border-error/50">
              {errorMsg}
            </div>
          )}

          <form className="refined-form" onSubmit={handleLogin}>
            <div className="form-group">
              <label className="input-label" style={{marginLeft: '4px'}} htmlFor="email">WORK EMAIL</label>
              <div className="input-wrapper">
                <span className="material-symbols-outlined input-icon">mail</span>
                <input
                  type="email"
                  id="email"
                  className="refined-input"
                  placeholder="attorney@firm.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px', marginLeft: '4px' }}>
                <label className="input-label" style={{margin: 0}} htmlFor="password">PASSWORD</label>
                <a href="#" className="forgot-password" style={{fontSize: '11px', letterSpacing: '0.05em'}}>Forgot Password?</a>
              </div>
              <div className="input-wrapper">
                <span className="material-symbols-outlined input-icon">lock</span>
                <input
                  type="password"
                  id="password"
                  className="refined-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="remember-me">
              <input type="checkbox" id="remember" />
              <label htmlFor="remember">Remember this session for 30 days</label>
            </div>

            <button type="submit" className="refined-submit" disabled={isLoading}>
              {isLoading ? 'Authenticating...' : 'Sign In'}
              {!isLoading && <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>arrow_forward</span>}
            </button>
          </form>

          <div className="login-bottom-nav">
            Don't have an enterprise account? 
            <Link to="/signup" style={{ marginLeft: '4px', color: '#c4a265', textDecoration: 'none' }}>Sign Up</Link>
          </div>
          
        </div>
      </section>
    </div>
  );
};

export default Login;
