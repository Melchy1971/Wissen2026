import { useEffect, useMemo, useRef, useState } from 'react';

import { rebuildSearchIndex } from '../api/admin.js';
import { getJob } from '../api/jobs.js';
import { EmptyState } from '../components/status/EmptyState.jsx';
import { ErrorState } from '../components/status/ErrorState.jsx';
import { mapError, mapJobStatus } from '../view-models/mappers.js';

function formatResult(result) {
  return JSON.stringify(result, null, 2);
}

export function AdminDiagnosticsPage() {
  const [adminToken, setAdminToken] = useState('');
  const [workspaceId, setWorkspaceId] = useState('');
  const [state, setState] = useState({ status: 'idle', job: null, result: null, error: null });
  const pollTimeoutRef = useRef(null);

  const copyPayload = useMemo(() => (state.result ? formatResult(state.result) : ''), [state.result]);
  const mappedJobState = mapJobStatus(state.job);

  useEffect(() => {
    return () => {
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }
    };
  }, []);

  async function pollJob(jobId) {
    try {
      const job = await getJob(jobId);
      if (job.status === 'completed') {
        setState({ status: 'success', job, result: job.result, error: null });
        return;
      }
      if (job.status === 'failed') {
        setState({
          status: 'error',
          job,
          result: null,
          error: mapError({ code: job.error_code, message: job.error_message, details: {} }),
        });
        return;
      }

      setState({ status: 'polling', job, result: null, error: null });
      pollTimeoutRef.current = setTimeout(() => {
        void pollJob(jobId);
      }, 250);
    } catch (error) {
      setState({ status: 'error', job: null, result: null, error: mapError(error) });
    }
  }

  async function handleRebuildSubmit(event) {
    event.preventDefault();

    const normalizedToken = adminToken.trim();
    if (!normalizedToken) {
      setState({
        status: 'error',
        job: null,
        result: null,
        error: {
          code: 'AUTH_REQUIRED',
          title: 'Admin-Authentifizierung erforderlich',
          message: 'Fuer den Rebuild ist ein Admin-Token erforderlich.',
        },
      });
      return;
    }

    setState({ status: 'loading', job: null, result: null, error: null });
    try {
      const job = await rebuildSearchIndex({ adminToken: normalizedToken, workspaceId });
      setState({ status: 'polling', job, result: null, error: null });
      void pollJob(job.id);
    } catch (error) {
      setState({ status: 'error', job: null, result: null, error: mapError(error) });
    }
  }

  async function handleCopyDetails() {
    if (!copyPayload) return;
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(copyPayload);
    }
  }

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <p className="panel__eyebrow">M4d Diagnostics</p>
          <h2>Admin-Diagnostik</h2>
        </div>
        <p className="page-header__meta">Maintenance Action: Search Index Rebuild</p>
      </div>

      <section className="panel diagnostics-card-grid">
        <article className="diagnostics-card diagnostics-card--accent">
          <div className="panel__header">
            <div>
              <p className="panel__eyebrow">Search Index</p>
              <h3>Rebuild ausfuehren</h3>
            </div>
            <span className="status-badge status-badge--info">Admin</span>
          </div>
          <p className="diagnostics-card__text">
            Baut den PostgreSQL FTS-Index fuer aktive Dokumente neu auf. Archivierte und geloeschte Dokumente bleiben ausgeschlossen.
          </p>
          <form className="search-bar" onSubmit={handleRebuildSubmit}>
            <label className="search-bar__field">
              <span className="search-bar__label">Admin-Token</span>
              <input
                type="password"
                value={adminToken}
                onChange={(event) => setAdminToken(event.target.value)}
                placeholder="x-admin-token"
              />
            </label>
            <label className="search-bar__field">
              <span className="search-bar__label">Workspace-ID optional</span>
              <input
                type="text"
                value={workspaceId}
                onChange={(event) => setWorkspaceId(event.target.value)}
                placeholder="leer = alle Workspaces"
              />
            </label>
            <div className="search-bar__actions">
              <button type="submit" disabled={state.status === 'loading'}>
                {state.status === 'loading' || state.status === 'polling' ? 'Rebuild laeuft...' : 'Search Index neu aufbauen'}
              </button>
            </div>
          </form>
        </article>

        <article className="diagnostics-card">
          <div className="panel__header">
            <div>
              <p className="panel__eyebrow">Sicherheitsgrenzen</p>
              <h3>Redaktion und Scope</h3>
            </div>
          </div>
          <ul className="diagnostics-list">
            <li>Keine Dokumenttexte in Logs oder Ergebnisansicht</li>
            <li>Rebuild ist idempotent und fuer Restore-Szenarien gedacht</li>
            <li>Admin-Rechte werden serverseitig ueber den API-Guard erzwungen</li>
          </ul>
        </article>
      </section>

      {state.status === 'error' ? <ErrorState error={state.error} /> : null}

      {state.status === 'idle' ? (
        <EmptyState
          title="Keine Aktion ausgefuehrt"
          message="Fuehre einen Search-Index-Rebuild aus, um den aktuellen Status und die technischen Details zu sehen."
        />
      ) : null}

      {state.status === 'polling' ? (
        <section className="panel diagnostics-result">
          <div className="panel__header">
            <div>
              <p className="panel__eyebrow">Rebuild-Job</p>
              <h3>Job wird verarbeitet</h3>
            </div>
            <span className={`status-badge status-badge--${mappedJobState.tone}`}>{mappedJobState.label}</span>
          </div>
          <div className="meta-grid">
            <div>
              <dt>Job-ID</dt>
              <dd>{state.job?.id}</dd>
            </div>
            <div>
              <dt>Fortschritt</dt>
              <dd>{mappedJobState.message}</dd>
            </div>
          </div>
        </section>
      ) : null}

      {state.status === 'success' ? (
        <section className="panel diagnostics-result">
          <div className="panel__header">
            <div>
              <p className="panel__eyebrow">Rebuild-Ergebnis</p>
              <h3>Technische Details</h3>
            </div>
            <div className="search-bar__actions">
              <button type="button" className="button-secondary" onClick={handleCopyDetails}>
                Details kopieren
              </button>
            </div>
          </div>
          <div className="meta-grid">
            <div>
              <dt>Status</dt>
              <dd>{state.result.status}</dd>
            </div>
            <div>
              <dt>Job-ID</dt>
              <dd>{state.job?.id || 'unbekannt'}</dd>
            </div>
            <div>
              <dt>Index-Aktion</dt>
              <dd>{state.result.index_action}</dd>
            </div>
            <div>
              <dt>Dokumente</dt>
              <dd>{state.result.reindexed_document_count}</dd>
            </div>
            <div>
              <dt>Chunks</dt>
              <dd>{state.result.reindexed_chunk_count}</dd>
            </div>
          </div>
          <pre className="diagnostics-code-block">{copyPayload}</pre>
        </section>
      ) : null}
    </section>
  );
}