import { useNavigate } from 'react-router-dom';
import React from 'react';

export function NotFound() {
  const navigate = useNavigate();
  return (
    <main id="main" className="section">
      <div className="max" style={{ textAlign: 'center', maxWidth: 640 }}>
        <h1 className="display display-xl" style={{ color: 'var(--emerald-800)' }}>404</h1>
        <p className="sub" style={{ margin: '12px auto 24px' }}>This page does not exist.</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>Back to home</button>
      </div>
    </main>
  );
}