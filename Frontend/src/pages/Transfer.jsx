import { useState, useEffect } from 'react';
import { MdSwapHoriz, MdCheckCircle, MdErrorOutline, MdAccountBalance } from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const Transfer = () => {
  const [accounts, setAccounts] = useState([]);
  const [form, setForm] = useState({ from_account_number: '', to_account_number: '', amount: '', narration: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    axiosInstance.get('/users/me')
      .then(res => setAccounts(res.data?.account_details || []))
      .catch(() => {});
  }, []);

  const handleChange = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const handleSubmit = async e => {
    e.preventDefault();
    setError(''); 
    setSuccess('');
    if (parseFloat(form.amount) <= 0 || isNaN(+form.amount)) {
      setError('Enter a valid amount greater than ₦0.');
      return;
    }
    setIsLoading(true);
    try {
      await axiosInstance.post('/services/internal-transfer', {
        from_account_number: form.from_account_number,
        to_account_number: form.to_account_number,
        amount: parseFloat(form.amount),
        narration: form.narration || 'Transfer',
      });
      setSuccess(`₦${parseFloat(form.amount).toLocaleString('en-NG', { minimumFractionDigits: 2 })} transferred successfully!`);
      setForm(p => ({ ...p, to_account_number: '', amount: '', narration: '' }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Transfer failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const inputClass = "w-full px-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all";

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-slate-900">Transfer Funds</h1>
        <p className="text-slate-500 text-sm mt-1">Send money to any Sentinel Bank account instantly.</p>
      </div>

      <div className="max-w-lg">
        {success && (
          <div className="flex items-center gap-3 bg-green-50 text-green-700 border border-green-200 rounded-xl px-4 py-4 mb-5">
            <MdCheckCircle size={22} className="shrink-0" />
            <p className="text-sm font-semibold">{success}</p>
          </div>
        )}
        {error && (
          <div className="flex items-center gap-3 bg-red-50 text-red-600 border border-red-200 rounded-xl px-4 py-4 mb-5">
            <MdErrorOutline size={22} className="shrink-0" />
            <p className="text-sm font-semibold">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm p-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* From account */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">From Account</label>
              <div className="relative">
                <MdAccountBalance className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <select name="from_account_number" value={form.from_account_number}
                  onChange={handleChange} required
                  className={`${inputClass} pl-11 appearance-none`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                >
                  <option value="">Select source account</option>
                  {accounts.map(a => (
                    <option key={a.account_number || a.account_id} value={a.account_number || a.account_id}>
                      {a.account_number || a.account_id} — ₦{parseFloat(a.balance || a.current_balance || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* To account */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Recipient Account Number</label>
              <input name="to_account_number" type="text" required
                value={form.to_account_number} onChange={handleChange}
                placeholder="Enter Sentinel account number"
                className={`${inputClass} px-4`}
                onFocus={e => e.target.style.borderColor = '#0000ff'}
                onBlur={e => e.target.style.borderColor = '#e2e8f0'}
              />
            </div>

            {/* Amount */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Amount (₦)</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm">₦</span>
                <input name="amount" type="number" min="1" step="0.01" required
                  value={form.amount} onChange={handleChange}
                  placeholder="0.00"
                  className={`${inputClass} pl-8`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'}
                  onBlur={e => e.target.style.borderColor = '#e2e8f0'}
                />
              </div>
            </div>

            {/* Narration */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Narration <span className="text-slate-400 font-normal">(Optional)</span></label>
              <input name="narration" type="text"
                value={form.narration} onChange={handleChange}
                placeholder="e.g. Rent payment"
                className={`${inputClass} px-4`}
                onFocus={e => e.target.style.borderColor = '#0000ff'}
                onBlur={e => e.target.style.borderColor = '#e2e8f0'}
              />
            </div>

            <button type="submit" disabled={isLoading}
              className="w-full py-4 rounded-xl text-white font-bold text-sm flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-60"
              style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.2)' }}
              onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
              onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
            >
              <MdSwapHoriz size={20} />
              {isLoading ? 'Processing...' : 'Transfer Now'}
            </button>
          </form>
        </div>
      </div>
    </Layout>
  );
};

export default Transfer;
