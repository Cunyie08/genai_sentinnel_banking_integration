import { useNavigate } from 'react-router-dom';

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { fundBetting, resetService } from '../features/servicesSlice';
import { ChevronLeft, Gamepad2, CheckCircle, AlertCircle } from 'lucide-react';

const PLATFORMS = [
  { id: 'bet9ja',    name: 'Bet9ja',    color: 'bg-green-600'  },
  { id: 'sportybet', name: 'SportyBet', color: 'bg-yellow-500' },
  { id: '1xbet',     name: '1xBet',     color: 'bg-blue-600'   },
  { id: 'betway',    name: 'Betway',    color: 'bg-green-500'  },
  { id: 'bangbet',   name: 'BangBet',   color: 'bg-red-600'    },
  { id: 'nairabet',  name: 'NairaBet',  color: 'bg-orange-500' },
];

const QUICK_AMOUNTS = [500, 1000, 2000, 5000, 10000, 20000];

const BettingScreen = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const { isLoading, status, lastResult, error } = useSelector(s => s.services);
  const [platform, setPlatform] = useState('');
  const [userId,   setUserId]   = useState('');
  const [amount,   setAmount]   = useState('');

  const user = useSelector(s => s.auth.user);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    const account = user?.accounts?.[0];
    dispatch(fundBetting({ 
      platform, 
      userId, 
      amount: Number(amount),
      account_number: account?.account_number
    }));
  };

  const handleReset = () => { dispatch(resetService()); setAmount(''); setUserId(''); };

  if (status === 'success' && lastResult?.service === 'betting') {
    return (
      <div className="min-h-full w-full bg-[#F8F9FB] flex flex-col items-center justify-center p-6 font-sans">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 w-full max-w-sm text-center">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-500" />
          </div>
          <h2 className="text-xl font-black text-gray-900 mb-1">Wallet Funded!</h2>
          <p className="text-gray-500 text-sm mb-4">₦{Number(lastResult.amount).toLocaleString()} sent to your {lastResult.platform} wallet.</p>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-6">Ref: {lastResult.ref}</p>
          <button onClick={handleReset} className="w-full bg-[#A01030] text-white py-3.5 rounded-2xl font-bold text-sm hover:bg-[#850d28] transition-colors">
            Fund Again
          </button>
          <button onClick={() => navigate('/home')} className="w-full mt-3 text-gray-500 text-sm font-bold hover:text-gray-700 py-2">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans">
      <header className="sticky top-0 z-20 bg-[#F8F9FB]/95 backdrop-blur-sm border-b border-gray-100 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button onClick={() => navigate('/home')}
          className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors">
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none">Services</p>
          <h1 className="text-lg font-extrabold text-gray-900">Betting Wallet</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 pb-28 max-w-2xl xl:max-w-none">
        {error && (
          <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Select Platform</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
              {PLATFORMS.map(p => (
                <button key={p.id} type="button" onClick={() => setPlatform(p.id)}
                  className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${platform === p.id ? 'border-[#A01030] bg-rose-50' : 'border-gray-100 bg-gray-50 hover:bg-gray-100'}`}>
                  <div className={`w-10 h-10 ${p.color} rounded-xl flex items-center justify-center`}>
                    <Gamepad2 size={18} className="text-white" />
                  </div>
                  <span className={`text-[10px] font-bold text-center leading-tight ${platform === p.id ? 'text-[#A01030]' : 'text-gray-500'}`}>{p.name}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Betting User ID</p>
            <input type="text" placeholder="Enter your betting account ID / username"
              value={userId} onChange={e => setUserId(e.target.value)}
              className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:border-[#A01030] focus:ring-2 focus:ring-[#A01030]/10 transition-all" />
          </div>

          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Amount</p>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-4">
              {QUICK_AMOUNTS.map(a => (
                <button key={a} type="button" onClick={() => setAmount(String(a))}
                  className={`py-2.5 rounded-xl text-xs font-bold border-2 transition-all ${amount === String(a) ? 'bg-[#A01030] text-white border-[#A01030]' : 'bg-gray-50 text-gray-600 border-gray-100 hover:bg-gray-100'}`}>
                  ₦{a.toLocaleString()}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-4 focus-within:border-[#A01030] transition-all">
              <span className="text-gray-500 font-bold text-sm">₦</span>
              <input type="number" placeholder="Or enter custom amount" value={amount} onChange={e => setAmount(e.target.value)}
                className="flex-1 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400" />
            </div>
          </div>

          <p className="text-[10px] text-gray-400 text-center leading-relaxed px-2 flex justify-center items-center gap-1">
            <AlertCircle size={14} /> Please gamble responsibly. This service is for adults 18+ only. Sentinnel does not promote gambling.
          </p>

          <button type="submit" disabled={isLoading || !platform || !userId || !amount}
            className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed">
            {isLoading ? 'Processing...' : `Fund ₦${amount ? Number(amount).toLocaleString() : '0'}`}
          </button>
        </form>
      </div>
    </div>
  );
};

export default BettingScreen;