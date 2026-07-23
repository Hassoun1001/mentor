import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import {
  type Heartbeat,
  type LoopEvent,
  type LoopPolicy,
  type LoopStatus,
  type PaperReport,
  type PromotionEntry,
  fetchLoopPaper,
  fetchLoopPromotions,
  fetchLoopStatus,
  getLoopPolicy,
} from '../api/loop';
import { EquityCurve } from '../components/EquityCurve';
import { Metric } from '../components/Metric';
import { SignificanceNote } from '../components/SignificanceNote';

const REFRESH_MS = 30_000;

export function LoopPage() {
  const [minConfidence, setMinConfidence] = useState(0);

  const status = useQuery({
    queryKey: ['loop-status'],
    queryFn: fetchLoopStatus,
    refetchInterval: REFRESH_MS,
  });
  const promotions = useQuery({
    queryKey: ['loop-promotions'],
    queryFn: fetchLoopPromotions,
    refetchInterval: REFRESH_MS * 2,
  });
  const paper = useQuery({
    queryKey: ['loop-paper', minConfidence],
    queryFn: () => fetchLoopPaper(minConfidence),
  });
  const policy = useQuery({
    queryKey: ['loop-policy'],
    queryFn: getLoopPolicy,
    refetchInterval: REFRESH_MS * 2,
  });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Loop</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          The autonomous cycle at work: ingest fresh bars → predict → grade every
          call against reality → retrain on evidence. This page is its heartbeat
          monitor and its scoreboard — a system that runs unattended must be
          observable, or it doesn&apos;t deserve trust.
        </p>
      </header>

      <StatusPanel status={status.data} loading={status.isLoading} />
      {policy.data && <PolicyPanel policy={policy.data} />}
      <PaperPanel
        report={paper.data}
        loading={paper.isLoading}
        minConfidence={minConfidence}
        onMinConfidence={setMinConfidence}
      />
      <EventsPanel events={status.data?.events ?? []} />
      <PromotionsPanel rows={promotions.data ?? []} loading={promotions.isLoading} />
    </section>
  );
}

// ---------- abstention policy ----------

function PolicyPanel({ policy }: { policy: LoopPolicy }) {
  const pct = (v: number) => `${Math.round(v * 100)}%`;
  const gain = policy.brier_all - policy.brier_covered;

  return (
    <div className="panel-pad space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          When the model is willing to speak
        </h2>
        <span
          className={`pill ${
            policy.abstains ? 'text-mentor-accent' : 'text-mentor-muted'
          }`}
        >
          {policy.abstains ? `speaks ${pct(policy.coverage)} of hours` : 'always speaks'}
        </span>
      </div>

      <p className="max-w-3xl text-sm leading-relaxed text-mentor-fg">
        {policy.explanation}
      </p>

      {policy.abstains && (
        <>
          <div className="space-y-1.5">
            <div className="flex h-3 w-full overflow-hidden rounded-full bg-mentor-panelLight">
              <div
                className="h-full bg-mentor-accent"
                style={{ width: `${policy.coverage * 100}%` }}
                title="hours it calls a direction"
              />
            </div>
            <div className="flex justify-between text-xs text-mentor-muted">
              <span>{pct(policy.coverage)} acted on ({policy.n_covered} hours)</span>
              <span>{pct(1 - policy.coverage)} stood aside</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Metric
              label="Brier when it acts"
              value={policy.brier_covered.toFixed(4)}
              sub="lower is better"
              tone={policy.brier_covered < 0.248 ? 'positive' : undefined}
            />
            <Metric
              label="Brier across all hours"
              value={policy.brier_all.toFixed(4)}
              sub="what it would score speaking always"
            />
            <Metric
              label="Gain from abstaining"
              value={`${gain >= 0 ? '+' : ''}${gain.toFixed(4)}`}
              tone={gain > 0 ? 'positive' : 'danger'}
            />
            <Metric
              label="Accuracy when it acts"
              value={pct(policy.accuracy_covered)}
              sub={`of ${policy.n_covered} calls`}
            />
          </div>
        </>
      )}
    </div>
  );
}

// ---------- status + heartbeats ----------

