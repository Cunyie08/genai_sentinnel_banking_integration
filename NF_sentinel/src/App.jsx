import React, { useEffect } from 'react';
import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { triggerPayment } from './features/uiSlice';

import AuthScreens from './screens/AuthScreens';
import HomeScreen from './screens/HomeScreen';
import ChatScreen from './screens/ChatScreen';
import AdminDashboard from './screens/AdminDashboard';
import AdminLogin from './screens/AdminLogin';
import BottomNav from './components/BottomNav';
import { VoiceModal, SentinelModal } from './components/SystemModals';
import PaymentModal from './components/PaymentModal';

import SendScreen from './screens/SendScreen';
import FundScreen from './screens/FundScreen';
import HistoryScreen from './screens/HistoryScreen';
import AirtimeScreen from './screens/AirtimeScreen';
import DataScreen from './screens/DataScreen';
import BillsScreen from './screens/BillsScreen';
import BettingScreen from './screens/BettingScreen';
import ProfileScreen from './screens/ProfileScreen';
import MerchantCheckout from './screens/MerchantCheckout';

import DesktopSidebar from './components/DesktopSidebar';
import FloatingNav from './components/FloatingNav';
import ProtectedRoute from './components/ProtectedRoute';

const App = () => {
  const dispatch = useDispatch();
  const location = useLocation();

  const path = location.pathname.toLowerCase();
  const isAdmin = path.includes('/admin');
  const isMerchant = path === '/merchant';
  const isAuth = path === '/' || path === '/login' || path === '/signup';
  const isChat = path === '/chat';
  const isHome = path === '/home';

  useEffect(() => {
    const saved = localStorage.getItem('sentinel_dark_mode');
    if (saved === 'true') {
      document.documentElement.classList.remove('light');
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
    }
  }, []);

  if (isMerchant) {
    return (
      <div className="h-[100dvh] w-full bg-vault-dark-bg font-sans overflow-y-auto">
        <Routes>
          <Route path="/merchant" element={<MerchantCheckout />} />
        </Routes>
      </div>
    );
  }

  if (isAuth || path === '/admin/login') {
    return (
      <div className="min-h-[100dvh] w-full font-sans">
        <Routes>
          <Route path="/" element={<AuthScreens />} />
          <Route path="/login" element={<AuthScreens />} />
          <Route path="/signup" element={<AuthScreens />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    );
  }


  return (
    <div className={`h-[100dvh] w-full flex overflow-hidden font-sans vault-bg-glow
      ${isAdmin
        ? 'bg-vault-light-bg dark:bg-vault-dark-bg'
        : 'bg-vault-light-bg dark:bg-vault-dark-bg'
      }`}
    >

      {!isAdmin && !isAuth && (
        <DesktopSidebar activeRoute={path} />
      )}

      <main className="flex-1 h-full flex flex-col overflow-hidden min-w-0 bg-vault-light-card dark:bg-vault-dark-bg relative z-[1]">
        <div className="flex-1 overflow-y-auto hide-scrollbar">
          <Routes>
            <Route path="/home"            element={<ProtectedRoute><HomeScreen /></ProtectedRoute>} />
            <Route path="/chat"            element={<ProtectedRoute><ChatScreen /></ProtectedRoute>} />
            <Route path="/send"            element={<ProtectedRoute><SendScreen /></ProtectedRoute>} />
            <Route path="/fund"            element={<ProtectedRoute><FundScreen /></ProtectedRoute>} />
            <Route path="/history"         element={<ProtectedRoute><HistoryScreen /></ProtectedRoute>} />
            <Route path="/airtime"         element={<ProtectedRoute><AirtimeScreen /></ProtectedRoute>} />
            <Route path="/data"            element={<ProtectedRoute><DataScreen /></ProtectedRoute>} />
            <Route path="/bills"           element={<ProtectedRoute><BillsScreen /></ProtectedRoute>} />
            <Route path="/betting"         element={<ProtectedRoute><BettingScreen /></ProtectedRoute>} />
            <Route path="/profile"         element={<ProtectedRoute><ProfileScreen /></ProtectedRoute>} />
            <Route path="/admin/dashboard" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
            <Route path="*"               element={<Navigate to="/home" replace />} />
          </Routes>
        </div>

        {!isAdmin && !isAuth && !isChat && (
          <div className="md:hidden">
             <BottomNav />
          </div>
        )}
      </main>

      <VoiceModal />
      <SentinelModal />
      <PaymentModal />

    </div>
  );
};

export default App;
