export function SafetyBlock() {
  const items = [
    'Synthetic data only',
    'No autonomous triage or booking',
    'Every appointment decision needs human sign-off',
    'Every action writes an audit event',
  ];
  return (
    <section className="section-tight">
      <div className="max">
        <div className="safe-block">
          <h2 className="display display-md" style={{ color: 'var(--emerald-800)' }}>Built to keep people in charge.</h2>
          <p className="sub">Safety is a product feature, not a footnote.</p>
          <div className="safe-list">
            {items.map((i) => (
              <div className="safe-item" key={i}>
                <h4>{i}</h4>
                <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>Prototype guidance, not a clinical protocol.</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}