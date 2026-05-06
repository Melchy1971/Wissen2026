import { requestJson } from './client.js';

export async function rebuildSearchIndex() {
  return requestJson('/api/v1/admin/search-index/rebuild', {
    method: 'POST',
  });
}