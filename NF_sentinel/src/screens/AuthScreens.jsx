import { useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { loginUser, clearAuthError } from '../features/authSlice';
import { triggerWelcome } from '../features/uiSlice';
import {
  Eye, EyeOff, Fingerprint, Lock, ChevronRight,
  AlertCircle, ShieldCheck, Globe, Share2,
  Zap, TrendingUp, Users, CheckCircle, XCircle
} from 'lucide-react';


const InjectStyles = () => (
  <style>{`
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(14px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .au  { animation: fadeUp 0.4s ease both; }
    .au1 { animation-delay: 0.05s; }
    .au2 { animation-delay: 0.13s; }
    .au3 { animation-delay: 0.21s; }
    .au4 { animation-delay: 0.29s; }
    .au5 { animation-delay: 0.37s; }

    @keyframes floatY {
      0%, 100% { transform: translateY(0px);  }
      50%       { transform: translateY(-7px); }
    }
    .fc1 { animation: floatY 4.0s ease-in-out infinite 0.0s; }
    .fc2 { animation: floatY 4.0s ease-in-out infinite 1.3s; }
    .fc3 { animation: floatY 4.0s ease-in-out infinite 2.6s; }
  `}</style>
);


const BrandPanel = ({ isLogin }) => {
  const navigate = useNavigate();

  const features = [
    { icon: Zap,        text: 'Instant transfers in under 3 seconds' },
    { icon: ShieldCheck,text: '256-bit bank-grade encryption'        },
    { icon: TrendingUp, text: 'Up to 15% interest on savings'       },
    { icon: Users,      text: '2 million+ Nigerians trust Sentinel'  },
  ];

  return (
    <div className="hidden lg:flex flex-col w-[44%] xl:w-[42%] 2xl:w-[40%] h-full shrink-0 bg-gradient-to-br from-[#800020] via-[#A01030] to-[#5a0a1e] relative overflow-hidden">
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-white/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-white/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-white/[0.03] rounded-full blur-2xl pointer-events-none" />

      <div className="relative z-10 flex flex-col h-full p-10 xl:p-12 2xl:p-16">

        {/* Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-10 h-10 xl:w-11 xl:h-11 bg-white/15 rounded-2xl flex items-center justify-center border border-white/20 backdrop-blur-sm shrink-0">
            <span className="text-white font-black text-lg xl:text-xl">S</span>
          </div>
          <div>
            <span className="text-white font-extrabold text-xl xl:text-2xl tracking-tight leading-none block">SENTINEL</span>
            <span className="text-white/50 text-[10px] font-bold uppercase tracking-widest">Fintech</span>
          </div>
        </div>

        {/* Hero Text */}
        <div className="flex-1 flex flex-col justify-center py-8">
          <p className="text-white/55 text-xs font-bold uppercase tracking-widest mb-4">
            {isLogin ? 'Welcome back' : 'Get started today'}
          </p>
          <h1 className="text-4xl xl:text-5xl 2xl:text-6xl font-black text-white leading-[1.1] mb-5">
            {isLogin
              ? <><span>Your money,</span><br /><span>always in</span><br /><span className="text-rose-300">your control.</span></>
              : <><span>Banking</span><br /><span>built for</span><br /><span className="text-rose-300">Nigeria.</span></>
            }
          </h1>
          <p className="text-white/60 text-sm xl:text-base leading-relaxed max-w-xs mb-8 xl:mb-10">
            {isLogin
              ? 'Sign in to manage transfers, bills, savings and more — all in one secure place.'
              : 'Join 2 million+ Nigerians who trust Sentinel for fast, secure everyday banking.'}
          </p>

          {/* Features */}
          <div className="space-y-3 xl:space-y-4">
            {features.map((f, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 xl:w-9 xl:h-9 bg-white/10 rounded-xl flex items-center justify-center border border-white/10 shrink-0">
                  <f.icon size={15} className="text-rose-300" />
                </div>
                <span className="text-white/75 text-sm font-medium">{f.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Floating Stats */}
        <div className="flex gap-3 xl:gap-4 shrink-0 mb-6">
          {[
            { val: '₦2.4B', label: 'Daily volume', cls: 'fc1' },
            { val: '4.9 ★', label: 'App rating',   cls: 'fc2' },
            { val: '2M+',   label: 'Users',         cls: 'fc3' },
          ].map(s => (
            <div key={s.label} className={`${s.cls} bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl px-4 py-3 xl:px-5 xl:py-4 flex-1`}>
              <p className="text-white font-black text-lg xl:text-xl leading-none mb-0.5">{s.val}</p>
              <p className="text-white/45 text-[9px] xl:text-[10px] font-bold uppercase tracking-wide">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Trust badge */}
        <div className="flex items-center gap-2 shrink-0">
          <ShieldCheck size={13} className="text-white/35" />
          <span className="text-white/35 text-[10px] font-bold uppercase tracking-widest">
            Licensed by the Central Bank of Nigeria
          </span>
        </div>

      </div>
    </div>
  );
};


const Footer = () => (
  <footer className="shrink-0 px-6 xl:px-10 py-4 border-t border-gray-100 bg-white">
    <div className="flex flex-col sm:flex-row justify-between items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
      <span>© 2026 Team Sentinel · Licensed by CBN</span>
      <div className="flex gap-4 items-center">
        <a href="#" className="hover:text-gray-600 transition-colors">Privacy</a>
        <a href="#" className="hover:text-gray-600 transition-colors">Terms</a>
        <a href="#" className="hover:text-gray-600 transition-colors">Support</a>
        <Share2 size={12} className="cursor-pointer hover:text-gray-600 transition-colors" />
        <Globe  size={12} className="cursor-pointer hover:text-gray-600 transition-colors" />
      </div>
    </div>
  </footer>
);


const AuthScreens = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error } = useSelector(state => state.auth);
  const [view, setView]         = useState('login');
  const [formData, setFormData] = useState({
    phone: '', password: '', name: '', email: '',
    gender: 'Other', date_of_birth: '', bvn: '', nin: '',
    telco_provider: '', state_of_origin: '', residential_state: '', banking_branch: ''
  });
  const [showPass,   setShowPass]   = useState(false);
  const [authError,  setAuthError]  = useState('');

  // Password validation rules
  const passwordRules = [
    { id: 'length',  text: 'Min. 8 characters',          regex: /.{8,}/       },
    { id: 'upper',   text: '1 Uppercase letter',          regex: /[A-Z]/       },
    { id: 'number',  text: '1 Number',                    regex: /\d/          },
    { id: 'special', text: '1 Special char (@$!%*?&)',    regex: /[@$!%*?&]/   },
  ];

  const passwordRegex   = /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
  const isPasswordValid = (pass) => passwordRegex.test(pass);

  const handleChange = (e) => {
    setAuthError('');
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // FIX: Clear both local and redux errors when switching views
  const switchView = (newView) => {
    setView(newView);
    setAuthError('');
    dispatch(clearAuthError());
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    if (!formData.email || !formData.password) {
      setAuthError('Please fill in all fields');
      return;
    }
    try {
      await dispatch(loginUser({ email: formData.email, password: formData.password })).unwrap();
      dispatch(triggerWelcome());
      navigate('/home');
    } catch (err) {
      setAuthError(err.message || 'Login failed');
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setAuthError('');
    if (!formData.name || !formData.phone || !formData.email || !formData.password ||
        !formData.date_of_birth || !formData.bvn || !formData.nin || !formData.telco_provider ||
        !formData.state_of_origin || !formData.residential_state || !formData.banking_branch) {
      setAuthError('Please fill in all fields');
      return;
    }
    if (formData.bvn.length !== 11 || formData.nin.length !== 11) {
      setAuthError('BVN and NIN must be exactly 11 digits');
      return;
    }
    if (!isPasswordValid(formData.password)) {
      setAuthError('Password must be at least 8 chars long, contain 1 uppercase letter, 1 number, and 1 special char.');
      return;
    }
    try {
      await dispatch(loginUser({ ...formData, isSignup: true })).unwrap();
      dispatch(triggerWelcome());
      navigate('/home');
    } catch (err) {
      setAuthError(err.message || 'Signup failed');
    }
  };

  const isLogin = view === 'login';

  const inputBase = "w-full px-4 py-4 bg-gray-50 border border-gray-200 rounded-2xl outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:border-[#A01030] focus:ring-2 focus:ring-[#A01030]/10 transition-all";
  const fieldWrap = "flex bg-gray-50 border border-gray-200 rounded-2xl overflow-hidden focus-within:border-[#A01030] focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all";
  const passWrap  = "relative bg-gray-50 border border-gray-200 rounded-2xl overflow-hidden focus-within:border-[#A01030] focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all";

  return (
    <div className="h-[100dvh] w-full flex flex-col lg:flex-row overflow-hidden font-sans">
      <InjectStyles />

      {/* LEFT: Branding Panel */}
      <BrandPanel isLogin={isLogin} />

      {/* RIGHT: Auth Forms */}
      <div className="flex-1 min-w-0 flex flex-col bg-[#F9FAFB] lg:bg-white overflow-y-auto">

        {/* Mobile Mini Header */}
        <div className="lg:hidden flex items-center gap-2.5 px-6 pt-8 pb-2 shrink-0">
          <div className="w-8 h-8 bg-[#A01030] rounded-xl flex items-center justify-center shrink-0">
            <span className="text-white font-black text-sm">S</span>
          </div>
          <div>
            <span className="text-[#A01030] font-extrabold text-base tracking-tight leading-none block">SENTINEL</span>
            <span className="text-gray-400 text-[9px] font-bold uppercase tracking-widest">Fintech</span>
          </div>
        </div>

        {/* Scrollable Center Block */}
        <div className="flex-1 flex flex-col justify-center px-6 sm:px-10 lg:px-12 xl:px-16 2xl:px-24 py-8">
          <div className="w-full max-w-sm sm:max-w-md mx-auto lg:mx-0 lg:max-w-lg xl:max-w-xl">

            {isLogin ? (

              <>
                <div className="hidden lg:flex w-14 h-14 xl:w-16 xl:h-16 bg-red-50 rounded-2xl xl:rounded-3xl items-center justify-center mb-6 au au1">
                  <Fingerprint size={28} className="text-[#A01030]" strokeWidth={1.5} />
                </div>

                <div className="au au1 mb-7 xl:mb-8">
                  <p className="text-[10px] xl:text-xs font-bold text-gray-400 uppercase tracking-widest mb-1.5">Secure Login</p>
                  <h2 className="text-2xl sm:text-3xl xl:text-4xl font-black text-gray-900 leading-tight mb-2">
                    Welcome back
                  </h2>
                  <p className="text-gray-500 text-sm xl:text-base leading-relaxed">
                    Securely access your account to manage your finances.
                  </p>
                </div>

                {(error || authError) && (
                  <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2 au au2">
                    <AlertCircle size={15} /> {authError || error}
                  </div>
                )}

                <form onSubmit={handleLogin} className="space-y-5 au au3">

                  {/* Email */}
                  <div>
                    <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Email Address</label>
                    <input name="email" type="email" placeholder="you@example.com"
                      className={inputBase} value={formData.email} onChange={handleChange} />
                  </div>

                  {/* Password */}
                  <div>
                    <div className="flex justify-between items-center mb-2 ml-1">
                      <label className="text-xs xl:text-sm font-bold text-gray-700">Password</label>
                      <button type="button" className="text-xs font-bold text-[#A01030] hover:underline">Forgot Password?</button>
                    </div>
                    <div className={passWrap}>
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                        <Lock size={18} />
                      </div>
                      <input name="password" type={showPass ? 'text' : 'password'} placeholder="Enter password"
                        className="w-full pl-12 pr-12 py-4 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400"
                        value={formData.password} onChange={handleChange} />
                      <button type="button" onClick={() => setShowPass(!showPass)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
                        {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  {/* Login Button */}
                  <button type="submit" disabled={isLoading}
                    className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm xl:text-base shadow-xl shadow-red-900/20 hover:bg-[#850d28] transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-70">
                    {isLoading ? 'Logging in securely...' : 'Login to Account'}
                    {!isLoading && <ChevronRight size={16} />}
                  </button>
                </form>

                <div className="flex items-center gap-4 my-6 au au4">
                  <div className="h-px bg-gray-200 flex-1" />
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">OR</span>
                  <div className="h-px bg-gray-200 flex-1" />
                </div>

                <button className="w-full py-4 bg-white border border-gray-200 text-gray-700 rounded-2xl font-bold text-sm hover:bg-gray-50 transition-colors flex items-center justify-center gap-2 au au4">
                  <Fingerprint size={20} className="text-[#A01030]" /> Login with FaceID / Biometrics
                </button>

                <p className="text-sm text-gray-500 mt-6 text-center au au5">
                  Don't have an account?{' '}
                  {/* FIX: Clear errors on view switch */}
                  <button onClick={() => switchView('signup')} className="text-[#A01030] font-bold hover:underline">
                    Create Account
                  </button>
                </p>

                <div className="mt-5 flex items-center justify-center gap-2 au au5">
                  <ShieldCheck size={13} className="text-gray-300" />
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">256-bit Encrypted · CBN Licensed</span>
                </div>
              </>

            ) : (

              <>
                <div className="hidden lg:flex w-14 h-14 xl:w-16 xl:h-16 bg-red-50 rounded-2xl xl:rounded-3xl items-center justify-center mb-6 au au1">
                  <CheckCircle size={28} className="text-[#A01030]" strokeWidth={1.5} />
                </div>

                <div className="au au1 mb-7 xl:mb-8">
                  <p className="text-[10px] xl:text-xs font-bold text-gray-400 uppercase tracking-widest mb-1.5">New Account</p>
                  <h2 className="text-2xl sm:text-3xl xl:text-4xl font-black text-gray-900 leading-tight mb-2">
                    Create your<br />Sentinel account
                  </h2>
                  <p className="text-gray-500 text-sm xl:text-base leading-relaxed">
                    Join millions of Nigerians managing their money smarter with Sentinel.
                  </p>
                </div>

                <form onSubmit={handleSignup} className="space-y-5 au au3">
                  {(error || authError) && (
                    <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2 au au2">
                      <AlertCircle size={15} /> {authError || error}
                    </div>
                  )}

                  <div>
                    <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Full Name</label>
                    <input name="name" type="text" placeholder="e.g. Reuben Tunde"
                      className={inputBase} value={formData.name} onChange={handleChange} />
                  </div>

                  <div>
                    <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Phone Number</label>
                    <div className={fieldWrap}>
                      <div className="px-4 py-4 bg-gray-100 text-gray-500 text-sm font-bold border-r border-gray-200 flex items-center shrink-0">+234</div>
                      <input name="phone" type="text" placeholder="800 000 0000"
                        className="flex-1 px-4 py-4 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400 min-w-0"
                        value={formData.phone} onChange={handleChange} />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Email Address</label>
                    <input name="email" type="email" placeholder="you@example.com"
                      className={inputBase} value={formData.email} onChange={handleChange} />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Gender</label>
                      <select name="gender" className={inputBase} value={formData.gender} onChange={handleChange}>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Date of Birth</label>
                      <input name="date_of_birth" type="date"
                        className={inputBase} value={formData.date_of_birth} onChange={handleChange} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">BVN</label>
                      <input name="bvn" type="text" placeholder="11 digits" maxLength={11}
                        className={inputBase} value={formData.bvn} onChange={handleChange} />
                    </div>
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">NIN</label>
                      <input name="nin" type="text" placeholder="11 digits" maxLength={11}
                        className={inputBase} value={formData.nin} onChange={handleChange} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">State of Origin</label>
                      <input name="state_of_origin" type="text" placeholder="e.g. Lagos"
                        className={inputBase} value={formData.state_of_origin} onChange={handleChange} />
                    </div>
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Residential State</label>
                      <input name="residential_state" type="text" placeholder="e.g. Abuja"
                        className={inputBase} value={formData.residential_state} onChange={handleChange} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Telco Provider</label>
                      <select name="telco_provider" className={inputBase} value={formData.telco_provider} onChange={handleChange}>
                        <option value="">Select</option>
                        <option value="MTN">MTN</option>
                        <option value="Airtel">Airtel</option>
                        <option value="Glo">Glo</option>
                        <option value="9mobile">9mobile</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Banking Branch</label>
                      <input name="banking_branch" type="text" placeholder="e.g. Digital HQ"
                        className={inputBase} value={formData.banking_branch} onChange={handleChange} />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label className="block text-xs xl:text-sm font-bold text-gray-700 mb-2 ml-1">Create Password</label>
                    <div className={passWrap}>
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                        <Lock size={18} />
                      </div>
                      <input name="password" type={showPass ? 'text' : 'password'} placeholder="Password"
                        className="w-full pl-12 pr-12 py-4 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400"
                        value={formData.password} onChange={handleChange} />
                      <button type="button" onClick={() => setShowPass(!showPass)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
                        {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>

                    {/* Live Validator */}
                    <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px] xl:text-xs">
                      {passwordRules.map(rule => {
                        const passed = rule.regex.test(formData.password);
                        return (
                          <div key={rule.id} className={`flex items-center gap-1.5 font-bold transition-colors ${passed ? 'text-green-600' : 'text-gray-400'}`}>
                            {passed ? <CheckCircle size={12} className="shrink-0" /> : <XCircle size={12} className="shrink-0" />}
                            <span>{rule.text}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <p className="text-[11px] text-gray-400 leading-relaxed">
                    By creating an account you agree to our{' '}
                    <span className="text-[#A01030] font-bold cursor-pointer hover:underline">Terms of Service</span>
                    {' '}and{' '}
                    <span className="text-[#A01030] font-bold cursor-pointer hover:underline">Privacy Policy</span>.
                  </p>

                  <button type="submit" disabled={isLoading}
                    className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm xl:text-base shadow-xl shadow-red-900/20 hover:bg-[#850d28] transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-70">
                    {isLoading ? 'Creating Account...' : 'Create My Account'}
                    {!isLoading && <ChevronRight size={16} />}
                  </button>
                </form>

                <p className="text-sm text-gray-500 mt-6 text-center au au5">
                  Already have an account?{' '}
                  {/* FIX: Clear errors on view switch */}
                  <button onClick={() => switchView('login')} className="text-[#A01030] font-bold hover:underline">
                    Log In
                  </button>
                </p>

                <div className="mt-4 flex items-center justify-center gap-2 au au5">
                  <ShieldCheck size={13} className="text-gray-300" />
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">256-bit Encrypted · CBN Licensed</span>
                </div>
              </>
            )}

          </div>
        </div>

        <Footer />
      </div>
    </div>
  );
};

export default AuthScreens;