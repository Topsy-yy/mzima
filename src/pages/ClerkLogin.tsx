import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { AuthLayout } from '../components/auth/AuthLayout';

export function ClerkLogin() {
  const navigate = useNavigate();
  const { loginClerk, status } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await loginClerk(identifier.trim().toUpperCase(), password);
      navigate('/visits', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in.');
    } finally {
      setSubmitting(false);
    }
  }

  if (status === 'loading') {
    return <div className="section" style={{ textAlign: 'center' }} aria-live="polite"><p className="sub" style={{ margin: '0 auto' }}>Loading…</p></div>;
  }

  return (
    <AuthLayout>
      <h1 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 6 }}>Clerk sign in</h1>
      <p className="sub" style={{ marginBottom: 24, fontSize: 15 }}>
        Use your clerk identifier (R001 to R010). Any password works for now.
      </p>
      <form onSubmit={submit} noValidate style={{ display: 'grid', gap: 16 }}>
        <div className="field">
          <label htmlFor="clerk-id">Clerk identifier</label>
          <input
            id="clerk-id"
            type="text"
            autoFocus
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="R001"
            style={{ minHeight: 48, padding: '12px 14px', border: '1px solid var(--peach-300)', borderRadius: 12, fontSize: 15, background: '#fff', color: 'var(--ink)' }}
          />
        </div>
        <div className="field">
          <label htmlFor="clerk-password">Password</label>
          <input
            id="clerk-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Any password"
            style={{ minHeight: 48, padding: '12px 14px', border: '1px solid var(--peach-300)', borderRadius: 12, fontSize: 15, background: '#fff', color: 'var(--ink)' }}
          />
        </div>
        {error && <p role="alert" style={{ color: '#B00020', fontWeight: 600, margin: 0 }}>{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={submitting} style={{ width: '100%', minHeight: 48 }}>
          {submitting ? 'Signing in…' : 'Sign in as clerk'}
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: 'var(--muted)' }}>
        Other staff? <Link to="/login" style={{ fontWeight: 700 }}>Standard sign in</Link>
      </p>
      <p className="sub" style={{ marginTop: 12, fontSize: 13 }}>
        Prototype access only. Clinicians and shift leads need backend-reviewed accounts. Patients never access this dashboard.
      </p>
    </AuthLayout>
  );
}