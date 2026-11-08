import type { ReactNode } from 'react';

import type { ComparisonSummary, ExitKind, TradeComparison, Verdict } from '../api/journal';
import { formatNumber } from '../lib/format';
import { Metric } from './Metric';

const VERDICT_STYLE: Record<Verdict, { label: string; cls: string }> = {
  match: { label: 'MATCH', cls: 'border-mentor-accent/50 bg-mentor-accent/10 text-mentor-accent' },
  partial: { label: 'PARTIAL', cls: 'border-mentor-warn/50 bg-mentor-warn/10 text-mentor-warn' },
  no_match: {
    label: 'NO MATCH',
    cls: 'border-mentor-danger/50 bg-mentor-danger/10 text-mentor-danger',
  },
  pending: {
    label: 'WAITING',
    cls: 'border-mentor-border bg-mentor-panelLight text-mentor-muted',
  },
};

const EXIT_LABEL: Record<ExitKind, string> = {
  stop: 'Stop',
  target: 'Target',
  time: 'Time limit',
  manual: 'Closed by hand',
};

const STANCE_LABEL: Record<string, string> = {
  long: 'Long',
  short: 'Short',
  stand_aside: 'Stand aside',
};

function utc(ts: string | null): string {
  if (!ts) return '—';
  const text = new Date(ts).toLocaleString('en-GB', {
    timeZone: 'UTC',
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
  return `${text.replace(',', '')} UTC`;
}

function price(value: string | null): string {
  return value === null ? '—' : Number(value).toFixed(5);
}

function signed(value: string | number | null, digits: number, unit = ''): string {
  if (value === null) return '—';
  const n = Number(value);
  return `${n > 0 ? '+' : ''}${formatNumber(n, digits)}${unit}`;
}

function toneOf(value: string | number | null): 'default' | 'positive' | 'danger' {
  const n = value === null ? 0 : Number(value);
  if (n > 0) return 'positive';
  if (n < 0) return 'danger';
  return 'default';
}

function slippageText(pips: string | null): string {
  if (pips === null) return '—';
  const n = Number(pips);
  if (n === 0) return 'Same';
  return `${Math.abs(n).toFixed(1)} pips ${n > 0 ? 'worse' : 'better'}`;
}

function systemEnding(c: TradeComparison): string {
  if (c.system.status === 'no_trade') return 'No trade';
  if (c.system.status === 'pending') return 'Still running';
  return c.system.exit_reason ? EXIT_LABEL[c.system.exit_reason] : '—';
}

/** Your trade beside the system's version of it, on one journal row. */
export function TradeVersusSystem({ c }: { c: TradeComparison }) {
  const style = c.verdict ? VERDICT_STYLE[c.verdict] : null;
  const pipsGap =
    c.system.pips !== null && c.actual.pips !== null
      ? Number(c.actual.pips) - Number(c.system.pips)
      : null;
  const sameDirection = c.plan.stance === c.actual.direction;
  const directionGap =
    c.plan.stance === 'stand_aside' ? 'Traded anyway' : sameDirection ? 'Same' : 'Opposite';

  return (
    <div className="space-y-3 rounded-lg border border-mentor-border bg-mentor-panelLight/40 p-3">
      <div className="flex items-start gap-3">
        {style && (
          <span
            className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${style.cls}`}
          >
            {style.label}
          </span>
        )}
        <p className="text-sm leading-snug text-mentor-fg">{c.explanation}</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-mentor-muted">
              <th className="py-1 pr-3 font-normal" />
              <th className="py-1 pr-3 font-medium">System</th>
              <th className="py-1 pr-3 font-medium">You</th>
              <th className="py-1 font-medium">Difference</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-mentor-border/60 font-mono text-mentor-fg">
            <Row
              label="Direction"
              system={STANCE_LABEL[c.plan.stance]}
              you={STANCE_LABEL[c.actual.direction]}
              gap={directionGap}
            />
            <Row
              label="Entry"
              system={price(c.system.entry_price)}
              you={price(c.actual.entry_price)}
              gap={slippageText(c.entry_slippage_pips)}
            />
            <Row
              label="Exit"
              system={price(c.system.exit_price)}
              you={price(c.actual.exit_price)}
            />
            <Row
              label="How it ended"
              system={systemEnding(c)}
              you={c.actual.exit_reason ? EXIT_LABEL[c.actual.exit_reason] : '—'}
            />
            <Row label="Ended at" system={utc(c.system.exit_ts)} you={utc(c.actual.exit_ts)} />
            <Row
              label="Pips"
              system={signed(c.system.pips, 1)}
              you={signed(c.actual.pips, 1)}
              gap={signed(pipsGap, 1)}
            />
            <Row
              label="Result (R)"
              system={c.system.status === 'no_trade' ? '0.00R' : signed(c.system.r, 2, 'R')}
              you={signed(c.actual.r, 2, 'R')}
              gap={signed(c.r_difference, 2, 'R')}
            />
          </tbody>
        </table>
      </div>

      <p className="text-[11px] leading-relaxed text-mentor-muted">
        Plan from {utc(c.plan.asof)} · {(Number(c.plan.p_up) * 100).toFixed(0)}% chance of up ·{' '}
        {(Number(c.plan.confidence) * 100).toFixed(0)}% confidence
        {c.plan.stop !== null && (
          <>
            {' '}
            · stop {price(c.plan.stop)} · target {price(c.plan.target)} · time limit{' '}
            {utc(c.plan.time_stop_deadline)}
          </>
        )}{' '}
        · model {c.plan.model_name}
      </p>
    </div>
  );
}

function Row({
  label,
  system,
  you,
  gap,
}: {
  label: string;
  system: ReactNode;
  you: ReactNode;
  gap?: ReactNode;
}) {
  return (
    <tr>
      <td className="py-1 pr-3 font-sans text-mentor-muted">{label}</td>
      <td className="py-1 pr-3">{system}</td>
      <td className="py-1 pr-3">{you}</td>
      <td className="py-1">{gap ?? ''}</td>
    </tr>
  );
}

/** The verdict counts and what the differences added up to. */
export function SystemComparisonSummary({ summary }: { summary: ComparisonSummary }) {
  const counts: [Verdict, number][] = [
    ['match', summary.matches],
    ['partial', summary.partials],
    ['no_match', summary.no_matches],
    ['pending', summary.pending],
  ];
  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          You versus the system
        </h2>
        <p className="mt-1 text-sm text-mentor-fg">{summary.headline}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {counts.map(([verdict, n]) => (
          <div
            key={verdict}
            className="rounded-lg border border-mentor-border bg-mentor-panelLight px-3 py-2 text-xs"
          >
            <div className="text-mentor-muted">{VERDICT_STYLE[verdict].label}</div>
            <div className="mt-0.5 font-mono text-lg text-mentor-fg">{n}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Metric
          label="Your total"
          value={signed(summary.actual_r, 2, 'R')}
          tone={toneOf(summary.actual_r)}
          sub={`across ${summary.compared} compared`}
        />
        <Metric
          label="System's total"
          value={signed(summary.system_r, 2, 'R')}
          tone={toneOf(summary.system_r)}
          sub="same trades, playing its plan to the end"
        />
        <Metric
          label="Gained or lost by how you traded"
          value={signed(summary.execution_r, 2, 'R')}
          tone={toneOf(summary.execution_r)}
          sub="your total minus the system's"
        />
      </div>

      <p className="text-xs text-mentor-muted">
        The system&apos;s figures include the usual spread and slippage on the way in and out.
        {summary.unlinked > 0 &&
          ` ${summary.unlinked} closed trade${summary.unlinked === 1 ? ' has' : 's have'} no system plan linked and ${summary.unlinked === 1 ? 'is' : 'are'} not counted here.`}
      </p>
    </div>
  );
}
