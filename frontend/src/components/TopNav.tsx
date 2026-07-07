import type { ReactNode } from 'react';
import { clsx } from 'clsx';

import type { Page } from '../App';
import type { Theme } from '../lib/useTheme';

interface TopNavProps {
  page: Page;
  onNavigate: (page: Page) => void;
  onLogout?: () => void;
  theme: Theme;
  onToggleTheme: () => void;
}

const LINKS: { id: Page; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'forecast', label: 'Forecast' },
  { id: 'system', label: 'System' },
  { id: 'tips', label: 'Tips' },
  { id: 'risk', label: 'Risk' },
  { id: 'journal', label: 'Journal' },
  { id: 'lessons', label: 'Lessons' },
  { id: 'prices', label: 'Prices' },
  { id: 'data', label: 'Data' },
  { id: 'backtest', label: 'Backtester' },
];

export function TopNav({ page, onNavigate, onLogout, theme, onToggleTheme }: TopNavProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-mentor-border bg-mentor-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-6">
        <div className="flex shrink-0 items-center gap-2 py-3">
          <div className="grid h-6 w-6 place-items-center rounded bg-mentor-accent/15 ring-1 ring-mentor-accent/50">
            <span className="h-2.5 w-2.5 rounded-sm bg-mentor-accent" />
          </div>
          <span className="text-sm font-medium tracking-tight text-mentor-fg">Mentor</span>
        </div>

        <nav className="flex flex-1 items-center gap-0.5 overflow-x-auto">
          {LINKS.map((l) => {
            const active = page === l.id;
            return (
              <button
                key={l.id}
                type="button"
                onClick={() => onNavigate(l.id)}
                className={clsx(
                  'flex items-center gap-1.5 whitespace-nowrap border-b-2 px-2.5 py-3.5 text-[13px] transition-colors',
                  active
                    ? 'border-mentor-accent text-mentor-fg'
                    : 'border-transparent text-mentor-muted hover:text-mentor-fg'
                )}
              >
                <NavIcon id={l.id} />
                {l.label}
              </button>
            );
          })}
        </nav>

        <button
          type="button"
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          className="shrink-0 rounded-md border border-mentor-border bg-mentor-panelLight p-2 text-mentor-muted transition-colors hover:text-mentor-fg"
        >
          {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
        </button>

        {onLogout && (
          <button type="button" onClick={onLogout} className="btn-ghost shrink-0">
            Sign out
          </button>
        )}
      </div>
    </header>
  );
}

function NavIcon({ id }: { id: Page }) {
  const p: Record<Page, ReactNode> = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    forecast: (
      <>
        <path d="M3 17l6-6 4 4 8-8" />
        <path d="M17 7h4v4" />
      </>
    ),
    system: <path d="M3 12h4l3 8 4-16 3 8h4" />,
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
  };
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {p[id]}
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </svg>
  );
}
