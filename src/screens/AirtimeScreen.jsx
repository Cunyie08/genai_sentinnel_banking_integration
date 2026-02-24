// src/screens/AirtimeScreen.jsx
import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setRoute } from '../features/uiSlice';
import { buyAirtime } from '../features/servicesSlice';
import { resetService } from '../features/servicesSlice';
import { ChevronLeft, Smartphone, CheckCircle, AlertCircle, X } from 'lucide-react';

const NETWORKS = [
  { id: 'mtn',   name: 'MTN',      color: 'bg-yellow-400', text: 'text-yellow-900' },
  { id: 'airtel',name: 'Airtel',   color: 'bg-red-500',    text: 'text-white'      },
  { id: 'glo',   name: 'Glo',      color: 'bg-green-500',  text: 'text-white'      },
  { id: '9mobile',name:'9Mobile',  color: 'bg-emerald-600',text: 'text-white'      },
];

const QUICK_AMOUNTS = [100, 200, 500, 1000, 2000, 5000];

const AirtimeScreen = () => {
  const dispatch = useDispatch();
  const { isLoading, status, lastResult, error } = useSelector(s => s.services);
  const [network, setNetwork] = useState('mtn');
  const [phone,   setPhone]   = useState('');
  const [amount,  setAmount]  = useState('');
  const [isSelf,  setIsSelf]  = useState(true);

  const user = useSelector(s => s.auth.user);

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(buyAirtime({ network, phone: isSelf ? user?.phone : phone, amount }));
  };

  const handleReset = () => {
    dispatch(resetService());
    setAmount(''); setPhone('');
  };

  // ── Success screen ─────────────────────────────────────────────────────
  if (status === 'success' && lastResult?.service === 'airtime') {
    return (
      <div className="min-h-full w-full bg-[#F8F9FB] flex flex-col items-center justify-center p-6 font-sans">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 w-full max-w-sm text-center">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-500" />
          </div>
          <h2 className="text-xl font-black text-gray-900 mb-1">Airtime Sent!</h2>
          <p className="text-gray-500 text-sm mb-4">₦{Number(lastResult.amount).toLocaleString()} {lastResult.network?.toUpperCase()} airtime sent successfully.</p>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-6">Ref: {lastResult.ref}</p>
          <button onClick={handleReset} className="w-full bg-[#A01030] text-white py-3.5 rounded-2xl font-bold text-sm hover:bg-[#850d28] transition-colors">
            Buy More Airtime
          </button>
          <button onClick={() => dispatch(setRoute('home'))} className="w-full mt-3 text-gray-500 text-sm font-bold hover:text-gray-700 py-2">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans">

      {/* Header */}
      <header className="sticky top-0 z-20 bg-[#F8F9FB]/95 backdrop-blur-sm border-b border-gray-100 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button onClick={() => dispatch(setRoute('home'))}
          className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors">
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none">Services</p>
          <h1 className="text-lg font-extrabold text-gray-900">Buy Airtime</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 max-w-2xl xl:max-w-none">

        {error && (
          <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Network selector */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Select Network</p>
            <div className="grid grid-cols-4 gap-3">
              {NETWORKS.map(n => (
                <button key={n.id} type="button" onClick={() => setNetwork(n.id)}
                  className={`flex flex-col items-center gap-2 p-3 rounded-2xl border-2 transition-all ${network === n.id ? 'border-[#A01030] bg-rose-50' : 'border-gray-100 bg-gray-50 hover:bg-gray-100'}`}>
                  <div className={`w-10 h-10 ${n.color} rounded-xl flex items-center justify-center`}>
                    <span className={`text-[10px] font-black ${n.text}`}>{n.name.slice(0,3)}</span>
                  </div>
                  <span className={`text-[10px] font-bold ${network === n.id ? 'text-[#A01030]' : 'text-gray-500'}`}>{n.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Phone number */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Phone Number</p>
            <div className="flex gap-3 mb-3">
              {['My Number', "Someone Else's"].map((label, i) => (
                <button key={i} type="button" onClick={() => setIsSelf(i === 0)}
                  className={`flex-1 py-2.5 rounded-xl text-xs font-bold border-2 transition-all ${isSelf === (i === 0) ? 'bg-[#A01030] text-white border-[#A01030]' : 'bg-gray-50 text-gray-500 border-gray-100 hover:bg-gray-100'}`}>
                  {label}
                </button>
              ))}
            </div>
            {!isSelf && (
              <div className="flex bg-gray-50 border border-gray-200 rounded-xl overflow-hidden focus-within:border-[#A01030] focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all">
                <div className="px-3 py-3.5 bg-gray-100 text-gray-500 text-sm font-bold border-r border-gray-200 flex items-center">+234</div>
                <input type="text" placeholder="800 000 0000" value={phone} onChange={e => setPhone(e.target.value)}
                  className="flex-1 px-3 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400" />
              </div>
            )}
            {isSelf && (
              <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-xl border border-gray-100">
                <Smartphone size={16} className="text-[#A01030]" />
                <span className="text-sm font-bold text-gray-700">{user?.phone || '080 000 00000'}</span>
                <span className="ml-auto text-[10px] text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded-full">Verified</span>
              </div>
            )}
          </div>

          {/* Amount */}
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
            <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-4 focus-within:border-[#A01030] focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all">
              <span className="text-gray-500 font-bold text-sm">₦</span>
              <input type="number" placeholder="Or enter custom amount" value={amount} onChange={e => setAmount(e.target.value)}
                className="flex-1 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400" />
            </div>
          </div>

          <button type="submit" disabled={isLoading || !amount}
            className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed">
            {isLoading ? 'Processing...' : `Buy ₦${amount ? Number(amount).toLocaleString() : '0'} Airtime`}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AirtimeScreen;