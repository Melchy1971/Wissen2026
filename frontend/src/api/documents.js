import { requestJson } from './client.js';

export function getDocuments({ workspaceId, limit = 20, offset = 0, lifecycleStatus } = {}) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  if (lifecycleStatus) {
    query.set('lifecycle_status', lifecycleStatus);
  }

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

export function searchChunks({ workspaceId, query, limit = 20, offset = 0 }) {
  const search = new URLSearchParams({
    q: query,
    limit: String(limit),
    offset: String(offset),
  });

  return requestJson(`/api/v1/search/chunks?${search.toString()}`);
}

export function importDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  return requestJson('/documents/import', {
    method: 'POST',
    body: formData,
  });
}

export function archiveDocument(id) {
  return requestJson(`/documents/${id}/archive`, {
    method: 'PATCH',
  });
}

export function restoreDocument(id) {
  return requestJson(`/documents/${id}/restore`, {
    method: 'PATCH',
  });
}

export function deleteDocument(id) {
  return requestJson(`/documents/${id}`, {
    method: 'DELETE',
  });
}