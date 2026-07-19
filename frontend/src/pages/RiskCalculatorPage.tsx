import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import {
  calculatePositionSize,
  type Direction,
  listInstruments,
  type PositionSizeResponse,
} from '../api/risk';
import { fetchVolatility } from '../api/forecast';
import { ApiError } from '../api/client';
import { Field } from '../components/Field';
import { Metric } from '../components/Metric';
import { RiskOfRuinPanel } from '../components/RiskOfRuinPanel';
import { WhyButton } from '../components/WhyButton';
import { formatLots, formatMoney, formatNumber, formatPercent } from '../lib/format';

interface FormState {
  symbol: string;
  accountAmount: string;
  accountCurrency: string;
  riskPercent: string;
  direction: Direction;
  entry: string;
  stop: string;
  target: string;
  quoteToAccountRate: string;
}

const DEFAULT_STATE: FormState = {
  symbol: 'EURUSD',
  accountAmount: '10000',
  accountCurrency: 'USD',
  riskPercent: '1',
  direction: 'long',
  entry: '1.08500',
  stop: '1.08200',
  target: '1.09100',
  quoteToAccountRate: '1',
};

const EXPLAINERS = {
  risk: (
    <>
      The percentage of account equity you're willing to lose if this trade hits its stop.
      The textbook discipline is 1–2% per trade — anything higher risks compounding losses
      into a hole that's hard to climb out of.
    </>
  ),
  entry: (
    <>
      The price at which you intend to open the trade. The size calculator assumes you get
      filled at this price; in fast markets <em>slippage</em> may move the actual fill.
    </>
  ),
  stop: (
    <>
      The price at which you'll exit if the trade goes against you. The further the stop
      from entry, the smaller the position must be to keep risk within budget. No stop,
      no trade.
    </>
  ),
  target: (
    <>
      The price at which you'll take profit. Combined with the stop, this gives the
      risk:reward ratio — a 1:2 R:R means you can be right less than half the time and
      still come out ahead.
    </>
  ),
  lots: (
    <>
      The standardised trade size. One standard lot is 100,000 units of the base
      currency; a 0.10 lot is a "mini" (10,000 units), and 0.01 is a "micro" (1,000
      units). The calculator rounds <em>down</em> to your broker's minimum step so risk
      stays within budget.
    </>
  ),
  pipDistance: (
    <>
      The distance from entry to stop, expressed in pips. A pip is the smallest standard
      price increment — 0.0001 for most forex majors, 0.01 for JPY-quoted pairs.
    </>
  ),
  pipValue: (
    <>
      The cash value of a one-pip move at the calculated lot size, in your account currency.
      Multiply by the pip distance to get the cash at risk.
    </>
  ),
  moneyAtRisk: (
    <>
      How many account-currency units you lose if the stop is hit at the rounded lot size.
      This is always ≤ your risk budget — never above it.
    </>
  ),
  rr: (
    <>
      Risk:reward ratio — how many units of profit you stand to make per unit risked.
      Combined with your historical win rate, R:R determines whether the strategy has
      positive expectancy.
    </>
  ),
};

