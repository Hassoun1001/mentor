import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import {
  type BacktestResponse,
  type BacktestRequest,
  compareStrategies,
  listStrategies,
  runBacktest,
} from '../api/backtest';
import { ApiError } from '../api/client';
import { listInstruments } from '../api/risk';
import { ComparisonChart } from '../components/ComparisonChart';
import { EquityCurve } from '../components/EquityCurve';
import { Metric } from '../components/Metric';
import { formatMoney, formatNumber, formatPercent } from '../lib/format';

interface FormState {
  symbol: string;
  timeframe: '1m' | '5m' | '1h' | '1d';
  daysBack: string;
  strategy: string;
  fastPeriod: string;
  slowPeriod: string;
  atrMultiple: string;
  startingAmount: string;
  currency: string;
  riskPercent: string;
  spreadPips: string;
  slippagePips: string;
  commission: string;
  doWalkForward: boolean;
  windows: string;
}

const DEFAULT: FormState = {
  symbol: 'EURUSD',
  timeframe: '1h',
  daysBack: '180',
  strategy: 'ma_crossover',
  fastPeriod: '20',
  slowPeriod: '50',
  atrMultiple: '2',
  startingAmount: '10000',
  currency: 'USD',
  riskPercent: '1',
  spreadPips: '0.8',
  slippagePips: '0.2',
  commission: '0',
  doWalkForward: true,
  windows: '4',
};

