import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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
    cleanup();
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

  it('renders search results with preview and source anchor', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
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
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([
          {
            document_id: 'doc-1',
            document_title: 'Vertragsentwurf',
            document_version_id: 'ver-1',
            version_number: 1,
            chunk_id: 'chunk-1',
            position: 0,
            text_preview: 'Abschnitt mit Suchtreffer',
            source_anchor: {
              type: 'text',
              page: null,
              paragraph: null,
              char_start: 10,
              char_end: 42,
            },
            rank: 0.91,
          },
        ]),
      });

    renderPage();

    expect(await screen.findByText('Vertragsentwurf')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/vertragsentwurf oder paragraph 5/i), {
      target: { value: 'vertragsentwurf' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Suchen' }));

    expect(await screen.findByText(/Treffer fuer/i)).toBeInTheDocument();
    expect(screen.getByText('Abschnitt mit Suchtreffer')).toBeInTheDocument();
    expect(screen.getByText(/Quelle: text \| Zeichen 10-42/i)).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Vertragsentwurf' })[0]).toHaveAttribute(
      'href',
      '/documents/doc-1?workspace_id=workspace-1',
    );
  });

  it('renders empty search state when no results are found', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([]),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([]),
      });

    renderPage();

    expect(await screen.findByText('Keine Dokumente vorhanden')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/vertragsentwurf oder paragraph 5/i), {
      target: { value: 'foo' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Suchen' }));

    expect(await screen.findByText('Keine Treffer gefunden')).toBeInTheDocument();
  });

  it('renders search error state when search api fails', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([]),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ error: { code: 'INVALID_QUERY', message: 'Invalid search query', details: {} } }),
      });

    renderPage();

    expect(await screen.findByText('Keine Dokumente vorhanden')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/vertragsentwurf oder paragraph 5/i), {
      target: { value: '***' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Suchen' }));

    expect(await screen.findByText('Ungueltige Suche')).toBeInTheDocument();
    expect(screen.getByText(/Fehlercode: INVALID_QUERY/i)).toBeInTheDocument();
  });
});