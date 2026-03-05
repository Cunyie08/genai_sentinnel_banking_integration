import { useState, useEffect } from 'react';
import { MdSettings, MdNotifications, MdLanguage, MdPalette, MdCheckCircle, MdErrorOutline } from 'react-icons/md';
import Layout from '../components/Layout';
import axiosInstance from '../api/axiosInstance';

const Settings = () => {
  const [prefs, setPrefs] = useState({
    theme: 'light',
    language: 'en',
    notify_transactions: true,
    notify_promotions: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState({ msg: '', type: '' });

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast({ msg: '', type: '' }), 3000);
  };

  useEffect(() => {
    axiosInstance.get('/users/settings').then(res => {
      if (res.data) setPrefs(prev => ({ ...prev, ...res.data }));
    }).catch(() => {});
  }, []);

  const save = async () => {
    setIsLoading(true);
    try {
      await axiosInstance.patch('/users/update-preferences', prefs);
      showToast('Settings saved successfully!');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Save failed.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const Toggle = ({ value, onChange, label, description, icon: Icon }) => (
    <div className="flex items-center justify-between py-4 border-b border-slate-50 last:border-0">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,255,0.06)' }}>
          <Icon size={18} style={{ color: '#0000ff' }} />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">{label}</p>
          <p className="text-xs text-slate-400">{description}</p>
        </div>
      </div>
      <button type="button" onClick={onChange}
        className={`relative w-12 h-6 rounded-full transition-all duration-300 focus:outline-none ${value ? 'bg-blue-600' : 'bg-slate-200'}`}
        style={value ? { backgroundColor: '#0000ff' } : {}}>
        <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all duration-300 ${value ? 'left-[26px]' : 'left-0.5'}`} />
      </button>
    </div>
  );

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-slate-900">Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your account preferences.</p>
      </div>

      {toast.msg && (
        <div className={`flex items-center gap-3 rounded-xl px-4 py-3 mb-5 text-sm font-semibold max-w-xl ${
          toast.type === 'error' ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {toast.type === 'error' ? <MdErrorOutline size={20} /> : <MdCheckCircle size={20} />}
          {toast.msg}
        </div>
      )}

      <div className="max-w-xl space-y-4">
        {/* Appearance */}
        <div className="bg-white rounded-2xl shadow-sm p-5">
          <h2 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2"><MdPalette size={17} style={{ color: '#0000ff' }} /> Appearance</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Theme</label>
              <div className="flex gap-3">
                {['light', 'dark'].map(t => (
                  <button key={t} type="button" onClick={() => setPrefs(p => ({ ...p, theme: t }))}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-bold border-2 transition-all capitalize ${
                      prefs.theme === t ? 'text-white border-transparent' : 'bg-white text-slate-600 border-slate-200'
                    }`}
                    style={prefs.theme === t ? { backgroundColor: '#0000ff', borderColor: '#0000ff' } : {}}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Language</label>
              <select value={prefs.language} onChange={e => setPrefs(p => ({ ...p, language: e.target.value }))}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-900 focus:outline-none"
                onFocus={el => el.target.style.borderColor = '#0000ff'}
                onBlur={el => el.target.style.borderColor = '#e2e8f0'}>
                <option value="en">English</option>
                <option value="yo">Yoruba</option>
                <option value="ha">Hausa</option>
                <option value="ig">Igbo</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white rounded-2xl shadow-sm p-5">
          <h2 className="text-sm font-bold text-slate-700 mb-2 flex items-center gap-2"><MdNotifications size={17} style={{ color: '#0000ff' }} /> Notifications</h2>
          <Toggle
            label="Transaction Alerts"
            description="Get notified for every debit and credit."
            icon={MdSettings}
            value={prefs.notify_transactions}
            onChange={() => setPrefs(p => ({ ...p, notify_transactions: !p.notify_transactions }))}
          />
          <Toggle
            label="Promotions & Offers"
            description="Receive promotional messages from Sentinel."
            icon={MdLanguage}
            value={prefs.notify_promotions}
            onChange={() => setPrefs(p => ({ ...p, notify_promotions: !p.notify_promotions }))}
          />
        </div>

        <button onClick={save} disabled={isLoading}
          className="w-full py-4 rounded-xl text-white font-bold text-sm transition-all active:scale-[0.98] disabled:opacity-60"
          style={{ backgroundColor: '#0000ff', boxShadow: '0 8px 20px rgba(0,0,255,0.2)' }}
          onMouseEnter={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#1414ff'; }}
          onMouseLeave={e => { if (!isLoading) e.currentTarget.style.backgroundColor = '#0000ff'; }}
        >
          {isLoading ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </Layout>
  );
};

export default Settings;
