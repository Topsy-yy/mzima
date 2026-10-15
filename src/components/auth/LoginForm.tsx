import React, { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { PasswordField } from './PasswordField';
import { useAuth } from '../../auth/AuthContext';
import { AuthFailure } from '../../auth/api';

function roleHome(role: string | undefined): string {
  if (role === 'clerk') return '/visits';
  if (role === 'nurse') return '/triage';
  if (role === 'shift_lead') return '/review';
  return '/visits';
}

export function LoginForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, status } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [touched, setTouched] = useState<{ username?: boolean; password?: boolean }>({});
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showForgot, setShowForgot] = useState(false);

  const disabled = submitting || success || cooldown > 0;

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = window.setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => window.clearInterval(id);
  }, [cooldown]);

  function validateField(field: 'username' | 'password', value: string) {
    if (!value.trim()) return field === 'username' ? 'Enter your username.' : 'Enter your password.';
    return '';
  }

  function usernameBlur() {
    setTouched((t) => ({ ...t, username: true }));
    setErrors((e) => ({ ...e, username: validateField('username', username) }));
  }

  function passwordBlur() {
    setTouched((t) => ({ ...t, password: true }));
    setErrors((e) => ({ ...e, password: validateField('password', password) }));
  }

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (disabled) return;

      const uErr = validateField('username', username);
      const pErr = validateField('password', password);
      setTouched({ username: true, password: true });
      setErrors({ username: uErr, password: pErr });
      if (uErr || pErr) return;

      setSubmitting(true);
      setFormError(null);
      try {
        const user = await login(username, password);
        setSuccess(true);
        const pendingFrom = (location.state as { from?: string } | null)?.from;
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.setTimeout(() => {
          if (pendingFrom) {
            navigate(pendingFrom, { replace: true });
          } else {
            navigate(roleHome(user.role), { replace: true });
          }
        }, reduceMotion ? 150 : 700);
      } catch (err) {
        if (err instanceof AuthFailure) {
          if (err.kind === 'credentials') {
            setFormError(err.message);
            setPassword('');
            setErrors((e) => ({ ...e, password: '' }));
          } else if (err.kind === 'rateLimited') {
            setFormError(err.message);
            const seconds = err.retryAfter && err.retryAfter > 0 ? err.retryAfter : 120;
            setCooldown(seconds);
          } else {
            setFormError(err.message);
          }
        } else {
          setFormError('We can\'t reach the server right now. Please try again.');
        }
      } finally {
        setSubmitting(false);
      }
    },
    [disabled, username, password, login, location.state, navigate],
  );

  if (success) {
    return (
      <div className="success-box" role="status" aria-live="polite">
        <div aria-hidden="true" style={{ fontSize: 42, color: 'var(--emerald-700)' }}>✓</div>
        <h2>Signed in</h2>
        <p className="sub" style={{ margin: '8px auto 0' }}>Taking you to your workspace.</p>
      </div>
    );
  }

  return (
    <>
      <h1 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 6 }}>
        Welcome back to the queue
      </h1>
      <p className="sub" style={{ marginBottom: 24, fontSize: 15 }}>
        Sign in to continue. Use the account your shift lead gave you.
      </p>

      <div aria-live="polite" aria-atomic="true" style={{ minHeight: 24, marginBottom: 12 }}>
        {formError && (
          <p
            className="err"
            role={formError ? 'alert' : undefined}
            style={{ color: '#B00020', fontSize: 14, fontWeight: 600, margin: 0 }}
          >
            {formError}
          </p>
        )}
        {cooldown > 0 && (
          <p style={{ color: 'var(--emerald-800)', fontSize: 13, margin: 0 }}>
            You can try again in {cooldown}s.
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} noValidate style={{ display: 'grid', gap: 16 }}>
        <div className="field">
          <label htmlFor="login-username">Username</label>
          <input
            id="login-username"
            type="text"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onBlur={usernameBlur}
            aria-invalid={touched.username && !!errors.username ? true : undefined}
            aria-describedby={touched.username && errors.username ? 'login-username-error' : undefined}
            disabled={disabled}
            style={{
              minHeight: 48,
              padding: '12px 14px',
              border: '1px solid var(--peach-300)',
              borderRadius: 12,
              fontSize: 15,
              background: '#fff',
              color: 'var(--ink)',
            }}
          />
          {touched.username && errors.username && (
            <span className="err" id="login-username-error">{errors.username}</span>
          )}
        </div>

        <PasswordField
          id="login-password"
          label="Password"
          value={password}
          onChange={setPassword}
          onBlur={passwordBlur}
          touched={touched.password}
          error={errors.password}
          describedBy={touched.password && errors.password ? 'login-password-error' : undefined}
          disabled={disabled}
        />

        {/* "Remember this device" removed until the backend supports it. TODO: revisit. */}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={disabled}
          style={{ width: '100%', minHeight: 48 }}
        >
          {submitting ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Signing in…
            </>
          ) : cooldown > 0 ? (
            'Wait…'
          ) : (
            'Sign in'
          )}
        </button>

        <p style={{ textAlign: 'center', margin: 0, fontSize: 14 }}>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setShowForgot((s) => !s)}
            disabled={disabled}
            style={{ minHeight: 36 }}
          >
            Forgot password?
          </button>
        </p>
        {showForgot && (
          <p className="sub" style={{ textAlign: 'center', fontSize: 13, margin: 0 }} role="status">
            Ask your shift lead to reset your access.
          </p>
        )}
      </form>

      <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: 'var(--muted)' }}>
        Need access?{' '}
        <Link to="/sign-up" style={{ fontWeight: 700 }}>
          Request it here
        </Link>
      </p>
      <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--muted)', margin: 0 }}>
        Access is issued on site by a shift lead and reviewed before activation.
      </p>
    </>
  );
}