function StatusPanel({ status, loading }: { status: LoopStatus | undefined; loading: boolean }) {
  return (
    <div className="panel-pad space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          Live status
        </h2>
        {status && (
          <div className="flex items-center gap-3 text-xs">
            <Pill on={status.running} yes="loop running" no="loop stopped" />
            <Pill on={status.alerts_enabled} yes="alerts on" no="alerts off" />
          </div>
        )}
      </div>

      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {status && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Metric label="Symbol" value={status.symbol} />
            <Metric
              label="Champion (hourly lane)"
              value={<span className="font-mono text-sm">{status.champion}</span>}
              sub={`${status.timeframe} · ${status.horizon_bars}-bar horizon`}
            />
            <Metric
              label="Champion (daily lane)"
              value={<span className="font-mono text-sm">{status.champion_d1}</span>}
              sub="1d · weekly horizon · the flagship"
            />
            <Metric label="Horizon" value={`${status.horizon_bars} bars`} />
          </div>
          {!status.enabled && (
            <p className="rounded-lg border border-mentor-warn/40 bg-mentor-warn/5 p-3 text-sm text-mentor-fg">
              The loop is disabled (<code className="font-mono">MENTOR_LOOP_ENABLED=false</code>).
              Jobs below won&apos;t tick until it&apos;s enabled — on the server it runs 24/7.
            </p>
          )}
          {status.heartbeats.length > 0 && (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {status.heartbeats.map((b) => (
                <HeartbeatCard key={b.job} beat={b} />
              ))}
            </div>
          )}
          {status.heartbeats.length === 0 && status.enabled && (
            <p className="text-sm text-mentor-muted">
              No job has ticked yet in this process — heartbeats appear after the first runs.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function HeartbeatCard({ beat }: { beat: Heartbeat }) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        beat.ok ? 'border-mentor-border bg-mentor-panelLight' : 'border-mentor-danger/50 bg-mentor-danger/5'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-wider text-mentor-muted">
          {beat.job}
        </span>
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            beat.ok ? 'bg-mentor-accent' : 'bg-mentor-danger'
          }`}
        />
      </div>
      <p className="mt-1 truncate text-sm text-mentor-fg" title={beat.note}>
        {beat.note}
      </p>
      <p className="mt-1 text-xs text-mentor-muted">{new Date(beat.at).toLocaleString()}</p>
    </div>
  );
}

function Pill({ on, yes, no }: { on: boolean; yes: string; no: string }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 font-mono ${
        on
          ? 'bg-mentor-accent/10 text-mentor-accent'
          : 'bg-mentor-muted/10 text-mentor-muted'
      }`}
    >
      {on ? yes : no}
    </span>
  );
}

// ---------- paper-trading scoreboard ----------

function PaperPanel({
  report,
  loading,
  minConfidence,
  onMinConfidence,
}: {
  report: PaperReport | undefined;
  loading: boolean;
  minConfidence: number;
  onMinConfidence: (v: number) => void;
}) {
  return (
    <div className="panel-pad space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
            Paper P&amp;L of the system&apos;s own calls
          </h2>
          <p className="text-xs text-mentor-muted">
            What following every resolved directional prediction would have done.
          </p>
        </div>
        <label className="flex items-center gap-2 text-xs text-mentor-muted">
          Min confidence
          <select
            value={minConfidence}
            onChange={(e) => onMinConfidence(Number(e.target.value))}
            className="rounded-md border border-mentor-border bg-mentor-panel px-2 py-1 font-mono text-xs text-mentor-fg"
          >
            <option value={0}>any</option>
            <option value={0.1}>≥ 10%</option>
            <option value={0.2}>≥ 20%</option>
            <option value={0.3}>≥ 30%</option>
          </select>
        </label>
      </div>

      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {report && report.trades === 0 && (
        <p className="text-sm text-mentor-muted">
          No resolved directional predictions at this confidence floor yet — the
          scoreboard fills as the live loop&apos;s calls get graded.
        </p>
      )}
      {report && report.trades > 0 && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <Metric label="Trades" value={String(report.trades)} />
            <Metric label="Win rate" value={`${(report.win_rate * 100).toFixed(0)}%`} />
            <Metric
              label="Total return"
              value={`${report.total_return_pct >= 0 ? '+' : ''}${report.total_return_pct.toFixed(2)}%`}
              tone={report.total_return_pct >= 0 ? 'positive' : 'danger'}
            />
            <Metric label="Max drawdown" value={`-${report.max_drawdown_pct.toFixed(2)}%`} />
            <Metric label="Avg trade" value={`${report.avg_trade_pct.toFixed(3)}%`} />
          </div>
          <EquityCurve
            points={report.curve.map((p) => ({ ts: p.ts, balance: String(p.equity) }))}
            height={260}
          />
          <SignificanceNote
            verdict={report.verdict}
            significant={report.significant}
            low={report.win_rate_low}
            high={report.win_rate_high}
            baseline={0.5}
          />
          <p className="text-xs text-mentor-muted">{report.note}</p>
        </>
      )}
    </div>
  );
}

