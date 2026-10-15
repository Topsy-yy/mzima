import React, { useState } from 'react';

type Props = {
  src: string;
  alt: string;
  width: number;
  height: number;
  credit?: { name: string; url: string } | null;
  loading?: 'lazy' | 'eager';
  className?: string;
};

export function ImageWithFallback({ src, alt, width, height, credit, loading = 'lazy', className }: Props) {
  const [failed, setFailed] = useState(false);

  return (
    <figure className={className}>
      <div className="img-wrap" style={{ aspectRatio: `${width}/${height}` }}>
        {!failed ? (
          <img
            src={src}
            alt={alt}
            width={width}
            height={height}
            loading={loading}
            decoding="async"
            onError={() => setFailed(true)}
          />
        ) : (
          <div className="img-fallback" aria-hidden="true">
            <svg viewBox="0 0 120 120" fill="none">
              <defs>
                <pattern id="p" width="12" height="12" patternUnits="userSpaceOnUse">
                  <path d="M0 12L12 0M-2 2L2 -2M10 14L14 10" stroke="#fff" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="120" height="120" fill="url(#p)" />
            </svg>
          </div>
        )}
      </div>
      {credit && (
        <figcaption className="credit">
          Photo by{' '}
          <a href={credit.url} target="_blank" rel="noopener noreferrer">
            {credit.name}
          </a>{' '}
          on Unsplash
        </figcaption>
      )}
    </figure>
  );
}