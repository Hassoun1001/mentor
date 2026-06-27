import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import {
  type AuditPrediction,
  type PredictResponse,
  type SnapshotResponse,
  fetchForecastSnapshot,
  listAuditLog,
  listModels,
  resolveAudit,
} from '../api/forecast';
import { type NewsItem, ingestNews, listNews } from '../api/news';
import { listInstruments } from '../api/risk';
import { CalibrationChart } from '../components/CalibrationChart';
import { Metric } from '../components/Metric';
import { WhyButton } from '../components/WhyButton';
import { formatNumber, formatPercent } from '../lib/format';

export function ForecastPage() {
  const queryClient = useQueryClient();
  const [symbol, setSymbol] = useState('EURUSD');
  const [modelName, setModelName] = useState('baseline');
  const [horizonBars, setHorizonBars] = useState(24);

  const instruments = useQuery({ queryKey: ['instruments'], queryFn: listInstruments });
  const models = useQuery({ queryKey: ['models'], queryFn: listModels });
  const news = useQuery({
    queryKey: ['news'],
    queryFn: () => listNews({ limit: 20, onlyClassified: true }),
  });
  const audit = useQuery({ queryKey: ['audit'], queryFn: () => listAuditLog(20) });

  const snapshot = useMutation({
    mutationFn: fetchForecastSnapshot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit'] });
    },
  });

  const ingest = useMutation({
    mutationFn: () => ingestNews(`${symbol.slice(0, 3)} ${symbol.slice(3)} forex`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['news'] }),
  });

  const resolver = useMutation({
    mutationFn: resolveAudit,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['audit'] }),
  });

  const runForecast = () =>
    snapshot.mutate({ symbol, timeframe: '1h', model_name: modelName, horizon_bars: horizonBars });

  const result: SnapshotResponse | undefined = snapshot.data;
  const forecast: PredictResponse | undefined = result?.forecast;

  return (
    <section className="space-y-8">
      <header>
        <h1 className="font-serif text-3xl tracking-tight">Forecast</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          Probability + reasoning, never a price target. The baseline rule
          model is the yardstick; any ML model must beat it out-of-sample
          after costs. Every read is logged to the audit table — the
          calibration loop closes itself.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.1fr,1fr]">
        <div className="panel-pad space-y-4">
          <h2 className="font-medium text-mentor-fg">Generate read</h2>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">Symbol</label>
              <select
                className="input"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
              >
                {(instruments.data ?? []).map((i) => (
                  <option key={i.symbol} value={i.symbol}>
                    {i.base}/{i.quote}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Model</label>
              <select
                className="input"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
              >
                <option value="baseline">baseline (rule)</option>
                {(models.data ?? []).map((m) => (
                  <option key={m.name} value={m.name}>
                    {m.name} (acc {Math.round(m.test_accuracy * 100)}%)
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Horizon (bars)</label>
              <input
                type="number"
                className="input"
                value={horizonBars}
                min={1}
                max={240}
                onChange={(e) => setHorizonBars(Number(e.target.value) || 24)}
              />
            </div>
          </div>

          <button
            type="button"
            disabled={snapshot.isPending}
            onClick={runForecast}
            className="w-full rounded-lg bg-mentor-accent px-4 py-2.5 text-sm font-medium text-white hover:bg-mentor-accentSoft disabled:opacity-50"
          >
            {snapshot.isPending ? 'Reading…' : 'Read the market'}
          </button>

          {snapshot.error instanceof ApiError && (
            <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
              {snapshot.error.message}
            </div>
          )}

          {forecast && result && (
            <div className="space-y-4 border-t border-mentor-border pt-4">
              <div className="flex items-center justify-between">
                <span className="pill capitalize">{forecast.direction}</span>
                <WhyButton
                  topic="expectancy"
                  label="Explain"
                  context={{
                    p_up: forecast.p_up,
                    confidence: forecast.confidence,
                    direction: forecast.direction,
                    model: forecast.model_name,
                    horizon_bars: forecast.horizon_bars,
                    asof_close: forecast.asof_close,
                    features: forecast.features,
                  }}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Metric
                  label="P(up)"
                  value={formatPercent(Number(forecast.p_up) * 100, 1)}
                  tone={Number(forecast.p_up) > 0.5 ? 'positive' : 'danger'}
                />
                <Metric
                  label="Confidence"
                  value={formatPercent(Number(forecast.confidence) * 100, 1)}
                  tone={Number(forecast.confidence) < 0.2 ? 'warn' : 'default'}
                  sub="distance from 50/50"
                />
              </div>
              <p className="rounded-lg border border-mentor-border bg-mentor-panelLight/50 p-3 text-sm leading-relaxed text-mentor-fg">
                {forecast.reasoning}
              </p>
              <p className="text-xs text-mentor-muted">
                As of {new Date(forecast.asof).toLocaleString()}. Resolves at{' '}
                {new Date(result.horizon_at).toLocaleString()}.
              </p>
            </div>
          )}
        </div>

        <NewsPanel
          items={news.data ?? []}
          loading={news.isLoading}
          onIngest={() => ingest.mutate()}
          ingestPending={ingest.isPending}
        />
      </div>

      <AuditPanel
        rows={audit.data ?? []}
        loading={audit.isLoading}
        onResolve={() => resolver.mutate()}
        resolvePending={resolver.isPending}
      />

      <CalibrationChart />
    </section>
  );
}

// ---------- news ----------

function NewsPanel({
  items,
  loading,
  onIngest,
  ingestPending,
}: {
  items: NewsItem[];
  loading: boolean;
  onIngest: () => void;
  ingestPending: boolean;
}) {
  return (
    <div className="panel-pad space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">News context</h2>
        <button
          type="button"
          onClick={onIngest}
          disabled={ingestPending}
          className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg disabled:opacity-50"
        >
          {ingestPending ? 'Ingesting…' : 'Refresh'}
        </button>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && items.length === 0 && (
        <p className="text-sm text-mentor-muted">
          No classified news yet. Press <b>Refresh</b> after setting{' '}
          <code className="font-mono text-mentor-fg/80">NEWSAPI_KEY</code> to
          pull and auto-classify recent headlines.
        </p>
      )}
      <ul className="divide-y divide-mentor-border">
        {items.map((n) => (
          <li key={n.id} className="py-3">
            <div className="flex items-center gap-2 text-xs">
              {n.classification && (
                <span
                  className="pill border-mentor-accent/40 text-mentor-accentSoft capitalize"
                  title={n.classification.rationale}
                >
                  {n.classification.category}
                </span>
              )}
              {n.classification && (
                <span className="text-mentor-muted">
                  impact {formatNumber(n.classification.impact, 2)} · conf{' '}
                  {formatNumber(n.classification.confidence, 2)}
                </span>
              )}
              <span className="ml-auto text-mentor-muted">
                {new Date(n.ts).toLocaleString()}
              </span>
            </div>
            <a
              className="mt-1 block text-sm text-mentor-fg hover:underline"
              href={n.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {n.headline}
            </a>
            {n.classification?.rationale && (
              <p className="mt-1 text-xs text-mentor-muted">
                {n.classification.rationale}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------- audit ----------

function AuditPanel({
  rows,
  loading,
  onResolve,
  resolvePending,
}: {
  rows: AuditPrediction[];
  loading: boolean;
  onResolve: () => void;
  resolvePending: boolean;
}) {
  return (
    <div className="panel-pad space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-medium text-mentor-fg">Prediction audit log</h2>
          <p className="text-xs text-mentor-muted">
            Every forecast logged against its real outcome — closing the
            calibration loop.
          </p>
        </div>
        <button
          type="button"
          onClick={onResolve}
          disabled={resolvePending}
          className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg disabled:opacity-50"
        >
          {resolvePending ? 'Resolving…' : 'Resolve elapsed'}
        </button>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && rows.length === 0 && (
        <p className="text-sm text-mentor-muted">
          No predictions logged yet. Generate a read above.
        </p>
      )}
      <table className="w-full text-xs">
        <thead className="text-mentor-muted">
          <tr className="border-b border-mentor-border">
            <th className="py-2 text-left">As of</th>
            <th className="py-2 text-left">Symbol</th>
            <th className="py-2 text-left">Model</th>
            <th className="py-2 text-right">P(up)</th>
            <th className="py-2 text-right">Conf</th>
            <th className="py-2 text-left">Direction</th>
            <th className="py-2 text-right">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-b border-mentor-border">
              <td className="py-2 font-mono text-mentor-muted">
                {new Date(r.asof).toLocaleString()}
              </td>
              <td className="py-2">{r.symbol}</td>
              <td className="py-2 font-mono text-mentor-muted">{r.model_name}</td>
              <td className="py-2 text-right font-mono">
                {Math.round(Number(r.p_up) * 100)}%
              </td>
              <td className="py-2 text-right font-mono text-mentor-muted">
                {Math.round(Number(r.confidence) * 100)}%
              </td>
              <td className="py-2 capitalize">{r.direction}</td>
              <td className="py-2 text-right">
                {r.realised_outcome === null ? (
                  <span className="text-mentor-muted">pending</span>
                ) : r.realised_outcome === 1 ? (
                  <span className="text-mentor-accentSoft">↑ up</span>
                ) : (
                  <span className="text-mentor-danger">↓ not up</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
