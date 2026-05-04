import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { DocumentsPage } from '../../pages/DocumentsPage.jsx';

function renderPage(initialEntry = '/documents?workspace_id=workspace-1') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/documents" element={<DocumentsPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('DocumentsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders documents from the API', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ([
        {
          id: 'doc-1',
          title: 'Vertragsentwurf',
          mime_type: 'text/plain',
          created_at: '2026-05-01T10:00:00',
          updated_at: '2026-05-01T10:10:00',
          latest_version_id: 'ver-1',
          import_status: 'chunked',
          version_count: 1,
          chunk_count: 2,
        },
      ]),
    });

    renderPage();

    expect(screen.getByText(/Dokumente werden geladen/i)).toBeInTheDocument();
    expect(await screen.findByText('Vertragsentwurf')).toBeInTheDocument();
    expect(screen.getByText('Lesbar')).toBeInTheDocument();
  });

  it('renders empty state for an empty list', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ([]),
    });

    renderPage();

    expect(await screen.findByText('Keine Dokumente vorhanden')).toBeInTheDocument();
  });

  it('renders visible error code on API errors', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error: { code: 'SERVICE_UNAVAILABLE', message: 'Service unavailable', details: {} } }),
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Service nicht verfuegbar')).toBeInTheDocument();
    });
    expect(screen.getByText(/Fehlercode: SERVICE_UNAVAILABLE/i)).toBeInTheDocument();
  });
});