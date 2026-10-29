import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import {
  ApiUser,
  AppointmentRequest,
  callVisit,
  checkInVisit,
  completeVisitTriage,
  createAppointmentRequest,
  decideAppointmentRequest,
  getAppointmentQueue,
  getCurrentUser,
  getWalkInQueue,
  login,
  QueueVisit,
  Visit,
} from './api';

type Page = 'home' | 'patient' | 'staff' | 'clinician' | 'signin';

const pageTitles: Record<Page, string> = {
  home: 'Welcome to Mzima',
  patient: 'Appointment request',
  staff: 'Front desk',
  clinician: 'Review inbox',
  signin: 'Staff sign in',
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('en-KE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function App() {
  const [page, setPage] = useState<Page>('home');
  const [token, setToken] = useState(() => sessionStorage.getItem('mzima_access_token') ?? '');
  const [user, setUser] = useState<ApiUser | null>(null);
  const [authLoading, setAuthLoading] = useState(Boolean(token));
  const [authError, setAuthError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    if (!token) {
      setAuthLoading(false);
      return;
    }
    getCurrentUser(token)
      .then(setUser)
      .catch((sessionError: unknown) => {
        sessionStorage.removeItem('mzima_access_token');
        setToken('');
        setUser(null);
        setAuthError(
          sessionError instanceof Error
            ? `Your staff session could not be verified: ${sessionError.message}`
            : 'Your staff session could not be verified. Please sign in again.',
        );
      })
      .finally(() => setAuthLoading(false));
  }, [token]);

  const signOut = () => {
    sessionStorage.removeItem('mzima_access_token');
    setToken('');
    setUser(null);
    setNotice('You have signed out.');
    setPage('home');
  };

  const handleSignedIn = (accessToken: string, currentUser: ApiUser) => {
    sessionStorage.setItem('mzima_access_token', accessToken);
    setToken(accessToken);
    setUser(currentUser);
    setAuthError('');
    setPage(
      currentUser.role === 'shift_lead' || currentUser.role === 'admin'
        ? 'clinician'
        : 'staff',
    );
    setNotice(`Signed in as ${currentUser.username} (${currentUser.role.replace('_', ' ')}).`);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage('home'); }}>
          <img className="brand-mark" src="/mzima-logo.svg" alt="" />
          <span>
            <strong>mzima</strong>
            <small>care access</small>
          </span>
        </a>

        <div className="nav-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          <button className={page === 'home' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('home')}>
            <span className="nav-icon">⌂</span> Home
          </button>
          <button className={page === 'patient' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('patient')}>
            <span className="nav-icon">＋</span> Appointment request
          </button>
          <button className={page === 'staff' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('staff')}>
            <span className="nav-icon">▤</span> Front desk
          </button>
          <button className={page === 'clinician' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('clinician')}>
            <span className="nav-icon">◷</span> Clinician inbox
          </button>
        </nav>

        <div className="sidebar-spacer" />
        <div className="sidebar-safety">
          <span className="safety-dot" />
          <div><strong>Prototype workspace</strong><small>Synthetic data only</small></div>
        </div>
        {user ? (
          <div className="account-area">
            <div className="avatar">{user.username.slice(0, 1).toUpperCase()}</div>
            <div className="account-copy">
              <strong>{user.username}</strong>
              <small>{user.role.replace('_', ' ')}</small>
            </div>
            <button className="icon-button" title="Sign out" onClick={signOut}>↗</button>
          </div>
        ) : (
          <button className="signin-link" onClick={() => setPage('signin')}>Staff sign in <span>→</span></button>
        )}
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="breadcrumb">MZIMA <span>/</span> {pageTitles[page].toUpperCase()}</div>
            <h1>{pageTitles[page]}</h1>
          </div>
          <div className="topbar-right">
            <span className="local-indicator"><span /> Local prototype</span>
            <button
              className="avatar top-avatar"
              title={user?.username ?? 'Staff account'}
              onClick={() => {
                if (!user) setPage('signin');
                else setPage(user.role === 'shift_lead' || user.role === 'admin' ? 'clinician' : 'staff');
              }}
            >
              {user ? user.username.slice(0, 1).toUpperCase() : '·'}
            </button>
          </div>
        </header>

        {notice && <div className="notice success-notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Dismiss">×</button></div>}
        {authError && <div className="notice error-notice" role="alert">{authError}<button onClick={() => setAuthError('')} aria-label="Dismiss">×</button></div>}

        {page === 'home' && <LandingPage onStartRequest={() => setPage('patient')} onStaffSignIn={() => setPage('signin')} />}
        {page === 'patient' && <PatientPage onNotice={setNotice} />}
        {page === 'staff' && (
          <StaffPage token={token} user={user} authLoading={authLoading} onSignIn={() => setPage('signin')} onNotice={setNotice} />
        )}
        {page === 'clinician' && (
          <ClinicianPage
            token={token}
            user={user}
            authLoading={authLoading}
            onSignIn={() => setPage('signin')}
            onGoToFrontDesk={() => setPage('staff')}
            onNotice={setNotice}
          />
        )}
        {page === 'signin' && <SignInPage onSignedIn={handleSignedIn} onError={setAuthError} />}
      </main>
    </div>
  );
}

