import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  MdSwapHoriz, MdFlashOn, MdCreditCard, MdHistory,
  MdTrendingUp, MdTrendingDown, MdArrowUpward, MdArrowDownward,
  MdAccountBalance, MdPerson
} from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axiosInstance.get('/users/me');
        setUser(res.data);
        // Try to load recent transactions (non‑blocking)
        try {
          const txRes = await axiosInstance.get('/transactions?limit=5');
          setTransactions(txRes.data?.transactions || txRes.data || []);
        } catch { /* transactions might 404 — ignore */ }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load dashboard.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const account = user?.account_details?.[0] || null;
  const customer = user?.customer_details || null;
  const firstName = customer?.first_name || user?.email?.split('@')[0] || 'User';
  const balance = account ? parseFloat(account.balance || account.current_balance || 0) : 0;

  const QUICK_ACTIONS = [
    { label: 'Transfer', icon: MdSwapHoriz, to: '/transfer', color: '#0000ff' },
    { label: 'Airtime', icon: MdFlashOn, to: '/services', color: '#7c3aed' },
    { label: 'Cards', icon: MdCreditCard, to: '/cards', color: '#0891b2' },
    { label: 'History', icon: MdHistory, to: '/history', color: '#059669' },
  ];

  if (isLoading) return (
    <Layout>
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 rounded-full border-4 border-slate-200 animate-spin" style={{ borderTopColor: '#0000ff' }} />
      </div>
    </Layout>
  );

  return (
    <Layout>
      {/* Greeting */}
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-slate-900">Good morning, {firstName} 👋</h1>
        <p className="text-slate-500 text-sm mt-1">Here's your financial overview for today.</p>
      </div>

      {error && <div className="bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-3 mb-5 text-sm">{error}</div>}

      {/* Balance Card */}
      <div
        className="rounded-2xl p-6 mb-6 relative overflow-hidden text-white"
        style={{ background: 'linear-gradient(135deg, #0000ff 0%, #1414ff 50%, #4a86e8 100%)' }}
      >
        <div className="absolute -top-8 -right-8 w-40 h-40 rounded-full opacity-20" style={{ backgroundColor: 'white' }} />
        <div className="absolute -bottom-10 -left-6 w-32 h-32 rounded-full opacity-10" style={{ backgroundColor: 'white' }} />
        <div className="relative z-10">
          <p className="text-sm font-medium opacity-80 mb-1">Total Balance</p>
          <p className="text-4xl font-extrabold mb-1">
            ₦{balance.toLocaleString('en-NG', { minimumFractionDigits: 2 })}
          </p>
          {account && (
            <p className="text-sm opacity-70 font-medium">
              <MdAccountBalance className="inline mr-1" size={14} />
              {account.account_number || account.account_id || '—'}
            </p>
          )}
        </div>
        <div className="relative z-10 flex gap-6 mt-5">
          <div className="flex items-center gap-2">
            <div className="bg-white/20 p-1.5 rounded-lg"><MdTrendingUp size={16} /></div>
            <div>
              <p className="text-xs opacity-70">Income</p>
              <p className="text-sm font-bold">₦0.00</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="bg-white/20 p-1.5 rounded-lg"><MdTrendingDown size={16} /></div>
            <div>
              <p className="text-xs opacity-70">Expenses</p>
              <p className="text-sm font-bold">₦0.00</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        {QUICK_ACTIONS.map(({ label, icon: Icon, to, color }) => (
          <Link key={label} to={to}
            className="flex flex-col items-center gap-2 bg-white rounded-2xl py-4 px-2 shadow-sm hover:shadow-md transition-all active:scale-95">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ backgroundColor: color + '15' }}>
              <Icon size={22} style={{ color }} />
            </div>
            <span className="text-xs font-bold text-slate-700">{label}</span>
          </Link>
        ))}
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-2xl shadow-sm p-5">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-bold text-slate-900">Recent Transactions</h2>
          <Link to="/history" className="text-xs font-bold" style={{ color: '#0000ff' }}>See All</Link>
        </div>

        {transactions.length === 0 ? (
          <div className="text-center py-10">
            <MdHistory size={36} className="text-slate-200 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No transactions yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {transactions.slice(0, 5).map((tx, i) => {
              const isDebit = tx.transaction_type === 'debit' || tx.amount < 0;
              return (
                <div key={tx.transaction_id || i} className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isDebit ? 'bg-red-50' : 'bg-green-50'}`}>
                    {isDebit ? <MdArrowUpward size={18} className="text-red-500" /> : <MdArrowDownward size={18} className="text-green-500" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">{tx.narration || tx.merchant_name || 'Transaction'}</p>
                    <p className="text-xs text-slate-400">{tx.created_at ? new Date(tx.created_at).toLocaleDateString() : '—'}</p>
                  </div>
                  <p className={`text-sm font-bold ${isDebit ? 'text-red-500' : 'text-green-600'}`}>
                    {isDebit ? '-' : '+'}₦{Math.abs(tx.amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Profile quick info */}
      {user && (
        <div className="mt-4 bg-white rounded-2xl shadow-sm p-4 flex items-center gap-4">
          <div className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg" style={{ backgroundColor: '#0000ff' }}>
            {firstName[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-slate-900 text-sm">{[customer?.first_name, customer?.last_name].filter(Boolean).join(' ') || user.email}</p>
            <p className="text-xs text-slate-400">{user.email}</p>
          </div>
          <Link to="/profile" className="text-slate-400 hover:text-blue-600 transition-colors"><MdPerson size={22} /></Link>
        </div>
      )}
    </Layout>
  );
};

export default Dashboard;
