import React from 'react';
import { useNavigate } from 'react-router-dom';

export function Footer() {
  const navigate = useNavigate();
  return (
    <footer className="footer" role="contentinfo">
      <div className="max footer-grid">
        <div>
          <div className="wordmark" style={{ color: '#fff' }}>
            <span className="wordmark-dot">m</span>
            Mzima
          </div>
          <small style={{ marginTop: 8 }}>
            Synthetic-data prototype. Not for live care. Not diagnostic. Every appointment decision requires human sign-off.
          </small>
        </div>
        <div>
          <strong style={{ display: 'block', marginBottom: 8, color: '#fff' }}>Pages</strong>
          <button onClick={() => navigate('/')} style={{ display: 'block', margin: '4px 0', border: 0, background: 'transparent', padding: 0, cursor: 'pointer', color: 'rgba(255,255,255,.8)' }}>Home</button>
          <button onClick={() => navigate('/how-it-works')} style={{ display: 'block', margin: '4px 0', border: 0, background: 'transparent', padding: 0, cursor: 'pointer', color: 'rgba(255,255,255,.8)' }}>How it works</button>
          <button onClick={() => navigate('/story')} style={{ display: 'block', margin: '4px 0', border: 0, background: 'transparent', padding: 0, cursor: 'pointer', color: 'rgba(255,255,255,.8)' }}>Story</button>
        </div>
        <div>
          <strong style={{ display: 'block', marginBottom: 8, color: '#fff' }}>Access</strong>
          <button onClick={() => navigate('/sign-up')} style={{ display: 'block', margin: '4px 0', border: 0, background: 'transparent', padding: 0, cursor: 'pointer', color: 'rgba(255,255,255,.8)' }}>Request access</button>
          <small>Reviewed by a shift lead before anything is enabled.</small>
          <small style={{ marginTop: 12, display: 'block' }}>Photos via Unsplash contributors.</small>
        </div>
      </div>
      <div className="max footer-bottom">
        © {new Date().getFullYear()} Mzima · Synthetic data only · Not for live care.
      </div>
    </footer>
  );
}