import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import {
  type AuditPrediction,
  type PostMortem,
  getLoopStatus,
  getPostMortem,
  listAuditLog,
  replayPredictions,
  retrainPromote,
  runLoopOnce,
} from '../api/forecast';
import { Metric } from '../components/Metric';
import { formatNumber, formatPercent } from '../lib/format';

export function SystemPredictionsPage() {
  const queryClient = useQueryClient();
  const [banner, setBanner] = useState<string | null>(null);

  const status = useQuery({ queryKey: ['loop-status'], queryFn: getLoopStatus });
  const audit = useQuery({ queryKey: ['system-audit'], queryFn: () => listAuditLog(100) });
  const pm = useQuery({ queryKey: ['postmortem'], queryFn: getPostMortem });

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['system-audit'] });
    queryClient.invalidateQueries({ queryKey: ['postmortem'] });
    queryClient.invalidateQueries({ queryKey: ['loop-status'] });
  };

  const replay = useMutation({
    mutationFn: () =>
      replayPredictions({
        symbol: 'EURUSD',
        timeframe: '1h',
        model_name: 'baseline',
        horizon_bars: 24,
        max_points: 300,
      }),
    onSuccess: (r) => {
      setBanner(
        `Replayed ${r.predictions_written} predictions (${r.skipped_existing} already existed).`
      );
      invalidateAll();
    },
    onError: (e) => setBanner(e instanceof ApiError ? e.message : 'Replay failed.'),
  });

  const runOnce = useMutation({
    mutationFn: runLoopOnce,
    onSuccess: (r) => {
      setBanner(
        r.predicted
          ? `Logged a live prediction; resolved ${r.resolved} due. (${r.note})`
          : `No new prediction (need fresh bars); resolved ${r.resolved}. (${r.note})`
      );
      invalidateAll();
    },
    onError: (e) => setBanner(e instanceof ApiError ? e.message : 'Cycle failed.'),
  });

  const retrain = useMutation({
    mutationFn: retrainPromote,
    onSuccess: (r) => {
      setBanner(r.result);
      invalidateAll();
    },
    onError: (e) => setBanner(e instanceof ApiError ? e.message : 'Retrain failed.'),
  });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">System predictions</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          The system predicts on its own, logs every call, and scores it against the
          real outcome once the horizon passes. It then studies its own hits and
          misses to stay honest about where it's wrong. It is not trying to beat the
          market — it's learning to be well-calibrated about an efficient one.
        </p>
      </header>

      {banner && (
        <div className="rounded-lg border border-mentor-accent/40 bg-mentor-accent/5 p-3 text-sm text-mentor-fg">
          {banner}
        </div>
      )}

      <LoopControls
        status={status.data}
        onReplay={() => replay.mutate()}
        onRunOnce={() => runOnce.mutate()}
        onRetrain={() => retrain.mutate()}
        busy={replay.isPending || runOnce.isPending || retrain.isPending}
      />

      <PostMortemPanel pm={pm.data} loading={pm.isLoading} />

      <PredictionsTable rows={audit.data ?? []} loading={audit.isLoading} />
    </section>
  );
}

