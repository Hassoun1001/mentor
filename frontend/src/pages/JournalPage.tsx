import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  type Analytics,
  type ChecklistResponse,
  type Trade,
  cancelTrade,
  closeTrade,
  evaluateChecklist,
  getAnalytics,
  getMistakeCatalog,
  getRootCauseReview,
  listTrades,
  openTrade,
  planTrade,
} from '../api/journal';
import { ApiError } from '../api/client';
import { SignificanceNote } from '../components/SignificanceNote';
import { Field } from '../components/Field';
import { Metric } from '../components/Metric';
import { formatLots, formatMoney, formatNumber, formatPercent } from '../lib/format';

interface NewTradeForm {
  account_balance: string;
  max_risk_percent: string;
  symbol: string;
  direction: 'long' | 'short';
  size_lots: string;
  entry: string;
  stop: string;
  target: string;
  initial_risk_amount: string;
  risk_currency: string;
  reason: string;
}

const EMPTY_FORM: NewTradeForm = {
  // Without these the guardrail rule cannot run at all.
  account_balance: '10000',
  max_risk_percent: '1',
  symbol: 'EURUSD',
  direction: 'long',
  size_lots: '0.33',
  entry: '1.08500',
  stop: '1.08200',
  target: '1.09100',
  initial_risk_amount: '100',
  risk_currency: 'USD',
  reason: '',
};

