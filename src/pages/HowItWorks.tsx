import { useNavigate } from 'react-router-dom';
import React from 'react';
import credits from '../data/photo-credits.json';
import { ImageWithFallback } from '../components/ui/ImageWithFallback';

const hero = credits.find((c) => c.key === 'problem-desk')!;

const steps = [
  { n: '1', title: 'Registration', text: 'A clerk records a walk-in visit and captures the reason for the visit.' },
  { n: '2', title: 'Ranking', text: 'Weighted FIFO with fast-track detection and wait capping sets the order.' },
  { n: '3', title: 'Triage', text: 'A nurse completes triage using fixed categories.' },
  { n: '4', title: 'Proposal', text: 'The AI agent suggests an appointment slot with supporting evidence.' },
  { n: '5', title: 'Review', text: 'A shift lead approves or rejects the proposal.' },
  { n: '6', title: 'Audit', text: 'Every step is logged as an audit event.' },
];

export function HowItWorks() {
  const navigate = useNavigate();
  return (
    <main id="main">
      <section className="hero" style={{ minHeight: '56vh' }}>
        <img src={hero.src} alt="A clipboard and desk in a quiet clinic" width={1200} height={800} className="hero-img" loading="eager" decoding="async" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }} />
        <div className="hero-overlay" />
        <div className="hero-inner" style={{ padding: '56px 0' }}>
          <span className="pill-badge">How it works</span>
          <h1 style={{ marginTop: 16 }}>From arrival to decision, step by step.</h1>
          <p>The co-pilot proposes. A person decides. Every step leaves a record.</p>
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={() => navigate('/sign-up')}>Request access</button>
            <button className="btn btn-outline" onClick={() => navigate('/')}>Back to home</button>
          </div>
        </div>
      </section>
      <section className="section">
        <div className="max">
          <h2 className="display display-lg" style={{ color: 'var(--emerald-800)', marginBottom: 28 }}>A six-step path</h2>
          <div className="timeline">
            {steps.map((s) => (
              <article className="tl-item" key={s.n} data-n={s.n}>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
      <section className="section-tight" style={{ background: 'var(--peach-100)' }}>
        <div className="max">
          <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 20 }}>Human decision in the middle</h2>
          <div className="hil">
            <div className="hil-row">
              <span className="node">PROPOSED_BY_AGENT</span>
              <span className="arrow">→</span>
              <span className="node node-human">Human decision</span>
              <span className="arrow">→</span>
              <span className="node">APPROVED</span>
              <span style={{ marginLeft: 6 }} />
              <span className="node">REJECTED</span>
            </div>
            <p className="sub" style={{ margin: '8px auto 0', textAlign: 'center' }}>
              The UI never auto-approves. A shift lead must choose approved or rejected, with a reason.
            </p>
          </div>
        </div>
      </section>
      <section className="section-tight">
        <div className="max" style={{ maxWidth: 820 }}>
          <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 20 }}>Short FAQ</h2>
          <div className="faq">
            <details open>
              <summary><span>Does the system move anyone automatically?</span><span>−</span></summary>
              <p>No. Position and appointments change only after human sign-off.</p>
            </details>
            <details>
              <summary><span>Is this a clinical protocol?</span><span>+</span></summary>
              <p>No. It is a synthetic-data prototype for operations, not care.</p>
            </details>
          </div>
        </div>
      </section>
      <div className="max" style={{ marginBottom: 32 }}>
        <small className="credit" style={{ display: 'block' }}>
          Photo by <a href={hero.photoPage} target="_blank" rel="noopener noreferrer">{hero.photographer}</a> on Unsplash
        </small>
      </div>
    </main>
  );
}