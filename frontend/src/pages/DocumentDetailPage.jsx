import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';

import { getDocumentChunks, getDocumentDetail, getDocumentVersions } from '../api/documents.js';
import { ChunkPreviewList } from '../components/documents/ChunkPreviewList.jsx';
import { DocumentMetaCard } from '../components/documents/DocumentMetaCard.jsx';
import { VersionList } from '../components/documents/VersionList.jsx';
import { EmptyState } from '../components/status/EmptyState.jsx';
import { ErrorState } from '../components/status/ErrorState.jsx';
import { LoadingState } from '../components/status/LoadingState.jsx';
import { mapDocumentDetail, mapError } from '../view-models/mappers.js';

export function DocumentDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const workspaceId = searchParams.get('workspace_id') || '';
  const [state, setState] = useState({ status: 'loading', document: null, error: null });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: 'loading', document: null, error: null });
      try {
        const [detail, versions, chunks] = await Promise.all([
          getDocumentDetail(id),
          getDocumentVersions(id),
          getDocumentChunks(id, { limit: 5 }),
        ]);
        if (cancelled) return;
        setState({ status: 'success', document: mapDocumentDetail(detail, versions, chunks), error: null });
      } catch (error) {
        if (cancelled) return;
        setState({ status: 'error', document: null, error: mapError(error) });
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (state.status === 'loading') {
    return <LoadingState label="Dokumentdetail wird geladen..." />;
  }

  if (state.status === 'error') {
    return <ErrorState error={state.error} />;
  }

  if (!state.document) {
    return <EmptyState title="Kein Dokument geladen" message="Das angeforderte Dokument konnte nicht dargestellt werden." />;
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <Link className="back-link" to={`/documents${workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ''}`}>
            Zur Dokumentliste
          </Link>
          <h2>{state.document.title}</h2>
        </div>
      </div>
      <DocumentMetaCard document={state.document} />
      <div className="detail-grid">
        <VersionList items={state.document.versions} />
        <ChunkPreviewList items={state.document.chunks} />
      </div>
    </div>
  );
}