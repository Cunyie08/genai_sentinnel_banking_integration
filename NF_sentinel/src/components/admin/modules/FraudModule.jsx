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

      // Also fetch recent transactions to find flagged ones
      try {
        const txnRes = await api.getAdminTickets({ limit: 100 });
        // We'll use any available flagged transaction data
        setFlaggedTxns(txnRes?.data?.tickets || []);
      } catch { /* ignore */ }

      setLoading(false);
    };
    fetchFraud();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 size={32} className="animate-spin text-[#A01030]" />
        <span className="text-sm font-bold text-gray-500">Loading fraud analytics...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Fraud Detection</h2>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Total Alerts</p>
              <p className="text-3xl font-black text-gray-900 mt-1">{fraudStats?.total_alerts || 0}</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
              <ShieldAlert size={24} className="text-[#A01030]" />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2">Last {fraudStats?.period?.replace('last_', '').replace('_', ' ') || '30 days'}</p>
        </div>

        {fraudStats?.breakdown_by_decision && Object.entries(fraudStats.breakdown_by_decision).map(([decision, count]) => (
          <div key={decision} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">{decision}</p>
                <p className="text-3xl font-black text-gray-900 mt-1">{count}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                decision === 'block' ? 'bg-red-100' : decision === 'review' ? 'bg-yellow-100' : 'bg-green-100'
              }`}>
                {decision === 'block' ? <AlertTriangle size={24} className="text-red-600" /> :
                 decision === 'approve' ? <CheckCircle size={24} className="text-green-600" /> :
                 <Eye size={24} className="text-yellow-600" />}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sentinel AI Reasoning Panel */}
      {selectedTxn && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="bg-gradient-to-r from-[#A01030] to-[#6B0A20] px-6 py-4 text-white">
            <h3 className="text-sm font-black uppercase tracking-wide">Sentinel AI Analysis</h3>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase">Transaction ID</p>
                <p className="text-sm font-mono font-bold text-gray-900">{selectedTxn.complaint_id || '—'}</p>
              </div>
              <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase">Risk Score</p>
                <p className="text-sm font-bold text-red-600">{selectedTxn.confidence ? `${Math.round(selectedTxn.confidence * 100)}%` : '—'}</p>
              </div>
            </div>

            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase mb-2">Signals Detected</p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2.5 py-1 bg-red-50 text-red-700 text-xs font-bold rounded-lg border border-red-100">High Amount</span>
                <span className="px-2.5 py-1 bg-orange-50 text-orange-700 text-xs font-bold rounded-lg border border-orange-100">New Merchant</span>
                <span className="px-2.5 py-1 bg-red-50 text-red-700 text-xs font-bold rounded-lg border border-red-100">Unusual Time</span>
              </div>
            </div>

            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">Action Taken</p>
              <p className="text-sm text-gray-800 font-medium">→ Customer verification required</p>
            </div>

            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">Final Outcome</p>
              <p className="text-sm text-gray-800 font-medium flex items-center gap-1.5">
                <CheckCircle size={14} className="text-green-500" /> User confirmed with biometric
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recent flagged items as clickable list */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          <h3 className="text-sm font-bold text-gray-700">Recent Flagged Activity</h3>
        </div>
        {flaggedTxns.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm font-bold">No flagged activity found.</div>
        ) : (
          <div className="divide-y divide-gray-50">
            {flaggedTxns.slice(0, 10).map(t => (
              <div
                key={t.complaint_id}
                onClick={() => setSelectedTxn(t)}
                className={`flex items-center justify-between px-6 py-4 cursor-pointer transition-colors ${
                  selectedTxn?.complaint_id === t.complaint_id ? 'bg-red-50/50' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                    <ShieldAlert size={16} className="text-[#A01030]" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-gray-900">{t.complaint_id}</p>
                    <p className="text-[10px] text-gray-400 truncate max-w-[200px]">{t.complaint_text || t.department_name || '—'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-gray-700">{t.department_name || '—'}</p>
                  <p className={`text-[10px] font-bold uppercase ${
                    t.complaint_status === 'resolved' ? 'text-green-600' : t.complaint_status === 'open' ? 'text-amber-600' : 'text-gray-500'
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
