import { useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { api } from '../api/axiosConfig';

import { Lock, Shield, ArrowRight, AlertCircle } from 'lucide-react';

const AdminLogin = () => {
  const navigate = useNavigate();
  const [id, setId] = useState('');
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError('');
    setLoading(true);

    try {
      await api.adminLogin({ email: id.trim(), password: key });

      localStorage.setItem('sentinel_admin', JSON.stringify({
        email: id.trim(),
        loggedInAt: new Date().toISOString(),
      }));
      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please check your Admin ID and Secure Key.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-vault-dark-bg flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute -top-32 -right-32 w-96 h-96 bg-vault-cyan/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-vault-purple/15 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-sm w-full bg-vault-dark-card rounded-[24px] border border-white/5 p-8 text-center shadow-2xl relative z-10">

        <div className="w-16 h-16 vault-gradient rounded-2xl flex items-center justify-center mx-auto mb-6 vault-glow">
          <Shield size={32} className="text-white" />
        </div>

        <h1 className="text-2xl font-bold text-white">Sentinnel Admin</h1>
        <p className="text-slate-500 text-sm mb-8">Secure Gateway v2.0</p>

        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium rounded-xl p-3 mb-4 text-left">
            <AlertCircle size={16} className="shrink-0" />
            {error}
          </div>
        )}

        <div className="space-y-4 text-left">
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Admin Email</label>
            <input
              value={id} onChange={e => { setId(e.target.value); setError(''); }}
              type="email"
              className="w-full p-4 bg-vault-dark-input border border-white/5 rounded-xl outline-none focus:border-vault-cyan focus:ring-2 focus:ring-vault-cyan/20 text-white transition-colors font-mono placeholder:text-slate-600"
              placeholder="admin@sentinnelbank.com"
            />
          </div>
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase ml-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                value={key} onChange={e => { setKey(e.target.value); setError(''); }}
                type="password"
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                className="w-full p-4 pl-12 bg-vault-dark-input border border-white/5 rounded-xl outline-none focus:border-vault-cyan focus:ring-2 focus:ring-vault-cyan/20 text-white transition-colors placeholder:text-slate-600"
                placeholder="••••••••"
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleLogin}
          disabled={loading || !id.trim() || !key.trim()}
          className="w-full vault-gradient text-white py-4 rounded-xl font-bold mt-8 transition-all shadow-lg vault-glow active:scale-95 flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <>Authenticate <ArrowRight size={18}/></>
          )}
        </button>

        <button
          onClick={() => navigate('/')}
          className="mt-6 text-xs font-bold text-slate-500 hover:text-white transition-colors"
        >
          ← Return to Mobile App
        </button>
      </div>
    </div>
  );
};

export default AdminLogin;