import { useQuery } from '@tanstack/react-query';

import { type CalibrationBucket, calibrationSummary } from '../api/forecast';

/**
 * Calibration chart — Principle 05 in screen form.
 *
 * Each row is one probability bucket; the bar on the left shows the
 * stated probability (the midpoint of the bucket), the bar on the right
 * shows the realised hit rate. A perfectly calibrated forecaster lines
 * the two up. Cells with very few samples are dimmed because variance
 * dominates the signal there.
 */
export function CalibrationChart() {
  const query = useQuery({
    queryKey: ['calibration'],
    queryFn: calibrationSummary,
  });

  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="font-medium text-mentor-fg">Calibration</h2>
        <p className="text-xs text-mentor-muted">
          Stated probability (left bar) vs. realised hit rate (right bar) per
          bucket. Buckets with fewer than 10 resolved predictions are dimmed —
          variance dominates the signal there.
        </p>
      </div>

      {query.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!query.isLoading && (query.data ?? []).length === 0 && (
        <p className="text-sm text-mentor-muted">
          Need some resolved predictions first. Run the resolver on the audit
          panel and check back after the horizon elapses on a few forecasts.
        </p>
      )}

      <div className="space-y-2">
        {(query.data ?? []).map((bucket) => (
          <Row key={bucket.bucket} bucket={bucket} />
        ))}
      </div>
    </div>
  );
}

function Row({ bucket }: { bucket: CalibrationBucket }) {
  const stated = midpointOf(bucket.bucket);
  const realised = bucket.hit_rate;
  const dim = bucket.samples < 10;
  const wellCalibrated = Math.abs(stated - realised) < 0.05;
  return (
    <div className={dim ? 'opacity-40' : ''}>
      <div className="mb-1 flex items-center justify-between text-xs font-mono text-mentor-muted">
        <span>{bucket.bucket}</span>
        <span>
          {Math.round(stated * 100)}% → {Math.round(realised * 100)}%
          {' · '}
          {bucket.samples} samples
        </span>
      </div>
      <div className="grid grid-cols-[1fr,1fr] gap-1">
        <Bar value={stated} tone="muted" />
        <Bar value={realised} tone={wellCalibrated ? 'positive' : 'warn'} />
      </div>
    </div>
  );
}

function Bar({ value, tone }: { value: number; tone: 'muted' | 'positive' | 'warn' }) {
  const colorClass =
    tone === 'positive'
      ? 'bg-mentor-accent'
      : tone === 'warn'
        ? 'bg-mentor-warn'
        : 'bg-mentor-border';
  return (
    <div className="h-1.5 rounded-full bg-mentor-panelLight">
      <div
        className={`h-full rounded-full ${colorClass}`}
        style={{ width: `${Math.max(2, Math.round(value * 100))}%` }}
      />
    </div>
  );
}

function midpointOf(label: string): number {
  // labels are "30-40%"
  const match = label.match(/(\d+)-(\d+)/);
  if (!match) return 0;
  const lo = Number(match[1]);
  const hi = Number(match[2]);
  return (lo + hi) / 200;
}
