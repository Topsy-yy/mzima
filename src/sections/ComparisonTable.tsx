export function ComparisonTable() {
  const rows = [
    ['Queue visibility', 'Paper tallies, stale by afternoon', 'Manual spreadsheets, delayed', 'Live, time-stamped queue'],
    ['Fast-track handling', 'Depends on memory', 'Sorting by hand', 'Weighted FIFO with detection'],
    ['Audit trail', 'None', 'Optional, often skipped', 'Every action logged'],
    ['Human sign-off', 'Implicit', 'Implicit', 'Required, named, reasoned'],
    ['Setup time', 'Weeks of training', 'Days of templates', 'Hours, synthetic data first'],
  ];
  return (
    <section className="section">
      <div className="max">
        <h2 className="display display-lg" style={{ color: 'var(--emerald-800)', marginBottom: 12 }}>Mzima vs. manual process</h2>
        <p className="sub" style={{ marginBottom: 32 }}>Columns: paper logs, spreadsheets, Mzima.</p>
        <div style={{ overflowX: 'auto' }}>
          <table className="compare">
            <thead>
              <tr>
                <th>Capability</th>
                <th>Paper logs</th>
                <th>Spreadsheets</th>
                <th className="hl">Mzima</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([label, a, b, c]) => (
                <tr key={label}>
                  <td className="rowlabel">{label}</td>
                  <td>{a}</td>
                  <td>{b}</td>
                  <td className="hl">{c}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}