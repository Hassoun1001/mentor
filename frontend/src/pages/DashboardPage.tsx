import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { clsx } from 'clsx';

import { type EventFreeze, getEventFreeze, sweepAlerts } from '../api/alerts';
import { type SnapshotResponse, fetchForecastSnapshot } from '../api/forecast';
import { type Analytics, type Trade, getAnalytics, listTrades } from '../api/journal';
import { type NewsItem, listNews } from '../api/news';
import { EconomicCalendar } from '../components/EconomicCalendar';
import { Metric } from '../components/Metric';
import { formatMoney, formatNumber, formatPercent } from '../lib/format';

const SYMBOL = 'EURUSD';

/**
 * The morning briefing — a calm, spacious "here's where things stand"
 * screen. Composes existing cached endpoints; nothing here is fetched
 * that another page hasn't already warmed.
 */
export function DashboardPage() {
  const queryClient = useQueryClient();

  const snapshot = useQuery({
    queryKey: ['dashboard', 'snapshot', SYMBOL],
    queryFn: () =>
      fetchForecastSnapshot({ symbol: SYMBOL, timeframe: '1h', model_name: 'baseline', horizon_bars: 24 }),
    refetchInterval: 5 * 60 * 1000,
  });
  const news = useQuery({
    queryKey: ['news', 'dashboard'],
    queryFn: () => listNews({ limit: 6, onlyClassified: true, minImpact: '0.4' }),
    refetchInterval: 5 * 60 * 1000,
  });
  const eventFreeze = useQuery({ queryKey: ['event-freeze'], queryFn: getEventFreeze, refetchInterval: 60_000 });
  const analytics = useQuery({ queryKey: ['journal-analytics'], queryFn: () => getAnalytics() });
  const trades = useQuery({ queryKey: ['trades-recent-dashboard'], queryFn: () => listTrades() });

  const sweep = useMutation({
    mutationFn: sweepAlerts,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  const greeting = useMemo(() => {
    const h = new Date().getHours();
    return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
  }, []);
  const today = useMemo(
    () => new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' }),
    []
  );

  return (
    <section className="space-y-6">
      <header>
        <p className="eyebrow">{today}</p>
        <h1 className="page-title mt-1">{greeting}.</h1>
        <p className="mt-1 text-sm text-mentor-muted">
          Here&apos;s where {SYMBOL} stands and how your trading is going.
        </p>
      </header>

      <HeroRead snapshot={snapshot.data} analytics={analytics.data} loading={snapshot.isLoading} />

      <FreezeBanner freeze={eventFreeze.data} />

      <div className="grid gap-6 lg:grid-cols-[1.25fr_1fr]">
        <LeanCard snapshot={snapshot.data} loading={snapshot.isLoading} />
        <PulseCard analytics={analytics.data} loading={analytics.isLoading} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <NewsCard items={news.data ?? []} loading={news.isLoading} />
        <EconomicCalendar />
      </div>

      <OpenRiskCard
        trades={trades.data ?? []}
        loading={trades.isLoading}
        onSweep={() => sweep.mutate()}
        sweepPending={sweep.isPending}
      />
    </section>
  );
}

// ---------- hero read ----------

function HeroRead({
  snapshot,
  analytics,
  loading,
}: {
  snapshot: SnapshotResponse | undefined;
  analytics: Analytics | undefined;
  loading: boolean;
}) {
  const f = snapshot?.forecast;
  const dir = f?.direction ?? 'neutral';
  const price = f ? Number(f.asof_close).toFixed(5) : '—';
  const pUp = f != null ? Math.round(Number(f.p_up) * 100) : null;
  const conf = f != null ? Math.round(Number(f.confidence) * 100) : null;
  const hasJournal = analytics != null && analytics.sample_size > 0;
  const exp = hasJournal ? Number(analytics.expectancy_r) : null;
  const win = hasJournal ? analytics.win_rate_percent : null;

  const stance =
    dir === 'long' ? 'Leaning up' : dir === 'short' ? 'Leaning down' : 'No clear lean';
  const stanceCls =
    dir === 'long' ? 'chip-up' : dir === 'short' ? 'chip-down' : 'chip-accent';

  return (
    <div className="hero grid gap-6 p-6 sm:p-7 lg:grid-cols-[auto_1fr] lg:items-center">
      <div className="flex items-center gap-6">
        <PupRing pct={pUp} />
        <div>
          <div className="flex items-center gap-2 text-sm text-mentor-muted">
            <span className="font-semibold text-mentor-fg">{SYMBOL}</span>
            <span>· 1h · next 24h</span>
          </div>
          <div className="mt-1 font-mono text-4xl font-semibold tracking-tight text-mentor-fg">
            {loading ? '·····' : price}
          </div>
          <span className={clsx('chip mt-2', stanceCls)}>
            {dir === 'long' ? '▲' : dir === 'short' ? '▼' : '•'} {stance}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <HeroStat label="Chance of rising" value={pUp != null ? `${pUp}%` : '—'} hint="model P(up)" />
        <HeroStat
          label="Conviction"
          value={conf != null ? `${conf}%` : '—'}
          hint={conf != null && conf < 20 ? 'weak — be cautious' : 'signal strength'}
          tone={conf != null && conf < 20 ? 'warn' : 'default'}
        />
        <HeroStat
          label="Your expectancy"
          value={exp != null ? `${exp.toFixed(2)}R` : '—'}
          hint={exp == null ? 'log trades to see' : 'avg per trade'}
          tone={exp == null ? 'default' : exp > 0 ? 'up' : 'down'}
        />
        <HeroStat
          label="Your win rate"
          value={win != null ? `${Math.round(Number(win))}%` : '—'}
          hint={win == null ? 'log trades to see' : 'of closed trades'}
        />
      </div>
    </div>
  );
}

function HeroStat({
  label,
  value,
  hint,
  tone = 'default',
}: {
  label: string;
  value: string;
  hint: string;
  tone?: 'default' | 'up' | 'down' | 'warn';
}) {
  return (
    <div className="rounded-2xl border border-mentor-border bg-mentor-panel/60 p-3.5">
      <div className="metric-label">{label}</div>
      <div
        className={clsx(
          'mt-1 text-2xl font-semibold tracking-tight tnum',
          tone === 'up' && 'text-mentor-accentSoft',
          tone === 'down' && 'text-mentor-danger',
          tone === 'warn' && 'text-mentor-warn',
          tone === 'default' && 'text-mentor-fg'
        )}
      >
        {value}
      </div>
      <div className="mt-0.5 text-[11px] text-mentor-muted">{hint}</div>
    </div>
  );
}

function PupRing({ pct }: { pct: number | null }) {
  const p = pct == null ? 0 : Math.max(0, Math.min(100, pct));
  const r = 34;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - p / 100);
  const stroke =
    pct == null
      ? 'rgb(var(--mentor-muted))'
      : p >= 50
        ? 'rgb(var(--mentor-accentSoft))'
        : 'rgb(var(--mentor-danger))';
  return (
    <div className="relative h-24 w-24 shrink-0">
      <svg viewBox="0 0 80 80" className="h-24 w-24 -rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" stroke="rgb(var(--mentor-border))" strokeWidth="7" />
        <circle
          cx="40"
          cy="40"
          r={r}
          fill="none"
          stroke={stroke}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset .7s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-semibold tnum text-mentor-fg">
          {pct == null ? '—' : `${pct}%`}
        </span>
        <span className="text-[10px] uppercase tracking-wider text-mentor-muted">up</span>
      </div>
    </div>
  );
}

// ---------- freeze banner ----------

function FreezeBanner({ freeze }: { freeze: EventFreeze | undefined }) {
  if (!freeze || !freeze.triggered) return null;
  const tone = freeze.soft
    ? 'border-mentor-warn/40 bg-mentor-warn/10'
    : 'border-mentor-danger/40 bg-mentor-danger/10';
  return (
    <div className={`rounded-2xl border p-4 ${tone}`}>
      <div className="flex items-center gap-2">
        <span className={clsx('chip', freeze.soft ? 'chip-warn' : 'chip-down')}>
          {freeze.soft ? 'Caution' : 'Trades blocked'}
        </span>
        <span className="text-sm font-medium text-mentor-fg">Event freeze</span>
      </div>
      <p className="mt-2 text-sm text-mentor-fg">{freeze.blocking_reason}</p>
      <p className="mt-1.5 text-xs text-mentor-muted">
        News releases regularly push price through stops at multiples of the usual range. A
        high-conviction setup that coincides with a Fed statement isn&apos;t a setup — it&apos;s
        a coin flip with a wider distribution.
      </p>
    </div>
  );
}

// ---------- today's lean ----------

function LeanCard({ snapshot, loading }: { snapshot: SnapshotResponse | undefined; loading: boolean }) {
  const f = snapshot?.forecast;
  return (
    <div className="card-pad space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">Why the model leans this way</h2>
          <p className="text-xs text-mentor-muted">Plain-English reasoning behind today&apos;s read.</p>
        </div>
        {f && <span className="pill capitalize">{f.direction}</span>}
      </div>
      {loading && <p className="text-sm text-mentor-muted">Reading the market…</p>}
      {!loading && !f && (
        <p className="text-sm text-mentor-muted">
          Backfill 1h bars for {SYMBOL} to get today&apos;s read.
        </p>
      )}
      {f && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="Chance of rising"
              value={`${Math.round(Number(f.p_up) * 100)}%`}
              tone={Number(f.p_up) > 0.5 ? 'positive' : 'danger'}
              sub={`over the next ${f.horizon_bars} hours`}
            />
            <Metric
              label="Conviction"
              value={`${Math.round(Number(f.confidence) * 100)}%`}
              tone={Number(f.confidence) < 0.2 ? 'warn' : 'default'}
              sub={`model: ${f.model_name}`}
            />
          </div>
          <p className="rounded-2xl border border-mentor-border bg-mentor-panelLight/60 p-4 text-sm leading-relaxed text-mentor-fg">
            {f.reasoning}
          </p>
        </>
      )}
    </div>
  );
}

