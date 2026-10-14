import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import { getAuthStatus, login } from '../api/auth';
import { Logo } from '../components/Logo';
import { lastSignOutReason, setToken } from '../lib/authStorage';

export function LoginPage() {
  const [username, setUsername] = useState('mentor');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  // Same query (and cache entry) the app shell uses for its auth gate.
  const status = useQuery({
    queryKey: ['auth-status'],
    queryFn: getAuthStatus,
    staleTime: 60_000,
  });
  const rememberDays = status.data?.remember_me_days;
  const [expired] = useState(() => lastSignOutReason() === 'expired');

  const mutation = useMutation({
    mutationFn: (vars: { u: string; p: string; remember: boolean }) =>
      login(vars.u, vars.p, vars.remember),
    onSuccess: (result, vars) => {
      setToken(result.access_token, new Date(result.expires_at), vars.remember);
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        className="panel-pad w-full max-w-sm space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate({ u: username, p: password, remember: rememberMe });
        }}
      >
        <div>
          <div className="flex items-center gap-3">
            <Logo size={36} />
            <div className="text-xl font-semibold tracking-tight">Mentor</div>
          </div>
          <p className="mt-2 text-xs text-mentor-muted">
            Your always-on trading mentor. Sign in to continue.
          </p>
        </div>

        <div>
          <label className="label">Username</label>
          <input
            className="input"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="label">Password</label>
          <input
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <label className="flex items-start gap-2 text-sm text-mentor-fg">
          <input
            type="checkbox"
            className="mt-0.5"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
          />
          <span>
            Remember me on this device
            <span className="mt-0.5 block text-xs text-mentor-muted">
              Stays signed in
              {rememberDays ? ` for ${rememberDays} days` : ''}, even after closing the
              browser. Only tick this on your own phone or computer — untick it on a
              shared one.
            </span>
          </span>
        </label>

        {expired && !mutation.error && (
          <div className="rounded-lg border border-mentor-border bg-mentor-panelLight/40 p-3 text-sm text-mentor-muted">
            Your sign-in expired. Please sign in again.
          </div>
        )}

        {mutation.error instanceof ApiError && (
          <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
            {mutation.error.message}
          </div>
        )}

        <button
          type="submit"
          disabled={mutation.isPending || !password}
          className="btn-primary w-full"
        >
          {mutation.isPending ? 'Signing in…' : 'Sign in'}
        </button>

        <p className="text-xs text-mentor-muted">
          First time? Generate a password hash on the backend with{' '}
          <code className="font-mono text-mentor-fg/80">
            python -m mentor.cli.hash_password
          </code>{' '}
          then put the result in <code className="font-mono">MENTOR_AUTH_PASSWORD_HASH</code>.
        </p>
      </form>
    </div>
  );
}