function LandingPage({
  onStartRequest,
  onStaffSignIn,
}: {
  onStartRequest: () => void;
  onStaffSignIn: () => void;
}) {
  return (
    <div className="content-wrap landing-page">
      <section className="landing-hero">
        <div className="landing-copy">
          <div className="landing-kicker"><span /> CARE ACCESS, MADE SIMPLER</div>
          <h2>A clearer first step <span>to care.</span></h2>
          <p>Tell the clinic what kind of appointment you need. Your request goes to the clinic team for review.</p>
          <div className="landing-actions">
            <button className="primary-button landing-primary" onClick={onStartRequest}>Start an appointment request <span>→</span></button>
            <button className="landing-secondary" onClick={onStaffSignIn}>Clinic staff sign in</button>
          </div>
          <div className="landing-assurance"><span aria-hidden="true">✓</span> A clinic staff member reviews your request.</div>
        </div>
        <div className="landing-visual" aria-hidden="true">
          <div className="landing-orbit orbit-one" />
          <div className="landing-orbit orbit-two" />
          <div className="landing-logo-card"><img src="/mzima-logo.svg" alt="" /><span>Care starts<br />with a conversation.</span></div>
          <div className="landing-note note-top"><span className="note-icon">✳</span><span><strong>Simple to start</strong><small>Just a few details</small></span></div>
          <div className="landing-note note-bottom"><span className="note-check">✓</span><span><strong>Reviewed by people</strong><small>Your clinic team is in charge</small></span></div>
        </div>
      </section>

      <section className="landing-details" aria-label="How Mzima works">
        <div className="landing-section-heading">
          <div><span className="eyebrow">HOW IT WORKS</span><h3>A simple path to your next step.</h3></div>
          <p>No diagnosis or automatic booking—just a clear way to send a request to your clinic.</p>
        </div>
        <div className="landing-steps">
          <article className="landing-step">
            <span className="landing-step-number">01</span>
            <span className="landing-step-icon" aria-hidden="true">↗</span>
            <h4>Tell us what you need</h4>
            <p>Choose the service you want to request and enter a demo reference.</p>
          </article>
          <article className="landing-step">
            <span className="landing-step-number">02</span>
            <span className="landing-step-icon" aria-hidden="true">◎</span>
            <h4>Review before sending</h4>
            <p>Check your details and confirm that you want to send the request.</p>
          </article>
          <article className="landing-step">
            <span className="landing-step-number">03</span>
            <span className="landing-step-icon" aria-hidden="true">♡</span>
            <h4>The clinic follows up</h4>
            <p>Clinic staff review the request and share any next steps with you.</p>
          </article>
        </div>
      </section>

      <div className="landing-safety">
        <span aria-hidden="true">i</span>
        <p><strong>For this prototype, use demo details only.</strong> Mzima does not diagnose or provide emergency help. A request is not an appointment confirmation.</p>
      </div>
    </div>
  );
}

