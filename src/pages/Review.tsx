import React from 'react';
import { useAuth } from '../auth/AuthContext';

export function Review() {
  const { user, logout } = useAuth();
  return (
    <main id="main" className="section">
      <div className="max" style={{ maxWidth: 720, margin: '0 auto' }}>
        <p className="eyebrow peach-eyebrow">SHIFT LEAD WORKSPACE</p>
        <h1 className="display display-md" style={{ color: 'var(--emerald-800)', marginTop: 8 }}>Review</h1>
        <p className="sub" style={{ margin: '12px auto 0' }}>
          Dashboard coming soon. This workspace is for the shift lead: approvals, exceptions and audit review.
        </p>
        {user && (
          <div className="card" style={{ padding: 20, marginTop: 24 }}>
            <strong style={{ color: 'var(--emerald-800)' }}>Access model</strong>
            <p style={{ color: 'var(--muted)', marginTop: 8, lineHeight: 1.6 }}>
              Signed in as {user.username} ({user.role}). Shift leads are the account owners for the site: they issue staff access, review access requests and approve operational changes.
            </p>
            <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={logout}>Sign out</button>
          </div>
        )}
      </div>
    </main>
  );
}