export function JournalPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<NewTradeForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const trades = useQuery({ queryKey: ['trades'], queryFn: () => listTrades() });
  const analytics = useQuery({ queryKey: ['analytics'], queryFn: () => getAnalytics() });

  const checklist = useQuery<ChecklistResponse>({
    queryKey: ['checklist', form],
    queryFn: () =>
      evaluateChecklist({
        symbol: form.symbol,
        direction: form.direction,
        size_lots: form.size_lots || '0',
        entry: form.entry || '0.0001',
        stop: form.stop || '0.0001',
        target: form.target || null,
        initial_risk_amount: form.initial_risk_amount || '0.01',
        risk_currency: form.risk_currency,
        reason: form.reason,
        // Without these the guardrail rule cannot run, and it used to
        // report a green pass anyway — a risk control that reassured
        // without ever checking anything.
        account_balance: form.account_balance || null,
        max_risk_per_trade_percent: form.max_risk_percent || null,
      }),
    enabled: isMostlyComplete(form),
    retry: false,
  });

  const planMutation = useMutation({
    mutationFn: planTrade,
    onSuccess: () => {
      setForm({ ...EMPTY_FORM, symbol: form.symbol });
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['trades'] });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Could not log trade.');
    },
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['trades'] });
    queryClient.invalidateQueries({ queryKey: ['analytics'] });
    queryClient.invalidateQueries({ queryKey: ['root-causes'] });
  };

  const checklistPassed = checklist.data?.passed ?? false;

  return (
    <section className="space-y-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Journal</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          The user's win rate, expectancy, and R-multiple distribution — the real
          measure of progress. Every trade requires a written reason. No trade
          opens without the pre-trade checklist.
        </p>
      </header>

      <AnalyticsPanel data={analytics.data} loading={analytics.isLoading} />

      <RootCausePanel />

      <div className="grid gap-6 lg:grid-cols-[1.1fr,1fr]">
        <div className="panel-pad space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-medium text-mentor-fg">Log new trade</h2>
            <ChecklistBadge data={checklist.data} loading={checklist.isFetching} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Symbol</label>
              <input
                className="input"
                value={form.symbol}
                maxLength={8}
                onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })}
              />
            </div>
            <div>
              <label className="label">Direction</label>
              <div className="grid grid-cols-2 gap-2">
                {(['long', 'short'] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setForm({ ...form, direction: d })}
                    className={
                      'rounded-lg border px-3 py-2 text-sm font-medium capitalize transition-colors ' +
                      (form.direction === d
                        ? 'border-mentor-accent bg-mentor-accent/15 text-mentor-fg'
                        : 'border-mentor-border bg-mentor-panelLight text-mentor-muted hover:text-mentor-fg')
                    }
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Field
              label="Entry"
              type="number"
              step="any"
              value={form.entry}
              onChange={(e) => setForm({ ...form, entry: e.target.value })}
            />
            <Field
              label="Stop"
              type="number"
              step="any"
              value={form.stop}
              onChange={(e) => setForm({ ...form, stop: e.target.value })}
            />
            <Field
              label="Target"
              type="number"
              step="any"
              value={form.target}
              onChange={(e) => setForm({ ...form, target: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Field
              label="Size (lots)"
              type="number"
              step="0.01"
              value={form.size_lots}
              onChange={(e) => setForm({ ...form, size_lots: e.target.value })}
            />
            <Field
              label="Risk amount"
              type="number"
              step="any"
              suffix={form.risk_currency}
              value={form.initial_risk_amount}
              onChange={(e) =>
                setForm({ ...form, initial_risk_amount: e.target.value })
              }
            />
            <Field
              label="Currency"
              value={form.risk_currency}
              maxLength={3}
              onChange={(e) =>
                setForm({ ...form, risk_currency: e.target.value.toUpperCase() })
              }
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field
              label="Account balance"
              type="number"
              step="any"
              suffix={form.risk_currency}
              value={form.account_balance}
              onChange={(e) => setForm({ ...form, account_balance: e.target.value })}
            />
            <Field
              label="Max risk per trade"
              type="number"
              step="0.1"
              suffix="%"
              value={form.max_risk_percent}
              onChange={(e) => setForm({ ...form, max_risk_percent: e.target.value })}
            />
          </div>

          <div>
            <label className="label">Reason — why this trade?</label>
            <textarea
              className="input min-h-[5rem] resize-y"
              placeholder="At least 20 characters. What's the setup, and what would change your mind?"
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
            />
            <p className="mt-1 text-xs text-mentor-muted">
              {form.reason.length} / 20 characters minimum
            </p>
          </div>

          {checklist.data &&
            checklist.data.items.some((i) => !i.passed || i.skipped) && (
              <ChecklistFailures
                items={checklist.data.items.filter((i) => !i.passed || i.skipped)}
              />
            )}

          {error && (
            <div className="rounded-lg border border-mentor-danger/40 bg-mentor-danger/10 p-3 text-sm text-mentor-danger">
              {error}
            </div>
          )}

          <button
            type="button"
            disabled={!checklistPassed || planMutation.isPending}
            onClick={() =>
              planMutation.mutate({
                symbol: form.symbol,
                direction: form.direction,
                size_lots: form.size_lots,
                entry: form.entry,
                stop: form.stop,
                target: form.target || null,
                initial_risk: { amount: form.initial_risk_amount, currency: form.risk_currency },
                reason: form.reason,
              })
            }
            className={
              'w-full rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ' +
              (checklistPassed
                ? 'bg-mentor-accent text-white hover:bg-mentor-accentHover'
                : 'cursor-not-allowed bg-mentor-panelLight text-mentor-muted')
            }
          >
            {checklistPassed
              ? planMutation.isPending
                ? 'Logging…'
                : 'Log planned trade'
              : 'Complete the checklist to continue'}
          </button>
        </div>

        <div className="panel-pad space-y-5">
          <h2 className="font-medium text-mentor-fg">Recent trades</h2>
          <TradesList
            trades={trades.data ?? []}
            loading={trades.isLoading}
            onChanged={refresh}
          />
        </div>
      </div>
    </section>
  );
}

function isMostlyComplete(form: NewTradeForm): boolean {
  return Boolean(
    form.symbol &&
      form.size_lots &&
      form.entry &&
      form.stop &&
      form.initial_risk_amount &&
      form.risk_currency
  );
}

// ---------- analytics ----------

function AnalyticsPanel({ data, loading }: { data?: Analytics; loading: boolean }) {
  return (
    <div className="panel-pad">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">Running edge</h2>
        {loading && <span className="text-xs text-mentor-muted">loading…</span>}
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric
          label="Trades"
          value={data ? data.sample_size : '—'}
          sub={data ? `${data.wins}W · ${data.losses}L · ${data.breakeven}BE` : null}
        />
        <Metric
          label="Win rate"
          value={data ? formatPercent(data.win_rate_percent, 1) : '—'}
        />
        <Metric
          label="Expectancy (R)"
          value={data ? formatNumber(data.expectancy_r, 3) : '—'}
          tone={data && Number(data.expectancy_r) > 0 ? 'positive' : 'default'}
          sub={data ? `avg win ${formatNumber(data.avg_win_r)}R · avg loss ${formatNumber(data.avg_loss_r)}R` : null}
        />
        <Metric
          label="Total R"
          value={data ? formatNumber(data.total_r, 2) : '—'}
          tone={data && Number(data.total_r) > 0 ? 'positive' : 'default'}
          sub={data ? `PF ${data.profit_factor ? formatNumber(data.profit_factor) : '—'}` : null}
        />
      </div>
      {data && (
        <div className="mt-4 space-y-3">
          <p className="text-sm text-mentor-fg/85">{data.interpretation}</p>
          {data.sample_size > 0 && (
            <>
              <SignificanceNote
                verdict={data.win_rate_verdict}
                significant={data.win_rate_significant}
                low={data.win_rate_low}
                high={data.win_rate_high}
                baseline={0.5}
              />
              <ExpectancyNote data={data} />
            </>
          )}
        </div>
      )}
    </div>
  );
}

/** The expectancy interval, on a track centred on zero R. */
function ExpectancyNote({ data }: { data: Analytics }) {
  if (!data.expectancy_verdict) return null;
  const ok = data.expectancy_significant && data.expectancy_low > 0;
  const bad = data.expectancy_significant && data.expectancy_high < 0;

  // Scale the track to whichever bound is furthest from zero, so the
  // interval and the zero mark are both always visible.
  const reach = Math.max(0.05, Math.abs(data.expectancy_low), Math.abs(data.expectancy_high));
  const pos = (v: number) => ((v + reach) / (2 * reach)) * 100;

  const border = ok
    ? 'border-mentor-accent/40 bg-mentor-accent/5'
    : bad
      ? 'border-mentor-danger/40 bg-mentor-danger/5'
      : 'border-mentor-warn/40 bg-mentor-warn/5';
  const bar = ok ? 'bg-mentor-accent' : bad ? 'bg-mentor-danger' : 'bg-mentor-warn';

  return (
    <div className={`rounded-lg border p-3 ${border}`}>
      <p className="text-sm leading-relaxed text-mentor-fg">{data.expectancy_verdict}</p>
      <div className="relative mt-3 h-6">
        <div className="absolute inset-x-0 top-2.5 h-1 rounded-full bg-mentor-panelLight" />
        <div
          className={`absolute top-2 h-2 rounded-full ${bar}`}
          style={{
            left: `${pos(data.expectancy_low)}%`,
            width: `${pos(data.expectancy_high) - pos(data.expectancy_low)}%`,
          }}
        />
        <div className="absolute top-0 h-6 w-px bg-mentor-fg/60" style={{ left: '50%' }} />
      </div>
      <div className="flex justify-between text-[10px] text-mentor-muted">
        <span>{(-reach).toFixed(2)}R</span>
        <span>break even (0R)</span>
        <span>+{reach.toFixed(2)}R</span>
      </div>
      {data.trades_needed !== null && !data.expectancy_significant && (
        <p className="mt-2 text-xs text-mentor-muted">
          {data.sample_size} of roughly {data.trades_needed.toLocaleString()} trades needed
          before this number settles.
        </p>
      )}
    </div>
  );
}

// ---------- checklist ----------

function ChecklistBadge({
  data,
  loading,
}: {
  data?: ChecklistResponse;
  loading: boolean;
}) {
  if (loading) return <span className="pill">checking…</span>;
  if (!data) return <span className="pill">incomplete</span>;
  if (data.passed)
    return (
      <span className="pill border-mentor-accent/50 text-mentor-accentSoft">
        ✓ checklist passes
      </span>
    );
  return (
    <span className="pill border-mentor-warn/50 text-mentor-warn">
      {data.failed_keys.length} unmet
    </span>
  );
}

function ChecklistFailures({ items }: { items: ChecklistResponse['items'] }) {
  return (
    <ul className="space-y-1.5 rounded-lg border border-mentor-warn/30 bg-mentor-warn/5 p-3 text-sm text-mentor-fg/90">
      {items.map((i) => (
        <li key={i.key}>
          <span
            className={`font-medium ${i.skipped ? 'text-mentor-muted' : 'text-mentor-warn'}`}
          >
            {i.skipped ? '?' : '×'}
          </span>{' '}
          {i.label}
          {i.skipped && <span className="text-mentor-muted"> (not checked)</span>}
          {i.detail && <span className="text-mentor-muted"> — {i.detail}</span>}
        </li>
      ))}
    </ul>
  );
}

// ---------- trades list ----------

function TradesList({
  trades,
  loading,
  onChanged,
}: {
  trades: Trade[];
  loading: boolean;
  onChanged: () => void;
}) {
  if (loading) return <p className="text-sm text-mentor-muted">Loading…</p>;
  if (trades.length === 0)
    return (
      <p className="text-sm text-mentor-muted">
        No trades yet. Log one with the form on the left — the discipline gate is
        the whole point.
      </p>
    );
  return (
    <ul className="divide-y divide-mentor-border">
      {trades.map((t) => (
        <TradeRow key={t.id} trade={t} onChanged={onChanged} />
      ))}
    </ul>
  );
}

function TradeRow({ trade, onChanged }: { trade: Trade; onChanged: () => void }) {
  const [exitPrice, setExitPrice] = useState('');
  const [acting, setActing] = useState(false);
  const [tags, setTags] = useState<string[]>([]);

  const toggleTag = (tag: string) =>
    setTags((prev) => (prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]));

  // Only ask "why did it lose?" once the typed exit actually implies a loss —
  // prompting on every close trains people to click through it.
  const losing = useMemo(() => {
    const exit = Number(exitPrice);
    const entry = Number(trade.actual_entry ?? trade.planned_entry);
    if (!exitPrice || !Number.isFinite(exit) || !Number.isFinite(entry)) return false;
    return trade.direction === 'long' ? exit < entry : exit > entry;
  }, [exitPrice, trade.actual_entry, trade.planned_entry, trade.direction]);

  const handle = async (fn: () => Promise<unknown>) => {
    setActing(true);
    try {
      await fn();
      onChanged();
    } catch (e) {
      if (e instanceof ApiError) {
        alert(e.message);
      }
    } finally {
      setActing(false);
    }
  };

  const r = trade.realised_r;
  const tone = useMemo(() => {
    if (trade.status !== 'closed' || r === null) return 'text-mentor-muted';
    if (Number(r) > 0) return 'text-mentor-accentSoft';
    if (Number(r) < 0) return 'text-mentor-danger';
    return 'text-mentor-muted';
  }, [trade.status, r]);

  return (
    <li className="space-y-2 py-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium">{trade.symbol}</span>
            <span className="pill capitalize">{trade.direction}</span>
            <span className="pill capitalize">{trade.status}</span>
            <span className="text-mentor-muted">
              {formatLots(trade.size_lots)} lots
            </span>
          </div>
          <div className="mt-1 text-xs text-mentor-muted">{trade.reason}</div>
        </div>
        <div className={`text-right font-mono text-sm ${tone}`}>
          {trade.status === 'closed' ? (
            <>
              <div>{r === null ? '—' : `${formatNumber(r, 2)}R`}</div>
              <div className="text-xs">
                {trade.realised_pnl
                  ? formatMoney(trade.realised_pnl.amount, trade.realised_pnl.currency)
                  : ''}
              </div>
            </>
          ) : (
            <div className="text-xs text-mentor-muted">
              risk {formatMoney(trade.initial_risk.amount, trade.initial_risk.currency)}
            </div>
          )}
        </div>
      </div>

      {trade.status === 'planned' && (
        <div className="flex flex-wrap items-center gap-2">
          <button
            disabled={acting}
            onClick={() => handle(() => openTrade(trade.id, trade.planned_entry))}
            className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs hover:text-mentor-fg"
          >
            Open at {trade.planned_entry}
          </button>
          <button
            disabled={acting}
            onClick={() => handle(() => cancelTrade(trade.id))}
            className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg"
          >
            Cancel
          </button>
        </div>
      )}

      {trade.status === 'open' && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!exitPrice) return;
            handle(() => closeTrade(trade.id, exitPrice, { mistake_tags: tags }));
          }}
          className="space-y-3"
        >
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="number"
              step="any"
              placeholder="Exit price"
              value={exitPrice}
              onChange={(e) => setExitPrice(e.target.value)}
              className="input w-32"
            />
            <button
              type="submit"
              disabled={acting || !exitPrice}
              className="rounded-md bg-mentor-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
            >
              Close
            </button>
            {losing && (
              <span className="text-xs text-mentor-muted">
                Closing at a loss — tag why, so the pattern can be counted.
              </span>
            )}
          </div>
          {losing && <TagPicker selected={tags} onToggle={toggleTag} />}
        </form>
      )}
    </li>
  );
}

