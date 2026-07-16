import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { getAuthStatus, getMe } from './api/auth';
import { ErrorBoundary } from './components/ErrorBoundary';
import { TopNav } from './components/TopNav';
import { useAuth } from './lib/useAuth';
import { useTheme } from './lib/useTheme';
import { BacktesterPage } from './pages/BacktesterPage';
import { DashboardPage } from './pages/DashboardPage';
import { DataHealthPage } from './pages/DataHealthPage';
import { ForecastPage } from './pages/ForecastPage';
import { JournalPage } from './pages/JournalPage';
import { LessonsPage } from './pages/LessonsPage';
import { LoginPage } from './pages/LoginPage';
import { LoopPage } from './pages/LoopPage';
import { PricesPage } from './pages/PricesPage';
import { RiskCalculatorPage } from './pages/RiskCalculatorPage';
import { SettingsPage } from './pages/SettingsPage';
import { SystemPredictionsPage } from './pages/SystemPredictionsPage';
import { TipsPage } from './pages/TipsPage';
import { TradePage } from './pages/TradePage';

export type Page =
  | 'dashboard'
  | 'trade'
  | 'forecast'
  | 'system'
  | 'loop'
  | 'tips'
  | 'risk'
  | 'journal'
  | 'lessons'
  | 'prices'
  | 'data'
  | 'backtest'
  | 'settings';

export function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const { hasToken, logout } = useAuth();
  const { theme, toggle: toggleTheme } = useTheme();
  const status = useQuery({
    queryKey: ['auth-status'],
    queryFn: getAuthStatus,
    staleTime: 60_000,
  });

  // Auth gate: when the server has auth enabled and we have no token,
  // every interactive screen is the login form. The status endpoint is
  // open (whitelisted in the middleware), so this resolves on first load.
  const needsLogin = Boolean(status.data?.auth_enabled && !hasToken);

  // Tab privileges: if this account can't see the current page, hop to the
  // first page it can see (settings is always allowed).
  const me = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    staleTime: 60_000,
    enabled: !needsLogin,
  });
  const allowedTabs = me.data?.tabs;
  useEffect(() => {
    if (allowedTabs != null && page !== 'settings' && !allowedTabs.includes(page)) {
      setPage((allowedTabs[0] as Page | undefined) ?? 'settings');
    }
  }, [allowedTabs, page]);

  if (needsLogin) return <LoginPage />;

  return (
    <div className="min-h-screen">
      <TopNav
        page={page}
        onNavigate={setPage}
        onLogout={hasToken ? logout : undefined}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <ErrorBoundary key={page}>
          {page === 'dashboard' && <DashboardPage />}
          {page === 'trade' && <TradePage />}
          {page === 'forecast' && <ForecastPage />}
          {page === 'system' && <SystemPredictionsPage />}
          {page === 'loop' && <LoopPage />}
          {page === 'tips' && <TipsPage />}
          {page === 'risk' && <RiskCalculatorPage />}
          {page === 'journal' && <JournalPage />}
          {page === 'lessons' && <LessonsPage />}
          {page === 'prices' && <PricesPage />}
          {page === 'data' && <DataHealthPage />}
          {page === 'backtest' && <BacktesterPage />}
          {page === 'settings' && <SettingsPage />}
        </ErrorBoundary>
      </main>
      <footer className="mx-auto max-w-6xl px-6 pb-10 pt-4 text-xs text-mentor-muted">
        Mentor is a personal, educational tool — not licensed financial advice.
        Paper-trade first. The human confirms every action.
      </footer>
    </div>
  );
}
