import React from 'react';
import { Users, AlertTriangle, CheckCircle, Activity } from 'lucide-react';

const StatCard = ({ label, value, color, icon: Icon }) => (
    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
        <div>
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">{label}</h4>
            <p className="text-2xl font-black text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${color}`}>
            <Icon size={20} />
        </div>
    </div>
);

const OverviewModule = ({ stats }) => {
  if (!stats) return <div>Loading stats...</div>;

  return (
    <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard label="Total Users" value={stats.totalUsers?.toLocaleString()} color="bg-blue-100 text-blue-600" icon={Users} />
            <StatCard label="Pending Tickets" value={stats.pendingTickets} color="bg-yellow-100 text-yellow-600" icon={AlertTriangle} />
            <StatCard label="Resolved Today" value={stats.activeToday} color="bg-green-100 text-green-600" icon={CheckCircle} />
            <StatCard label="System Health" value="99.9%" color="bg-purple-100 text-purple-600" icon={Activity} />
        </div>
    </div>
  );
};

export default OverviewModule;