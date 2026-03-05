import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { MdMarkEmailRead, MdTimer } from 'react-icons/md';
import axiosInstance from '../api/axiosInstance';
import AuthFooter from '../components/AuthFooter';

const SentinelLogo = () => (
  <svg width="26" height="26" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
    <path clipRule="evenodd" d="M39.475 21.6262C40.358 21.4363 40.6863 21.5589 40.7581 21.5934C40.7876 21.655 40.8547 21.857 40.8082 22.3336C40.7408 23.0255 40.4502 24.0046 39.8572 25.2301C38.6799 27.6631 36.5085 30.6631 33.5858 33.5858C30.6631 36.5085 27.6632 38.6799 25.2301 39.8572C24.0046 40.4502 23.0255 40.7407 22.3336 40.8082C21.8571 40.8547 21.6551 40.7875 21.5934 40.7581C21.5589 40.6863 21.4363 40.358 21.6262 39.475C21.8562 38.4054 22.4689 36.9657 23.5038 35.2817C24.7575 33.2417 26.5497 30.9744 28.7621 28.762C30.9744 26.5497 33.2417 24.7574 35.2817 23.5037C36.9657 22.4689 38.4054 21.8562 39.475 21.6262ZM4.41189 29.2403L18.7597 43.5881C19.8813 44.7097 21.4027 44.9179 22.7217 44.7893C24.0585 44.659 25.5148 44.1631 26.9723 43.4579C29.9052 42.0387 33.2618 39.5667 36.4142 36.4142C39.5667 33.2618 42.0387 29.9052 43.4579 26.9723C44.1631 25.5148 44.659 24.0585 44.7893 22.7217C44.9179 21.4027 44.7097 19.8813 43.5881 18.7597L29.2403 4.41187C27.8527 3.02428 25.8765 3.02573 24.2861 3.36776C22.6081 3.72863 20.7334 4.58419 18.8396 5.74801C16.4978 7.18716 13.9881 9.18353 11.5858 11.5858C9.18354 13.988 7.18717 16.4978 5.74802 18.8396C4.58421 20.7334 3.72865 22.6081 3.36778 24.2861C3.02574 25.8765 3.02429 27.8527 4.41189 29.2403Z" fill="currentColor" fillRule="evenodd" />
  </svg>
);

const OTPVerify = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const purpose = location.state?.purpose || 'registration';

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [countdown, setCountdown] = useState(60);
  const inputRefs = useRef([]);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => setCountdown(p => p - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const handleOtpChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    if (value && index < 5) inputRefs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) inputRefs.current[index - 1]?.focus();
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = [...otp];
    pasted.split('').forEach((c, i) => { newOtp[i] = c; });
    setOtp(newOtp);
    inputRefs.current[Math.min(pasted.length, 5)]?.focus();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const otpCode = otp.join('');
    if (otpCode.length !== 6) { setError('Please enter the full 6-digit code.'); return; }
    setIsLoading(true);
    setError('');
    try {
      await axiosInstance.post('/auth/verify-otp', { email, otp_code: otpCode, purpose });
      setSuccess('Account verified! Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    if (countdown > 0) return;
    setIsResending(true);
    setError('');
    try {
      await axiosInstance.post('/auth/resend-otp', { email });
      setSuccess('A new OTP has been sent to your email.');
      setCountdown(60);
      setOtp(['', '', '', '', '', '']);
      setTimeout(() => setSuccess(''), 4000);
    } catch {
      setError('Failed to resend OTP. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ fontFamily: 'Manrope, sans-serif', backgroundColor: '#f5f5f8' }}>

      {/* ── LEFT PANEL ── */}
      <div
        className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden"
        style={{ backgroundColor: '#0000ff' }}
      >
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 50%, rgba(74,134,232,0.4) 0%, transparent 70%)' }} />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 rounded-full opacity-40 pointer-events-none" style={{ backgroundColor: '#1414ff', filter: 'blur(80px)' }} />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="bg-white p-2 rounded-lg text-blue-700 flex items-center justify-center">
              <SentinelLogo />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">Sentinel Bank</span>
          </div>
          <h1 className="text-4xl xl:text-5xl font-extrabold leading-tight text-white mb-5">
            One last step to secure your account.
          </h1>
          <p className="text-lg leading-relaxed" style={{ color: 'rgba(255,255,255,0.75)' }}>
            We take your security seriously. A verification code keeps your account safe from unauthorised access.
          </p>
        </div>

        <div className="relative z-10 grid grid-cols-2 gap-4">
          {[
            { icon: <MdMarkEmailRead size={26} />, title: 'Check Email', sub: 'Code sent to your inbox' },
            { icon: <MdTimer size={26} />, title: '15 Minutes', sub: 'Code expires soon' },
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

          {/* Icon badge */}
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6" style={{ backgroundColor: 'rgba(0,0,255,0.08)' }}>
            <MdMarkEmailRead size={30} style={{ color: '#0000ff' }} />
          </div>

          <h2 className="text-3xl font-bold text-slate-900 mb-1">Verify Your Email</h2>
          <p className="text-slate-500 text-sm mb-8">
            We've sent a 6-digit code to{' '}
            <span className="font-semibold text-slate-700">{email || 'your email'}</span>. Enter it below.
          </p>

          {error && <div className="bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-3 mb-5 text-sm">{error}</div>}
          {success && <div className="bg-green-50 text-green-600 border border-green-200 rounded-xl px-4 py-3 mb-5 text-sm">{success}</div>}

          <form onSubmit={handleSubmit}>
            {/* OTP Boxes */}
            <div className="flex gap-2 sm:gap-3 justify-between mb-8" onPaste={handlePaste}>
              {otp.map((digit, i) => (
                <input
                  key={i}
                  ref={el => inputRefs.current[i] = el}
                  type="text" inputMode="numeric" maxLength={1}
                  value={digit}
                  onChange={e => handleOtpChange(i, e.target.value)}
                  onKeyDown={e => handleKeyDown(i, e)}
                  className="w-10 h-12 sm:w-12 sm:h-14 text-center text-xl sm:text-2xl font-bold bg-slate-50 rounded-xl border-2 border-slate-200 focus:outline-none transition-all"
                  style={digit ? { borderColor: '#0000ff', color: '#0000ff' } : {}}
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => { if (!digit) e.target.style.borderColor = '#e2e8f0'; }}
                />
              ))}
            </div>

            <button
              type="submit"
              disabled={isLoading || otp.join('').length !== 6}
              className="w-full py-4 rounded-xl text-white font-bold text-sm transition-all active:scale-[0.98] disabled:opacity-60"
              style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.25)' }}
              onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
              onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
            >
              {isLoading ? 'Verifying...' : 'Verify & Activate Account'}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-5">
            Didn't receive the code?{' '}
            <button type="button" onClick={handleResend}
              disabled={countdown > 0 || isResending}
              className="font-bold transition-colors disabled:text-slate-400 disabled:cursor-not-allowed"
              style={countdown === 0 && !isResending ? { color: '#0000ff' } : {}}>
              {isResending ? 'Resending...' : countdown > 0 ? `Resend in ${countdown}s` : 'Resend Code'}
            </button>
          </p>

          <p className="text-center text-sm text-slate-500 mt-3">
            Wrong email? <Link to="/signup" className="font-bold hover:underline" style={{ color: '#0000ff' }}>Go back</Link>
          </p>

          <AuthFooter showBadges={false} />
        </div>
      </div>
    </div>
  );
};

export default OTPVerify;
