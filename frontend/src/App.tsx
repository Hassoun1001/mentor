import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { getAuthStatus } from './api/auth';
import { TopNav } from './components/TopNav';
import { useAuth } from './lib/useAuth';
import { BacktesterPage } from './pages/BacktesterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ForecastPage } from './pages/ForecastPage';
import { JournalPage } from './pages/JournalPage';
import { LessonsPage } from './pages/LessonsPage';
import { LoginPage } from './pages/LoginPage';
import { PricesPage } from './pages/PricesPage';
import { RiskCalculatorPage } from './pages/RiskCalculatorPage';

export type Page =
  | 'dashboard'
  | 'forecast'
  | 'risk'
  | 'journal'
  | 'lessons'
  | 'prices'
  | 'backtest';

export function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const { hasToken, logout } = useAuth();
  const status = useQuery({
    queryKey: ['auth-status'],
    queryFn: getAuthStatus,
    staleTime: 60_000,
  });

  // Auth gate: when the server has auth enabled and we have no token,
  // every interactive screen is the login form. The status endpoint is
  // open (whitelisted in the middleware), so this resolves on first load.
  const needsLogin = status.data?.auth_enabled && !hasToken;
  if (needsLogin) return <LoginPage />;

  return (
    <div className="min-h-screen">
      <TopNav page={page} onNavigate={setPage} onLogout={hasToken ? logout : undefined} />
      <main className="mx-auto max-w-6xl px-6 py-8">
        {page === 'dashboard' && <DashboardPage />}
        {page === 'forecast' && <ForecastPage />}
        {page === 'risk' && <RiskCalculatorPage />}
        {page === 'journal' && <JournalPage />}
        {page === 'lessons' && <LessonsPage />}
        {page === 'prices' && <PricesPage />}
        {page === 'backtest' && <BacktesterPage />}
      </main>
      <footer className="mx-auto max-w-6xl px-6 pb-10 pt-4 text-xs text-mentor-muted">
        Mentor is a personal, educational tool — not licensed financial advice.
        Paper-trade first. The human confirms every action.
      </footer>
    </div>
  );
}
