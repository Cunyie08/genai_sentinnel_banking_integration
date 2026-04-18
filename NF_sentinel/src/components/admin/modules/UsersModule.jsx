import React from 'react';
import { MoreVertical, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

const UsersModule = ({ users }) => {
  return (
    <div className="space-y-6">
        <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">User Management</h3>
            <div className="flex gap-2">
            <button className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-vault-dark-card border border-gray-200 dark:border-white/5 rounded-lg text-xs font-bold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-white/5">
                <Filter size={14}/> Filter
            </button>
            <button className="flex items-center gap-2 px-3 py-2 vault-gradient text-white rounded-lg text-xs font-bold">
                + Add User
            </button>
            </div>
        </div>

        <div className="bg-white dark:bg-vault-dark-card border border-gray-200 dark:border-white/5 rounded-2xl overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse">
                <thead className="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/5">
                <tr>
                    <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Tier</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider text-right">Balance</th>
                </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                {users && users.map((u, i) => (
                    <tr key={u.id || i} className="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group cursor-pointer">
                    <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gray-100 dark:bg-white/10 flex items-center justify-center overflow-hidden border border-gray-200 dark:border-white/5">
                            <span className="font-bold text-gray-500 dark:text-slate-400 text-xs">{u.name?.substring(0,2).toUpperCase()}</span>
                        </div>
                        <span className="text-sm font-bold text-gray-900 dark:text-white">{u.name}</span>
                        </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-slate-400">{u.email}</td>
                    <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded uppercase border border-blue-100 dark:border-blue-500/20">{u.tier}</span>
                    </td>
                    <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-[10px] font-bold rounded uppercase border flex items-center gap-1.5 w-fit ${u.status === 'Active' ? 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border-green-100 dark:border-green-500/20' : 'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-100 dark:border-red-500/20'}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${u.status === 'Active' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                            {u.status}
                        </span>
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-mono font-medium text-gray-700 dark:text-slate-300">{u.balance}</td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    </div>
  );
};

export default UsersModule;