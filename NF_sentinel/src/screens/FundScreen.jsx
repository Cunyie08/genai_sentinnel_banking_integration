import { useNavigate } from 'react-router-dom';

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { fundWallet, clearLastTx } from '../features/transactionSlice';
import { ChevronLeft, Copy, CheckCircle, AlertCircle, CreditCard, Building2, Smartphone } from 'lucide-react';

const METHODS = [
  { id: 'bank_transfer', label: 'Bank Transfer',  icon: Building2,   desc: 'Transfer from any Nigerian bank' },
  { id: 'card',          label: 'Debit Card',      icon: CreditCard,  desc: 'Visa, Mastercard accepted'      },
  { id: 'ussd',          label: 'USSD',            icon: Smartphone,  desc: 'Fund with *737#, *901# etc.'    },
];

const QUICK_AMOUNTS = [1000, 2000, 5000, 10000, 20000, 50000, 100000];

const FundScreen = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const { isFunding, error, lastTx } = useSelector(s => s.transactions);
  const user = useSelector(s => s.auth.user);
  const [method,   setMethod]   = useState('bank_transfer');
  const [amount,   setAmount]   = useState('');
  const [copied,   setCopied]   = useState(false);

  const ACCOUNT_NUMBER = user?.accounts?.[0]?.account_number || '0123456789';

  const handleCopy = () => {
    navigator.clipboard?.writeText(ACCOUNT_NUMBER);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const accountNumber = user?.accounts?.[0]?.account_number;
    dispatch(fundWallet({ 
      amount: Number(amount), 
      method,
      account_number: accountNumber
    }));
  };

  const handleReset = () => {
    dispatch(clearLastTx());
    setAmount('');
  };

  
  if (lastTx?.type === 'credit') {
    return (
      <div className="min-h-full w-full bg-vault-light-bg dark:bg-vault-dark-bg flex flex-col items-center justify-center p-6 font-sans vault-transition">
        <div className="bg-white dark:bg-vault-dark-card rounded-3xl p-8 shadow-sm border border-gray-100 dark:border-white/5 w-full max-w-sm text-center">
          <div className="w-16 h-16 bg-green-50 dark:bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-500 dark:text-green-400" />
          </div>
          <h2 className="text-xl font-black text-gray-900 dark:text-white mb-1">Wallet Funded!</h2>
          <p className="text-gray-500 dark:text-slate-400 text-sm mb-1">₦{Number(lastTx.amount).toLocaleString()} added to your wallet.</p>
          <p className="text-[10px] text-gray-400 dark:text-slate-500 font-bold uppercase tracking-widest mb-6">Ref: {lastTx.ref}</p>
          <button onClick={handleReset}
            className="w-full vault-gradient text-white py-3.5 rounded-2xl font-bold text-sm transition-colors mb-3 vault-glow">
            Fund Again
          </button>
          <button onClick={() => navigate('/home')}
            className="w-full text-gray-500 dark:text-slate-400 text-sm font-bold hover:text-gray-700 dark:hover:text-white py-2">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full w-full bg-vault-light-bg dark:bg-vault-dark-bg font-sans vault-transition">
      <header className="sticky top-0 z-20 bg-vault-light-bg/95 dark:bg-vault-dark-bg/95 backdrop-blur-sm border-b border-gray-100 dark:border-white/5 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button onClick={() => navigate('/home')}
          className="w-9 h-9 rounded-xl bg-white dark:bg-vault-dark-card border border-gray-100 dark:border-white/5 flex items-center justify-center shadow-sm hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
          <ChevronLeft size={20} className="text-gray-600 dark:text-slate-400" />
        </button>
        <div>
          <p className="text-[10px] text-gray-400 dark:text-slate-500 font-bold uppercase tracking-widest leading-none">Wallet</p>
          <h1 className="text-lg font-extrabold text-gray-900 dark:text-white">Fund Wallet</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 pb-28 max-w-2xl xl:max-w-none">

        {}
        <div className="vault-gradient rounded-2xl p-5 text-white mb-5 relative overflow-hidden shadow-lg vault-glow">
          <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
          <p className="text-white/60 text-[10px] font-bold uppercase tracking-widest mb-3">Your Sentinnel Account</p>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-black tracking-widest mb-1">{ACCOUNT_NUMBER}</p>
              <p className="text-white/70 text-xs font-medium">Sentinnel MFB · {user?.name || 'Reuben'}</p>
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
          <div className="mb-5 p-3 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-red-600 dark:text-red-400 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          {}
          <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5">
            <p className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3">Funding Method</p>
            <div className="space-y-2">
              {METHODS.map(m => (
                <button key={m.id} type="button" onClick={() => setMethod(m.id)}
                  className={`w-full flex items-center gap-4 p-4 rounded-2xl border-2 text-left transition-all ${method === m.id ? 'border-vault-cyan bg-cyan-50 dark:bg-vault-cyan/10' : 'border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 hover:bg-gray-100 dark:hover:bg-white/10'}`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${method === m.id ? 'vault-gradient text-white' : 'bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-slate-400'}`}>
                    <m.icon size={18} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-bold ${method === m.id ? 'text-vault-cyan' : 'text-gray-800 dark:text-white'}`}>{m.label}</p>
                    <p className="text-[11px] text-gray-400 dark:text-slate-500">{m.desc}</p>
                  </div>
                  <div className={`w-4 h-4 rounded-full border-2 shrink-0 ${method === m.id ? 'border-vault-cyan bg-vault-cyan' : 'border-gray-300 dark:border-white/20'}`} />
                </button>
              ))}
            </div>
          </div>

          {}
          <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5">
            <p className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3">Amount</p>
            <div className="grid grid-cols-3 sm:grid-cols-7 gap-2 mb-4">
              {QUICK_AMOUNTS.map(a => (
                <button key={a} type="button" onClick={() => setAmount(String(a))}
                  className={`py-2.5 rounded-xl text-xs font-bold border-2 transition-all ${amount === String(a) ? 'vault-gradient text-white border-transparent' : 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-slate-300 border-gray-100 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/10'}`}>
                  ₦{a >= 1000 ? (a/1000)+'k' : a}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 bg-gray-50 dark:bg-vault-dark-input border border-gray-200 dark:border-white/5 rounded-xl px-4 focus-within:border-vault-cyan focus-within:ring-2 focus-within:ring-vault-cyan/10 transition-all">
              <span className="text-gray-500 dark:text-slate-400 font-bold text-sm">₦</span>
              <input type="number" placeholder="Or enter custom amount"
                value={amount} onChange={e => setAmount(e.target.value)}
                className="flex-1 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500" />
            </div>
          </div>

          <button type="submit" disabled={isFunding || !amount}
            className="w-full vault-gradient text-white py-4 rounded-2xl font-bold text-sm shadow-lg vault-glow transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed">
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