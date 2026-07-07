import { useQuery } from '@tanstack/react-query';

import { getPostMortem } from '../api/forecast';

/**
 * Reliability diagram — predicted probability (x) vs realised hit rate (y),
 * per bucket, against the 45-degree "perfect calibration" line. Points on
 * the diagonal mean "when the model says 60%, it happens 60% of the time."
 * The ECE (expected calibration error) is the sample-weighted average
 * distance from that diagonal — lower is better.
 */
const SIZE = 220;
const PAD = 28;

export function ReliabilityDiagram() {
  const query = useQuery({ queryKey: ['postmortem'], queryFn: getPostMortem });
  const pm = query.data;
  const buckets = pm?.calibration ?? [];

  const x = (v: number) => PAD + v * (SIZE - 2 * PAD);
  const y = (v: number) => SIZE - PAD - v * (SIZE - 2 * PAD);
  const maxSamples = Math.max(1, ...buckets.map((b) => b.samples));

  return (
    <div className="panel-pad space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="font-medium text-mentor-fg">Reliability diagram</h2>
        {pm && pm.sample_size > 0 && (
          <span className="text-xs font-mono text-mentor-muted">
            ECE {(pm.ece * 100).toFixed(1)}% · {pm.sample_size} resolved
          </span>
        )}
      </div>
      <p className="text-xs text-mentor-muted">
        Predicted probability vs. realised frequency. On the dashed diagonal = perfectly
        calibrated. ECE is the average gap; calibration shrinks it without claiming an edge.
      </p>

      {query.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!query.isLoading && buckets.length === 0 && (
        <p className="text-sm text-mentor-muted">
          Need resolved predictions first — run a replay or the resolver, then check back.
        </p>
      )}

      {buckets.length > 0 && (
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="w-full max-w-[280px]" role="img"
          aria-label="reliability diagram">
          {/* frame */}
          <rect x={PAD} y={PAD} width={SIZE - 2 * PAD} height={SIZE - 2 * PAD}
            fill="none" stroke="currentColor" className="text-mentor-border" />
          {/* diagonal */}
          <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="currentColor"
            strokeDasharray="4 3" className="text-mentor-muted" />
          {/* connecting path of actual points */}
          <polyline
            points={buckets.map((b) => `${x(b.stated_midpoint)},${y(b.realised_hit_rate)}`).join(' ')}
            fill="none" stroke="currentColor" className="text-mentor-accent" strokeWidth={1.5} />
          {/* points, sized by sample count */}
          {buckets.map((b) => (
            <circle key={b.bucket} cx={x(b.stated_midpoint)} cy={y(b.realised_hit_rate)}
              r={3 + 4 * (b.samples / maxSamples)}
              className="fill-mentor-accent" opacity={b.samples < 5 ? 0.4 : 0.9}>
              <title>{`${b.bucket}: predicted ${Math.round(b.stated_midpoint * 100)}%, realised ${Math.round(b.realised_hit_rate * 100)}% (${b.samples})`}</title>
            </circle>
          ))}
          {/* axis labels */}
          <text x={SIZE / 2} y={SIZE - 6} textAnchor="middle" className="fill-mentor-muted"
            fontSize={8}>predicted P(up)</text>
          <text x={10} y={SIZE / 2} textAnchor="middle" className="fill-mentor-muted"
            fontSize={8} transform={`rotate(-90 10 ${SIZE / 2})`}>realised rate</text>
        </svg>
      )}
    </div>
  );
}
