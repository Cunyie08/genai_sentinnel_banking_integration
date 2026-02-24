// src/screens/BillsScreen.jsx
import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setRoute } from '../features/uiSlice';
import { payBill, resetService } from '../features/servicesSlice';
import { ChevronLeft, Zap, Tv, Wifi, CheckCircle, AlertCircle } from 'lucide-react';

const BILL_TYPES = [
  { id: 'electricity', label: 'Electricity', icon: Zap,  providers: ['EKEDC','IKEDC','AEDC','PHED','KEDCO','IBEDC','BEDC','EEDC'] },
  { id: 'tv',          label: 'Cable TV',    icon: Tv,   providers: ['DSTV', 'GOtv', 'StarTimes'] },
  { id: 'internet',    label: 'Internet',    icon: Wifi, providers: ['Spectranet', 'Smile', 'iPNX', 'Swift'] },
];

const QUICK_AMOUNTS = [1000, 2000, 5000, 10000, 20000, 50000];

const BillsScreen = () => {
  const dispatch = useDispatch();
  const { isLoading, status, lastResult, error } = useSelector(s => s.services);
  const [billType,     setBillType]     = useState('electricity');
  const [provider,     setProvider]     = useState('');
  const [meterNumber,  setMeterNumber]  = useState('');
  const [amount,       setAmount]       = useState('');
  const [customerName, setCustomerName] = useState('');
  const [verified,     setVerified]     = useState(false);

  const currentType = BILL_TYPES.find(b => b.id === billType);

  const handleVerify = () => {
    if (meterNumber.length >= 5) {
      setCustomerName('Reuben Tunde Adeyemi');
      setVerified(true);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(payBill({ billType, meterNumber, amount, provider }));
  };

  const handleReset = () => {
    dispatch(resetService());
    setAmount(''); setMeterNumber(''); setVerified(false); setCustomerName('');
  };

  if (status === 'success' && lastResult?.service === 'bills') {
    return (
      <div className="min-h-full w-full bg-[#F8F9FB] flex flex-col items-center justify-center p-6 font-sans">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 w-full max-w-sm text-center">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-500" />
          </div>
          <h2 className="text-xl font-black text-gray-900 mb-1">Bill Paid!</h2>
          <p className="text-gray-500 text-sm mb-4">₦{Number(lastResult.amount).toLocaleString()} {lastResult.billType} bill paid successfully.</p>
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-6">Ref: {lastResult.ref}</p>
          <button onClick={handleReset} className="w-full bg-[#A01030] text-white py-3.5 rounded-2xl font-bold text-sm hover:bg-[#850d28] transition-colors">
            Pay Another Bill
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
          <h1 className="text-lg font-extrabold text-gray-900">Pay Bills</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 max-w-2xl xl:max-w-none">
        {error && (
          <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Bill Type Tabs */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Bill Category</p>
            <div className="grid grid-cols-3 gap-3">
              {BILL_TYPES.map(b => (
                <button key={b.id} type="button" onClick={() => { setBillType(b.id); setProvider(''); }}
                  className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${billType === b.id ? 'border-[#A01030] bg-rose-50' : 'border-gray-100 bg-gray-50 hover:bg-gray-100'}`}>
                  <b.icon size={22} className={billType === b.id ? 'text-[#A01030]' : 'text-gray-400'} />
                  <span className={`text-[10px] font-bold ${billType === b.id ? 'text-[#A01030]' : 'text-gray-500'}`}>{b.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Provider */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Provider</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {currentType?.providers.map(p => (
                <button key={p} type="button" onClick={() => setProvider(p)}
                  className={`py-2.5 px-3 rounded-xl text-xs font-bold border-2 transition-all text-center ${provider === p ? 'bg-[#A01030] text-white border-[#A01030]' : 'bg-gray-50 text-gray-600 border-gray-100 hover:bg-gray-100'}`}>
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Meter / Account Number */}
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">
              {billType === 'electricity' ? 'Meter Number' : billType === 'tv' ? 'Smartcard / IUC Number' : 'Account Number'}
            </p>
            <div className="flex gap-2">
              <input type="text" placeholder="Enter number"
                value={meterNumber} onChange={e => { setMeterNumber(e.target.value); setVerified(false); setCustomerName(''); }}
                className="flex-1 px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:border-[#A01030] transition-all" />
              <button type="button" onClick={handleVerify} disabled={meterNumber.length < 5}
                className="px-4 py-3.5 bg-[#A01030] text-white rounded-xl text-xs font-bold disabled:opacity-40 hover:bg-[#850d28] transition-colors">
                Verify
              </button>
            </div>
            {verified && (
              <div className="mt-3 flex items-center gap-2 p-3 bg-green-50 rounded-xl border border-green-100">
                <CheckCircle size={15} className="text-green-500" />
                <span className="text-xs font-bold text-green-700">{customerName}</span>
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
            <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-4 focus-within:border-[#A01030] transition-all">
              <span className="text-gray-500 font-bold text-sm">₦</span>
              <input type="number" placeholder="Or enter custom amount" value={amount} onChange={e => setAmount(e.target.value)}
                className="flex-1 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400" />
            </div>
          </div>

          <button type="submit" disabled={isLoading || !amount || !meterNumber || !provider}
            className="w-full bg-[#A01030] text-white py-4 rounded-2xl font-bold text-sm shadow-lg shadow-red-900/20 hover:bg-[#850d28] transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed">
            {isLoading ? 'Processing...' : `Pay ₦${amount ? Number(amount).toLocaleString() : '0'}`}
          </button>
        </form>
      </div>
    </div>
  );
};

export default BillsScreen;