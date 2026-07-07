import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { type MacroPoint, fetchMacroSeries, ingestMacro } from '../api/macro';

// One-line "what it means" per FRED series, plus display formatting.
const META: Record<string, { label: string; meaning: string; fmt: (v: number) => string }> = {
  DGS2: { label: 'US 2Y yield', meaning: 'Short-rate expectations (Fed path)', fmt: (v) => `${v.toFixed(2)}%` },
  DGS10: { label: 'US 10Y yield', meaning: 'Long-end / growth + inflation', fmt: (v) => `${v.toFixed(2)}%` },
  T10Y2Y: { label: 'US 2s10s', meaning: 'Curve slope; negative = inversion', fmt: (v) => `${v.toFixed(2)}%` },
  DTWEXBGS: { label: 'Broad USD index', meaning: 'Dollar strength (EURUSD headwind up)', fmt: (v) => v.toFixed(2) },
  VIXCLS: { label: 'VIX', meaning: 'Risk-on/off; spikes = stress', fmt: (v) => v.toFixed(1) },
};

const ORDER = ['DGS2', 'DGS10', 'T10Y2Y', 'DTWEXBGS', 'VIXCLS'];

export function MacroContextPanel() {
  const queryClient = useQueryClient();
  const macro = useQuery({ queryKey: ['macro'], queryFn: () => fetchMacroSeries(10) });

  const ingest = useMutation({
    mutationFn: () => ingestMacro(3650),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['macro'] }),
  });

  const latest = useMemo(() => {
    const bySeries = new Map<string, MacroPoint[]>();
    for (const p of macro.data ?? []) {
      const arr = bySeries.get(p.series_id) ?? [];
      arr.push(p);
      bySeries.set(p.series_id, arr);
    }
    return bySeries;
  }, [macro.data]);

  return (
    <div className="panel-pad space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-medium text-mentor-fg">Macro drivers</h2>
          <p className="text-xs text-mentor-muted">
            EUR/USD is driven by rates &amp; the dollar far more than headlines — that&apos;s why news
            tone scored 0%. Measured honestly; the promotion gate decides if they help the model.
          </p>
        </div>
        <button
          type="button"
          onClick={() => ingest.mutate()}
          disabled={ingest.isPending}
          className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg disabled:opacity-50"
        >
          {ingest.isPending ? 'Refreshing…' : 'Refresh FRED'}
        </button>
      </div>

      {macro.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!macro.isLoading && (macro.data ?? []).length === 0 && (
        <p className="text-sm text-mentor-muted">
          No macro data yet. Press <b>Refresh FRED</b> to backfill US rates, the 2s10s curve, the
          broad dollar index and VIX (free, no key).
        </p>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {ORDER.map((sid) => {
          const pts = latest.get(sid);
          const meta = META[sid];
          const last = pts?.[pts.length - 1];
          if (!last || !meta) return null;
          const prev = pts.length > 1 ? pts[pts.length - 2] : last;
          const v = Number(last.value);
          const delta = v - Number(prev?.value ?? last.value);
          return (
            <div key={sid} className="rounded-xl border border-mentor-border bg-mentor-panelLight/60 p-3">
              <div className="metric-label" title={meta.meaning}>
                {meta.label}
              </div>
              <div className="metric-value mt-1 text-lg">{meta.fmt(v)}</div>
              <div className={`mt-0.5 text-xs ${delta >= 0 ? 'text-mentor-accentSoft' : 'text-mentor-danger'}`}>
                {delta >= 0 ? '▲' : '▼'} {Math.abs(delta).toFixed(2)}
              </div>
              <div className="mt-1 text-[11px] leading-snug text-mentor-muted">{meta.meaning}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
