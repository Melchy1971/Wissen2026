import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getDocuments, searchChunks } from '../api/documents.js';
import { DocumentTable } from '../components/documents/DocumentTable.jsx';
import { SearchResultList } from '../components/documents/SearchResultList.jsx';
import { EmptyState } from '../components/status/EmptyState.jsx';
import { ErrorState } from '../components/status/ErrorState.jsx';
import { LoadingState } from '../components/status/LoadingState.jsx';
import { mapDocumentListItem, mapError, mapSearchResult } from '../view-models/mappers.js';

export function DocumentsPage() {
  const [searchParams] = useSearchParams();
  const workspaceId = searchParams.get('workspace_id') || '00000000-0000-0000-0000-000000000001';
  const [state, setState] = useState({ status: 'loading', items: [], error: null });
  const [searchState, setSearchState] = useState({ status: 'idle', items: [], error: null, query: '' });
  const [queryInput, setQueryInput] = useState('');

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

  async function handleSearchSubmit(event) {
    event.preventDefault();

    const query = queryInput.trim();
    if (!query) {
      setSearchState({ status: 'idle', items: [], error: null, query: '' });
      return;
    }

    setSearchState({ status: 'loading', items: [], error: null, query });
    try {
      const response = await searchChunks({ workspaceId, query, limit: 10, offset: 0 });
      setSearchState({ status: 'success', items: response.map(mapSearchResult), error: null, query });
    } catch (error) {
      setSearchState({ status: 'error', items: [], error: mapError(error), query });
    }
  }

  function handleSearchReset() {
    setQueryInput('');
    setSearchState({ status: 'idle', items: [], error: null, query: '' });
  }

  if (state.status === 'loading') {
    return <LoadingState label="Dokumente werden geladen..." />;
  }

  if (state.status === 'error') {
    return <ErrorState error={state.error} />;
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
      <section className="panel">
        <div className="panel__header search-bar__header">
          <div>
            <p className="panel__eyebrow">Einfache Suche</p>
            <h3>Chunk-Suche</h3>
          </div>
        </div>
        <form className="search-bar" onSubmit={handleSearchSubmit}>
          <label className="search-bar__field">
            <span className="search-bar__label">Suchbegriff</span>
            <input
              type="search"
              value={queryInput}
              onChange={(event) => setQueryInput(event.target.value)}
              placeholder="z. B. Vertragsentwurf oder Paragraph 5"
            />
          </label>
          <div className="search-bar__actions">
            <button type="submit">Suchen</button>
            <button type="button" className="button-secondary" onClick={handleSearchReset}>Zuruecksetzen</button>
          </div>
        </form>
      </section>

      {searchState.status === 'loading' ? <LoadingState label="Suchtreffer werden geladen..." /> : null}
      {searchState.status === 'error' ? <ErrorState error={searchState.error} /> : null}
      {searchState.status === 'success' && searchState.items.length === 0 ? (
        <EmptyState
          title="Keine Treffer gefunden"
          message={`Fuer \"${searchState.query}\" wurden im aktuellen Workspace keine Chunks gefunden.`}
        />
      ) : null}
      {searchState.status === 'success' && searchState.items.length > 0 ? (
        <SearchResultList items={searchState.items} query={searchState.query} />
      ) : null}
      {state.items.length === 0 ? (
        <EmptyState title="Keine Dokumente vorhanden" message="Fuer diesen Workspace liegen aktuell keine Dokumente vor." />
      ) : (
        <DocumentTable items={state.items} />
      )}
    </section>
  );
}