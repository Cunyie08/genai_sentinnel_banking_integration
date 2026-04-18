import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { setAdminTab } from '../../features/uiSlice';
import { LayoutDashboard, Users, MessageSquareWarning, ShieldAlert, Settings, LogOut, Activity } from 'lucide-react';

const TABS = [
  { id: 'overview',   label: 'Overview',    icon: LayoutDashboard },
  { id: 'users',      label: 'Users',       icon: Users           },
  { id: 'complaints', label: 'Complaints',  icon: MessageSquareWarning },
  { id: 'fraud',      label: 'Fraud',       icon: ShieldAlert     },
  { id: 'config',     label: 'Config',      icon: Settings        },
];

const DashboardLayout = ({ children, stats }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const activeTab = useSelector(state => state.ui.adminActiveTab);

  const handleLogout = () => {
    localStorage.removeItem('sentinel_admin');
    navigate('/admin');
  };

  return (
    <div className="flex h-full w-full bg-vault-light-bg dark:bg-vault-dark-bg vault-transition">
      <aside className="hidden md:flex flex-col w-64 bg-white dark:bg-vault-dark-card border-r border-gray-100 dark:border-white/5 shrink-0 vault-transition">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-white/5">
          <h1 className="text-base font-extrabold vault-gradient-text">Sentinel Admin</h1>
          <p className="text-[10px] text-gray-400 dark:text-slate-500 font-bold uppercase tracking-widest">Dashboard</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => dispatch(setAdminTab(tab.id))}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === tab.id
                  ? 'vault-gradient text-white shadow-lg vault-glow'
                  : 'text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-white/5 hover:text-gray-800 dark:hover:text-white'
              }`}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="px-3 pb-4 mt-auto">
          <button onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-bold text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/5 transition-colors">
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-6 md:p-8">
        <div className="md:hidden flex gap-2 overflow-x-auto pb-4 mb-4 scrollbar-hide">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => dispatch(setAdminTab(tab.id))}
              className={`shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === tab.id
                  ? 'vault-gradient text-white shadow-md'
                  : 'bg-white dark:bg-vault-dark-card text-gray-500 dark:text-slate-400 border border-gray-100 dark:border-white/5'
              }`}
            >
              <tab.icon size={14} />
              {tab.label}
            </button>
          ))}
        </div>

        {children}
      </main>
    </div>
  );
};

export default DashboardLayout;