// ---------- events ----------

const EVENT_LABEL: Record<string, string> = {
  drift_detected: 'Drift detected',
  promotion: 'Champion promoted',
  quality_skip: 'Prediction skipped (data quality)',
  ingest_error: 'Feed problem',
  alert: 'Alert sent',
};

function EventsPanel({ events }: { events: LoopEvent[] }) {
  return (
    <div className="panel-pad space-y-3">
      <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
        Notable events
      </h2>
      {events.length === 0 && (
        <p className="text-sm text-mentor-muted">
          Nothing notable yet — drift verdicts, promotions, quality skips and
          alerts will show up here as they happen.
        </p>
      )}
      <ul className="space-y-2">
        {events.map((e, i) => (
          <li
            key={`${e.at}-${i}`}
            className="flex items-start gap-3 rounded-lg border border-mentor-border bg-mentor-panelLight p-3 text-sm"
          >
            <span className="whitespace-nowrap font-mono text-xs text-mentor-muted">
              {new Date(e.at).toLocaleString()}
            </span>
            <span>
              <span className="font-medium text-mentor-fg">
                {EVENT_LABEL[e.kind] ?? e.kind}
              </span>{' '}
              <span className="text-mentor-muted">{e.detail}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------- promotions audit trail ----------

function PromotionsPanel({ rows, loading }: { rows: PromotionEntry[]; loading: boolean }) {
  return (
    <div className="panel-pad space-y-3">
      <div>
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          Retrain decisions
        </h2>
        <p className="text-xs text-mentor-muted">
          Every challenger the loop ever trained, and whether it earned promotion.
          Lower Brier is better; a worse model never ships.
        </p>
      </div>
      {loading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!loading && rows.length === 0 && (
        <p className="text-sm text-mentor-muted">
          No retrains recorded yet — the first entry appears after the loop&apos;s
          first scheduled (or drift-triggered) retrain.
        </p>
      )}
      {rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-mentor-border text-xs uppercase tracking-wider text-mentor-muted">
                <th className="py-2 pr-4">When</th>
                <th className="py-2 pr-4">Family</th>
                <th className="py-2 pr-4">Challenger Brier</th>
                <th className="py-2 pr-4">Champion Brier</th>
                <th className="py-2 pr-4">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.at}-${i}`} className="border-b border-mentor-border/50">
                  <td className="whitespace-nowrap py-2 pr-4 font-mono text-xs text-mentor-muted">
                    {new Date(r.at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs">{r.family}</td>
                  <td className="py-2 pr-4 font-mono">{r.challenger_brier.toFixed(4)}</td>
                  <td className="py-2 pr-4 font-mono">
                    {r.champion_brier !== null ? r.champion_brier.toFixed(4) : '—'}
                    {r.champion_brier_fresh !== null && (
                      <span className="ml-1 text-xs text-mentor-muted">(fresh)</span>
                    )}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={`rounded-full px-2 py-0.5 font-mono text-xs ${
                        r.promoted
                          ? 'bg-mentor-accent/10 text-mentor-accent'
                          : 'bg-mentor-muted/10 text-mentor-muted'
                      }`}
                    >
                      {r.promoted ? 'promoted' : 'kept champion'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
