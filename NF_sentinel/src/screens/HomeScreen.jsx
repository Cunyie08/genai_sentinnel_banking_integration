import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { dismissWelcome, triggerPayment } from "../features/uiSlice";
import { fetchDashboard } from "../features/accountSlice";
import { api } from "../api/axiosConfig";
import {
  Bell, Eye, EyeOff, Copy, QrCode, Send, Plus, Clock, FileText,
  Smartphone, Wifi, Gamepad2, Zap, Sparkles, X, Settings,
  ShieldAlert, Fingerprint, XCircle, CheckCircle, Loader2, Lock
} from "lucide-react";

const bufferToBase64url = (buffer) => {
  const bytes = new Uint8Array(buffer);
  let str = '';
  for (let i = 0; i < bytes.length; i++) str += String.fromCharCode(bytes[i]);
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
};

const base64urlToBuffer = (base64url) => {
  const padding = '='.repeat((4 - base64url.length % 4) % 4);
  const base64 = (base64url + padding).replace(/\-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const buffer = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) buffer[i] = rawData.charCodeAt(i);
  return buffer;
};

const FALLBACK_CARDS = [
  { id: 'fb1', label: 'Education First', labelColor: '#22d3ee', title: 'Student Loan', subtitle: 'Up to ₦500k', gradient: ['#0B0C10', '#1A1B23'], cta: 'APPLY NOW', ctaRoute: 'loans', reasoning: 'Zero interest for the first 3 months. Apply instantly to secure your tuition fees.' },
  { id: 'fb2', label: 'High Yield', labelColor: '#6EE7B7', title: 'Fixed Deposit', subtitle: '15% Interest', gradient: ['#0f766e', '#0d5e56'], cta: 'START SAVING', ctaRoute: 'savings', reasoning: 'Lock in your funds and earn 15% annual returns.' },
  { id: 'fb3', label: 'Flexible', labelColor: '#a78bfa', title: 'Credit Card', subtitle: 'Pre-approved', gradient: ['#7c3aed', '#4c1d95'], cta: 'GET CARD', ctaRoute: '#', reasoning: 'Based on your spending patterns, you qualify for our premium credit card.' },
];

const styleMap = {
  'Student Loan':    { grad: ['#155e2f', '#14532d'], label: 'Education First',      labelColor: '#22d3ee' },
  'Car Loan':        { grad: ['#1d4ed8', '#1e1b4b'], label: 'Lifestyle',            labelColor: '#93c5fd' },
  'Fixed Deposit':   { grad: ['#0f766e', '#0d5e56'], label: 'Grow Wealth',          labelColor: '#6ee7b7' },
  'Credit Card':     { grad: ['#7c3aed', '#4c1d95'], label: 'Flexible',             labelColor: '#c4b5fd' },
  'Investment Plan': { grad: ['#1d4ed8', '#1e3a8a'], label: 'Smart Investing',      labelColor: '#93c5fd' },
  'Trust Fund':      { grad: ['#5b21b6', '#3b0764'], label: 'Wealth Preservation',  labelColor: '#a78bfa' },
  'Personal Loan':   { grad: ['#b45309', '#7c2d12'], label: 'Quick Cash',           labelColor: '#fdba74' },
  'Savings Plan':    { grad: ['#0f766e', '#064e3b'], label: 'Save Smart',           labelColor: '#6ee7b7' },
  'Mortgage':        { grad: ['#1e40af', '#1e3a5f'], label: 'Home Ownership',       labelColor: '#7dd3fc' },
  'Insurance':       { grad: ['#6d28d9', '#4c1d95'], label: 'Stay Protected',       labelColor: '#ddd6fe' },
};

const getSubtitle = (product, emi) => {
  const amount = (emi || 0) * 10;
  if (amount > 0) return `Up to ₦${amount.toLocaleString()}`;
  const fallbacks = {
    'Student Loan':    'Zero interest for 3 months',
    'Car Loan':        'Flexible repayment plans',
    'Fixed Deposit':   'Up to 15% annual returns',
    'Credit Card':     'Pre-approved for you',
    'Investment Plan': 'Tailored to your goals',
    'Savings Plan':    'Start saving today',
    'Personal Loan':   'Quick approval process',
    'Mortgage':        'Affordable monthly payments',
    'Insurance':       'Comprehensive coverage',
    'Trust Fund':      'Wealth preservation plan',
  };
  return fallbacks[product] || 'Personalized for you';
};

