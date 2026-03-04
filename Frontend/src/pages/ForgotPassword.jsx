import { useState } from 'react';
import { Link } from 'react-router-dom';
import { MdEmail, MdArrowBack, MdMarkEmailRead } from 'react-icons/md';
import axiosInstance from '../api/axiosInstance';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await axiosInstance.post('/auth/forgot-password', { email });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ fontFamily: 'Manrope, sans-serif', backgroundColor: '#f5f5f8' }}>
      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center p-12 relative overflow-hidden" style={{ backgroundColor: '#0000ff' }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 50%, rgba(74,134,232,0.4) 0%, transparent 70%)' }} />
        <div className="relative z-10 max-w-lg text-white">
          <div className="flex items-center gap-3 mb-12">
            <div className="bg-white p-2 rounded-lg"><MdEmail size={26} style={{ color: '#0000ff' }} /></div>
            <span className="text-2xl font-bold">Sentinel Bank</span>
          </div>
          <h1 className="text-5xl font-extrabold leading-tight mb-6">Forgot your password?</h1>
          <p className="text-xl leading-relaxed" style={{ color: 'rgba(255,255,255,0.8)' }}>
            No worries. Enter your registered email and we'll send you a secure reset link instantly.
          </p>
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-white px-6 py-10 sm:px-12 lg:px-24">
        <div className="w-full max-w-md">
          <Link to="/login" className="inline-flex items-center gap-2 text-sm font-semibold mb-8 transition-colors" style={{ color: '#0000ff' }}>
            <MdArrowBack size={18} /> Back to Login
          </Link>

          {sent ? (
            <div className="text-center">
              <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: 'rgba(0,0,255,0.08)' }}>
                <MdMarkEmailRead size={40} style={{ color: '#0000ff' }} />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-3">Check Your Inbox</h2>
              <p className="text-slate-500 text-sm mb-8">
                We sent a password reset link to <span className="font-semibold text-slate-700">{email}</span>. Check your spam folder if you don't see it.
              </p>
              <Link to="/login" className="block w-full py-4 rounded-xl text-white font-bold text-sm text-center transition-all"
                style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.25)' }}>
                Back to Login
              </Link>
            </div>
          ) : (
            <>
              <h2 className="text-3xl font-bold text-slate-900 mb-1">Reset Password</h2>
              <p className="text-slate-500 text-sm mb-8">Enter your email address and we'll send you a reset link.</p>

              {error && <div className="bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-3 mb-5 text-sm">{error}</div>}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email Address</label>
                  <div className="relative">
                    <MdEmail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                    <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                      placeholder="name@example.com"
                      className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all"
                      onFocus={e => e.target.style.borderColor = '#0000ff'}
                      onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                    />
                  </div>
                </div>
                <button type="submit" disabled={isLoading}
                  className="w-full py-4 rounded-xl text-white font-bold text-sm transition-all active:scale-[0.98] disabled:opacity-60"
                  style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.25)' }}
                  onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
                  onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
                >
                  {isLoading ? 'Sending...' : 'Send Reset Link'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
