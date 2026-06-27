import { useSyncExternalStore } from 'react';

import { clearToken, getToken, subscribe } from './authStorage';

export interface AuthState {
  hasToken: boolean;
  logout: () => void;
}

export function useAuth(): AuthState {
  const snapshot = useSyncExternalStore(
    (cb) => subscribe(cb),
    () => Boolean(getToken()),
    () => false
  );
  return {
    hasToken: snapshot,
    logout: clearToken,
  };
}
