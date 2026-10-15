export function ProblemStrip() {
  const cards = [
    { title: 'Fast-track patients lost behind routine visits', text: 'Urgent, simple cases sit behind long routine queues with nobody noticing.' },
    { title: 'Triage decisions that drift under pressure', text: 'The same symptom can get three different answers depending on the hour.' },
    { title: 'Backlogs nobody sees until waits grow', text: 'Bottlenecks form quietly and only surface once patients are already waiting.' },
    { title: 'No record of why a decision was made', text: 'Staff handoffs leave reasoning in heads and sticky notes, not in the system.' },
  ];
  return (
    <section className="section-tight">
      <div className="max">
        <h2 className="display display-md" style={{ color: 'var(--emerald-800)', marginBottom: 12 }}>Sound familiar?</h2>
        <p className="sub" style={{ marginBottom: 32 }}>Small outpatient clinics carry heavy load with thin visibility.</p>
        <div className="grid-4">
          {cards.map((c) => (
            <article className="prob-card" key={c.title}>
              <h3>{c.title}</h3>
              <p>{c.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}