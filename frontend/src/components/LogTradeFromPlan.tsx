import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import { evaluateChecklist, logTradeFromPlan } from '../api/journal';
import type { TradePlan } from '../api/tradePlan';
import { Field } from './Field';

interface Props {
  plan: TradePlan;
  balance: number;
  riskPercent: number;
  reason: string;
  onReason: (v: string) => void;
}

/**
 * Saves a Journal trade with this exact plan frozen beside it. The levels
 * start as the ticket's and stay editable, because what the broker took and
 * what the system said are the two things being compared. Mount with a key
 * built from the plan so the form can never describe a different plan from
 * the one being saved.
 */
export function LogTradeFromPlan({ plan, balance, riskPercent, reason, onReason }: Props) {
  const queryClient = useQueryClient();
  const standAside = plan.stance === 'stand_aside';
  const currency = plan.size?.risk_currency ?? 'USD';

  const [direction, setDirection] = useState<'long' | 'short'>(
    plan.stance === 'short' ? 'short' : 'long'
  );
  const [entry, setEntry] = useState(plan.levels?.entry ?? '');
  const [stop, setStop] = useState(plan.levels?.stop ?? '');
  const [target, setTarget] = useState(plan.levels?.target ?? '');
  const [lots, setLots] = useState(plan.size?.lots ?? '');
  const [risk, setRisk] = useState(
    plan.size?.money_at_risk ?? ((balance * riskPercent) / 100).toFixed(2)
  );
  const [error, setError] = useState<string | null>(null);

  const complete = Boolean(entry && stop && lots && risk && reason.trim());
  const checklist = useQuery({
    queryKey: ['checklist', 'from-plan', direction, entry, stop, target, lots, risk, reason, balance, riskPercent],
    queryFn: () =>
      evaluateChecklist({
        symbol: plan.symbol,
        direction,
        size_lots: lots,
        entry,
        stop,
        target: target || null,
        initial_risk_amount: risk,
        risk_currency: currency,
        reason,
        account_balance: String(balance),
        max_risk_per_trade_percent: String(riskPercent),
      }),
    enabled: complete,
    retry: false,
  });

  const log = useMutation({
    mutationFn: () =>
      logTradeFromPlan({
        plan: {
          symbol: plan.symbol,
          timeframe: plan.timeframe,
          asof: plan.asof,
          model_name: plan.model_name,
          p_up: plan.p_up,
          confidence: plan.confidence,
          stance: plan.stance,
          horizon_bars: plan.horizon_bars,
          entry: plan.levels?.entry ?? null,
          stop: plan.levels?.stop ?? null,
          target: plan.levels?.target ?? null,
          reward_multiple: plan.levels?.risk_reward ?? null,
        },
        trade: {
          symbol: plan.symbol,
          direction,
          size_lots: lots,
          entry,
          stop,
          target: target || null,
          initial_risk: { amount: risk, currency },
          reason,
        },
      }),
    onSuccess: () => {
      setError(null);
      onReason('');
      queryClient.invalidateQueries({ queryKey: ['trades'] });
      queryClient.invalidateQueries({ queryKey: ['system-comparison'] });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Could not log this trade.');
    },
  });

  if (log.isSuccess) {
    return (
      <div className="panel-pad text-sm text-mentor-fg">
        <span className="font-medium text-mentor-accent">Saved to your Journal</span> with this
        plan attached. Open the Journal and enter your fill price once the broker has filled it.
      </div>
    );
  }

  const passed = checklist.data?.passed ?? false;
  const unmet = checklist.data?.items.filter((i) => !i.passed && !i.skipped) ?? [];
  const against = !standAside && direction !== plan.stance;

  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          {standAside ? 'Took a trade anyway? Log it' : 'Log this trade'}
        </h2>
        <p className="mt-1 text-xs text-mentor-muted">
          Saves the trade to your Journal with this exact plan attached, so later you can see what
          the system would have done next to what you got.
        </p>
      </div>

      {standAside && (
        <p className="rounded-lg border border-mentor-warn/40 bg-mentor-warn/5 p-3 text-sm text-mentor-fg">
          The system says to stand aside, so it has no levels to offer. A trade logged here will be
          marked NO MATCH.
        </p>
      )}
      {against && (
        <p className="rounded-lg border border-mentor-warn/40 bg-mentor-warn/5 p-3 text-sm text-mentor-fg">
          This goes against the system&apos;s direction and will be marked NO MATCH.
        </p>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-6">
        <div>
          <label className="label">Direction</label>
          <div className="grid grid-cols-2 gap-1">
            {(['long', 'short'] as const).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDirection(d)}
                className={
                  'rounded-lg border px-2 py-2 text-sm font-medium capitalize transition-colors ' +
                  (direction === d
                    ? 'border-mentor-accent bg-mentor-accent/15 text-mentor-fg'
                    : 'border-mentor-border bg-mentor-panelLight text-mentor-muted hover:text-mentor-fg')
                }
              >
                {d}
              </button>
            ))}
          </div>
        </div>
        <Field label="Entry" type="number" step="any" value={entry} onChange={(e) => setEntry(e.target.value)} />
        <Field label="Stop" type="number" step="any" value={stop} onChange={(e) => setStop(e.target.value)} />
        <Field label="Target" type="number" step="any" value={target} onChange={(e) => setTarget(e.target.value)} />
        <Field label="Size (lots)" type="number" step="0.01" value={lots} onChange={(e) => setLots(e.target.value)} />
        <Field
          label="Risk amount"
          type="number"
          step="any"
          suffix={currency}
          value={risk}
          onChange={(e) => setRisk(e.target.value)}
        />
      </div>

      <div>
        <label className="label">Reason — why this trade?</label>
        <textarea
          className="input min-h-[4rem] resize-y"
          placeholder="At least 20 characters. In your own words: why are you taking it, and what would change your mind?"
          value={reason}
          onChange={(e) => onReason(e.target.value)}
        />
      </div>

      {unmet.length > 0 && (
        <ul className="space-y-1 text-sm text-mentor-fg/90">
          {unmet.map((i) => (
            <li key={i.key}>
              <span className="font-medium text-mentor-warn">×</span> {i.label}
              {i.detail && <span className="text-mentor-muted"> — {i.detail}</span>}
            </li>
          ))}
        </ul>
      )}

      {error && <p className="text-sm text-mentor-danger">{error}</p>}

      <button
        type="button"
        disabled={!passed || log.isPending}
        onClick={() => log.mutate()}
        className={
          'rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ' +
          (passed
            ? 'bg-mentor-accent text-white hover:bg-mentor-accentHover'
            : 'cursor-not-allowed bg-mentor-panelLight text-mentor-muted')
        }
      >
        {log.isPending ? 'Saving…' : passed ? 'Log this trade' : 'Complete the checklist to continue'}
      </button>
    </div>
  );
}
