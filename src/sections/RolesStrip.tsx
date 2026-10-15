export function RolesStrip() {
  const roles = [
    { name: 'Clerk', can: 'Register walk-ins, capture visit details, view queue order.', cannot: 'Cannot triage, approve appointments, or view more than their queue.' },
    { name: 'Nurse', can: 'Complete triage using fixed categories and flag concerns.', cannot: 'Cannot approve, edit, or reject proposed appointments.' },
    { name: 'Shift Lead', can: 'Review and approve or reject appointment proposals.', cannot: 'Cannot auto-approve; every decision is logged with a reason.' },
    { name: 'Patient', can: 'Request information and view their own request status.', cannot: 'Cannot change queue priority or see other patients.' },
    { name: 'AI Agent', can: 'Read-only. Proposes slots, routes, and next steps with evidence.', cannot: 'Never books, never triages, never overrides staff.' },
  ];
  return (
    <section className="section" style={{ background: 'var(--peach-100)' }}>
      <div className="max">
        <h2 className="display display-lg" style={{ color: 'var(--emerald-800)', marginBottom: 12 }}>Who does what</h2>
        <p className="sub" style={{ marginBottom: 32 }}>Five roles, sharp boundaries.</p>
        <div className="grid-3">
          {roles.map((r) => (
            <article className="role-card" key={r.name}>
              <h3>{r.name}</h3>
              <ul className="role-can">
                <li><strong>Can:</strong> {r.can}</li>
              </ul>
              <ul className="role-cant">
                <li><strong>Cannot:</strong> {r.cannot}</li>
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}