import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { clsx } from 'clsx';

import { ApiError } from '../api/client';
import { type VolForecast, type VolResponse, fetchVolatility } from '../api/forecast';
import { Metric } from './Metric';

const regimeTone: Record<VolForecast['regime'], 'default' | 'positive' | 'warn' | 'danger'> = {
  calm: 'positive',
  normal: 'default',
  wide: 'danger',
};

export function VolatilityCard({ symbol }: { symbol: string }) {
  const [horizon, setHorizon] = useState(5);
  const [useMl, setUseMl] = useState(false);

  const vol = useMutation({
    mutationFn: () =>
      fetchVolatility({
        symbol,
        timeframe: '1d',
        horizon_bars: horizon,
        model: useMl ? 'ml' : 'ewma',
      }),
  });

  const data: VolResponse | undefined = vol.data;
  const f = data?.forecast;

  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="font-medium text-mentor-fg">Expected range (volatility)</h2>
        <p className="text-xs text-mentor-muted">
          Direction is ~a coin flip, but volatility <em>clusters</em> — so unlike an arrow,
          a range is genuinely forecastable. EWMA is the transparent baseline; the ML model
          is shown only if it beats EWMA out-of-sample.
        </p>
      </div>

      <div className="grid grid-cols-[1fr,auto] items-end gap-4">
        <div>
          <label className="label">Horizon (days)</label>
          <input
            type="number"
            className="input"
            value={horizon}
            min={1}
            max={60}
            onChange={(e) => setHorizon(Number(e.target.value) || 5)}
          />
        </div>
        <label className="flex items-center gap-2 pb-2 text-xs text-mentor-muted">
          <input type="checkbox" checked={useMl} onChange={(e) => setUseMl(e.target.checked)} />
          grade ML vs EWMA
        </label>
      </div>

      <button
        type="button"
        disabled={vol.isPending}
        onClick={() => vol.mutate()}
        className="btn-primary w-full"
      >
        {vol.isPending ? 'Estimating…' : 'Estimate the range'}
      </button>

      {vol.error instanceof ApiError && (
        <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
          {vol.error.message}
        </div>
      )}

      {f && data && (
        <div className="space-y-4 border-t border-mentor-border pt-4">
          <div className="flex items-center justify-between">
            <span className={clsx('pill capitalize')}>{f.regime}</span>
            <span className="text-xs font-mono text-mentor-muted">{f.model_name}</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Metric
              label={`Expected move (${f.horizon_bars}d)`}
              value={`±${Math.round(Number(f.expected_range_pips))} pips`}
              tone={regimeTone[f.regime]}
              sub={
                f.range_low_pips != null && f.range_high_pips != null && f.coverage != null
                  ? `${Math.round(Number(f.range_low_pips))}–${Math.round(Number(f.range_high_pips))} pips at ${Math.round(Number(f.coverage) * 100)}% coverage`
                  : '1σ band — two-in-three of moves land inside'
              }
            />
            <Metric
              label="Vs history"
              value={`${Math.round(Number(f.percentile_vs_history) * 100)}th pct`}
              sub="percentile of trailing realized vol"
            />
          </div>
          <p className="rounded-lg border border-mentor-border bg-mentor-panelLight/50 p-3 text-sm leading-relaxed text-mentor-fg">
            {f.reasoning}
          </p>
          <div
            className={clsx(
              'rounded-lg border p-3 text-sm leading-relaxed',
              data.guidance.event_freeze
                ? 'border-mentor-warn/50 bg-mentor-warn/10 text-mentor-warn'
                : 'border-mentor-border bg-mentor-panelLight/50 text-mentor-fg'
            )}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">
                {data.guidance.event_freeze ? '⚠ Event freeze' : 'Sizing guidance'}
              </span>
              <span className="font-mono text-xs">
                stop ≈ {Math.round(Number(data.guidance.suggested_stop_pips))} pips
              </span>
            </div>
            <p className="mt-1 text-xs">{data.guidance.rationale}</p>
          </div>
          {data.eval && (
            <div
              className={clsx(
                'rounded-lg border p-3 text-xs',
                data.eval.beats_ewma
                  ? 'border-mentor-accent/40 bg-mentor-accent/10 text-mentor-accentSoft'
                  : 'border-mentor-border bg-mentor-panelLight/50 text-mentor-muted'
              )}
            >
              <div className="font-medium">
                {data.eval.beats_ewma ? 'ML beats EWMA out-of-sample' : 'EWMA kept — ML did not beat it'}
              </div>
              <div className="mt-1 font-mono">
                MAE ML {data.eval.ml_mae.toExponential(2)} vs EWMA {data.eval.ewma_mae.toExponential(2)} ·
                QLIKE {data.eval.ml_qlike.toFixed(3)} vs {data.eval.ewma_qlike.toFixed(3)} · R²-vs-EWMA{' '}
                {data.eval.r2_vs_ewma >= 0 ? '+' : ''}
                {data.eval.r2_vs_ewma.toFixed(3)} (n={data.eval.n_test})
              </div>
            </div>
          )}
          <p className="text-xs text-mentor-muted">As of {new Date(f.asof).toLocaleString()}.</p>
        </div>
      )}
    </div>
  );
}
