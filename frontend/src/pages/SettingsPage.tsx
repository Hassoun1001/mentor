import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  type UserDto,
  changePassword,
  createUser,
  deleteUser,
  getMe,
  listUsers,
  updateUserTabs,
} from '../api/auth';
import { ApiError } from '../api/client';

const TAB_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  forecast: 'Forecast',
  system: 'System',
  loop: 'Loop',
  trade: 'Trade',
  tips: 'Tips',
  risk: 'Risk',
  journal: 'Journal',
  lessons: 'Lessons',
  prices: 'Prices',
  data: 'Data',
  backtest: 'Backtester',
};

function errMsg(e: unknown): string {
  return e instanceof ApiError ? e.message : 'something went wrong';
}

export function SettingsPage() {
  const me = useQuery({ queryKey: ['me'], queryFn: getMe });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Settings</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          {me.data
            ? `Signed in as ${me.data.username}${me.data.is_admin ? ' (admin)' : ''}.`
            : 'Account settings.'}
        </p>
      </header>

      <PasswordPanel />
      {me.data?.is_admin && <UsersPanel allTabs={me.data.all_tabs} />}
    </section>
  );
}

// ---------- change password ----------

function PasswordPanel() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);

  const mutation = useMutation({
    mutationFn: () => changePassword(current, next),
    onSuccess: (r) => {
      setNote({ ok: true, text: r.message || 'Password updated.' });
      setCurrent('');
      setNext('');
      setConfirm('');
    },
    onError: (e) => setNote({ ok: false, text: errMsg(e) }),
  });

  const mismatch = confirm.length > 0 && next !== confirm;
  const canSubmit = current && next.length >= 8 && next === confirm && !mutation.isPending;
  const inputCls =
    'w-full max-w-sm rounded-md border border-mentor-border bg-mentor-panel px-3 py-2 text-sm text-mentor-fg';

  return (
    <div className="panel-pad space-y-4">
      <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
        Change my password
      </h2>
      <div className="space-y-3">
        <label className="block text-xs text-mentor-muted">
          Current password
          <input
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            className={inputCls}
            autoComplete="current-password"
          />
        </label>
        <label className="block text-xs text-mentor-muted">
          New password (min 8 characters)
          <input
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            className={inputCls}
            autoComplete="new-password"
          />
        </label>
        <label className="block text-xs text-mentor-muted">
          Confirm new password
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className={inputCls}
            autoComplete="new-password"
          />
          {mismatch && <span className="mt-1 block text-mentor-danger">Passwords differ.</span>}
        </label>
      </div>
      <button
        type="button"
        disabled={!canSubmit}
        onClick={() => mutation.mutate()}
        className="btn-primary disabled:opacity-40"
      >
        {mutation.isPending ? 'Updating…' : 'Update password'}
      </button>
      {note && (
        <p className={`text-sm ${note.ok ? 'text-mentor-accent' : 'text-mentor-danger'}`}>
          {note.text}
        </p>
      )}
    </div>
  );
}

// ---------- admin: users ----------

function UsersPanel({ allTabs }: { allTabs: string[] }) {
  const queryClient = useQueryClient();
  const users = useQuery({ queryKey: ['users'], queryFn: listUsers });
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['users'] });

  const remove = useMutation({
    mutationFn: (username: string) => deleteUser(username),
    onSuccess: (r) => {
      setBanner({ ok: true, text: r.message });
      refresh();
    },
    onError: (e) => setBanner({ ok: false, text: errMsg(e) }),
  });

  const saveTabs = useMutation({
    mutationFn: ({ username, tabs }: { username: string; tabs: string[] | null }) =>
      updateUserTabs(username, tabs),
    onSuccess: (u) => {
      setBanner({ ok: true, text: `Access updated for ${u.username}.` });
      refresh();
    },
    onError: (e) => setBanner({ ok: false, text: errMsg(e) }),
  });

  return (
    <div className="panel-pad space-y-5">
      <div>
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          People with access
        </h2>
        <p className="text-xs text-mentor-muted">
          Each person gets their own login and sees only the pages you tick. Page access is
          a courtesy fence for trusted people, not bank-grade isolation.
        </p>
      </div>

      {banner && (
        <p className={`text-sm ${banner.ok ? 'text-mentor-accent' : 'text-mentor-danger'}`}>
          {banner.text}
        </p>
      )}

      <div className="space-y-3">
        {(users.data ?? []).map((u) => (
          <UserRow
            key={u.username}
            user={u}
            allTabs={allTabs}
            onSaveTabs={(tabs) => saveTabs.mutate({ username: u.username, tabs })}
            onDelete={() => remove.mutate(u.username)}
            busy={saveTabs.isPending || remove.isPending}
          />
        ))}
        {users.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}
      </div>

      <NewUserForm
        allTabs={allTabs}
        onCreated={(name) => {
          setBanner({ ok: true, text: `User ${name} created — share their password privately.` });
          refresh();
        }}
        onError={(text) => setBanner({ ok: false, text })}
      />
    </div>
  );
}

