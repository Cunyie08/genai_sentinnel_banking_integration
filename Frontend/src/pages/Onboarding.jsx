import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  MdPerson, MdVerifiedUser, MdLocationOn, MdPhone,
  MdEmail, MdArrowForward, MdBadge, MdAccountBalance
} from 'react-icons/md';
import { useStore } from '../store/useStore';
import AuthFooter from '../components/AuthFooter';

const NIGERIAN_STATES = [
  'Abia','Adamawa','Akwa Ibom','Anambra','Bauchi','Bayelsa','Benue','Borno',
  'Cross River','Delta','Ebonyi','Edo','Ekiti','Enugu','FCT','Gombe','Imo',
  'Jigawa','Kaduna','Kano','Katsina','Kebbi','Kogi','Kwara','Lagos','Nasarawa',
  'Niger','Ogun','Ondo','Osun','Oyo','Plateau','Rivers','Sokoto','Taraba',
  'Yobe','Zamfara'
];

const TELCOS = ['MTN','Airtel','Glo','9mobile'];

const Section = ({ icon: Icon, title, children }) => (
  <div className="mb-8">
    <div className="flex items-center gap-2 mb-5 pb-3 border-b border-slate-100">
      <Icon size={18} style={{ color: '#0000ff' }} />
      <h3 className="text-sm font-bold text-slate-700">{title}</h3>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div>
  </div>
);

const Field = ({ label, children, full = false }) => (
  <div className={`flex flex-col gap-1.5 ${full ? 'md:col-span-2' : ''}`}>
    <label className="text-sm font-semibold text-slate-700">{label}</label>
    {children}
  </div>
);

