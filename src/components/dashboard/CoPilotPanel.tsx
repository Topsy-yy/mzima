import React, { useState } from 'react';

type Kind = 'visits' | 'triage' | 'review';

export function CoPilotPanel({ kind, stats }: { kind: Kind; stats: { total: number; highlight: number } }) {
  const [reply, setReply] = useState<string>('');

  function ask(type: 'overview' | 'highlight' | 'safety') {
    if (type === 'overview') {
      setReply(`Queue overview: ${stats.total} items currently listed. Counts and ordering come from the backend ranking rules; I only summarise them.`);
    } else if (type === 'highlight') {
      setReply(`Highlights: ${stats.highlight} item(s) flagged by rule-based checks. Open the relevant case before deciding anything.`);
    } else {
      setReply('Safety: I am read-only. I never approve, triage, or change queue order. Every decision stays with staff and is audited.');
    }
  }

  return (
    <section className="card" style={{ padding: 24, marginTop: 24, background: 'var(--peach-100)' }}>
      <h2 style={{ color: 'var(--emerald-800)', marginBottom: 8 }}>AI co-pilot (read-only)</h2>
      <p className="sub" style={{ fontSize: 15, marginBottom: 16 }}>
        The co-pilot summarises queue data and explains the rules. It never acts on its own.
      </p>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
        <button className="btn btn-outline" onClick={() => ask('overview')}>Summarise queue</button>
        <button className="btn btn-outline" onClick={() => ask('highlight')}>Flagged items</button>
        <button className="btn btn-outline" onClick={() => ask('safety')}>Safety rules</button>
      </div>
      {reply && (
        <div role="status" aria-live="polite" style={{ padding: 16, background: 'var(--peach-50)', borderRadius: 12, border: '1px solid var(--peach-300)', color: 'var(--ink)' }}>
          {reply}
        </div>
      )}
      {kind === 'review' && (
        <small style={{ display: 'block', marginTop: 10, color: 'var(--muted)' }}>
          Proposals still need a shift lead’s approval or rejection.
        </small>
      )}
    </section>
  );
}