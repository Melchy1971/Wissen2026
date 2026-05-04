import { Link, Outlet } from 'react-router-dom';

export function AppShell() {
  return (
    <div className="shell">
      <header className="shell__header">
        <div>
          <p className="shell__eyebrow">M3c Chat UI</p>
          <h1>Wissensbasis V1</h1>
        </div>
        <nav>
          <div className="shell__nav">
            <Link to="/documents">Dokumente</Link>
            <Link to="/chat">Chat</Link>
          </div>
        </nav>
      </header>
      <main className="shell__content">
        <Outlet />
      </main>
    </div>
  );
}