const InjectStyles = () => (
  <style>{`
    @keyframes slideLeft {
      0%   { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }
    .marquee-track {
      display: flex;
      width: max-content;
      gap: 1rem;
      animation: slideLeft 22s linear infinite;
    }
    .marquee-track:hover { animation-play-state: paused; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(12px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fu  { animation: fadeUp 0.38s ease both; }
    .fu1 { animation-delay: 0.04s; }
    .fu2 { animation-delay: 0.10s; }
    .fu3 { animation-delay: 0.18s; }
    .fu4 { animation-delay: 0.26s; }
    .fu5 { animation-delay: 0.34s; }
  `}</style>
);

let _cachedFeedCards = null;

const HomeScreen = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const user = useSelector((state) => state.auth.user);
  const account = useSelector((state) => state.account?.details);
  const showPopup = useSelector((state) => state.ui.showWelcome);

  const [showBal, setShowBal] = useState(true);
  const [feedCards, setFeedCards] = useState(_cachedFeedCards || []);
  const [loadingFeed, setLoadingFeed] = useState(!_cachedFeedCards);

  const [sentinelAlert, setSentinelAlert] = useState(null);
  const [confirmStep, setConfirmStep] = useState('idle');
  const [password, setPassword] = useState('');
  const [confirmError, setConfirmError] = useState('');

  const displayCards = feedCards.length > 0 ? feedCards : FALLBACK_CARDS;
  const popupCard = displayCards[0];

  useEffect(() => {
    dispatch(fetchDashboard());

    if (_cachedFeedCards) {
      setFeedCards(_cachedFeedCards);
      setLoadingFeed(false);
      return;
    }

    const loadFeed = async () => {
      try {
        const res = await api.getSmartFeed();
        const data = res?.data || {};
        console.log('[SmartFeed] Raw response:', JSON.stringify(data, null, 2));
        let cards = data.cards || [];

        if (cards.length > 0) {
          cards = cards.map(card => {
            const style = styleMap[card.title];
            return {
              ...card,
              gradient:   style?.grad      || card.gradient || ['#1d4ed8', '#1e3a8a'],
              label:      card.label       || style?.label  || card.title,
              labelColor: style?.labelColor || card.labelColor || '#ffffff',
              subtitle:   card.subtitle?.includes('₦0')
                ? getSubtitle(card.title, 0)
                : card.subtitle || getSubtitle(card.title, 0),
            };
          });
          _cachedFeedCards = cards;
          setFeedCards(cards);
          return;
        }

        if (data.recommendations?.primary_product) {
          const rec = data.recommendations;
          const product = rec.primary_product;
          const style = styleMap[product] || { grad: ['#1d4ed8', '#1e3a8a'], label: 'Special Offer', labelColor: '#93c5fd' };
          const builtCard = [{
            id: `rec-${Date.now()}`,
            label:      style.label,
            labelColor: style.labelColor,
            title:      product,
            subtitle:   getSubtitle(product, rec.monthly_emi),
            cta:        'APPLY NOW',
            ctaRoute:   'loans',
            gradient:   style.grad,
            reasoning:  rec.reasoning || 'Based on your financial profile, we think this is a great fit for you.',
          }];
          console.log('[SmartFeed] Built card from recommendations:', product);
          _cachedFeedCards = builtCard;
          setFeedCards(builtCard);
        }

      } catch (err) {
        console.warn('Smart feed unavailable, using fallback cards:', err?.message || err);
      } finally {
        setLoadingFeed(false);
      }
    };

    loadFeed();
  }, [dispatch, user?.id]);

  useEffect(() => {
    const checkPending = () => {
      const raw = localStorage.getItem('sentinel_pending_txn');
      if (raw) {
        try {
          const data = JSON.parse(raw);
          setSentinelAlert(prev => {
            if (prev?.transaction_id === data.transaction_id) return prev;
            return data;
          });
          setConfirmStep(prev => (prev === 'idle' || prev === 'success') ? 'idle' : prev);
        } catch { /* ignore */ }
      }
    };
    checkPending();
    const interval = setInterval(checkPending, 2000);
    const onStorage = (e) => { if (e.key === 'sentinel_pending_txn') checkPending(); };
    window.addEventListener('storage', onStorage);
    return () => { clearInterval(interval); window.removeEventListener('storage', onStorage); };
  }, []);

  useEffect(() => {
    if (showPopup && popupCard) {
      const timer = setTimeout(() => dispatch(dismissWelcome()), 7000);
      return () => clearTimeout(timer);
    }
  }, [showPopup, popupCard, dispatch]);

  const quickItems = [
    { icon: Smartphone, label: "Airtime",     route: "airtime" },
    { icon: Wifi,       label: "Data",        route: "data" },
    { icon: Gamepad2,   label: "Betting",     route: "betting" },
    { icon: Zap,        label: "Electricity", route: "bills" },
  ];

  const approveTransaction = async (method, pwd) => {
    try {
      await api.confirmTransaction({
        transaction_id: sentinelAlert.transaction_id,
        password: pwd || 'biometric_verified'
      });
      setConfirmStep('success');
      localStorage.removeItem('sentinel_pending_txn');
      localStorage.setItem('sentinel_txn_result', JSON.stringify({
        status: 'APPROVED',
        transaction_id: sentinelAlert.transaction_id,
        method,
      }));
      setTimeout(() => { setSentinelAlert(null); setConfirmStep('idle'); dispatch(fetchDashboard()); }, 3000);
    } catch (err) {
      setConfirmStep('password');
      setConfirmError(err?.detail || 'Verification failed. Please enter password.');
    }
  };

  const handleConfirmTransaction = async () => {
    if (!sentinelAlert) return;
    setConfirmError('');
    setConfirmStep('scanning');

    if (window.PublicKeyCredential && typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function') {
      try {
        const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        if (available) {
          const credentialIdBase64 = localStorage.getItem('sentinel_biometric_id');
          const challenge = new Uint8Array(32);
          window.crypto.getRandomValues(challenge);

          if (credentialIdBase64) {
            await navigator.credentials.get({
              publicKey: {
                challenge, timeout: 60000, userVerification: 'required',
                rpId: window.location.hostname,
                allowCredentials: [{ type: 'public-key', id: base64urlToBuffer(credentialIdBase64), transports: ['internal'] }],
              }
            });
          } else {
            const userId = new Uint8Array(16);
            window.crypto.getRandomValues(userId);
            const cred = await navigator.credentials.create({
              publicKey: {
                challenge,
                rp: { name: "Sentinel Banking", id: window.location.hostname },
                user: { id: userId, name: "user_sentinel", displayName: user?.name || "Sentinel User" },
                pubKeyCredParams: [{ type: "public-key", alg: -7 }, { type: "public-key", alg: -257 }],
                authenticatorSelection: { authenticatorAttachment: "platform", userVerification: "required" },
                timeout: 60000, attestation: "none"
              }
            });
            localStorage.setItem('sentinel_biometric_id', bufferToBase64url(cred.rawId));
          }
          await approveTransaction('biometric');
          return;
        }
      } catch (bioErr) {
        if (bioErr.name === 'NotAllowedError') { setConfirmStep('idle'); return; }
        console.warn('Native biometric failed:', bioErr);
      }
    }
    setTimeout(() => setConfirmStep('password'), 2000);
  };

  const handlePasswordConfirm = async () => {
    if (!password.trim()) { setConfirmError('Please enter your password.'); return; }
    setConfirmStep('verifying');
    setConfirmError('');
    try {
      await approveTransaction('password', password);
    } catch (err) {
      setConfirmStep('password');
      setConfirmError(err?.detail || 'Invalid password. Please try again.');
    }
  };

  const handleRejectTransaction = () => {
    localStorage.removeItem('sentinel_pending_txn');
    localStorage.setItem('sentinel_txn_result', JSON.stringify({
      status: 'REJECTED',
      transaction_id: sentinelAlert?.transaction_id,
      method: 'user_rejected'
    }));
    setConfirmStep('rejected');
    setTimeout(() => { setSentinelAlert(null); setConfirmStep('idle'); }, 2500);
  };

  return (
    <div className="min-h-full w-full bg-vault-light-bg dark:bg-vault-dark-bg font-sans relative vault-transition">
      <InjectStyles />

      {sentinelAlert && confirmStep !== 'success' && confirmStep !== 'rejected' && (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" style={{ animation: 'fadeUp 0.3s ease' }}>
          <div className="relative w-[min(92vw,380px)] max-h-[90dvh] flex flex-col bg-white dark:bg-vault-dark-card rounded-[28px] shadow-2xl overflow-hidden border border-gray-100 dark:border-white/5" onClick={e => e.stopPropagation()}>
            <div className="vault-gradient px-6 py-5 text-white shrink-0">
              <div className="flex items-center gap-3 mb-1">
                <ShieldAlert size={24} />
                <h3 className="text-lg font-black">SENTINEL ALERT</h3>
              </div>
              <p className="text-white/80 text-xs font-medium">Suspicious Transaction Detected</p>
            </div>

            <div className="p-6 space-y-4 overflow-y-auto">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 dark:text-slate-500 font-bold">Merchant</span>
                  <span className="font-black text-gray-900 dark:text-white">{sentinelAlert.merchant || 'Unknown'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 dark:text-slate-500 font-bold">Amount</span>
                  <span className="font-black vault-gradient-text">₦{Number(sentinelAlert.amount || 0).toLocaleString('en-NG')}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 dark:text-slate-500 font-bold">Time</span>
                  <span className="font-bold text-gray-700 dark:text-slate-300">{sentinelAlert.time || new Date().toLocaleTimeString()}</span>
                </div>
              </div>

              <div className="bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl p-4">
                <p className="text-[10px] font-black text-amber-600 dark:text-amber-400 uppercase tracking-wider mb-2">Sentinel AI says:</p>
                <p className="text-xs text-amber-900 dark:text-amber-200 leading-relaxed font-medium">
                  {sentinelAlert.fraud_analysis?.policy_explanation ||
                    sentinelAlert.fraud_analysis?.reasoning ||
                    `"This transaction is unusual because it is the first time you are paying ${sentinelAlert.merchant || 'this merchant'} and it occurred at an unusual hour."`}
                </p>
                {sentinelAlert.fraud_analysis?.total_risk_score != null && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400">Risk Score:</span>
                    <div className="flex-1 h-1.5 bg-amber-200 dark:bg-amber-900/50 rounded-full overflow-hidden">
                      <div className="h-full bg-red-500 rounded-full" style={{ width: `${Math.min(sentinelAlert.fraud_analysis.total_risk_score, 100)}%` }} />
                    </div>
                    <span className="text-[10px] font-bold text-red-600 dark:text-red-400">{Math.round(sentinelAlert.fraud_analysis.total_risk_score)}%</span>
                  </div>
                )}
              </div>

              {confirmStep === 'password' && (
                <div className="space-y-3">
                  <p className="text-xs font-bold text-gray-500 dark:text-slate-400">Enter your password to confirm:</p>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500" />
                    <input
                      type="password" value={password} onChange={e => setPassword(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handlePasswordConfirm()}
                      placeholder="Your password"
                      className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-vault-dark-input border-0 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-vault-cyan/30 transition-colors text-gray-900 dark:text-white"
                      autoFocus
                    />
                  </div>
                  {confirmError && <p className="text-xs text-red-500 dark:text-red-400 font-bold">{confirmError}</p>}
                  <button onClick={handlePasswordConfirm} className="w-full vault-gradient text-white py-3.5 rounded-xl font-bold text-sm active:scale-95 transition-all mt-2 vault-glow">Confirm with Password</button>
                  <button onClick={handleRejectTransaction} className="w-full flex items-center justify-center gap-2 bg-white dark:bg-white/5 text-gray-600 dark:text-slate-300 py-3.5 rounded-xl font-bold text-sm border border-gray-200 dark:border-white/5 active:scale-95 transition-all">
                    <XCircle size={18} /> Cancel
                  </button>
                </div>
              )}

              {confirmStep === 'verifying' && (
                <div className="flex flex-col items-center py-4 gap-3">
                  <Loader2 size={28} className="text-vault-cyan animate-spin" />
                  <p className="text-sm font-bold text-gray-700 dark:text-white">Verifying...</p>
                </div>
              )}

              {confirmStep === 'scanning' && (
                <div className="flex flex-col items-center py-6 gap-4">
                  <div className="relative flex items-center justify-center">
                    <div className="absolute w-24 h-24 rounded-full border-2 border-vault-cyan/20 animate-ping" />
                    <div className="absolute w-20 h-20 rounded-full border border-vault-cyan/30 animate-pulse" />
                    <div className="relative z-10 w-16 h-16 rounded-full bg-vault-cyan/10 dark:bg-vault-cyan/10 flex items-center justify-center text-vault-cyan">
                      <Fingerprint size={32} className="animate-pulse" />
                    </div>
                  </div>
                  <p className="text-sm font-bold text-vault-cyan animate-pulse">Scanning Biometrics...</p>
                  <p className="text-[10px] text-gray-400 dark:text-slate-500 text-center px-4">Use your fingerprint or Face ID to confirm</p>
                </div>
              )}

              {confirmStep === 'idle' && (
                <div className="space-y-3">
                  <button onClick={handleConfirmTransaction} className="w-full flex items-center justify-center gap-2.5 vault-gradient text-white py-4 rounded-xl font-bold text-sm shadow-lg vault-glow active:scale-95 transition-all">
                    <Fingerprint size={20} /> Confirm with Biometric
                  </button>
                  <button onClick={handleRejectTransaction} className="w-full flex items-center justify-center gap-2 bg-white dark:bg-white/5 text-gray-600 dark:text-slate-300 py-3.5 rounded-xl font-bold text-sm border border-gray-200 dark:border-white/5 active:scale-95 transition-all">
                    <XCircle size={18} /> Reject
                  </button>
                  <button onClick={() => setConfirmStep('password')} className="w-full text-center text-xs text-gray-400 dark:text-slate-500 font-bold mt-2 hover:underline">
                    Use Password instead
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {sentinelAlert && confirmStep === 'success' && (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="text-center text-white space-y-4" style={{ animation: 'fadeUp 0.3s ease' }}>
            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto shadow-xl">
              <CheckCircle size={40} />
            </div>
            <h3 className="text-2xl font-black">Transaction Approved</h3>
            <p className="text-white/70 text-sm">Securely authorized via Sentinel</p>
          </div>
        </div>
      )}

      {sentinelAlert && confirmStep === 'rejected' && (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="text-center text-white space-y-4" style={{ animation: 'fadeUp 0.3s ease' }}>
            <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto shadow-xl">
              <XCircle size={40} />
            </div>
            <h3 className="text-2xl font-black">Transaction Rejected</h3>
            <p className="text-white/70 text-sm">The transaction has been blocked</p>
          </div>
        </div>
      )}

      {showPopup && popupCard && !sentinelAlert && (
        <div
          className="fixed top-0 left-0 right-0 bottom-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) dispatch(dismissWelcome()); }}
        >
          <div
            className="relative text-white shadow-2xl border border-white/10"
            style={{
              background: `linear-gradient(to bottom right, ${popupCard.gradient?.[0] || '#1d4ed8'}, ${popupCard.gradient?.[1] || '#1e3a8a'})`,
              width: "min(92vw, 360px)",
              borderRadius: "28px",
              padding: "clamp(20px, 4vw, 28px)"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => dispatch(dismissWelcome())}
              className="absolute top-4 right-4 w-8 h-8 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 active:scale-90 transition-all z-20"
            >
              <X size={16} />
            </button>
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
            <div className="relative z-10">
              <span className="text-[10px] font-bold uppercase tracking-wider mb-2 block" style={{ color: popupCard.labelColor || '#22d3ee' }}>
                {popupCard.label}
              </span>
              <h3 className="text-xl sm:text-2xl font-black leading-tight mb-2">{popupCard.title}<br />{popupCard.subtitle}</h3>
              <p className="text-white/80 text-xs mb-6 leading-relaxed flex items-start gap-1">
                <Sparkles size={14} className="shrink-0 mt-0.5 text-yellow-300" />
                {popupCard.reasoning || "Based on your recent activity, we recommend this offer."}
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => { dispatch(dismissWelcome()); navigate(popupCard.ctaRoute || '#'); }}
                  className="w-full bg-white text-xs font-extrabold py-3.5 rounded-full shadow-lg active:scale-95 hover:shadow-xl transition-all"
                  style={{ color: popupCard.gradient?.[0] || '#1d4ed8' }}
                >
                  {popupCard.cta}
                </button>
                <button
                  type="button"
                  onClick={() => dispatch(dismissWelcome())}
                  className="w-full text-white/50 text-[10px] font-bold uppercase tracking-widest hover:text-white transition-colors py-1 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="w-full bg-gradient-to-br from-[#00b4d8] via-[#5b4bdb] to-[#7c3aed] text-white px-4 sm:px-6 xl:px-8 pt-8 pb-6 rounded-b-[32px] shadow-lg mb-6 relative z-20 overflow-hidden">
        <div className="absolute -top-20 -right-20 w-60 h-60 bg-vault-cyan/15 rounded-full blur-[80px] pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-vault-purple/15 rounded-full blur-[60px] pointer-events-none" />
        
        <div className="flex justify-between items-center mb-6 fu fu1 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full overflow-hidden shrink-0 bg-white/10 border-2 border-white/20">
              <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'Lukman'}`} alt="User" className="w-full h-full object-cover" />
            </div>
            <div>
              <p className="text-white/70 text-[13px] font-medium leading-none mb-1">Good Afternoon</p>
              <h2 className="text-lg font-bold leading-tight">{user?.name}</h2>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors">
              <Bell size={22} />
              <span className="absolute top-2 right-2.5 w-2 h-2 bg-vault-cyan rounded-full border border-slate-800 dark:border-vault-dark-bg" />
            </button>
            <button className="w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors">
              <Settings size={22} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-4 fu fu2 relative z-10">
          <span className="text-white/60 text-[12px] sm:text-[13px] font-medium">
            Tier {account?.tier} Savings Account | <span className="text-white font-bold">{account?.number}</span>
          </span>
          <button className="text-white hover:text-white/80 transition-colors"><Copy size={16} /></button>
        </div>

        <div className="vault-glass rounded-2xl p-5 relative fu fu3">
          <div className="absolute top-0 right-0 bg-vault-cyan text-vault-dark-bg text-[11px] font-bold px-3 py-1 rounded-bl-[14px] rounded-tr-[14px]">Active</div>
          <p className="text-white/70 text-sm font-medium mb-1.5">Account Balance</p>
          <div className="flex items-center gap-2 mb-6">
            <h1 className="text-4xl font-extrabold tracking-tight">
              {showBal ? `₦${Number(account?.balance ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "••••••••"}
            </h1>
            <button onClick={() => setShowBal(!showBal)} className="text-white/80 hover:text-white transition-colors focus:outline-none">
              {showBal ? <EyeOff size={22} /> : <Eye size={22} />}
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3 pt-2">
            <button onClick={() => navigate('/fund')} className="w-full flex items-center justify-center gap-2 py-3 bg-transparent border border-white/30 shadow-sm rounded-xl hover:bg-white/10 transition-colors font-semibold text-sm">
              <Plus size={18} /> Fund Account
            </button>
            <button onClick={() => navigate('/history')} className="w-full flex items-center justify-center gap-2 py-3 bg-transparent border border-white/30 shadow-sm rounded-xl hover:bg-white/10 transition-colors font-semibold text-sm">
              <FileText size={18} /> History
            </button>
          </div>
        </div>
      </div>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-2 pb-28 space-y-6">

        <div className="fu fu3 grid grid-cols-3 gap-3 sm:gap-4 xl:gap-6 w-full">
          <button onClick={() => navigate('/send')} className="w-full h-full min-h-[85px] md:min-h-[100px] vault-gradient rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-white shadow-xl vault-glow active:scale-95 hover:scale-[1.03] transition-transform p-3">
            <Send className="w-6 h-6 md:w-8 md:h-8" />
            <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate">Send</span>
          </button>
          <button onClick={() => navigate('/bills')} className="w-full h-full min-h-[85px] md:min-h-[100px] bg-white dark:bg-vault-dark-card rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-vault-cyan shadow-sm dark:shadow-none border border-gray-100 dark:border-white/5 active:scale-95 hover:scale-[1.03] transition-transform p-3">
            <FileText className="w-6 h-6 md:w-8 md:h-8" />
            <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate text-gray-700 dark:text-white">Pay Bills</span>
          </button>
          <button onClick={() => navigate('#')} className="w-full h-full min-h-[85px] md:min-h-[100px] bg-white dark:bg-vault-dark-card rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-vault-purple shadow-sm dark:shadow-none border border-gray-100 dark:border-white/5 active:scale-95 hover:scale-[1.03] transition-transform p-3">
            <QrCode className="w-6 h-6 md:w-8 md:h-8" />
            <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate text-gray-700 dark:text-white">Cards</span>
          </button>
        </div>

        <div className="fu fu4">
          <div className="flex justify-between items-center mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm md:text-base xl:text-lg">Quick Access</h3>
            <span className="text-xs md:text-sm font-bold text-vault-cyan cursor-pointer hover:underline">View All</span>
          </div>
          <div className="grid grid-cols-4 gap-3 md:gap-5 xl:gap-8">
            {quickItems.map((item, idx) => (
              <div key={idx} onClick={() => navigate(item.route)} className="flex flex-col items-center gap-2 xl:gap-3 cursor-pointer group">
                <div className="w-14 h-14 sm:w-16 sm:h-16 xl:w-20 xl:h-20 bg-vault-cyan/10 dark:bg-vault-cyan/10 rounded-[20px] xl:rounded-[24px] flex items-center justify-center text-vault-cyan group-hover:bg-vault-cyan/20 group-active:scale-90 transition-all">
                  <item.icon className="w-6 h-6 xl:w-8 xl:h-8" />
                </div>
                <span className="text-[10px] sm:text-xs md:text-sm font-bold text-gray-500 dark:text-slate-400 text-center">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="fu fu5 overflow-hidden pb-2">
          <div className="flex items-center gap-2 mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm md:text-base xl:text-lg">Smart Feed</h3>
            <span className="vault-gradient text-white text-[9px] md:text-[10px] font-black px-2.5 py-0.5 rounded-md uppercase tracking-wide">AI Powered</span>
          </div>
          <div className="relative w-full overflow-hidden">
            {loadingFeed ? (
              <div className="flex gap-4">
                {[1, 2].map(i => <div key={i} className="w-[240px] h-[145px] bg-gray-100 dark:bg-vault-dark-card rounded-[24px] animate-pulse"></div>)}
              </div>
            ) : (
              <div className="marquee-track">
                {[...displayCards, ...displayCards].map((card, i) => (
                  <div
                    key={`${card.id}-${i}`}
                    className="w-[240px] sm:w-[280px] xl:w-[300px] h-[145px] xl:h-[160px] rounded-[24px] sm:rounded-[28px] p-5 sm:p-6 text-white flex flex-col justify-between shrink-0 shadow-lg relative overflow-hidden"
                    style={{ background: `linear-gradient(135deg, ${card.gradient?.[0] || '#1d4ed8'}, ${card.gradient?.[1] || '#1e3a8a'})` }}
                  >
                    <div className="absolute right-0 top-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider mb-1.5 block" style={{ color: card.labelColor || '#fff' }}>
                        {card.label}
                      </span>
                      <h3 className="text-lg sm:text-xl font-bold leading-tight">{card.title}<br />{card.subtitle}</h3>
                    </div>
                    <button
                      onClick={() => card.ctaRoute && navigate(card.ctaRoute)}
                      className="bg-white text-[10px] font-bold px-5 py-2.5 rounded-full w-fit hover:shadow-md active:scale-95 transition-all"
                      style={{ color: card.gradient?.[0] || '#1d4ed8' }}
                    >
                      {card.cta}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default HomeScreen;