function LoopControls({
  status,
  onReplay,
  onRunOnce,
  onRetrain,
  busy,
}: {
  status: ReturnType<typeof Object> | undefined;
  onReplay: () => void;
  onRunOnce: () => void;
  onRetrain: () => void;
  busy: boolean;
}) {
  const s = status as
    | { enabled: boolean; running: boolean; champion: string; symbol: string; timeframe: string }
    | undefined;
  return (
    <div className="panel-pad space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-medium text-mentor-fg">The loop</h2>
        <div className="flex items-center gap-2 text-xs">
          <span className="pill">
            scheduler: {s?.running ? 'running' : s?.enabled ? 'enabled' : 'off'}
          </span>
          {s && (
            <span className="pill">
              champion: <span className="ml-1 font-mono">{s.champion}</span>
            </span>
          )}
        </div>
      </div>
      <p className="text-xs text-mentor-muted">
        The autonomous scheduler is{' '}
        {s?.enabled ? 'on' : (
          <>
            off by default (enable with <code className="font-mono">MENTOR_LOOP_ENABLED=true</code>)
          </>
        )}
        . Use the buttons to drive it by hand: <b>Replay</b> backfills hundreds of
        point-in-time predictions from history so you have real hits/misses now;{' '}
        <b>Run one cycle</b> fires a single live predict+resolve; <b>Retrain</b> trains
        a challenger and promotes it only if it beats the champion.
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={onReplay}
          className="btn-primary"
        >
          Replay history
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onRunOnce}
          className="rounded-lg border border-mentor-border bg-mentor-panelLight px-4 py-2 text-sm text-mentor-fg hover:border-mentor-accent disabled:opacity-50"
        >
          Run one cycle
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onRetrain}
          className="rounded-lg border border-mentor-border bg-mentor-panelLight px-4 py-2 text-sm text-mentor-fg hover:border-mentor-accent disabled:opacity-50"
        >
          Retrain &amp; promote
        </button>
      </div>
    </div>
  );
}

