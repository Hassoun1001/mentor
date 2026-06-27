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

export function EquityCurve({ points, height = 320 }: EquityCurveProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);

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
    const series = chart.addAreaSeries({
      lineColor: '#2faa8e',
      topColor: 'rgba(47, 170, 142, 0.35)',
      bottomColor: 'rgba(47, 170, 142, 0.02)',
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
    const data = points.map((p) => ({
      time: (new Date(p.ts).getTime() / 1000) as Time,
      value: Number(p.balance),
    }));
    series.setData(data);
    if (data.length > 0) chart.timeScale().fitContent();
  }, [points]);

  return <div ref={containerRef} style={{ height }} />;
}
