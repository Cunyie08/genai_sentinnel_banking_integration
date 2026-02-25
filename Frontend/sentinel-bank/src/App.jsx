// import React, { useEffect } from 'react';
// import { useSelector, useDispatch } from 'react-redux';
// import { setRoute, triggerPayment } from './features/uiSlice';

// import AuthScreens from './screens/AuthScreens';
// import HomeScreen from './screens/HomeScreen';
// import ChatScreen from './screens/ChatScreen';
// import AdminDashboard from './screens/AdminDashboard';
// import AdminLogin from './screens/AdminLogin';
// import BottomNav from './components/BottomNav';
// import { VoiceModal, SentinelModal } from './components/SystemModals';
// import PaymentModal from './components/PaymentModal';

// // NEW Screens
// import SendScreen from './screens/SendScreen';
// import FundScreen from './screens/FundScreen';
// import HistoryScreen from './screens/HistoryScreen';
// import AirtimeScreen from './screens/AirtimeScreen';
// import DataScreen from './screens/DataScreen';
// import BillsScreen from './screens/BillsScreen';
// import BettingScreen from './screens/BettingScreen';
// import ProfileScreen from './screens/ProfileScreen';

// // NEW Components
// import DesktopSidebar from './components/DesktopSidebar';
// import RightPanel from './components/RightPanel';

// const App = () => {
//   const dispatch = useDispatch();
//   const activeRoute = useSelector(state => state.ui.activeRoute);

//   useEffect(() => {
//     const path = window.location.pathname.toLowerCase();

//     if (path.includes('/admin/dashboard'))
//       dispatch(setRoute('adminDashboard'));
//     else if (path.includes('/admin/login'))
//       dispatch(setRoute('adminLogin'));

//     if (activeRoute === 'home') {
//       const timer = setTimeout(() => dispatch(triggerPayment()), 5000);
//       return () => clearTimeout(timer);
//     }
//   }, [dispatch, activeRoute]);

//   const renderScreen = () => {
//     switch (activeRoute) {

//       case 'welcome':
//       case 'login':
//       case 'signup':
//         return <AuthScreens />;

//       case 'home':           return <HomeScreen />;
//       case 'chat':           return <ChatScreen />;
//       case 'adminLogin':     return <AdminLogin />;
//       case 'adminDashboard': return <AdminDashboard />;

//       case 'send':     return <SendScreen />;
//       case 'fund':     return <FundScreen />;
//       case 'history':  return <HistoryScreen />;
//       case 'airtime':  return <AirtimeScreen />;
//       case 'data':     return <DataScreen />;
//       case 'bills':    return <BillsScreen />;
//       case 'betting':  return <BettingScreen />;
//       case 'profile':  return <ProfileScreen />;

//       default:
//         return <AuthScreens />;
//     }
//   };

//   const isAdmin = ['adminLogin', 'adminDashboard'].includes(activeRoute);
//   const isAuth  = ['welcome', 'login', 'signup'].includes(activeRoute);
//   const isHome  = activeRoute === 'home';
//   const showNav = !isAdmin && !isAuth && activeRoute !== 'chat';

//   if (isAuth) {
//     return (
//       <div className="h-[100dvh] w-full overflow-hidden font-sans">
//         <AuthScreens />
//       </div>
//     );
//   }

//   return (
//     <div className={`h-[100dvh] w-full flex overflow-hidden font-sans ${isAdmin ? 'bg-gray-100' : 'bg-gray-50'}`}>

//       {!isAdmin && !isAuth && (
//         <DesktopSidebar activeRoute={activeRoute} />
//       )}

//       <main className="flex-1 h-full flex flex-col overflow-hidden min-w-0 bg-white">
//         <div className="flex-1 overflow-y-auto">
//           {renderScreen()}
//         </div>

//         {showNav && (
//           <div className="md:hidden">
//             <BottomNav />
//           </div>
//         )}

//         {!isAdmin && <VoiceModal />}
//         {!isAdmin && <SentinelModal />}
//         {!isAdmin && <PaymentModal />}
//       </main>

//       {isHome && <RightPanel />}
//     </div>
//   );
// };

// export default App;

import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setRoute, triggerPayment } from './features/uiSlice';

