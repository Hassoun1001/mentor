import { clsx } from 'clsx';

import type { Page } from '../App';

interface TopNavProps {
  page: Page;
  onNavigate: (page: Page) => void;
  onLogout?: () => void;
}

const LINKS: { id: Page; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'forecast', label: 'Forecast' },
  { id: 'risk', label: 'Risk Calculator' },
  { id: 'journal', label: 'Journal' },
  { id: 'lessons', label: 'Lessons' },
  { id: 'prices', label: 'Prices' },
  { id: 'backtest', label: 'Backtester' },
];

export function TopNav({ page, onNavigate, onLogout }: TopNavProps) {
  return (
    <header className="border-b border-mentor-border bg-mentor-panel/70 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 rounded-md bg-mentor-accent/20 ring-1 ring-mentor-accent">
            <div className="m-1 h-5 w-5 rounded-sm bg-mentor-accent" />
          </div>
          <div className="font-serif text-xl tracking-tight">Mentor</div>
          <span className="pill">Phase 5 · Polish</span>
        </div>
        <nav className="hidden items-center gap-5 text-sm md:flex">
          {LINKS.map((l) => (
            <button
              key={l.id}
              type="button"
              onClick={() => onNavigate(l.id)}
              className={clsx(
                'transition-colors',
                page === l.id ? 'text-mentor-fg' : 'text-mentor-muted hover:text-mentor-fg'
              )}
            >
              {l.label}
            </button>
          ))}
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              className="ml-2 rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg"
            >
              Sign out
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
