import { useNavigate } from 'react-router-dom';
import React, { useState, useMemo, useEffect } from 'react';
import credits from '../data/photo-credits.json';
import { ImageWithFallback } from '../components/ui/ImageWithFallback';

const side = credits.find((c) => c.key === 'signup')!;

type Role = 'clerk' | 'nurse' | 'lead';

const roleInfo: Record<Role, { title: string; desc: string; can: string }> = {
  clerk: { title: 'Clerk (front desk)', desc: 'Front desk and registration.', can: 'Register walk-ins, capture visit details, view queue order.' },
  nurse: { title: 'Nurse', desc: 'Triage and care coordination.', can: 'Complete triage using fixed categories, flag concerns.' },
  lead: { title: 'Shift Lead', desc: 'Review and sign off.', can: 'Approve or reject proposed appointments; every decision logged.' },
};

export function SignUp() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [role, setRole] = useState<Role | null>(null);
  const [roleError, setRoleError] = useState('');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [clinic, setClinic] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [errors, setErrors] = useState<{ name?: string; email?: string; clinic?: string; password?: string }>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const [consent1, setConsent1] = useState(false);
  const [consent2, setConsent2] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [formError, setFormError] = useState('');

  const [ticketId] = useState(() => 'REQ-' + String(Math.floor(Math.random() * 10000)).padStart(4, '0'));

  const strength = useMemo(() => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  }, [password]);

  function validateName(v: string) { return v.trim().length >= 2 ? '' : 'Enter at least 2 characters.'; }
  function validateEmail(v: string) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? '' : 'Enter a valid work email.'; }
  function validateClinic(v: string) { return v.trim().length >= 2 ? '' : 'Enter your clinic or site name.'; }
  function validatePassword(v: string) { return v.length >= 8 ? '' : 'Password must be at least 8 characters.'; }

  function blurValidate(field: string, value: string) {
    let msg = '';
    if (field === 'name') msg = validateName(value);
    if (field === 'email') msg = validateEmail(value);
    if (field === 'clinic') msg = validateClinic(value);
    if (field === 'password') msg = validatePassword(value);
    setErrors((e) => ({ ...e, [field]: msg }));
  }

  function canAdvanceStep2() {
    return (
      !validateName(name) &&
      !validateEmail(email) &&
      !validateClinic(clinic) &&
      !validatePassword(password)
    );
  }

  // TODO(back-end): wire submitAccessRequest to the access-request API.
  async function submitAccessRequest(payload: { role: Role; name: string; email: string; clinic: string; password: string; ticketId: string }) {
    void payload;
    // Simulate a short review queue handoff.
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!role || !canAdvanceStep2() || !consent1 || !consent2) return;
    setSubmitting(true);
    setFormError('');
    try {
      await submitAccessRequest({ role, name, email, clinic, password, ticketId });
      setSuccess(true);
    } catch {
      setFormError('Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  const stepAnnouncement =
    step === 1 ? 'Step 1 of 3: choose your role' :
    step === 2 ? 'Step 2 of 3: your details' :
    'Step 3 of 3: review and confirm';

  // keep a visible focus ring target for step changes (no-op except announce)
  useEffect(() => { }, [step]);

  if (success) {
    return (
      <div className="su-wrap">
        <aside className="su-side" aria-hidden="true">
          <ImageWithFallback src={side.src} alt="Soft light in a clinic hallway" width={1200} height={800} credit={{ name: side.photographer, url: side.photoPage }} />
        </aside>
        <section className="su-main">
          <div className="success-box">
            <div aria-hidden="true" style={{ fontSize: 42 }}>✓</div>
            <h2>Request received.</h2>
            <p className="sub" style={{ margin: '0 auto' }}>A shift lead will review it.</p>
            <p style={{ marginTop: 12, color: 'var(--muted)' }}>Ticket {ticketId}</p>
            <button className="btn btn-primary" style={{ marginTop: 20 }} onClick={() => navigate('/')}>Back to home</button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="su-wrap">
      <aside className="su-side">
        <h2>Access is reviewed by a shift lead before anything is enabled.</h2>
        <p>This is a synthetic-data prototype. Do not enter real patient information.</p>
        <div style={{ marginTop: 'auto', paddingTop: 28 }}>
          <ImageWithFallback src={side.src} alt="Soft light in a clinic hallway" width={1200} height={800} credit={{ name: side.photographer, url: side.photoPage }} />
        </div>
      </aside>
      <section className="su-main">
        <div className="su-progress" aria-hidden="true">
          {[1, 2, 3].map((i) => (
            <span key={i} className={step >= i ? 'done' : ''} />
          ))}
        </div>
        <div aria-live="polite" aria-atomic="true" style={{ position: 'absolute', left: -9999, width: 1, height: 1, overflow: 'hidden' }}>
          {stepAnnouncement}
        </div>

        {step === 1 && (
          <>
            <h1 className="display display-lg" style={{ color: 'var(--emerald-800)', marginBottom: 8 }}>Your role</h1>
            <p className="sub" style={{ marginBottom: 24 }}>Choose the part you play. Patient access is not offered here.</p>
            <div className="su-card-grid">
              {(Object.keys(roleInfo) as Role[]).map((r) => (
                <button
                  type="button"
                  key={r}
                  className={'role-card-big' + (role === r ? ' selected' : '')}
                  onClick={() => { setRole(r); setRoleError(''); }}
                  aria-pressed={role === r}
                >
                  <h3>{roleInfo[r].title}</h3>
                  <p>{roleInfo[r].desc}</p>
                  <p style={{ marginTop: 8, fontSize: 13 }}><strong>Can do:</strong> {roleInfo[r].can}</p>
                </button>
              ))}
            </div>
            {roleError && <p className="err" role="alert" style={{ marginTop: 12, color: '#B00020' }}>{roleError}</p>}
            {role && (
              <p style={{ marginTop: 16, color: 'var(--emerald-800)', fontWeight: 600 }}>
                Selected: {roleInfo[role].title}. {roleInfo[role].desc}
              </p>
            )}
            <div style={{ marginTop: 24 }}>
              <button
                className="btn btn-primary"
                onClick={() => {
                  if (!role) { setRoleError('Choose a role to continue.'); return; }
                  setStep(2);
                }}
              >
                Continue
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <form
            onSubmit={(e) => { e.preventDefault(); if (canAdvanceStep2()) setStep(3); }}
            style={{ display: 'grid', gap: 16, maxWidth: 520 }}
          >
            <h1 className="display display-lg" style={{ color: 'var(--emerald-800)', marginBottom: 8 }}>Your details</h1>
            <div className="field">
              <label htmlFor="su-name">Name</label>
              <input id="su-name" value={name} onChange={(e) => setName(e.target.value)} onBlur={() => { setTouched((t) => ({ ...t, name: true })); blurValidate('name', name); }} />
              {touched.name && errors.name && <span className="err">{errors.name}</span>}
              {touched.name && !errors.name && validateName(name) === '' && <span style={{ color: 'var(--emerald-700)', fontSize: 13 }}>Looks good.</span>}
            </div>
            <div className="field">
              <label htmlFor="su-email">Work email</label>
              <input id="su-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} onBlur={() => { setTouched((t) => ({ ...t, email: true })); blurValidate('email', email); }} />
              {touched.email && errors.email && <span className="err">{errors.email}</span>}
            </div>
            <div className="field">
              <label htmlFor="su-clinic">Clinic or site name</label>
              <input id="su-clinic" value={clinic} onChange={(e) => setClinic(e.target.value)} onBlur={() => { setTouched((t) => ({ ...t, clinic: true })); blurValidate('clinic', clinic); }} />
              {touched.clinic && errors.clinic && <span className="err">{errors.clinic}</span>}
            </div>
            <div className="field">
              <label htmlFor="su-password">Password</label>
              <div className="password-row">
                <input
                  id="su-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => { setTouched((t) => ({ ...t, password: true })); blurValidate('password', password); }}
                  style={{ flex: 1 }}
                />
                <button type="button" className="toggle" onClick={() => setShowPassword((s) => !s)}>
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {touched.password && errors.password && <span className="err">{errors.password}</span>}
              <div className="strength" aria-hidden="true">
                {[1,2,3,4,5].map((i) => (
                  <span key={i} className={strength >= i ? 'on' : ''} />
                ))}
              </div>
              <small style={{ color: 'var(--muted)' }}>Strength: {strength <= 1 ? 'Weak' : strength <= 3 ? 'Fair' : 'Strong'}</small>
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
              <button type="button" className="btn btn-outline" onClick={() => setStep(1)}>Back</button>
              <button type="submit" className="btn btn-primary" disabled={!canAdvanceStep2()}>Continue</button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 16, maxWidth: 520 }}>
            <h1 className="display display-lg" style={{ color: 'var(--emerald-800)', marginBottom: 8 }}>Review and confirm</h1>
            <div className="ticket">
              <div className="ticket-id">{ticketId}</div>
              <dl style={{ margin: 0 }}>
                <div className="ticket-row"><dt>Role</dt><dd>{role ? roleInfo[role].title : ''}</dd></div>
                <div className="ticket-row"><dt>Name</dt><dd>{name}</dd></div>
                <div className="ticket-row"><dt>Email</dt><dd>{email}</dd></div>
                <div className="ticket-row"><dt>Clinic</dt><dd>{clinic}</dd></div>
                <div className="ticket-row"><dt>Status</dt><dd>Awaiting review</dd></div>
              </dl>
            </div>
            <label className="checkline">
              <input type="checkbox" checked={consent1} onChange={(e) => setConsent1(e.target.checked)} />
              <span>I understand this is a synthetic-data prototype and I will not enter real patient information.</span>
            </label>
            <label className="checkline">
              <input type="checkbox" checked={consent2} onChange={(e) => setConsent2(e.target.checked)} />
              <span>I understand access is reviewed by a shift lead.</span>
            </label>
            {formError && <p role="alert" style={{ color: '#B00020' }}>{formError}</p>}
            <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
              <button type="button" className="btn btn-outline" onClick={() => setStep(2)}>Back</button>
              <button type="submit" className="btn btn-primary" disabled={!consent1 || !consent2 || submitting}>
                {submitting ? 'Submitting…' : 'Submit request'}
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}