function PostMortemPanel({ pm, loading }: { pm: PostMortem | undefined; loading: boolean }) {
  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="font-medium text-mentor-fg">Post-mortem — why it hit, why it missed</h2>
        <p className="text-xs text-mentor-muted">
          Calibration and feature attribution over every resolved prediction.
        </p>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {pm && pm.sample_size === 0 && (
        <p className="text-sm text-mentor-muted">{pm.headline}</p>
      )}
      {pm && pm.sample_size > 0 && (
        <>
          <p className="rounded-lg border border-mentor-border bg-mentor-panelLight/60 p-3 text-sm leading-relaxed">
            {pm.headline}
          </p>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Metric
              label="Directional accuracy"
              value={formatPercent(pm.directional_accuracy * 100, 1)}
              tone={pm.directional_accuracy > 0.52 ? 'positive' : 'danger'}
              sub={`${pm.hits}W / ${pm.misses}L of ${pm.directional}`}
            />
            <Metric
              label="Brier score"
              value={formatNumber(pm.brier_score, 3)}
              tone={pm.brier_score < 0.25 ? 'positive' : 'danger'}
              sub="0.25 = coin flip; lower better"
            />
            <Metric
              label="Conf. on hits"
              value={formatPercent(pm.avg_confidence_on_hits * 100, 1)}
              tone={pm.avg_confidence_on_hits > pm.avg_confidence_on_misses ? 'positive' : 'warn'}
            />
            <Metric
              label="Conf. on misses"
              value={formatPercent(pm.avg_confidence_on_misses * 100, 1)}
              sub={`${pm.neutral} neutral calls excluded`}
            />
          </div>

          {pm.feature_contrasts.length > 0 && (
            <div>
              <div className="mb-2 text-xs uppercase tracking-wider text-mentor-muted">
                Where hits and misses differ most (feature mean on hits vs misses)
              </div>
              <table className="w-full text-xs">
                <thead className="text-mentor-muted">
                  <tr className="border-b border-mentor-border">
                    <th className="py-1.5 text-left">Feature</th>
                    <th className="py-1.5 text-right">on hits</th>
                    <th className="py-1.5 text-right">on misses</th>
                    <th className="py-1.5 text-right">gap</th>
                  </tr>
                </thead>
                <tbody>
                  {pm.feature_contrasts.map((c) => (
                    <tr key={c.feature} className="border-b border-mentor-border">
                      <td className="py-1.5 font-mono">{c.feature}</td>
                      <td className="py-1.5 text-right font-mono">{c.mean_on_hits.toFixed(4)}</td>
                      <td className="py-1.5 text-right font-mono">{c.mean_on_misses.toFixed(4)}</td>
                      <td
                        className={
                          'py-1.5 text-right font-mono ' +
                          (Math.abs(c.gap) > 0.01 ? 'text-mentor-warn' : 'text-mentor-muted')
                        }
                      >
                        {c.gap >= 0 ? '+' : ''}
                        {c.gap.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function PredictionsTable({ rows, loading }: { rows: AuditPrediction[]; loading: boolean }) {
  const [openId, setOpenId] = useState<string | null>(null);
  return (
    <div className="panel-pad space-y-3">
      <h2 className="font-medium text-mentor-fg">
        Logged predictions{rows.length > 0 && <span className="text-mentor-muted"> ({rows.length})</span>}
      </h2>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && rows.length === 0 && (
        <p className="text-sm text-mentor-muted">
          No predictions yet — press <b>Replay history</b> above to populate.
        </p>
      )}
      <table className="w-full text-xs">
        <thead className="text-mentor-muted">
          <tr className="border-b border-mentor-border">
            <th className="py-2 text-left">As of</th>
            <th className="py-2 text-left">Model</th>
            <th className="py-2 text-left">Lean</th>
            <th className="py-2 text-right">P(up)</th>
            <th className="py-2 text-right">Conf</th>
            <th className="py-2 text-center">Outcome</th>
            <th className="py-2 text-right">Why</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <RowWithReason
              key={r.id}
              row={r}
              open={openId === r.id}
              onToggle={() => setOpenId(openId === r.id ? null : r.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RowWithReason({
  row,
  open,
  onToggle,
}: {
  row: AuditPrediction;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr className="border-b border-mentor-border">
        <td className="py-2 font-mono text-mentor-muted">{new Date(row.asof).toLocaleString()}</td>
        <td className="py-2 font-mono text-mentor-muted">{shortModel(row.model_name)}</td>
        <td className="py-2 capitalize">{row.direction}</td>
        <td className="py-2 text-right font-mono">{Math.round(Number(row.p_up) * 100)}%</td>
        <td className="py-2 text-right font-mono text-mentor-muted">
          {Math.round(Number(row.confidence) * 100)}%
        </td>
        <td className="py-2 text-center">
          <OutcomeBadge correct={row.correct} outcome={row.realised_outcome} />
        </td>
        <td className="py-2 text-right">
          <button
            type="button"
            onClick={onToggle}
            className="rounded-full border border-mentor-border bg-mentor-panelLight px-2 py-0.5 text-[10px] uppercase tracking-wider text-mentor-muted hover:text-mentor-fg"
          >
            {open ? 'hide' : 'why'}
          </button>
        </td>
      </tr>
      {open && (
        <tr className="border-b border-mentor-border bg-mentor-panelLight/30">
          <td colSpan={7} className="px-2 py-3 text-xs leading-relaxed text-mentor-fg/90">
            {row.reasoning}
          </td>
        </tr>
      )}
    </>
  );
}

function OutcomeBadge({ correct, outcome }: { correct: boolean | null; outcome: number | null }) {
  if (outcome === null) {
    return <span className="text-mentor-muted">pending</span>;
  }
  if (correct === null) {
    // neutral lean — no directional stance; show what actually happened
    return (
      <span className="text-mentor-muted">
        {outcome === 1 ? 'went up' : 'went down'}
      </span>
    );
  }
  return correct ? (
    <span className="rounded-full bg-mentor-accent/15 px-2 py-0.5 text-mentor-accentSoft">✓ hit</span>
  ) : (
    <span className="rounded-full bg-mentor-danger/15 px-2 py-0.5 text-mentor-danger">✗ miss</span>
  );
}

function shortModel(name: string): string {
  // "regime_adjusted(sklearn_hgb(h=24))" → "hgb", "baseline_rule(h=24)" → "baseline"
  if (name.includes('hgb')) return 'ml';
  if (name.includes('baseline')) return 'baseline';
  return name.slice(0, 14);
}
