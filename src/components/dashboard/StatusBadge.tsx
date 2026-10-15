import React from 'react';
const map: Record<string, string> = {
  Routine: 'slate',
  'Fast-track': 'amber',
  Urgent: 'red',
  'Awaiting review': 'indigo',
  Approved: 'emerald',
  Rejected: 'slate-strike',
};
export function StatusBadge({ label }: { label: string }) {
  const cls = map[label] || 'slate';
  return <span className={'sc-badge sc-badge-' + cls}>{label}</span>;
}