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
/** Read a `--mentor-*` CSS variable (space-separated RGB channels) as a
 * comma-form `rgb(r, g, b)` — lightweight-charts can't parse the modern
 * space-separated `rgb(r g b)` syntax. */
function themeColor(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (!v) return fallback;
  return `rgb(${v.split(/[\s,]+/).filter(Boolean).join(', ')})`;
}

export function Chart({ bars, trades = [], height = 360 }: ChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const up = themeColor('--mentor-accentSoft', '#2ebd85');
    const down = themeColor('--mentor-danger', '#f6465d');
    const border = themeColor('--mentor-border', '#1e2530');
    const muted = themeColor('--mentor-muted', '#8b949e');
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: muted,
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
      },
      grid: {
        vertLines: { color: border },
        horzLines: { color: border },
      },
      rightPriceScale: { borderColor: border },
      timeScale: { borderColor: border, timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    const series = chart.addCandlestickSeries({
      upColor: up,
      downColor: down,
      borderUpColor: up,
      borderDownColor: down,
      wickUpColor: up,
      wickDownColor: down,
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
    // lightweight-charts throws if times aren't strictly ascending & unique —
    // and mixed-source bars (Twelve Data + Yahoo) can collide on a timestamp.
    // Sort, then keep the last bar for any duplicated time, so setData is safe.
    const byTime = new Map<number, { time: Time; open: number; high: number; low: number; close: number }>();
    for (const b of bars) {
      const time = Math.floor(new Date(b.ts).getTime() / 1000);
      if (!Number.isFinite(time)) continue;
      byTime.set(time, {
        time: time as Time,
        open: Number(b.open),
        high: Number(b.high),
        low: Number(b.low),
        close: Number(b.close),
      });
    }
    const data = [...byTime.values()].sort((a, b) => (a.time as number) - (b.time as number));
    try {
      series.setData(data);
      if (data.length > 0) chart.timeScale().fitContent();
    } catch (err) {
      console.error('chart setData failed', err);
    }
  }, [bars]);

  // ---------- markers ----------
  const markers = useMemo<SeriesMarker<Time>[]>(() => {
    if (!trades.length) return [];
    const up = themeColor('--mentor-accentSoft', '#2ebd85');
    const down = themeColor('--mentor-danger', '#f6465d');
    const muted = themeColor('--mentor-muted', '#8b949e');
    const warn = themeColor('--mentor-warn', '#d29922');
    const accent = themeColor('--mentor-accent', '#2f81f7');
    const out: SeriesMarker<Time>[] = [];
    for (const t of trades) {
      const isLong = t.direction === 'long';
      const r = t.realised_r ? Number(t.realised_r) : null;
      const exitTone = r === null ? muted : r > 0 ? up : r < 0 ? down : warn;
      if (t.entry_ts) {
        out.push({
          time: (new Date(t.entry_ts).getTime() / 1000) as Time,
          position: isLong ? 'belowBar' : 'aboveBar',
          color: accent,
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
