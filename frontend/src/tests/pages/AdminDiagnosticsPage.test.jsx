import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider } from '../../auth/AuthContext.jsx';
import { AdminDiagnosticsPage } from '../../pages/AdminDiagnosticsPage.jsx';

function renderPage(initialAuthState = { token: 'test-token', user: null, active_workspace_id: 'workspace-1', memberships: [{ workspace_id: 'workspace-1', role: 'owner' }] }) {
  return render(
    <AuthProvider initialAuthState={initialAuthState}>
      <MemoryRouter initialEntries={['/admin/diagnostics']}>
        <Routes>
          <Route path="/admin/diagnostics" element={<AdminDiagnosticsPage />} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

describe('AdminDiagnosticsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  it('renders diagnostics rebuild action', async () => {
    renderPage();

    expect(screen.getByText('Admin-Diagnostik')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Search Index neu aufbauen/i })).toBeInTheDocument();
    expect(screen.getByText(/Keine Aktion ausgefuehrt/i)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/x-admin-token/i)).not.toBeInTheDocument();
  });

  it('executes rebuild and renders copyable technical details', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'job-1',
          job_type: 'search_index_rebuild',
          status: 'queued',
          workspace_id: 'workspace-1',
          requested_by_user_id: null,
          filename: null,
          created_at: '2026-05-05T00:00:00Z',
          started_at: null,
          finished_at: null,
          progress_current: 0,
          progress_total: 1,
          progress_message: 'Rebuild ist in Warteschlange',
          error_code: null,
          error_message: null,
          result: null,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'job-1',
          job_type: 'search_index_rebuild',
          status: 'completed',
          workspace_id: 'workspace-1',
          requested_by_user_id: null,
          filename: null,
          created_at: '2026-05-05T00:00:00Z',
          started_at: '2026-05-05T00:00:01Z',
          finished_at: '2026-05-05T00:00:02Z',
          progress_current: 1,
          progress_total: 1,
          progress_message: 'Search-Index-Rebuild abgeschlossen',
          error_code: null,
          error_message: null,
          result: {
            workspace_id: 'workspace-1',
            reindexed_chunk_count: 12,
            reindexed_document_count: 3,
            index_name: 'ix_document_chunks_search_vector',
            index_action: 'reindexed',
            status: 'completed',
          },
        }),
      });
    const clipboardWriteText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText: clipboardWriteText } });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /Search Index neu aufbauen/i }));

    expect(await screen.findByText('Technische Details')).toBeInTheDocument();
    expect(screen.getByText('reindexed')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('job-1')).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);

    fireEvent.click(screen.getByRole('button', { name: /Details kopieren/i }));
    await waitFor(() => {
      expect(clipboardWriteText).toHaveBeenCalledTimes(1);
    });
    expect(clipboardWriteText.mock.calls[0][0]).toContain('"reindexed_chunk_count": 12');
  });

  it('shows API errors when rebuild fails', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'job-1',
          job_type: 'search_index_rebuild',
          status: 'queued',
          workspace_id: 'workspace-1',
          requested_by_user_id: null,
          filename: null,
          created_at: '2026-05-05T00:00:00Z',
          started_at: null,
          finished_at: null,
          progress_current: 0,
          progress_total: 1,
          progress_message: 'Rebuild ist in Warteschlange',
          error_code: null,
          error_message: null,
          result: null,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'job-1',
          job_type: 'search_index_rebuild',
          status: 'failed',
          workspace_id: 'workspace-1',
          requested_by_user_id: null,
          filename: null,
          created_at: '2026-05-05T00:00:00Z',
          started_at: '2026-05-05T00:00:01Z',
          finished_at: '2026-05-05T00:00:02Z',
          progress_current: 1,
          progress_total: 1,
          progress_message: 'Search-Index-Rebuild fehlgeschlagen',
          error_code: 'ADMIN_REQUIRED',
          error_message: 'Admin access required',
          result: null,
        }),
      });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /Search Index neu aufbauen/i }));

    expect(await screen.findByText(/Admin-Zugriff erforderlich/i)).toBeInTheDocument();
    expect(screen.getByText(/Fehlercode: ADMIN_REQUIRED/i)).toBeInTheDocument();
  });

  it('renders normalized queued rebuild job status labels', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'job-1',
          job_type: 'search_index_rebuild',
          status: 'queued',
          workspace_id: 'workspace-1',
          requested_by_user_id: null,
          filename: null,
          created_at: '2026-05-05T00:00:00Z',
          started_at: null,
          finished_at: null,
          progress_current: 0,
          progress_total: 1,
          progress_message: null,
          error_code: null,
          error_message: null,
          result: null,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 'job-1',
          job_type: 'search_index_rebuild',
          status: 'queued',
          workspace_id: 'workspace-1',
          requested_by_user_id: null,
          filename: null,
          created_at: '2026-05-05T00:00:00Z',
          started_at: null,
          finished_at: null,
          progress_current: 0,
          progress_total: 1,
          progress_message: null,
          error_code: null,
          error_message: null,
          result: null,
        }),
      });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /Search Index neu aufbauen/i }));

    expect(await screen.findByText('In Warteschlange')).toBeInTheDocument();
    expect(screen.getByText('Rebuild wartet auf Ausfuehrung.')).toBeInTheDocument();
  });

  it('blocks rebuild in the UI when the active workspace membership is not admin-capable', async () => {
    renderPage({
      token: 'test-token',
      user: null,
      active_workspace_id: 'workspace-1',
      memberships: [{ workspace_id: 'workspace-1', role: 'member' }],
    });

    expect(screen.getByRole('button', { name: /Search Index neu aufbauen/i })).toBeDisabled();
    expect(screen.getByText(/keine Adminrolle im aktiven Workspace/i)).toBeInTheDocument();
  });
});