export function RiskCalculatorPage() {
  const [state, setState] = useState<FormState>(DEFAULT_STATE);
  const [result, setResult] = useState<PositionSizeResponse | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const instrumentsQuery = useQuery({
    queryKey: ['instruments'],
    queryFn: listInstruments,
  });

  // Size from *measured* volatility rather than a guessed stop: pull the live
  // vol forecast, anchor the entry to the latest price, and place the stop a
  // volatility-appropriate distance away (beyond routine noise). Target
  // defaults to 2× that distance.
  const volFill = useMutation({
    mutationFn: () =>
      fetchVolatility({ symbol: state.symbol, timeframe: '1d', horizon_bars: 5, model: 'ml' }),
    onSuccess: (data) => {
      const pip = Number(
        (instrumentsQuery.data ?? []).find((i) => i.symbol === state.symbol)?.pip_size ?? 0.0001
      );
      const entry = Number(data.forecast.asof_close);
      const stopPips = Number(data.guidance.suggested_stop_pips);
      const dir = state.direction === 'long' ? 1 : -1;
      const stop = entry - dir * stopPips * pip;
      const target = entry + dir * stopPips * 2 * pip;
      const dp = pip < 0.001 ? 5 : 3;
      setState((s) => ({
        ...s,
        entry: entry.toFixed(dp),
        stop: stop.toFixed(dp),
        target: target.toFixed(dp),
      }));
      setFormError(null);
    },
    onError: (err) =>
      setFormError(
        err instanceof ApiError ? err.message : 'Could not read live volatility right now.'
      ),
  });

  const mutation = useMutation({
    mutationFn: calculatePositionSize,
    onSuccess: (data) => {
      setResult(data);
      setFormError(null);
    },
    onError: (err) => {
      setResult(null);
      if (err instanceof ApiError) {
        setFormError(err.message);
      } else {
        setFormError('Could not compute — check inputs and that the backend is running.');
      }
    },
  });

  // Debounced recompute on input change.
  useEffect(() => {
    const id = window.setTimeout(() => {
      if (!isFormComplete(state)) return;
      mutation.mutate({
        symbol: state.symbol,
        account: { amount: state.accountAmount, currency: state.accountCurrency },
        risk_percent: state.riskPercent,
        direction: state.direction,
        entry: state.entry,
        stop: state.stop,
        target: state.target || null,
        quote_to_account_rate: state.quoteToAccountRate || '1',
      });
    }, 250);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  const rrTone = useMemo<'positive' | 'warn' | 'danger' | 'default'>(() => {
    const rr = result?.risk_reward_ratio ? Number(result.risk_reward_ratio) : null;
    if (rr === null) return 'default';
    if (rr >= 2) return 'positive';
    if (rr >= 1) return 'warn';
    return 'danger';
  }, [result]);

  return (
    <section id="risk" className="space-y-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Risk Calculator</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          Most traders fail on risk management, not forecasting. Size every trade from how
          much you're willing to lose — not from a hunch about how big it could win.
          Hover any label for an explanation.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="panel-pad space-y-5">
          <h2 className="font-medium text-mentor-fg">Trade setup</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Instrument</label>
              <select
                className="input"
                value={state.symbol}
                onChange={(e) => setState({ ...state, symbol: e.target.value })}
              >
                {(instrumentsQuery.data ?? []).map((i) => (
                  <option key={i.symbol} value={i.symbol}>
                    {i.base}/{i.quote}
                  </option>
                ))}
                {instrumentsQuery.isLoading && <option>Loading…</option>}
              </select>
            </div>
            <div>
              <label className="label">Direction</label>
              <div className="grid grid-cols-2 gap-2">
                {(['long', 'short'] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setState({ ...state, direction: d })}
                    className={
                      'rounded-lg border px-3 py-2 text-sm font-medium capitalize transition-colors ' +
                      (state.direction === d
                        ? 'border-mentor-accent bg-mentor-accent/15 text-mentor-fg'
                        : 'border-mentor-border bg-mentor-panelLight text-mentor-muted hover:text-mentor-fg')
                    }
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field
              label="Account balance"
              type="number"
              inputMode="decimal"
              step="any"
              suffix={state.accountCurrency}
              value={state.accountAmount}
              onChange={(e) => setState({ ...state, accountAmount: e.target.value })}
            />
            <Field
              label="Currency"
              value={state.accountCurrency}
              maxLength={3}
              onChange={(e) =>
                setState({ ...state, accountCurrency: e.target.value.toUpperCase() })
              }
            />
          </div>

          <Field
            label="Risk per trade"
            explainer={EXPLAINERS.risk}
            type="number"
            inputMode="decimal"
            step="0.1"
            suffix="%"
            value={state.riskPercent}
            onChange={(e) => setState({ ...state, riskPercent: e.target.value })}
          />

          <div className="grid grid-cols-3 gap-4">
            <Field
              label="Entry"
              explainer={EXPLAINERS.entry}
              type="number"
              inputMode="decimal"
              step="any"
              value={state.entry}
              onChange={(e) => setState({ ...state, entry: e.target.value })}
            />
            <Field
              label="Stop"
              explainer={EXPLAINERS.stop}
              type="number"
              inputMode="decimal"
              step="any"
              value={state.stop}
              onChange={(e) => setState({ ...state, stop: e.target.value })}
            />
            <Field
              label="Target"
              hint="optional"
              explainer={EXPLAINERS.target}
              type="number"
              inputMode="decimal"
              step="any"
              value={state.target}
              onChange={(e) => setState({ ...state, target: e.target.value })}
            />
          </div>

          <button
            type="button"
            onClick={() => volFill.mutate()}
            disabled={volFill.isPending}
            className="btn-ghost w-full"
          >
            {volFill.isPending
              ? 'Reading volatility…'
              : '📏 Set entry & stop from live volatility'}
          </button>
          <p className="-mt-3 text-xs text-mentor-muted">
            Fills the entry with the latest price and the stop a
            volatility-appropriate distance away — so your size flows from measured
            noise, not a guess. Adjust freely afterward.
          </p>

          {formError && (
            <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
              {formError}
            </div>
          )}
        </div>

        <div className="panel-pad space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-medium text-mentor-fg">Sized trade</h2>
            <div className="flex items-center gap-2">
              {mutation.isPending && (
                <span className="text-xs text-mentor-muted">computing…</span>
              )}
              {result && (
                <WhyButton
                  topic="position-size"
                  label="Why this size?"
                  context={{
                    symbol: result.symbol,
                    direction: result.direction,
                    account: `${state.accountAmount} ${state.accountCurrency}`,
                    risk_pct: state.riskPercent,
                    entry: state.entry,
                    stop: state.stop,
                    target: state.target || null,
                    lots: result.lots,
                    units: result.units,
                    pip_distance: result.pip_distance,
                    money_at_risk: `${result.money_at_risk.amount} ${result.money_at_risk.currency}`,
                    risk_reward_ratio: result.risk_reward_ratio,
                    is_aggressive: result.is_aggressive,
                  }}
                />
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="Position size"
              explainer={EXPLAINERS.lots}
              value={result ? formatLots(result.lots) : '—'}
              sub={result ? `${formatNumber(result.units, 0)} units` : null}
              tone={result && result.lots === '0' ? 'warn' : 'default'}
            />
            <Metric
              label="Stop distance"
              explainer={EXPLAINERS.pipDistance}
              value={result ? `${formatNumber(result.pip_distance, 1)} pips` : '—'}
            />
            <Metric
              label="Money at risk"
              explainer={EXPLAINERS.moneyAtRisk}
              value={
                result
                  ? formatMoney(result.money_at_risk.amount, result.money_at_risk.currency)
                  : '—'
              }
              sub={
                result
                  ? `${formatPercent(result.risk_pct_of_account)} of equity`
                  : null
              }
              tone={result?.is_aggressive ? 'warn' : 'default'}
            />
            <Metric
              label="Risk : Reward"
              explainer={EXPLAINERS.rr}
              value={result?.risk_reward_ratio ? `1 : ${formatNumber(result.risk_reward_ratio)}` : '—'}
              tone={rrTone}
            />
            <Metric
              label="Pip value"
              explainer={EXPLAINERS.pipValue}
              value={
                result
                  ? formatMoney(
                      result.pip_value_in_account.amount,
                      result.pip_value_in_account.currency
                    )
                  : '—'
              }
              sub="per pip, at sized lot"
            />
            <Metric
              label="Notional"
              value={
                result
                  ? formatMoney(result.notional_in_quote, 'USD')
                  : '—'
              }
              sub="exposure in quote currency"
            />
          </div>

          {result && result.notes.length > 0 && (
            <div className="space-y-2 rounded-xl border border-mentor-warn/30 bg-mentor-warn/5 p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-mentor-warn">
                <span aria-hidden>!</span> Mentor notes
              </div>
              <ul className="space-y-1.5 text-sm text-mentor-fg/90">
                {result.notes.map((n) => (
                  <li key={n} className="leading-relaxed">
                    {n}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <RiskOfRuinPanel currency={state.accountCurrency} />
    </section>
  );
}

function isFormComplete(state: FormState): boolean {
  const required = [
    state.symbol,
    state.accountAmount,
    state.accountCurrency,
    state.riskPercent,
    state.entry,
    state.stop,
  ];
  return required.every((v) => v && v.trim().length > 0);
}
