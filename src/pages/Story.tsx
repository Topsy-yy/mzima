import { useNavigate } from 'react-router-dom';
import React from 'react';
import credits from '../data/photo-credits.json';
import { ImageWithFallback } from '../components/ui/ImageWithFallback';

const story = credits.find((c) => c.key === 'story')!;

export function Story() {
  const navigate = useNavigate();
  return (
    <main id="main">
      <section className="hero" style={{ minHeight: '56vh' }}>
        <ImageWithFallback src={story.src} alt="Soft light on green leaves in a clinic window" width={1200} height={800} loading="eager" credit={{ name: story.photographer, url: story.photoPage }} className="hero-media" />
        <div className="hero-overlay" />
        <div className="hero-inner" style={{ padding: '56px 0' }}>
          <span className="pill-badge">Our story</span>
          <h1 style={{ marginTop: 16 }}>Why we built Mzima.</h1>
          <p>Small outpatient clinics carry heavy load with thin visibility. Mzima exists to make the queue visible before it becomes a problem.</p>
        </div>
      </section>
      <section className="section">
        <div className="max" style={{ display: 'grid', gap: 20 }}>
          <article className="story-block">
            <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 10 }}>The problem in clinics</h2>
            <p className="sub">Walk-ins, fast-track cases, and routine visits share one crowded line. Decisions happen under pressure and leave little trace.</p>
          </article>
          <article className="story-block">
            <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 10 }}>AI proposes, humans decide</h2>
            <p className="sub">The agent reads patterns and suggests. It never books, never triages, never overrides. A named person signs off.</p>
          </article>
          <article className="story-block">
            <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 10 }}>What the prototype is still learning</h2>
            <p className="sub">Synthetic data first. Real calibration comes later, with approvals and a pilot facility.</p>
          </article>
        </div>
      </section>
      <section className="section-tight" style={{ background: 'var(--peach-100)' }}>
        <div className="max">
          <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 20 }}>Principles</h2>
          <div className="grid-4">
            {[
              { t: 'Safety first', d: 'No autonomous action. Staff decide.' },
              { t: 'Transparency', d: 'Every proposal shows its basis.' },
              { t: 'Synthetic data', d: 'Prototype runs on synthetic records.' },
              { t: 'Humans decide', d: 'Sign-off is named and logged.' },
            ].map((p) => (
              <div className="principle" key={p.t}>
                <h4>{p.t}</h4>
                <p style={{ color: 'var(--muted)', margin: 0 }}>{p.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="section-tight">
        <div className="max">
          <div className="story-block" style={{ maxWidth: 720 }}>
            <h3 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 8 }}>Built by [Name]</h3>
            <p className="sub">[Bio placeholder: edit this with your background, motivation, and what you learned building Mzima.]</p>
          </div>
          <div style={{ marginTop: 28 }}>
            <button className="btn btn-primary" onClick={() => navigate('/')}>Back to home</button>
          </div>
        </div>
      </section>
    </main>
  );
}