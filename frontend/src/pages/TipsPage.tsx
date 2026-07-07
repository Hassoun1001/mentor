import { Fragment, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import {
  type AnalystSnapshot,
  type BacktestResponse,
  type Bucket,
  type LeaderboardRow,
  type ScoredResponse,
  type TipOutcome,
  getAnalyst,
  getLeaderboard,
  getScored,
  getTipsters,
  ingestTips,
  runFollowBacktest,
} from '../api/tips';
import { EquityCurve } from '../components/EquityCurve';
import { Metric } from '../components/Metric';

export function TipsPage() {
  const queryClient = useQueryClient();
  const [tipster, setTipster] = useState('Mohit');
  const [text, setText] = useState('');
  const [banner, setBanner] = useState<string | null>(null);

  const scored = useQuery({ queryKey: ['tips-scored'], queryFn: () => getScored() });

  const ingest = useMutation({
    mutationFn: () => ingestTips({ tipster, text }),
    onSuccess: (r) => {
      setBanner(
        `Parsed ${r.parsed} tips from ${r.tipster}, priced ${r.priced}.` +
          (r.unpriced_tickers.length ? ` No price for: ${r.unpriced_tickers.join(', ')}.` : '')
      );
      setText('');
      queryClient.invalidateQueries({ queryKey: ['tips-scored'] });
    },
    onError: (e) => setBanner(e instanceof ApiError ? e.message : 'Ingest failed.'),
  });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Tip tracker</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          Paste a tipster's message. The system extracts every call, snapshots
          the price the day they said it, and tracks what actually happened —
          building an honest track record of whether following them makes money.
          It never tells you to buy; it tells you how their past calls did.
        </p>
      </header>

      {banner && (
        <div className="rounded-lg border border-mentor-accent/40 bg-mentor-accent/5 p-3 text-sm text-mentor-fg">
          {banner}
        </div>
      )}

      <div className="panel-pad space-y-3">
        <div className="flex items-center gap-3">
          <label className="text-sm text-mentor-muted" htmlFor="tipster">
            Tipster
          </label>
          <input
            id="tipster"
            value={tipster}
            onChange={(e) => setTipster(e.target.value)}
            className="rounded-lg border border-mentor-border bg-mentor-panelLight px-3 py-1.5 text-sm text-mentor-fg"
          />
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          placeholder="Paste the WhatsApp message with the stock tips here…"
          className="w-full rounded-lg border border-mentor-border bg-mentor-panelLight px-3 py-2 text-sm text-mentor-fg placeholder:text-mentor-muted"
        />
        <button
          type="button"
          disabled={ingest.isPending || !text.trim() || !tipster.trim()}
          onClick={() => ingest.mutate()}
          className="btn-primary"
        >
          {ingest.isPending ? 'Parsing…' : 'Parse & track'}
        </button>
      </div>

      <ScorecardPanel data={scored.data} loading={scored.isLoading} />
      <OutcomesTable outcomes={scored.data?.outcomes ?? []} />

      <LeaderboardPanel />
      <FollowBacktestPanel />

      <p className="text-xs text-mentor-muted">
        Not financial advice. A tipster's past hit-rate does not predict their
        next call — markets are efficient and these are volatile names. This tool
        measures a track record so you can decide how much weight to give it.
      </p>
    </section>
  );
}

function pct(v: string): number {
  return Number(v);
}

function toneForReturn(v: number): 'positive' | 'danger' | 'default' {
  if (v > 0.5) return 'positive';
  if (v < -0.5) return 'danger';
  return 'default';
}

function ScorecardPanel({ data, loading }: { data: ScoredResponse | undefined; loading: boolean }) {
  if (loading) return <div className="panel-pad text-sm text-mentor-muted">Loading scorecard…</div>;
  if (!data || data.scorecard.total === 0) {
    return (
      <div className="panel-pad text-sm text-mentor-muted">
        {data?.scorecard.headline ?? 'No tips tracked yet — paste a message above.'}
      </div>
    );
  }
  const s = data.scorecard;
  const meanRet = pct(s.overall.mean_return_pct);
  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="font-medium text-mentor-fg">{s.tipster}'s track record</h2>
        <p className="text-xs leading-relaxed text-mentor-muted">{s.headline}</p>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Metric label="Tracked calls" value={s.overall.count} sub={`~${s.overall.avg_days_held} days avg`} />
        <Metric
          label="Avg return"
          value={`${meanRet > 0 ? '+' : ''}${meanRet.toFixed(1)}%`}
          tone={toneForReturn(meanRet)}
        />
        <Metric
          label="Win rate"
          value={`${Math.round(pct(s.overall.win_rate) * 100)}%`}
          tone={pct(s.overall.win_rate) > 0.55 ? 'positive' : 'warn'}
          sub="calls that went up"
        />
        <Metric
          label="Dip calls that dipped"
          value={s.dip_accuracy != null ? `${Math.round(pct(s.dip_accuracy) * 100)}%` : '—'}
          sub="'buy on dip' accuracy"
        />
      </div>

      <BucketTable title="By category" buckets={s.by_category} />
      <BucketTable title="By action" buckets={s.by_action} />
    </div>
  );
}

