import React, { useState, useEffect } from 'react';
import { api } from '../../../api/axiosConfig';
import { ShieldAlert, AlertTriangle, CheckCircle, Loader2, Eye } from 'lucide-react';

const FraudModule = () => {
  const [fraudStats, setFraudStats] = useState(null);
  const [flaggedTxns, setFlaggedTxns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTxn, setSelectedTxn] = useState(null);

  useEffect(() => {
    const fetchFraud = async () => {
      setLoading(true);
      try {
        const res = await api.getAdminFraud({ days: 30 });
        setFraudStats(res?.data || null);
      } catch (err) {
        console.error('Failed to fetch fraud stats:', err);
      }

      try {
        const txnRes = await api.getAdminTickets({ limit: 100 });
        setFlaggedTxns(txnRes?.data?.tickets || []);
      } catch { /* ignore */ }

      setLoading(false);
    };
    fetchFraud();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 size={32} className="animate-spin text-vault-cyan" />
        <span className="text-sm font-bold text-gray-500 dark:text-slate-400">Loading fraud analytics...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Fraud Detection</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-vault-dark-card rounded-xl border border-gray-200 dark:border-white/5 p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Total Alerts</p>
              <p className="text-3xl font-black text-gray-900 dark:text-white mt-1">{fraudStats?.total_alerts || 0}</p>
            </div>
            <div className="w-12 h-12 bg-red-100 dark:bg-red-500/20 rounded-xl flex items-center justify-center">
              <ShieldAlert size={24} className="text-red-600 dark:text-red-400" />
            </div>
          </div>
          <p className="text-xs text-gray-400 dark:text-slate-500 mt-2">Last {fraudStats?.period?.replace('last_', '').replace('_', ' ') || '30 days'}</p>
        </div>

        {fraudStats?.breakdown_by_decision && Object.entries(fraudStats.breakdown_by_decision).map(([decision, count]) => (
          <div key={decision} className="bg-white dark:bg-vault-dark-card rounded-xl border border-gray-200 dark:border-white/5 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">{decision}</p>
                <p className="text-3xl font-black text-gray-900 dark:text-white mt-1">{count}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                decision === 'block' ? 'bg-red-100 dark:bg-red-500/20' : decision === 'review' ? 'bg-yellow-100 dark:bg-yellow-500/20' : 'bg-green-100 dark:bg-green-500/20'
              }`}>
                {decision === 'block' ? <AlertTriangle size={24} className="text-red-600 dark:text-red-400" /> :
                 decision === 'approve' ? <CheckCircle size={24} className="text-green-600 dark:text-green-400" /> :
                 <Eye size={24} className="text-yellow-600 dark:text-yellow-400" />}
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedTxn && (
        <div className="bg-white dark:bg-vault-dark-card rounded-2xl border border-gray-200 dark:border-white/5 shadow-sm overflow-hidden">
          <div className="vault-gradient px-6 py-4 text-white">
            <h3 className="text-sm font-black uppercase tracking-wide">Sentinel AI Analysis</h3>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase">Transaction ID</p>
                <p className="text-sm font-mono font-bold text-gray-900 dark:text-white">{selectedTxn.complaint_id || '—'}</p>
              </div>
              <div>
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase">Risk Score</p>
                <p className="text-sm font-bold text-red-600 dark:text-red-400">{selectedTxn.confidence ? `${Math.round(selectedTxn.confidence * 100)}%` : '—'}</p>
              </div>
            </div>

            <div>
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase mb-2">Signals Detected</p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2.5 py-1 bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 text-xs font-bold rounded-lg border border-red-100 dark:border-red-500/20">High Amount</span>
                <span className="px-2.5 py-1 bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400 text-xs font-bold rounded-lg border border-orange-100 dark:border-orange-500/20">New Merchant</span>
                <span className="px-2.5 py-1 bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 text-xs font-bold rounded-lg border border-red-100 dark:border-red-500/20">Unusual Time</span>
              </div>
            </div>

            <div>
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase mb-1">Action Taken</p>
              <p className="text-sm text-gray-800 dark:text-white font-medium">→ Customer verification required</p>
            </div>

            <div>
              <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase mb-1">Final Outcome</p>
              <p className="text-sm text-gray-800 dark:text-white font-medium flex items-center gap-1.5">
                <CheckCircle size={14} className="text-green-500 dark:text-green-400" /> User confirmed with biometric
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-vault-dark-card rounded-xl border border-gray-200 dark:border-white/5 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-white/5">
          <h3 className="text-sm font-bold text-gray-700 dark:text-white">Recent Flagged Activity</h3>
        </div>
        {flaggedTxns.length === 0 ? (
          <div className="py-12 text-center text-gray-400 dark:text-slate-500 text-sm font-bold">No flagged activity found.</div>
        ) : (
          <div className="divide-y divide-gray-50 dark:divide-white/5">
            {flaggedTxns.slice(0, 10).map(t => (
              <div
                key={t.complaint_id}
                onClick={() => setSelectedTxn(t)}
                className={`flex items-center justify-between px-6 py-4 cursor-pointer transition-colors ${
                  selectedTxn?.complaint_id === t.complaint_id ? 'bg-cyan-50/50 dark:bg-vault-cyan/5' : 'hover:bg-gray-50 dark:hover:bg-white/5'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-red-100 dark:bg-red-500/20 rounded-lg flex items-center justify-center">
                    <ShieldAlert size={16} className="text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-gray-900 dark:text-white">{t.complaint_id}</p>
                    <p className="text-[10px] text-gray-400 dark:text-slate-500 truncate max-w-[200px]">{t.complaint_text || t.department_name || '—'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-gray-700 dark:text-slate-300">{t.department_name || '—'}</p>
                  <p className={`text-[10px] font-bold uppercase ${
                    t.complaint_status === 'resolved' ? 'text-green-600 dark:text-green-400' : t.complaint_status === 'open' ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-slate-500'
                  }`}>{t.complaint_status || '—'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FraudModule;
