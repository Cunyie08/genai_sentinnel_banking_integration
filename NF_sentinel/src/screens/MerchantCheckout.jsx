import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchDashboard } from '../features/accountSlice';
import { api } from '../api/axiosConfig';
import {
  CreditCard, ShieldAlert, Clock, CheckCircle, Loader2,
  AlertTriangle, User
} from 'lucide-react';

const STEPS = { CHECKOUT: 0, PROCESSING: 1, WAITING: 2, RESULT: 3 };

// =============================================================================
// CLIENT-SIDE RISK FLOOR — mirrors FRM-002 MERCHANT_RISK exactly.
// Used when the backend returns total_risk_score = 0 due to a field-name
// mismatch (merchant_category not read in calculate_fraud_risk yet).
// The backend score always wins when it comes back > 0.
// =============================================================================
const CLIENT_MERCHANT_RISK = {
  fintech:     25,
  betting:     25,
  transport:   15,
  education:   15,
  healthcare:  15,
  telecoms:     5,
  supermarket:  0,
  restaurants:  0,
  fuel:         0,
  utilities:    0,
};

function computeClientFloorScore({ merchantCategory, amount, isNewMerchant, transactionTime }) {
  let score = CLIENT_MERCHANT_RISK[merchantCategory] ?? 0;

  // New merchant — large amount uses +25 weight, small uses +10 (FRM-002 §2)
  if (isNewMerchant) score += amount > 100_000 ? 25 : 10;

  // Late-night (midnight–5 AM) heightened alert +10
  if (transactionTime) {
    const m = transactionTime.match(/^(\d+):(\d+)\s*(AM|PM)/i);
    if (m) {
      const h = parseInt(m[1]);
      const isPM  = m[3].toUpperCase() === 'PM';
      const h24   = isPM && h !== 12 ? h + 12 : (!isPM && h === 12 ? 0 : h);
      if (h24 >= 0 && h24 < 5) score += 10;
    }
  }

  // Betting-specific: amount > ₦100,000 heightened alert +10 (FRM-002 §1 betting)
  if (merchantCategory === 'betting' && amount > 100_000) score += 10;

  return Math.min(score, 100);
}

function scoreToLevel(score) {
  if (score >= 86) return 'CRITICAL';
  if (score >= 61) return 'HIGH';
  if (score >= 31) return 'MEDIUM';
  return 'LOW';
}