function BucketTable({ title, buckets }: { title: string; buckets: Bucket[] }) {
  if (buckets.length === 0) return null;
  return (
    <div>
      <div className="mb-2 text-xs uppercase tracking-wider text-mentor-muted">{title}</div>
      <table className="w-full text-xs">
        <thead className="text-mentor-muted">
          <tr className="border-b border-mentor-border">
            <th className="py-1.5 text-left">Bucket</th>
            <th className="py-1.5 text-right">Calls</th>
            <th className="py-1.5 text-right">Avg return</th>
            <th className="py-1.5 text-right">Win rate</th>
            <th className="py-1.5 text-left">Best / worst</th>
          </tr>
        </thead>
        <tbody>
          {buckets.map((b) => {
            const mean = pct(b.mean_return_pct);
            return (
              <tr key={b.key} className="border-b border-mentor-border">
                <td className="py-1.5 font-mono">{b.key}</td>
                <td className="py-1.5 text-right">{b.count}</td>
                <td
                  className={
                    'py-1.5 text-right font-mono ' +
                    (mean > 0 ? 'text-mentor-accentSoft' : mean < 0 ? 'text-mentor-danger' : '')
                  }
                >
                  {mean > 0 ? '+' : ''}
                  {mean.toFixed(1)}%
                </td>
                <td className="py-1.5 text-right">{Math.round(pct(b.win_rate) * 100)}%</td>
                <td className="py-1.5 text-mentor-muted">
                  {b.best_ticker} ({pct(b.best_return_pct).toFixed(1)}%) /{' '}
                  {b.worst_ticker} ({pct(b.worst_return_pct).toFixed(1)}%)
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function OutcomesTable({ outcomes }: { outcomes: TipOutcome[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  if (outcomes.length === 0) return null;
  const sorted = [...outcomes].sort((a, b) => pct(b.return_pct) - pct(a.return_pct));
  const atEntry = outcomes.filter((o) => o.at_or_below_entry);
  return (
    <div className="panel-pad space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">
          Every call <span className="text-mentor-muted">({outcomes.length})</span>
        </h2>
        <span className="text-[11px] text-mentor-muted">click a row for Wall-Street coverage</span>
      </div>
      {atEntry.length > 0 && (
        <div className="rounded-lg border border-mentor-warn/40 bg-mentor-warn/10 p-3 text-xs text-mentor-warn">
          <b>{atEntry.length}</b> of his buy calls{' '}
          {atEntry.length === 1 ? 'is' : 'are'} back at or below the price he named:{' '}
          <span className="font-mono">{atEntry.map((o) => o.ticker).join(', ')}</span>. Objective
          observation — not a recommendation to buy.
        </div>
      )}
      <table className="w-full text-xs">
        <thead className="text-mentor-muted">
          <tr className="border-b border-mentor-border">
            <th className="py-2 text-left">Ticker</th>
            <th className="py-2 text-left">Call</th>
            <th className="py-2 text-right">Entry</th>
            <th className="py-2 text-right">Now</th>
            <th className="py-2 text-right">Today</th>
            <th className="py-2 text-right">Since call</th>
            <th className="py-2 text-right">Peak / trough</th>
            <th className="py-2 text-right">Volatility</th>
            <th className="py-2 text-left">Note</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((o) => {
            const ret = pct(o.return_pct);
            const key = `${o.ticker}-${o.action}`;
            const isOpen = expanded === key;
            return (
              <Fragment key={key}>
                <tr
                  onClick={() => setExpanded(isOpen ? null : key)}
                  className="cursor-pointer border-b border-mentor-border hover:bg-mentor-panelLight/40"
                >
                  <td className="py-2 font-mono font-medium">
                    <span className="mr-1 text-mentor-muted">{isOpen ? '▾' : '▸'}</span>
                    {o.ticker}
                  </td>
                <td className="py-2">
                  <span className="capitalize">{o.action.replace(/_/g, ' ')}</span>
                  {o.dipped != null && (
                    <span className="ml-1 text-mentor-muted">{o.dipped ? '· dipped ✓' : '· no dip'}</span>
                  )}
                  {o.at_or_below_entry && (
                    <span className="ml-1 rounded bg-mentor-warn/20 px-1 text-mentor-warn">
                      at entry
                    </span>
                  )}
                </td>
                <td className="py-2 text-right font-mono text-mentor-muted">{Number(o.mention_price).toFixed(2)}</td>
                <td className="py-2 text-right font-mono">{Number(o.current_price).toFixed(2)}</td>
                <td
                  className={
                    'py-2 text-right font-mono ' +
                    (o.daily_change_pct == null
                      ? 'text-mentor-muted'
                      : pct(o.daily_change_pct) > 0
                        ? 'text-mentor-accentSoft'
                        : pct(o.daily_change_pct) < 0
                          ? 'text-mentor-danger'
                          : 'text-mentor-muted')
                  }
                >
                  {o.daily_change_pct == null
                    ? '—'
                    : `${pct(o.daily_change_pct) > 0 ? '+' : ''}${pct(o.daily_change_pct).toFixed(1)}%`}
                </td>
                <td
                  className={
                    'py-2 text-right font-mono ' +
                    (ret > 0 ? 'text-mentor-accentSoft' : ret < 0 ? 'text-mentor-danger' : '')
                  }
                >
                  {ret > 0 ? '+' : ''}
                  {ret.toFixed(1)}%
                </td>
                <td className="py-2 text-right font-mono text-mentor-muted">
                  +{pct(o.max_drawup_pct).toFixed(1)} / {pct(o.max_drawdown_pct).toFixed(1)}
                </td>
                <td className="py-2 text-right">
                  {o.expected_move_pct != null ? (
                    <span
                      className={
                        'font-mono ' +
                        (o.vol_regime === 'wide'
                          ? 'text-mentor-danger'
                          : o.vol_regime === 'calm'
                            ? 'text-mentor-accentSoft'
                            : 'text-mentor-muted')
                      }
                      title={`${o.vol_regime} — typical 5-day swing`}
                    >
                      ±{pct(o.expected_move_pct).toFixed(1)}%
                    </span>
                  ) : (
                    <span className="text-mentor-muted">—</span>
                  )}
                </td>
                  <td className="py-2 text-mentor-muted">{o.note}</td>
                </tr>
                {isOpen && (
                  <tr>
                    <td colSpan={9} className="border-b border-mentor-border bg-mentor-bg/30 px-2 py-3">
                      <AnalystPanel ticker={o.ticker} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------- analyst coverage ----------

function AnalystPanel({ ticker }: { ticker: string }) {
  const q = useQuery({
    queryKey: ['analyst', ticker],
    queryFn: () => getAnalyst(ticker),
    staleTime: 10 * 60 * 1000,
  });

  if (q.isLoading) return <p className="px-2 text-xs text-mentor-muted">Loading Wall-Street coverage…</p>;
  const a: AnalystSnapshot | undefined = q.data;
  if (!a || !a.available) {
    return (
      <p className="px-2 text-xs text-mentor-muted">
        No analyst data available for {ticker} right now.
      </p>
    );
  }
  const c = a.consensus;
  const upside = c?.upside_pct != null ? Number(c.upside_pct) : null;
  const total = c ? c.strong_buy + c.buy + c.hold + c.sell + c.strong_sell : 0;
  const buys = c ? c.strong_buy + c.buy : 0;
  const holds = c ? c.hold : 0;
  const sells = c ? c.sell + c.strong_sell : 0;
  const bp = total ? (buys / total) * 100 : 0;
  const hp = total ? (holds / total) * 100 : 0;
  const sp = total ? (sells / total) * 100 : 0;

  return (
    <div className="space-y-3 px-2">
      {c && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-mentor-border/60 bg-mentor-panelLight/40 px-3 py-2">
            <div className="metric-label">Consensus target</div>
            <div className="font-mono text-lg text-mentor-fg">
              {c.target_mean != null ? `$${Number(c.target_mean).toFixed(0)}` : '—'}
            </div>
            <div className="text-[11px] text-mentor-muted">
              {c.target_low != null && c.target_high != null
                ? `$${Number(c.target_low).toFixed(0)}–$${Number(c.target_high).toFixed(0)}`
                : ''}
            </div>
          </div>
          <div className="rounded-lg border border-mentor-border/60 bg-mentor-panelLight/40 px-3 py-2">
            <div className="metric-label">Implied upside</div>
            <div
              className={
                'font-mono text-lg ' +
                (upside == null ? 'text-mentor-muted' : upside >= 0 ? 'text-mentor-accentSoft' : 'text-mentor-danger')
              }
            >
              {upside == null ? '—' : `${upside >= 0 ? '+' : ''}${upside.toFixed(1)}%`}
            </div>
            <div className="text-[11px] text-mentor-muted">
              {a.current_price != null ? `now $${Number(a.current_price).toFixed(2)}` : ''}
            </div>
          </div>
          <div className="rounded-lg border border-mentor-border/60 bg-mentor-panelLight/40 px-3 py-2">
            <div className="metric-label">Rating</div>
            <div className="text-sm font-medium capitalize text-mentor-fg">
              {c.rating_key ? c.rating_key.replace(/_/g, ' ') : '—'}
            </div>
            <div className="text-[11px] text-mentor-muted">{c.num_analysts ?? 0} analysts</div>
          </div>
          <div className="rounded-lg border border-mentor-border/60 bg-mentor-panelLight/40 px-3 py-2">
            <div className="metric-label">Buy / hold / sell</div>
            <div className="mt-1.5 flex h-2 overflow-hidden rounded-full bg-mentor-panelLight">
              <div style={{ width: `${bp}%` }} className="bg-mentor-accentSoft" />
              <div style={{ width: `${hp}%` }} className="bg-mentor-muted" />
              <div style={{ width: `${sp}%` }} className="bg-mentor-danger" />
            </div>
            <div className="mt-1 font-mono text-[11px] text-mentor-muted">
              {buys} / {holds} / {sells}
            </div>
          </div>
        </div>
      )}

      <div>
        <div className="mb-1.5 text-[11px] uppercase tracking-wider text-mentor-muted">
          Bank ratings
        </div>
        {a.ratings.length === 0 ? (
          <p className="text-xs text-mentor-muted">No recent bank ratings on record.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {a.ratings.map((r) => (
              <span
                key={r.firm}
                className="inline-flex items-center gap-1.5 rounded-md border border-mentor-border bg-mentor-panelLight/50 px-2 py-1 text-[11px]"
                title={new Date(r.date).toLocaleDateString()}
              >
                <span className="text-mentor-fg">{r.firm}</span>
                <span className="font-medium text-mentor-accentSoft">{r.rating}</span>
                {r.action === 'up' && <span className="text-mentor-accentSoft">↑</span>}
                {r.action === 'down' && <span className="text-mentor-danger">↓</span>}
              </span>
            ))}
          </div>
        )}
      </div>

      <p className="text-[11px] text-mentor-muted">{a.note}</p>
    </div>
  );
}

// ---------- leaderboard ----------

function LeaderboardPanel() {
  const board = useQuery({ queryKey: ['tips-leaderboard'], queryFn: getLeaderboard });
  const rows: LeaderboardRow[] = board.data ?? [];
  return (
    <div className="panel-pad space-y-3">
      <div>
        <h2 className="font-medium text-mentor-fg">Tipster leaderboard</h2>
        <p className="text-xs text-mentor-muted">
          Ranked by risk-adjusted return (mean ÷ dispersion), so steady beats lucky. Measurement,
          not a recommendation to follow anyone.
        </p>
      </div>
      {board.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!board.isLoading && rows.length === 0 && (
        <p className="text-sm text-mentor-muted">No tipsters tracked yet.</p>
      )}
      {rows.length > 0 && (
        <table className="w-full text-xs">
          <thead className="text-mentor-muted">
            <tr className="border-b border-mentor-border">
              <th className="py-2 text-left">#</th>
              <th className="py-2 text-left">Tipster</th>
              <th className="py-2 text-right">Calls</th>
              <th className="py-2 text-right">Mean ret</th>
              <th className="py-2 text-right">Win rate</th>
              <th className="py-2 text-right">Risk-adj</th>
              <th className="py-2 text-left">Best</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const mean = pct(r.mean_return_pct);
              return (
                <tr key={r.tipster} className="border-b border-mentor-border">
                  <td className="py-1.5 text-mentor-muted">{i + 1}</td>
                  <td className="py-1.5 font-medium">{r.tipster}</td>
                  <td className="py-1.5 text-right font-mono text-mentor-muted">{r.tracked_calls}</td>
                  <td
                    className={
                      'py-1.5 text-right font-mono ' +
                      (mean > 0 ? 'text-mentor-accentSoft' : mean < 0 ? 'text-mentor-danger' : '')
                    }
                  >
                    {mean > 0 ? '+' : ''}
                    {mean.toFixed(1)}%
                  </td>
                  <td className="py-1.5 text-right font-mono">{Math.round(pct(r.win_rate) * 100)}%</td>
                  <td className="py-1.5 text-right font-mono">{pct(r.risk_adjusted).toFixed(2)}</td>
                  <td className="py-1.5 text-mentor-muted">
                    {r.best_ticker} ({pct(r.best_return_pct).toFixed(1)}%)
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------- "follow him" backtest ----------

function FollowBacktestPanel() {
  const tipsters = useQuery({ queryKey: ['tipsters'], queryFn: getTipsters });
  const [tipster, setTipster] = useState('');
  const [riskPct, setRiskPct] = useState(1);
  const [stopPct, setStopPct] = useState(10);

  const selected = tipster || tipsters.data?.[0] || '';

  const backtest = useMutation({
    mutationFn: () =>
      runFollowBacktest({ tipster: selected, risk_pct: riskPct / 100, stop_pct: stopPct / 100 }),
  });
  const r: BacktestResponse | undefined = backtest.data;

  // Map to the equity-curve component's shape with synthetic strictly-ascending
  // timestamps (trade sequence) so lightweight-charts never sees a duplicate.
  const curve = (r?.equity_curve ?? []).map((p, i) => ({
    ts: new Date(Date.UTC(2020, 0, 1) + i * 86400000).toISOString(),
    balance: p.equity,
  }));

  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="font-medium text-mentor-fg">What if I'd followed him?</h2>
        <p className="text-xs text-mentor-muted">
          Mechanically buys every actionable call at its mention price, sized to risk a fixed % of
          equity with a stop as the ceiling. Equity curve, drawdown and expectancy from
          already-known outcomes — a simulation, not advice.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <label className="label">Tipster</label>
          <select className="input" value={selected} onChange={(e) => setTipster(e.target.value)}>
            {(tipsters.data ?? []).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Risk / trade (%)</label>
          <input
            type="number"
            className="input"
            value={riskPct}
            min={0.1}
            max={50}
            step={0.5}
            onChange={(e) => setRiskPct(Number(e.target.value) || 1)}
          />
        </div>
        <div>
          <label className="label">Stop (%)</label>
          <input
            type="number"
            className="input"
            value={stopPct}
            min={1}
            max={90}
            step={1}
            onChange={(e) => setStopPct(Number(e.target.value) || 10)}
          />
        </div>
        <div className="flex items-end">
          <button
            type="button"
            disabled={backtest.isPending || !selected}
            onClick={() => backtest.mutate()}
            className="w-full btn-primary"
          >
            {backtest.isPending ? 'Simulating…' : 'Run backtest'}
          </button>
        </div>
      </div>

      {backtest.error instanceof ApiError && (
        <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
          {backtest.error.message}
        </div>
      )}

      {r && r.n_trades === 0 && (
        <p className="text-sm text-mentor-muted">{r.headline}</p>
      )}

      {r && r.n_trades > 0 && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Metric
              label="Total return"
              value={`${pct(r.total_return_pct) >= 0 ? '+' : ''}${pct(r.total_return_pct).toFixed(1)}%`}
              tone={pct(r.total_return_pct) >= 0 ? 'positive' : 'danger'}
              sub={`$${Number(r.starting_equity).toLocaleString()} → $${Number(r.ending_equity).toLocaleString()}`}
            />
            <Metric label="Max drawdown" value={`${pct(r.max_drawdown_pct).toFixed(1)}%`} tone="warn" />
            <Metric label="Expectancy" value={`${pct(r.expectancy_r).toFixed(2)}R`} sub={`${r.n_trades} trades`} />
            <Metric label="Win rate" value={`${Math.round(pct(r.win_rate) * 100)}%`} />
          </div>
          <p className="text-xs leading-relaxed text-mentor-muted">{r.headline}</p>
          <div className="rounded-xl border border-mentor-border bg-mentor-panelLight/40 p-2">
            <EquityCurve points={curve} height={260} />
          </div>
          <p className="text-[11px] text-mentor-muted">{r.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
