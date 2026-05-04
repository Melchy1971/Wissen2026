export function ChunkPreviewList({ items }) {
  return (
    <section className="panel">
      <div className="panel__header"><h3>Chunk-Vorschau</h3></div>
      <ul className="stack-list">
        {items.map((item) => (
          <li key={item.id} className="stack-list__item stack-list__item--block">
            <div className="chunk-row">
              <strong>{item.positionLabel}</strong>
              <span>{item.sourceAnchorLabel}</span>
            </div>
            <p>{item.textPreview || 'Keine Vorschau verfuegbar'}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}