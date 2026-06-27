import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { type EventFreeze, getEventFreeze, sweepAlerts } from '../api/alerts';
import { type SnapshotResponse, fetchForecastSnapshot } from '../api/forecast';
import { type Analytics, type Trade, getAnalytics, listTrades } from '../api/journal';
import { type NewsItem, listNews } from '../api/news';
import { EconomicCalendar } from '../components/EconomicCalendar';
import { Metric } from '../components/Metric';
import { formatMoney, formatNumber, formatPercent } from '../lib/format';

const SYMBOL = 'EURUSD';

/**
 * The morning briefing — Principle 01 in screen form.
 *
 * Composes existing endpoints; doesn't fetch anything that isn't
 * already cached by another page's query. The layout is deliberately
 * spacious — the plan calls for a "calm, uncluttered" interface and
 * trading dashboards generally fail this test spectacularly.
 */
export function DashboardPage() {
  const queryClient = useQueryClient();

  const snapshot = useQuery({
    queryKey: ['dashboard', 'snapshot', SYMBOL],
    queryFn: () =>
      fetchForecastSnapshot({
        symbol: SYMBOL,
        timeframe: '1h',
        model_name: 'baseline',
        horizon_bars: 24,
      }),
    refetchInterval: 5 * 60 * 1000,
  });
  const news = useQuery({
    queryKey: ['news', 'dashboard'],
    queryFn: () => listNews({ limit: 6, onlyClassified: true, minImpact: '0.4' }),
    refetchInterval: 5 * 60 * 1000,
  });
  const eventFreeze = useQuery({
    queryKey: ['event-freeze'],
    queryFn: getEventFreeze,
    refetchInterval: 60_000,
  });
  const analytics = useQuery({
    queryKey: ['journal-analytics'],
    queryFn: () => getAnalytics(),
  });
  const trades = useQuery({
    queryKey: ['trades-recent-dashboard'],
    queryFn: () => listTrades(),
  });

  const sweep = useMutation({
    mutationFn: sweepAlerts,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  const today = useMemo(() => new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' }), []);

  return (
    <section className="space-y-8">
      <header className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wider text-mentor-muted">
          Morning briefing · {today}
        </span>
        <h1 className="font-serif text-3xl tracking-tight">
          {SYMBOL} — what matters today
        </h1>
      </header>

      <FreezeBanner freeze={eventFreeze.data} />

      <div className="grid gap-6 lg:grid-cols-[1.3fr,1fr]">
        <LeanCard snapshot={snapshot.data} loading={snapshot.isLoading} />
        <PulseCard analytics={analytics.data} loading={analytics.isLoading} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <NewsCard items={news.data ?? []} loading={news.isLoading} />
        <EconomicCalendar />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <OpenRiskCard
          trades={trades.data ?? []}
          loading={trades.isLoading}
          onSweep={() => sweep.mutate()}
          sweepPending={sweep.isPending}
        />
        <div className="hidden lg:block" aria-hidden />
      </div>
    </section>
  );
}

// ---------- freeze banner ----------

function FreezeBanner({ freeze }: { freeze: EventFreeze | undefined }) {
  if (!freeze || !freeze.triggered) return null;
  const tone = freeze.soft
    ? 'border-mentor-warn/40 bg-mentor-warn/10 text-mentor-warn'
    : 'border-mentor-danger/40 bg-mentor-danger/10 text-mentor-danger';
  return (
    <div className={`rounded-lg border p-4 ${tone}`}>
      <div className="text-xs uppercase tracking-wider">
        {freeze.soft ? 'Event-freeze warning' : 'Event-freeze · trades blocked'}
      </div>
      <p className="mt-1 text-sm">{freeze.blocking_reason}</p>
      <p className="mt-2 text-xs opacity-80">
        News releases regularly move price through stops at multiples of the
        usual ATR. The high-conviction setup that coincides with a Fed
        statement is not a setup — it's a coin flip with a wider distribution.
      </p>
    </div>
  );
}

// ---------- today's lean ----------

function LeanCard({
  snapshot,
  loading,
}: {
  snapshot: SnapshotResponse | undefined;
  loading: boolean;
}) {
  const f = snapshot?.forecast;
  return (
    <div className="panel-pad space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">Today's lean</h2>
        {f && (
          <span className="pill capitalize text-mentor-accentSoft border-mentor-accent/30">
            {f.direction}
          </span>
        )}
      </div>
      {loading && <p className="text-sm text-mentor-muted">Reading the market…</p>}
      {!loading && !f && (
        <p className="text-sm text-mentor-muted">
          Backfill bars for {SYMBOL} on 1h to get today's read.
        </p>
      )}
      {f && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="P(up)"
              value={`${Math.round(Number(f.p_up) * 100)}%`}
              tone={Number(f.p_up) > 0.5 ? 'positive' : 'danger'}
              sub={`horizon ${f.horizon_bars} bars`}
            />
            <Metric
              label="Confidence"
              value={`${Math.round(Number(f.confidence) * 100)}%`}
              tone={Number(f.confidence) < 0.2 ? 'warn' : 'default'}
              sub={`model: ${f.model_name}`}
            />
          </div>
          <p className="rounded-lg border border-mentor-border bg-mentor-panelLight/60 p-3 text-sm leading-relaxed">
            {f.reasoning}
          </p>
        </>
      )}
    </div>
  );
}

// ---------- journal pulse ----------

function PulseCard({
  analytics,
  loading,
}: {
  analytics: Analytics | undefined;
  loading: boolean;
}) {
  return (
    <div className="panel-pad space-y-4">
      <h2 className="font-medium text-mentor-fg">Your pulse</h2>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && analytics && analytics.sample_size > 0 && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="Trades"
              value={analytics.sample_size}
              sub={`${analytics.wins}W / ${analytics.losses}L`}
            />
            <Metric
              label="Expectancy"
              value={`${formatNumber(analytics.expectancy_r, 2)} R`}
              tone={Number(analytics.expectancy_r) > 0 ? 'positive' : 'danger'}
            />
            <Metric
              label="Win rate"
              value={formatPercent(analytics.win_rate_percent, 1)}
            />
            <Metric
              label="Profit factor"
              value={analytics.profit_factor ? formatNumber(analytics.profit_factor) : '—'}
            />
          </div>
          <p className="text-xs italic text-mentor-muted">{analytics.interpretation}</p>
        </>
      )}
      {!loading && (!analytics || analytics.sample_size === 0) && (
        <p className="text-sm text-mentor-muted">No journal data yet — log your first trade.</p>
      )}
    </div>
  );
}

