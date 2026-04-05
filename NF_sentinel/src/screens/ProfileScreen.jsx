import { useNavigate } from 'react-router-dom';

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { logoutUser } from '../features/authSlice';
import {
  ChevronLeft, ChevronRight, User, Bell, Shield,
  HelpCircle, LogOut, Moon, Fingerprint,
  CreditCard, FileText, Star, Globe, ChevronDown,
  ShoppingCart, ExternalLink
} from 'lucide-react';

const Toggle = ({ on, onToggle }) => (
  <button onClick={onToggle} type="button"
    className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${on ? 'bg-[#A01030]' : 'bg-gray-200'}`}>
    <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${on ? 'translate-x-5' : 'translate-x-0'}`} />
  </button>
);

const ProfileScreen = () => {
  const navigate = useNavigate();

  const dispatch = useDispatch();
  const user = useSelector(s => s.auth.user);
  const [notifs,      setNotifs]      = useState(true);
  const [biometrics,  setBiometrics]  = useState(true);
  const [darkMode,    setDarkMode]    = useState(false);
  const [loggingOut,  setLoggingOut]  = useState(false);

  const handleLogout = async () => {
    setLoggingOut(true);
    await dispatch(logoutUser());
    navigate('/login');
  };

  const SettingRow = ({ icon: Icon, label, sublabel, action, danger = false, right }) => (
    <button onClick={action}
      className={`w-full flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors text-left ${danger ? 'hover:bg-red-50' : ''}`}>
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${danger ? 'bg-red-50' : 'bg-gray-100'}`}>
        <Icon size={17} className={danger ? 'text-red-500' : 'text-gray-500'} />
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-bold ${danger ? 'text-red-600' : 'text-gray-800'}`}>{label}</p>
        {sublabel && <p className="text-[11px] text-gray-400">{sublabel}</p>}
      </div>
      {right ?? <ChevronRight size={16} className="text-gray-300 shrink-0" />}
    </button>
  );

  return (
    <div className="min-h-full w-full bg-[#F8F9FB] font-sans">

      {}
      <header className="sticky top-0 z-20 bg-[#F8F9FB]/95 backdrop-blur-sm border-b border-gray-100 px-4 sm:px-6 xl:px-8 py-4 flex items-center gap-3">
        <button onClick={() => navigate('/home')}
          className="w-9 h-9 rounded-xl bg-white border border-gray-100 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors">
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <h1 className="text-lg font-extrabold text-gray-900">Profile & Settings</h1>
      </header>

      <div className="w-full px-4 sm:px-6 xl:px-8 py-6 pb-28 max-w-2xl xl:max-w-none space-y-5">

        {}
        <div className="bg-gradient-to-br from-[#800020] via-[#A01030] to-[#5a0a1e] rounded-2xl p-6 text-white shadow-lg shadow-red-900/20 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
          <div className="flex items-center gap-4 relative z-10">
            <div className="w-16 h-16 rounded-2xl bg-white/20 border-2 border-white/30 overflow-hidden shrink-0">
              <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'Tunde'}`} alt="Avatar" className="w-full h-full" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-lg font-black leading-tight truncate">{user?.name || 'Reuben'}</p>
              <p className="text-white/70 text-xs truncate">{user?.email || 'reuben@sentinel.ng'}</p>
              <p className="text-white/70 text-xs">{user?.phone || '+234 800 000 0000'}</p>
            </div>
            <div className="bg-[#FFD700]/20 border border-[#FFD700]/30 px-3 py-1 rounded-full shrink-0">
              <span className="text-[#FFD700] text-[10px] font-bold uppercase tracking-wider">Premium</span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3 mt-5 pt-5 border-t border-white/15 relative z-10">
            {[
              { label: 'Account',  value: user?.account || '0123456789' },
              { label: 'Balance',  value: '₦400,850'                    },
              { label: 'Tier',     value: 'Tier 3'                      },
            ].map(s => (
              <div key={s.label} className="text-center">
                <p className="text-white font-extrabold text-sm">{s.value}</p>
                <p className="text-white/50 text-[10px] uppercase tracking-wide">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-5 pt-4 pb-2">Account</p>
          <SettingRow icon={User}       label="Personal Information"  sublabel="Name, phone, email"         action={() => {}} />
          <SettingRow icon={CreditCard} label="Bank Accounts"         sublabel="Linked accounts & cards"    action={() => {}} />
          <SettingRow icon={Star}       label="Upgrade to Premium"    sublabel="Unlock higher limits"       action={() => {}} />
          <SettingRow icon={FileText}   label="Statements"            sublabel="Download account statement" action={() => navigate('/history')} />
        </div>

        {}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-5 pt-4 pb-2">Preferences</p>
          <SettingRow icon={Bell}
            label="Push Notifications"
            sublabel={notifs ? 'Enabled' : 'Disabled'}
            action={() => setNotifs(!notifs)}
            right={<Toggle on={notifs} onToggle={() => setNotifs(!notifs)} />}
          />
          <SettingRow icon={Fingerprint}
            label="Biometric Login"
            sublabel={biometrics ? 'Face ID / Fingerprint on' : 'Disabled'}
            action={() => setBiometrics(!biometrics)}
            right={<Toggle on={biometrics} onToggle={() => setBiometrics(!biometrics)} />}
          />
          <SettingRow icon={Moon}
            label="Dark Mode"
            sublabel={darkMode ? 'On' : 'Off'}
            action={() => setDarkMode(!darkMode)}
            right={<Toggle on={darkMode} onToggle={() => setDarkMode(!darkMode)} />}
          />
          <SettingRow icon={Globe} label="Language" sublabel="English (Nigeria)" action={() => {}} />
        </div>

        {}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-5 pt-4 pb-2">Security</p>
          <SettingRow icon={Shield} label="Change PIN"     sublabel="Update your transaction PIN" action={() => {}} />
          <SettingRow icon={Shield} label="Change Password" sublabel="Update login password"      action={() => {}} />
          <SettingRow icon={Shield} label="2-Factor Auth"  sublabel="Add extra login security"    action={() => {}} />
        </div>

        {}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-5 pt-4 pb-2">Support</p>
          <SettingRow icon={HelpCircle} label="Help Center"    sublabel="FAQs and guides"        action={() => {}} />
          <SettingRow icon={HelpCircle} label="Contact Us"     sublabel="Chat with support"      action={() => navigate('/chat')} />
          <SettingRow icon={Star}       label="Rate the App"   sublabel="Leave us a review"      action={() => {}} />
        </div>

        {/* Demo Simulation */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-5 pt-4 pb-2">Demo & Simulation</p>
          <button
            onClick={() => window.open('/merchant', '_blank')}
            className="w-full flex items-center gap-4 px-5 py-4 hover:bg-blue-50 transition-colors text-left"
          >
            <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-blue-100">
              <ShoppingCart size={17} className="text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-gray-800">Merchant Simulator</p>
              <p className="text-[11px] text-gray-400">Simulate a card payment to test Sentinnel AI</p>
            </div>
            <ExternalLink size={16} className="text-blue-400 shrink-0" />
          </button>
        </div>

        {}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <SettingRow icon={LogOut}
            label={loggingOut ? 'Logging out...' : 'Logout'}
            sublabel="Sign out of your account"
            action={handleLogout}
            danger
            right={loggingOut
              ? <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
              : <ChevronRight size={16} className="text-red-300 shrink-0" />
            }
          />
        </div>

        <p className="text-center text-[10px] text-gray-300 font-bold uppercase tracking-widest pb-4">
          Sentinnel Licensed by CBN
        </p>
      </div>
    </div>
  );
};

export default ProfileScreen;