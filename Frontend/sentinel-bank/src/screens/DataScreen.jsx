// src/screens/DataScreen.jsx
import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setRoute } from '../features/uiSlice';
import { buyData, resetService } from '../features/servicesSlice';
import { ChevronLeft, Wifi, CheckCircle, AlertCircle } from 'lucide-react';

const NETWORKS = [
  { id: 'mtn',    name: 'MTN',     color: 'bg-yellow-400', text: 'text-yellow-900' },
  { id: 'airtel', name: 'Airtel',  color: 'bg-red-500',    text: 'text-white'      },
  { id: 'glo',    name: 'Glo',     color: 'bg-green-500',  text: 'text-white'      },
  { id: '9mobile',name: '9Mobile', color: 'bg-emerald-600',text: 'text-white'      },
];

const DATA_PLANS = {
  mtn: [
    { id: 'mtn_100mb', label: '100MB',  price: 100,  validity: '1 Day'   },
    { id: 'mtn_1gb',   label: '1GB',    price: 300,  validity: '7 Days'  },
    { id: 'mtn_2gb',   label: '2GB',    price: 500,  validity: '30 Days' },
    { id: 'mtn_5gb',   label: '5GB',    price: 1500, validity: '30 Days' },
    { id: 'mtn_10gb',  label: '10GB',   price: 2500, validity: '30 Days' },
    { id: 'mtn_20gb',  label: '20GB',   price: 3500, validity: '30 Days' },
  ],
  airtel: [
    { id: 'air_500mb', label: '500MB',  price: 200,  validity: '7 Days'  },
    { id: 'air_1gb',   label: '1GB',    price: 350,  validity: '30 Days' },
    { id: 'air_3gb',   label: '3GB',    price: 1000, validity: '30 Days' },
    { id: 'air_6gb',   label: '6GB',    price: 1500, validity: '30 Days' },
    { id: 'air_15gb',  label: '15GB',   price: 3000, validity: '30 Days' },
  ],
  glo: [
    { id: 'glo_1gb',   label: '1.35GB', price: 300,  validity: '14 Days' },
    { id: 'glo_3gb',   label: '3.2GB',  price: 500,  validity: '30 Days' },
    { id: 'glo_7gb',   label: '7.7GB',  price: 1000, validity: '30 Days' },
    { id: 'glo_15gb',  label: '15GB',   price: 2000, validity: '30 Days' },
  ],
  '9mobile': [
    { id: '9m_1gb',    label: '1GB',    price: 200,  validity: '30 Days' },
    { id: '9m_2gb',    label: '2.5GB',  price: 500,  validity: '30 Days' },
    { id: '9m_5gb',    label: '5GB',    price: 1000, validity: '30 Days' },
  ],
};

const DataScreen = () => {
  const dispatch = useDispatch();
  const { isLoading, status, lastResult, error } = useSelector(s => s.services);
  const user    = useSelector(s => s.auth.user);
  const [network, setNetwork] = useState('mtn');
  const [plan,    setPlan]    = useState(null);
  const [phone,   setPhone]   = useState('');
  const [isSelf,  setIsSelf]  = useState(true);

  const plans = DATA_PLANS[network] || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!plan) return;
    dispatch(buyData({ network, phone: isSelf ? user?.phone : phone, plan }));
  };

  const handleReset = () => { dispatch(resetService()); setPlan(null); setPhone(''); };

  if (status === 'success' && lastResult?.service === 'data') {
    return (
      <div className="min-h-full w-full bg-[#F8F9FB] flex flex-col items-center justify-center p-6 font-sans">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 w-full max-w-sm text-center">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-500" />
          </div>
          <h2 className="text-xl font-black text-gray-900 mb-1">Data Activated!</h2>
          <p className="text-gray-500 text-sm mb-4">{lastResult.plan?.label} {lastResult.network?.toUpperCase()} data bundle activated.</p>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-6">Ref: {lastResult.ref}</p>
          <button onClick={handleReset} className="w-full bg-[#A01030] text-white py-3.5 rounded-2xl font-bold text-sm hover:bg-[#850d28] transition-colors">
            Buy More Data
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
      <header className="sticky top-0 z-20 bg-[#F8F9FB]/95 backdrop-blur-sm border-b border-gray-100 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button onClick={() => dispatch(setRoute('home'))}
          className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors">
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none">Services</p>
          <h1 className="text-lg font-extrabold text-gray-900">Buy Data</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 max-w-2xl xl:max-w-none">
        {error && (
          <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Network */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Select Network</p>
            <div className="grid grid-cols-4 gap-3">
              {NETWORKS.map(n => (
                <button key={n.id} type="button" onClick={() => { setNetwork(n.id); setPlan(null); }}
                  className={`flex flex-col items-center gap-2 p-3 rounded-2xl border-2 transition-all ${network === n.id ? 'border-[#A01030] bg-rose-50' : 'border-gray-100 bg-gray-50 hover:bg-gray-100'}`}>
                  <div className={`w-10 h-10 ${n.color} rounded-xl flex items-center justify-center`}>
                    <span className={`text-[10px] font-black ${n.text}`}>{n.name.slice(0,3)}</span>
                  </div>
                  <span className={`text-[10px] font-bold ${network === n.id ? 'text-[#A01030]' : 'text-gray-500'}`}>{n.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Phone */}
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
              <div className="flex bg-gray-50 border border-gray-200 rounded-xl overflow-hidden focus-within:border-[#A01030] transition-all">
                <div className="px-3 py-3.5 bg-gray-100 text-gray-500 text-sm font-bold border-r border-gray-200">+234</div>
                <input type="text" placeholder="800 000 0000" value={phone} onChange={e => setPhone(e.target.value)}
                  className="flex-1 px-3 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400" />
              </div>
            )}
            {isSelf && (
              <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-xl border border-gray-100">
                <Wifi size={16} className="text-[#A01030]" />
                <span className="text-sm font-bold text-gray-700">{user?.phone || '080 000 00000'}</span>
                <span className="ml-auto text-[10px] text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded-full">Verified</span>
              </div>
            )}
          </div>

          {/* Data Plans */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Select Plan</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
              {plans.map(p => (
                <button key={p.id} type="button" onClick={() => setPlan(p)}
                  className={`flex flex-col p-4 rounded-2xl border-2 text-left transition-all ${plan?.id === p.id ? 'border-[#A01030] bg-rose-50' : 'border-gray-100 bg-gray-50 hover:bg-gray-100'}`}>
                  <span className={`text-base font-black mb-0.5 ${plan?.id === p.id ? 'text-[#A01030]' : 'text-gray-900'}`}>{p.label}</span>
                  <span className="text-xs text-gray-500 mb-2">{p.validity}</span>
                  <span className={`text-sm font-extrabold ${plan?.id === p.id ? 'text-[#A01030]' : 'text-gray-700'}`}>₦{p.price.toLocaleString()}</span>
                </button>
              ))}
            </div>
          </div>

          <button type="submit" disabled={isLoading || !plan}
            className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed">
            {isLoading ? 'Processing...' : plan ? `Buy ${plan.label} for ₦${plan.price.toLocaleString()}` : 'Select a Plan'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default DataScreen;