import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setAdminTab, setRoute } from '../../features/uiSlice';
import { LayoutGrid, Users, Bell, ShieldAlert, Settings, LogOut } from 'lucide-react';

const SidebarItem = ({ id, icon: Icon, label }) => {
  const dispatch = useDispatch();
  const activeTab = useSelector(state => state.ui.adminActiveTab);

  return (
    <button
      onClick={() => dispatch(setAdminTab(id))}
      className={`w-full flex items-center gap-3 px-6 py-4 text-sm font-medium border-l-4 transition-all ${
        activeTab === id
          ? 'bg-red-50 text-[#A01030] border-[#A01030]'
          : 'text-gray-500 border-transparent hover:bg-gray-50'
      }`}
    >
      <Icon size={20} />
      {label}
    </button>
  );
};

const DashboardLayout = ({ children }) => {
  const dispatch = useDispatch();
  
  return (
    <div className="flex h-screen bg-[#F8F9FB] font-sans overflow-hidden">
      {/* SIDEBAR */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20">
        <div className="h-20 flex items-center px-6 border-b border-gray-100">
           <div className="w-8 h-8 bg-[#A01030] rounded-lg flex items-center justify-center text-white font-black mr-3">N</div>
           <span className="text-xl font-bold text-gray-900 tracking-tight">Nexus<span className="text-[#A01030]">Bank</span></span>
        </div>

        <div className="flex-1 py-6 space-y-1">
          <SidebarItem id="overview" icon={LayoutGrid} label="Overview" />
          <SidebarItem id="users" icon={Users} label="Users" />
          <SidebarItem id="complaints" icon={Bell} label="Complaints" />
          <SidebarItem id="fraud" icon={ShieldAlert} label="Fraud Detection" />
          <div className="pt-8 pb-2 px-6 text-xs font-bold text-gray-400 uppercase tracking-wider">Settings</div>
          <SidebarItem id="config" icon={Settings} label="System Config" />
        </div>

        <div className="p-4 border-t border-gray-100">
            <button onClick={() => dispatch(setRoute('welcome'))} className="flex items-center gap-2 text-gray-500 hover:text-[#A01030] text-sm font-bold">
               <LogOut size={16} /> Logout
            </button>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto p-8">
            {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;