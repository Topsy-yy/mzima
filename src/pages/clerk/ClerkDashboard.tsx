import React, { useCallback, useEffect, useState } from 'react';
import { DashboardLayout } from '../../components/shell/DashboardLayout';
import { DataPanel } from '../../components/dashboard/DataPanel';
import { StatCard } from '../../components/dashboard/StatCard';
import { StatusBadge } from '../../components/dashboard/StatusBadge';
import { EmptyState } from '../../components/dashboard/EmptyState';
import { ErrorState } from '../../components/dashboard/ErrorState';
import { useAuth } from '../../auth/AuthContext';
import { checkInVisit, getWalkInQueue } from '../../api';
import type { QueueVisit as QueueItem } from '../../api';

const items = [
  { label: 'Registration', to: '/visits' },
  { label: 'Queue order', to: '/visits' },
];

export function ClerkDashboard() {
  const { token } = useAuth();
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [patientRef, setPatientRef] = useState('');
  const [ageBand, setAgeBand] = useState('adult');
  const [visitType, setVisitType] = useState('new');
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [submitting, setSubmitting] = useState(false);
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setError('');
      const data = await getWalkInQueue(token);
      setQueue(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load queue.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
    const interval = window.setInterval(() => {
      if (document.visibilityState === 'visible') load();
    }, 15000);
    const onVis = () => { if (document.visibilityState === 'visible') load(); };
    document.addEventListener('visibilitychange', onVis);
    return () => { window.clearInterval(interval); document.removeEventListener('visibilitychange', onVis); };
  }, [load]);

  function toggleFlag(key: string) {
    setFlags((f) => ({ ...f, [key]: !f[key] }));
  }

  async function register(e: React.FormEvent) {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!ageBand) errs.age = 'Select an age band.';
    if (!visitType) errs.visit = 'Select a visit type.';
    setFieldErrors(errs);
    if (Object.keys(errs).length) return;
    if (!token) return;
    setSubmitting(true);
    setCreatedToken(null);
    try {
      const visit = await checkInVisit({ age_band: ageBand, visit_type: visitType, red_flags: flags }, token);
      setCreatedToken(visit.token_number);
      setPatientRef('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed.');
    } finally {
      setSubmitting(false);
    }
  }

  const waiting = queue.length;
  const longest = queue.reduce((max, q) => Math.max(max, q.minutes_waiting), 0);

  return (
    <DashboardLayout role="Clerk" items={items}>
      <div className="sc-purpose">Front desk · Registration and queue order</div>
      <div className="sc-stats">
        <StatCard label="Registered today" value={waiting + (createdToken ? 1 : 0)} />
        <StatCard label="Currently waiting" value={waiting} />
        <StatCard label="Longest current wait" value={`${longest} min`} />
      </div>
      <div className="sc-grid-2">
        <DataPanel title="Register walk-in">
          <form onSubmit={register} className="sc-form">
            <div className="sc-field">
              <label>Patient reference</label>
              <input value={patientRef} onChange={(e) => setPatientRef(e.target.value)} placeholder="Optional reference" />
            </div>
            <div className="sc-field">
              <label>Age band</label>
              <select value={ageBand} onChange={(e) => setAgeBand(e.target.value)}>
                <option value="under_5">Under 5</option>
                <option value="adult">Adult</option>
                <option value="over_65">Over 65</option>
              </select>
              {fieldErrors.age && <span className="sc-err">{fieldErrors.age}</span>}
            </div>
            <div className="sc-field">
              <label>Visit type</label>
              <select value={visitType} onChange={(e) => setVisitType(e.target.value)}>
                <option value="new">New</option>
                <option value="review">Review</option>
                <option value="refill">Refill</option>
              </select>
              {fieldErrors.visit && <span className="sc-err">{fieldErrors.visit}</span>}
            </div>
            <div className="sc-field">
              <label>Reason for visit</label>
              <input placeholder="Short description" />
            </div>
            <div className="sc-field">
              <label>Contact name and phone (optional)</label>
              <input placeholder="Name, phone" />
            </div>
            <label className="sc-check">
              <input type="checkbox" checked={!!flags.companion} onChange={() => toggleFlag('companion')} />
              <span>Patient reports they are with a companion.</span>
            </label>
            <div className="sc-field">
              <label>Concern flags</label>
              <div className="sc-flag-list">
                {['Pain', 'Fever', 'Bleeding'].map((f) => (
                  <label key={f} className="sc-check">
                    <input type="checkbox" checked={!!flags[f]} onChange={() => toggleFlag(f)} />
                    <span>{f}</span>
                  </label>
                ))}
              </div>
            </div>
            <button className="sc-btn primary" type="submit" disabled={submitting}>
              {submitting ? 'Registering…' : 'Register walk-in'}
            </button>
          </form>
          {createdToken && (
            <div className="sc-token-card">
              <div className="sc-token-label">New visit reference</div>
              <div className="sc-token-id">{createdToken}</div>
              <button className="sc-btn ghost" onClick={() => setCreatedToken(null)}>Register another</button>
            </div>
          )}
        </DataPanel>
        <DataPanel title="Queue order">
          {loading && <p className="sc-muted">Loading…</p>}
          {error && <ErrorState message={error} onRetry={load} />}
          {!loading && !error && queue.length === 0 && <EmptyState title="No one waiting" body="Registered patients will appear here." />}
          {!loading && !error && queue.length > 0 && (
            <>
              <table className="sc-table">
                <thead>
                  <tr><th>Position</th><th>Token</th><th>Arrival</th><th>Category</th><th>Waiting</th></tr>
                </thead>
                <tbody>
                  {queue.map((q, i) => (
                    <tr key={q.visit_id}>
                      <td>{i + 1}</td>
                      <td className="sc-mono">{q.token_number}</td>
                      <td className="sc-mono">{new Date(q.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                      <td>
                        <StatusBadge label={q.is_fast_track ? 'Fast-track' : (Object.values(q.red_flags || {}).some(Boolean) ? 'Urgent' : 'Routine')} />
                      </td>
                      <td className="sc-mono">{q.minutes_waiting} min</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="sc-note">Order is set by the queue service. Fast-track and wait-capping rules apply automatically.</p>
            </>
          )}
        </DataPanel>
      </div>
    </DashboardLayout>
  );
}