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
    <div
      className={clsx(
        'group relative overflow-hidden rounded-xl border p-4 transition-colors',
        'border-mentor-border bg-mentor-panelLight/50 hover:border-mentor-border/80',
        tone === 'positive' && 'border-mentor-accentSoft/25',
        tone === 'warn' && 'border-mentor-warn/25',
        tone === 'danger' && 'border-mentor-danger/25'
      )}
    >
      {/* subtle toned accent bar down the left edge */}
      <span
        aria-hidden
        className={clsx(
          'absolute inset-y-0 left-0 w-0.5',
          tone === 'positive' && 'bg-mentor-accentSoft/70',
          tone === 'warn' && 'bg-mentor-warn/70',
          tone === 'danger' && 'bg-mentor-danger/70',
          tone === 'default' && 'bg-transparent'
        )}
      />
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
