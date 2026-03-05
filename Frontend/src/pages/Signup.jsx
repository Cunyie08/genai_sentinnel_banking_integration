import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  MdEmail, MdLock, MdLockReset, MdVisibility, MdVisibilityOff,
  MdVerifiedUser, MdAccountBalance
} from 'react-icons/md';
import axiosInstance from '../api/axiosInstance';
import AuthFooter from '../components/AuthFooter';

const SentinelLogo = () => (
  <svg width="26" height="26" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
    <path clipRule="evenodd" d="M39.475 21.6262C40.358 21.4363 40.6863 21.5589 40.7581 21.5934C40.7876 21.655 40.8547 21.857 40.8082 22.3336C40.7408 23.0255 40.4502 24.0046 39.8572 25.2301C38.6799 27.6631 36.5085 30.6631 33.5858 33.5858C30.6631 36.5085 27.6632 38.6799 25.2301 39.8572C24.0046 40.4502 23.0255 40.7407 22.3336 40.8082C21.8571 40.8547 21.6551 40.7875 21.5934 40.7581C21.5589 40.6863 21.4363 40.358 21.6262 39.475C21.8562 38.4054 22.4689 36.9657 23.5038 35.2817C24.7575 33.2417 26.5497 30.9744 28.7621 28.762C30.9744 26.5497 33.2417 24.7574 35.2817 23.5037C36.9657 22.4689 38.4054 21.8562 39.475 21.6262ZM4.41189 29.2403L18.7597 43.5881C19.8813 44.7097 21.4027 44.9179 22.7217 44.7893C24.0585 44.659 25.5148 44.1631 26.9723 43.4579C29.9052 42.0387 33.2618 39.5667 36.4142 36.4142C39.5667 33.2618 42.0387 29.9052 43.4579 26.9723C44.1631 25.5148 44.659 24.0585 44.7893 22.7217C44.9179 21.4027 44.7097 19.8813 43.5881 18.7597L29.2403 4.41187C27.8527 3.02428 25.8765 3.02573 24.2861 3.36776C22.6081 3.72863 20.7334 4.58419 18.8396 5.74801C16.4978 7.18716 13.9881 9.18353 11.5858 11.5858C9.18354 13.988 7.18717 16.4978 5.74802 18.8396C4.58421 20.7334 3.72865 22.6081 3.36778 24.2861C3.02574 25.8765 3.02429 27.8527 4.41189 29.2403Z" fill="currentColor" fillRule="evenodd" />
  </svg>
);

