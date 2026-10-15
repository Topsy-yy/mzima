import React, { useCallback, useEffect, useState } from 'react';
import { DashboardLayout } from '../../components/shell/DashboardLayout';
import { DataPanel } from '../../components/dashboard/DataPanel';
import { StatusBadge } from '../../components/dashboard/StatusBadge';
import { EmptyState } from '../../components/dashboard/EmptyState';
import { ErrorState } from '../../components/dashboard/ErrorState';
import { useAuth } from '../../auth/AuthContext';
import { callVisit, completeVisitTriage, getWalkInQueue } from '../../api';
import { TRIAGE_CATEGORIES, TRIAGE_DESTINATIONS, CONCERN_FLAGS } from '../../constants/clinical';
import type { QueueVisit } from '../../api';

const items = [
  { label: 'Triage', to: '/triage' },
  { label: 'Care coordination', to: '/triage' },
];

export function NurseDashboard() {
  const { token } = useAuth();
  const [queue, setQueue] = useState<QueueVisit[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('');
  const [destination, setDestination] = useState(TRIAGE_DESTINATIONS[0]);
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [note, setNote] = useState('');
  const [flagForLead, setFlagForLead] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [categoryError, setCategoryError] = useState('');
  const [calling, setCalling] = useState(false);
  const [flagged, setFlagged] = useState<string[]>([]);

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
    const interval = window.setInterval(() => { if (document.visibilityState === 'visible') load(); }, 15000);
    const onVis = () => { if (document.visibilityState === 'visible') load(); };
    document.addEventListener('visibilitychange', onVis);
    return () => { window.clearInterval(interval); document.removeEventListener('visibilitychange', onVis); };
  }, [load]);

  async function callNext() {
    if (!queue.length || !token) return;
    setCalling(true);
    try {
      await callVisit(queue[0].visit_id, '', token);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to call patient.');
    } finally {
      setCalling(false);
    }
  }

  const selected = queue.find((q) => q.visit_id === selectedId) || null;

  async function submitTriage(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    if (!category) { setCategoryError('Select a triage category before submitting.'); return; }
    setCategoryError('');
    if (!token) return;
    setSubmitting(true);
    setSuccess(false);
    try {
      await completeVisitTriage(selected.visit_id, category, destination, token);
      setSuccess(true);
      if (flagForLead) setFlagged((f) => (f.includes(selected.visit_id) ? f : [...f, selected.visit_id]));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Triage failed.');
    } finally {
      setSubmitting(false);
    }
  }

  function resetForm() {
    setCategory(''); setDestination(TRIAGE_DESTINATIONS[0]); setFlags({}); setNote(''); setFlagForLead(false); setSuccess(false); setCategoryError('');
  }

  useEffect(() => { resetForm(); }, [selectedId]);

  return (
    <DashboardLayout role="Nurse" items={items}>
      <div className="sc-purpose">Triage · Fixed categories and concern flags</div>
      <div className="sc-grid-2">
        <DataPanel title="Awaiting triage">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span className="sc-muted">{queue.length} waiting</span>
            <button className="sc-btn primary" disabled={!queue.length || calling} onClick={callNext}>
              {calling ? 'Calling…' : 'Call next'}
            </button>
          </div>
          {loading && <p className="sc-muted">Loading…</p>}
          {error && <ErrorState message={error} onRetry={load} />}
          {!loading && !error && queue.length === 0 && <EmptyState title="No patients awaiting triage" body="New walk-ins will appear here." />}
          {!loading && !error && queue.length > 0 && (
            <div className="sc-list" role="listbox" aria-label="Awaiting triage">
              {queue.map((q) => (
                <button
                  key={q.visit_id}
                  role="option"
                  aria-selected={selectedId === q.visit_id}
                  className={'sc-row' + (selectedId === q.visit_id ? ' selected' : '')}
                  onClick={() => setSelectedId(q.visit_id)}
                >
                  <span className="sc-mono">{q.token_number}</span>
                  <span>{q.minutes_waiting} min</span>
                  <StatusBadge label={q.is_fast_track ? 'Fast-track' : (Object.values(q.red_flags || {}).some(Boolean) ? 'Urgent' : 'Routine')} />
                  {Object.values(q.red_flags || {}).some(Boolean) && <span className="sc-flag">Concern</span>}
                </button>
              ))}
            </div>
          )}
        </DataPanel>
        <DataPanel title="Triage form">
          {!selected && <EmptyState title="Select a patient" body="Choose an item from the awaiting list." />}
          {selected && (
            <form onSubmit={submitTriage} className="sc-form">
              <div className="sc-field">
                <label>Token</label>
                <div className="sc-mono">{selected.token_number}</div>
              </div>
              <div className="sc-field">
                <label>Triage category (required)</label>
                <div className="sc-radio-grid">
                  {TRIAGE_CATEGORIES.map((c) => (
                    <label key={c} className="sc-radio">
                      <input type="radio" name="cat" value={c} checked={category === c} onChange={() => setCategory(c)} />
                      <span>{c}</span>
                    </label>
                  ))}
                </div>
                {categoryError && <span className="sc-err">{categoryError}</span>}
              </div>
              <div className="sc-field">
                <label>Destination</label>
                <select value={destination} onChange={(e) => setDestination(e.target.value)}>
                  {TRIAGE_DESTINATIONS.map((d) => <option key={d}>{d}</option>)}
                </select>
              </div>
              <div className="sc-field">
                <label>Concern flags</label>
                <div className="sc-flag-list">
                  {CONCERN_FLAGS.map((f) => (
                    <label key={f} className="sc-check">
                      <input type="checkbox" checked={!!flags[f]} onChange={() => setFlags((x) => ({ ...x, [f]: !x[f] }))} />
                      <span>{f}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="sc-field">
                <label>Note (500 chars)</label>
                <textarea value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} rows={4} />
                <small className="sc-muted">{note.length}/500</small>
              </div>
              <label className="sc-check">
                <input type="checkbox" checked={flagForLead} onChange={() => setFlagForLead((v) => !v)} />
                <span>Flag for shift lead (marks for review, does not change queue order)</span>
              </label>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="sc-btn primary" type="submit" disabled={submitting}>
                  {submitting ? 'Submitting…' : 'Submit triage'}
                </button>
                {success && <span className="sc-success">Triage saved.</span>}
              </div>
            </form>
          )}
        </DataPanel>
      </div>
      <DataPanel title="Care coordination (read-only)">
        <p className="sc-muted" style={{ marginBottom: 12 }}>Flagged visits waiting for shift lead review. Status only.</p>
        {flagged.length === 0 && <EmptyState title="No flagged visits" body="Visits flagged for the shift lead will appear here." />}
        {flagged.length > 0 && (
          <ul className="sc-simple-list">
            {flagged.map((id) => {
              const q = queue.find((x) => x.visit_id === id);
              return <li key={id}>{q?.token_number ?? id} · {q?.minutes_waiting ?? 0} min waiting</li>;
            })}
          </ul>
        )}
      </DataPanel>
    </DashboardLayout>
  );
}