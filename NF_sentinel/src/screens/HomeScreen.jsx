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

// ─── WebAuthn Base64 Helpers ──────────────────────────────────────────
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

// ─── Fallback cards when trajectory API returns empty ───────────────────
const FALLBACK_CARDS = [
  { id: 'fb1', label: 'Education First', labelColor: '#FFD700', title: 'Student Loan', subtitle: 'Up to ₦500k', gradient: ['#2F4F4F', '#1A2E2E'], cta: 'APPLY NOW', ctaRoute: 'loans', reasoning: 'Zero interest for the first 3 months. Apply instantly to secure your tuition fees.' },
  { id: 'fb2', label: 'High Yield', labelColor: '#6EE7B7', title: 'Fixed Deposit', subtitle: '15% Interest', gradient: ['#0F766E', '#0D5E56'], cta: 'START SAVING', ctaRoute: 'savings', reasoning: 'Lock in your funds and earn 15% annual returns.' },
  { id: 'fb3', label: 'Flexible', labelColor: '#C4B5FD', title: 'Credit Card', subtitle: 'Pre-approved', gradient: ['#7c3aed', '#4c1d95'], cta: 'GET CARD', ctaRoute: '#', reasoning: 'Based on your spending patterns, you qualify for our premium credit card.' },
];

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