export function BacktesterPage() {
  const [form, setForm] = useState<FormState>(DEFAULT);
  const [error, setError] = useState<string | null>(null);
  const [compareTo, setCompareTo] = useState<BacktestResponse | null>(null);

  const instruments = useQuery({ queryKey: ['instruments'], queryFn: listInstruments });
  const strategies = useQuery({ queryKey: ['strategies'], queryFn: listStrategies });

  const mutation = useMutation({
    mutationFn: runBacktest,
    onSuccess: () => setError(null),
    onError: (err) => {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Backtest failed — make sure bars are ingested for this window.'
      );
    },
  });

  const pinAsBaseline = () => {
    if (mutation.data) {
      setCompareTo(mutation.data);
      mutation.reset();
    }
  };

  const clearComparison = () => setCompareTo(null);

  const submit = () => {
    const days = Number(form.daysBack) || 30;
    const now = new Date();
    const start = new Date(now.getTime() - days * 86400 * 1000);

    const params: Record<string, unknown> = {};
    if (form.strategy === 'ma_crossover') {
      params.fast_period = Number(form.fastPeriod);
      params.slow_period = Number(form.slowPeriod);
      params.atr_stop_multiple = form.atrMultiple;
    }

    const body: BacktestRequest = {
      symbol: form.symbol,
      timeframe: form.timeframe,
      start: start.toISOString(),
      end: now.toISOString(),
      strategy: form.strategy,
      strategy_params: params,
      starting_balance: { amount: form.startingAmount, currency: form.currency },
      risk_per_trade_percent: form.riskPercent,
      cost_model: {
        spread_pips: form.spreadPips,
        slippage_pips: form.slippagePips,
        commission_per_lot_round_trip: form.commission,
      },
      do_walk_forward: form.doWalkForward,
      walk_forward_windows: Number(form.windows) || 4,
    };
    mutation.mutate(body);
  };

  const result = mutation.data;

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Backtester</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          The backtester is the judge of everything. No signal reaches the
          dashboard until it survives this — out-of-sample, cost-aware,
          and lookahead-impossible by construction.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr,1fr]">
        <div className="panel-pad space-y-4">
          <h2 className="font-medium text-mentor-fg">Run</h2>

          <div className="grid grid-cols-2 gap-4">
            <Labelled label="Instrument">
              <select
                className="input"
                value={form.symbol}
                onChange={(e) => setForm({ ...form, symbol: e.target.value })}
              >
                {(instruments.data ?? []).map((i) => (
                  <option key={i.symbol} value={i.symbol}>
                    {i.base}/{i.quote}
                  </option>
                ))}
              </select>
            </Labelled>
            <Labelled label="Timeframe">
              <div className="flex gap-2">
                {(['5m', '1h', '1d'] as const).map((tf) => (
                  <button
                    key={tf}
                    type="button"
                    onClick={() => setForm({ ...form, timeframe: tf })}
                    className={
                      'flex-1 rounded-md border px-2 py-1.5 text-sm font-mono ' +
                      (tf === form.timeframe
                        ? 'border-mentor-accent bg-mentor-accent/15 text-mentor-fg'
                        : 'border-mentor-border bg-mentor-panelLight text-mentor-muted')
                    }
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </Labelled>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Labelled label="Days back">
              <input
                className="input"
                type="number"
                value={form.daysBack}
                onChange={(e) => setForm({ ...form, daysBack: e.target.value })}
              />
            </Labelled>
            <Labelled label="Start balance">
              <input
                className="input"
                type="number"
                value={form.startingAmount}
                onChange={(e) => setForm({ ...form, startingAmount: e.target.value })}
              />
            </Labelled>
            <Labelled label="Risk %">
              <input
                className="input"
                type="number"
                step="0.1"
                value={form.riskPercent}
                onChange={(e) => setForm({ ...form, riskPercent: e.target.value })}
              />
            </Labelled>
          </div>

          <Labelled label="Strategy">
            <select
              className="input"
              value={form.strategy}
              onChange={(e) => setForm({ ...form, strategy: e.target.value })}
            >
              {(strategies.data ?? []).map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
          </Labelled>

          {form.strategy === 'ma_crossover' && (
            <div className="grid grid-cols-3 gap-4">
              <Labelled label="Fast EMA">
                <input
                  className="input"
                  type="number"
                  value={form.fastPeriod}
                  onChange={(e) => setForm({ ...form, fastPeriod: e.target.value })}
                />
              </Labelled>
              <Labelled label="Slow EMA">
                <input
                  className="input"
                  type="number"
                  value={form.slowPeriod}
                  onChange={(e) => setForm({ ...form, slowPeriod: e.target.value })}
                />
              </Labelled>
              <Labelled label="ATR stop ×">
                <input
                  className="input"
                  type="number"
                  step="0.5"
                  value={form.atrMultiple}
                  onChange={(e) => setForm({ ...form, atrMultiple: e.target.value })}
                />
              </Labelled>
            </div>
          )}

          <div className="grid grid-cols-3 gap-4">
            <Labelled label="Spread pips">
              <input
                className="input"
                type="number"
                step="0.1"
                value={form.spreadPips}
                onChange={(e) => setForm({ ...form, spreadPips: e.target.value })}
              />
            </Labelled>
            <Labelled label="Slippage pips">
              <input
                className="input"
                type="number"
                step="0.1"
                value={form.slippagePips}
                onChange={(e) => setForm({ ...form, slippagePips: e.target.value })}
              />
            </Labelled>
            <Labelled label="Comm/lot">
              <input
                className="input"
                type="number"
                step="0.5"
                value={form.commission}
                onChange={(e) => setForm({ ...form, commission: e.target.value })}
              />
            </Labelled>
          </div>

          <label className="flex items-center gap-2 text-sm text-mentor-fg">
            <input
              type="checkbox"
              checked={form.doWalkForward}
              onChange={(e) =>
                setForm({ ...form, doWalkForward: e.target.checked })
              }
            />
            <span>Walk-forward validation</span>
            {form.doWalkForward && (
              <input
                className="input ml-2 w-16"
                type="number"
                value={form.windows}
                onChange={(e) => setForm({ ...form, windows: e.target.value })}
              />
            )}
          </label>

          {error && (
            <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
              {error}
            </div>
          )}

          <button
            type="button"
            disabled={mutation.isPending}
            onClick={submit}
            className="btn-primary w-full"
          >
            {mutation.isPending ? 'Running…' : 'Run backtest'}
          </button>

          {result && !compareTo && (
            <button
              type="button"
              onClick={pinAsBaseline}
              className="w-full rounded-lg border border-mentor-border bg-mentor-panelLight px-4 py-2 text-xs text-mentor-muted hover:text-mentor-fg"
            >
              Pin this run as baseline (A) and compare with next
            </button>
          )}
          {compareTo && (
            <div className="rounded-lg border border-mentor-accent/40 bg-mentor-accent/5 p-3 text-xs">
              <div className="flex items-center justify-between gap-2">
                <span>
                  Baseline pinned: <code className="font-mono">{compareTo.strategy}</code>
                </span>
                <button
                  type="button"
                  onClick={clearComparison}
                  className="rounded-md border border-mentor-border bg-mentor-panelLight px-2 py-0.5 text-mentor-muted hover:text-mentor-fg"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>

        <ResultsPanel result={result} />
      </div>

      {result && compareTo && (
        <ComparisonPanel a={compareTo} b={result} />
      )}

      {result && !compareTo && (
        <>
          <EquityPanel result={result} />
          {result.walk_forward && <WalkForwardPanel wf={result.walk_forward} />}
          <TradesPanel result={result} />
        </>
      )}

      <CompareAllPanel form={form} strategyNames={(strategies.data ?? []).map((s) => s.name)} />
    </section>
  );
}

function CompareAllPanel({
  form,
  strategyNames,
}: {
  form: FormState;
  strategyNames: string[];
}) {
  const compare = useMutation({ mutationFn: compareStrategies });

  const run = () => {
    const days = Number(form.daysBack) || 30;
    const now = new Date();
    const start = new Date(now.getTime() - days * 86400 * 1000);
    compare.mutate({
      symbol: form.symbol,
      timeframe: form.timeframe,
      start: start.toISOString(),
      end: now.toISOString(),
      strategies: strategyNames.map((name) => ({ strategy: name, strategy_params: {} })),
      starting_balance: { amount: form.startingAmount, currency: form.currency },
      risk_per_trade_percent: form.riskPercent,
      cost_model: {
        spread_pips: form.spreadPips,
        slippage_pips: form.slippagePips,
        commission_per_lot_round_trip: form.commission,
      },
    });
  };

  const ranked = [...(compare.data?.entries ?? [])].sort(
    (a, b) => Number(b.metrics.total_return_pct) - Number(a.metrics.total_return_pct)
  );

  return (
    <div className="panel-pad space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-medium text-mentor-fg">Compare all strategies</h2>
          <p className="text-xs text-mentor-muted">
            Every strategy over the <b>same</b> window, costs and risk — an honest apples-to-apples
            ranking. A fancy idea has to beat these baselines to be worth trading.
          </p>
        </div>
        <button
          type="button"
          disabled={compare.isPending || strategyNames.length < 2}
          onClick={run}
          className="btn-primary"
        >
          {compare.isPending ? 'Running…' : 'Compare'}
        </button>
      </div>

      {compare.error instanceof ApiError && (
        <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
          {compare.error.message}
        </div>
      )}

      {ranked.length > 0 && (
        <table className="w-full text-xs">
          <thead className="text-mentor-muted">
            <tr className="border-b border-mentor-border">
              <th className="py-2 text-left">#</th>
              <th className="py-2 text-left">Strategy</th>
              <th className="py-2 text-right">Return</th>
              <th className="py-2 text-right">Max DD</th>
              <th className="py-2 text-right">Expectancy</th>
              <th className="py-2 text-right">Trades</th>
              <th className="py-2 text-right">Win rate</th>
              <th className="py-2 text-right">End balance</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((e, i) => {
              const ret = Number(e.metrics.total_return_pct);
              return (
                <tr key={e.label} className="border-b border-mentor-border">
                  <td className="py-1.5 text-mentor-muted">{i + 1}</td>
                  <td className="py-1.5 font-mono">{e.label}</td>
                  <td
                    className={
                      'py-1.5 text-right font-mono ' +
                      (ret > 0 ? 'text-mentor-accentSoft' : ret < 0 ? 'text-mentor-danger' : '')
                    }
                  >
                    {ret > 0 ? '+' : ''}
                    {ret.toFixed(1)}%
                  </td>
                  <td className="py-1.5 text-right font-mono text-mentor-warn">
                    {Number(e.metrics.max_drawdown_pct).toFixed(1)}%
                  </td>
                  <td className="py-1.5 text-right font-mono">
                    {Number(e.metrics.expectancy_r).toFixed(2)}R
                  </td>
                  <td className="py-1.5 text-right font-mono text-mentor-muted">
                    {e.metrics.trade_count}
                  </td>
                  <td className="py-1.5 text-right font-mono">
                    {Math.round(Number(e.metrics.win_rate_pct))}%
                  </td>
                  <td className="py-1.5 text-right font-mono">
                    {formatMoney(e.ending_balance, compare.data?.currency ?? 'USD')}
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

function ComparisonPanel({ a, b }: { a: BacktestResponse; b: BacktestResponse }) {
  const winnerLabel = (() => {
    const ea = Number(a.metrics.expectancy_r);
    const eb = Number(b.metrics.expectancy_r);
    if (ea === eb) return 'tied';
    return ea > eb ? a.strategy : b.strategy;
  })();
  return (
    <div className="panel-pad space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">Strategy comparison</h2>
        <span className="pill border-mentor-accent/30 text-mentor-accentSoft">
          Winner by expectancy: <span className="ml-1 font-mono">{winnerLabel}</span>
        </span>
      </div>
      <ComparisonChart
        primary={{ label: `A · ${a.strategy}`, points: a.equity_curve }}
        secondary={{ label: `B · ${b.strategy}`, points: b.equity_curve }}
      />
      <div className="grid grid-cols-2 gap-6">
        <ComparisonColumn label="A" run={a} />
        <ComparisonColumn label="B" run={b} />
      </div>
    </div>
  );
}

function ComparisonColumn({ label, run }: { label: string; run: BacktestResponse }) {
  return (
    <div className="space-y-2">
      <div className="text-xs uppercase tracking-wider text-mentor-muted">
        {label} · {run.strategy}
      </div>
      <table className="w-full text-xs">
        <tbody>
          <Row k="Total return" v={formatPercent(run.metrics.total_return_pct, 2)} />
          <Row k="Max drawdown" v={formatPercent(run.metrics.max_drawdown_pct, 2)} />
          <Row k="Expectancy" v={`${formatNumber(run.metrics.expectancy_r, 3)} R`} />
          <Row
            k="Profit factor"
            v={run.metrics.profit_factor ? formatNumber(run.metrics.profit_factor) : '—'}
          />
          <Row k="Trades" v={String(run.metrics.trade_count)} />
          <Row k="Win rate" v={formatPercent(run.metrics.win_rate_pct, 1)} />
          <Row k="Costs paid" v={formatMoney(run.metrics.total_costs_paid, run.currency)} />
          <Row k="Sharpe-ish" v={formatNumber(run.metrics.sharpe_like, 3)} />
        </tbody>
      </table>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <tr className="border-b border-mentor-border">
      <td className="py-1.5 text-mentor-muted">{k}</td>
      <td className="py-1.5 text-right font-mono">{v}</td>
    </tr>
  );
}

function Labelled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  );
}

function ResultsPanel({ result }: { result?: BacktestResponse }) {
  return (
    <div className="panel-pad">
      <h2 className="font-medium text-mentor-fg">Verdict</h2>
      {!result && (
        <p className="mt-4 text-sm text-mentor-muted">
          Run a backtest to see the metrics. The judge does not flatter.
        </p>
      )}
      {result && (
        <div className="mt-4 grid grid-cols-2 gap-3">
          <Metric
            label="Total return"
            value={formatPercent(result.metrics.total_return_pct, 2)}
            tone={Number(result.metrics.total_return_pct) > 0 ? 'positive' : 'danger'}
            sub={`${formatMoney(result.starting_balance, result.currency)} → ${formatMoney(result.ending_balance, result.currency)}`}
          />
          <Metric
            label="Max drawdown"
            value={formatPercent(result.metrics.max_drawdown_pct, 2)}
            tone={Number(result.metrics.max_drawdown_pct) > 25 ? 'danger' : 'warn'}
            sub={`${result.metrics.max_drawdown_duration_bars} bars`}
          />
          <Metric
            label="Trades"
            value={result.metrics.trade_count}
            sub={`win rate ${formatPercent(result.metrics.win_rate_pct, 1)}`}
          />
          <Metric
            label="Expectancy"
            value={`${formatNumber(result.metrics.expectancy_r, 3)} R`}
            tone={Number(result.metrics.expectancy_r) > 0 ? 'positive' : 'danger'}
            sub={`PF ${result.metrics.profit_factor ? formatNumber(result.metrics.profit_factor) : '—'}`}
          />
          <Metric
            label="Costs paid"
            value={formatMoney(result.metrics.total_costs_paid, result.currency)}
            sub={`${result.metrics.forced_closes} forced closes at end`}
          />
          <Metric
            label="Sharpe-ish"
            value={formatNumber(result.metrics.sharpe_like, 3)}
            sub="bar-return / std (not annualised)"
          />
        </div>
      )}
    </div>
  );
}

function EquityPanel({ result }: { result: BacktestResponse }) {
  return (
    <div className="panel-pad">
      <h2 className="mb-2 font-medium text-mentor-fg">Equity curve</h2>
      <EquityCurve points={result.equity_curve} />
    </div>
  );
}

function WalkForwardPanel({ wf }: { wf: NonNullable<BacktestResponse['walk_forward']> }) {
  return (
    <div className="panel-pad space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">Walk-forward</h2>
        {wf.is_overfit_signal && (
          <span className="pill border-mentor-danger/40 text-mentor-danger">
            ⚠ possible overfit
          </span>
        )}
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Metric
          label="In-sample expectancy"
          value={`${formatNumber(wf.in_sample_avg_expectancy_r, 3)} R`}
          tone={Number(wf.in_sample_avg_expectancy_r) > 0 ? 'positive' : 'default'}
        />
        <Metric
          label="Out-of-sample"
          value={`${formatNumber(wf.out_of_sample_avg_expectancy_r, 3)} R`}
          tone={
            Number(wf.out_of_sample_avg_expectancy_r) > 0 ? 'positive' : 'danger'
          }
        />
        <Metric
          label="Degradation"
          value={wf.degradation_pct ? formatPercent(wf.degradation_pct, 1) : '—'}
          tone={
            wf.degradation_pct && Number(wf.degradation_pct) > 50 ? 'danger' : 'default'
          }
        />
      </div>
      <table className="w-full text-xs">
        <thead className="text-mentor-muted">
          <tr className="border-b border-mentor-border">
            <th className="py-2 text-left">Window</th>
            <th className="py-2 text-right">Train R</th>
            <th className="py-2 text-right">Test R</th>
            <th className="py-2 text-right">Train trades</th>
            <th className="py-2 text-right">Test trades</th>
          </tr>
        </thead>
        <tbody>
          {wf.windows.map((w) => (
            <tr key={w.index} className="border-b border-mentor-border">
              <td className="py-2 font-mono">{w.index}</td>
              <td className="py-2 text-right font-mono">
                {formatNumber(w.train_metrics.expectancy_r, 3)}
              </td>
              <td className="py-2 text-right font-mono">
                {formatNumber(w.test_metrics.expectancy_r, 3)}
              </td>
              <td className="py-2 text-right text-mentor-muted">
                {w.train_metrics.trade_count}
              </td>
              <td className="py-2 text-right text-mentor-muted">
                {w.test_metrics.trade_count}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TradesPanel({ result }: { result: BacktestResponse }) {
  const recent = result.closed_trades.slice(-20).reverse();
  return (
    <div className="panel-pad space-y-3">
      <h2 className="font-medium text-mentor-fg">
        Last {recent.length} of {result.closed_trades.length} trades
      </h2>
      <table className="w-full text-xs">
        <thead className="text-mentor-muted">
          <tr className="border-b border-mentor-border">
            <th className="py-2 text-left">Entry</th>
            <th className="py-2 text-left">Side</th>
            <th className="py-2 text-right">Lots</th>
            <th className="py-2 text-right">Entry/Exit</th>
            <th className="py-2 text-right">Exit reason</th>
            <th className="py-2 text-right">R</th>
            <th className="py-2 text-right">PnL</th>
          </tr>
        </thead>
        <tbody>
          {recent.map((t) => (
            <tr key={t.entry_ts + t.exit_ts} className="border-b border-mentor-border">
              <td className="py-2 font-mono text-mentor-muted">
                {new Date(t.entry_ts).toLocaleString()}
              </td>
              <td className="py-2 capitalize">{t.direction}</td>
              <td className="py-2 text-right font-mono">{formatNumber(t.size_lots, 2)}</td>
              <td className="py-2 text-right font-mono text-mentor-muted">
                {Number(t.entry_price).toFixed(5)} → {Number(t.exit_price).toFixed(5)}
              </td>
              <td className="py-2 text-right text-mentor-muted">{t.exit_reason}</td>
              <td
                className={
                  'py-2 text-right font-mono ' +
                  (Number(t.realised_r) > 0
                    ? 'text-mentor-accentSoft'
                    : 'text-mentor-danger')
                }
              >
                {formatNumber(t.realised_r, 2)}
              </td>
              <td className="py-2 text-right font-mono text-mentor-muted">
                {formatMoney(t.realised_pnl, result.currency)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
