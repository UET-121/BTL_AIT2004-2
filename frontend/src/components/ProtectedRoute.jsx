import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const token = localStorage.getItem('access_token');
  const userRole = localStorage.getItem('user_role');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // If role is required but user has no role stored, treat as viewer (least privilege)
  const effectiveRole = userRole || 'viewer';

  if (allowedRoles && !allowedRoles.includes(effectiveRole)) {
    // If user doesn't have the required role, redirect to dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default ProtectedRoute;
