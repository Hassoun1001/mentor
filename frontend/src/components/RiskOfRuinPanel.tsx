import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import { runMonteCarlo, type MonteCarloResponse } from '../api/riskSim';
import { formatMoney, formatPercent } from '../lib/format';
import { Metric } from './Metric';

/**
 * Risk-of-ruin Monte Carlo panel.
 *
 * The simulator draws from the user's actual realised R-distribution
 * (when the journal has trades) or a fallback synthetic mix. The
 * mentor framing here is the plan's: median path is what *typical*
 * traders see; p5 is what 1-in-20 traders see. The number that
 * matters most is probability of ruin.
 */
export function RiskOfRuinPanel({ currency = 'USD' }: { currency?: string }) {
  const [riskPct, setRiskPct] = useState('1');
  const [nTrades, setNTrades] = useState('200');
  const [startingBalance, setStartingBalance] = useState('10000');

  const mutation = useMutation({
    mutationFn: runMonteCarlo,
    onError: () => {},
  });

  const run = () =>
    mutation.mutate({
      starting_balance: startingBalance,
      risk_per_trade_percent: riskPct,
      n_trades: Number(nTrades) || 200,
      n_runs: 5000,
      ruin_fraction: '0.5',
      use_journal: true,
      fallback_distribution: ['2', '-1', '-1', '2', '-1', '3', '-1'], // synthetic ~+0.4R EV
    });

  const result: MonteCarloResponse | undefined = mutation.data;
  const error =
    mutation.error instanceof ApiError ? mutation.error.message : null;

  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="font-medium text-mentor-fg">Risk-of-ruin simulator</h2>
        <p className="text-xs text-mentor-muted">
          5,000 paths over your realised R-distribution. The most
          important number is probability of ruin — surviving long enough
          to realise the edge is the whole game.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="label">Start balance</label>
          <input
            className="input"
            type="number"
            value={startingBalance}
            onChange={(e) => setStartingBalance(e.target.value)}
          />
        </div>
        <div>
          <label className="label">Risk %</label>
          <input
            className="input"
            type="number"
            step="0.5"
            value={riskPct}
            onChange={(e) => setRiskPct(e.target.value)}
          />
        </div>
        <div>
          <label className="label"># trades</label>
          <input
            className="input"
            type="number"
            value={nTrades}
            onChange={(e) => setNTrades(e.target.value)}
          />
        </div>
      </div>

      <button
        type="button"
        onClick={run}
        disabled={mutation.isPending}
        className="w-full rounded-lg bg-mentor-accent px-4 py-2 text-sm font-medium text-white hover:bg-mentor-accentSoft disabled:opacity-50"
      >
        {mutation.isPending ? 'Simulating…' : 'Simulate'}
      </button>

      {error && (
        <div className="rounded-lg border border-mentor-warn/40 bg-mentor-warn/10 p-2 text-xs text-mentor-warn">
          {error}
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="Probability of ruin"
              value={formatPercent(Number(result.probability_of_ruin) * 100, 2)}
              tone={
                Number(result.probability_of_ruin) > 0.05 ? 'danger' : 'positive'
              }
              sub={`ruin at ${formatMoney(result.ruin_threshold, currency)}`}
            />
            <Metric
              label="Median terminal"
              value={formatMoney(result.median_terminal, currency)}
              sub={`50th percentile of ${result.n_runs.toLocaleString()} paths`}
            />
            <Metric
              label="P5 terminal"
              value={formatMoney(result.p5_terminal, currency)}
              tone="warn"
              sub="what 1-in-20 traders see"
            />
            <Metric
              label="P95 max drawdown"
              value={formatPercent(result.p95_max_drawdown_pct, 1)}
              tone={Number(result.p95_max_drawdown_pct) > 30 ? 'danger' : 'warn'}
              sub="95th percentile worst path"
            />
          </div>
          <p className="text-xs text-mentor-muted">
            {result.used_journal
              ? `Sampled from ${result.sample_size} closed trades in your journal.`
              : 'No closed trades in the journal — used a synthetic fallback distribution. The simulator becomes more accurate as you log real trades.'}
          </p>
        </>
      )}
    </div>
  );
}
