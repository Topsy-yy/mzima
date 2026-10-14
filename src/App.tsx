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

type Page = 'patient' | 'staff' | 'clinician' | 'signin';

const pageTitles: Record<Page, string> = {
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
  const [page, setPage] = useState<Page>('patient');
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
      .catch(() => {
        sessionStorage.removeItem('mzima_access_token');
        setToken('');
        setUser(null);
      })
      .finally(() => setAuthLoading(false));
  }, [token]);

  const signOut = () => {
    sessionStorage.removeItem('mzima_access_token');
    setToken('');
    setUser(null);
    setNotice('You have signed out.');
    setPage('patient');
  };

  const handleSignedIn = (accessToken: string, currentUser: ApiUser) => {
    sessionStorage.setItem('mzima_access_token', accessToken);
    setToken(accessToken);
    setUser(currentUser);
    setAuthError('');
    setPage(currentUser.role === 'clerk' ? 'staff' : 'clinician');
    setNotice(`Signed in as ${currentUser.username} (${currentUser.role.replace('_', ' ')}).`);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage('patient'); }}>
          <span className="brand-mark">m</span>
          <span>
            <strong>mzima</strong>
            <small>care access</small>
          </span>
        </a>

        <div className="nav-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
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
            <button className="avatar top-avatar" title={user?.username ?? 'Staff account'} onClick={() => setPage(user ? 'clinician' : 'signin')}>
              {user ? user.username.slice(0, 1).toUpperCase() : '·'}
            </button>
          </div>
        </header>

        {notice && <div className="notice success-notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Dismiss">×</button></div>}
        {authError && <div className="notice error-notice" role="alert">{authError}<button onClick={() => setAuthError('')} aria-label="Dismiss">×</button></div>}

        {page === 'patient' && <PatientPage onNotice={setNotice} />}
        {page === 'staff' && (
          <StaffPage token={token} user={user} authLoading={authLoading} onSignIn={() => setPage('signin')} onNotice={setNotice} />
        )}
        {page === 'clinician' && (
          <ClinicianPage token={token} user={user} authLoading={authLoading} onSignIn={() => setPage('signin')} onNotice={setNotice} />
        )}
        {page === 'signin' && <SignInPage onSignedIn={handleSignedIn} onError={setAuthError} />}
      </main>
    </div>
  );
}

