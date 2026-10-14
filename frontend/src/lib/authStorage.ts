/**
 * Token storage.
 *
 * Where the token lives depends on the "Remember me" choice at sign-in:
 * - remembered → localStorage: survives closing the browser and is shared
 *   by every tab, so opening a link in a new tab doesn't ask again. Meant
 *   for the owner's own device; the server issues a longer-lived token.
 * - not remembered → sessionStorage: this tab only, gone when it closes.
 *
 * A token is only ever in one of the two; signing out, expiry and a token
 * the server rejects all wipe both. An in-memory cache avoids a storage
 * read on every request.
 *
 * Subscribers (the auth-aware app shell) get notified when the token
 * changes so React can re-render — including when it expires while the
 * app sits open, and when another tab signs in or out.
 */

const TOKEN_KEY = 'mentor.access_token';
const EXPIRY_KEY = 'mentor.token_expires_at';

// setTimeout overflows past ~24.8 days (2^31-1 ms) and fires at once, so a
// 30-day token re-arms the expiry check at most this far ahead.
const MAX_TIMER_MS = 24 * 60 * 60 * 1000;

interface StoredToken {
  token: string;
  expiresAt: number;
}

export type SignOutReason = 'signed-out' | 'expired';

// undefined = not read from storage yet; null = signed out.
let cached: StoredToken | null | undefined;
let lastSignOut: SignOutReason | null = null;
let expiryTimer: ReturnType<typeof setTimeout> | undefined;
const listeners = new Set<() => void>();

function notify(): void {
  listeners.forEach((fn) => fn());
}

function storages(): Storage[] {
  return [sessionStorage, localStorage];
}

function readFrom(store: Storage): StoredToken | null {
  const token = store.getItem(TOKEN_KEY);
  const expiresAt = Number(store.getItem(EXPIRY_KEY));
  // A token without a readable expiry counts as absent, never as "forever".
  if (!token || !Number.isFinite(expiresAt) || expiresAt <= 0) return null;
  return { token, expiresAt };
}

function removeFrom(store: Storage): void {
  try {
    store.removeItem(TOKEN_KEY);
    store.removeItem(EXPIRY_KEY);
  } catch {
    // Storage may be unavailable (private mode, sandbox); nothing to remove.
  }
}

function hydrate(): StoredToken | null {
  if (cached !== undefined) return cached;
  cached = null;
  for (const store of storages()) {
    try {
      cached = readFrom(store);
    } catch {
      // Storage may be unavailable; try the other one, else signed out.
    }
    if (cached) break;
  }
  armExpiryTimer();
  return cached;
}

function armExpiryTimer(): void {
  clearTimeout(expiryTimer);
  expiryTimer = undefined;
  if (!cached) return;
  const delay = Math.min(Math.max(cached.expiresAt - Date.now(), 0), MAX_TIMER_MS);
  expiryTimer = setTimeout(() => {
    // getToken() ends the session (and notifies) if it's due; otherwise
    // re-arm for the time that's left.
    if (getToken()) armExpiryTimer();
  }, delay);
}

function endSession(reason: SignOutReason, deferNotify = false): void {
  cached = null;
  lastSignOut = reason;
  armExpiryTimer();
  storages().forEach(removeFrom);
  if (deferNotify) queueMicrotask(notify);
  else notify();
}

export function getToken(): string | null {
  const current = hydrate();
  if (current && current.expiresAt <= Date.now()) {
    // Also called from React's snapshot read, so don't notify mid-render;
    // subscribers re-render on the next microtask.
    endSession('expired', true);
    return null;
  }
  return current?.token ?? null;
}

export function setToken(token: string, expiresAt: Date, remember: boolean): void {
  cached = { token, expiresAt: expiresAt.getTime() };
  lastSignOut = null;
  const [keep, drop] = remember
    ? [localStorage, sessionStorage]
    : [sessionStorage, localStorage];
  removeFrom(drop);
  try {
    keep.setItem(TOKEN_KEY, token);
    keep.setItem(EXPIRY_KEY, String(cached.expiresAt));
  } catch {
    // Storage unavailable: the in-memory copy still signs this tab in.
  }
  armExpiryTimer();
  notify();
}

/** Ends the session: drops the token from memory and from both storages. */
export function clearToken(reason: SignOutReason = 'signed-out'): void {
  endSession(reason);
}

/** Why the last session ended, so the login form can say it expired. */
export function lastSignOutReason(): SignOutReason | null {
  return lastSignOut;
}

export function subscribe(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

if (typeof window !== 'undefined') {
  // Another tab signed in with "Remember me", or signed out: follow it.
  window.addEventListener('storage', (event) => {
    if (event.storageArea !== localStorage || event.key !== TOKEN_KEY) return;
    if (event.newValue === null) {
      endSession('signed-out');
    } else {
      cached = undefined;
      hydrate();
      notify();
    }
  });
  // Timers are throttled in background tabs and paused while a laptop
  // sleeps; re-check as soon as the app is looked at again.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') getToken();
  });
}
