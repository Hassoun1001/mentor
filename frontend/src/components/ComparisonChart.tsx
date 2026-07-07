import { useEffect, useRef } from 'react';
import {
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
  createChart,
} from 'lightweight-charts';

import type { EquityPoint } from '../api/backtest';

interface ComparisonChartProps {
  primary: { label: string; points: EquityPoint[] };
  secondary?: { label: string; points: EquityPoint[] };
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

/**
 * Two-curve overlay equity chart. Primary in accent green, secondary in
 * amber. We keep both series so absolute dollar values stay readable.
 */
export function ComparisonChart({ primary, secondary, height = 320 }: ComparisonChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const primaryRef = useRef<ISeriesApi<'Area'> | null>(null);
  const secondaryRef = useRef<ISeriesApi<'Area'> | null>(null);

  const primaryLine = themeColor('--mentor-accentSoft', '#2ebd85');
  const secondaryLine = themeColor('--mentor-warn', '#d29922');

  useEffect(() => {
    if (!containerRef.current) return;
    const border = themeColor('--mentor-border', '#1e2530');
    const muted = themeColor('--mentor-muted', '#8b949e');
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: muted,
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
      },
      grid: { vertLines: { color: border }, horzLines: { color: border } },
      rightPriceScale: { borderColor: border },
      timeScale: { borderColor: border, timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    primaryRef.current = chart.addAreaSeries({
      lineColor: primaryLine,
      topColor: alpha(primaryLine, 0.3),
      bottomColor: alpha(primaryLine, 0.02),
      lineWidth: 2,
    });
    secondaryRef.current = chart.addAreaSeries({
      lineColor: secondaryLine,
      topColor: alpha(secondaryLine, 0.25),
      bottomColor: alpha(secondaryLine, 0.02),
      lineWidth: 2,
    });
    chartRef.current = chart;
    return () => {
      chart.remove();
      chartRef.current = null;
      primaryRef.current = null;
      secondaryRef.current = null;
    };
  }, [primaryLine, secondaryLine]);

  useEffect(() => {
    const series = primaryRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;
    try {
      series.setData(toData(primary.points));
      chart.timeScale().fitContent();
    } catch (err) {
      console.error('comparison chart setData failed', err);
    }
  }, [primary]);

  useEffect(() => {
    const series = secondaryRef.current;
    if (!series) return;
    try {
      series.setData(secondary ? toData(secondary.points) : []);
    } catch (err) {
      console.error('comparison chart setData failed', err);
    }
  }, [secondary]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-4 text-xs">
        <Legend dot={primaryLine} label={primary.label} />
        {secondary && <Legend dot={secondaryLine} label={secondary.label} />}
      </div>
      <div ref={containerRef} style={{ height }} />
    </div>
  );
}

function Legend({ dot, label }: { dot: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: dot }} />
      <span className="font-mono text-mentor-fg">{label}</span>
    </div>
  );
}

function toData(points: EquityPoint[]): { time: Time; value: number }[] {
  const byTime = new Map<number, { time: Time; value: number }>();
  for (const p of points) {
    const time = Math.floor(new Date(p.ts).getTime() / 1000);
    if (!Number.isFinite(time)) continue;
    byTime.set(time, { time: time as Time, value: Number(p.balance) });
  }
  return [...byTime.values()].sort((a, b) => (a.time as number) - (b.time as number));
}
