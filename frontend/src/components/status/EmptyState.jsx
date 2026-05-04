export function EmptyState({ title, message }) {
  return (
    <section className="state-card">
      <h2>{title}</h2>
      <p>{message}</p>
    </section>
  );
}