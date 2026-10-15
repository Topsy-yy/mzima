export function ClosingCta({ onNavigate }: { onNavigate: (to: string) => void }) {
  return (
    <section className="section-tight">
      <div className="max">
        <div className="cta-band">
          <h2 className="display display-lg">Ready to see the queue clearly?</h2>
          <p>Walk the full flow, from arrival to decision.</p>
          <button className="btn btn-primary" onClick={() => onNavigate('/how-it-works')}>See how it works</button>
        </div>
      </div>
    </section>
  );
}