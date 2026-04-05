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

const App = () => {
  const dispatch = useDispatch();
  const location = useLocation();

  const path = location.pathname.toLowerCase();
  const isAdmin = path.includes('/admin');
  const isMerchant = path === '/merchant';
  const isAuth = path === '/' || path === '/login' || path === '/signup';
  const isChat = path === '/chat';
  const isHome = path === '/home';

  if (isMerchant) {
    return (
      <div className="h-[100dvh] w-full bg-[#0A0A0A] font-sans overflow-y-auto">
        <Routes>
          <Route path="/merchant" element={<MerchantCheckout />} />
        </Routes>
      </div>
    );
  }

  if (isAuth || path === '/admin/login') {
    return (
      <div className="h-[100dvh] w-full overflow-hidden font-sans">
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
    <div className={`h-[100dvh] w-full flex overflow-hidden font-sans ${isAdmin ? 'bg-gray-100' : 'bg-gray-50'}`}>

      {!isAdmin && !isAuth && (
        <DesktopSidebar activeRoute={path} />
      )}

      <main className="flex-1 h-full flex flex-col overflow-hidden min-w-0 bg-white relative">
        <div className="flex-1 overflow-y-auto hide-scrollbar">
          <Routes>
            <Route path="/home" element={<HomeScreen />} />
            <Route path="/chat" element={<ChatScreen />} />
            <Route path="/send" element={<SendScreen />} />
            <Route path="/fund" element={<FundScreen />} />
            <Route path="/history" element={<HistoryScreen />} />
            <Route path="/airtime" element={<AirtimeScreen />} />
            <Route path="/data" element={<DataScreen />} />
            <Route path="/bills" element={<BillsScreen />} />
            <Route path="/betting" element={<BettingScreen />} />
            <Route path="/profile" element={<ProfileScreen />} />
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
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
