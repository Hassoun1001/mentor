import type { ReactNode } from 'react';
import { clsx } from 'clsx';

import { Tooltip } from './Tooltip';

interface MetricProps {
  label: ReactNode;
  value: ReactNode;
  sub?: ReactNode;
  explainer?: ReactNode;
  tone?: 'default' | 'positive' | 'warn' | 'danger';
}

const TONE_TEXT: Record<NonNullable<MetricProps['tone']>, string> = {
  default: 'text-mentor-fg',
  positive: 'text-mentor-accentSoft',
  warn: 'text-mentor-warn',
  danger: 'text-mentor-danger',
};

const TONE_DOT: Record<NonNullable<MetricProps['tone']>, string> = {
  default: 'bg-mentor-muted/40',
  positive: 'bg-mentor-accentSoft',
  warn: 'bg-mentor-warn',
  danger: 'bg-mentor-danger',
};

/**
 * A clean, self-explanatory stat tile: a small label (optionally with a
 * hover explainer), a big tabular value, and an optional plain-English
 * sub-line. A tone dot gives an at-a-glance read without shouting.
 */
export function Metric({ label, value, sub, explainer, tone = 'default' }: MetricProps) {
  return (
    <div className="rounded-2xl border border-mentor-border bg-mentor-panelLight/50 p-4 transition-colors hover:border-mentor-accent/30">
      <div className="flex items-center gap-2">
        <span className={clsx('h-1.5 w-1.5 shrink-0 rounded-full', TONE_DOT[tone])} aria-hidden />
        <div className="metric-label">
          {explainer ? <Tooltip label={explainer}>{label}</Tooltip> : label}
        </div>
      </div>
      <div className={clsx('metric-value mt-2', TONE_TEXT[tone])}>{value}</div>
      {sub && <div className="mt-1 text-xs text-mentor-muted">{sub}</div>}
    </div>
  );
}