function PatientPage({ onNotice }: { onNotice: (message: string) => void }) {
  const [patientIdentifier, setPatientIdentifier] = useState('');
  const [specialty, setSpecialty] = useState('General outpatient');
  const [submitted, setSubmitted] = useState<AppointmentRequest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const request = await createAppointmentRequest(patientIdentifier.trim(), specialty);
      setSubmitted(request);
      onNotice('Your appointment request was saved.');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not submit your request.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="content-wrap">
      <section className="welcome-banner">
        <div className="welcome-copy">
          <div className="eyebrow">A simpler way to get started</div>
          <h2>Let’s get your appointment request underway.</h2>
          <p>Share the service you need. Clinic staff will review your request and follow up with you.</p>
          <div className="banner-footnote"><span className="shield">✓</span> Your request is handled by the clinic team.</div>
        </div>
        <div className="banner-art" aria-hidden="true"><div className="art-circle">+</div><div className="art-card"><span>REQUEST</span><strong>Received</strong><i>✓</i></div><div className="art-spark">✳</div></div>
      </section>

      <div className="patient-columns">
        <section className="panel request-panel">
          <div className="panel-heading">
            <div><div className="eyebrow">NEW REQUEST</div><h2>Appointment details</h2></div>
            <span className="step-count">STEP 1 OF 1</span>
          </div>
          {submitted ? (
            <div className="submitted-card" role="status">
              <div className="submitted-icon">✓</div>
              <div className="eyebrow">REQUEST RECEIVED</div>
              <h3>Your request is with the clinic team.</h3>
              <p>Keep this reference for follow-up. This is a request receipt, not a confirmed appointment.</p>
              <dl className="request-summary">
                <div><dt>Reference</dt><dd>{submitted.id}</dd></div>
                <div><dt>Requested service</dt><dd>{submitted.requested_specialty}</dd></div>
                <div><dt>Status</dt><dd><span className="status-chip pending">{submitted.status.replace(/_/g, ' ')}</span></dd></div>
                <div><dt>Submitted</dt><dd>{formatDate(submitted.created_at)}</dd></div>
              </dl>
              <button className="secondary-button" onClick={() => { setSubmitted(null); setPatientIdentifier(''); }}>Make another request</button>
            </div>
          ) : (
            <form className="stack-form" onSubmit={handleSubmit}>
              <div className="privacy-note"><span>i</span><div><strong>Only the details this prototype supports</strong><small>The current clinic API accepts a patient reference and requested specialty. Do not enter real health information.</small></div></div>
              <label>
                Synthetic patient reference
                <input value={patientIdentifier} onChange={(event) => setPatientIdentifier(event.target.value)} placeholder="e.g. DEMO-024" required maxLength={100} />
                <small>Use a demo identifier only. Do not use a national ID or real patient details.</small>
              </label>
              <label>
                Service requested
                <select value={specialty} onChange={(event) => setSpecialty(event.target.value)}>
                  <option>General outpatient</option>
                  <option>Maternal and child health</option>
                  <option>Chronic care review</option>
                  <option>Follow-up appointment</option>
                </select>
              </label>
              {error && <p className="inline-error" role="alert">{error}</p>}
              <button className="primary-button" disabled={loading}>{loading ? 'Sending request…' : 'Send appointment request'} <span>→</span></button>
              <p className="form-footnote">Submitting creates a request for review. It does not book a slot or change queue position.</p>
            </form>
          )}
        </section>

        <aside className="panel next-steps-panel">
          <div className="eyebrow">WHAT HAPPENS NEXT</div>
          <h2>One step at a time.</h2>
          <div className="steps-list">
            <div className="step-item"><div className="step-number current">1</div><div><strong>Request received</strong><p>Your request is saved for staff review.</p></div></div>
            <div className="step-item"><div className="step-number">2</div><div><strong>Clinic team reviews</strong><p>A staff member checks the request and follows up if needed.</p></div></div>
            <div className="step-item"><div className="step-number">3</div><div><strong>Appointment confirmed</strong><p>The clinic will provide details when a booking is confirmed.</p></div></div>
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
  onNotice,
}: {
  token: string;
  user: ApiUser | null;
  authLoading: boolean;
  onSignIn: () => void;
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

  return (
    <div className="content-wrap">
      <div className="page-intro-row">
        <div><p className="page-intro">Review each request and record a named staff decision.</p><p className="last-updated">This backend exposes requests and decisions, but not agent evidence or appointment slots yet.</p></div>
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
              <div className="capability-note"><strong>Evidence not available from this API</strong><p>The current backend does not return agent rationale, routing rules, priority, appointment slots, or an audit-history endpoint. No recommendation is shown here as if it were real.</p></div>
              <form className="decision-form" onSubmit={handleDecision}>
                <div className="eyebrow">RECORD DECISION</div>
                <div className="decision-options">
                  <label className={`decision-option ${decision === 'APPROVE' ? 'chosen' : ''}`}><input type="radio" name="decision" value="APPROVE" checked={decision === 'APPROVE'} onChange={() => setDecision('APPROVE')} /><span><strong>Approve request</strong><small>Mark this request approved.</small></span></label>
                  <label className={`decision-option ${decision === 'REJECT' ? 'chosen' : ''}`}><input type="radio" name="decision" value="REJECT" checked={decision === 'REJECT'} onChange={() => setDecision('REJECT')} /><span><strong>Reject request</strong><small>Mark this request rejected.</small></span></label>
                </div>
                <label>Decision reason<textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={3} required placeholder="Record the reason for this decision" /></label>
                <div className="decision-footer"><span>Decision is submitted under <strong>{user.username}</strong>.</span><button className={decision === 'REJECT' ? 'danger-button' : 'primary-button'} disabled={saving}>{saving ? 'Saving decision…' : 'Submit decision'} <span>→</span></button></div>
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

export default App;
