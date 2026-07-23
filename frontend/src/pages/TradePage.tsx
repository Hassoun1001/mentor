import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { type TradeManagement, type TradePlan, fetchTradePlan } from '../api/tradePlan';
import { Metric } from '../components/Metric';

export function TradePage() {
  const [balance, setBalance] = useState(10000);
  const [riskPercent, setRiskPercent] = useState(1);
  const [rewardMultiple, setRewardMultiple] = useState(2);

  const plan = useQuery({
    queryKey: ['trade-plan', balance, riskPercent, rewardMultiple],
    queryFn: () => fetchTradePlan({ balance, riskPercent, rewardMultiple }),
    refetchInterval: 60_000,
  });

  return (
    <section className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Trade plan</h1>
          <p className="max-w-2xl text-sm text-mentor-muted">
            The system&apos;s current read turned into a concrete, sized plan — or an
            honest &quot;don&apos;t trade&quot;. Refreshes every minute.
          </p>
        </div>
        <PlanInputs
          balance={balance}
          riskPercent={riskPercent}
          rewardMultiple={rewardMultiple}
          onBalance={setBalance}
          onRisk={setRiskPercent}
          onReward={setRewardMultiple}
        />
      </header>

      {plan.isLoading && (
        <div className="panel-pad text-sm text-mentor-muted">Building your plan…</div>
      )}
      {plan.isError && (
        <div className="panel-pad text-sm text-mentor-danger">
          Could not build a plan: {plan.error instanceof Error ? plan.error.message : 'error'}.
          Usually this means price history hasn&apos;t been backfilled yet.
        </div>
      )}
      {plan.data && <PlanView plan={plan.data} />}
    </section>
  );
}

// ---------- inputs ----------

function PlanInputs({
  balance,
  riskPercent,
  rewardMultiple,
  onBalance,
  onRisk,
  onReward,
}: {
  balance: number;
  riskPercent: number;
  rewardMultiple: number;
  onBalance: (v: number) => void;
  onRisk: (v: number) => void;
  onReward: (v: number) => void;
}) {
  const inputCls =
    'w-28 rounded-md border border-mentor-border bg-mentor-panel px-2 py-1.5 font-mono text-sm text-mentor-fg';
  return (
    <div className="flex flex-wrap items-end gap-3 text-xs text-mentor-muted">
      <label className="flex flex-col gap-1">
        Account (USD)
        <input
          type="number"
          min={100}
          step={100}
          value={balance}
          onChange={(e) => onBalance(Math.max(100, Number(e.target.value) || 100))}
          className={inputCls}
        />
      </label>
      <label className="flex flex-col gap-1">
        Risk per trade
        <select
          value={riskPercent}
          onChange={(e) => onRisk(Number(e.target.value))}
          className={inputCls}
        >
          <option value={0.5}>0.5%</option>
          <option value={1}>1%</option>
          <option value={2}>2%</option>
        </select>
      </label>
      <label className="flex flex-col gap-1">
        Reward : risk
        <select
          value={rewardMultiple}
          onChange={(e) => onReward(Number(e.target.value))}
          className={inputCls}
        >
          <option value={1.5}>1.5 : 1</option>
          <option value={2}>2 : 1</option>
          <option value={3}>3 : 1</option>
        </select>
      </label>
    </div>
  );
}

// ---------- the plan ----------

const STANCE_STYLE: Record<TradePlan['stance'], { label: string; cls: string; arrow: string }> = {
  long: {
    label: 'GO LONG',
    cls: 'border-mentor-accent/40 bg-mentor-accent/5 text-mentor-accent',
    arrow: '▲',
  },
  short: {
    label: 'GO SHORT',
    cls: 'border-mentor-danger/40 bg-mentor-danger/5 text-mentor-danger',
    arrow: '▼',
  },
  stand_aside: {
    label: 'STAND ASIDE',
    cls: 'border-mentor-border bg-mentor-panelLight text-mentor-muted',
    arrow: '⏸',
  },
};

