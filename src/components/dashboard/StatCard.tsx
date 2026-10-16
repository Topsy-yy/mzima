import React from 'react';
export function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="sc-stat">
      <div className="sc-stat-label">{label}</div>
      <div className="sc-stat-value">{value}</div>
    </div>
  );
}