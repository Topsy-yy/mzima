import React, { useState } from 'react';

const items = [
  { q: 'Is this used in real clinics?', a: 'No. It is a synthetic-data prototype and is not used in live care.' },
  { q: 'Does it diagnose patients?', a: 'No. It never diagnoses. Fixed categories support staff decisions, which remain human.' },
  { q: 'Can the AI approve bookings?', a: 'No. The AI proposes a slot. A shift lead must approve or reject.' },
  { q: 'What data is stored?', a: 'Prototype records use synthetic data only. No real patient information is collected.' },
  { q: 'What roles exist?', a: 'Clerk, nurse, shift lead, patient, and a read-only AI agent.' },
  { q: 'How do I get access?', a: 'Submit a request. A shift lead reviews it before anything is enabled.' },
];

export function Faq() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section className="section-tight">
      <div className="max" style={{ maxWidth: 820 }}>
        <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 24 }}>Questions clinics ask first</h2>
        <div className="faq">
          {items.map((it, i) => (
            <details key={it.q} open={open === i} onToggle={(e) => { if ((e.target as HTMLDetailsElement).open) setOpen(i); else setOpen(null); }}>
              <summary>
                <span>{it.q}</span>
                <span aria-hidden="true">{open === i ? '−' : '+'}</span>
              </summary>
              <p>{it.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}