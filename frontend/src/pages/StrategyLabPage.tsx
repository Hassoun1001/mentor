import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';

import {
  type LabCandidate,
  type LabStatus,
  type PaperPosition,
  type PaperRecord,
  type StrategyLab,
  type TradeStats,
  fetchPaperPositions,
  fetchStrategyLab,
} from '../api/strategyLab';
import { Metric } from '../components/Metric';
import { PageHeader } from '../components/PageHeader';

const REFRESH_MS = 60_000;

const STATUS_ORDER: LabStatus[] = ['recommended', 'paper', 'demoted', 'retired', 'rejected'];

const STATUS_LABEL: Record<LabStatus, string> = {
  recommended: 'Recommended',
  paper: 'Paper trading',
  demoted: 'Demoted — still paper trading',
  retired: 'Retired',
  rejected: 'Failed the history test',
};

const STATUS_CHIP: Record<LabStatus, string> = {
  recommended: 'chip-up',
  paper: 'chip-accent',
  demoted: 'chip-warn',
  retired: 'chip-down',
  rejected: 'pill',
};

const r = (v: number | null | undefined, digits = 2) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(digits)}R`;
const pct = (v: number | null | undefined) => (v == null ? '—' : `${(v * 100).toFixed(0)}%`);
const day = (iso: string | null | undefined) => (iso ? iso.slice(0, 10) : '—');

export function StrategyLabPage() {
  const lab = useQuery({
    queryKey: ['strategy-lab'],
    queryFn: fetchStrategyLab,
    refetchInterval: REFRESH_MS,
  });

  return (
    <section className="space-y-8">
      <PageHeader
        title="Strategy Lab"
        subtitle={
          <>
            Where trading ideas are tested the way a disciplined professional would. Each idea
            is a complete plan — entry, stop, target, time limit, position size — with a reason
            it might work. It is tested once on years of history it was not tuned on, then
            paper-traded against the live market, and only called <em>recommended</em> if it
            proves itself there too. Most ideas fail. That is the honest result, not a fault.
            The system never places a real trade.
          </>
        }
      />

      {lab.isLoading && <div className="panel-pad text-sm text-mentor-muted">Loading the lab…</div>}
      {lab.error && (
        <div className="panel-pad text-sm text-mentor-danger">
          Could not load the lab: {(lab.error as Error).message}
        </div>
      )}
      {lab.data && <LabBody lab={lab.data} />}
    </section>
  );
}

function LabBody({ lab }: { lab: StrategyLab }) {
  const sorted = [...lab.candidates].sort(
    (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
  );
  return (
    <>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Metric label="Ideas tested" value={lab.counts.evaluated} sub="each tested exactly once" />
        <Metric
          label="Variations tried"
          value={lab.trials_ever}
          sub="every one counted"
          explainer="Every parameter set ever tried is recorded and never forgotten. Try enough variations and one will look brilliant by luck, so each extra try raises the bar for everyone."
        />
        <Metric
          label="Today's bar"
          value={lab.bar_now.toFixed(2)}
          sub="score an idea must reach"
          explainer="The evidence score a new idea must beat: the best score pure luck would produce across all the variations tried, plus the usual 95% safety margin."
        />
        <Metric
          label="Paper trading"
          value={lab.counts.paper}
          tone={lab.counts.paper > 0 ? 'positive' : 'default'}
          sub="passed history, being watched"
        />
        <Metric
          label="Recommended"
          value={lab.counts.recommended}
          tone={lab.counts.recommended > 0 ? 'positive' : 'default'}
          sub="proven live as well"
        />
      </div>

      {(lab.waiting.length > 0 || lab.changed.length > 0) && (
        <div className="panel-pad space-y-1 text-sm">
          {lab.waiting.length > 0 && (
            <p className="text-mentor-muted">
              Waiting for their test: <span className="font-mono">{lab.waiting.join(', ')}</span>.
              The lab tests new ideas shortly after a restart and every Sunday.
            </p>
          )}
          {lab.changed.length > 0 && (
            <p className="text-mentor-warn">
              Edited after testing, so not re-tested:{' '}
              <span className="font-mono">{lab.changed.join(', ')}</span>. A revised idea needs a
              new name — re-testing the same idea would spend the untouched history twice.
            </p>
          )}
        </div>
      )}

      <WeekPanel events={lab.events_week} />

      {sorted.length === 0 ? (
        <div className="panel-pad text-sm text-mentor-muted">
          No idea has been tested yet. The first test runs shortly after the server starts.
        </div>
      ) : (
        <div className="space-y-4">
          {sorted.map((c) => (
            <CandidateCard key={c.key} c={c} account={lab.paper_account} />
          ))}
        </div>
      )}
    </>
  );
}

function WeekPanel({ events }: { events: StrategyLab['events_week'] }) {
  if (events.length === 0) return null;
  // Rejections are the common case and each card already says why; list
  // them by name and keep the full lines for news that changes something.
  const rejected = events.filter((e) => e.kind === 'rejected');
  const news = events.filter((e) => e.kind !== 'rejected');
  return (
    <div className="panel-pad space-y-3">
      <h2 className="section-title">This week</h2>
      <ul className="space-y-2 text-sm">
        {news.map((e) => (
          <li key={`${e.key}-${e.at}-${e.kind}`} className="text-mentor-muted">
            <span className="font-mono text-mentor-fg">{e.key}</span> — {e.kind}: {e.detail}
          </li>
        ))}
        {rejected.length > 0 && (
          <li className="text-mentor-muted">
            Tested and rejected ({rejected.length}):{' '}
            <span className="font-mono text-mentor-fg">
              {rejected.map((e) => e.key).join(', ')}
            </span>
            . Each card below says why.
          </li>
        )}
      </ul>
    </div>
  );
}

function CandidateCard({ c, account }: { c: LabCandidate; account: string }) {
  const ev = c.evidence;
  return (
    <article className="panel-pad space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-mentor-fg">{c.title}</h2>
          <p className="font-mono text-xs text-mentor-muted">
            {c.key} · {c.timeframe === '1h' ? 'hourly bars' : 'daily bars'} · tested{' '}
            {day(c.evaluated_at)}
          </p>
        </div>
        <span className={clsx('chip', STATUS_CHIP[c.status])}>{STATUS_LABEL[c.status]}</span>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <div className="eyebrow">Why it might work</div>
          <p className="mt-1 text-sm text-mentor-fg">{c.hypothesis}</p>
        </div>
        {c.plan && (
          <div>
            <div className="eyebrow">
              {c.status === 'rejected' ? 'The plan it would have traded' : 'The plan'}
            </div>
            <p className="mt-1 text-sm text-mentor-fg">{c.plan.plan}</p>
          </div>
        )}
      </div>

      <HistoryVerdict c={c} />

      {ev.reasons && ev.reasons.length > 0 && (
        <ul className="list-disc space-y-1 pl-5 text-sm text-mentor-muted">
          {ev.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}

      {c.paper && <PaperPanel c={c} paper={c.paper} account={account} />}
    </article>
  );
}

function HistoryVerdict({ c }: { c: LabCandidate }) {
  const ev = c.evidence;
  const oos: TradeStats | undefined = ev.out_of_sample;
  const holdout: TradeStats | undefined = ev.holdout;
  const passed = Boolean(ev.passed);
  return (
    <div className="space-y-2">
      <div className="eyebrow">The history test</div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric
          label="Trades it was graded on"
          value={oos?.n ?? 0}
          sub="never seen while choosing settings"
          explainer="Settings were chosen on earlier years and graded on later ones, then once more on a final stretch kept untouched. Only these graded trades count."
        />
        <Metric
          label="Average per trade"
          value={r(oos?.mean_r)}
          tone={oos && oos.mean_r > 0 ? 'positive' : 'danger'}
          sub={
            oos?.ci_low != null && oos.ci_high != null
              ? `95% range ${r(oos.ci_low)} to ${r(oos.ci_high)}, after costs`
              : 'after spread and slippage'
          }
          explainer="R is profit in units of the amount risked: +1R means the trade made what it risked. Zero is breakeven, because costs are already taken out."
        />
        <Metric
          label="Evidence score"
          value={ev.score != null ? ev.score.toFixed(2) : '—'}
          tone={passed ? 'positive' : 'default'}
          sub={
            ev.bar != null
              ? `needed ${ev.bar.toFixed(2)} (${ev.n_trials ?? '?'} variations tried)`
              : undefined
          }
          explainer="How strongly the graded trades beat zero, after allowing for every variation ever tried in this lab."
        />
        <Metric
          label="Untouched final stretch"
          value={holdout && holdout.n > 0 ? r(holdout.mean_r) : '—'}
          tone={holdout && holdout.n > 0 ? (holdout.mean_r > 0 ? 'positive' : 'danger') : 'default'}
          sub={
            ev.data?.holdout_start
              ? `${holdout?.n ?? 0} trades since ${day(ev.data.holdout_start)}`
              : undefined
          }
          explainer="A stretch of recent history the lab never looks at until the very end, and only once per idea."
        />
      </div>
      {oos && oos.win_rate != null && oos.breakeven_win_rate != null && (
        <p className="text-xs text-mentor-muted">
          Won {pct(oos.win_rate)} of graded trades; with its typical win and loss sizes it needed{' '}
          {pct(oos.breakeven_win_rate)} to break even.
          {c.status !== 'rejected' && !c.clears_todays_bar && (
            <span className="text-mentor-warn">
              {' '}
              More variations have been tried since it passed; it would not clear today&apos;s bar.
            </span>
          )}
        </p>
      )}
    </div>
  );
}

function PaperPanel({
  c,
  paper,
  account,
}: {
  c: LabCandidate;
  paper: PaperRecord;
  account: string;
}) {
  const [showLog, setShowLog] = useState(false);
  const progress = Math.min(1, paper.trades / paper.next_check_at);
  return (
    <div className="space-y-3 rounded-xl border border-mentor-border bg-mentor-panelLight/50 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="eyebrow">Paper trading since {day(c.paper_started_at)}</div>
        <span className="text-xs text-mentor-muted">
          sized on a {account} account · last bar {paper.last_bar_ts?.slice(0, 16) ?? '—'}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="Closed paper trades" value={paper.trades} />
        <Metric
          label="Average per trade"
          value={r(paper.mean_r)}
          tone={paper.mean_r == null ? 'default' : paper.mean_r > 0 ? 'positive' : 'danger'}
        />
        <Metric
          label="Win rate"
          value={pct(paper.win_rate)}
          sub={
            paper.breakeven_win_rate != null
              ? `needs ${pct(paper.breakeven_win_rate)} at its payoff`
              : undefined
          }
        />
        <Metric
          label="Next verdict"
          value={`${paper.trades} / ${paper.next_check_at}`}
          sub="judged only at checkpoints"
          explainer="Re-checking after every trade and stopping at the first good-looking moment is a reliable way to fool yourself, so promotion is only considered every 30 trades."
        />
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-mentor-panel">
        <div className="h-full bg-mentor-accent" style={{ width: `${progress * 100}%` }} />
      </div>
      <p className="text-sm text-mentor-muted">{c.status_reason}</p>
      {paper.open_position && <OpenPosition p={paper.open_position} label="Open position" />}
      {paper.pending_order && (
        <OpenPosition p={paper.pending_order} label="Waiting to fill at the next open" />
      )}
      <button type="button" className="btn-ghost" onClick={() => setShowLog((v) => !v)}>
        {showLog ? 'Hide' : 'Show'} paper trade log
      </button>
      {showLog && <PositionsTable strategyKey={c.key} />}
    </div>
  );
}

function OpenPosition({ p, label }: { p: PaperPosition; label: string }) {
  return (
    <div className="rounded-lg border border-mentor-border bg-mentor-panel p-3 text-sm">
      <div className="eyebrow">{label}</div>
      <p className="mt-1 text-mentor-fg">
        <span className={clsx('chip', p.direction === 'long' ? 'chip-up' : 'chip-down')}>
          {p.direction}
        </span>{' '}
        {p.entry_price != null && <>entered {p.entry_price.toFixed(5)} · </>}
        stop {p.stop_price.toFixed(5)}
        {p.target_price != null && <> · target {p.target_price.toFixed(5)}</>}
        {p.suggested_lots != null && <> · {p.suggested_lots.toFixed(2)} lots</>}
      </p>
      <p className="mt-1 text-xs text-mentor-muted">{p.reason}</p>
    </div>
  );
}

function PositionsTable({ strategyKey }: { strategyKey: string }) {
  const q = useQuery({
    queryKey: ['strategy-lab-positions', strategyKey],
    queryFn: () => fetchPaperPositions(strategyKey),
  });
  if (q.isLoading) return <p className="text-sm text-mentor-muted">Loading…</p>;
  if (!q.data || q.data.length === 0)
    return <p className="text-sm text-mentor-muted">No paper trades yet.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead className="text-mentor-muted">
          <tr>
            <th className="py-1 pr-3">Signal</th>
            <th className="py-1 pr-3">Side</th>
            <th className="py-1 pr-3">Status</th>
            <th className="py-1 pr-3">Entry</th>
            <th className="py-1 pr-3">Exit</th>
            <th className="py-1 pr-3">Result</th>
          </tr>
        </thead>
        <tbody className="font-mono text-mentor-fg">
          {q.data.map((p) => (
            <tr key={p.signal_ts} className="border-t border-mentor-border">
              <td className="py-1 pr-3">{p.signal_ts.slice(0, 16)}</td>
              <td className="py-1 pr-3">{p.direction}</td>
              <td className="py-1 pr-3">{p.status}</td>
              <td className="py-1 pr-3">{p.entry_price?.toFixed(5) ?? '—'}</td>
              <td className="py-1 pr-3">
                {p.exit_price != null ? `${p.exit_price.toFixed(5)} (${p.exit_reason})` : p.note ?? '—'}
              </td>
              <td
                className={clsx(
                  'py-1 pr-3',
                  p.realised_r != null && (p.realised_r > 0 ? 'text-mentor-accentSoft' : 'text-mentor-danger')
                )}
              >
                {r(p.realised_r)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
