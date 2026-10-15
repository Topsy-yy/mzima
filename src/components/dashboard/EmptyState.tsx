import React from 'react';
export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="sc-empty">
      <div className="sc-empty-title">{title}</div>
      <p className="sc-empty-body">{body}</p>
    </div>
  );
}