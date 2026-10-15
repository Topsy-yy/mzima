import React from 'react';
import { useAuth } from '../auth/AuthContext';

export function Visits() {
  const { user, logout } = useAuth();
  return (
    <main id="main" className="section">
      <div className="max" style={{ maxWidth: 720, margin: '0 auto' }}>
        <p className="eyebrow peach-eyebrow">CLERK WORKSPACE</p>
        <h1 className="display display-md" style={{ color: 'var(--emerald-800)', marginTop: 8 }}>Visits</h1>
        <p className="sub" style={{ margin: '12px auto 0' }}>
          Dashboard coming soon. This workspace is for the clerk role: walk-in registration, visit capture and queue position updates.
        </p>
        {user && (
          <div className="card" style={{ padding: 20, marginTop: 24 }}>
            <strong style={{ color: 'var(--emerald-800)' }}>Access model</strong>
            <p style={{ color: 'var(--muted)', marginTop: 8, lineHeight: 1.6 }}>
              Signed in as {user.username} ({user.role}). Accounts are issued by a shift lead; administrative changes are reviewed before they take effect.
            </p>
            <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={logout}>Sign out</button>
          </div>
        )}
      </div>
    </main>
  );
}