import { useEffect, useRef } from 'react';
import {
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
  createChart,
} from 'lightweight-charts';

import type { EquityPoint } from '../api/backtest';

interface EquityCurveProps {
  points: EquityPoint[];
  height?: number;
}

function themeColor(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (!v) return fallback;
  return `rgb(${v.split(/[\s,]+/).filter(Boolean).join(', ')})`;
}
const alpha = (rgb: string, a: number) =>
  `rgba(${rgb.match(/\d+(?:\.\d+)?/g)?.slice(0, 3).join(', ') ?? '0, 0, 0'}, ${a})`;

export function EquityCurve({ points, height = 320 }: EquityCurveProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const accent = themeColor('--mentor-accent', '#2f81f7');
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
    const series = chart.addAreaSeries({
      lineColor: accent,
      topColor: alpha(accent, 0.28),
      bottomColor: alpha(accent, 0.02),
      lineWidth: 2,
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
    // De-dup + sort by time so lightweight-charts never throws on the data.
    const byTime = new Map<number, { time: Time; value: number }>();
    for (const p of points) {
      const time = Math.floor(new Date(p.ts).getTime() / 1000);
      if (!Number.isFinite(time)) continue;
      byTime.set(time, { time: time as Time, value: Number(p.balance) });
    }
    const data = [...byTime.values()].sort((a, b) => (a.time as number) - (b.time as number));
    try {
      series.setData(data);
      if (data.length > 0) chart.timeScale().fitContent();
    } catch (err) {
      console.error('equity curve setData failed', err);
    }
  }, [points]);

  return <div ref={containerRef} style={{ height }} />;
}