// ---------- root-cause tagging ----------

function TagPicker({
  selected,
  onToggle,
}: {
  selected: string[];
  onToggle: (tag: string) => void;
}) {
  const catalog = useQuery({
    queryKey: ['mistake-catalog'],
    queryFn: getMistakeCatalog,
    staleTime: Infinity,
  });
  if (!catalog.data) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {catalog.data.map((d) => {
        const on = selected.includes(d.tag);
        const good = !d.is_process_error;
        return (
          <button
            key={d.tag}
            type="button"
            title={d.question}
            onClick={() => onToggle(d.tag)}
            className={`rounded-full border px-2.5 py-1 text-xs transition ${
              on
                ? good
                  ? 'border-mentor-accent/50 bg-mentor-accent/15 text-mentor-accent'
                  : 'border-mentor-danger/50 bg-mentor-danger/15 text-mentor-danger'
                : 'border-mentor-border bg-mentor-panelLight text-mentor-muted hover:text-mentor-fg'
            }`}
          >
            {d.label}
          </button>
        );
      })}
    </div>
  );
}

function RootCausePanel() {
  const review = useQuery({ queryKey: ['root-causes'], queryFn: getRootCauseReview });
  const r = review.data;
  if (!r) return null;

  const worst = r.causes[0];
  const worstR = worst ? Math.abs(Number(worst.r_lost)) : 0;

  return (
    <div className="panel-pad space-y-4">
      <div>
        <h2 className="text-sm font-medium uppercase tracking-wider text-mentor-muted">
          Why your losers lost
        </h2>
        <p className="mt-1 text-sm text-mentor-fg">{r.verdict}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs md:grid-cols-4">
        <Stat label="Closed losses" value={r.closed_losses} />
        <Stat label="Tagged" value={r.tagged_losses} />
        <Stat label="Fixable habits" value={r.process_error_losses} tone="danger" />
        <Stat label="Good process" value={r.good_process_losses} tone="ok" />
      </div>

      {r.causes.length > 0 && (
        <ul className="space-y-3">
          {r.causes.map((c) => {
            const lost = Math.abs(Number(c.r_lost));
            const width = worstR > 0 ? Math.max(4, (lost / worstR) * 100) : 0;
            return (
              <li key={c.tag} className="space-y-1">
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className={c.is_process_error ? 'text-mentor-fg' : 'text-mentor-accent'}>
                    {c.label}
                  </span>
                  <span className="font-mono text-xs text-mentor-muted">
                    −{lost.toFixed(2)}R · {c.occurrences}×
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-mentor-panelLight">
                  <div
                    className={`h-full rounded-full ${
                      c.is_process_error ? 'bg-mentor-danger' : 'bg-mentor-accent'
                    }`}
                    style={{ width: `${width}%` }}
                  />
                </div>
                <p className="text-xs leading-relaxed text-mentor-muted">{c.fix}</p>
              </li>
            );
          })}
        </ul>
      )}

      {r.untagged_losses > 0 && (
        <p className="text-xs text-mentor-muted">
          {r.untagged_losses} loss(es) untagged — tag them at close and they join the ranking.
        </p>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: 'ok' | 'danger';
}) {
  const cls =
    tone === 'danger'
      ? 'text-mentor-danger'
      : tone === 'ok'
        ? 'text-mentor-accent'
        : 'text-mentor-fg';
  return (
    <div className="rounded-lg border border-mentor-border bg-mentor-panelLight px-3 py-2">
      <div className="text-mentor-muted">{label}</div>
      <div className={`mt-0.5 font-mono text-lg ${cls}`}>{value}</div>
    </div>
  );
}