function PatientPage({ onNotice }: { onNotice: (message: string) => void }) {
  const [patientIdentifier, setPatientIdentifier] = useState('');
  const [specialty, setSpecialty] = useState('General outpatient');
  const [submitted, setSubmitted] = useState<AppointmentRequest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'service' | 'reference' | 'review' | 'submitted'>('service');
  const [messages, setMessages] = useState<Array<{ id: number; sender: 'assistant' | 'user'; text: string }>>([
    {
      id: 0,
      sender: 'assistant',
      text: 'Hello! I can help you send an appointment request to the clinic team.',
    },
    {
      id: 1,
      sender: 'assistant',
      text: 'Which service would you like to request?',
    },
  ]);

  function addMessage(sender: 'assistant' | 'user', text: string) {
    setMessages((current) => [...current, { id: current.length, sender, text }]);
  }

  function chooseService(service: string) {
    setSpecialty(service);
    addMessage('user', service);
    addMessage(
      'assistant',
      'Thanks. Enter a synthetic patient reference so the clinic can identify this demo request.',
    );
    setStep('reference');
    setError('');
  }

  function handleReferenceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const reference = patientIdentifier.trim();
    if (!reference) return;

    setError('');
    setPatientIdentifier(reference);
    addMessage('user', reference);
    addMessage(
      'assistant',
      `Here is your request: ${specialty}. Would you like me to send it to the clinic team?`,
    );
    setStep('review');
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const request = await createAppointmentRequest(patientIdentifier.trim(), specialty);
      setSubmitted(request);
      setStep('submitted');
      addMessage('assistant', 'Your request has been received by the clinic team.');
      onNotice('Your appointment request was saved.');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not submit your request.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="content-wrap">
      <div className="patient-columns">
        <section className="panel chat-panel" aria-label="Appointment request assistant">
          <div className="chat-header">
            <div className="chat-assistant">
              <img className="chat-avatar" src="/mzima-logo.svg" alt="" />
              <div>
                <strong>Mzima assistant</strong>
                <span><i /> Here to help with your request</span>
              </div>
            </div>
            <span className="chat-secure"><span aria-hidden="true">◇</span> Demo mode</span>
          </div>

          <div className="chat-context">
            <span className="chat-context-icon" aria-hidden="true">✳</span>
            <div>
              <strong>A simple appointment request</strong>
              <p>I’ll ask for a service and a demo reference. A clinic staff member reviews every request.</p>
            </div>
          </div>

          <div className="chat-transcript" aria-live="polite" aria-relevant="additions">
            {messages.map((message) => (
              <div className={`chat-message ${message.sender}`} key={message.id}>
                {message.sender === 'assistant' && <img className="message-avatar" src="/mzima-logo.svg" alt="" />}
                <p><span className="visually-hidden">{message.sender === 'assistant' ? 'Mzima assistant: ' : 'You: '}</span>{message.text}</p>
              </div>
            ))}

            {step === 'service' && (
              <div className="chat-options" aria-label="Choose a service">
                {['General outpatient', 'Maternal and child health', 'Chronic care review', 'Follow-up appointment'].map((service) => (
                  <button className="chat-option" key={service} onClick={() => chooseService(service)}>{service}<span>↗</span></button>
                ))}
              </div>
            )}

            {step === 'review' && (
              <div className="chat-review">
                <div><span>REQUESTED SERVICE</span><strong>{specialty}</strong></div>
                <div><span>DEMO REFERENCE</span><strong>{patientIdentifier}</strong></div>
                {error && <p className="inline-error" role="alert">{error}</p>}
                <form onSubmit={handleSubmit}>
                  <button className="primary-button" disabled={loading}>{loading ? 'Sending request…' : 'Send to clinic team'} <span>→</span></button>
                  <button type="button" className="chat-edit-button" onClick={() => { setError(''); setStep('reference'); addMessage('assistant', 'No problem. Enter your synthetic patient reference again.'); }}>Edit reference</button>
                  <button type="button" className="chat-edit-button" onClick={() => { setStep('service'); addMessage('assistant', 'Choose a different service for your request.'); }}>Change service</button>
                </form>
              </div>
            )}

            {submitted && (
              <div className="chat-receipt" role="status">
                <div className="receipt-heading"><span>✓</span><div><strong>Request received</strong><small>Clinic staff will review it. This is not a confirmed appointment.</small></div></div>
                <dl className="request-summary">
                  <div><dt>Reference</dt><dd>{submitted.id}</dd></div>
                  <div><dt>Requested service</dt><dd>{submitted.requested_specialty}</dd></div>
                  <div><dt>Status</dt><dd><span className="status-chip pending">{submitted.status.replace(/_/g, ' ')}</span></dd></div>
                  <div><dt>Submitted</dt><dd>{formatDate(submitted.created_at)}</dd></div>
                </dl>
                <button className="secondary-button" onClick={() => {
                  setSubmitted(null);
                  setPatientIdentifier('');
                  setSpecialty('General outpatient');
                  setMessages([
                    { id: 0, sender: 'assistant', text: 'Hello! I can help you send an appointment request to the clinic team.' },
                    { id: 1, sender: 'assistant', text: 'Which service would you like to request?' },
                  ]);
                  setStep('service');
                }}>Start another request</button>
              </div>
            )}
          </div>

          {step === 'reference' ? (
            <form className="chat-composer" onSubmit={handleReferenceSubmit}>
              <label className="visually-hidden" htmlFor="chat-reference">Synthetic patient reference</label>
              <input
                id="chat-reference"
                value={patientIdentifier}
                onChange={(event) => setPatientIdentifier(event.target.value)}
                placeholder="Type a demo reference, e.g. DEMO-024"
                required
                maxLength={100}
                autoComplete="off"
              />
              <button className="chat-send" type="submit" aria-label="Continue" disabled={!patientIdentifier.trim()}>→</button>
              <small>Demo reference only — never enter real health details.</small>
            </form>
          ) : (
            <div className="chat-composer chat-composer-disabled">
              <span>{step === 'submitted' ? 'Your request has been sent.' : step === 'review' ? 'Review your request above' : 'Choose a service above to get started'}</span>
              <button className="chat-send" type="button" disabled aria-label="Continue">→</button>
            </div>
          )}
        </section>

        <aside className="panel next-steps-panel">
          <div className="eyebrow">WHAT HAPPENS NEXT</div>
          <h2>One step at a time.</h2>
          <div className="steps-list">
            <div className="step-item"><div className={`step-number ${submitted ? 'complete' : 'current'}`}>{submitted ? '✓' : '1'}</div><div><strong>Share request details</strong><p>Choose a service and enter a synthetic demo reference.</p></div></div>
            <div className="step-item"><div className={`step-number ${submitted ? 'current' : ''}`}>2</div><div><strong>Clinic team reviews</strong><p>A staff member checks your request and follows up if needed.</p></div></div>
            <div className="step-item"><div className="step-number">3</div><div><strong>Next steps from the clinic</strong><p>The clinic will share appointment details if a booking is arranged.</p></div></div>
          </div>
          <div className="safety-callout"><strong>Need help sooner?</strong><p>This prototype does not assess symptoms or provide emergency advice. Contact your facility directly for urgent help.</p></div>
        </aside>
      </div>
    </div>
  );
}