import AuthScreens from './screens/AuthScreens';
import HomeScreen from './screens/HomeScreen';
import ChatScreen from './screens/ChatScreen';
import AdminDashboard from './screens/AdminDashboard';
import AdminLogin from './screens/AdminLogin';
import BottomNav from './components/BottomNav';
import { VoiceModal, SentinelModal } from './components/SystemModals';
import PaymentModal from './components/PaymentModal';

// NEW Screens
import SendScreen from './screens/SendScreen';
import FundScreen from './screens/FundScreen';
import HistoryScreen from './screens/HistoryScreen';
import AirtimeScreen from './screens/AirtimeScreen';
import DataScreen from './screens/DataScreen';
import BillsScreen from './screens/BillsScreen';
import BettingScreen from './screens/BettingScreen';
import ProfileScreen from './screens/ProfileScreen';

// NEW Components
import DesktopSidebar from './components/DesktopSidebar';
import RightPanel from './components/RightPanel';
import SplitNav from './components/SplitNav';
import FloatingNav from './components/FloatingNav';

const App = () => {
  const dispatch = useDispatch();
  const activeRoute = useSelector(state => state.ui.activeRoute);

  useEffect(() => {
    const path = window.location.pathname.toLowerCase();

    if (path.includes('/admin/dashboard'))
      dispatch(setRoute('adminDashboard'));
    else if (path.includes('/admin/login'))
      dispatch(setRoute('adminLogin'));
  }, [dispatch]);

  // RENDER STRATEGY: Switch Statement
  const renderScreen = () => {
    switch (activeRoute) {
      case 'welcome':
      case 'login':
      case 'signup':   return <AuthScreens />;
      
      case 'adminLogin':     return <AdminLogin />;
      case 'adminDashboard': return <AdminDashboard />;
      
      case 'home':     return <HomeScreen />;
      case 'chat':     return <ChatScreen />;
      case 'send':     return <SendScreen />;
      case 'fund':     return <FundScreen />;
      case 'history':  return <HistoryScreen />;
      case 'airtime':  return <AirtimeScreen />;
      case 'data':     return <DataScreen />;
      case 'bills':    return <BillsScreen />;
      case 'betting':  return <BettingScreen />;
      
      // ✅ UPDATE: Map both 'profile' AND 'menu' to the ProfileScreen
      case 'profile':  
      case 'menu':     return <ProfileScreen />;

      default:
        return <AuthScreens />;
    }
  };

  const isAdmin = ['adminLogin', 'adminDashboard'].includes(activeRoute);
  const isAuth  = ['welcome', 'login', 'signup'].includes(activeRoute);
  const isChat  = activeRoute === 'chat';

  // Auth/Admin Layout (Full Screen)
  if (isAuth || activeRoute === 'adminLogin') {
    return (
      <div className="h-[100dvh] w-full overflow-hidden font-sans">
        {renderScreen()}
      </div>
    );
  }

  return (
    <div className={`h-[100dvh] w-full flex overflow-hidden font-sans ${isAdmin ? 'bg-gray-100' : 'bg-gray-50'}`}>

      {/* 1. Desktop Sidebar (Hidden on Mobile) */}
      {!isAdmin && !isAuth && (
        <DesktopSidebar activeRoute={activeRoute} />
      )}

      {/* 2. Main Content Area */}
      <main className="flex-1 h-full flex flex-col overflow-hidden min-w-0 bg-white relative">
        
        {/* Screen Content */}
        <div className="flex-1 overflow-y-auto hide-scrollbar">
          {renderScreen()}
        </div>

        {/* 3. Mobile Navigation (Hidden on Desktop) */}
        {!isAdmin && !isAuth && !isChat && (
          <div className="md:hidden">
             {/* You can swap this with <SplitNav /> or <FloatingNav /> if you prefer */}
             <BottomNav />
          </div>
        )}

      </main>

      {/* 4. Right Panel (Desktop Home Only) */}
      {!isAdmin && !isAuth && activeRoute === 'home' && (
        <RightPanel />
      )}

      {/* 5. Global Overlays */}
      <VoiceModal />
      <SentinelModal />
      <PaymentModal />

    </div>
  );
};

export default App;