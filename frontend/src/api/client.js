const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const AUTH_TOKEN_STORAGE_KEY = 'wissen.authToken';
const WORKSPACE_ID_STORAGE_KEY = 'wissen.workspaceId';
const memoryRequestContext = new Map();

function getStorage() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return null;
  }

  const storage = window.localStorage;
  if (typeof storage.getItem !== 'function' || typeof storage.setItem !== 'function' || typeof storage.removeItem !== 'function') {
    return null;
  }

  return storage;
}

function readStoredValue(key, fallback = '') {
  const storage = getStorage();
  if (storage) {
    return storage.getItem(key) || fallback;
  }

  return memoryRequestContext.get(key) || fallback;
}

export function getApiRequestContext() {
  const authToken = readStoredValue(AUTH_TOKEN_STORAGE_KEY, import.meta.env.VITE_AUTH_TOKEN || '');
  const workspaceId = readStoredValue(WORKSPACE_ID_STORAGE_KEY, import.meta.env.VITE_WORKSPACE_ID || '');

  return {
    authToken: authToken.trim(),
    workspaceId: workspaceId.trim(),
  };
}

export function setApiRequestContext({ authToken = '', workspaceId = '' }) {
  const storage = getStorage();

  if (authToken.trim()) {
    if (storage) {
      storage.setItem(AUTH_TOKEN_STORAGE_KEY, authToken.trim());
    }
    memoryRequestContext.set(AUTH_TOKEN_STORAGE_KEY, authToken.trim());
  } else {
    if (storage) {
      storage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    }
    memoryRequestContext.delete(AUTH_TOKEN_STORAGE_KEY);
  }

  if (workspaceId.trim()) {
    if (storage) {
      storage.setItem(WORKSPACE_ID_STORAGE_KEY, workspaceId.trim());
    }
    memoryRequestContext.set(WORKSPACE_ID_STORAGE_KEY, workspaceId.trim());
  } else {
    if (storage) {
      storage.removeItem(WORKSPACE_ID_STORAGE_KEY);
    }
    memoryRequestContext.delete(WORKSPACE_ID_STORAGE_KEY);
  }
}

function buildRequestHeaders(optionsHeaders = {}) {
  const requestContext = getApiRequestContext();
  const headers = {
    Accept: 'application/json',
    ...optionsHeaders,
  };

  if (requestContext.authToken && !headers.Authorization) {
    headers.Authorization = `Bearer ${requestContext.authToken}`;
  }
  if (requestContext.workspaceId && !headers['X-Workspace-Id']) {
    headers['X-Workspace-Id'] = requestContext.workspaceId;
  }

  return headers;
}

export class ApiClientError extends Error {
  constructor({ code, message, details, status }) {
    super(message || 'API request failed');
    this.name = 'ApiClientError';
    this.code = code || 'UNKNOWN_ERROR';
    this.details = details || {};
    this.status = status ?? null;
  }
}

export async function requestJson(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: buildRequestHeaders(options.headers || {}),
      ...options,
    });
  } catch (error) {
    throw new ApiClientError({
      code: 'NETWORK_ERROR',
      message: 'API is not reachable',
      details: { cause: error instanceof Error ? error.message : String(error) },
      status: null,
    });
  }

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const errorPayload = payload?.error;
    throw new ApiClientError({
      code: errorPayload?.code || (response.status === 503 ? 'SERVICE_UNAVAILABLE' : 'HTTP_ERROR'),
      message: errorPayload?.message || response.statusText || 'API request failed',
      details: errorPayload?.details || {},
      status: response.status,
    });
  }

  return payload;
}