import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export interface NavItem { label: string; to: string; }

export function Sidebar({ role, items }: { role: string; items: NavItem[] }) {
  const navigate = useNavigate();
  const location = useLocation();
  return (
    <aside className="sc-sidebar" aria-label="Primary navigation">
      <div className="sc-sidebar-role">{role}</div>
      <nav className="sc-nav">
        {items.map((item) => (
          <button
            key={item.to}
            data-short={item.label.slice(0, 2)}
            className={'sc-nav-item' + (location.pathname === item.to ? ' active' : '')}
            onClick={() => navigate(item.to)}
            aria-current={location.pathname === item.to ? 'page' : undefined}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}