const MerchantCheckout = () => {
  const dispatch    = useDispatch();
  const user        = useSelector(s => s.auth.user);
  const accountInfo = useSelector(s => s.account?.details);

  const firstAccount = user?.accounts?.[0] || null;

  const synthesizedAccount = !firstAccount && accountInfo?.number
    ? {
        account_number: accountInfo.number,
        account_type:   accountInfo.type   || 'Savings',
        balance:        accountInfo.balance || 0,
        currency:       'NGN',
        status:         accountInfo.status  || 'Active',
        tier:           accountInfo.tier    || 'Tier 3',
        card: { masked_number: '**** **** **** 4832', type: 'Visa', expiry: '12/28', status: 'Active' },
      }
    : null;

  const [fetchedAccount, setFetchedAccount] = useState(null);
  const [accountLoading, setAccountLoading] = useState(false);

  const resolvedAccount = firstAccount || synthesizedAccount || fetchedAccount;

  const [step, setStep]     = useState(STEPS.CHECKOUT);
  const [txnId, setTxnId]   = useState('');
  const [fraud, setFraud]   = useState(null);
  const [error, setError]   = useState('');
  const [result, setResult] = useState(null);

  // BetKing → merchant_category "betting" → FRM-002 Tier 1 → +25 base risk
  const merchant         = 'BetKing';
  const merchantCategory = 'betting';
  const amount           = 250000;
  const card             = resolvedAccount?.card?.masked_number || '**** **** **** 4832';
  const time             = '02:14 AM';

  // Compute the client-side floor once (doesn't change during a session)
  const clientFloorScore = computeClientFloorScore({
    merchantCategory,
    amount,
    isNewMerchant:   true,  // this simulation always treats BetKing as new merchant
    transactionTime: time,
  });

  useEffect(() => {
    if (firstAccount || synthesizedAccount) return;

    setAccountLoading(true);
    dispatch(fetchDashboard());

    api.getDashboard()
      .then(res => {
        const d    = res.data;
        const accArr = d?.account_details || d?.user?.accounts || d?.accounts || [];
        if (accArr.length > 0) {
          const a = accArr[0];
          setFetchedAccount({
            account_number: a.account_number || a.number,
            account_type:   a.account_type   || a.type || 'Savings',
            balance:        a.balance || a.current_balance || 0,
            currency:       a.currency || 'NGN',
            status:         a.status   || 'Active',
            tier:           a.tier     || 'Tier 3',
            card: a.card || { masked_number: '**** **** **** 4832', type: 'Visa', expiry: '12/28', status: 'Active' },
          });
        }
      })
      .catch(err => console.error('Failed to fetch dashboard in checkout:', err))
      .finally(() => setAccountLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (step !== STEPS.WAITING) return;

    const poll = setInterval(() => {
      const raw = localStorage.getItem('sentinel_txn_result');
      if (raw) {
        try {
          const data = JSON.parse(raw);
          if (data.transaction_id === txnId) {
            setResult(data.status);
            setStep(STEPS.RESULT);
            localStorage.removeItem('sentinel_txn_result');
          }
        } catch { /* ignore */ }
      }
    }, 1500);

    return () => clearInterval(poll);
  }, [step, txnId]);

  const handlePayNow = async () => {
    const accountToUse = resolvedAccount;
    if (!accountToUse) {
      setError('No active account detected. Please log in.');
      return;
    }

    setStep(STEPS.PROCESSING);
    setError('');

    try {
      const res = await api.cardTransaction({
        account_number:    accountToUse.account_number,
        channel:           'pos',
        device_id:         'MERCHANT-POS-001',
        counterparty_bank: merchant,
        narration:         `Card payment to ${merchant}`,
        transaction_type:  'debit',
        amount,
        currency:          'NGN',
        merchant_name:     merchant,
        merchant_category: merchantCategory,
        is_new_merchant:   true,
      });

      const data         = res?.data;
      const backendFraud = data?.fraud_analysis || null;
      const backendScore = backendFraud?.total_risk_score ?? 0;
      const effectiveScore = Math.max(backendScore, clientFloorScore);
      const clientCorrected = effectiveScore > backendScore;

      const reconciledFraud = {
        ...(backendFraud ?? {}),
        total_risk_score:     effectiveScore,
        risk_level:           scoreToLevel(effectiveScore),
        merchant_category:    merchantCategory,
        merchant_risk:        CLIENT_MERCHANT_RISK[merchantCategory] ?? 0,
        requires_challenge:   effectiveScore >= 61,
        should_block:         effectiveScore >= 86,
        is_new_merchant:      backendFraud?.is_new_merchant  ?? true,
        new_merchant:         backendFraud?.new_merchant      ?? true,
        multiple_failures:    backendFraud?.multiple_failures ?? false,
        flags:                backendFraud?.flags             ?? [],
        client_floor_applied: clientCorrected,
      };

      setTxnId(data?.transaction_id || '');
      setFraud(reconciledFraud);

      localStorage.setItem('sentinel_pending_txn', JSON.stringify({
        transaction_id:    data?.transaction_id,
        merchant,
        merchant_category: merchantCategory,
        amount,
        time,
        fraud_analysis:    reconciledFraud,
        account_number:    accountToUse.account_number,
      }));

      setStep(STEPS.WAITING);
    } catch (err) {
      setError(err?.detail || err?.message || 'Transaction failed. Check that the backend is running.');
      setStep(STEPS.CHECKOUT);
    }
  };

  // ===========================================================================
  // FRAUD PANEL — extracted so it's readable
  // ===========================================================================
  const renderFraudPanel = () => {
    // Always render for betting — use reconciled fraud or client floor fallback
    const displayFraud = fraud ?? {
      total_risk_score:  clientFloorScore,
      risk_level:        scoreToLevel(clientFloorScore),
      is_new_merchant:   true,
      new_merchant:      true,
      multiple_failures: false,
      client_floor_applied: true,
    };

    const score  = Math.round(displayFraud.total_risk_score || 0);
    const level  = scoreToLevel(score);
    const isHigh = score >= 61;
    const isMed  = score >= 31 && score < 61;

    const riskLabel = level === 'CRITICAL' ? 'Critical Risk'
                    : level === 'HIGH'     ? 'High Risk'
                    : level === 'MEDIUM'   ? 'Moderate Risk'
                    : 'Low Risk';

    const riskColor = score >= 61 ? 'red' : score >= 31 ? 'amber' : 'green';
    const colorMap  = {
      red:   { bg: 'bg-red-500/10',   border: 'border-red-500/20',   bar: 'bg-red-500',   text: 'text-red-400',   badge: 'bg-red-500/20 text-red-300' },
      amber: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', bar: 'bg-amber-400', text: 'text-amber-400', badge: 'bg-amber-500/20 text-amber-300' },
      green: { bg: 'bg-green-500/10', border: 'border-green-500/20', bar: 'bg-green-500', text: 'text-green-400', badge: 'bg-green-500/20 text-green-300' },
    };
    const c = colorMap[riskColor];

    const flags = [
      'Betting platform',
      'Large amount ₦250,000 > ₦100,000 threshold',
      'Late night transaction 02:14 AM',
    ];
    if (displayFraud.is_new_merchant || displayFraud.new_merchant) {
      flags.push('First-time merchant — new merchant weight applied');
    }
    if (displayFraud.multiple_failures) {
      flags.push('Recent failed attempts on account');
    }
    if (isHigh || isMed) {
      flags.push('Biometric verification required');
    }
    if (displayFraud.client_floor_applied) {
      flags.push('Score floor applied — backend merchant_category patch pending');
    }

    const message = isHigh
      ? "We've placed a hold on this payment. Multiple high-risk signals detected. Please verify in your banking app."
      : isMed
      ? "This payment looks unusual. Review the details carefully before approving."
      : "Transaction looks normal. Confirm in your banking app to complete.";

    return (
      <div className={`${c.bg} border ${c.border} rounded-xl p-4 mt-3`}>
        <div className="flex items-center justify-between mb-3">
          <p className="text-[10px] font-black uppercase tracking-wider text-white/40">Security Check</p>
          <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${c.badge}`}>
            {riskLabel}
          </span>
        </div>

        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full ${c.bar} rounded-full transition-all`}
              style={{ width: `${Math.min(score, 100)}%` }}
            />
          </div>
          <span className={`text-xs font-bold ${c.text}`}>{score}%</span>
        </div>

        <p className="text-xs text-white/70 leading-relaxed mb-3">{message}</p>

        <div className="space-y-1.5">
          {flags.map((flag, i) => (
            <div key={i} className="flex items-center gap-2 text-xs text-white/50">
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.bar}`} />
              {flag}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ===========================================================================
  // RENDER
  // ===========================================================================
  return (
    <div className="min-h-[100dvh] w-full bg-vault-dark-bg flex flex-col items-center p-4 sm:p-6 md:p-8 font-sans overflow-x-hidden overflow-y-auto relative">
      <div className="absolute -top-32 -right-32 w-96 h-96 bg-vault-cyan/8 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-vault-purple/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md mt-4 mb-20 shrink-0 relative z-10">

        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 px-5 py-2 rounded-full mb-4">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <span className="text-white/60 text-xs font-bold uppercase tracking-widest">Secure Checkout</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">MERCHANT CHECKOUT</h1>
          <p className="text-white/40 text-sm mt-1">Powered by Sentinnel Payment Gateway</p>
        </div>

        {/* CHECKOUT */}
        {step === STEPS.CHECKOUT && (
          <div className="bg-vault-dark-card border border-white/5 rounded-[24px] overflow-hidden shadow-2xl">
            <div className="p-6 space-y-5">
              <div className="flex justify-between items-center">
                <span className="text-white/40 text-sm font-bold">Merchant</span>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center text-white font-black text-xs">BK</div>
                  <span className="text-white font-black text-lg">{merchant}</span>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-white/40 text-sm font-bold">Category</span>
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-orange-500/20 text-orange-300 uppercase tracking-wider">
                  Betting Platform
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-white/40 text-sm font-bold">Amount</span>
                <span className="text-white font-black text-2xl">₦{amount.toLocaleString('en-NG')}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-white/40 text-sm font-bold">Payment Method</span>
                <div className="flex items-center gap-2">
                  <CreditCard size={18} className="text-vault-cyan" />
                  <span className="text-white font-bold text-sm">Saved Visa Card {card}</span>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-white/40 text-sm font-bold">Paying From</span>
                <div className="flex items-center gap-2">
                  {accountLoading ? (
                    <>
                      <Loader2 size={14} className="text-white/40 animate-spin" />
                      <span className="text-white/40 text-xs font-medium">Detecting account...</span>
                    </>
                  ) : resolvedAccount ? (
                    <>
                      <User size={16} className="text-green-400" />
                      <span className="text-white font-bold text-sm font-mono">
                        ****{resolvedAccount.account_number.slice(-4)}
                      </span>
                    </>
                  ) : (
                    <span className="text-amber-400 text-xs font-bold">Not logged in</span>
                  )}
                </div>
              </div>

              <div className="border-t border-white/5" />

              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle size={14} className="text-amber-500" />
                  <span className="text-[10px] font-black text-amber-500 uppercase tracking-wider">Risk Indicators</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 text-amber-400/80 text-xs font-medium">
                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full" /> Betting Platform
                  </div>
                  <div className="flex items-center gap-2 text-amber-400/80 text-xs font-medium">
                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full" /> High Amount ₦250,000
                  </div>
                  <div className="flex items-center gap-2 text-amber-400/80 text-xs font-medium">
                    <span className="w-1.5 h-1.5 bg-orange-500 rounded-full" /> New Merchant — first BetKing transaction
                  </div>
                  <div className="flex items-center gap-2 text-amber-400/80 text-xs font-medium">
                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full" /> Late Night — {time}
                  </div>
                  <div className="flex items-center gap-2 text-amber-400/80 text-xs font-bold mt-2 pt-2 border-t border-amber-500/20">
                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
                    Pre-score estimate: ~{clientFloorScore}/100 — {scoreToLevel(clientFloorScore)}
                  </div>
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                <p className="text-white/30 text-[10px] leading-relaxed text-center">
                  Betting transactions are non-refundable once funds are wagered. Please gamble responsibly. 18+ only.
                </p>
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-xs text-red-400 font-bold">
                  {error}
                </div>
              )}
            </div>

            <div className="px-6 pb-6">
              <button
                onClick={handlePayNow}
                disabled={accountLoading}
                className="w-full vault-gradient disabled:opacity-60 disabled:cursor-not-allowed text-white py-4.5 rounded-xl font-black text-base shadow-lg vault-glow active:scale-[0.97] transition-all flex items-center justify-center gap-2"
                style={{ paddingTop: '18px', paddingBottom: '18px' }}
              >
                {accountLoading
                  ? <><Loader2 size={18} className="animate-spin" /> Detecting Account...</>
                  : <><ShieldAlert size={20} /> PAY NOW — ₦{amount.toLocaleString('en-NG')}</>
                }
              </button>
            </div>
          </div>
        )}

        {/* PROCESSING */}
        {step === STEPS.PROCESSING && (
          <div className="bg-vault-dark-card border border-white/5 rounded-[24px] p-10 text-center">
            <Loader2 size={48} className="text-vault-cyan animate-spin mx-auto mb-4" />
            <h3 className="text-white font-black text-lg mb-2">Processing Payment...</h3>
            <p className="text-white/40 text-sm">Sentinnel AI is analyzing this transaction</p>
          </div>
        )}

        {/* WAITING */}
        {step === STEPS.WAITING && (
          <div className="bg-vault-dark-card border border-white/5 rounded-[24px] overflow-hidden">
            <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-4 flex items-center gap-3">
              <Clock size={20} className="text-amber-400" />
              <div>
                <h3 className="text-amber-300 font-black text-sm">WAITING FOR CUSTOMER APPROVAL</h3>
                <p className="text-amber-400/60 text-[11px]">Transaction requires verification in banking app</p>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-white/40 font-bold">Transaction ID</span>
                <span className="text-white font-mono font-bold">{txnId}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/40 font-bold">Status</span>
                <span className="text-amber-400 font-bold uppercase flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />Pending Confirmation
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/40 font-bold">Merchant</span>
                <span className="text-white font-bold">{merchant}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/40 font-bold">Category</span>
                <span className="text-orange-300 font-bold text-xs uppercase">Betting Platform</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/40 font-bold">Amount</span>
                <span className="text-white font-bold">₦{amount.toLocaleString('en-NG')}</span>
              </div>

              {renderFraudPanel()}

              <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center mt-4">
                <p className="text-white/40 text-xs font-medium">
                  Open the <strong className="text-white">Sentinnel Banking App</strong> to approve or reject this transaction.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* RESULT */}
        {step === STEPS.RESULT && (
          <div className="bg-vault-dark-card border border-white/5 rounded-[24px] p-10 text-center">
            {result === 'APPROVED' ? (
              <>
                <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4 ring-4 ring-green-500/10">
                  <CheckCircle size={40} className="text-green-400" />
                </div>
                <h3 className="text-green-400 font-black text-xl mb-2">Payment Approved</h3>
                <p className="text-white/40 text-sm mb-1">Transaction ID: <span className="font-mono text-white/60">{txnId}</span></p>
                <p className="text-white/40 text-sm">Authorized via Sentinnel Biometric Verification</p>
              </>
            ) : (
              <>
                <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4 ring-4 ring-red-500/10">
                  <AlertTriangle size={40} className="text-red-400" />
                </div>
                <h3 className="text-red-400 font-black text-xl mb-2">Payment Rejected</h3>
                <p className="text-white/40 text-sm mb-1">Transaction ID: <span className="font-mono text-white/60">{txnId}</span></p>
                <p className="text-white/40 text-sm">Customer declined this transaction</p>
              </>
            )}
            <button
              onClick={() => { setStep(STEPS.CHECKOUT); setTxnId(''); setFraud(null); setResult(null); setError(''); }}
              className="mt-8 px-6 py-3 bg-white/10 border border-white/20 text-white rounded-xl font-bold text-sm hover:bg-white/20 active:scale-95 transition-all"
            >
              New Transaction
            </button>
          </div>
        )}

        <p className="text-center text-white/20 text-[10px] mt-6 uppercase tracking-widest font-bold">
          Sentinnel Payment Gateway • Simulated Merchant Environment
        </p>
      </div>
    </div>
  );
};

export default MerchantCheckout;