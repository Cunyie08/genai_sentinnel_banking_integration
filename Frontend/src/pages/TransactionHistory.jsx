import { useState, useEffect } from 'react';
import {
  MdArrowUpward, MdArrowDownward, MdFilterList,
  MdSearch, MdReceipt
} from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const FILTERS = ['All', 'Debit', 'Credit'];

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axiosInstance.get('/transactions');
        setTransactions(res.data?.transactions || res.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load transactions.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const filtered = transactions.filter(tx => {
    const matchType = filter === 'All'
      || (filter === 'Debit' && (tx.transaction_type === 'debit' || tx.amount < 0))
      || (filter === 'Credit' && (tx.transaction_type === 'credit' || tx.amount >= 0));
    const matchSearch = !search
      || (tx.narration || tx.merchant_name || '').toLowerCase().includes(search.toLowerCase());
    return matchType && matchSearch;
  });

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-slate-900">Transaction History</h1>
        <p className="text-slate-500 text-sm mt-1">A full record of all your account activity.</p>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <div className="relative flex-1">
          <MdSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search transactions…"
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-white text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
            onFocus={e => e.target.style.borderColor = '#0000ff'}
            onBlur={e => e.target.style.borderColor = '#e2e8f0'}
          />
        </div>
        <div className="flex gap-2">
          {FILTERS.map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
                filter === f ? 'text-white shadow-md' : 'bg-white text-slate-600 border border-slate-200'
              }`}
              style={filter === f ? { backgroundColor: '#0000ff' } : {}}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-3 mb-4 text-sm">{error}</div>}

      {/* List */}
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 rounded-full border-4 border-slate-200 animate-spin" style={{ borderTopColor: '#0000ff' }} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <MdReceipt size={40} className="text-slate-200 mx-auto mb-3" />
            <p className="text-slate-400 text-sm font-medium">No transactions found</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-50">
            {filtered.map((tx, i) => {
              const isDebit = tx.transaction_type === 'debit' || tx.amount < 0;
              const amt = Math.abs(tx.amount);
              return (
                <div key={tx.transaction_id || i} className="flex items-center gap-4 px-5 py-4 hover:bg-slate-50 transition-colors">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${isDebit ? 'bg-red-50' : 'bg-green-50'}`}>
                    {isDebit ? <MdArrowUpward size={18} className="text-red-500" /> : <MdArrowDownward size={18} className="text-green-500" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">{tx.narration || tx.merchant_name || 'Transaction'}</p>
                    <p className="text-xs text-slate-400">{tx.created_at ? new Date(tx.created_at).toLocaleString() : '—'} · {tx.channel || 'online'}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className={`text-sm font-bold ${isDebit ? 'text-red-500' : 'text-green-600'}`}>
                      {isDebit ? '-' : '+'}₦{amt.toLocaleString('en-NG', { minimumFractionDigits: 2 })}
                    </p>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      tx.status === 'success' || tx.status === 'completed'
                        ? 'bg-green-50 text-green-600'
                        : tx.status === 'pending'
                        ? 'bg-yellow-50 text-yellow-600'
                        : 'bg-red-50 text-red-500'
                    }`}>
                      {tx.status || 'success'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default TransactionHistory;
