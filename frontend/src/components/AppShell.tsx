import { type ReactNode, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';

import { getMe } from '../api/auth';
import type { Page } from '../App';
import type { Theme } from '../lib/useTheme';

interface AppShellProps {
  page: Page;
  onNavigate: (page: Page) => void;
  onLogout?: () => void;
  theme: Theme;
  onToggleTheme: () => void;
  children: ReactNode;
}

type NavItem = { id: Page; label: string; hint: string };
type NavGroup = { heading: string; items: NavItem[] };

const NAV: NavGroup[] = [
  {
    heading: 'Trade',
    items: [
      { id: 'dashboard', label: 'Dashboard', hint: 'Your morning briefing' },
      { id: 'trade', label: 'Trade plan', hint: 'What to do right now' },
      { id: 'forecast', label: 'Forecast', hint: 'Direction & volatility' },
      { id: 'tips', label: 'Tips', hint: 'Stock-tip scorecard' },
    ],
  },
  {
    heading: 'The system',
    items: [
      { id: 'system', label: 'Predictions', hint: 'The audit log' },
      { id: 'loop', label: 'Loop', hint: 'The learning engine' },
      { id: 'backtest', label: 'Backtester', hint: 'Test strategies' },
    ],
  },
  {
    heading: 'Toolkit',
    items: [
      { id: 'risk', label: 'Risk calculator', hint: 'Size a position' },
      { id: 'journal', label: 'Journal', hint: 'Log & review trades' },
      { id: 'prices', label: 'Prices', hint: 'Price history' },
      { id: 'data', label: 'Data health', hint: 'Feed coverage' },
      { id: 'lessons', label: 'Learn', hint: 'The curriculum' },
    ],
  },
];

export function AppShell({
  page,
  onNavigate,
  onLogout,
  theme,
  onToggleTheme,
  children,
}: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const me = useQuery({ queryKey: ['me'], queryFn: getMe, staleTime: 60_000 });
  const allowed = me.data?.tabs; // null = every tab

  const visibleGroups = NAV.map((g) => ({
    ...g,
    items: allowed == null ? g.items : g.items.filter((i) => allowed.includes(i.id)),
  })).filter((g) => g.items.length > 0);

  const go = (p: Page) => {
    onNavigate(p);
    setMobileOpen(false);
  };

  const nav = (
    <SidebarBody
      groups={visibleGroups}
      page={page}
      onNavigate={go}
      onLogout={onLogout}
      theme={theme}
      onToggleTheme={onToggleTheme}
      username={me.data?.username}
      isAdmin={me.data?.is_admin}
    />
  );

  return (
    <div className="min-h-screen lg:flex">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-[264px] shrink-0 border-r border-mentor-border bg-mentor-panel/70 backdrop-blur-xl lg:block">
        {nav}
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-mentor-border bg-mentor-panel/85 px-4 py-3 backdrop-blur-xl lg:hidden">
        <Brand />
        <div className="flex items-center gap-2">
          <ThemeButton theme={theme} onToggle={onToggleTheme} />
          <button
            type="button"
            aria-label="Open menu"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg border border-mentor-border bg-mentor-panelLight p-2 text-mentor-muted"
          >
            <BurgerIcon />
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-[280px] max-w-[85%] border-r border-mentor-border bg-mentor-panel shadow-2xl">
            {nav}
          </div>
        </div>
      )}

      {/* Content */}
      <main className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-[1360px] px-5 py-7 sm:px-8 sm:py-9">{children}</div>
        <footer className="mx-auto w-full max-w-[1360px] px-5 pb-10 pt-2 text-xs text-mentor-muted sm:px-8">
          Mentor is a personal, educational tool — not licensed financial advice. Paper-trade
          first. The human confirms every action.
        </footer>
      </main>
    </div>
  );
}

// ---------- sidebar body ----------

