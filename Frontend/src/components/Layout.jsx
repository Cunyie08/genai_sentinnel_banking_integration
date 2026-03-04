import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  MdDashboard, MdSwapHoriz, MdHistory, MdCreditCard,
  MdFlashOn, MdPerson, MdNotifications, MdSettings,
  MdLogout, MdMenu, MdClose, MdShield
} from 'react-icons/md';
import Chatbot from './Chatbot';

const NAV_ITEMS = [
  { to: '/dashboard',      icon: MdDashboard,     label: 'Dashboard' },
  { to: '/transfer',       icon: MdSwapHoriz,     label: 'Transfer' },
  { to: '/history',        icon: MdHistory,        label: 'History' },
  { to: '/cards',          icon: MdCreditCard,     label: 'Cards' },
  { to: '/services',       icon: MdFlashOn,        label: 'Services' },
  { to: '/profile',        icon: MdPerson,         label: 'Profile' },
  { to: '/notifications',  icon: MdNotifications,  label: 'Alerts' },
  { to: '/settings',       icon: MdSettings,       label: 'Settings' },
];

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login', { replace: true });
  };

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
      isActive
        ? 'bg-white text-[#0000ff]'
        : 'text-white/80 hover:bg-white/10 hover:text-white'
    }`;

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-6 mb-2">
        <div className="bg-white p-2 rounded-lg flex items-center justify-center">
          <MdShield size={22} style={{ color: '#0000ff' }} />
        </div>
        <span className="text-white text-lg font-extrabold tracking-tight">Sentinel Bank</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={linkClass} onClick={() => setMobileOpen(false)}>
            <Icon size={20} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="px-3 pb-6 mt-4">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-semibold text-white/70 hover:bg-white/10 hover:text-white transition-all"
        >
          <MdLogout size={20} />
          Logout
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex" style={{ fontFamily: 'Manrope, sans-serif', backgroundColor: '#f5f5f8' }}>

      {/* Desktop Sidebar */}
      <aside
        className="hidden lg:flex flex-col w-64 fixed top-0 left-0 h-full z-30"
        style={{ backgroundColor: '#0000ff' }}
      >
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Drawer */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 z-50 transform transition-transform duration-300 lg:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ backgroundColor: '#0000ff' }}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 text-white/70 hover:text-white"
        >
          <MdClose size={24} />
        </button>
        <SidebarContent />
      </aside>

      {/* Main content */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Mobile top bar */}
        <header className="lg:hidden flex items-center justify-between px-5 py-4 bg-white shadow-sm sticky top-0 z-20">
          <button onClick={() => setMobileOpen(true)} className="text-slate-700">
            <MdMenu size={26} />
          </button>
          <div className="flex items-center gap-2">
            <MdShield size={20} style={{ color: '#0000ff' }} />
            <span className="font-extrabold text-slate-900 text-base">Sentinel Bank</span>
          </div>
          <NavLink to="/notifications" className="text-slate-500 hover:text-blue-600">
            <MdNotifications size={24} />
          </NavLink>
        </header>

        {/* Page content */}
        <main className="flex-1 px-5 py-6 sm:px-8 max-w-6xl w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Floating Chat */}
      <Chatbot />
    </div>
  );
};

export default Layout;
