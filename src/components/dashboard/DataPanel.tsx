import React from 'react';
export function DataPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="sc-panel">
      <h2 className="sc-panel-title">{title}</h2>
      <div className="sc-panel-body">{children}</div>
    </section>
  );
}