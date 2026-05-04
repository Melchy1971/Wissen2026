export function VersionList({ items }) {
  return (
    <section className="panel">
      <div className="panel__header"><h3>Versionen</h3></div>
      <ul className="stack-list">
        {items.map((item) => (
          <li key={item.id} className="stack-list__item">
            <strong>v{item.versionNumber}</strong>
            <span>{item.createdAtLabel}</span>
            <code>{item.contentHash || 'kein Hash'}</code>
            {item.isLatest ? <span className="pill">Aktuell</span> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}