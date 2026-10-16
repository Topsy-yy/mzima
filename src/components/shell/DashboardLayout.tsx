import React from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function DashboardLayout({
  role,
  items,
  children,
}: {
  role: string;
  items: { label: string; to: string }[];
  children: React.ReactNode;
}) {
  return (
    <div className="sc-shell">
      <Sidebar role={role} items={items} />
      <div className="sc-main-wrap">
        <TopBar />
        <main className="sc-main" id="main">{children}</main>
      </div>
    </div>
  );
}