// src/screens/FundScreen.jsx
import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setRoute } from '../features/uiSlice';
import { fundWallet, clearLastTx } from '../features/transactionSlice';
import { ChevronLeft, Copy, CheckCircle, AlertCircle, CreditCard, Building2, Smartphone } from 'lucide-react';

const METHODS = [
  { id: 'bank_transfer', label: 'Bank Transfer',  icon: Building2,   desc: 'Transfer from any Nigerian bank' },
  { id: 'card',          label: 'Debit Card',      icon: CreditCard,  desc: 'Visa, Mastercard accepted'      },
  { id: 'ussd',          label: 'USSD',            icon: Smartphone,  desc: 'Fund with *737#, *901# etc.'    },
];

const QUICK_AMOUNTS = [1000, 2000, 5000, 10000, 20000, 50000, 100000];

const FundScreen = () => {
  const dispatch = useDispatch();
  const { isFunding, error, lastTx } = useSelector(s => s.transactions);
  const user = useSelector(s => s.auth.user);
  const [method,   setMethod]   = useState('bank_transfer');
  const [amount,   setAmount]   = useState('');
  const [copied,   setCopied]   = useState(false);

  const ACCOUNT_NUMBER = user?.account || '0123456789';

  const handleCopy = () => {
    navigator.clipboard?.writeText(ACCOUNT_NUMBER);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(fundWallet({ amount, method }));
  };

  const handleReset = () => {
    dispatch(clearLastTx());
    setAmount('');
  };

  // ── Success ──────────────────────────────────────────────────────────────
  if (lastTx?.type === 'credit') {
    return (
      <div className="min-h-full w-full bg-[#F8F9FB] flex flex-col items-center justify-center p-6 font-sans">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 w-full max-w-sm text-center">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-500" />
          </div>
          <h2 className="text-xl font-black text-gray-900 mb-1">Wallet Funded!</h2>
          <p className="text-gray-500 text-sm mb-1">₦{Number(lastTx.amount).toLocaleString()} added to your wallet.</p>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-6">Ref: {lastTx.ref}</p>
          <button onClick={handleReset}
            className="w-full bg-[#A01030] text-white py-3.5 rounded-2xl font-bold text-sm hover:bg-[#850d28] transition-colors mb-3">
            Fund Again
          </button>
          <button onClick={() => dispatch(setRoute('home'))}
            className="w-full text-gray-500 text-sm font-bold hover:text-gray-700 py-2">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans">
      <header className="sticky top-0 z-20 bg-[#F8F9FB]/95 backdrop-blur-sm border-b border-gray-100 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button onClick={() => dispatch(setRoute('home'))}
          className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors">
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none">Wallet</p>
          <h1 className="text-lg font-extrabold text-gray-900">Fund Wallet</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 max-w-2xl xl:max-w-none">

        {/* Nexa account details — always visible */}
        <div className="bg-gradient-to-br from-[#9F1239] to-[#881337] rounded-2xl p-5 text-white mb-5 relative overflow-hidden shadow-lg shadow-red-900/20">
          <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
          <p className="text-white/60 text-[10px] font-bold uppercase tracking-widest mb-3">Your Nexa Account</p>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-black tracking-widest mb-1">{ACCOUNT_NUMBER}</p>
              <p className="text-white/70 text-xs font-medium">Nexa MFB · {user?.name || 'Reuben'}</p>
            </div>
            <button onClick={handleCopy}
              className="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 backdrop-blur-sm px-3 py-2 rounded-xl border border-white/20 transition-all active:scale-95">
              <Copy size={14} />
              <span className="text-xs font-bold">{copied ? 'Copied!' : 'Copy'}</span>
            </button>
          </div>
          <p className="text-white/50 text-[10px] mt-3 font-medium">Transfer to this account from any bank to fund instantly</p>
        </div>

        {error && (
          <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Funding method */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Funding Method</p>
            <div className="space-y-2">
              {METHODS.map(m => (
                <button key={m.id} type="button" onClick={() => setMethod(m.id)}
                  className={`w-full flex items-center gap-4 p-4 rounded-2xl border-2 text-left transition-all ${method === m.id ? 'border-[#A01030] bg-rose-50' : 'border-gray-100 bg-gray-50 hover:bg-gray-100'}`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${method === m.id ? 'bg-[#A01030] text-white' : 'bg-gray-200 text-gray-500'}`}>
                    <m.icon size={18} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-bold ${method === m.id ? 'text-[#A01030]' : 'text-gray-800'}`}>{m.label}</p>
                    <p className="text-[11px] text-gray-400">{m.desc}</p>
                  </div>
                  <div className={`w-4 h-4 rounded-full border-2 shrink-0 ${method === m.id ? 'border-[#A01030] bg-[#A01030]' : 'border-gray-300'}`} />
                </button>
              ))}
            </div>
          </div>

          {/* Amount */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Amount</p>
            <div className="grid grid-cols-3 sm:grid-cols-7 gap-2 mb-4">
              {QUICK_AMOUNTS.map(a => (
                <button key={a} type="button" onClick={() => setAmount(String(a))}
                  className={`py-2.5 rounded-xl text-xs font-bold border-2 transition-all ${amount === String(a) ? 'bg-[#A01030] text-white border-[#A01030]' : 'bg-gray-50 text-gray-600 border-gray-100 hover:bg-gray-100'}`}>
                  ₦{a >= 1000 ? (a/1000)+'k' : a}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-4 focus-within:border-[#A01030] focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all">
              <span className="text-gray-500 font-bold text-sm">₦</span>
              <input type="number" placeholder="Or enter custom amount"
                value={amount} onChange={e => setAmount(e.target.value)}
                className="flex-1 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400" />
            </div>
          </div>

          <button type="submit" disabled={isFunding || !amount}
            className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed">
            {isFunding ? (
              <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Processing...</>
            ) : `Fund ₦${amount ? Number(amount).toLocaleString() : '0'}`}
          </button>
        </form>
      </div>
    </div>
  );
};

export default FundScreen;