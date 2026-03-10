import { useNavigate } from 'react-router-dom';

import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { fetchTransactions } from '../features/transactionSlice';
import { ChevronLeft, Search, ArrowDownLeft, ArrowUpRight, Filter, Smartphone, Globe, Zap, Send, Landmark, Gamepad2, Wallet, FileText } from 'lucide-react';

const CATEGORY_ICON = {
  airtime:  Smartphone, data:     Globe, bills:    Zap,
  transfer: Send, salary:   Landmark, betting:  Gamepad2,
  fund:     Wallet, default:  FileText,
};

const FILTERS = ['All', 'Credit', 'Debit', 'Transfer', 'Bills', 'Airtime'];

const HistoryScreen = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const { list, isLoading } = useSelector(s => s.transactions);
  const [search,    setSearch]    = useState('');
  const [filter,    setFilter]    = useState('All');

  useEffect(() => { if (list.length === 0) dispatch(fetchTransactions()); }, []);

  const filtered = list.filter(tx => {
    const matchSearch = tx.name.toLowerCase().includes(search.toLowerCase()) || tx.ref?.toLowerCase().includes(search.toLowerCase());
    const matchFilter =
      filter === 'All'      ? true :
      filter === 'Credit'   ? tx.type === 'credit' :
      filter === 'Debit'    ? tx.type === 'debit' :
      filter === 'Transfer' ? tx.category === 'transfer' :
      filter === 'Bills'    ? tx.category === 'bills' :
      filter === 'Airtime'  ? tx.category === 'airtime' : true;
    return matchSearch && matchFilter;
  });

  const formatDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-NG', { day:'numeric', month:'short', hour:'2-digit', minute:'2-digit' });
  };

  return (
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans">
      <header className="sticky top-0 z-20 bg-[#F8F9FB]/95 backdrop-blur-sm border-b border-gray-100 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button onClick={() => navigate('/home')}
          className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors">
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-none">Account</p>
          <h1 className="text-lg font-extrabold text-gray-900">Transaction History</h1>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-5 space-y-4">

        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-2xl px-4 shadow-sm focus-within:border-[#A01030] focus-within:ring-2 focus-within:ring-[#A01030]/10 transition-all">
          <Search size={16} className="text-gray-400 shrink-0" />
          <input type="text" placeholder="Search transactions..." value={search} onChange={e => setSearch(e.target.value)}
            className="flex-1 py-3.5 bg-transparent outline-none text-sm font-medium text-gray-900 placeholder:text-gray-400" />
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {FILTERS.map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`shrink-0 px-4 py-2 rounded-xl text-xs font-bold border-2 transition-all ${filter === f ? 'bg-[#A01030] text-white border-[#A01030]' : 'bg-white text-gray-500 border-gray-100 hover:bg-gray-50'}`}>
              {f}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Total In',  value: list.filter(t => t.type === 'credit').reduce((a, t) => a + t.amount, 0), icon: ArrowDownLeft, color: 'text-emerald-600', bg: 'bg-emerald-50' },
            { label: 'Total Out', value: list.filter(t => t.type === 'debit').reduce((a, t) => a + t.amount, 0),  icon: ArrowUpRight,  color: 'text-rose-600',    bg: 'bg-rose-50'    },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex items-center gap-3">
              <div className={`w-9 h-9 ${s.bg} rounded-xl flex items-center justify-center shrink-0`}>
                <s.icon size={16} className={s.color} />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wide">{s.label}</p>
                <p className={`text-sm font-extrabold ${s.color} truncate`}>₦{s.value.toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-[#A01030] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center px-6">
              <span className="text-4xl mb-3">
                <Search size={40} className="text-gray-300 mx-auto" />
              </span>
              <p className="text-gray-700 font-bold">No transactions found</p>
              <p className="text-gray-400 text-xs mt-1">Try a different search or filter</p>
            </div>
          ) : (
            <div>
              {filtered.map((tx, i) => {
                const IconComp = CATEGORY_ICON[tx.category] || CATEGORY_ICON.default;
                return (
                  <div key={tx.id} className={`flex items-center gap-3 px-4 sm:px-5 py-4 ${i < filtered.length - 1 ? 'border-b border-gray-50' : ''} hover:bg-gray-50/50 transition-colors`}>
                    <span className="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center shrink-0">
                      <IconComp size={20} className="text-gray-600" />
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-gray-800 truncate">{tx.name}</p>
                      <p className="text-[10px] text-gray-400">{formatDate(tx.date)} · {tx.ref}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className={`text-sm font-extrabold ${tx.type === 'credit' ? 'text-emerald-600' : 'text-gray-800'}`}>
                        {tx.type === 'credit' ? '+' : '-'}₦{tx.amount.toLocaleString()}
                      </p>
                      <span className="text-[10px] text-green-500 font-bold capitalize">{tx.status}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default HistoryScreen;