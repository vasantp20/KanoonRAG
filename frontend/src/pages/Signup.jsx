import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../api/authService';
import logo from '../assets/logo.png';
import './Signup.css';

const Signup = () => {
  const [fullName, setFullName] = useState('');
  const [org, setOrg] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match.');
      return;
    }
    
    setIsLoading(true);
    setErrorMsg('');
    try {
      await authService.register(fullName, org, email, password);
      navigate('/dashboard');
    } catch (error) {
      console.error('Signup failed:', error);
      setErrorMsg(error.message || 'Failed to create account. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="signup-page-wrapper dark flex min-h-screen items-center justify-center p-4 lg:p-0">
      {/* Background Atmospheric Effect */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-primary/5 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/5 rounded-full blur-[120px]"></div>
        <div className="absolute inset-0 glass-overlay"></div>
      </div>
      
      {/* Main Container */}
      <main className="relative z-10 w-full max-w-[1200px] grid grid-cols-1 lg:grid-cols-2 overflow-hidden rounded-xl obsidian-card shadow-2xl signup-container">
        {/* Left Side: Visual/Branding (Hidden on mobile) */}
        <section className="hidden lg:flex flex-col justify-between p-16 relative overflow-hidden bg-surface-dim border-r border-outline-variant">
          <div className="absolute inset-0 opacity-20">
            <div 
              className="w-full h-full bg-cover bg-center grayscale contrast-125 brightness-50" 
              style={{backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuADt4oRPqOYlxmZe48LgSZe53iKpv4GbvEfmULfieVS0J5bZmRPZNX6fpm_YjNRywVpzEYaS5TSEuXdEiMDt09PgNQDP_S2-KlCZAIsHXmOHadgQlnqw4LbJwUkQUAzMDUraqZziqqNKY0Z9lwoI_VimDyvBrsgoTean-S7dveDUzlH38bj_stiBv3Tm375mbqop75xr75DUi-4jpC1kK2hIWUODHFNwtGMTUPpH3_ktPo20ug1jiBV')"}}>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-surface-dim via-transparent to-transparent"></div>
          </div>
          <div className="relative z-20">
            <div className="flex items-center gap-3 mb-8">
              <img src={logo} alt="KanoonRAG Logo" className="h-12 w-auto object-contain" />
            </div>
            <h2 className="text-4xl font-bold leading-tight text-on-surface mb-6 font-display-lg">
              Elevate your <br /> <span className="gold-gradient-text">legal intelligence</span>.
            </h2>
            <p className="text-on-surface-variant text-lg max-w-md leading-relaxed font-body-lg">
              Join the elite network of legal professionals leveraging AI-driven research to achieve unprecedented accuracy and speed in case analysis.
            </p>
          </div>
          <div className="relative z-20 flex flex-col gap-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                <span className="material-symbols-outlined text-primary text-xl">verified</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-on-surface font-label-md">Precision RAG Architecture</p>
                <p className="text-xs text-on-surface-variant font-body-md">Validated legal citations with 99.9% accuracy.</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                <span className="material-symbols-outlined text-primary text-xl">shield_person</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-on-surface font-label-md">Secure &amp; Confidential</p>
                <p className="text-xs text-on-surface-variant font-body-md">Military-grade encryption for all case documents.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Right Side: Signup Form */}
        <section className="p-8 lg:p-16 flex flex-col justify-center bg-surface">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <img src={logo} alt="KanoonRAG Logo" className="h-10 w-auto object-contain" />
          </div>
          <div className="mb-10">
            <h3 className="text-2xl font-bold text-on-surface mb-2 font-headline-lg">Create Account</h3>
            <p className="text-on-surface-variant text-sm font-body-md">Join the next generation of legal research.</p>
          </div>

          {errorMsg && (
            <div className="bg-error-container text-on-error-container p-3 rounded-lg text-sm mb-4 border border-error/50">
              {errorMsg}
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSignup}>
            {/* Full Name */}
            <div className="space-y-2">
              <label className="block text-xs font-bold tracking-widest uppercase text-on-surface-variant ml-1 font-label-sm" htmlFor="full_name">Full Name</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">person</span>
                <input 
                  className="w-full bg-surface-dim border border-outline-variant rounded-lg py-3.5 pl-12 pr-4 text-on-surface placeholder:text-outline text-sm input-gold-focus transition-all" 
                  id="full_name" 
                  name="full_name" 
                  placeholder="E.g. Justice Oliver" 
                  type="text" 
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>
            </div>
            {/* Firm/Organization */}
            <div className="space-y-2">
              <label className="block text-xs font-bold tracking-widest uppercase text-on-surface-variant ml-1 font-label-sm" htmlFor="org">Law Firm / Organization</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">account_balance</span>
                <input 
                  className="w-full bg-surface-dim border border-outline-variant rounded-lg py-3.5 pl-12 pr-4 text-on-surface placeholder:text-outline text-sm input-gold-focus transition-all" 
                  id="org" 
                  name="org" 
                  placeholder="Firm name" 
                  type="text" 
                  value={org}
                  onChange={(e) => setOrg(e.target.value)}
                />
              </div>
            </div>
            {/* Professional Email */}
            <div className="space-y-2">
              <label className="block text-xs font-bold tracking-widest uppercase text-on-surface-variant ml-1 font-label-sm" htmlFor="email">Professional Email</label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">mail</span>
                <input 
                  className="w-full bg-surface-dim border border-outline-variant rounded-lg py-3.5 pl-12 pr-4 text-on-surface placeholder:text-outline text-sm input-gold-focus transition-all" 
                  id="email" 
                  name="email" 
                  placeholder="name@firm.com" 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
            {/* Password Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="block text-xs font-bold tracking-widest uppercase text-on-surface-variant ml-1 font-label-sm" htmlFor="password">Password</label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">lock</span>
                  <input 
                    className="w-full bg-surface-dim border border-outline-variant rounded-lg py-3.5 pl-12 pr-4 text-on-surface placeholder:text-outline text-sm input-gold-focus transition-all" 
                    id="password" 
                    name="password" 
                    placeholder="••••••••" 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="block text-xs font-bold tracking-widest uppercase text-on-surface-variant ml-1 font-label-sm" htmlFor="confirm_password">Confirm Password</label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">lock</span>
                  <input 
                    className="w-full bg-surface-dim border border-outline-variant rounded-lg py-3.5 pl-12 pr-4 text-on-surface placeholder:text-outline text-sm input-gold-focus transition-all" 
                    id="confirm_password" 
                    name="confirm_password" 
                    placeholder="••••••••" 
                    type="password" 
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>
            {/* CTA Button */}
            <div className="pt-4">
              <button 
                className="w-full bg-primary hover:bg-primary-container text-on-primary font-bold py-4 rounded-lg shadow-lg shadow-primary/20 transition-all active:scale-[0.98] flex items-center justify-center gap-2 group" 
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="animate-spin material-symbols-outlined">sync</span> 
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>Create Account</span>
                    <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
                  </>
                )}
              </button>
            </div>
            {/* Disclaimer */}
            <p className="text-[10px] text-center text-on-surface-variant leading-relaxed px-4">
              By signing up, you agree to our <a className="text-primary hover:underline underline-offset-4" href="#">Terms of Service</a> and <a className="text-primary hover:underline underline-offset-4" href="#">Privacy Policy</a>. All data is processed according to legal compliance standards.
            </p>
          </form>
          {/* Secondary Action */}
          <div className="mt-8 pt-8 border-t border-outline-variant text-center">
            <p className="text-sm text-on-surface-variant">
              Already have an account? <Link className="text-primary font-bold hover:underline underline-offset-4 transition-all ml-1" to="/login">Log In</Link>
            </p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Signup;
