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
  listTrades,
  openTrade,
  planTrade,
} from '../api/journal';
import { ApiError } from '../api/client';
import { Field } from '../components/Field';
import { Metric } from '../components/Metric';
import { formatLots, formatMoney, formatNumber, formatPercent } from '../lib/format';

interface NewTradeForm {
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
  };

  const checklistPassed = checklist.data?.passed ?? false;

  return (
    <section className="space-y-8">
      <header className="flex flex-col gap-2">
        <h1 className="font-serif text-3xl tracking-tight">Journal</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          The user's win rate, expectancy, and R-multiple distribution — the real
          measure of progress. Every trade requires a written reason. No trade
          opens without the pre-trade checklist.
        </p>
      </header>

      <AnalyticsPanel data={analytics.data} loading={analytics.isLoading} />

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

          {checklist.data && checklist.data.failed_keys.length > 0 && (
            <ChecklistFailures items={checklist.data.items.filter((i) => !i.passed)} />
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
                ? 'bg-mentor-accent text-white hover:bg-mentor-accentSoft'
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
        <p className="mt-4 text-sm text-mentor-fg/85">{data.interpretation}</p>
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
          <span className="font-medium text-mentor-warn">×</span> {i.label}
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
            handle(() => closeTrade(trade.id, exitPrice));
          }}
          className="flex flex-wrap items-center gap-2"
        >
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
        </form>
      )}
    </li>
  );
}
