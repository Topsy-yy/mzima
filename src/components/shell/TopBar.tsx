import React, { useEffect, useState } from 'react';
import { useAuth } from '../../auth/AuthContext';

export function TopBar({ siteLabel }: { siteLabel?: string }) {
  const { user, logout } = useAuth();
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <header className="sc-topbar">
      <div className="sc-topbar-left">
        <span className="sc-site">Shift site: {siteLabel || 'Site not specified'}</span>
        <span className="sc-time" aria-live="polite">{now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
      <div className="sc-topbar-right">
        <span className="sc-user">{user?.username ?? 'Staff'}</span>
        <button className="sc-signout" onClick={logout}>Sign out</button>
      </div>
    </header>
  );
}