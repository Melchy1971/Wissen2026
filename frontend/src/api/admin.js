import { requestJson } from './client.js';

export async function rebuildSearchIndex({ adminToken, workspaceId }) {
  const params = new URLSearchParams();
  if (workspaceId?.trim()) {
    params.set('workspace_id', workspaceId.trim());
  }

  const suffix = params.toString() ? `?${params.toString()}` : '';
  return requestJson(`/api/v1/admin/search-index/rebuild${suffix}`, {
    method: 'POST',
    headers: {
      'x-admin-token': adminToken,
    },
  });
}