// ---------- journal pulse ----------

function PulseCard({ analytics, loading }: { analytics: Analytics | undefined; loading: boolean }) {
  return (
    <div className="card-pad space-y-4">
      <div>
        <h2 className="section-title">Your pulse</h2>
        <p className="text-xs text-mentor-muted">How your own logged trades are doing.</p>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && analytics && analytics.sample_size > 0 && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Metric label="Trades" value={analytics.sample_size} sub={`${analytics.wins}W / ${analytics.losses}L`} />
            <Metric
              label="Expectancy"
              value={`${formatNumber(analytics.expectancy_r, 2)} R`}
              tone={Number(analytics.expectancy_r) > 0 ? 'positive' : 'danger'}
              sub="avg risk-multiple per trade"
            />
            <Metric label="Win rate" value={formatPercent(analytics.win_rate_percent, 1)} />
            <Metric
              label="Profit factor"
              value={analytics.profit_factor ? formatNumber(analytics.profit_factor) : '—'}
            />
          </div>
          <p className="text-xs italic text-mentor-muted">{analytics.interpretation}</p>
        </>
      )}
      {!loading && (!analytics || analytics.sample_size === 0) && (
        <EmptyHint>No journal data yet — log your first trade on the Journal page.</EmptyHint>
      )}
    </div>
  );
}