const Signup = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!agreedToTerms) { setError('Please agree to the Terms of Service and Privacy Policy.'); return; }
    if (formData.password !== formData.confirmPassword) { setError('Passwords do not match.'); return; }
    if (formData.password.length < 8) { setError('Password must be at least 8 characters.'); return; }

    setIsLoading(true);
    try {
      await axiosInstance.post('/auth/register', { email: formData.email, password: formData.password });
      navigate('/verify-otp', { state: { email: formData.email, purpose: 'registration' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const inputClass = "w-full rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all";

  return (
    <div className="min-h-screen flex items-center justify-center p-4 md:p-8" style={{ backgroundColor: '#f5f5f8', fontFamily: 'Manrope, sans-serif' }}>
      <div className="max-w-5xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row" style={{ minHeight: '680px' }}>

        {/* ── LEFT PANEL ── */}
        <div
          className="hidden md:flex md:w-5/12 p-10 text-white flex-col justify-between relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, #4a86e8 0%, #0000ff 50%, #1414ff 100%)' }}
        >
          {/* Grid overlay */}
          <div className="absolute inset-0 opacity-10 pointer-events-none">
            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="sg" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#sg)" />
            </svg>
          </div>

          {/* Top */}
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-10">
              <div className="bg-white/20 p-2.5 rounded-xl flex items-center justify-center">
                <MdVerifiedUser size={26} className="text-white" />
              </div>
              <h1 className="text-xl font-extrabold tracking-tight">Sentinel Bank</h1>
            </div>
            <h2 className="text-3xl font-black leading-tight mb-4">Secure Banking Starts Here</h2>
            <p className="text-sm leading-relaxed" style={{ color: 'rgba(219,234,254,0.9)' }}>
              Join over 2 million customers who trust Sentinel Bank for their financial future. Our world-class security protocols ensure your assets are protected 24/7.
            </p>
          </div>

          {/* Feature list */}
          <div className="relative z-10 space-y-4">
            {[
              { icon: <MdVerifiedUser size={22} />, title: 'Institutional Grade Security', sub: 'Multi-layer encryption for every transaction.' },
              { icon: <MdAccountBalance size={22} />, title: 'Fully Licensed', sub: 'Regulated and compliant with global standards.' },
            ].map(({ icon, title, sub }) => (
              <div key={title} className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(255,255,255,0.2)' }}>
                  {icon}
                </div>
                <div>
                  <p className="font-bold text-sm">{title}</p>
                  <p className="text-xs" style={{ color: 'rgba(219,234,254,0.8)' }}>{sub}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="relative z-10 pt-6 border-t" style={{ borderColor: 'rgba(255,255,255,0.2)' }}>
            <p className="text-xs" style={{ color: 'rgba(219,234,254,0.7)' }}>© {new Date().getFullYear()} Sentinel Bank Corp. All rights reserved.</p>
          </div>
        </div>

        {/* ── RIGHT PANEL ── */}
        <div className="w-full md:w-7/12 p-8 md:p-12 flex flex-col justify-center bg-white">
          <div className="mb-8">
            <h3 className="text-2xl md:text-3xl font-bold text-slate-900 mb-1">Create Your Account</h3>
            <p className="text-slate-500 text-sm">Enter your details to get started with a premium banking experience.</p>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-3 mb-5 text-sm">{error}</div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            {/* Email */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Email Address</label>
              <div className="relative">
                <MdEmail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input name="email" type="email" required value={formData.email} onChange={handleChange}
                  placeholder="name@example.com"
                  className={`${inputClass} pl-11 pr-4 py-4`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Password</label>
              <div className="relative">
                <MdLock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input name="password" type={showPassword ? 'text' : 'password'} required
                  value={formData.password} onChange={handleChange}
                  placeholder="Create a strong password"
                  className={`${inputClass} pl-11 pr-12 py-4`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                />
                <button type="button" onClick={() => setShowPassword(v => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-600 transition-colors">
                  {showPassword ? <MdVisibilityOff size={20} /> : <MdVisibility size={20} />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-slate-700">Confirm Password</label>
              <div className="relative">
                <MdLockReset className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input name="confirmPassword" type={showConfirm ? 'text' : 'password'} required
                  value={formData.confirmPassword} onChange={handleChange}
                  placeholder="Repeat your password"
                  className={`${inputClass} pl-11 pr-12 py-4`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                />
                <button type="button" onClick={() => setShowConfirm(v => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-600 transition-colors">
                  {showConfirm ? <MdVisibilityOff size={20} /> : <MdVisibility size={20} />}
                </button>
              </div>
            </div>

            {/* Terms */}
            <div className="flex items-start gap-2 py-1">
              <input id="terms" type="checkbox" checked={agreedToTerms} onChange={e => setAgreedToTerms(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded border-slate-300 flex-shrink-0" style={{ accentColor: '#0000ff' }} />
              <label htmlFor="terms" className="text-sm text-slate-600 leading-relaxed">
                I agree to the{' '}
                <a href="#" className="font-semibold hover:underline" style={{ color: '#0000ff' }}>Terms of Service</a>
                {' '}and{' '}
                <a href="#" className="font-semibold hover:underline" style={{ color: '#0000ff' }}>Privacy Policy</a>.
              </label>
            </div>

            <button type="submit" disabled={isLoading}
              className="w-full py-4 rounded-xl text-white font-bold text-sm transition-all active:scale-[0.98] disabled:opacity-60 mt-2"
              style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.25)' }}
              onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
              onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>

            <p className="text-center text-sm text-slate-600 pt-2">
              Already have an account?{' '}
              <Link to="/login" className="font-bold hover:underline" style={{ color: '#0000ff' }}>Login</Link>
            </p>
          </form>

          <AuthFooter />
        </div>
      </div>
    </div>
  );
};

export default Signup;
