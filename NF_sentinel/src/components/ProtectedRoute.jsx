import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';


const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const isAdminRoute = location.pathname.toLowerCase().startsWith('/admin');

  const token = isAdminRoute
    ? localStorage.getItem('sentinel_admin_token')
    : localStorage.getItem('sentinel_token');

  if (!token) {
    return <Navigate to={isAdminRoute ? '/admin/login' : '/'} replace />;
  }

  return children;
};

export default ProtectedRoute;
