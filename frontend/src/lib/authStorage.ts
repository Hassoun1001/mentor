/**
 * Token storage.
 *
 * We use sessionStorage (cleared on tab close) + an in-memory cache.
 * - sessionStorage > localStorage because it's tab-scoped — a stolen
 *   localStorage token survives logout from other tabs; sessionStorage
 *   doesn't.
 * - The in-memory cache avoids a sessionStorage read on every request.
 *
 * Subscribers (the auth-aware app shell) get notified when the token
 * changes so React can re-render.
 */

const TOKEN_KEY = 'mentor.access_token';
const EXPIRY_KEY = 'mentor.token_expires_at';

let cachedToken: string | null = null;
let cachedExpiresAt: number | null = null;
const listeners = new Set<() => void>();

function notify(): void {
  listeners.forEach((fn) => fn());
}

function hydrate(): void {
  if (cachedToken !== null) return;
  try {
    cachedToken = sessionStorage.getItem(TOKEN_KEY);
    const expiry = sessionStorage.getItem(EXPIRY_KEY);
    cachedExpiresAt = expiry ? Number(expiry) : null;
  } catch {
    // sessionStorage may be unavailable (SSR, sandbox); fail open.
    cachedToken = null;
    cachedExpiresAt = null;
  }
}

export function getToken(): string | null {
  hydrate();
  if (cachedExpiresAt && cachedExpiresAt < Date.now()) {
    clearToken();
    return null;
  }
  return cachedToken;
}

export function setToken(token: string, expiresAt: Date): void {
  cachedToken = token;
  cachedExpiresAt = expiresAt.getTime();
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(EXPIRY_KEY, String(cachedExpiresAt));
  } catch {
    /* ignore */
  }
  notify();
}

export function clearToken(): void {
  cachedToken = null;
  cachedExpiresAt = null;
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(EXPIRY_KEY);
  } catch {
    /* ignore */
  }
  notify();
}

export function subscribe(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
