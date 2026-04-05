import { useNavigate } from 'react-router-dom';
import React from 'react';
import { useDispatch } from 'react-redux';


const DesktopSidebar = ({ activeRoute }) => {
  const navigate = useNavigate();

  const dispatch = useDispatch();

  const navItems = [
    { route: 'home',    label: 'Home' },
    { route: 'chat',    label: 'Chat' },
    { route: 'airtime', label: 'Airtime' },
    { route: 'data',    label: 'Data' },
    { route: 'bills',   label: 'Bills' },
    { route: 'betting', label: 'Betting' },
    { route: 'history', label: 'History' },
    { route: 'profile', label: 'Profile' },
  ];

  return (
    <aside className="hidden md:flex flex-col w-60 lg:w-64 xl:w-72 h-full bg-white border-r border-gray-100 shrink-0">
      <div className="px-6 py-6 border-b border-gray-100">
        <h1 className="text-lg font-extrabold text-gray-900">Sentinnel</h1>
        <p className="text-xs text-gray-400">Bank</p>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
        {navItems.map(item => {
          const active = activeRoute === item.route;
          return (
            <button
              key={item.route}
              onClick={() => navigate(item.route)}
              className={`w-full text-left px-4 py-2 rounded-xl text-sm transition
                ${active
                  ? 'bg-rose-50 text-rose-700 font-bold'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-800'}`}
            >
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
};

export default DesktopSidebar;