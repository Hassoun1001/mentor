import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { listTrades } from '../api/journal';
import { type Timeframe, getPrices } from '../api/prices';
import { listInstruments } from '../api/risk';
import { Chart } from '../components/Chart';

const TIMEFRAMES: Timeframe[] = ['1m', '5m', '1h', '1d'];

export function PricesPage() {
  const [symbol, setSymbol] = useState('EURUSD');
  const [timeframe, setTimeframe] = useState<Timeframe>('1h');
  const [showTrades, setShowTrades] = useState(true);

  const instruments = useQuery({ queryKey: ['instruments'], queryFn: listInstruments });
  const prices = useQuery({
    queryKey: ['prices', symbol, timeframe],
    queryFn: () => getPrices({ symbol, timeframe }),
  });
  const tradesQuery = useQuery({
    queryKey: ['trades', symbol],
    queryFn: () => listTrades(symbol),
  });

  const noData = !prices.isLoading && (prices.data?.bars.length ?? 0) === 0;

  const tradesToShow = useMemo(() => {
    if (!showTrades) return [];
    return (tradesQuery.data ?? []).filter(
      (t) => t.entry_ts && (t.status === 'open' || t.status === 'closed')
    );
  }, [showTrades, tradesQuery.data]);

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Prices</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          Multi-timeframe view of the bars already ingested into the local
          TimescaleDB. Data-quality gaps are flagged below the chart — silent
          gaps quietly poison any model trained on the series.
        </p>
      </header>

      <div className="panel-pad space-y-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="label">Instrument</label>
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
            <label className="label">Timeframe</label>
            <div className="flex gap-2">
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf}
                  type="button"
                  onClick={() => setTimeframe(tf)}
                  className={
                    'rounded-md border px-3 py-1.5 text-sm font-mono transition-colors ' +
                    (tf === timeframe
                      ? 'border-mentor-accent bg-mentor-accent/15 text-mentor-fg'
                      : 'border-mentor-border bg-mentor-panelLight text-mentor-muted hover:text-mentor-fg')
                  }
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>
          <label className="flex items-center gap-2 text-xs text-mentor-fg">
            <input
              type="checkbox"
              checked={showTrades}
              onChange={(e) => setShowTrades(e.target.checked)}
            />
            <span>
              Trade markers
              {tradesToShow.length > 0 && (
                <span className="ml-1 text-mentor-muted">({tradesToShow.length})</span>
              )}
            </span>
          </label>
          <div className="ml-auto text-xs text-mentor-muted">
            {prices.data?.last_seen_at
              ? `last bar: ${new Date(prices.data.last_seen_at).toLocaleString()}`
              : 'no bars yet'}
          </div>
        </div>

        <Chart bars={prices.data?.bars ?? []} trades={tradesToShow} />

        {noData && (
          <p className="rounded-lg border border-mentor-border bg-mentor-panelLight/60 p-3 text-sm text-mentor-muted">
            No bars in the database for {symbol} ({timeframe}). Backfill with:{' '}
            <code className="font-mono text-mentor-fg/80">
              python -m mentor.cli.ingest --symbol {symbol} --timeframe {timeframe} --days 30
            </code>
          </p>
        )}

        {(prices.data?.gaps ?? []).length > 0 && (() => {
          const all = prices.data!.gaps;
          const unexplained = all.filter((g) => !g.weekend_closure);
          const weekends = all.length - unexplained.length;
          const clean = unexplained.length === 0;
          return (
            <div
              className={`rounded-lg border p-3 text-sm ${
                clean
                  ? 'border-mentor-border bg-mentor-panelLight/40'
                  : 'border-mentor-warn/30 bg-mentor-warn/5'
              }`}
            >
              <div
                className={`mb-2 text-xs font-medium uppercase tracking-wider ${
                  clean ? 'text-mentor-muted' : 'text-mentor-warn'
                }`}
              >
                {clean
                  ? `No unexplained gaps — ${weekends} weekend closure${weekends === 1 ? '' : 's'}`
                  : `${unexplained.length} unexplained gap${unexplained.length === 1 ? '' : 's'}`}
              </div>
              <p className="mb-2 text-xs text-mentor-muted">
                FX stops printing from Friday evening to Sunday night, so a hole there is
                the market being shut, not data going missing.
                {weekends > 0 && !clean && ` ${weekends} of these are weekends and are excluded.`}
              </p>
              {!clean && (
                <ul className="space-y-1 font-mono text-xs text-mentor-fg/90">
                  {unexplained.slice(0, 8).map((g) => (
                    <li key={g.expected_after}>
                      {new Date(g.expected_after).toLocaleString()} →{' '}
                      {new Date(g.next_seen).toLocaleString()} ({g.missing_bars} missing)
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })()}
      </div>
    </section>
  );
}
