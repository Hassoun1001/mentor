import { useEffect, useMemo, useRef } from 'react';
import {
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarker,
  type Time,
  createChart,
} from 'lightweight-charts';

import type { Bar } from '../api/prices';
import type { Trade } from '../api/journal';

interface ChartProps {
  bars: Bar[];
  trades?: Trade[];
  height?: number;
}

/**
 * Lightweight-charts wrapper with optional trade markers.
 *
 * We re-use a single chart + series instance; only the data and
 * markers are replaced on each render. Markers come from the journal:
 * arrow-up for entries, square for exits — green when realised R is
 * positive, red when negative. Markers without a matching bar (entry
 * outside the visible window) are dropped.
 */
export function Chart({ bars, trades = [], height = 360 }: ChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#8aa098',
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
      },
      grid: {
        vertLines: { color: '#1d3a33' },
        horzLines: { color: '#1d3a33' },
      },
      rightPriceScale: { borderColor: '#1d3a33' },
      timeScale: { borderColor: '#1d3a33', timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    const series = chart.addCandlestickSeries({
      upColor: '#2faa8e',
      downColor: '#d75f5f',
      borderUpColor: '#2faa8e',
      borderDownColor: '#d75f5f',
      wickUpColor: '#2faa8e',
      wickDownColor: '#d75f5f',
    });
    chartRef.current = chart;
    seriesRef.current = series;

    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;
    const data = bars.map((b) => ({
      time: (new Date(b.ts).getTime() / 1000) as Time,
      open: Number(b.open),
      high: Number(b.high),
      low: Number(b.low),
      close: Number(b.close),
    }));
    series.setData(data);
    if (data.length > 0) {
      chart.timeScale().fitContent();
    }
  }, [bars]);

  // ---------- markers ----------
  const markers = useMemo<SeriesMarker<Time>[]>(() => {
    if (!trades.length) return [];
    const out: SeriesMarker<Time>[] = [];
    for (const t of trades) {
      const isLong = t.direction === 'long';
      const r = t.realised_r ? Number(t.realised_r) : null;
      const exitTone =
        r === null ? '#8aa098' : r > 0 ? '#2faa8e' : r < 0 ? '#d75f5f' : '#d4a14a';
      if (t.entry_ts) {
        out.push({
          time: (new Date(t.entry_ts).getTime() / 1000) as Time,
          position: isLong ? 'belowBar' : 'aboveBar',
          color: '#1f8a70',
          shape: isLong ? 'arrowUp' : 'arrowDown',
          text: `${isLong ? 'BUY' : 'SELL'} ${Number(t.size_lots).toFixed(2)}`,
        });
      }
      if (t.exit_ts) {
        out.push({
          time: (new Date(t.exit_ts).getTime() / 1000) as Time,
          position: isLong ? 'aboveBar' : 'belowBar',
          color: exitTone,
          shape: 'square',
          text: r !== null ? `${r >= 0 ? '+' : ''}${r.toFixed(2)}R` : 'EXIT',
        });
      }
    }
    return out.sort((a, b) => (a.time as number) - (b.time as number));
  }, [trades]);

  useEffect(() => {
    const series = seriesRef.current;
    if (series) series.setMarkers(markers);
  }, [markers]);

  return <div ref={containerRef} style={{ height }} />;
}
