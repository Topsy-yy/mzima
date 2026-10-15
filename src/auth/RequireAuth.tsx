import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import type { ApiRole } from '../types';

export function RequireAuth({ children, role }: { children: React.ReactNode; role?: ApiRole }) {
  const { status, user } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return (
      <div className="section" style={{ textAlign: 'center' }} aria-live="polite">
        <p className="sub" style={{ margin: '0 auto' }}>Loading…</p>
      </div>
    );
  }

  if (status !== 'authenticated' || !user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (role && user.role !== role && user.role !== 'admin') {
    const home =
      user.role === 'clerk' ? '/visits' :
      user.role === 'nurse' ? '/triage' :
      user.role === 'shift_lead' ? '/review' :
      '/visits';
    return <Navigate to={home} replace />;
  }

  return <>{children}</>;
}