function SignInPage({
  onSignedIn,
  onError,
}: {
  onSignedIn: (token: string, user: ApiUser) => void;
  onError: (message: string) => void;
}) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    onError('');
    try {
      const accessToken = await login(username, password);
      const currentUser = await getCurrentUser(accessToken);
      onSignedIn(accessToken, currentUser);
    } catch (loginError) {
      const message = loginError instanceof Error ? loginError.message : 'Unable to sign in.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="signin-page">
      <section className="panel signin-card">
        <div className="signin-icon">↗</div>
        <div className="eyebrow">STAFF ACCESS</div>
        <h2>Welcome back.</h2>
        <p>Sign in with your clinic account to access the review inbox or front desk tools.</p>
        <form className="stack-form" onSubmit={handleSubmit}>
          <label>Username<input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
          <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
          {error && <p className="inline-error" role="alert">{error}</p>}
          <button className="primary-button" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'} <span>→</span></button>
        </form>
        <div className="signin-footnote">Access is verified by the Mzima API. Roles control which actions are available.</div>
      </section>
    </div>
  );
}

function StaffPage({
  token,
  user,
  authLoading,
  onSignIn,
  onNotice,
}: {
  token: string;
  user: ApiUser | null;
  authLoading: boolean;
  onSignIn: () => void;
  onNotice: (message: string) => void;
}) {
  const [queue, setQueue] = useState<QueueVisit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [ageBand, setAgeBand] = useState('adult');
  const [visitType, setVisitType] = useState('new');
  const [checkingIn, setCheckingIn] = useState(false);
  const [activeVisit, setActiveVisit] = useState<Visit | null>(null);
  const [triageCategory, setTriageCategory] = useState('');
  const [destination, setDestination] = useState('');
  const [actionError, setActionError] = useState('');
  const [actionBusy, setActionBusy] = useState(false);

  useEffect(() => {
    if (!token || !user) return;
    setLoading(true);
    setError('');
    getWalkInQueue(token)
      .then(setQueue)
      .catch((queueError) => setError(queueError instanceof Error ? queueError.message : 'Could not load queue.'))
      .finally(() => setLoading(false));
  }, [token, user, refreshKey]);

  async function handleCheckIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setCheckingIn(true);
    setActionError('');
    try {
      const visit = await checkInVisit({ age_band: ageBand, visit_type: visitType, red_flags: {} }, token);
      onNotice(`Walk-in checked in. Token ${visit.token_number}.`);
      setRefreshKey((value) => value + 1);
    } catch (checkInError) {
      setActionError(checkInError instanceof Error ? checkInError.message : 'Could not check in visit.');
    } finally {
      setCheckingIn(false);
    }
  }

  async function handleCall(visitId: string) {
    if (!token) return;
    setActionBusy(true);
    setActionError('');
    try {
      const calledVisit = await callVisit(visitId, '', token);
      setActiveVisit(calledVisit);
      onNotice(`Token ${calledVisit.token_number} called.`);
      setRefreshKey((value) => value + 1);
    } catch (callError) {
      setActionError(callError instanceof Error ? callError.message : 'Could not call this visit.');
    } finally {
      setActionBusy(false);
    }
  }

  async function handleTriage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !activeVisit) return;
    setActionBusy(true);
    setActionError('');
    try {
      const result = await completeVisitTriage(activeVisit.id, triageCategory, destination, token);
      setActiveVisit(result);
      onNotice(`Triage record saved for ${result.token_number}.`);
      setRefreshKey((value) => value + 1);
    } catch (triageError) {
      setActionError(triageError instanceof Error ? triageError.message : 'Could not save triage record.');
    } finally {
      setActionBusy(false);
    }
  }

  if (authLoading) return <LoadingPanel label="Checking staff session…" />;
  if (!token || !user) return <SignInPrompt onSignIn={onSignIn} message="Sign in to view the walk-in queue and front desk actions." />;

  const canCheckIn = user.role === 'clerk' || user.role === 'admin';
  const canCall = user.role === 'nurse' || user.role === 'shift_lead' || user.role === 'admin';
  const averageWait = queue.length ? Math.round(queue.reduce((sum, visit) => sum + visit.minutes_waiting, 0) / queue.length) : 0;

  return (
    <div className="content-wrap">
      <div className="page-intro-row">
        <div><p className="page-intro">A clear view of today's walk-in flow.</p><p className="last-updated">Queue data is live from the Mzima API.</p></div>
        <button className="secondary-button" onClick={() => setRefreshKey((value) => value + 1)} disabled={loading}>↻ Refresh queue</button>
      </div>
      {error && <div className="notice error-notice" role="alert">{error}</div>}
      {actionError && <div className="notice error-notice" role="alert">{actionError}</div>}
      <div className="metric-grid">
        <MetricCard label="Waiting" value={loading ? '—' : String(queue.length)} detail="Visits currently in queue" icon="◷" tone="blue" />
        <MetricCard label="Fast-track" value={String(queue.filter((visit) => visit.is_fast_track).length)} detail="As recorded by the backend" icon="!" tone="amber" />
        <MetricCard label="Average wait" value={`${averageWait} min`} detail="Across visible queue entries" icon="⌁" tone="green" />
      </div>

      <div className="staff-grid">
        <section className="panel table-panel">
          <div className="panel-heading"><div><div className="eyebrow">LIVE QUEUE</div><h2>Walk-in visits</h2></div><span className="subtle-count">{queue.length} records</span></div>
          {loading ? <LoadingPanel label="Loading queue…" /> : queue.length ? (
            <div className="table-scroll">
              <table>
                <thead><tr><th>Token</th><th>Arrival</th><th>Wait</th><th>Queue score</th><th>Status</th><th /></tr></thead>
                <tbody>
                  {queue.map((visit) => (
                    <tr key={visit.visit_id}>
                      <td><strong>{visit.token_number}</strong><small>{visit.visit_id.slice(0, 8)}</small></td>
                      <td>{formatDate(visit.arrival_time)}</td>
                      <td>{visit.minutes_waiting} min</td>
                      <td>{visit.calculated_score.toFixed(1)}</td>
                      <td><span className={`status-chip ${visit.is_fast_track ? 'attention' : 'pending'}`}>{visit.is_fast_track ? 'Fast-track' : 'Waiting'}</span></td>
                      <td>{canCall && <button className="small-button" onClick={() => handleCall(visit.visit_id)} disabled={actionBusy}>Call</button>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <EmptyState title="No visits in queue" description="When a synthetic walk-in is checked in, it will appear here." />}
          <p className="table-footnote">Queue score and fast-track state are supplied by the backend. Use the clinic’s approved protocol; this prototype is not for live care.</p>
        </section>

        <aside className="staff-side">
          {canCheckIn && (
            <section className="panel compact-panel">
              <div className="eyebrow">FRONT DESK</div><h2>Check in a walk-in</h2>
              <form className="stack-form" onSubmit={handleCheckIn}>
                <label>Age band<select value={ageBand} onChange={(event) => setAgeBand(event.target.value)}><option value="under_5">Under 5</option><option value="adult">Adult</option><option value="over_65">Over 65</option></select></label>
                <label>Visit type<select value={visitType} onChange={(event) => setVisitType(event.target.value)}><option value="new">New</option><option value="review">Review</option><option value="refill">Refill</option></select></label>
                <button className="primary-button" disabled={checkingIn}>{checkingIn ? 'Checking in…' : 'Create walk-in record'} <span>→</span></button>
              </form>
              <p className="form-footnote">No red flags are inferred or submitted by this form.</p>
            </section>
          )}
          {activeVisit && canCall && (
            <section className="panel compact-panel">
              <div className="eyebrow">CALLED TOKEN</div><h2>{activeVisit.token_number}</h2>
              <p className="muted-copy">Record staff-entered triage outcome when ready.</p>
              <form className="stack-form" onSubmit={handleTriage}>
                <label>Triage category<input value={triageCategory} onChange={(event) => setTriageCategory(event.target.value)} required placeholder="Enter the clinic-recorded category" /></label>
                <label>Destination<input value={destination} onChange={(event) => setDestination(event.target.value)} required placeholder="Enter the clinic destination" /></label>
                <button className="secondary-button" disabled={actionBusy}>Save staff record</button>
              </form>
            </section>
          )}
          <div className="safety-callout"><strong>Human-owned decisions</strong><p>Actions are sent to the API and audited with the signed-in staff account.</p></div>
        </aside>
      </div>
    </div>
  );
}

function ClinicianPage({
  token,
  user,
  authLoading,
  onSignIn,
  onGoToFrontDesk,
  onNotice,
}: {
  token: string;
  user: ApiUser | null;
  authLoading: boolean;
  onSignIn: () => void;
  onGoToFrontDesk: () => void;
  onNotice: (message: string) => void;
}) {
  const [requests, setRequests] = useState<AppointmentRequest[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [decision, setDecision] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  const selectedRequest = useMemo(
    () => requests.find((request) => request.id === selectedId) ?? requests[0],
    [requests, selectedId],
  );
  const selectedProposal = selectedRequest?.agent_proposal;

  const refresh = useCallback(() => {
    if (!token || !user) return;
    setLoading(true);
    setError('');
    getAppointmentQueue(token)
      .then((items) => {
        setRequests(items);
        setSelectedId((current) => items.some((item) => item.id === current) ? current : items[0]?.id ?? '');
      })
      .catch((queueError) => setError(queueError instanceof Error ? queueError.message : 'Could not load review inbox.'))
      .finally(() => setLoading(false));
  }, [token, user]);

  useEffect(() => {
    refresh();
  }, [refresh, refreshKey]);

  useEffect(() => {
    setDecision(selectedRequest?.proposed_slot_id ? 'APPROVE' : 'REJECT');
  }, [selectedRequest?.id, selectedRequest?.proposed_slot_id]);

  async function handleDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedRequest) return;
    setSaving(true);
    setError('');
    try {
      const saved = await decideAppointmentRequest(selectedRequest.id, decision, reason.trim(), token);
      setRequests((current) => current.filter((request) => request.id !== selectedRequest.id));
      setReason('');
      onNotice(`${saved.decision} decision recorded for request ${selectedRequest.id}.`);
    } catch (decisionError) {
      setError(decisionError instanceof Error ? decisionError.message : 'Could not submit clinician decision.');
    } finally {
      setSaving(false);
    }
  }

  if (authLoading) return <LoadingPanel label="Checking staff session…" />;
  if (!token || !user) return <SignInPrompt onSignIn={onSignIn} message="Sign in as a shift lead or administrator to review appointment requests." />;
  if (user.role !== 'shift_lead' && user.role !== 'admin') {
    return <RoleDenied onGoToFrontDesk={onGoToFrontDesk} />;
  }

  return (
    <div className="content-wrap">
      <div className="page-intro-row">
        <div><p className="page-intro">Review the synthetic slot proposal and record a named staff decision.</p><p className="last-updated">The proposal is deterministic and does not infer diagnosis or clinical priority.</p></div>
        <button className="secondary-button" onClick={() => setRefreshKey((value) => value + 1)} disabled={loading}>↻ Refresh inbox</button>
      </div>
      {error && <div className="notice error-notice" role="alert">{error}</div>}
      <div className="clinician-layout">
        <section className="panel inbox-panel">
          <div className="panel-heading"><div><div className="eyebrow">PENDING REQUESTS</div><h2>Review inbox</h2></div><span className="count-bubble">{requests.length}</span></div>
          {loading ? <LoadingPanel label="Loading review inbox…" /> : requests.length ? (
            <div className="inbox-list">
              {requests.map((request) => (
                <button key={request.id} className={`inbox-item ${request.id === selectedRequest?.id ? 'selected' : ''}`} onClick={() => setSelectedId(request.id)}>
                  <span className="inbox-icon">↗</span>
                  <span className="inbox-item-copy"><strong>{request.requested_specialty}</strong><small>{request.patient_identifier}</small><small>{formatDate(request.created_at)}</small></span>
                  <span className="item-chevron">›</span>
                </button>
              ))}
            </div>
          ) : <EmptyState title="Inbox is clear" description="No pending appointment requests were returned by the API." />}
        </section>

        <section className="panel review-panel">
          {selectedRequest ? (
            <>
              <div className="review-topline"><span className="status-chip pending">{selectedRequest.status.replace(/_/g, ' ')}</span><span className="request-id">REF {selectedRequest.id}</span></div>
              <h2>Request review</h2>
              <p className="review-intro">Check the request details, then record the clinic's decision.</p>
              <div className="review-facts">
                <div><span>Patient reference</span><strong>{selectedRequest.patient_identifier}</strong></div>
                <div><span>Requested service</span><strong>{selectedRequest.requested_specialty}</strong></div>
                <div><span>Submitted</span><strong>{formatDate(selectedRequest.created_at)}</strong></div>
              </div>
              <div className="capability-note">
                <strong>{selectedRequest.proposed_slot_id ? 'Synthetic slot proposal' : 'No matching slot'}</strong>
                <p>{selectedProposal?.status === 'NO_MATCH'
                  ? 'No configured slot matches this requested service. Do not approve this request as a booking.'
                  : selectedProposal?.starts_at
                    ? `Earliest available matching slot: ${formatDate(selectedProposal.starts_at)}.`
                    : 'A matching slot was not available when this request was submitted.'}</p>
                {(selectedProposal?.evidence ?? []).length > 0 && (
                  <ul>{selectedProposal?.evidence?.map((item) => <li key={item}>{item}</li>)}</ul>
                )}
                <small>Tool: {selectedProposal?.tool ?? 'none'} · Rules: {selectedProposal?.rule_version ?? 'legacy request'}</small>
              </div>
              <form className="decision-form" onSubmit={handleDecision}>
                <div className="eyebrow">RECORD DECISION</div>
                <div className="decision-options">
                  {selectedRequest.proposed_slot_id && <label className={`decision-option ${decision === 'APPROVE' ? 'chosen' : ''}`}><input type="radio" name="decision" value="APPROVE" checked={decision === 'APPROVE'} onChange={() => setDecision('APPROVE')} /><span><strong>Approve and book slot</strong><small>Reserve the proposed synthetic slot.</small></span></label>}
                  <label className={`decision-option ${decision === 'REJECT' ? 'chosen' : ''}`}><input type="radio" name="decision" value="REJECT" checked={decision === 'REJECT'} onChange={() => setDecision('REJECT')} /><span><strong>Reject request</strong><small>Mark this request rejected.</small></span></label>
                </div>
                <label>Decision reason<textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={3} required placeholder="Record the reason for this decision" /></label>
                <div className="decision-footer"><span>Decision is submitted under <strong>{user.username}</strong>.</span><button className={decision === 'REJECT' ? 'danger-button' : 'primary-button'} disabled={saving || (decision === 'APPROVE' && !selectedRequest.proposed_slot_id)}>{saving ? 'Saving decision…' : decision === 'APPROVE' ? 'Approve and book' : 'Reject request'} <span>→</span></button></div>
              </form>
            </>
          ) : <EmptyState title="Select a request" description="Choose an item from the inbox to review." />}
        </section>
      </div>
    </div>
  );
}

function MetricCard({ label, value, detail, icon, tone }: { label: string; value: string; detail: string; icon: string; tone: string }) {
  return <section className="metric-card"><div className={`metric-icon ${tone}`}>{icon}</div><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></section>;
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty-state"><div className="empty-icon">⌁</div><strong>{title}</strong><p>{description}</p></div>;
}

function LoadingPanel({ label }: { label: string }) {
  return <div className="loading-state"><span className="spinner" />{label}</div>;
}

function SignInPrompt({ onSignIn, message }: { onSignIn: () => void; message: string }) {
  return <div className="signin-prompt panel"><div className="signin-icon">↗</div><h2>Staff sign-in required</h2><p>{message}</p><button className="primary-button" onClick={onSignIn}>Continue to sign in <span>→</span></button></div>;
}

function RoleDenied({ onGoToFrontDesk }: { onGoToFrontDesk: () => void }) {
  return (
    <div className="signin-prompt panel">
      <div className="signin-icon">↗</div>
      <h2>Clinician access required</h2>
      <p>Your signed-in role cannot review appointment requests. A shift lead or administrator can access this inbox.</p>
      <button className="primary-button" onClick={onGoToFrontDesk}>Go to front desk <span>→</span></button>
    </div>
  );
}

export default App;
