import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import { login } from '../api/auth';
import { Logo } from '../components/Logo';
import { setToken } from '../lib/authStorage';

export function LoginPage() {
  const [username, setUsername] = useState('mentor');
  const [password, setPassword] = useState('');

  const mutation = useMutation({
    mutationFn: ({ u, p }: { u: string; p: string }) => login(u, p),
    onSuccess: (result) => {
      setToken(result.access_token, new Date(result.expires_at));
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        className="panel-pad w-full max-w-sm space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate({ u: username, p: password });
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
