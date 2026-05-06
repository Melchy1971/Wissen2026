import { Link } from 'react-router-dom';

export function ChatSessionList({ items, activeSessionId }) {
  return (
    <section className="panel chat-sidebar">
      <div className="panel__header">
        <div>
          <p className="panel__eyebrow">Sitzungen</p>
          <h3>Chat-Sessions</h3>
        </div>
        <span className="pill">{items.length}</span>
      </div>
      <ul className="stack-list">
        {items.map((item) => (
          <li key={item.id} className={`stack-list__item stack-list__item--block chat-session-card${item.id === activeSessionId ? ' chat-session-card--active' : ''}`}>
            <Link to={`/chat/${item.id}`}>
              {item.title}
            </Link>
            <p className="state-card__meta">{item.lastUserQuestionPreview}</p>
            <p className="state-card__meta">{item.messageCount} Nachrichten · Aktualisiert {item.updatedAtLabel}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}