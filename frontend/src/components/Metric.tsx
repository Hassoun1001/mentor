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

export function Metric({ label, value, sub, explainer, tone = 'default' }: MetricProps) {
  return (
    <div className="rounded-xl border border-mentor-border bg-mentor-panelLight/60 p-4">
      <div className="metric-label">
        {explainer ? <Tooltip label={explainer}>{label}</Tooltip> : label}
      </div>
      <div
        className={clsx(
          'metric-value mt-1',
          tone === 'positive' && 'text-mentor-accentSoft',
          tone === 'warn' && 'text-mentor-warn',
          tone === 'danger' && 'text-mentor-danger'
        )}
      >
        {value}
      </div>
      {sub && <div className="mt-1 text-xs text-mentor-muted">{sub}</div>}
    </div>
  );
}
