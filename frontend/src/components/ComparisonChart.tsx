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

const COLORS = {
  primary: { line: '#2faa8e', top: 'rgba(47, 170, 142, 0.30)', bottom: 'rgba(47, 170, 142, 0.02)' },
  secondary: { line: '#d4a14a', top: 'rgba(212, 161, 74, 0.25)', bottom: 'rgba(212, 161, 74, 0.02)' },
};

/**
 * Two-curve overlay equity chart.
 *
 * Primary is rendered in mentor-accent green; secondary (optional) in
 * mentor-warn gold. We keep the two series so the user can read absolute
 * dollar values for each — relative comparisons are misleading when the
 * starting balances diverge.
 */
export function ComparisonChart({ primary, secondary, height = 320 }: ComparisonChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const primaryRef = useRef<ISeriesApi<'Area'> | null>(null);
  const secondaryRef = useRef<ISeriesApi<'Area'> | null>(null);

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
    primaryRef.current = chart.addAreaSeries({
      lineColor: COLORS.primary.line,
      topColor: COLORS.primary.top,
      bottomColor: COLORS.primary.bottom,
      lineWidth: 2,
    });
    secondaryRef.current = chart.addAreaSeries({
      lineColor: COLORS.secondary.line,
      topColor: COLORS.secondary.top,
      bottomColor: COLORS.secondary.bottom,
      lineWidth: 2,
    });
    chartRef.current = chart;
    return () => {
      chart.remove();
      chartRef.current = null;
      primaryRef.current = null;
      secondaryRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = primaryRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;
    series.setData(toData(primary.points));
    chart.timeScale().fitContent();
  }, [primary]);

  useEffect(() => {
    const series = secondaryRef.current;
    if (!series) return;
    series.setData(secondary ? toData(secondary.points) : []);
  }, [secondary]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-4 text-xs">
        <Legend dot={COLORS.primary.line} label={primary.label} />
        {secondary && <Legend dot={COLORS.secondary.line} label={secondary.label} />}
      </div>
      <div ref={containerRef} style={{ height }} />
    </div>
  );
}

function Legend({ dot, label }: { dot: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="inline-block h-3 w-3 rounded-full"
        style={{ backgroundColor: dot }}
      />
      <span className="font-mono text-mentor-fg">{label}</span>
    </div>
  );
}

function toData(points: EquityPoint[]): { time: Time; value: number }[] {
  return points.map((p) => ({
    time: (new Date(p.ts).getTime() / 1000) as Time,
    value: Number(p.balance),
  }));
}
