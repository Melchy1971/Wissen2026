const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

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
      headers: {
        Accept: 'application/json',
        ...(options.headers || {}),
      },
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