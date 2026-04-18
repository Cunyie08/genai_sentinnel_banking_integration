import React from 'react';
import { Users, AlertTriangle, CheckCircle, Activity, DollarSign } from 'lucide-react';

const StatCard = ({ label, value, color, icon: Icon }) => (
    <div className="bg-white dark:bg-vault-dark-card p-6 rounded-xl border border-gray-200 dark:border-white/5 shadow-sm flex items-center justify-between">
        <div>
            <h4 className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">{label}</h4>
            <p className="text-2xl font-black text-gray-900 dark:text-white mt-1">{value ?? '—'}</p>
        </div>
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${color}`}>
            <Icon size={20} />
        </div>
    </div>
);

const OverviewModule = ({ stats, ticketCount }) => {
  const totalTxns  = stats?.total_transactions ?? '—';
  const totalAmt   = stats?.total_amount != null
    ? `₦${Number(stats.total_amount).toLocaleString('en-NG', { minimumFractionDigits: 0 })}`
    : '—';

  return (
    <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">System Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard label="Total Transactions" value={totalTxns.toLocaleString?.()} color="bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400" icon={Activity} />
            <StatCard label="Transaction Volume" value={totalAmt} color="bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400" icon={DollarSign} />
            <StatCard label="Open Complaints" value={ticketCount ?? 0} color="bg-yellow-100 dark:bg-yellow-500/20 text-yellow-600 dark:text-yellow-400" icon={AlertTriangle} />
            <StatCard label="System Health" value="99.9%" color="bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400" icon={CheckCircle} />
        </div>
    </div>
  );
};

export default OverviewModule;