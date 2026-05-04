import { requestJson } from './client.js';

export function getChatSessions({ workspaceId, limit = 20, offset = 0 }) {
  const query = new URLSearchParams({
    workspace_id: workspaceId,
    limit: String(limit),
    offset: String(offset),
  });

  return requestJson(`/api/v1/chat/sessions?${query.toString()}`);
}

export function createChatSession({ workspaceId, title }) {
  return requestJson('/api/v1/chat/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      workspace_id: workspaceId,
      title,
    }),
  });
}

export function getChatSession(id) {
  return requestJson(`/api/v1/chat/sessions/${id}`);
}

export function postChatMessage(id, { workspaceId, question, retrievalLimit = 8 }) {
  return requestJson(`/api/v1/chat/sessions/${id}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      workspace_id: workspaceId,
      question,
      retrieval_limit: retrievalLimit,
    }),
  });
}