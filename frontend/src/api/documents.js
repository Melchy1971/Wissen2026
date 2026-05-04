import { requestJson } from './client.js';

export function getDocuments({ workspaceId, limit = 20, offset = 0 }) {
  const query = new URLSearchParams({
    workspace_id: workspaceId,
    limit: String(limit),
    offset: String(offset),
  });

  return requestJson(`/documents?${query.toString()}`);
}

export function getDocumentDetail(id) {
  return requestJson(`/documents/${id}`);
}

export function getDocumentVersions(id) {
  return requestJson(`/documents/${id}/versions`);
}

export function getDocumentChunks(id, { limit } = {}) {
  const query = new URLSearchParams();
  if (limit != null) {
    query.set('limit', String(limit));
  }

  const suffix = query.size > 0 ? `?${query.toString()}` : '';
  return requestJson(`/documents/${id}/chunks${suffix}`);
}