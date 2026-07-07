import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import {
  type CoverageRow,
  type CrossSourceResponse,
  getCoverage,
  getCrossSource,
  ingestPrices,
} from '../api/prices';
import { Metric } from '../components/Metric';

const SYMBOL = 'EURUSD';

export function DataHealthPage() {
  const queryClient = useQueryClient();
  const [banner, setBanner] = useState<string | null>(null);

  const coverage = useQuery({ queryKey: ['coverage', SYMBOL], queryFn: () => getCoverage(SYMBOL) });
  const cross = useQuery({
    queryKey: ['cross-source', SYMBOL],
    queryFn: () => getCrossSource(SYMBOL, '1d', 45),
    retry: false,
  });

  const backfill = useMutation({
    mutationFn: (source: 'yahoo' | 'failover') =>
      ingestPrices(SYMBOL, { timeframe: '1d', days_back: 3650, source }),
    onSuccess: (r) => {
      setBanner(
        `Ingested from ${r.source}: fetched ${r.fetched}, ${r.persisted} new bars added.`
      );
      queryClient.invalidateQueries({ queryKey: ['coverage', SYMBOL] });
    },
    onError: (e) => setBanner(e instanceof ApiError ? e.message : 'Backfill failed.'),
  });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Data health</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          How much price data you hold, where it came from, and whether your
          sources agree. A model is only as honest as the bars under it — silent
          gaps or a feed that quietly disagrees will poison every backtest that
          crosses them.
        </p>
      </header>

      {banner && (
        <div className="rounded-lg border border-mentor-accent/40 bg-mentor-accent/5 p-3 text-sm text-mentor-fg">
          {banner}
        </div>
      )}

      <CrossSourcePanel data={cross.data} loading={cross.isLoading} error={cross.error} />

      <CoveragePanel
        rows={coverage.data?.coverage ?? []}
        loading={coverage.isLoading}
        onBackfill={(s) => backfill.mutate(s)}
        busy={backfill.isPending}
      />
    </section>
  );
}

function CrossSourcePanel({
  data,
  loading,
  error,
}: {
  data: CrossSourceResponse | undefined;
  loading: boolean;
  error: unknown;
}) {
  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="font-medium text-mentor-fg">Do the feeds agree?</h2>
        <p className="text-xs text-mentor-muted">
          Twelve Data vs Yahoo daily closes over the last 45 days. FX has no
          official daily close, so some disagreement is expected — a large gap
          means one feed is stale or quoting a different fixing.
        </p>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {error instanceof Error && (
        <p className="text-sm text-mentor-muted">
          Cross-source check unavailable ({error.message}). It needs both Twelve
          Data (key) and Yahoo configured.
        </p>
      )}
      {data && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Metric
              label="Agreement"
              value={data.agree ? 'In tolerance' : 'Diverges'}
              tone={data.agree ? 'positive' : 'warn'}
              sub={`${data.source_a} vs ${data.source_b}`}
            />
            <Metric
              label="Mean |Δ close|"
              value={`${data.mean_diff_pips.toFixed(1)} pips`}
              tone={data.mean_diff_pips > 20 ? 'warn' : 'positive'}
            />
            <Metric
              label="Max |Δ close|"
              value={`${data.max_diff_pips.toFixed(1)} pips`}
              tone={data.max_diff_pips > 50 ? 'warn' : 'default'}
            />
            <Metric label="Overlapping days" value={data.overlapping} sub={`${data.bars_a} / ${data.bars_b} bars`} />
          </div>
          {!data.agree && (
            <p className="rounded-lg border border-mentor-warn/30 bg-mentor-warn/5 p-3 text-xs leading-relaxed text-mentor-fg/90">
              The two feeds diverge by more than the pip tolerance. That's normal
              for daily FX (different end-of-day cutoffs) but worth knowing before
              you trust any single number — the model trains on one convention.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function CoveragePanel({
  rows,
  loading,
  onBackfill,
  busy,
}: {
  rows: CoverageRow[];
  loading: boolean;
  onBackfill: (source: 'yahoo' | 'failover') => void;
  busy: boolean;
}) {
  return (
    <div className="panel-pad space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-medium text-mentor-fg">Coverage</h2>
          <p className="text-xs text-mentor-muted">Bars held per timeframe, span, and source.</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => onBackfill('yahoo')}
            className="rounded-lg bg-mentor-accent px-3 py-2 text-xs font-medium text-white hover:bg-mentor-accentHover disabled:opacity-50"
          >
            Backfill 10y daily (Yahoo)
          </button>
        </div>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && rows.length === 0 && (
        <p className="text-sm text-mentor-muted">No price data yet — backfill above.</p>
      )}
      {rows.length > 0 && (
        <table className="w-full text-sm">
          <thead className="text-mentor-muted">
            <tr className="border-b border-mentor-border text-xs uppercase tracking-wider">
              <th className="py-2 text-left">Timeframe</th>
              <th className="py-2 text-right">Bars</th>
              <th className="py-2 text-left">Span</th>
              <th className="py-2 text-left">Sources</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.timeframe} className="border-b border-mentor-border">
                <td className="py-2 font-mono">{r.timeframe}</td>
                <td className="py-2 text-right font-mono">{r.bars.toLocaleString()}</td>
                <td className="py-2 text-xs text-mentor-muted">
                  {r.first_ts ? new Date(r.first_ts).toLocaleDateString() : '—'}
                  {' → '}
                  {r.last_ts ? new Date(r.last_ts).toLocaleDateString() : '—'}
                </td>
                <td className="py-2 text-xs">
                  {Object.entries(r.sources).map(([src, n]) => (
                    <span
                      key={src}
                      className="mr-1 inline-block rounded-full border border-mentor-border bg-mentor-panelLight px-2 py-0.5 text-mentor-muted"
                    >
                      {src} {n.toLocaleString()}
                    </span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