const Onboarding = () => {
  const navigate = useNavigate();
  const { createCustomer, isLoading } = useStore();

  const [formData, setFormData] = useState({
    first_name: '', last_name: '', gender: '', date_of_birth: '',
    bvn: '', nin: '', phone_number: '', telco_provider: '', email: '',
    state_of_origin: '', residential_state: '', banking_branch: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(null); // { account_number }

  const inputClass = "w-full px-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all";
  const selectClass = `${inputClass} appearance-none`;

  const set = (e) => setFormData(p => ({ ...p, [e.target.name]: e.target.value }));
  const focus = (e) => { e.target.style.borderColor = '#0000ff'; };
  const blur  = (e) => { e.target.style.borderColor = '#e2e8f0'; };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (formData.bvn.length !== 11 || formData.nin.length !== 11) {
      setError('BVN and NIN must each be exactly 11 digits.');
      return;
    }
    try {
      const res = await createCustomer(formData);
      setSuccess(res);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create account. Please try again.');
    }
  };

  // Success state
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 md:p-8" style={{ backgroundColor: '#f5f5f8', fontFamily: 'Manrope, sans-serif' }}>
        <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-10 text-center">
          <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: 'rgba(0,0,255,0.08)' }}>
            <MdVerifiedUser size={40} style={{ color: '#0000ff' }} />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 mb-2">Account Created!</h2>
          <p className="text-slate-500 text-sm mb-6">Your Sentinel Bank account has been set up successfully.</p>
          <div className="bg-slate-50 rounded-xl p-4 mb-8 border border-slate-100">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-bold mb-1">Account Number</p>
            <p className="text-2xl font-extrabold tracking-widest" style={{ color: '#0000ff' }}>{success.account_number}</p>
          </div>
          <p className="text-sm text-slate-500 mb-6">Now create your online banking login to access your account.</p>
          <button onClick={() => navigate('/signup')}
            className="w-full py-4 rounded-xl text-white font-bold text-sm flex items-center justify-center gap-2"
            style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.25)' }}>
            Continue to Sign Up <MdArrowForward size={18} />
          </button>
          <AuthFooter showBadges={false} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-start justify-center p-4 md:p-8" style={{ backgroundColor: '#f5f5f8', fontFamily: 'Manrope, sans-serif' }}>
      <div className="max-w-5xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row">

        {/* ── LEFT PANEL ── */}
        <div
          className="hidden md:flex md:w-5/12 p-10 text-white flex-col justify-between relative overflow-hidden shrink-0"
          style={{ background: 'linear-gradient(135deg, #4a86e8 0%, #0000ff 50%, #1414ff 100%)' }}
        >
          {/* Grid overlay */}
          <div className="absolute inset-0 opacity-10 pointer-events-none">
            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
              <defs><pattern id="og" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1" />
              </pattern></defs>
              <rect width="100%" height="100%" fill="url(#og)" />
            </svg>
          </div>

          {/* Top */}
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-10">
              <div className="bg-white/20 p-2.5 rounded-xl flex items-center">
                <MdAccountBalance size={24} className="text-white" />
              </div>
              <h1 className="text-xl font-extrabold">Sentinel Bank</h1>
            </div>
            <h2 className="text-3xl font-black leading-tight mb-4">Open Your Account Today</h2>
            <p className="text-sm leading-relaxed" style={{ color: 'rgba(219,234,254,0.9)' }}>
              Complete this one-time form with your legal details, BVN, and NIN to create your Sentinel Bank account.
            </p>
          </div>

          {/* Info cards */}
          <div className="relative z-10 space-y-4">
            {[
              { icon: MdVerifiedUser, title: 'BVN & NIN Required', sub: 'Secure identity verification by CBN.' },
              { icon: MdAccountBalance, title: 'Instant Account Number', sub: 'Receive your account number immediately.' },
            ].map(({ icon: Icon, title, sub }) => (
              <div key={title} className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: 'rgba(255,255,255,0.2)' }}>
                  <Icon size={20} />
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
        <div className="w-full md:w-7/12 p-8 md:p-10 bg-white overflow-y-auto">
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-slate-900 mb-1">Create Your Account</h3>
            <p className="text-slate-500 text-sm">Fill in your legal details to open your Sentinel Bank account.</p>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-3 mb-6 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Personal Info */}
            <Section icon={MdPerson} title="Personal Information">
              <Field label="First Name">
                <input name="first_name" type="text" required value={formData.first_name} onChange={set}
                  placeholder="John" className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
              <Field label="Last Name">
                <input name="last_name" type="text" required value={formData.last_name} onChange={set}
                  placeholder="Doe" className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
              <Field label="Gender">
                <select name="gender" required value={formData.gender} onChange={set} className={selectClass} onFocus={focus} onBlur={blur}>
                  <option value="">Select Gender</option>
                  <option>Male</option><option>Female</option><option>Other</option>
                </select>
              </Field>
              <Field label="Date of Birth">
                <input name="date_of_birth" type="date" required value={formData.date_of_birth} onChange={set}
                  className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
            </Section>

            {/* Verification */}
            <Section icon={MdVerifiedUser} title="Verification & Contact">
              <Field label="BVN (11 digits)">
                <input name="bvn" type="text" required maxLength={11} value={formData.bvn} onChange={set}
                  placeholder="22233344455" className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
              <Field label="NIN (11 digits)">
                <input name="nin" type="text" required maxLength={11} value={formData.nin} onChange={set}
                  placeholder="11122233344" className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
              <Field label="Phone Number" full>
                <input name="phone_number" type="tel" required value={formData.phone_number} onChange={set}
                  placeholder="+2348012345678" className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
              <Field label="Telco Provider" full>
                <select name="telco_provider" required value={formData.telco_provider} onChange={set} className={selectClass} onFocus={focus} onBlur={blur}>
                  <option value="">Select Network</option>
                  {TELCOS.map(t => <option key={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Email Address" full>
                <input name="email" type="email" required value={formData.email} onChange={set}
                  placeholder="john.doe@example.com" className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
            </Section>

            {/* Regional */}
            <Section icon={MdLocationOn} title="Regional Details">
              <Field label="State of Origin">
                <select name="state_of_origin" required value={formData.state_of_origin} onChange={set} className={selectClass} onFocus={focus} onBlur={blur}>
                  <option value="">Select State</option>
                  {NIGERIAN_STATES.map(s => <option key={s}>{s}</option>)}
                </select>
              </Field>
              <Field label="Residential State">
                <select name="residential_state" required value={formData.residential_state} onChange={set} className={selectClass} onFocus={focus} onBlur={blur}>
                  <option value="">Select State</option>
                  {NIGERIAN_STATES.map(s => <option key={s}>{s}</option>)}
                </select>
              </Field>
              <Field label="Preferred Banking Branch" full>
                <input name="banking_branch" type="text" required value={formData.banking_branch} onChange={set}
                  placeholder="e.g. Victoria Island HQ" className={inputClass} onFocus={focus} onBlur={blur} />
              </Field>
            </Section>

            <button type="submit" disabled={isLoading}
              className="w-full py-4 rounded-xl text-white font-bold text-sm flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-60"
              style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.25)' }}
              onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
              onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
            >
              {isLoading ? 'Creating Account...' : <><span>Create Account</span><MdArrowForward size={18} /></>}
            </button>

            <p className="text-center text-sm text-slate-600 mt-5">
              Already have an account?{' '}
              <Link to="/login" className="font-bold hover:underline" style={{ color: '#0000ff' }}>Sign In</Link>
            </p>

            <AuthFooter />
          </form>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
