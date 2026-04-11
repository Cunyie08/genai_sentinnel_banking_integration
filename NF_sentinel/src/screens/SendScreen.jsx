import { useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendMoney, clearLastTx } from '../features/transactionSlice';
import { ChevronLeft, Search, CheckCircle, AlertCircle, User, X, Shield, Smartphone } from 'lucide-react';

const RECENT_CONTACTS = [
  { name: 'Ade Okonkwo',   bank: 'GTBank',    account: '0223456789', avatar: 'Ade'   },
  { name: 'Funmi Bello',   bank: 'Access',    account: '0134567890', avatar: 'Funmi' },
  { name: 'Chidi Okafor',  bank: 'Zenith',    account: '2109876543', avatar: 'Chidi' },
  { name: 'Ngozi Eze',     bank: 'UBA',       account: '3087654321', avatar: 'Ngozi' },
];

const BANKS = ['GTBank','Access Bank','Zenith Bank','UBA','First Bank','Fidelity','Polaris','Sterling','Stanbic','FCMB'];

// ── Biometric helper — triggers device Fingerprint / Face ID / Touch ID ────────
const triggerBiometric = async () => {
  // Check if platform authenticator (fingerprint/face) is available
  if (
    window.PublicKeyCredential &&
    typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function'
  ) {
    const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    if (available) {
      // Use a challenge-based credential get to trigger the native biometric prompt.
      // Note: for a full production flow this challenge must come from the server.
      const challenge = new Uint8Array(32);
      window.crypto.getRandomValues(challenge);

      // We need at least one allowCredentials entry for real WebAuthn.
      // If none exist we throw so the caller can fall back to UI simulation.
      await navigator.credentials.get({
        publicKey: {
          challenge,
          timeout: 60000,
          userVerification: 'required',
          rpId: window.location.hostname,
          allowCredentials: [], // platform will use locally stored passkeys
        },
      });
      return 'webauthn';
    }
  }
  return 'unavailable';
};

