import { Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from './components/PrivateRoute';

// Public — Auth
import Onboarding from './pages/Onboarding';
import Signup from './pages/Signup';
import OTPVerify from './pages/OTPVerify';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';

// Protected — Dashboard
import Dashboard from './pages/Dashboard';
import TransactionHistory from './pages/TransactionHistory';
import Transfer from './pages/Transfer';
import Cards from './pages/Cards';
import Services from './pages/Services';
import Profile from './pages/Profile';
import Notifications from './pages/Notifications';
import Settings from './pages/Settings';

import './App.css';

function App() {
  return (
    <Routes>
      {/* ── Public ── */}
      <Route path="/onboarding"      element={<Onboarding />} />
      <Route path="/signup"          element={<Signup />} />
      <Route path="/verify-otp"      element={<OTPVerify />} />
      <Route path="/login"           element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* ── Protected ── */}
      <Route path="/dashboard"    element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/history"      element={<PrivateRoute><TransactionHistory /></PrivateRoute>} />
      <Route path="/transfer"     element={<PrivateRoute><Transfer /></PrivateRoute>} />
      <Route path="/cards"        element={<PrivateRoute><Cards /></PrivateRoute>} />
      <Route path="/services"     element={<PrivateRoute><Services /></PrivateRoute>} />
      <Route path="/profile"      element={<PrivateRoute><Profile /></PrivateRoute>} />
      <Route path="/notifications" element={<PrivateRoute><Notifications /></PrivateRoute>} />
      <Route path="/settings"     element={<PrivateRoute><Settings /></PrivateRoute>} />

      {/* Default */}
      <Route path="/" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;