// ---------- news ----------

function NewsCard({ items, loading }: { items: NewsItem[]; loading: boolean }) {
  return (
    <div className="panel-pad space-y-3">
      <h2 className="font-medium text-mentor-fg">News context</h2>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && items.length === 0 && (
        <p className="text-sm text-mentor-muted">
          No classified news in the last window. Pull the latest from the
          Forecast page if you've set NEWSAPI_KEY.
        </p>
      )}
      <ul className="space-y-3">
        {items.map((n) => (
          <li key={n.id} className="rounded-lg border border-mentor-border bg-mentor-panelLight/40 p-3">
            <div className="flex items-center gap-2 text-xs">
              {n.classification && (
                <span className="pill capitalize text-mentor-accentSoft border-mentor-accent/30">
                  {n.classification.category}
                </span>
              )}
              {n.classification && (
                <span className="text-mentor-muted">
                  impact {formatNumber(n.classification.impact, 2)} ·{' '}
                  {new Date(n.ts).toLocaleString()}
                </span>
              )}
            </div>
            <a
              className="mt-1 block text-sm font-medium hover:underline"
              href={n.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {n.headline}
            </a>
            {n.classification?.rationale && (
              <p className="mt-1 text-xs text-mentor-muted">
                {n.classification.rationale}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------- open risk ----------

function OpenRiskCard({
  trades,
  loading,
  onSweep,
  sweepPending,
}: {
  trades: Trade[];
  loading: boolean;
  onSweep: () => void;
  sweepPending: boolean;
}) {
  const open = trades.filter((t) => t.status === 'open');
  const openRisk = open.reduce(
    (sum, t) => sum + Number(t.initial_risk.amount ?? 0),
    0
  );
  const currency = trades[0]?.initial_risk.currency ?? 'USD';
  return (
    <div className="panel-pad space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">Open risk &amp; alerts</h2>
        <button
          type="button"
          onClick={onSweep}
          disabled={sweepPending}
          className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg"
        >
          {sweepPending ? 'Checking…' : 'Sweep alerts'}
        </button>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      <div className="grid grid-cols-2 gap-3">
        <Metric label="Open positions" value={open.length} />
        <Metric
          label="Total open risk"
          value={openRisk ? formatMoney(openRisk, currency) : '—'}
          tone={openRisk > 0 ? 'warn' : 'default'}
        />
      </div>
      {!loading && open.length === 0 && (
        <p className="text-xs text-mentor-muted">
          Nothing open. The boring days are usually the most profitable.
        </p>
      )}
      {open.length > 0 && (
        <ul className="space-y-2 text-xs">
          {open.map((t) => (
            <li
              key={t.id}
              className="flex items-center justify-between rounded-md bg-mentor-panelLight/40 px-3 py-2"
            >
              <span className="font-mono">
                {t.symbol} · {t.direction} · {formatNumber(t.size_lots, 2)} lots
              </span>
              <span className="text-mentor-muted">
                stop {Number(t.planned_stop).toFixed(5)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
