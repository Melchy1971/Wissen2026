export function ErrorState({ error }) {
  return (
    <section className="state-card state-card--error">
      <h2>{error.title}</h2>
      <p>{error.message}</p>
      <p className="state-card__meta">Fehlercode: {error.code}</p>
    </section>
  );
}