// ---------- news ----------

function NewsCard({ items, loading }: { items: NewsItem[]; loading: boolean }) {
  return (
    <div className="card-pad space-y-3">
      <div>
        <h2 className="section-title">News context</h2>
        <p className="text-xs text-mentor-muted">Recent headlines the classifier flagged as market-relevant.</p>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && items.length === 0 && (
        <EmptyHint>
          No classified news in the last window. Pull the latest from the Forecast page if you&apos;ve
          set NEWSAPI_KEY.
        </EmptyHint>
      )}
      <ul className="space-y-2.5">
        {items.map((n) => (
          <li key={n.id} className="rounded-2xl border border-mentor-border bg-mentor-panelLight/40 p-3.5">
            <div className="flex items-center gap-2 text-xs">
              {n.classification && <span className="chip chip-accent capitalize">{n.classification.category}</span>}
              {n.classification && (
                <span className="text-mentor-muted">
                  impact {formatNumber(n.classification.impact, 2)} · {new Date(n.ts).toLocaleString()}
                </span>
              )}
            </div>
            <a
              className="mt-1.5 block text-sm font-medium text-mentor-fg hover:text-mentor-accent hover:underline"
              href={n.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {n.headline}
            </a>
            {n.classification?.rationale && (
              <p className="mt-1 text-xs text-mentor-muted">{n.classification.rationale}</p>
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
  const openRisk = open.reduce((sum, t) => sum + Number(t.initial_risk.amount ?? 0), 0);
  const currency = trades[0]?.initial_risk.currency ?? 'USD';
  return (
    <div className="card-pad space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">Open risk &amp; alerts</h2>
          <p className="text-xs text-mentor-muted">What&apos;s live right now, and how much is on the line.</p>
        </div>
        <button type="button" onClick={onSweep} disabled={sweepPending} className="btn-ghost">
          {sweepPending ? 'Checking…' : 'Sweep alerts'}
        </button>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:max-w-md">
        <Metric label="Open positions" value={open.length} />
        <Metric
          label="Total open risk"
          value={openRisk ? formatMoney(openRisk, currency) : '—'}
          tone={openRisk > 0 ? 'warn' : 'default'}
        />
      </div>
      {!loading && open.length === 0 && (
        <EmptyHint>Nothing open. The boring days are usually the most profitable.</EmptyHint>
      )}
      {open.length > 0 && (
        <ul className="space-y-2 text-sm">
          {open.map((t) => (
            <li
              key={t.id}
              className="flex items-center justify-between rounded-xl bg-mentor-panelLight/50 px-3.5 py-2.5"
            >
              <span className="font-mono">
                {t.symbol} · {t.direction} · {formatNumber(t.size_lots, 2)} lots
              </span>
              <span className="text-mentor-muted">stop {Number(t.planned_stop).toFixed(5)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function EmptyHint({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-mentor-border bg-mentor-panelLight/30 p-4 text-sm text-mentor-muted">
      {children}
    </div>
  );
}
