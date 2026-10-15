import React from 'react';
import credits from '../data/photo-credits.json';
import { ImageWithFallback } from '../components/ui/ImageWithFallback';

const walkin = credits.find((c) => c.key === 'walkin')!;
const triage = credits.find((c) => c.key === 'triage')!;
const appointments = credits.find((c) => c.key === 'appointments')!;

const rows = [
  {
    kicker: 'Walk-in flow',
    title: 'Register once, see the queue build in real time.',
    text: 'A clerk records an arrival. Weighted FIFO with fast-track detection and wait capping sets the order. Nothing moves on its own.',
    credit: walkin,
    alt: 'Empty waiting-room chairs in soft daylight',
    illustrative: 'Illustrative example',
  },
  {
    kicker: 'Triage flow',
    title: 'Fixed categories keep triage consistent.',
    text: 'A nurse completes triage using a small set of categories. The co-pilot surfaces the visit, never the verdict.',
    credit: triage,
    alt: 'Softly lit pastel medicine bottles on a shelf',
    illustrative: 'Illustrative example',
  },
  {
    kicker: 'Appointment review',
    title: 'A proposal, a human decision, a written record.',
    text: 'The AI agent suggests an appointment slot. A shift lead approves or rejects. Every step is logged.',
    credit: appointments,
    alt: 'A minimal calendar resting on a desk',
    illustrative: 'Illustrative example',
  },
];

export function SolutionRows() {
  return (
    <section className="section">
      <div className="max">
        <h2 className="display display-lg" style={{ color: 'var(--emerald-800)', marginBottom: 12 }}>One co-pilot. A human always in control.</h2>
        <p className="sub" style={{ marginBottom: 40 }}>Three flows, one principle: propose, then decide.</p>
        <div style={{ display: 'grid', gap: 48 }}>
          {rows.map((r, i) => (
            <div key={r.kicker} className="grid-2" style={{ direction: i % 2 ? 'rtl' : 'ltr' }}>
              <div style={{ direction: 'ltr' }}>
                <ImageWithFallback
                  src={r.credit.src}
                  alt={r.alt}
                  width={1200}
                  height={800}
                  loading="lazy"
                  credit={{ name: r.credit.photographer, url: r.credit.photoPage }}
                />
                <small style={{ display: 'block', marginTop: 6, color: 'var(--muted)' }}>{r.illustrative}</small>
              </div>
              <div style={{ direction: 'ltr' }}>
                <span className="pill-badge" style={{ marginBottom: 14 }}>{r.kicker}</span>
                <h3 className="display display-md" style={{ color: 'var(--emerald-800)', margin: '8px 0 12px' }}>{r.title}</h3>
                <p className="sub">{r.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}