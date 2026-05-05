import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ChatPage } from '../../pages/ChatPage.jsx';

function renderPage(initialEntry = '/chat/session-1?workspace_id=workspace-1') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:id" element={<ChatPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('ChatPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  it('renders sessions and message history with citations', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([
          {
            id: 'session-1',
            workspace_id: 'workspace-1',
            title: 'Arbeitsvertrag',
            created_at: '2026-05-04T12:00:00Z',
            updated_at: '2026-05-04T12:10:00Z',
            message_count: 2,
            last_user_question_preview: 'Welche Frist gilt?',
          },
        ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'session-1',
          workspace_id: 'workspace-1',
          title: 'Arbeitsvertrag',
          created_at: '2026-05-04T12:00:00Z',
          updated_at: '2026-05-04T12:10:00Z',
          messages: [
            {
              id: 'msg-1',
              role: 'user',
              content: 'Welche Frist gilt?',
              created_at: '2026-05-04T12:05:00Z',
            },
            {
              id: 'msg-2',
              role: 'assistant',
              answer: 'Die Kuendigungsfrist betraegt vier Wochen.',
              created_at: '2026-05-04T12:05:02Z',
              citations: [
                {
                  chunk_id: 'chunk-1',
                  document_id: 'doc-1',
                  document_title: 'Arbeitsvertrag Hybridmodell',
                  source_anchor: { type: 'text', page: null, paragraph: null, char_start: 120, char_end: 240 },
                  quote_preview: 'Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen ...',
                },
              ],
              confidence: {
                sufficient_context: true,
                retrieval_score_max: 0.91,
                retrieval_score_avg: 0.78,
              },
            },
          ],
        }),
      });

    renderPage();

    expect(await screen.findByText('Arbeitsvertrag')).toBeInTheDocument();
    expect(await screen.findByText('Die Kuendigungsfrist betraegt vier Wochen.')).toBeInTheDocument();
    expect(screen.getByText('Arbeitsvertrag Hybridmodell')).toBeInTheDocument();
    expect(screen.getByText(/Chunk: chunk-1/i)).toBeInTheDocument();
  });

  it('creates a new session and sends a question to the real chat api contract', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([]),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'session-2',
          workspace_id: 'workspace-1',
          title: 'Neue Analyse',
          created_at: '2026-05-04T12:00:00Z',
          updated_at: '2026-05-04T12:00:00Z',
          message_count: 0,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([
          {
            id: 'session-2',
            workspace_id: 'workspace-1',
            title: 'Neue Analyse',
            created_at: '2026-05-04T12:00:00Z',
            updated_at: '2026-05-04T12:00:00Z',
            message_count: 0,
            last_user_question_preview: 'Noch keine Frage gestellt',
          },
        ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'session-2',
          workspace_id: 'workspace-1',
          title: 'Neue Analyse',
          created_at: '2026-05-04T12:00:00Z',
          updated_at: '2026-05-04T12:00:00Z',
          messages: [],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'msg-assistant-1',
          session_id: 'session-2',
          role: 'assistant',
          content: 'Vier Wochen zum Monatsende. Quelle: chunk-1',
          basis_type: 'knowledge_base',
          created_at: '2026-05-04T12:05:02Z',
          citations: [
            {
              chunk_id: 'chunk-1',
              document_id: 'doc-1',
              source_anchor: {
                type: 'text',
                page: null,
                paragraph: 4,
                char_start: 10,
                char_end: 120,
              },
              quote_preview: 'Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen.',
            },
          ],
          confidence: {
            sufficient_context: true,
            retrieval_score_max: 0.91,
            retrieval_score_avg: 0.91,
          },
        }),
      });

    renderPage('/chat?workspace_id=workspace-1');

    expect(await screen.findByText('Keine Chat-Sitzungen vorhanden')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/vertragsanalyse mai/i), {
      target: { value: 'Neue Analyse' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Neue Sitzung' }));

    await waitFor(() => {
      expect(screen.getByText('Neue Analyse')).toBeInTheDocument();
    });
    expect(await screen.findByRole('button', { name: 'Frage senden' })).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/frage an den dokumentbestand stellen/i), {
      target: { value: 'Welche Frist gilt?' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Frage senden' }));

    expect(await screen.findByText('Welche Frist gilt?')).toBeInTheDocument();
    expect(await screen.findByText('Vier Wochen zum Monatsende. Quelle: chunk-1')).toBeInTheDocument();
    expect(screen.getByText('Unbenanntes Dokument')).toBeInTheDocument();
    expect(screen.getByText(/Chunk: chunk-1/i)).toBeInTheDocument();

    const messageRequest = JSON.parse(globalThis.fetch.mock.calls.at(-1)[1].body);
    expect(messageRequest).toEqual({
      workspace_id: 'workspace-1',
      question: 'Welche Frist gilt?',
      retrieval_limit: 8,
    });
  });

  it('renders insufficient context with exact error format', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ([
          {
            id: 'session-1',
            workspace_id: 'workspace-1',
            title: 'Arbeitsvertrag',
            created_at: '2026-05-04T12:00:00Z',
            updated_at: '2026-05-04T12:10:00Z',
          },
        ]),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'session-1',
          workspace_id: 'workspace-1',
          title: 'Arbeitsvertrag',
          created_at: '2026-05-04T12:00:00Z',
          updated_at: '2026-05-04T12:10:00Z',
          messages: [],
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          error: {
            code: 'INSUFFICIENT_CONTEXT',
            message: 'no_retrieval_hits',
            details: { session_id: 'session-1' },
          },
        }),
      });

    renderPage();

    expect(await screen.findByText('Arbeitsvertrag')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText(/frage an den dokumentbestand stellen/i), {
      target: { value: 'Welche Frist gilt?' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Frage senden' }));

    expect(await screen.findByText('Zu wenig Kontext')).toBeInTheDocument();
    expect(screen.getByText('no_retrieval_hits')).toBeInTheDocument();
    expect(screen.getByText(/Fehlercode: INSUFFICIENT_CONTEXT/i)).toBeInTheDocument();
  });

  it.each([
    ['CHAT_SESSION_NOT_FOUND', 'Chat-Sitzung nicht gefunden', 404],
    ['RETRIEVAL_FAILED', 'Retrieval fehlgeschlagen', 502],
    ['LLM_UNAVAILABLE', 'LLM nicht verfuegbar', 503],
  ])('renders %s with visible code', async (code, title, status) => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status,
      statusText: 'API Error',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error: { code, message: `${code} message`, details: {} } }),
    });

    renderPage('/chat?workspace_id=workspace-1');

    await waitFor(() => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
    expect(screen.getByText(`${code} message`)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(`Fehlercode: ${code}`, 'i'))).toBeInTheDocument();
  });
});
