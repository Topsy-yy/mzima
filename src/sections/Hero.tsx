import React from 'react';
import credits from '../data/photo-credits.json';

const credit = credits.find((c) => c.key === 'hero')!;

type Props = { onNavigate: (to: string) => void };

export function Hero({ onNavigate }: Props) {
  return (
    <section className="hero">
      <img
        className="hero-img"
        src={credit.src}
        alt="Sunlight spilling across a softly lit clinic counter"
        width={1920}
        height={1080}
        loading="eager"
        decoding="async"
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).style.display = 'none';
        }}
      />
      <div className="hero-overlay" />
      <div className="hero-inner">
        <span className="pill-badge">Synthetic-data prototype · Not for live care</span>
        <h1>Clinic queues, handled with clarity.</h1>
        <p>The co-pilot proposes a slot, a route, or a next step. A person always decides.</p>
        <div className="hero-actions">
          <button className="btn btn-primary" onClick={() => onNavigate('/how-it-works')}>See how it works</button>
          <button className="btn btn-outline" onClick={() => onNavigate('/story')}>Read our story</button>
        </div>
        <div className="hero-foot">
          <span aria-hidden="true">✓</span>
          Synthetic data only. Humans remain in charge of every decision.
        </div>
        <p className="hero-credit">
          Photo by <a href={credit.photoPage} target="_blank" rel="noopener noreferrer">{credit.photographer}</a> on Unsplash
        </p>
      </div>
    </section>
  );
}