function UserRow({
  user,
  allTabs,
  onSaveTabs,
  onDelete,
  busy,
}: {
  user: UserDto;
  allTabs: string[];
  onSaveTabs: (tabs: string[] | null) => void;
  onDelete: () => void;
  busy: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set(user.tabs ?? allTabs));

  const summary =
    user.tabs === null
      ? 'all pages'
      : user.tabs.length === 0
        ? 'no pages'
        : user.tabs.map((t) => TAB_LABELS[t] ?? t).join(', ');

  return (
    <div className="rounded-lg border border-mentor-border bg-mentor-panelLight p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <span className="font-mono text-sm text-mentor-fg">{user.username}</span>
          {user.is_admin && (
            <span className="ml-2 rounded-full bg-mentor-accent/10 px-2 py-0.5 text-xs text-mentor-accent">
              admin
            </span>
          )}
          <p className="text-xs text-mentor-muted">sees: {summary}</p>
        </div>
        <div className="flex gap-2">
          {!user.is_admin && (
            <button
              type="button"
              onClick={() => setEditing((v) => !v)}
              className="btn-ghost text-xs"
              disabled={busy}
            >
              {editing ? 'Close' : 'Edit access'}
            </button>
          )}
          {!user.is_admin && (
            <button
              type="button"
              onClick={onDelete}
              className="btn-ghost text-xs text-mentor-danger"
              disabled={busy}
            >
              Remove
            </button>
          )}
        </div>
      </div>

      {editing && (
        <div className="mt-3 space-y-3 border-t border-mentor-border pt-3">
          <TabPicker allTabs={allTabs} selected={selected} onChange={setSelected} />
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-primary text-xs"
              disabled={busy}
              onClick={() => {
                onSaveTabs([...selected]);
                setEditing(false);
              }}
            >
              Save access
            </button>
            <button
              type="button"
              className="btn-ghost text-xs"
              disabled={busy}
              onClick={() => {
                onSaveTabs(null);
                setEditing(false);
              }}
            >
              Grant all pages
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function TabPicker({
  allTabs,
  selected,
  onChange,
}: {
  allTabs: string[];
  selected: Set<string>;
  onChange: (s: Set<string>) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
      {allTabs.map((tab) => (
        <label key={tab} className="flex cursor-pointer items-center gap-2 text-sm text-mentor-fg">
          <input
            type="checkbox"
            checked={selected.has(tab)}
            onChange={(e) => {
              const next = new Set(selected);
              if (e.target.checked) next.add(tab);
              else next.delete(tab);
              onChange(next);
            }}
            className="accent-current"
          />
          {TAB_LABELS[tab] ?? tab}
        </label>
      ))}
    </div>
  );
}

function NewUserForm({
  allTabs,
  onCreated,
  onError,
}: {
  allTabs: string[];
  onCreated: (username: string) => void;
  onError: (text: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set(['tips']));

  const create = useMutation({
    mutationFn: () =>
      createUser({ username, password, is_admin: false, tabs: [...selected] }),
    onSuccess: (u) => {
      onCreated(u.username);
      setUsername('');
      setPassword('');
      setOpen(false);
    },
    onError: (e) => onError(errMsg(e)),
  });

  const inputCls =
    'rounded-md border border-mentor-border bg-mentor-panel px-3 py-2 text-sm text-mentor-fg';

  if (!open) {
    return (
      <button type="button" onClick={() => setOpen(true)} className="btn-primary text-sm">
        + Add a user
      </button>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-mentor-border p-4">
      <h3 className="text-sm font-medium text-mentor-fg">New user</h3>
      <div className="flex flex-wrap gap-3">
        <input
          placeholder="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className={inputCls}
          autoComplete="off"
        />
        <input
          placeholder="password (min 8 chars)"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={inputCls}
          autoComplete="new-password"
        />
      </div>
      <p className="text-xs text-mentor-muted">Pages this user can see:</p>
      <TabPicker allTabs={allTabs} selected={selected} onChange={setSelected} />
      <div className="flex gap-2">
        <button
          type="button"
          className="btn-primary text-sm disabled:opacity-40"
          disabled={username.length < 2 || password.length < 8 || create.isPending}
          onClick={() => create.mutate()}
        >
          {create.isPending ? 'Creating…' : 'Create user'}
        </button>
        <button type="button" className="btn-ghost text-sm" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </div>
  );
}
