import { Link, Outlet } from 'react-router-dom';

export function AppShell() {
  return (
    <div className="shell">
      <header className="shell__header">
        <div>
          <p className="shell__eyebrow">M3a GUI Foundation</p>
          <h1>Wissensbasis V1</h1>
        </div>
        <nav>
          <Link to="/documents">Dokumente</Link>
        </nav>
      </header>
      <main className="shell__content">
        <Outlet />
      </main>
    </div>
  );
}