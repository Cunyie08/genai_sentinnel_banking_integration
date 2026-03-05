import { useState, useEffect } from 'react';
import { MdFlashOn, MdSignalCellularAlt, MdElectricBolt, MdCheckCircle, MdErrorOutline } from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const TABS = [
  { id: 'airtime', label: 'Airtime', icon: MdFlashOn },
  { id: 'data', label: 'Data', icon: MdSignalCellularAlt },
  { id: 'bills', label: 'Bills', icon: MdElectricBolt },
];

const Services = () => {
  const [tab, setTab] = useState('airtime');
  const [providers, setProviders] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [billCategories, setBillCategories] = useState([]);
  const [form, setForm] = useState({ account_id: '', provider: '', phone_number: '', amount: '', data_plan: '', category: '', bill_account_number: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState({ msg: '', type: '' });

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast({ msg: '', type: '' }), 3500);
  };

  // Load providers when tab changes
  useEffect(() => {
    const load = async () => {
      try {
        const [provRes, userRes] = await Promise.all([
          tab === 'bills'
            ? axiosInstance.get('/services/bills/providers')
            : axiosInstance.get(`/services/${tab}/providers`),
          axiosInstance.get('/users/me'),
        ]);
        setProviders(provRes.data || []);
        setAccounts(userRes.data?.account_details || []);
        if (tab === 'bills') {
          const catRes = await axiosInstance.get('/services/bills/categories');
          setBillCategories(catRes.data || []);
        }
      } catch { /* ignore */ }
    };
    load();
    setForm({ account_id: '', provider: '', phone_number: '', amount: '', data_plan: '', category: '', bill_account_number: '' });
  }, [tab]);

  const handleChange = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const handleSubmit = async e => {
    e.preventDefault();
    setToast({ msg: '', type: '' });
    if (parseFloat(form.amount) <= 0 || isNaN(+form.amount)) { showToast('Enter a valid amount.', 'error'); return; }
    setIsLoading(true);
    try {
      const payload = { account_id: form.account_id, provider: form.provider, amount: parseFloat(form.amount) };
      if (tab === 'airtime') { payload.phone_number = form.phone_number; await axiosInstance.post('/services/airtime/purchase', payload); }
      else if (tab === 'data') { payload.phone_number = form.phone_number; payload.data_plan = form.data_plan; await axiosInstance.post('/services/data/purchase', payload); }
      else { payload.category = form.category; payload.bill_account_number = form.bill_account_number; await axiosInstance.post('/services/bills/pay', payload); }
      showToast('Transaction successful!');
      setForm(p => ({ ...p, phone_number: '', amount: '', data_plan: '', bill_account_number: '' }));
    } catch (err) {
      showToast(err.response?.data?.detail || 'Transaction failed.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const inputClass = "w-full px-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none transition-all";

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-slate-900">Quick Services</h1>
        <p className="text-slate-500 text-sm mt-1">Buy airtime, data bundles, and pay bills instantly.</p>
      </div>

      {toast.msg && (
        <div className={`flex items-center gap-3 rounded-xl px-4 py-3 mb-5 text-sm font-semibold ${
          toast.type === 'error' ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {toast.type === 'error' ? <MdErrorOutline size={20} /> : <MdCheckCircle size={20} />}
          {toast.msg}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
              tab === id ? 'text-white shadow-md' : 'bg-white text-slate-600 border border-slate-200'
            }`}
            style={tab === id ? { backgroundColor: '#0000ff' } : {}}>
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      <div className="max-w-lg">
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Account */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Debit Account</label>
              <select name="account_id" value={form.account_id} onChange={handleChange} required className={`${inputClass} appearance-none`}
                onFocus={e => e.target.style.borderColor = '#0000ff'} onBlur={e => e.target.style.borderColor = '#e2e8f0'}>
                <option value="">Select account</option>
                {accounts.map(a => <option key={a.account_id} value={a.account_id}>{a.account_number || a.account_id}</option>)}
              </select>
            </div>

            {/* Provider */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Provider / Network</label>
              <div className="flex flex-wrap gap-2">
                {providers.map(p => (
                  <button key={p.code} type="button" onClick={() => setForm(f => ({ ...f, provider: p.code }))}
                    className={`px-3.5 py-2 rounded-xl text-sm font-bold border-2 transition-all ${
                      form.provider === p.code ? 'text-white border-transparent' : 'bg-white text-slate-600 border-slate-200'
                    }`}
                    style={form.provider === p.code ? { backgroundColor: '#0000ff', borderColor: '#0000ff' } : {}}>
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Phone (airtime/data) */}
            {(tab === 'airtime' || tab === 'data') && (
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Phone Number</label>
                <input name="phone_number" type="tel" required value={form.phone_number} onChange={handleChange}
                  placeholder="e.g. 08012345678" className={`${inputClass} px-4`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'} onBlur={e => e.target.style.borderColor = '#e2e8f0'} />
              </div>
            )}

            {/* Data plan */}
            {tab === 'data' && (
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Data Plan</label>
                <input name="data_plan" type="text" required value={form.data_plan} onChange={handleChange}
                  placeholder="e.g. 2GB, 5GB" className={`${inputClass} px-4`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'} onBlur={e => e.target.style.borderColor = '#e2e8f0'} />
              </div>
            )}

            {/* Bills — category + account number */}
            {tab === 'bills' && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Category</label>
                  <select name="category" value={form.category} onChange={handleChange} required className={`${inputClass} appearance-none`}
                    onFocus={e => e.target.style.borderColor = '#0000ff'} onBlur={e => e.target.style.borderColor = '#e2e8f0'}>
                    <option value="">Select category</option>
                    {billCategories.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Bill Account Number / Meter No.</label>
                  <input name="bill_account_number" type="text" required value={form.bill_account_number} onChange={handleChange}
                    placeholder="e.g. 01234567890" className={`${inputClass} px-4`}
                    onFocus={e => e.target.style.borderColor = '#0000ff'} onBlur={e => e.target.style.borderColor = '#e2e8f0'} />
                </div>
              </>
            )}

            {/* Amount */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Amount (₦)</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm">₦</span>
                <input name="amount" type="number" min="1" step="0.01" required value={form.amount} onChange={handleChange}
                  placeholder="0.00" className={`${inputClass} pl-8`}
                  onFocus={e => e.target.style.borderColor = '#0000ff'} onBlur={e => e.target.style.borderColor = '#e2e8f0'} />
              </div>
            </div>

            <button type="submit" disabled={isLoading}
              className="w-full py-4 rounded-xl text-white font-bold text-sm transition-all active:scale-[0.98] disabled:opacity-60"
              style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.2)' }}
              onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
              onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
            >
              {isLoading ? 'Processing...' : `Pay ${tab === 'airtime' ? 'Airtime' : tab === 'data' ? 'Data' : 'Bill'}`}
            </button>
          </form>
        </div>
      </div>
    </Layout>
  );
};

export default Services;
