import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { dismissWelcome, triggerPayment } from "../features/uiSlice";
import { fetchDashboard } from "../features/accountSlice";
import { api } from "../api/axiosConfig";
import {
  Bell, Eye, EyeOff, Copy, QrCode, Send, Plus, Clock, FileText,
  Smartphone, Wifi, Gamepad2, Zap, Sparkles, X, Settings,
  ShieldAlert, Fingerprint, XCircle, CheckCircle, Loader2, Lock,
  BadgeCheck, ArrowRight, Calendar, TrendingUp
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
  { id: 'fb1', label: 'Education First', labelColor: '#22d3ee', title: 'Student Loan', subtitle: 'Up to ₦500k', gradient: ['#0B0C10', '#1A1B23'], cta: 'APPLY NOW', ctaRoute: 'loans', reasoning: null },
  { id: 'fb2', label: 'High Yield', labelColor: '#6EE7B7', title: 'Fixed Deposit', subtitle: '15% Interest', gradient: ['#0f766e', '#0d5e56'], cta: 'START SAVING', ctaRoute: 'savings', reasoning: null },
  { id: 'fb3', label: 'Flexible', labelColor: '#a78bfa', title: 'Credit Card', subtitle: 'Pre-approved', gradient: ['#7c3aed', '#4c1d95'], cta: 'GET CARD', ctaRoute: '#', reasoning: null },
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

// Repayment / tenure metadata per product
const repaymentMap = {
  'Student Loan':    { min: 12, max: 36,  note: 'No repayment for the first 3 months' },
  'Car Loan':        { min: 12, max: 60,  note: 'Flexible monthly instalments, no penalties for early payment' },
  'Personal Loan':   { min: 3,  max: 24,  note: 'No collateral required, disbursed within 24 hours' },
  'Mortgage':        { min: 60, max: 240, note: 'Up to 20-year tenure with fixed monthly payments' },
  'Credit Card':     { min: 1,  max: 12,  note: 'Pay as little as the monthly minimum, interest-free on full payment' },
  'Fixed Deposit':   { min: 3,  max: 24,  note: 'Full principal + interest paid at maturity' },
  'Investment Plan': { min: 6,  max: 60,  note: 'Auto-renews at maturity — withdraw anytime with 48hr notice' },
  'Savings Plan':    { min: 1,  max: 36,  note: 'Flexible contribution schedule, no lock-in' },
  'Trust Fund':      { min: 12, max: 120, note: 'Managed by certified fund managers, quarterly statements' },
  'Insurance':       { min: 12, max: 12,  note: 'Renews annually — cancel before renewal date at no cost' },
};

// Human-readable eligibility lines per product, built from real RAG numbers
// rawRec = the full recommendations object from the API
const buildEligibilityLine = (product, rawRec) => {
  const inflow  = rawRec?.monthly_inflow  ? Number(rawRec.monthly_inflow)  : null;
  const balance = rawRec?.balance         ? Number(rawRec.balance)         : null;
  const emi     = rawRec?.monthly_emi     ? Number(rawRec.monthly_emi)     : null;
  const score   = rawRec?.credit_score    ? Number(rawRec.credit_score)    : null;

  // Format helpers
  const fmt = (n) => `₦${Number(n).toLocaleString('en-NG')}`;

  switch (product) {
    case 'Investment Plan':
      if (inflow) return `Your monthly inflow of ${fmt(inflow)} shows you have strong financial headroom — enough to grow your money instead of just saving it. An Investment Plan puts that surplus to work.`;
      if (balance) return `With a balance of ${fmt(balance)}, you have idle funds that could be earning returns instead of sitting still. This plan is built for people at your level.`;
      return `Your account activity shows consistent surplus income — exactly the profile our Investment Plan is designed for. Put your money to work.`;

    case 'Fixed Deposit':
      if (balance) return `You have ${fmt(balance)} sitting in your account. Locking even a portion into a Fixed Deposit earns you up to 15% annually — far more than a regular savings balance.`;
      if (inflow) return `With your income pattern, setting aside a fixed amount each month and locking it in can earn you guaranteed returns of up to 15% per year.`;
      return `Your savings pattern makes you a strong candidate for a Fixed Deposit — earn guaranteed returns without any market risk.`;

    case 'Student Loan':
      if (emi) return `Based on your account, you qualify for up to ${fmt(emi * 10)} — repayable at ${fmt(emi)}/month with zero interest for the first 3 months.`;
      return `Your account history qualifies you for a Student Loan with zero interest for the first 3 months. Cover your tuition now and start repaying when you're ready.`;

    case 'Personal Loan':
      if (emi) return `You qualify for quick cash — up to ${fmt(emi * 10)} disbursed within 24 hours, repayable at just ${fmt(emi)}/month. No collateral, no stress.`;
      if (inflow) return `Your consistent income of ${fmt(inflow)}/month makes you eligible for a Personal Loan — fast approval, no collateral, funds in your account within 24 hours.`;
      return `Your account qualifies you for a Personal Loan with same-day disbursement. No paperwork, no collateral — just fast cash when you need it.`;

    case 'Car Loan':
      if (emi) return `Your income supports a repayment of ${fmt(emi)}/month — enough to comfortably finance a car without stretching your budget. Get on the road sooner.`;
      if (inflow) return `With a monthly inflow of ${fmt(inflow)}, you're in a great position to finance a car. Our Car Loan offers competitive rates with flexible repayment up to 5 years.`;
      return `Your financial profile qualifies you for a Car Loan with flexible repayment up to 60 months — own your car without draining your savings.`;

    case 'Mortgage':
      if (balance && inflow) return `Your balance of ${fmt(balance)} combined with a monthly inflow of ${fmt(inflow)} puts homeownership within reach. Lock in your rate now before they rise.`;
      if (inflow) return `Your monthly income of ${fmt(inflow)} qualifies you for a Mortgage with affordable fixed monthly payments spread over up to 20 years.`;
      return `Your profile qualifies you for a Mortgage. Stop paying rent and start building equity — affordable monthly payments, up to 20-year tenure.`;

    case 'Credit Card':
      if (balance) return `Based on your balance of ${fmt(balance)} and account activity, you've been pre-approved for our Credit Card. Shop now, pay later — interest-free on full monthly payment.`;
      return `Your spending and savings pattern earns you a pre-approved Credit Card. Use it anywhere, pay in full monthly and pay zero interest.`;

    case 'Savings Plan':
      if (inflow) return `You earn ${fmt(inflow)}/month but your savings rate could be higher. A structured Savings Plan lets you automate the habit and build a cushion without thinking about it.`;
      return `Your account activity shows you're ready to build a more consistent savings habit. Set a target, automate contributions, and watch your balance grow.`;

    case 'Trust Fund':
      if (balance) return `With ${fmt(balance)} in your account, you're at a level where wealth preservation matters. A Trust Fund protects and grows your assets for the long term.`;
      return `Your financial profile puts you in the bracket where a Trust Fund makes sense — protect your wealth and leave a legacy.`;

    case 'Insurance':
      return `Protecting what you've built is just as important as growing it. Your profile qualifies you for comprehensive coverage tailored to your lifestyle and assets.`;

    default:
      if (inflow) return `Your monthly activity of ${fmt(inflow)} qualifies you for this offer — designed specifically for customers with your financial profile.`;
      if (balance) return `Your balance of ${fmt(balance)} and account history make you eligible for this personalized offer.`;
      return `Your account activity and financial profile qualify you for this offer. It's been matched specifically to your spending and savings pattern.`;
  }
};

// Popup teaser — short, punchy, no policy language
const buildPopupTeaser = (product, rawRec) => {
  const inflow  = rawRec?.monthly_inflow ? Number(rawRec.monthly_inflow) : null;
  const balance = rawRec?.balance        ? Number(rawRec.balance)        : null;
  const fmt     = (n) => `₦${Number(n).toLocaleString('en-NG')}`;

  switch (product) {
    case 'Investment Plan':
      if (inflow) return `Your ₦${(inflow / 1000000).toFixed(1)}M monthly inflow qualifies you to invest, not just save. Grow your surplus with up to 18% annual returns.`;
      return `Your income puts you in the top tier of earners. Time to make that money work harder — invest it.`;
    case 'Fixed Deposit':
      if (balance) return `${fmt(balance)} in your account could be earning 15% annually. Lock it in and let it grow.`;
      return `Earn guaranteed returns of up to 15% per year. Zero risk, maximum growth.`;
    case 'Student Loan':
      return `Zero interest for 3 months. Get your tuition funded today — instant approval.`;
    case 'Personal Loan':
      return `Quick cash, no collateral. Get up to ₦5M in your account within 24 hours.`;
    case 'Car Loan':
      return `Finance your car with flexible repayment up to 5 years. Get on the road sooner.`;
    case 'Credit Card':
      return `You've been pre-approved. Shop now, pay later — zero interest on full monthly payment.`;
    case 'Mortgage':
      return `Stop paying rent. Own your home with affordable monthly payments over up to 20 years.`;
    case 'Savings Plan':
      return `Automate your savings and build a financial cushion without the hassle.`;
    case 'Trust Fund':
      return `Preserve and grow your wealth. Managed by certified fund managers.`;
    case 'Insurance':
      return `Protect everything you've built — comprehensive coverage tailored to your lifestyle.`;
    default:
      return `We've matched a product to your financial profile. See why you qualify.`;
  }
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

    @keyframes scaleIn {
      from { opacity: 0; transform: scale(0.92) translateY(16px); }
      to   { opacity: 1; transform: scale(1) translateY(0); }
    }
    .scale-in { animation: scaleIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
  `}</style>
);

let _cachedFeedCards    = null;
let _cachedRagPopupCard = null;
let _cachedRawRec       = null; // store the full recommendations object for copy-building

const HomeScreen = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const user    = useSelector((state) => state.auth.user);
  const account = useSelector((state) => state.account?.details);
  const showPopup = useSelector((state) => state.ui.showWelcome);

  const [showBal, setShowBal] = useState(true);
  const [feedCards, setFeedCards] = useState(_cachedFeedCards || []);
  const [loadingFeed, setLoadingFeed] = useState(!_cachedFeedCards);

  // RAG popup card held separately — never populated from fallback
  const [ragPopupCard, setRagPopupCard]   = useState(_cachedRagPopupCard || null);
  const [rawRec, setRawRec]               = useState(_cachedRawRec       || null);
  const [ragPopupReady, setRagPopupReady] = useState(!!_cachedRagPopupCard);

  const [sentinelAlert, setSentinelAlert] = useState(null);
  const [confirmStep, setConfirmStep]     = useState('idle');
  const [password, setPassword]           = useState('');
  const [confirmError, setConfirmError]   = useState('');

  // Apply modal
  const [appliedProduct, setAppliedProduct] = useState(null);
  const [notifOpen, setNotifOpen]           = useState(false);
  const [hasUnreadNotif, setHasUnreadNotif] = useState(true);
  const [confirmApply, setConfirmApply]     = useState(false);
  // Keep the rawRec that was live when Apply was tapped
  const [applyRawRec, setApplyRawRec]       = useState(null);

  const displayCards = feedCards.length > 0 ? feedCards : FALLBACK_CARDS;

  const handleApply = (card, rec) => {
    setConfirmApply(false);
    setAppliedProduct(card);
    setApplyRawRec(rec || rawRec || null);
  };

  useEffect(() => {
    dispatch(fetchDashboard());

    if (_cachedFeedCards && _cachedRagPopupCard) {
      setFeedCards(_cachedFeedCards);
      setRagPopupCard(_cachedRagPopupCard);
      setRawRec(_cachedRawRec);
      setRagPopupReady(true);
      setLoadingFeed(false);
      return;
    }

    const loadFeed = async () => {
      try {
        const res  = await api.getSmartFeed();
        const data = res?.data || {};
        console.log('[SmartFeed] Raw response:', JSON.stringify(data, null, 2));
        let cards = data.cards || [];

        if (cards.length > 0) {
          const rec = data.recommendations || {};
          cards = cards.map(card => {
            const style = styleMap[card.title];
            return {
              ...card,
              gradient:   style?.grad       || card.gradient   || ['#1d4ed8', '#1e3a8a'],
              label:      card.label        || style?.label    || card.title,
              labelColor: style?.labelColor || card.labelColor || '#ffffff',
              subtitle:   card.subtitle?.includes('₦0')
                ? getSubtitle(card.title, 0)
                : card.subtitle || getSubtitle(card.title, 0),
              // Store the raw rec blob on every card for copy-building
              _rawRec: rec,
            };
          });
          _cachedFeedCards    = cards;
          _cachedRagPopupCard = cards[0];
          _cachedRawRec       = rec;
          setFeedCards(cards);
          setRagPopupCard(cards[0]);
          setRawRec(rec);
          setRagPopupReady(true);
          return;
        }

        if (data.recommendations?.primary_product) {
          const rec     = data.recommendations;
          const product = rec.primary_product;
          const style   = styleMap[product] || { grad: ['#1d4ed8', '#1e3a8a'], label: 'Special Offer', labelColor: '#93c5fd' };
          const builtCard = {
            id:         `rec-${Date.now()}`,
            label:      style.label,
            labelColor: style.labelColor,
            title:      product,
            subtitle:   getSubtitle(product, rec.monthly_emi),
            cta:        'APPLY NOW',
            ctaRoute:   'loans',
            gradient:   style.grad,
            _rawRec:    rec,
          };
          console.log('[SmartFeed] Built card from recommendations:', product);
          _cachedFeedCards    = [builtCard];
          _cachedRagPopupCard = builtCard;
          _cachedRawRec       = rec;
          setFeedCards([builtCard]);
          setRagPopupCard(builtCard);
          setRawRec(rec);
          setRagPopupReady(true);
        } else {
          // No RAG product — marquee will use fallback, but popup stays hidden
          setRagPopupReady(false);
        }

      } catch (err) {
        console.warn('Smart feed unavailable, using fallback cards:', err?.message || err);
        setRagPopupReady(false);
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
    if (showPopup && ragPopupReady && ragPopupCard) {
      const timer = setTimeout(() => dispatch(dismissWelcome()), 9000);
      return () => clearTimeout(timer);
    }
  }, [showPopup, ragPopupReady, ragPopupCard, dispatch]);

  const quickItems = [
      { icon: Smartphone, label: "Airtime",     route: "/airtime" },
      { icon: Wifi,       label: "Data",        route: "/data"    },
      { icon: Gamepad2,   label: "Betting",     route: "/betting" },
      { icon: Zap,        label: "Electricity", route: "/bills"   },
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

  // ── Build apply modal display data from RAG numbers ───────────────────────
  const buildApplyMeta = (card, rec) => {
    if (!card) return {};
    const r        = repaymentMap[card.title] || { min: 6, max: 24, note: 'Flexible repayment available' };
    const emi      = rec?.monthly_emi      ? Number(rec.monthly_emi)      : null;
    const months   = rec?.repayment_months ? Number(rec.repayment_months) : r.max;
    const rate     = rec?.interest_rate    ? Number(rec.interest_rate)    : null;
    const maxAmt   = emi ? emi * 10 : null;
    const fmt      = (n) => `₦${Number(n).toLocaleString('en-NG')}`;

    const amountText    = maxAmt ? `Up to ${fmt(maxAmt)}` : card.subtitle || 'See offer details';
    const repaymentText = emi && months
      ? `${fmt(emi)} / month × ${months} months`
      : months
        ? `Up to ${months} months`
        : `${r.min}–${r.max} months`;
    const rateText      = rate ? `${rate}% per annum` : null;
    const tenureNote    = r.note;
    const eligLine      = buildEligibilityLine(card.title, rec);

    return { amountText, repaymentText, rateText, tenureNote, eligLine, months, emi };
  };

  return (
    <div className="min-h-full w-full bg-vault-light-bg dark:bg-vault-dark-bg font-sans relative vault-transition">
      <InjectStyles />

    {/* ── Notification Drawer ──────────────────────────────────────────── */}
      {notifOpen && (
        <div
          className="fixed inset-0 z-[9998] flex items-start justify-end pt-16 pr-4"
          onClick={() => setNotifOpen(false)}
        >
          <div
            className="w-[min(92vw,340px)] bg-white dark:bg-vault-dark-card rounded-[24px] shadow-2xl border border-gray-100 dark:border-white/5 overflow-hidden scale-in"
            onClick={e => e.stopPropagation()}
          >
            <div className="px-5 py-4 border-b border-gray-100 dark:border-white/5 flex items-center justify-between">
              <h3 className="text-sm font-black text-gray-900 dark:text-white">Notifications</h3>
              <button
                onClick={() => { setNotifOpen(false); setHasUnreadNotif(false); }}
                className="text-[10px] font-bold text-vault-cyan hover:underline"
              >
                Mark all read
              </button>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-white/5 max-h-[60dvh] overflow-y-auto">
              {[
                { icon: ShieldAlert, color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-500/10', title: 'Suspicious transaction flagged', sub: 'A payment to BetKing was flagged by Sentinel AI.', time: '2 min ago', unread: true },
                { icon: CheckCircle, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-500/10', title: 'Transfer successful', sub: `₦${(5000).toLocaleString('en-NG')} sent successfully.`, time: '1 hr ago', unread: true },
                { icon: Sparkles,    color: 'text-vault-cyan',  bg: 'bg-cyan-50 dark:bg-cyan-500/10',       title: 'New offer available', sub: 'You\'ve been pre-approved for an Investment Plan.', time: '3 hrs ago', unread: false },
                { icon: Bell,        color: 'text-vault-purple',bg: 'bg-purple-50 dark:bg-purple-500/10',   title: 'Account funded',      sub: 'Your account has been credited.', time: 'Yesterday', unread: false },
              ].map((n, i) => (
                <div key={i} className={`flex items-start gap-3 px-5 py-4 ${n.unread ? 'bg-blue-50/40 dark:bg-white/[0.02]' : ''}`}>
                  <div className={`w-9 h-9 rounded-xl ${n.bg} flex items-center justify-center shrink-0 mt-0.5`}>
                    <n.icon size={16} className={n.color} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-gray-900 dark:text-white leading-tight">{n.title}</p>
                    <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5 leading-relaxed">{n.sub}</p>
                    <p className="text-[10px] text-gray-300 dark:text-slate-600 mt-1 font-bold">{n.time}</p>
                  </div>
                  {n.unread && <span className="w-2 h-2 bg-vault-cyan rounded-full shrink-0 mt-1.5" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Sentinel Alert Modal ──────────────────────────────────────────── */}
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
                  {(() => {
                    const score    = sentinelAlert.fraud_analysis?.total_risk_score || 0;
                    const merchant = sentinelAlert.merchant || 'this merchant';
                    const amount   = Number(sentinelAlert.amount || 0);
                    const time     = sentinelAlert.time || '';
                    const isLateNight = time.includes('AM') && parseInt(time) < 6;
                    if (score >= 61)
                      return `We've flagged this payment as high risk. Paying ₦${amount.toLocaleString('en-NG')} to ${merchant}${isLateNight ? ' at this hour of the night' : ''} matches patterns we associate with fraud. Only approve if you initiated this.`;
                    if (score >= 30)
                      return `This payment to ${merchant} looks unusual${isLateNight ? ', especially at this time of night' : ''}. Review carefully before approving.`;
                    return `You're about to pay ₦${amount.toLocaleString('en-NG')} to ${merchant}${isLateNight ? ' at an unusual hour' : ''}. Please confirm this was you.`;
                  })()}
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

      {/* ── Sentinel: Transaction Approved ───────────────────────────────── */}
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

      {/* ── Sentinel: Transaction Rejected ───────────────────────────────── */}
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

      {/*
        ── Welcome / RAG Recommendation Popup ────────────────────────────────
        Only renders after the async fetch resolves with a real RAG card.
        Fallback cards never appear here.
      */}
      {showPopup && ragPopupReady && ragPopupCard && !sentinelAlert && (
        <div
          className="fixed top-0 left-0 right-0 bottom-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) dispatch(dismissWelcome()); }}
        >
          <div
            className="relative text-white shadow-2xl border border-white/10 scale-in"
            style={{
              background: `linear-gradient(to bottom right, ${ragPopupCard.gradient?.[0] || '#1d4ed8'}, ${ragPopupCard.gradient?.[1] || '#1e3a8a'})`,
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
              <span className="text-[10px] font-bold uppercase tracking-wider mb-2 block" style={{ color: ragPopupCard.labelColor || '#22d3ee' }}>
                {ragPopupCard.label}
              </span>
              <h3 className="text-xl sm:text-2xl font-black leading-tight mb-2">
                {ragPopupCard.title}<br />{ragPopupCard.subtitle}
              </h3>
              <p className="text-white/80 text-xs mb-6 leading-relaxed flex items-start gap-1.5">
                <Sparkles size={14} className="shrink-0 mt-0.5 text-yellow-300" />
                {buildPopupTeaser(ragPopupCard.title, rawRec)}
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => { dispatch(dismissWelcome()); handleApply(ragPopupCard, rawRec); }}
                  className="w-full bg-white text-xs font-extrabold py-3.5 rounded-full shadow-lg active:scale-95 hover:shadow-xl transition-all"
                  style={{ color: ragPopupCard.gradient?.[0] || '#1d4ed8' }}
                >
                  {ragPopupCard.cta || 'APPLY NOW'}
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

      {/*
        ── Application Modal ─────────────────────────────────────────────────
        Step 1 (confirmApply=false): Eligibility details + "Yes, Apply Now"
        Step 2 (confirmApply=true):  Submitted confirmation + next steps
      */}
      {appliedProduct && (() => {
        const meta = buildApplyMeta(appliedProduct, applyRawRec);
        return (
          <div
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            style={{ animation: 'fadeUp 0.3s ease' }}
            onClick={(e) => { if (e.target === e.currentTarget) { setAppliedProduct(null); setConfirmApply(false); } }}
          >
            <div
              className="relative w-[min(92vw,420px)] bg-white dark:bg-vault-dark-card rounded-[28px] shadow-2xl overflow-hidden border border-gray-100 dark:border-white/5 scale-in"
              style={{ maxHeight: '90dvh', overflowY: 'auto' }}
              onClick={e => e.stopPropagation()}
            >
              {/* Gradient header */}
              <div
                className="px-6 pt-7 pb-6 text-white text-center relative overflow-hidden"
                style={{ background: `linear-gradient(135deg, ${appliedProduct.gradient?.[0] || '#1d4ed8'}, ${appliedProduct.gradient?.[1] || '#1e3a8a'})` }}
              >
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-white/5 rounded-full blur-2xl pointer-events-none" />
                <div className="absolute -bottom-6 -left-6 w-24 h-24 bg-white/5 rounded-full blur-xl pointer-events-none" />
                <div className="relative z-10">
                  {confirmApply ? (
                    <>
                      <div className="relative w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                        <div className="absolute inset-0 rounded-full bg-white/10 animate-ping" style={{ animationDuration: '1.6s' }} />
                        <div className="relative w-20 h-20 bg-white/20 rounded-full flex items-center justify-center border border-white/30">
                          <CheckCircle size={34} className="text-white" />
                        </div>
                      </div>
                      <h3 className="text-xl font-black mb-1">Application Received!</h3>
                      <p className="text-white/75 text-sm">
                        Your <span className="font-bold text-white">{appliedProduct.title}</span> application has been submitted.
                      </p>
                    </>
                  ) : (
                    <>
                      <div className="w-16 h-16 mx-auto mb-3 bg-white/20 rounded-full flex items-center justify-center border border-white/30">
                        <BadgeCheck size={30} className="text-white" />
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-wider block mb-1" style={{ color: appliedProduct.labelColor || '#22d3ee' }}>
                        {appliedProduct.label}
                      </span>
                      <h3 className="text-xl font-black mb-1">You're Eligible!</h3>
                      <p className="text-white/75 text-sm">Here's exactly what you're getting.</p>
                    </>
                  )}
                </div>
              </div>

              {/* Body */}
              <div className="p-5 space-y-4">
                {!confirmApply ? (
                  <>
                    {/* Offer stats grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-gray-50 dark:bg-white/5 rounded-2xl p-3.5 border border-gray-100 dark:border-white/5">
                        <p className="text-[10px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1">Amount</p>
                        <p className="text-base font-black text-gray-900 dark:text-white leading-tight">{meta.amountText}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-white/5 rounded-2xl p-3.5 border border-gray-100 dark:border-white/5">
                        <p className="text-[10px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1">Repayment</p>
                        <p className="text-base font-black text-gray-900 dark:text-white leading-tight">{meta.repaymentText}</p>
                      </div>
                      {meta.rateText && (
                        <div className="bg-gray-50 dark:bg-white/5 rounded-2xl p-3.5 border border-gray-100 dark:border-white/5">
                          <p className="text-[10px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1">Interest Rate</p>
                          <p className="text-base font-black text-gray-900 dark:text-white leading-tight">{meta.rateText}</p>
                        </div>
                      )}
                      <div className={`bg-gray-50 dark:bg-white/5 rounded-2xl p-3.5 border border-gray-100 dark:border-white/5 ${meta.rateText ? '' : 'col-span-2'}`}>
                        <p className="text-[10px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-1">Status</p>
                        <span
                          className="text-[11px] font-black px-2.5 py-1 rounded-full inline-block"
                          style={{
                            background: `${appliedProduct.gradient?.[0]}22`,
                            color: appliedProduct.labelColor || '#22d3ee',
                            border: `1px solid ${appliedProduct.labelColor || '#22d3ee'}33`
                          }}
                        >
                          PRE-APPROVED
                        </span>
                      </div>
                    </div>

                    {/* Why you qualify — human copy, never policy text */}
                    <div className="bg-gray-50 dark:bg-white/5 rounded-2xl p-4 border border-gray-100 dark:border-white/5">
                      <p className="text-[10px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                        <Sparkles size={11} className="text-amber-400" /> Why you qualify
                      </p>
                      <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed font-medium">
                        {meta.eligLine}
                      </p>
                    </div>

                    {/* Tenure note */}
                    <div className="flex items-start gap-3 bg-cyan-50 dark:bg-cyan-500/10 rounded-2xl px-4 py-3 border border-cyan-100 dark:border-cyan-500/20">
                      <Calendar size={15} className="text-vault-cyan shrink-0 mt-0.5" />
                      <p className="text-xs text-cyan-800 dark:text-cyan-200 font-medium leading-relaxed">
                        {meta.tenureNote}. You can pay ahead at any time without penalties.
                      </p>
                    </div>

                    {/* Action buttons */}
                    <div className="space-y-3 pt-1">
                      <button
                        onClick={() => setConfirmApply(true)}
                        className="w-full vault-gradient text-white py-4 rounded-xl font-bold text-sm vault-glow active:scale-95 transition-all shadow-lg flex items-center justify-center gap-2"
                      >
                        Yes, Apply Now <ArrowRight size={16} />
                      </button>
                      <button
                        onClick={() => { setAppliedProduct(null); setConfirmApply(false); }}
                        className="w-full flex items-center justify-center gap-2 bg-white dark:bg-white/5 text-gray-500 dark:text-slate-400 py-3.5 rounded-xl font-bold text-sm border border-gray-200 dark:border-white/5 active:scale-95 transition-all"
                      >
                        <X size={15} /> Not right now
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    {/* Product summary pill */}
                    <div className="flex items-center justify-between bg-gray-50 dark:bg-white/5 rounded-2xl px-4 py-3 border border-gray-100 dark:border-white/5">
                      <div>
                        <p className="text-[10px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-0.5">
                          {appliedProduct.label}
                        </p>
                        <p className="text-sm font-black text-gray-900 dark:text-white">{appliedProduct.title}</p>
                      </div>
                      <span
                        className="text-[10px] font-black px-3 py-1.5 rounded-full"
                        style={{
                          background: `${appliedProduct.gradient?.[0]}22`,
                          color: appliedProduct.labelColor || '#22d3ee',
                          border: `1px solid ${appliedProduct.labelColor || '#22d3ee'}33`
                        }}
                      >
                        PENDING REVIEW
                      </span>
                    </div>

                    {/* Next steps */}
                    <div>
                      <p className="text-[11px] font-black text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-3">
                        What happens next
                      </p>
                      {[
                        { icon: CheckCircle, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-500/10', title: 'Application submitted',   sub: "We've received your request and it's in the queue",                                done: true  },
                        { icon: Loader2,     color: 'text-vault-cyan',   bg: 'bg-cyan-50 dark:bg-cyan-500/10',       title: 'Under review',             sub: 'Our team reviews your profile — usually 2–5 minutes',                            done: false },
                        { icon: Bell,        color: 'text-vault-purple', bg: 'bg-purple-50 dark:bg-purple-500/10',   title: 'Email confirmation',       sub: `Check ${user?.email || 'your inbox'} for next steps & approval details`,        done: false },
                        { icon: Sparkles,    color: 'text-amber-500',    bg: 'bg-amber-50 dark:bg-amber-500/10',     title: 'Decision within 24 hrs',   sub: "You'll be notified in-app and via email once approved",                          done: false },
                      ].map(({ icon: Icon, color, bg, title, sub, done }, idx) => (
                        <div key={idx} className="flex items-start gap-3 py-2.5">
                          <div className={`w-9 h-9 rounded-xl ${bg} flex items-center justify-center shrink-0 mt-0.5`}>
                            <Icon size={17} className={`${color} ${!done && idx === 1 ? 'animate-spin' : ''}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm font-bold leading-tight ${done ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-800 dark:text-white'}`}>{title}</p>
                            <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5 leading-relaxed">{sub}</p>
                          </div>
                          {done && (
                            <div className="w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center shrink-0 mt-1">
                              <CheckCircle size={12} className="text-white" />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    <div className="pt-1">
                      <button
                        onClick={() => { setAppliedProduct(null); setConfirmApply(false); }}
                        className="w-full vault-gradient text-white py-4 rounded-xl font-bold text-sm vault-glow active:scale-95 transition-all shadow-lg"
                      >
                        Got it, thanks!
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── Hero header ──────────────────────────────────────────────────── */}
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
                      <button
                        onClick={() => setSentinelAlert(prev => {
                          // If no real pending txn, show a demo notification drawer via notifOpen
                          setNotifOpen(o => !o);
                          return prev;
                        })}
                        className="relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors"
                      >
                        <Bell size={22} />
                        {hasUnreadNotif && (
                          <span className="absolute top-2 right-2.5 w-2 h-2 bg-vault-cyan rounded-full border border-slate-800 dark:border-vault-dark-bg" />
                        )}
                      </button>
                      <button
                        onClick={() => navigate('/profile')}
                        className="w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-colors"
                      >
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

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <div className="w-full px-4 sm:px-6 xl:px-8 py-2 pb-28 space-y-6">

        {/* Quick action buttons */}
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

        {/* Quick Access */}
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

        {/* Smart Feed */}
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
                      onClick={() => handleApply(card, card._rawRec || rawRec)}
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