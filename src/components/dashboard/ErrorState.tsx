import React from 'react';
export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="sc-error">
      <p>{message}</p>
      <button className="sc-btn" onClick={onRetry}>Retry</button>
    </div>
  );
}