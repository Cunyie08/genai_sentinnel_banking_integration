import { useNavigate } from 'react-router-dom';

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { payBill, resetService } from '../features/servicesSlice';
import { ChevronLeft, Zap, Tv, Wifi, CheckCircle, AlertCircle } from 'lucide-react';

const BILL_TYPES = [
  { id: 'electricity', label: 'Electricity', icon: Zap,  providers: ['EKEDC','IKEDC','AEDC','PHED','KEDCO','IBEDC','BEDC','EEDC'] },
  { id: 'tv',          label: 'Cable TV',    icon: Tv,   providers: ['DSTV', 'GOtv', 'StarTimes'] },
  { id: 'internet',    label: 'Internet',    icon: Wifi, providers: ['Spectranet', 'Smile', 'iPNX', 'Swift'] },
];

const QUICK_AMOUNTS = [1000, 2000, 5000, 10000, 20000, 50000];

const BillsScreen = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const { isLoading, status, lastResult, error } = useSelector(s => s.services);
  const [billType,     setBillType]     = useState('electricity');
  const [provider,     setProvider]     = useState('');
  const [meterNumber,  setMeterNumber]  = useState('');
  const [amount,       setAmount]       = useState('');
  const [customerName, setCustomerName] = useState('');
  const [verified,     setVerified]     = useState(false);

  const user = useSelector(s => s.auth.user);
  const currentType = BILL_TYPES.find(b => b.id === billType);

  const handleVerify = () => {
    if (meterNumber.length >= 5) {
      setCustomerName('Reuben Tunde Adeyemi');
      setVerified(true);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const accountId = user?.accounts?.[0]?.account_id;
    dispatch(payBill({ 
      billType, 
      meterNumber, 
      amount: Number(amount), 
      provider: provider,
      category: billType,
      account_id: accountId
    }));
  };

  const handleReset = () => {
    dispatch(resetService());
    setAmount(''); setMeterNumber(''); setVerified(false); setCustomerName('');
  };

  if (status === 'success' && lastResult?.service === 'bills') {
    return (
      <div className="min-h-full w-full bg-vault-light-bg dark:bg-vault-dark-bg flex flex-col items-center justify-center p-6 font-sans vault-transition">
        <div className="bg-white dark:bg-vault-dark-card rounded-3xl p-8 shadow-sm border border-gray-100 dark:border-white/5 w-full max-w-sm text-center">
          <div className="w-16 h-16 bg-green-50 dark:bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-500 dark:text-green-400" />
          </div>
          <h2 className="text-xl font-black text-gray-900 dark:text-white mb-1">Bill Paid!</h2>
          <p className="text-gray-500 dark:text-slate-400 text-sm mb-4">₦{Number(lastResult.amount).toLocaleString()} {lastResult.billType} bill paid successfully.</p>
          <p className="text-[10px] text-gray-400 dark:text-slate-500 font-bold uppercase tracking-widest mb-6">Ref: {lastResult.ref}</p>
          <button onClick={handleReset} className="w-full vault-gradient text-white py-3.5 rounded-2xl font-bold text-sm transition-colors vault-glow">
            Pay Another Bill
          </button>
          <button onClick={() => navigate('/home')} className="w-full mt-3 text-gray-500 dark:text-slate-400 text-sm font-bold hover:text-gray-700 dark:hover:text-white py-2">
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
          <p className="text-[10px] text-gray-400 dark:text-slate-500 font-bold uppercase tracking-widest leading-none">Services</p>
          <h1 className="text-lg font-extrabold text-gray-900 dark:text-white">Pay Bills</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 pb-28 max-w-2xl xl:max-w-none">
        {error && (
          <div className="mb-5 p-3 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-red-600 dark:text-red-400 rounded-xl text-xs font-bold flex items-center gap-2">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5">
            <p className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3">Bill Category</p>
            <div className="grid grid-cols-3 gap-3">
              {BILL_TYPES.map(b => (
                <button key={b.id} type="button" onClick={() => { setBillType(b.id); setProvider(''); }}
                  className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${billType === b.id ? 'border-vault-cyan bg-cyan-50 dark:bg-vault-cyan/10' : 'border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 hover:bg-gray-100 dark:hover:bg-white/10'}`}>
                  <b.icon size={22} className={billType === b.id ? 'text-vault-cyan' : 'text-gray-400 dark:text-slate-500'} />
                  <span className={`text-[10px] font-bold ${billType === b.id ? 'text-vault-cyan' : 'text-gray-500 dark:text-slate-400'}`}>{b.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5">
            <p className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3">Provider</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {currentType?.providers.map(p => (
                <button key={p} type="button" onClick={() => setProvider(p)}
                  className={`py-2.5 px-3 rounded-xl text-xs font-bold border-2 transition-all text-center ${provider === p ? 'vault-gradient text-white border-transparent' : 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-slate-300 border-gray-100 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/10'}`}>
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5">
            <p className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3">
              {billType === 'electricity' ? 'Meter Number' : billType === 'tv' ? 'Smartcard / IUC Number' : 'Account Number'}
            </p>
            <div className="flex gap-2">
              <input type="text" placeholder="Enter number"
                value={meterNumber} onChange={e => { setMeterNumber(e.target.value); setVerified(false); setCustomerName(''); }}
                className="flex-1 px-4 py-3.5 bg-gray-50 dark:bg-vault-dark-input border border-gray-200 dark:border-white/5 rounded-xl outline-none text-sm font-medium text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:border-vault-cyan transition-all" />
              <button type="button" onClick={handleVerify} disabled={meterNumber.length < 5}
                className="px-4 py-3.5 vault-gradient text-white rounded-xl text-xs font-bold disabled:opacity-40 transition-colors">
                Verify
              </button>
            </div>
            {verified && (
              <div className="mt-3 flex items-center gap-2 p-3 bg-green-50 dark:bg-green-500/10 rounded-xl border border-green-100 dark:border-green-500/20">
                <CheckCircle size={15} className="text-green-500 dark:text-green-400" />
                <span className="text-xs font-bold text-green-700 dark:text-green-400">{customerName}</span>
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-vault-dark-card rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-white/5">
            <p className="text-xs font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-3">Amount</p>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-4">
              {QUICK_AMOUNTS.map(a => (
                <button key={a} type="button" onClick={() => setAmount(String(a))}
                  className={`py-2.5 rounded-xl text-xs font-bold border-2 transition-all ${amount === String(a) ? 'vault-gradient text-white border-transparent' : 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-slate-300 border-gray-100 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/10'}`}>
                  ₦{a.toLocaleString()}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 bg-gray-50 dark:bg-vault-dark-input border border-gray-200 dark:border-white/5 rounded-xl px-4 focus-within:border-vault-cyan transition-all">
              <span className="text-gray-500 dark:text-slate-400 font-bold text-sm">₦</span>
              <input type="number" placeholder="Or enter custom amount" value={amount} onChange={e => setAmount(e.target.value)}
                className="flex-1 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500" />
            </div>
          </div>

          <button type="submit" disabled={isLoading || !amount || !meterNumber || !provider}
            className="w-full vault-gradient text-white py-4 rounded-2xl font-bold text-sm shadow-lg vault-glow transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed">
            {isLoading ? 'Processing...' : `Pay ₦${amount ? Number(amount).toLocaleString() : '0'}`}
          </button>
        </form>
      </div>
    </div>
  );
};

export default BillsScreen;