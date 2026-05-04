import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { DocumentDetailPage } from '../../pages/DocumentDetailPage.jsx';

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/documents/doc-1?workspace_id=workspace-1']}>
      <Routes>
        <Route path="/documents/:id" element={<DocumentDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('DocumentDetailPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders metadata, versions and chunk previews', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'doc-1',
          workspace_id: 'workspace-1',
          owner_user_id: 'user-1',
          title: 'Dokument A',
          source_type: 'upload',
          mime_type: 'text/plain',
          content_hash: 'hash-1',
          created_at: '2026-05-01T10:00:00',
          updated_at: '2026-05-01T10:10:00',
          latest_version_id: 'ver-1',
          parser_metadata: { parser_version: '1.0', ocr_used: false, ki_provider: null, ki_model: null, metadata: {} },
          import_status: 'chunked',
          chunk_summary: { chunk_count: 1, total_chars: 120, first_chunk_id: 'chunk-1', last_chunk_id: 'chunk-1' },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([{ id: 'ver-1', version_number: 1, created_at: '2026-05-01T10:00:00', content_hash: 'hash-v1' }]),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([{ chunk_id: 'chunk-1', position: 0, text_preview: 'Preview', source_anchor: { type: 'text', char_start: 0, char_end: 50 } }]),
      });

    renderPage();

    expect(await screen.findAllByText('Dokument A')).toHaveLength(2);
    expect(screen.getByText('v1')).toBeInTheDocument();
    expect(screen.getByText('Preview')).toBeInTheDocument();
  });

  it('renders API errors visibly', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error: { code: 'DOCUMENT_NOT_FOUND', message: 'Document not found', details: {} } }),
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Dokument nicht gefunden')).toBeInTheDocument();
    });
    expect(screen.getByText(/Fehlercode: DOCUMENT_NOT_FOUND/i)).toBeInTheDocument();
  });
});