function SidebarBody({
  groups,
  page,
  onNavigate,
  onLogout,
  theme,
  onToggleTheme,
  username,
  isAdmin,
}: {
  groups: NavGroup[];
  page: Page;
  onNavigate: (p: Page) => void;
  onLogout?: () => void;
  theme: Theme;
  onToggleTheme: () => void;
  username?: string;
  isAdmin?: boolean;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-5 py-5">
        <Brand />
        <ThemeButton theme={theme} onToggle={onToggleTheme} />
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 pb-4">
        {groups.map((group) => (
          <div key={group.heading}>
            <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-mentor-muted/70">
              {group.heading}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.id}
                  item={item}
                  active={page === item.id}
                  onClick={() => onNavigate(item.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-mentor-border p-3">
        <button
          type="button"
          onClick={() => onNavigate('settings')}
          className={clsx(
            'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors',
            page === 'settings'
              ? 'bg-mentor-accent/10 text-mentor-fg'
              : 'text-mentor-muted hover:bg-mentor-panelLight hover:text-mentor-fg'
          )}
        >
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-mentor-panelLight text-mentor-fg">
            {(username ?? 'U').slice(0, 1).toUpperCase()}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-mentor-fg">
              {username ?? 'Account'}
            </span>
            <span className="block text-xs text-mentor-muted">
              {isAdmin ? 'Admin · Settings' : 'Settings'}
            </span>
          </span>
          <GearIcon />
        </button>
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className="mt-1 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-mentor-muted transition-colors hover:text-mentor-danger"
          >
            <LogoutIcon />
            Sign out
          </button>
        )}
      </div>
    </div>
  );
}

function NavLink({
  item,
  active,
  onClick,
}: {
  item: NavItem;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all',
        active
          ? 'bg-mentor-accent/10 text-mentor-fg shadow-[inset_0_0_0_1px_rgb(var(--mentor-accent)/0.2)]'
          : 'text-mentor-muted hover:bg-mentor-panelLight hover:text-mentor-fg'
      )}
    >
      <span
        className={clsx(
          'grid h-8 w-8 shrink-0 place-items-center rounded-lg transition-colors',
          active
            ? 'bg-mentor-accent text-white'
            : 'bg-mentor-panelLight text-mentor-muted group-hover:text-mentor-fg'
        )}
      >
        <NavIcon id={item.id} />
      </span>
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium">{item.label}</span>
        <span className="block truncate text-xs text-mentor-muted">{item.hint}</span>
      </span>
    </button>
  );
}

// ---------- brand + buttons ----------

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <span
        className="grid h-8 w-8 place-items-center rounded-xl text-white shadow-md"
        style={{
          background: 'linear-gradient(140deg, rgb(var(--mentor-accent)), rgb(var(--mentor-accentSoft)))',
        }}
      >
        <SparkIcon />
      </span>
      <span className="text-[15px] font-semibold tracking-tight text-mentor-fg">Mentor</span>
    </div>
  );
}

function ThemeButton({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
      className="rounded-lg border border-mentor-border bg-mentor-panelLight p-2 text-mentor-muted transition-colors hover:text-mentor-fg"
    >
      {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

// ---------- icons ----------

const stroke = {
  width: 15,
  height: 15,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.9,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
};

function NavIcon({ id }: { id: Page }) {
  const p: Record<Page, ReactNode> = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
    trade: (
      <>
        <path d="M12 3v18" />
        <path d="M7 8l5-5 5 5" />
        <path d="M8 14h8M8 18h8" />
      </>
    ),
    forecast: (
      <>
        <path d="M3 17l6-6 4 4 8-8" />
        <path d="M17 7h4v4" />
      </>
    ),
    system: <path d="M3 12h4l3 8 4-16 3 8h4" />,
    loop: (
      <>
        <path d="M21 12a9 9 0 1 1-3-6.7" />
        <path d="M21 3v5h-5" />
      </>
    ),
    tips: <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />,
    risk: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
    journal: (
      <>
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </>
    ),
    lessons: (
      <>
        <path d="M22 10L12 5 2 10l10 5 10-5z" />
        <path d="M6 12v5c0 1 3 3 6 3s6-2 6-3v-5" />
      </>
    ),
    prices: (
      <>
        <path d="M3 3v18h18" />
        <rect x="7" y="10" width="3" height="8" />
        <rect x="12" y="6" width="3" height="12" />
        <rect x="17" y="13" width="3" height="5" />
      </>
    ),
    data: (
      <>
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 5v6c0 1.7-4 3-9 3s-9-1.3-9-3V5" />
        <path d="M21 11v6c0 1.7-4 3-9 3s-9-1.3-9-3v-6" />
      </>
    ),
    backtest: (
      <>
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
        <path d="M3 3v5h5" />
        <path d="M12 8v4l3 2" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </>
    ),
  };
  return <svg {...stroke}>{p[id]}</svg>;
}

function SparkIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2l2.2 5.8L20 10l-5.8 2.2L12 18l-2.2-5.8L4 10l5.8-2.2L12 2z" />
    </svg>
  );
}

function GearIcon() {
  return (
    <svg {...stroke} width="16" height="16">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg {...stroke}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}

function BurgerIcon() {
  return (
    <svg {...stroke} width="20" height="20">
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg {...stroke}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg {...stroke}>
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </svg>
  );
}