const HomeScreen = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const user = useSelector((state) => state.auth.user);
  const account = useSelector((state) => state.account?.details);
  const showPopup = useSelector((state) => state.ui.showWelcome);

  const [showBal, setShowBal] = useState(true);
  const [feedCards, setFeedCards] = useState([]);
  const [loadingFeed, setLoadingFeed] = useState(true);

  // ── Sentinel Alert state ──────────────────────────────────────────
  const [sentinelAlert, setSentinelAlert] = useState(null);
  const [confirmStep, setConfirmStep] = useState('idle'); // idle | password | verifying | success | rejected
  const [password, setPassword] = useState('');
  const [confirmError, setConfirmError] = useState('');

  // Use the first card from trajectory for the popup (fallback if empty)
  const displayCards = feedCards.length > 0 ? feedCards : FALLBACK_CARDS;
  const popupCard = displayCards[0];

  useEffect(() => {
    dispatch(fetchDashboard());

    const loadFeed = async () => {
      try {
        const res = await api.getSmartFeed();
        const data = res?.data || {};
        console.log('[SmartFeed] Raw response:', JSON.stringify(data, null, 2));
        let cards = data.cards || [];

        // Style map covering all possible product types from trajectory agent
        const styleMap = {
          'Student Loan': { grad: ['#2F4F4F', '#1a2e2e'], label: 'Education First', labelColor: '#ffd700' },
          'Car Loan': { grad: ['#1e3a8a', '#1e1b4b'], label: 'Lifestyle', labelColor: '#93c5fd' },
          'Fixed Deposit': { grad: ['#065f46', '#064e3b'], label: 'Grow Wealth', labelColor: '#6ee7b7' },
          'Credit Card': { grad: ['#7c3aed', '#4c1d95'], label: 'Flexible', labelColor: '#c4b5fd' },
          'Investment Plan': { grad: ['#0f172a', '#1e293b'], label: 'Smart Investing', labelColor: '#38bdf8' }, // ← ADD
          'Trust Fund': { grad: ['#1a1a2e', '#16213e'], label: 'Wealth Preservation', labelColor: '#a78bfa' }, // ← ADD
          'Personal Loan': { grad: ['#7c2d12', '#431407'], label: 'Quick Cash', labelColor: '#fdba74' }, // ← ADD
          'Savings Plan': { grad: ['#065f46', '#064e3b'], label: 'Save Smart', labelColor: '#6ee7b7' },
          'Mortgage': { grad: ['#1e3a5f', '#0c1929'], label: 'Home Ownership', labelColor: '#7dd3fc' },
          'Insurance': { grad: ['#4a1d96', '#2e1065'], label: 'Stay Protected', labelColor: '#ddd6fe' },
        };

        // Helper: generate a meaningful subtitle for a product
        const getSubtitle = (product, emi) => {
          const amount = (emi || 0) * 10;
          if (amount > 0) return `Up to ₦${amount.toLocaleString()}`;
          // Fallback subtitles when no EMI data is available
          const fallbacks = {
            'Student Loan': 'Zero interest for 3 months',
            'Car Loan': 'Flexible repayment plans',
            'Fixed Deposit': 'Up to 15% annual returns',
            'Credit Card': 'Pre-approved for you',
            'Investment Plan': 'Tailored to your goals',
            'Savings Plan': 'Start saving today',
            'Personal Loan': 'Quick approval process',
            'Mortgage': 'Affordable monthly payments',
            'Insurance': 'Comprehensive coverage',
          };
          return fallbacks[product] || 'Personalized for you';
        };

        // If backend returned empty cards but has recommendation data with primary_product,
        // build a card from it on the frontend
        if ((!Array.isArray(cards) || cards.length === 0) && data.recommendations?.primary_product) {
          let cards = data.cards || [];

          // if backend says no_recommendation but product exists, build card anyway
          if (data.status === "no_recommendation" && data.recommendations?.primary_product) {
            const rec = data.recommendations;
            const product = rec.primary_product;
            const style = styleMap[product] || { grad: ['#111827', '#1f2937'], label: 'Special Offer', labelColor: '#fcd34d' };
            cards = [{
              id: `rec-${Date.now()}`,
              label: style.label,
              labelColor: style.labelColor,
              title: product,
              subtitle: getSubtitle(product, rec.monthly_emi),
              cta: 'APPLY NOW',
              ctaRoute: 'loans',
              gradient: style.grad,
              reasoning: rec.reasoning || 'Based on your financial profile, we think this is a great fit for you.',
            }];
          }

            console.log('[SmartFeed] Built card from recommendations.primary_product:', product);
          }

          // Post-process cards from backend that may have "Up to ₦0" subtitle
          if (Array.isArray(cards) && cards.length > 0) {
            cards = cards.map(card => {
              if (card.subtitle && card.subtitle.includes('₦0')) {
                const style = styleMap[card.title];
                return { ...card, subtitle: getSubtitle(card.title, 0), ...(style ? { labelColor: style.labelColor } : {}) };
              }
              return card;
            });
            setFeedCards(cards);
          }
          // If cards is still empty, fallback cards will be shown automatically
        } catch (err) {
          console.warn('Smart feed unavailable, using fallback cards:', err?.message || err);
        } finally {
          setLoadingFeed(false);
        }
      };

      loadFeed();
    }, [dispatch, user?.id]);

  // ── Poll for pending Sentinel transactions (from merchant checkout) ──
  useEffect(() => {
    const checkPending = () => {
      const raw = localStorage.getItem('sentinel_pending_txn');
      if (raw) {
        try {
          const data = JSON.parse(raw);
          // Only set alert if we don't already have one being confirmed
          setSentinelAlert(prev => {
            if (prev?.transaction_id === data.transaction_id) return prev;
            return data;
          });
          // Don't reset confirmStep if the user is actively in the confirmation flow
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
    { icon: Smartphone, label: "Airtime", route: "airtime" },
    { icon: Wifi, label: "Data", route: "data" },
    { icon: Gamepad2, label: "Betting", route: "betting" },
    { icon: Zap, label: "Electricity", route: "bills" },
  ];

  // ── Biometric / password confirmation handler ─────────────────────
  const handleConfirmTransaction = async () => {
    if (!sentinelAlert) return;
    setConfirmError('');
    setConfirmStep('scanning');

    const approveTransaction = async () => {
      try {
        await api.confirmTransaction({
          transaction_id: sentinelAlert.transaction_id,
          password: user?.password || 'biometric_verified'
        });
        setConfirmStep('success');
        localStorage.removeItem('sentinel_pending_txn');
        localStorage.setItem('sentinel_txn_result', JSON.stringify({
          status: 'APPROVED',
          transaction_id: sentinelAlert.transaction_id,
          method: 'biometric'
        }));
        setTimeout(() => { setSentinelAlert(null); setConfirmStep('idle'); dispatch(fetchDashboard()); }, 3000);
      } catch (err) {
        setConfirmStep('password');
        setConfirmError(err?.detail || 'Verification failed. Please enter password.');
      }
    };

    // Try Web Authentication API (biometric) first
    if (window.PublicKeyCredential && typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function') {
      try {
        const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        if (available) {
          const credentialIdBase64 = localStorage.getItem('sentinel_biometric_id');
          const challenge = new Uint8Array(32);
          window.crypto.getRandomValues(challenge);

          if (credentialIdBase64) {
            // Trigger native biometric prompt using the specifically created local credential
            await navigator.credentials.get({
              publicKey: {
                challenge,
                timeout: 60000,
                userVerification: 'required',
                rpId: window.location.hostname,
                allowCredentials: [{
                  type: 'public-key',
                  id: base64urlToBuffer(credentialIdBase64),
                  transports: ['internal']
                }],
              }
            });
          } else {
            // Create a credential to bind to the device's biometrics locally
            const userId = new Uint8Array(16);
            window.crypto.getRandomValues(userId);
            const cred = await navigator.credentials.create({
              publicKey: {
                challenge,
                rp: { name: "Sentinel Banking", id: window.location.hostname },
                user: { id: userId, name: "user_sentinel", displayName: user?.name || "Sentinel User" },
                pubKeyCredParams: [{ type: "public-key", alg: -7 }, { type: "public-key", alg: -257 }],
                authenticatorSelection: { authenticatorAttachment: "platform", userVerification: "required" },
                timeout: 60000,
                attestation: "none"
              }
            });
            localStorage.setItem('sentinel_biometric_id', bufferToBase64url(cred.rawId));
          }
          await approveTransaction();
          return;
        }
      } catch (bioErr) {
        if (bioErr.name === 'NotAllowedError') {
          // User explicitly cancelled or failed native prompt
          setConfirmStep('idle');
          return;
        }
        console.warn('Native biometric failed, falling through to simulation:', bioErr);
      }
    }

    // Fallback: no biometric available — visually simulate scanning then go to password entry
    setTimeout(() => {
      setConfirmStep('password');
    }, 2000);
  };

  const handlePasswordConfirm = async () => {
    if (!password.trim()) { setConfirmError('Please enter your password.'); return; }
    setConfirmStep('verifying');
    setConfirmError('');
    try {
      await api.confirmTransaction({
        transaction_id: sentinelAlert.transaction_id,
        password: password
      });
      setConfirmStep('success');
      localStorage.removeItem('sentinel_pending_txn');
      localStorage.setItem('sentinel_txn_result', JSON.stringify({
        status: 'APPROVED',
        transaction_id: sentinelAlert.transaction_id,
        method: 'password'
      }));
      setTimeout(() => { setSentinelAlert(null); setConfirmStep('idle'); setPassword(''); dispatch(fetchDashboard()); }, 3000);
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
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans relative">
      <InjectStyles />

      {/* ═══ SENTINEL ALERT MODAL ══════════════════════════════════════════ */}
      {sentinelAlert && confirmStep !== 'success' && confirmStep !== 'rejected' && (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" style={{ animation: 'fadeUp 0.3s ease' }}>
          <div className="relative w-[min(92vw,380px)] max-h-[90dvh] flex flex-col bg-white rounded-[28px] shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
            {/* Red top banner */}
            <div className="bg-gradient-to-r from-[#A01030] to-[#6B0A20] px-6 py-5 text-white shrink-0">
              <div className="flex items-center gap-3 mb-1">
                <ShieldAlert size={24} />
                <h3 className="text-lg font-black">SENTINNEL ALERT</h3>
              </div>
              <p className="text-white/80 text-xs font-medium">Suspicious Transaction Detected</p>
            </div>

            <div className="p-6 space-y-4 overflow-y-auto">
              {/* Transaction details */}
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 font-bold">Merchant</span>
                  <span className="font-black text-gray-900">{sentinelAlert.merchant || 'Unknown'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 font-bold">Amount</span>
                  <span className="font-black text-[#A01030]">₦{Number(sentinelAlert.amount || 0).toLocaleString('en-NG')}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 font-bold">Time</span>
                  <span className="font-bold text-gray-700">{sentinelAlert.time || new Date().toLocaleTimeString()}</span>
                </div>
              </div>

              {/* AI Reasoning */}
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <p className="text-[10px] font-black text-amber-600 uppercase tracking-wider mb-2">Sentinnel AI says:</p>
                <p className="text-xs text-amber-900 leading-relaxed font-medium">
                  {sentinelAlert.fraud_analysis?.policy_explanation ||
                    sentinelAlert.fraud_analysis?.reasoning ||
                    `"This transaction is unusual because it is the first time you are paying ${sentinelAlert.merchant || 'this merchant'} and it occurred at an unusual hour."`}
                </p>
                {sentinelAlert.fraud_analysis?.total_risk_score != null && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-[10px] font-bold text-amber-600">Risk Score:</span>
                    <div className="flex-1 h-1.5 bg-amber-200 rounded-full overflow-hidden">
                      <div className="h-full bg-red-500 rounded-full" style={{ width: `${Math.min(sentinelAlert.fraud_analysis.total_risk_score, 100)}%` }} />
                    </div>
                    <span className="text-[10px] font-bold text-red-600">{Math.round(sentinelAlert.fraud_analysis.total_risk_score)}%</span>
                  </div>
                )}
              </div>

              {/* Password entry (fallback) */}
              {confirmStep === 'password' && (
                <div className="space-y-3">
                  <p className="text-xs font-bold text-gray-500">Enter your password to confirm:</p>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="password" value={password} onChange={e => setPassword(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handlePasswordConfirm()}
                      placeholder="Your password"
                      className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium outline-none focus:border-[#A01030] transition-colors"
                      autoFocus
                    />
                  </div>
                  {confirmError && <p className="text-xs text-red-500 font-bold">{confirmError}</p>}
                  <button onClick={handlePasswordConfirm} className="w-full bg-[#A01030] text-white py-3.5 rounded-xl font-bold text-sm active:scale-95 transition-all mt-2">Confirm with Password</button>
                  <button
                    onClick={handleRejectTransaction}
                    className="w-full flex items-center justify-center gap-2 bg-white text-gray-600 py-3.5 rounded-xl font-bold text-sm border border-gray-200 active:scale-95 transition-all"
                  >
                    <XCircle size={18} /> Cancel
                  </button>
                </div>
              )}

              {/* Verifying generic state */}
              {confirmStep === 'verifying' && (
                <div className="flex flex-col items-center py-4 gap-3">
                  <Loader2 size={28} className="text-[#A01030] animate-spin" />
                  <p className="text-sm font-bold text-gray-700">Verifying...</p>
                </div>
              )}

              {/* Scanning visual state (Biometric Simulation fallback) */}
              {confirmStep === 'scanning' && (
                <div className="flex flex-col items-center py-6 gap-4">
                  <div className="relative flex items-center justify-center">
                    <div className="absolute w-24 h-24 rounded-full border-2 border-[#A01030]/20 animate-ping" />
                    <div className="absolute w-20 h-20 rounded-full border border-[#A01030]/30 animate-pulse" />
                    <div className="relative z-10 w-16 h-16 rounded-full bg-red-50 flex items-center justify-center text-[#A01030]">
                      <Fingerprint size={32} className="animate-pulse" />
                    </div>
                  </div>
                  <p className="text-sm font-bold text-[#A01030] animate-pulse">Scanning Biometrics...</p>
                  <p className="text-[10px] text-gray-400 text-center px-4">Use your fingerprint or Face ID to confirm</p>
                </div>
              )}

              {/* Action buttons (initial state) */}
              {confirmStep === 'idle' && (
                <div className="space-y-3">
                  <button
                    onClick={handleConfirmTransaction}
                    className="w-full flex items-center justify-center gap-2.5 bg-[#A01030] text-white py-4 rounded-xl font-bold text-sm shadow-lg shadow-red-900/20 active:scale-95 transition-all"
                  >
                    <Fingerprint size={20} /> Confirm with Biometric
                  </button>
                  <button
                    onClick={handleRejectTransaction}
                    className="w-full flex items-center justify-center gap-2 bg-white text-gray-600 py-3.5 rounded-xl font-bold text-sm border border-gray-200 active:scale-95 transition-all"
                  >
                    <XCircle size={18} /> Reject
                  </button>
                  <button
                    onClick={() => setConfirmStep('password')}
                    className="w-full text-center text-xs text-gray-400 font-bold mt-2 hover:underline"
                  >
                    Use Password instead
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══ SENTINEL SUCCESS OVERLAY ══════════════════════════════════════ */}
      {sentinelAlert && confirmStep === 'success' && (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="text-center text-white space-y-4" style={{ animation: 'fadeUp 0.3s ease' }}>
            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto shadow-xl">
              <CheckCircle size={40} />
            </div>
            <h3 className="text-2xl font-black">Transaction Approved</h3>
            <p className="text-white/70 text-sm">Securely authorized via Sentinnel</p>
          </div>
        </div>
      )}

      {/* ═══ SENTINEL REJECTED OVERLAY ═════════════════════════════════════ */}
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

      {/* ═══ TRAJECTORY POPUP (Welcome Offer) ══════════════════════════════ */}
      {showPopup && popupCard && !sentinelAlert && (
        <div
          className="fixed top-0 left-0 right-0 bottom-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) dispatch(dismissWelcome()); }}
        >
          <div
            className="relative text-white shadow-2xl border border-white/10"
            style={{
              background: `linear-gradient(to bottom right, ${popupCard.gradient?.[0] || '#2F4F4F'}, ${popupCard.gradient?.[1] || '#1A2E2E'})`,
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
              <span className="text-[10px] font-bold uppercase tracking-wider mb-2 block" style={{ color: popupCard.labelColor || '#FFD700' }}>
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
                  style={{ color: popupCard.gradient?.[0] || '#2F4F4F' }}
                >
                  {popupCard.cta}
                </button>
                <button
                  type="button"
                  onClick={() => dispatch(dismissWelcome())}
                  className="w-full text-white/50 text-[10px] font-bold uppercase tracking-widest hover:text-white active:text-white transition-colors py-1 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Header + Balance Area */}
      <div className="w-full bg-gradient-to-br from-[#800020] via-[#A01030] to-[#5a0a1e] text-white px-4 sm:px-6 xl:px-8 pt-8 pb-6 rounded-b-[32px] shadow-lg shadow-red-900/10 mb-6 relative z-20">
        <div className="flex justify-between items-center mb-6 fu fu1">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full overflow-hidden shrink-0 bg-white/10 border-2 border-white/20">
              <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'Lukman'}`} alt="User" className="w-full h-full object-cover" />
            </div>
            <div>
              <p className="text-white/90 text-[13px] font-medium leading-none mb-1">Good Afternoon</p>
              <h2 className="text-lg font-bold leading-tight">{user?.name}</h2>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors">
              <Bell size={22} />
              <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-red-900" />
            </button>
            <button className="w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors">
              <Settings size={22} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-4 fu fu2">
          <span className="text-white/80 text-[12px] sm:text-[13px] font-medium">Tier {account?.tier} Savings Account | <span className="text-white font-bold">{account?.number}</span></span>
          <button className="text-white hover:text-white/80 transition-colors">
            <Copy size={16} />
          </button>
        </div>

        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-5 relative fu fu3">
          <div className="absolute top-0 right-0 bg-white text-green-700 text-[11px] font-bold px-3 py-1 rounded-bl-[14px] rounded-tr-[14px]">
            Active
          </div>
          <p className="text-white text-sm font-medium mb-1.5">Account Balance</p>
          <div className="flex items-center gap-2 mb-6">
            <h1 className="text-4xl font-extrabold tracking-tight">
              {showBal ? `₦${Number(account?.balance ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "••••••••"}
            </h1>
            <button onClick={() => setShowBal(!showBal)} className="text-white/80 hover:text-white transition-colors focus:outline-none">
              {showBal ? <EyeOff size={22} /> : <Eye size={22} />}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <button onClick={() => navigate('/fund')} className="w-full flex items-center justify-center gap-2 py-3 bg-transparent border border-white/50 shadow-sm rounded-xl hover:bg-white/10 transition-colors font-semibold text-sm">
              <Plus size={18} /> Fund Account
            </button>
            <button onClick={() => navigate('/history')} className="w-full flex items-center justify-center gap-2 py-3 bg-transparent border border-white/50 shadow-sm rounded-xl hover:bg-white/10 transition-colors font-semibold text-sm">
              <FileText size={18} /> History
            </button>
          </div>
        </div>
      </div>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-2 pb-28 space-y-6">

        {/* Send Action */}
        <div className="fu fu3 grid grid-cols-3 gap-3 sm:gap-4 xl:gap-6 w-full">
          <button
            onClick={() => navigate('/send')}
            className="w-full h-full min-h-[85px] md:min-h-[100px] bg-[#A01030] rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-white shadow-xl shadow-red-900/20 active:scale-95 hover:scale-[1.03] transition-transform p-3"
          >
            <Send className="w-6 h-6 md:w-8 md:h-8" />
            <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate">Send</span>
          </button>
          <button
            onClick={() => navigate('/bills')}
            className="w-full h-full min-h-[85px] md:min-h-[100px] bg-white rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-[#A01030] shadow-sm border border-gray-100 active:scale-95 hover:scale-[1.03] transition-transform p-3"
          >
            <FileText className="w-6 h-6 md:w-8 md:h-8" />
            <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate text-gray-700">Pay Bills</span>
          </button>
          <button
            onClick={() => navigate('#')}
            className="w-full h-full min-h-[85px] md:min-h-[100px] bg-white rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 text-[#A01030] shadow-sm border border-gray-100 active:scale-95 hover:scale-[1.03] transition-transform p-3"
          >
            <QrCode className="w-6 h-6 md:w-8 md:h-8" />
            <span className="text-[11px] sm:text-xs md:text-sm font-bold truncate text-gray-700">Cards</span>
          </button>
        </div>

        {/* Quick Access */}
        <div className="fu fu4">
          <div className="flex justify-between items-center mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 text-sm md:text-base xl:text-lg">Quick Access</h3>
            <span className="text-xs md:text-sm font-bold text-[#A01030] cursor-pointer hover:underline">View All</span>
          </div>
          <div className="grid grid-cols-4 gap-3 md:gap-5 xl:gap-8">
            {quickItems.map((item, idx) => (
              <div key={idx} onClick={() => navigate(item.route)} className="flex flex-col items-center gap-2 xl:gap-3 cursor-pointer group">
                <div className="w-14 h-14 sm:w-16 sm:h-16 xl:w-20 xl:h-20 bg-[#FFF5F7] rounded-[20px] xl:rounded-[24px] flex items-center justify-center text-[#A01030] group-hover:bg-rose-100 group-active:scale-90 transition-all">
                  <item.icon className="w-6 h-6 xl:w-8 xl:h-8" />
                </div>
                <span className="text-[10px] sm:text-xs md:text-sm font-bold text-gray-500 text-center">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Smart Feed */}
        <div className="fu fu5 overflow-hidden pb-2">
          <div className="flex items-center gap-2 mb-3 sm:mb-4 xl:mb-5">
            <h3 className="font-bold text-gray-900 text-sm md:text-base xl:text-lg">Smart Feed</h3>
            <span className="bg-[#FCE7F3] text-[#BE185D] text-[9px] md:text-[10px] font-black px-2 py-0.5 rounded-md uppercase tracking-wide">AI Powered</span>
          </div>
          <div className="relative w-full overflow-hidden">
            {loadingFeed ? (
              <div className="flex gap-4">
                {[1, 2].map(i => <div key={i} className="w-[240px] h-[145px] bg-gray-100 rounded-[24px] animate-pulse"></div>)}
              </div>
            ) : (
              <div className="marquee-track">
                {[...displayCards, ...displayCards].map((card, i) => (
                  <div
                    key={`${card.id}-${i}`}
                    className="w-[240px] sm:w-[280px] xl:w-[300px] h-[145px] xl:h-[160px] rounded-[24px] sm:rounded-[28px] p-5 sm:p-6 text-white flex flex-col justify-between shrink-0 shadow-lg relative overflow-hidden"
                    style={{ background: card.gradient ? `linear-gradient(to right, ${card.gradient[0]}, ${card.gradient[1]})` : '#333' }}
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
                      style={{ color: card.gradient?.[0] || '#000' }}
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