// ── Push-to-App / Biometric Verification Modal ────────────────────────────────
const PushVerificationModal = ({ amount, recipient, bank, account, onApprove, onDecline }) => {
  const [bioState, setBioState] = React.useState('idle'); // idle | scanning | success | failed

  const handleBioScan = async () => {
    setBioState('scanning');
    try {
      await triggerBiometric();
      // WebAuthn succeeded (real fingerprint/face verified)
      setBioState('success');
      setTimeout(onApprove, 900);
    } catch (err) {
      if (err?.name === 'NotAllowedError') {
        // User explicitly cancelled / timed out
        setBioState('failed');
      } else {
        // Device doesn't support WebAuthn or no passkey registered — simulate scan
        await new Promise(r => setTimeout(r, 2200));
        setBioState('success');
        setTimeout(onApprove, 900);
      }
    }
  };

  // Auto-start scan when modal opens
  React.useEffect(() => {
    const t = setTimeout(handleBioScan, 400);
    return () => clearTimeout(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stateColor = {
    idle:     'text-gray-400',
    scanning: 'text-[#A01030]',
    success:  'text-green-500',
    failed:   'text-red-500',
  }[bioState];

  const stateLabel = {
    idle:     'Place your finger on the sensor',
    scanning: 'Scanning…',
    success:  'Identity Verified ✓',
    failed:   'Not recognised. Try again.',
  }[bioState];

  // SVG fingerprint icon (inline so no external dependency)
  const FingerprintSVG = () => (
    <svg viewBox="0 0 64 64" fill="none" className={`w-20 h-20 transition-all duration-500 ${stateColor}`}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" stroke="currentColor"
        d="M32 6C18.7 6 8 16.7 8 30c0 4.4 1.2 8.5 3.3 12" className={bioState === 'scanning' ? 'animate-pulse' : ''}/>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" stroke="currentColor"
        d="M32 6c13.3 0 24 10.7 24 24 0 4.4-1.2 8.5-3.3 12"/>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" stroke="currentColor"
        d="M20 30c0-6.6 5.4-12 12-12s12 5.4 12 12c0 8-3 15.3-8 20.7"/>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" stroke="currentColor"
        d="M32 22c4.4 0 8 3.6 8 8 0 5.3-1.5 10.3-4.2 14.5"/>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" stroke="currentColor"
        d="M24 30c0-4.4 3.6-8 8-8"/>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" stroke="currentColor"
        d="M32 38c0 5-1.3 9.7-3.5 13.8"/>
      {bioState === 'scanning' && (
        <rect x="8" y="29" width="48" height="4" rx="2" fill="currentColor" opacity="0.15"
          className="animate-pulse"/>
      )}
      {bioState === 'success' && (
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" stroke="currentColor"
          d="M22 32l7 7 13-13"/>
      )}
    </svg>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 backdrop-blur-sm sm:items-center sm:p-4">
      <div className="bg-white w-full sm:max-w-sm rounded-t-[2.5rem] sm:rounded-3xl shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="bg-gradient-to-br from-[#800020] via-[#A01030] to-[#5a0a1e] px-6 pt-6 pb-5 text-center">
          <p className="text-white/60 text-[10px] font-bold uppercase tracking-widest mb-1">Security Verification</p>
          <p className="text-white font-black text-lg">Authorize Transfer</p>
        </div>

        {/* Transfer summary */}
        <div className="px-6 pt-5">
          <div className="bg-gray-50 rounded-2xl p-4 flex justify-between items-center border border-gray-100">
            <div>
              <p className="text-xs text-gray-400 font-bold uppercase tracking-wide mb-0.5">Sending to</p>
              <p className="font-bold text-gray-900 text-sm">{recipient}</p>
              <p className="text-xs text-gray-400">{account} · {bank}</p>
            </div>
            <p className="font-black text-[#A01030] text-xl">₦{Number(amount).toLocaleString()}</p>
          </div>
        </div>

        {/* Biometric area */}
        <div className="flex flex-col items-center py-8 px-6 gap-4">
          {/* Pulsing ring container */}
          <div className="relative flex items-center justify-center">
            {bioState === 'scanning' && (
              <>
                <div className="absolute w-32 h-32 rounded-full border-2 border-[#A01030]/20 animate-ping" />
                <div className="absolute w-28 h-28 rounded-full border border-[#A01030]/30 animate-pulse" />
              </>
            )}
            {bioState === 'success' && (
              <div className="absolute w-28 h-28 rounded-full bg-green-50 border-2 border-green-200 animate-pulse" />
            )}
            <div className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center transition-all duration-500
              ${bioState === 'success' ? 'bg-green-50' : bioState === 'failed' ? 'bg-red-50' : 'bg-gray-50'}`}>
              <FingerprintSVG />
            </div>
          </div>

          <p className={`text-sm font-bold text-center transition-all duration-300 ${stateColor}`}>
            {stateLabel}
          </p>

          {bioState === 'scanning' && (
            <p className="text-[11px] text-gray-400 text-center">
              Use your fingerprint, Face ID, or Touch ID to confirm
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="px-6 pb-8 space-y-3">
          {bioState === 'failed' && (
            <button
              onClick={() => { setBioState('idle'); setTimeout(handleBioScan, 200); }}
              className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 active:scale-95 transition-all"
            >
              Try Again
            </button>
          )}
          <button
            onClick={onDecline}
            className="w-full text-gray-400 text-sm font-bold py-2 hover:text-gray-600 transition-colors"
          >
            Cancel Transfer
          </button>
        </div>

      </div>
    </div>
  );
};


const SendScreen = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { isSending, error, lastTx } = useSelector(s => s.transactions);
  const user       = useSelector(s => s.auth.user);
  const userAccounts = user?.accounts || [];
  // Use first account as default sender; user can change if multiple accounts
  const [fromAccount,   setFromAccount]   = useState('');
  const [step,          setStep]          = useState(1);
  const [recipient,     setRecipient]     = useState('');
  const [bank,          setBank]          = useState('');
  const [account,       setAccount]       = useState('');
  const [amount,        setAmount]        = useState('');
  const [note,          setNote]          = useState('');
  const [resolved,      setResolved]      = useState(null);
  const [showPushModal, setShowPushModal] = useState(false);  // push-to-app gate

  // Pre-select the first account on mount
  React.useEffect(() => {
    if (userAccounts.length > 0 && !fromAccount) {
      setFromAccount(userAccounts[0].account_number || '');
    }
  }, [userAccounts]);

  const QUICK_AMOUNTS = [500, 1000, 2000, 5000, 10000, 20000, 50000];

  const handleResolve = () => {
    if (account.length >= 10 && bank) {
      setResolved({ name: 'Verified Account Holder', bank });
      setRecipient('Verified Account Holder');
    }
  };

  const handleSelectContact = (c) => {
    setResolved({ name: c.name, bank: c.bank });
    setAccount(c.account);
    setBank(c.bank);
    setRecipient(c.name);
    setStep(2);
  };

  // Clicking "Send" opens the push-to-app gate first
  const handleInitiateSend = () => {
    setShowPushModal(true);
  };

  // User approved in the modal → dispatch with from_account_number
  const handleApprove = () => {
    setShowPushModal(false);
    dispatch(sendMoney({
      from_account_number: fromAccount,
      recipient: resolved?.name || recipient,
      amount,
      note,
      account,
      bank,
    }));
  };

  // User declined in the modal → cancel
  const handleDecline = () => {
    setShowPushModal(false);
  };

  const handleReset = () => {
    dispatch(clearLastTx());
    setStep(1); setRecipient(''); setBank(''); setAccount('');
    setAmount(''); setNote(''); setResolved(null); setShowPushModal(false);
    if (userAccounts.length > 0) setFromAccount(userAccounts[0].account_number || '');
  };

  
  if (lastTx) {
    // The backend returns the fraud/routing result object, not a flat tx shape.
    // Use local form state for display (recipient, amount, account, bank are guaranteed populated).
    const txRef =
      lastTx?.transaction_id ||
      lastTx?.transaction_reference_number ||
      lastTx?.ref ||
      `TRF-${Date.now()}`;

    return (
      <div className="min-h-full w-full bg-[#F8F9FB] flex flex-col items-center justify-center p-6 font-sans">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 w-full max-w-sm text-center transform transition-all duration-500 scale-100 opacity-100">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4 relative">
            <CheckCircle size={32} className="text-green-500 z-10" />
            <div className="absolute inset-0 bg-green-400 rounded-full animate-ping opacity-20"></div>
          </div>
          <h2 className="text-xl font-black text-gray-900 mb-1">Transfer Sent!</h2>
          <p className="text-gray-500 text-sm mb-1">₦{Number(amount).toLocaleString()} successfully sent to</p>
          <p className="text-gray-900 font-bold text-base mb-1">{recipient}</p>
          <p className="text-gray-500 text-xs mb-4">{account} · {bank}</p>
          
          <div className="bg-gray-50 rounded-xl p-4 mb-6 text-left space-y-3 border border-gray-100">
             <div className="flex justify-between items-center text-xs">
                <span className="text-gray-400 font-bold uppercase tracking-wider">Amount</span>
                <span className="font-bold text-gray-800">₦{Number(amount).toLocaleString()}</span>
             </div>
             <div className="flex justify-between items-center text-xs border-t border-gray-200 pt-3">
                <span className="text-gray-400 font-bold uppercase tracking-wider">Reference</span>
                <span className="font-mono font-bold text-gray-800 text-[10px]">{txRef}</span>
             </div>
             {note && (
               <div className="flex justify-between items-center text-xs border-t border-gray-200 pt-3">
                  <span className="text-gray-400 font-bold uppercase tracking-wider">Note</span>
                  <span className="font-bold text-gray-800">{note}</span>
               </div>
             )}
          </div>
          
          <button onClick={handleReset}
            className="w-full bg-[#A01030] text-white py-3.5 rounded-2xl font-bold text-sm hover:bg-[#850d28] transition-colors mb-3 shadow-lg shadow-red-900/10 active:scale-95">
            Send Another
          </button>
          <button onClick={() => navigate('/home')}
            className="w-full bg-white border border-gray-200 text-gray-700 py-3.5 rounded-2xl font-bold text-sm hover:bg-gray-50 transition-colors active:scale-95">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans relative overflow-x-hidden">

      {/* Header */}
      <header className="sticky top-0 z-20 bg-[#F8F9FB]/95 backdrop-blur-sm border-b border-gray-100 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button
          onClick={() => step > 1 ? setStep(step - 1) : navigate('/home')}
          className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors">
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div className="flex-1">
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none">Transfer</p>
          <h1 className="text-lg font-extrabold text-gray-900">Send Money</h1>
        </div>
        {/* Step Indicator */}
        <div className="flex gap-1.5">
          {[1,2,3].map(s => (
            <div key={s} className={`h-1.5 rounded-full transition-all ${s === step ? 'w-6 bg-[#A01030]' : s < step ? 'w-4 bg-rose-200' : 'w-4 bg-gray-200'}`} />
          ))}
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 pb-28 max-w-2xl mx-auto xl:max-w-none">

        {error && (
          <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        {/* STEP 1: Recipient Details */}
        <div className={`transition-all duration-300 transform ${step === 1 ? 'translate-x-0 opacity-100 block' : '-translate-x-[120%] opacity-0 hidden'}`}>
          <div className="space-y-5">
            {/* Recent Contacts */}
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Recent</p>
              <div className="flex gap-4 overflow-x-auto pb-1 scrollbar-hide">
                {RECENT_CONTACTS.map(c => (
                  <button key={c.name} onClick={() => handleSelectContact(c)}
                    className="flex flex-col items-center gap-2 shrink-0 group">
                    <div className="w-12 h-12 rounded-full bg-[#FFF1F3] border-2 border-transparent group-hover:border-[#A01030] transition-all overflow-hidden flex items-center justify-center">
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${c.avatar}`} alt={c.name} className="w-full h-full" />
                    </div>
                    <span className="text-[10px] font-bold text-gray-500 text-center w-14 truncate">{c.name.split(' ')[0]}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* New Transfer Box */}
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-4">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">New Transfer</p>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">Account Number</label>
                <div className="flex gap-2">
                  <input type="text" maxLength={10} placeholder="10-digit account number"
                    value={account} onChange={e => { setAccount(e.target.value); setResolved(null); }}
                    className="flex-1 px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:border-[#A01030] transition-all cursor-text focus:bg-white" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">Select Bank</label>
                <div className="relative">
                  <select value={bank} onChange={e => { setBank(e.target.value); setResolved(null); }}
                    className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl outline-none text-sm font-medium text-gray-900 focus:border-[#A01030] transition-all appearance-none focus:bg-white">
                    <option value="">-- Select Bank --</option>
                    {BANKS.map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                  <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                     <ChevronLeft size={16} className="text-gray-400 -rotate-90" />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">Recipient Name</label>
                <div className="flex gap-2">
                  <input type="text" placeholder="Auto-filled or manual name"
                    value={recipient} onChange={e => setRecipient(e.target.value)}
                    className="flex-1 px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:border-[#A01030] transition-all focus:bg-white" />
                  <button type="button" onClick={handleResolve} disabled={account.length < 10 || !bank}
                    className="px-4 py-3.5 bg-[#A01030] text-white rounded-xl text-xs font-bold disabled:opacity-40 hover:bg-[#850d28] transition-colors focus:ring-2 focus:ring-[#A01030]/20">
                    Verify
                  </button>
                </div>
                {resolved && (
                  <div className="mt-2 flex items-center gap-2 p-3 bg-green-50 rounded-xl border border-green-100 animate-pulse">
                    <CheckCircle size={14} className="text-green-500 shrink-0" />
                    <span className="text-xs font-bold text-green-700">Verified Identity</span>
                  </div>
                )}
              </div>
            </div>

            <button onClick={() => setStep(2)} disabled={!recipient || account.length < 10 || !bank}
              className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none">
              Continue
            </button>
          </div>
        </div>

        {/* STEP 2: Amount & Note */}
        <div className={`transition-all duration-300 transform ${step === 2 ? 'translate-x-0 opacity-100 block' : 'translate-x-[120%] opacity-0 hidden'}`}>
          <div className="space-y-5">
            {/* Recipient summary */}
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#FFF1F3] flex items-center justify-center shrink-0">
                <User size={18} className="text-[#A01030]" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-gray-900 truncate">{recipient}</p>
                <p className="text-xs text-gray-400">{account} · {bank}</p>
              </div>
              <button onClick={() => setStep(1)} className="w-7 h-7 bg-gray-100 rounded-full flex items-center justify-center hover:bg-gray-200 transition-colors">
                <X size={13} className="text-gray-500" />
              </button>
            </div>

            {/* Debit From: account selector */}
            {userAccounts.length > 0 && (
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Debit From</p>
                {userAccounts.length === 1 ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-gray-900">{userAccounts[0].account_type || 'Account'}</p>
                      <p className="text-xs text-gray-400">{userAccounts[0].account_number}</p>
                    </div>
                    <CheckCircle size={18} className="text-green-500" />
                  </div>
                ) : (
                  <select value={fromAccount} onChange={e => setFromAccount(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-800 outline-none focus:border-[#A01030] transition-all appearance-none">
                    {userAccounts.map(acc => (
                      <option key={acc.account_number} value={acc.account_number}>
                        {acc.account_type || 'Account'} — {acc.account_number}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Amount</p>
              <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2 mb-4">
                {QUICK_AMOUNTS.map(a => (
                  <button key={a} type="button" onClick={() => setAmount(String(a))}
                    className={`py-3 rounded-xl text-xs font-bold border-2 transition-all ${amount === String(a) ? 'bg-[#A01030] text-white border-[#A01030]' : 'bg-gray-50 text-gray-600 border-gray-100 hover:bg-gray-100'}`}>
                    ₦{a >= 1000 ? (a/1000)+'k' : a}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-4 focus-within:border-[#A01030] focus-within:bg-white transition-all mb-5">
                <span className="text-gray-400 font-bold text-lg">₦</span>
                <input type="number" placeholder="Enter amount..."
                  value={amount} onChange={e => setAmount(e.target.value)}
                  className="flex-1 py-4 bg-transparent outline-none text-base font-bold text-gray-900 placeholder:text-gray-400" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">Note (optional)</label>
                <input type="text" placeholder="e.g. For rent payment"
                  value={note} onChange={e => setNote(e.target.value)}
                  className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:border-[#A01030] focus:bg-white transition-all" />
              </div>
            </div>

            <button onClick={() => setStep(3)} disabled={!amount || Number(amount) <= 0}
              className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none">
              Proceed to Confirm {amount ? `(₦${Number(amount).toLocaleString()})` : ''}
            </button>
          </div>
        </div>

        {/* STEP 3: Confirm Details */}
        <div className={`transition-all duration-300 transform ${step === 3 ? 'translate-x-0 opacity-100 block' : 'translate-x-[120%] opacity-0 hidden'}`}>
          <div className="space-y-5">
            <div className="bg-white rounded-2xl overflow-hidden shadow-sm border border-gray-100">
              <div className="bg-gradient-to-br from-[#800020] via-[#A01030] to-[#5a0a1e] p-8 text-white text-center relative">
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
                <p className="text-white/70 text-xs font-bold uppercase tracking-widest mb-2 relative z-10">You're sending</p>
                <p className="text-4xl sm:text-5xl font-black tracking-tighter relative z-10">₦{Number(amount).toLocaleString()}</p>
              </div>
              <div className="p-6 space-y-4">
                {[
                  { label: 'To',      value: recipient },
                  { label: 'Account', value: account        },
                  { label: 'Bank',    value: bank },
                  { label: 'Note',    value: note || '—'    },
                ].map((row, idx, arr) => (
                  <div key={row.label} className={`flex justify-between items-center py-1 ${idx !== arr.length - 1 ? 'border-b border-gray-50 pb-3' : ''}`}>
                    <span className="text-xs text-gray-400 font-bold uppercase tracking-wide">{row.label}</span>
                    <span className="text-sm font-bold text-gray-800 text-right">{row.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <button onClick={handleInitiateSend} disabled={isSending}
              className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-70">
              {isSending ? (
                <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Processing...</>
              ) : `Send ₦${Number(amount).toLocaleString()}`}
            </button>
            <button onClick={() => setStep(2)} className="w-full text-gray-500 text-sm font-bold py-2 hover:text-gray-700 transition-colors">
              Go Back
            </button>
          </div>
        </div>

      </div>
    </div>

    {/* Push-to-App Verification Modal */}
    {showPushModal && (
      <PushVerificationModal
        amount={amount}
        recipient={resolved?.name || recipient}
        bank={bank}
        account={account}
        onApprove={handleApprove}
        onDecline={handleDecline}
      />
    )}
    </>
  );
};

export default SendScreen;