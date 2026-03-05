import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  MdEmail, MdLock, MdVisibility, MdVisibilityOff,
  MdShield, MdBolt
} from 'react-icons/md';
import axiosInstance from '../api/axiosInstance';
import AuthFooter from '../components/AuthFooter';

const SentinelLogo = () => (
  <svg width="28" height="28" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
    <path clipRule="evenodd" d="M39.475 21.6262C40.358 21.4363 40.6863 21.5589 40.7581 21.5934C40.7876 21.655 40.8547 21.857 40.8082 22.3336C40.7408 23.0255 40.4502 24.0046 39.8572 25.2301C38.6799 27.6631 36.5085 30.6631 33.5858 33.5858C30.6631 36.5085 27.6632 38.6799 25.2301 39.8572C24.0046 40.4502 23.0255 40.7407 22.3336 40.8082C21.8571 40.8547 21.6551 40.7875 21.5934 40.7581C21.5589 40.6863 21.4363 40.358 21.6262 39.475C21.8562 38.4054 22.4689 36.9657 23.5038 35.2817C24.7575 33.2417 26.5497 30.9744 28.7621 28.762C30.9744 26.5497 33.2417 24.7574 35.2817 23.5037C36.9657 22.4689 38.4054 21.8562 39.475 21.6262ZM4.41189 29.2403L18.7597 43.5881C19.8813 44.7097 21.4027 44.9179 22.7217 44.7893C24.0585 44.659 25.5148 44.1631 26.9723 43.4579C29.9052 42.0387 33.2618 39.5667 36.4142 36.4142C39.5667 33.2618 42.0387 29.9052 43.4579 26.9723C44.1631 25.5148 44.659 24.0585 44.7893 22.7217C44.9179 21.4027 44.7097 19.8813 43.5881 18.7597L29.2403 4.41187C27.8527 3.02428 25.8765 3.02573 24.2861 3.36776C22.6081 3.72863 20.7334 4.58419 18.8396 5.74801C16.4978 7.18716 13.9881 9.18353 11.5858 11.5858C9.18354 13.988 7.18717 16.4978 5.74802 18.8396C4.58421 20.7334 3.72865 22.6081 3.36778 24.2861C3.02574 25.8765 3.02429 27.8527 4.41189 29.2403Z" fill="currentColor" fillRule="evenodd" />
  </svg>
);

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('username', formData.email);
      params.append('password', formData.password);
      const res = await axiosInstance.post('/auth/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      localStorage.setItem('access_token', res.data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ fontFamily: 'Manrope, sans-serif', backgroundColor: '#f5f5f8' }}>

      {/* ── LEFT PANEL ── */}
      <div
        className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden"
        style={{ backgroundColor: '#0000ff' }}
      >
        {/* Radial glow */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 50%, rgba(74,134,232,0.4) 0%, transparent 70%)' }} />
        {/* Blur circle */}
        <div className="absolute -bottom-24 -right-24 w-96 h-96 rounded-full opacity-40 pointer-events-none" style={{ backgroundColor: '#1414ff', filter: 'blur(80px)' }} />

        <div className="relative z-10">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="bg-white p-2 rounded-lg text-blue-700 flex items-center justify-center">
              <SentinelLogo />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">Sentinel Bank</span>
          </div>

          <h1 className="text-4xl xl:text-5xl font-extrabold leading-tight text-white mb-5">
            Experience next-generation digital banking.
          </h1>
          <p className="text-lg leading-relaxed" style={{ color: 'rgba(255,255,255,0.75)' }}>
            Secure, fast, and intuitive. Join thousands of users who trust Sentinel for their financial future.
          </p>
        </div>

        {/* Feature cards */}
        <div className="relative z-10 grid grid-cols-2 gap-4">
          {[
            { icon: <MdShield size={26} />, title: 'Encrypted', sub: 'Military-grade security' },
            { icon: <MdBolt size={26} />, title: 'Instant', sub: 'Real-time transactions' },
          ].map(({ icon, title, sub }) => (
            <div key={title} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)' }}>
              <div className="text-white mb-2">{icon}</div>
              <p className="font-bold text-white text-sm">{title}</p>
              <p className="text-xs" style={{ color: 'rgba(255,255,255,0.65)' }}>{sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── RIGHT PANEL ── */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-white px-6 py-10 sm:px-12 lg:px-16 xl:px-24">
        <div className="w-full max-w-md">

          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div className="p-2 rounded-lg flex items-center" style={{ backgroundColor: '#0000ff', color: 'white' }}>
              <SentinelLogo />
            </div>
            <span className="text-xl font-bold" style={{ color: '#0000ff' }}>Sentinel Bank</span>
          </div>

          <h2 className="text-3xl font-bold text-slate-900 mb-1">Welcome Back</h2>
          <p className="text-slate-500 mb-8 text-sm">Please enter your credentials to access your account.</p>

          {error && (
            <div className="bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-3 mb-6 text-sm">
              {error}
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Email */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email Address</label>
              <div className="relative">
                <MdEmail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input
                  name="email" type="email" required
                  value={formData.email} onChange={handleChange}
                  placeholder="e.g. name@email.com"
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all"
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-sm font-semibold text-slate-700">Password</label>
                <Link to="/forgot-password" className="text-sm font-bold" style={{ color: '#0000ff' }}>Forgot Password?</Link>
              </div>
              <div className="relative">
                <MdLock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input
                  name="password" type={showPassword ? 'text' : 'password'} required
                  value={formData.password} onChange={handleChange}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-12 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all"
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                />
                <button type="button" onClick={() => setShowPassword(v => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-600 transition-colors">
                  {showPassword ? <MdVisibilityOff size={20} /> : <MdVisibility size={20} />}
                </button>
              </div>
            </div>

            {/* Remember */}
            <div className="flex items-center gap-2">
              <input id="remember" type="checkbox" className="w-4 h-4 rounded border-slate-300" style={{ accentColor: '#0000ff' }} />
              <label htmlFor="remember" className="text-sm text-slate-600">Remember this device</label>
            </div>

            <button
              type="submit" disabled={isLoading}
              className="w-full py-4 rounded-xl text-white font-bold text-sm transition-all active:scale-[0.98] disabled:opacity-60"
              style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.25)' }}
              onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
              onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-7">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200" /></div>
            <div className="relative flex justify-center text-xs"><span className="px-4 bg-white text-slate-400 font-medium">Or continue with</span></div>
          </div>

          {/* Social */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Google', svg: <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg> },
              { label: 'Apple', svg: <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M17.05 20.28c-.96 0-2.04-.6-3.23-.6-1.2 0-2.3.56-3.2.56-1.55 0-4.04-2.87-4.04-6.32 0-3.32 2.08-5.08 4.05-5.08 1.1 0 2.03.63 2.86.63.8 0 1.9-.66 3.12-.66 1.4 0 2.6.77 3.3 1.83-2.8 1.57-2.35 5.3.44 6.5-.68 1.7-1.57 3.14-3.3 3.14zM12.03 7.25c-.02-2.3 1.95-4.27 4.23-4.3.06 2.4-2.12 4.45-4.23 4.3z"/></svg> },
            ].map(({ label, svg }) => (
              <button key={label} type="button"
                className="flex items-center justify-center gap-2 py-3 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors text-sm font-semibold text-slate-700">
                {svg}{label}
              </button>
            ))}
          </div>

          <p className="text-center text-sm text-slate-500 mt-8">
            Don't have an account?{' '}
            <Link to="/onboarding" className="font-bold hover:underline" style={{ color: '#0000ff' }}>Open an account</Link>
          </p>

          <AuthFooter showBadges={false} />
        </div>
      </div>
    </div>
  );
};

export default Login;