function PlanView({ plan }: { plan: TradePlan }) {
  const s = STANCE_STYLE[plan.stance];
  const pUp = Number(plan.p_up) * 100;
  const conf = Number(plan.confidence) * 100;

  return (
    <div className="space-y-6">
      {/* stance hero */}
      <div className={`rounded-2xl border-2 p-6 ${s.cls}`}>
        <div className="flex flex-wrap items-center gap-4">
          <span className="text-4xl">{s.arrow}</span>
          <div>
            <div className="text-2xl font-semibold tracking-wide">
              {s.label}
              <span className="ml-3 font-mono text-lg text-mentor-fg">{plan.symbol}</span>
            </div>
            <p className="mt-1 max-w-3xl text-sm text-mentor-fg">{plan.headline}</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-xs">
          <Chip>P(up) {pUp.toFixed(0)}%</Chip>
          <Chip>confidence {conf.toFixed(0)}%</Chip>
          <Chip>
            horizon {plan.horizon_bars} × {plan.timeframe}
          </Chip>
          <Chip>volatility: {plan.vol_regime}</Chip>
          <Chip>±{Number(plan.expected_move_pips).toFixed(0)} pips expected move</Chip>
          <Chip>vol {Math.round(Number(plan.vol_percentile) * 100)}th pctile</Chip>
        </div>
      </div>

      <ExpectedRange plan={plan} />

      {plan.warnings.length > 0 && (
        <div className="space-y-2">
          {plan.warnings.map((w) => (
            <div
              key={w}
              className="rounded-lg border border-mentor-warn/40 bg-mentor-warn/5 p-3 text-sm text-mentor-fg"
            >
              ⚠️ {w}
            </div>
          ))}
        </div>
      )}

      {plan.levels && plan.size && (
        <div className="panel-pad space-y-4">
          <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
            Your trade ticket — copy these into your broker
          </h2>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Metric
              label="Entry (market)"
              value={<Mono>{plan.levels.entry}</Mono>}
              sub="current price"
            />
            <Metric
              label="Stop loss"
              value={<Mono>{plan.levels.stop}</Mono>}
              sub={`${Number(plan.levels.stop_pips).toFixed(0)} pips away`}
              tone="danger"
            />
            <Metric
              label="Take profit"
              value={<Mono>{plan.levels.target}</Mono>}
              sub={`${Number(plan.levels.target_pips).toFixed(0)} pips away (${plan.levels.risk_reward}:1)`}
              tone="positive"
            />
            <Metric
              label="Position size"
              value={<Mono>{Number(plan.size.lots).toFixed(2)} lots</Mono>}
              sub={`${Number(plan.size.units).toLocaleString()} units`}
            />
          </div>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
            <Metric
              label="Money at risk"
              value={`${Number(plan.size.money_at_risk).toFixed(2)} ${plan.size.risk_currency}`}
              sub="if the stop is hit"
            />
            <Metric
              label="Pip value"
              value={`${Number(plan.size.pip_value).toFixed(2)} ${plan.size.risk_currency}/pip`}
            />
            <Metric label="Model" value={<Mono>{plan.model_name}</Mono>} />
          </div>
          {plan.size.notes.length > 0 && (
            <ul className="space-y-1 text-xs text-mentor-muted">
              {plan.size.notes.map((n) => (
                <li key={n}>• {n}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {plan.management && <ManagementPanel m={plan.management} />}

      <div className="grid gap-6 md:grid-cols-2">
        <div className="panel-pad space-y-2">
          <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
            Why the model leans this way
          </h2>
          <p className="text-sm leading-relaxed text-mentor-fg">{plan.reasoning}</p>
        </div>
        <Checklist items={plan.checklist} />
      </div>

      <p className="text-xs text-mentor-muted">{plan.disclaimer}</p>
    </div>
  );
}

function ManagementPanel({ m }: { m: TradeManagement }) {
  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          After you&apos;re in — decide these now, not while money is moving
        </h2>
        <p className="mt-1 text-xs text-mentor-muted">
          Derived from the same volatility forecast that set your stop, so the rules adapt to
          today&apos;s regime instead of using round-number guesses.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Metric
          label="Move stop to break-even at"
          value={<Mono>{m.break_even_price}</Mono>}
          sub={`+${Number(m.break_even_pips).toFixed(0)} pips (1R)`}
        />
        <Metric
          label="Then trail by"
          value={<Mono>{Number(m.trail_distance_pips).toFixed(0)} pips</Mono>}
          sub="one sigma of expected move"
        />
        <Metric
          label={`Bank ${Math.round(Number(m.partial_close_fraction) * 100)}% at`}
          value={<Mono>{m.partial_close_price}</Mono>}
          sub="let the rest run to target"
          tone="positive"
        />
        <Metric
          label="Time stop"
          value={<Mono>{m.time_stop_bars} bars</Mono>}
          sub="close it — forecast expired"
          tone="danger"
        />
      </div>
      <ol className="space-y-2 text-sm leading-relaxed text-mentor-fg">
        {m.rules.map((r, i) => (
          <li key={r} className="flex gap-3">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-mentor-accent/15 text-[11px] font-semibold text-mentor-accent">
              {i + 1}
            </span>
            <span>{r}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-mentor-border bg-mentor-panel px-2.5 py-1 font-mono text-mentor-fg">
      {children}
    </span>
  );
}

// The honest range: a calibrated band on how far price is likely to travel,
// drawn symmetrically around the entry. Only shown when the ML vol model
// supplied a conformal band (the EWMA baseline doesn't).
function ExpectedRange({ plan }: { plan: TradePlan }) {
  const high =
    plan.range_high_pips != null ? Number(plan.range_high_pips) : Number(plan.expected_move_pips);
  const cov = plan.range_coverage != null ? Number(plan.range_coverage) : null;
  const conformal = plan.range_high_pips != null && cov != null;
  const pct = Math.max(4, Math.min(96, (Number(plan.expected_move_pips) / (high * 1.15)) * 100));

  return (
    <div className="panel-pad space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          How far price is likely to move
        </h2>
        <span className="text-xs text-mentor-muted">
          {conformal
            ? `${Math.round(cov! * 100)}% of moves land within this band`
            : '1σ band — about two-in-three of moves land inside'}
        </span>
      </div>
      <div className="relative h-16">
        {/* full conformal band */}
        <div className="absolute inset-x-0 top-1/2 h-9 -translate-y-1/2 rounded-xl border border-mentor-border bg-mentor-panelLight/60" />
        {/* 1σ expected-move core, centred */}
        <div
          className="absolute top-1/2 h-9 -translate-y-1/2 rounded-xl bg-mentor-accent/15 ring-1 ring-mentor-accent/40"
          style={{ left: `${50 - pct / 2}%`, width: `${pct}%` }}
        />
        {/* centre line = entry */}
        <div className="absolute left-1/2 top-1/2 h-12 w-px -translate-x-1/2 -translate-y-1/2 bg-mentor-fg/50" />
        <span className="absolute left-1/2 top-0 -translate-x-1/2 text-[10px] text-mentor-muted">
          entry
        </span>
        <span className="absolute left-0 bottom-0 font-mono text-[11px] text-mentor-muted">
          −{Math.round(high)} pips
        </span>
        <span className="absolute right-0 bottom-0 font-mono text-[11px] text-mentor-muted">
          +{Math.round(high)} pips
        </span>
        <span className="absolute left-1/2 bottom-0 -translate-x-1/2 font-mono text-[11px] text-mentor-accent">
          ±{Math.round(Number(plan.expected_move_pips))} typical
        </span>
      </div>
      <p className="text-xs text-mentor-muted">
        This is the one thing the system forecasts with a real edge — <em>how far</em>, not{' '}
        <em>which way</em>. Your stop sits just beyond the typical move so ordinary noise
        can&apos;t clip it.
      </p>
    </div>
  );
}

function Mono({ children }: { children: React.ReactNode }) {
  return <span className="font-mono">{children}</span>;
}

function Checklist({ items }: { items: string[] }) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const done = items.every((_, i) => checked[i]);
  return (
    <div className="panel-pad space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          Before you click buy/sell
        </h2>
        {done && <span className="text-xs text-mentor-accent">✓ all checked — disciplined</span>}
      </div>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={item}>
            <label className="flex cursor-pointer items-start gap-2 text-sm text-mentor-fg">
              <input
                type="checkbox"
                checked={!!checked[i]}
                onChange={(e) => setChecked((c) => ({ ...c, [i]: e.target.checked }))}
                className="mt-0.5 accent-current"
              />
              <span>{item}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
