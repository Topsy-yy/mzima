import React from 'react';
import { Link } from 'react-router-dom';
import credits from '../../data/photo-credits.json';
import { ImageWithFallback } from '../ui/ImageWithFallback';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  const photo = credits.find((c) => c.key === 'hero')!;

  return (
    <div className="auth-layout">
      <aside className="auth-side" aria-label="Staff access information">
        <div className="auth-side-inner">
          <p className="eyebrow" style={{ color: 'rgba(255,255,255,0.75)' }}>STAFF ACCESS</p>
          <h2 style={{ color: '#fff', marginTop: 12 }}>
            Staff access to the clinic queue. Synthetic data only.
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.82)', marginTop: 12, lineHeight: 1.6 }}>
            Sign in with the account your shift lead gave you. No live patient data is stored here.
          </p>
          <div style={{ marginTop: 'auto', paddingTop: 24 }}>
            <ImageWithFallback
              src={photo.src}
              alt="Soft natural light falling across an empty clinic workspace"
              width={1600}
              height={1067}
              loading="eager"
              credit={{ name: photo.photographer, url: photo.photoPage }}
              className="auth-photo"
            />
          </div>
        </div>
      </aside>
      <section className="auth-main">
        <header className="auth-topbar">
          <Link to="/" className="wordmark" aria-label="Mzima home">
            <span className="wordmark-dot" aria-hidden="true">m</span>
            Mzima
          </Link>
          <Link to="/sign-up" className="btn btn-ghost">
            Request access
          </Link>
        </header>
        <div className="auth-formwrap">{children}</div>
      </section>
    </div>
  );
}