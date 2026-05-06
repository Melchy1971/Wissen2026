import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { getApiRequestContext, setApiRequestContext } from '../api/client.js';

const AUTH_STATE_STORAGE_KEY = 'wissen.authState';

const AuthContext = createContext(null);

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

function normalizeAuthState(value = {}) {
  return {
    token: typeof value.token === 'string' ? value.token.trim() : '',
    user: value.user && typeof value.user === 'object' ? value.user : null,
    active_workspace_id: typeof value.active_workspace_id === 'string' ? value.active_workspace_id.trim() : '',
    memberships: Array.isArray(value.memberships) ? value.memberships : [],
  };
}

function readStoredAuthState() {
  const storage = getStorage();
  const requestContext = getApiRequestContext();

  if (!storage) {
    return normalizeAuthState({
      token: requestContext.authToken,
      active_workspace_id: requestContext.workspaceId,
    });
  }

  const rawState = storage.getItem(AUTH_STATE_STORAGE_KEY);
  if (!rawState) {
    return normalizeAuthState({
      token: requestContext.authToken,
      active_workspace_id: requestContext.workspaceId,
    });
  }

  try {
    return normalizeAuthState(JSON.parse(rawState));
  } catch {
    return normalizeAuthState({
      token: requestContext.authToken,
      active_workspace_id: requestContext.workspaceId,
    });
  }
}

export function AuthProvider({ children, initialAuthState = null }) {
  const [authState, setAuthState] = useState(() => normalizeAuthState(initialAuthState || readStoredAuthState()));

  useEffect(() => {
    const normalizedState = normalizeAuthState(authState);
    setApiRequestContext({
      authToken: normalizedState.token,
      workspaceId: normalizedState.active_workspace_id,
    });

    const storage = getStorage();
    if (!storage) {
      return;
    }

    storage.setItem(AUTH_STATE_STORAGE_KEY, JSON.stringify(normalizedState));
  }, [authState]);

  const value = useMemo(() => ({
    ...authState,
    setAuthState(nextState) {
      setAuthState(normalizeAuthState(nextState));
    },
    updateAuthState(partialState) {
      setAuthState((current) => normalizeAuthState({ ...current, ...partialState }));
    },
    clearAuthState() {
      setAuthState(normalizeAuthState());
    },
  }), [authState]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}