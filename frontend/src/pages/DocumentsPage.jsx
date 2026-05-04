import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getDocuments } from '../api/documents.js';
import { DocumentTable } from '../components/documents/DocumentTable.jsx';
import { EmptyState } from '../components/status/EmptyState.jsx';
import { ErrorState } from '../components/status/ErrorState.jsx';
import { LoadingState } from '../components/status/LoadingState.jsx';
import { mapDocumentListItem, mapError } from '../view-models/mappers.js';

export function DocumentsPage() {
  const [searchParams] = useSearchParams();
  const workspaceId = searchParams.get('workspace_id') || '00000000-0000-0000-0000-000000000001';
  const [state, setState] = useState({ status: 'loading', items: [], error: null });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: 'loading', items: [], error: null });
      try {
        const response = await getDocuments({ workspaceId, limit: 20, offset: 0 });
        if (cancelled) return;
        const items = response.map(mapDocumentListItem);
        setState({ status: 'success', items, error: null });
      } catch (error) {
        if (cancelled) return;
        setState({ status: 'error', items: [], error: mapError(error) });
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  if (state.status === 'loading') {
    return <LoadingState label="Dokumente werden geladen..." />;
  }

  if (state.status === 'error') {
    return <ErrorState error={state.error} />;
  }

  if (state.items.length === 0) {
    return <EmptyState title="Keine Dokumente vorhanden" message="Fuer diesen Workspace liegen aktuell keine Dokumente vor." />;
  }

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <p className="panel__eyebrow">Dokumentuebersicht</p>
          <h2>Dokumente</h2>
        </div>
        <p className="page-header__meta">Workspace: {workspaceId}</p>
      </div>
      <DocumentTable items={state.items} />
    </section>
  );
}