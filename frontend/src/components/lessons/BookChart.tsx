/**
 * Draws any chart the book describes as data: candlesticks, lines or bars.
 *
 * The SVG is rebuilt at the container's real width rather than scaled, so labels
 * keep a readable size on a phone. Colours come from the app theme via
 * `currentColor`, so light mode, dark mode and print all work without extra code.
 */
import { useLayoutEffect, useRef, useState } from 'react';

import type { BookChart as BookChartData, ChartTone } from '../../api/curriculum';

const TONE: Record<ChartTone, string> = {
  fg: 'text-mentor-fg',
  muted: 'text-mentor-muted',
  accent: 'text-mentor-accent',
  accentSoft: 'text-mentor-accentSoft',
  warn: 'text-mentor-warn',
  danger: 'text-mentor-danger',
};

const DATA_KIND: Record<BookChartData['data_kind'], { label: string; tone: string }> = {
  illustrative: {
    label: 'Illustrative: made up to show the idea, not a real market',
    tone: 'border-mentor-warn/40 text-mentor-warn',
  },
  calculated: {
    label: 'Calculated from the assumptions below',
    tone: 'border-mentor-accent/40 text-mentor-accent',
  },
  published: {
    label: 'Published figures, redrawn',
    tone: 'border-mentor-accentSoft/40 text-mentor-accentSoft',
  },
};

const MARGIN = { top: 12, right: 12, bottom: 22, left: 50 };

function formatValue(value: number, format: BookChartData['y_format']): string {
  if (format === 'pct') return `${Math.round(value * 10) / 10}%`;
  if (format === 'r') return `${Math.round(value * 10) / 10}R`;
  if (format === 'usd') {
    const abs = Math.abs(value);
    const text = abs >= 1000 ? `${Math.round(abs / 100) / 10}k` : `${Math.round(abs)}`;
    return `${value < 0 ? '-' : ''}$${text}`;
  }
  if (format === 'plain') return `${Math.round(value * 10) / 10}`;
  const abs = Math.abs(value);
  const digits = abs < 10 ? 4 : abs < 1000 ? 2 : 0;
  return value.toFixed(digits);
}

function niceTicks(min: number, max: number, count: number): number[] {
  const span = max - min || 1;
  const rough = span / count;
  const power = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * power).find((s) => s >= rough) ?? rough;
  const ticks: number[] = [];
  for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-6; v += step) ticks.push(v);
  return ticks;
}

function useWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    setWidth(element.clientWidth);
    const observer = new ResizeObserver(([entry]) => {
      if (entry) setWidth(entry.contentRect.width);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return { ref, width };
}

function Axis({
  ticks,
  scale,
  x,
  right,
  format,
}: {
  ticks: number[];
  scale: (v: number) => number;
  x: number;
  right: number;
  format: BookChartData['y_format'];
}) {
  return (
    <g>
      {ticks.map((t) => (
        <g key={t} className="text-mentor-border">
          <line x1={x} x2={right} y1={scale(t)} y2={scale(t)} stroke="currentColor" strokeWidth={1} />
          <text
            x={x - 6}
            y={scale(t) + 3.5}
            textAnchor="end"
            fontSize={10}
            fill="rgb(var(--mentor-muted))"
          >
            {formatValue(t, format)}
          </text>
        </g>
      ))}
    </g>
  );
}

function linePath(
  values: (number | null)[],
  xs: (i: number) => number,
  ys: (v: number) => number
): string {
  let d = '';
  let pen = false;
  values.forEach((value, i) => {
    if (value == null) {
      pen = false;
      return;
    }
    d += `${pen ? 'L' : 'M'}${xs(i).toFixed(1)} ${ys(value).toFixed(1)}`;
    pen = true;
  });
  return d;
}

function PriceChart({ chart, width }: { chart: BookChartData; width: number }) {
  const isCandles = chart.kind === 'candles';
  const lowerSeries = chart.series.filter((s) => s.panel === 'lower');
  const lowerLines = chart.hlines.filter((h) => h.panel === 'lower');
  const hasLower = lowerSeries.length > 0;
  const mainSeries = chart.series.filter((s) => s.panel === 'main');
  const mainLines = chart.hlines.filter((h) => h.panel === 'main');

  const height = Math.max(240, Math.min(380, width * 0.62)) + (hasLower ? 90 : 0);
  const lowerH = hasLower ? 82 : 0;
  const gap = hasLower ? 18 : 0;
  const plotBottom = height - MARGIN.bottom - lowerH - gap;
  const plotRight = width - MARGIN.right;
  const plotWidth = Math.max(plotRight - MARGIN.left, 40);

  const pointCount = isCandles
    ? chart.candles.length
    : Math.max(0, ...chart.series.map((s) => s.values.length));
  const slot = plotWidth / Math.max(pointCount, 1);
  const xAt = isCandles
    ? (i: number) => MARGIN.left + (i + 0.5) * slot
    : (i: number) => MARGIN.left + (i * plotWidth) / Math.max(pointCount - 1, 1);

  const values: number[] = [];
  if (isCandles) chart.candles.forEach(([, h, l]) => values.push(h, l));
  mainSeries.forEach((s) => s.values.forEach((v) => v != null && values.push(v)));
  mainLines.forEach((h) => values.push(h.y));
  chart.zones.forEach((z) => values.push(z.y0, z.y1));
  chart.marks.forEach((m) => values.push(m.y));
  chart.segments.forEach((s) => values.push(s.y0, s.y1));
  const minY = values.length ? Math.min(...values) : 0;
  const maxY = values.length ? Math.max(...values) : 1;
  const pad = (maxY - minY || Math.abs(maxY) || 1) * 0.08;
  const yMin = minY - pad;
  const yMax = maxY + pad;
  const yAt = (v: number) =>
    MARGIN.top + ((yMax - v) / (yMax - yMin)) * (plotBottom - MARGIN.top);

  const lowerValues: number[] = [];
  lowerSeries.forEach((s) => s.values.forEach((v) => v != null && lowerValues.push(v)));
  lowerLines.forEach((h) => lowerValues.push(h.y));
  const lowerMin = Math.min(0, ...(lowerValues.length ? lowerValues : [0]));
  const lowerMax = Math.max(1e-9, ...(lowerValues.length ? lowerValues : [1]));
  const lowerTop = plotBottom + gap;
  const lowerBottom = lowerTop + lowerH;
  const lowerYAt = (v: number) =>
    lowerTop + ((lowerMax - v) / (lowerMax - lowerMin || 1)) * (lowerBottom - lowerTop);

  const candleWidth = Math.max(1.5, Math.min(slot * 0.68, 9));
  const clampLabelX = (x: number) => Math.min(Math.max(x, MARGIN.left + 18), plotRight - 18);
  const axisStep =
    pointCount > 1 ? Math.max(1, Math.round(pointCount / Math.max(3, Math.floor(plotWidth / 90)))) : 1;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      role="img"
      aria-label={chart.title}
      className="block"
    >
      <Axis
        ticks={niceTicks(yMin, yMax, 5)}
        scale={yAt}
        x={MARGIN.left}
        right={plotRight}
        format={chart.y_format}
      />

      {chart.zones.map((zone, i) => {
        const x0 = zone.x0 == null ? MARGIN.left : xAt(zone.x0);
        const x1 = zone.x1 == null ? plotRight : xAt(zone.x1);
        const top = yAt(Math.max(zone.y0, zone.y1));
        const bottom = yAt(Math.min(zone.y0, zone.y1));
        return (
          <g key={`z${i}`} className={TONE[zone.tone]}>
            <rect
              x={x0}
              y={top}
              width={Math.max(x1 - x0, 1)}
              height={Math.max(bottom - top, 1)}
              fill="currentColor"
              fillOpacity={0.12}
            />
            {zone.label && (
              <text x={x0 + 4} y={top + 12} fontSize={10.5} fill="currentColor" fontWeight={600}>
                {zone.label}
              </text>
            )}
          </g>
        );
      })}

      {mainLines.map((line, i) => (
        <g key={`h${i}`} className={TONE[line.tone]}>
          <line
            x1={MARGIN.left}
            x2={plotRight}
            y1={yAt(line.y)}
            y2={yAt(line.y)}
            stroke="currentColor"
            strokeWidth={1.2}
            strokeDasharray="5 3"
          />
          {line.label && (
            <text
              x={plotRight - 2}
              y={yAt(line.y) - 3}
              textAnchor="end"
              fontSize={10.5}
              fill="currentColor"
              fontWeight={600}
            >
              {line.label}
            </text>
          )}
        </g>
      ))}

      {mainSeries
        .filter((s) => s.style === 'area')
        .map((s) => {
          const first = s.values.findIndex((v) => v != null);
          const lastIndex = s.values.length - 1;
          const d = `${linePath(s.values, xAt, yAt)}L${xAt(lastIndex).toFixed(1)} ${plotBottom}L${xAt(first).toFixed(1)} ${plotBottom}Z`;
          return (
            <path
              key={`a${s.name}`}
              d={d}
              className={TONE[s.tone]}
              fill="currentColor"
              fillOpacity={0.15}
            />
          );
        })}

      {isCandles &&
        chart.candles.map(([open, high, low, close], i) => {
          const up = close >= open;
          const x = xAt(i);
          const top = yAt(Math.max(open, close));
          const bottom = yAt(Math.min(open, close));
          return (
            <g key={i} className={up ? 'text-mentor-accentSoft' : 'text-mentor-danger'}>
              <line x1={x} x2={x} y1={yAt(high)} y2={yAt(low)} stroke="currentColor" strokeWidth={1} />
              <rect
                x={x - candleWidth / 2}
                y={top}
                width={candleWidth}
                height={Math.max(bottom - top, 1)}
                fill="currentColor"
              />
            </g>
          );
        })}

      {mainSeries
        .filter((s) => s.style !== 'area')
        .map((s) => (
          <path
            key={`s${s.name}`}
            d={linePath(s.values, xAt, yAt)}
            className={TONE[s.tone]}
            stroke="currentColor"
            strokeWidth={chart.series.length > 6 ? 1 : 1.8}
            strokeOpacity={chart.series.length > 6 ? 0.55 : 1}
            strokeDasharray={s.style === 'dashed' ? '5 3' : undefined}
            fill="none"
          />
        ))}

      {chart.segments.map((seg, i) => {
        const midX = (xAt(seg.x0) + xAt(seg.x1)) / 2;
        const midY = (yAt(seg.y0) + yAt(seg.y1)) / 2;
        return (
          <g key={`seg${i}`} className={TONE[seg.tone]}>
            <line
              x1={xAt(seg.x0)}
              x2={xAt(seg.x1)}
              y1={yAt(seg.y0)}
              y2={yAt(seg.y1)}
              stroke="currentColor"
              strokeWidth={1.6}
            />
            {seg.label && (
              <text
                x={clampLabelX(midX)}
                y={midY - 6}
                textAnchor="middle"
                fontSize={10.5}
                fill="currentColor"
                fontWeight={600}
              >
                {seg.label}
              </text>
            )}
          </g>
        );
      })}

      {chart.marks.map((mark, i) => {
        const x = xAt(mark.x);
        const y = yAt(mark.y);
        const below = mark.shape === 'up';
        return (
          <g key={`m${i}`} className={TONE[mark.tone]}>
            {mark.shape === 'dot' && <circle cx={x} cy={y} r={3.2} fill="currentColor" />}
            {mark.shape === 'up' && (
              <polygon points={`${x},${y + 4} ${x - 5},${y + 13} ${x + 5},${y + 13}`} fill="currentColor" />
            )}
            {mark.shape === 'down' && (
              <polygon points={`${x},${y - 4} ${x - 5},${y - 13} ${x + 5},${y - 13}`} fill="currentColor" />
            )}
            {mark.label && (
              <text
                x={clampLabelX(x)}
                y={below ? y + 25 : y - (mark.shape === 'down' ? 18 : 8)}
                textAnchor="middle"
                fontSize={10.5}
                fill="currentColor"
                fontWeight={600}
              >
                {mark.label}
              </text>
            )}
          </g>
        );
      })}

      {hasLower && (
        <g>
          <text x={MARGIN.left} y={lowerTop - 4} fontSize={10} fill="rgb(var(--mentor-muted))">
            {chart.lower_title}
          </text>
          <Axis
            ticks={niceTicks(lowerMin, lowerMax, 2)}
            scale={lowerYAt}
            x={MARGIN.left}
            right={plotRight}
            format="plain"
          />
          {lowerLines.map((line, i) => (
            <g key={`lh${i}`} className={TONE[line.tone]}>
              <line
                x1={MARGIN.left}
                x2={plotRight}
                y1={lowerYAt(line.y)}
                y2={lowerYAt(line.y)}
                stroke="currentColor"
                strokeDasharray="4 3"
              />
              {line.label && (
                <text x={plotRight - 2} y={lowerYAt(line.y) - 2} textAnchor="end" fontSize={9.5} fill="currentColor">
                  {line.label}
                </text>
              )}
            </g>
          ))}
          {lowerSeries.map((s) =>
            s.style === 'bars' ? (
              <g key={`lb${s.name}`} className={TONE[s.tone]}>
                {s.values.map((v, i) =>
                  v == null ? null : (
                    <rect
                      key={i}
                      x={xAt(i) - candleWidth / 2}
                      width={candleWidth}
                      y={Math.min(lowerYAt(v), lowerYAt(0))}
                      height={Math.max(Math.abs(lowerYAt(v) - lowerYAt(0)), 1)}
                      fill="currentColor"
                      fillOpacity={0.7}
                    />
                  )
                )}
              </g>
            ) : (
              <path
                key={`ls${s.name}`}
                d={linePath(s.values, xAt, lowerYAt)}
                className={TONE[s.tone]}
                stroke="currentColor"
                strokeWidth={1.5}
                strokeDasharray={s.style === 'dashed' ? '4 3' : undefined}
                fill="none"
              />
            )
          )}
        </g>
      )}

      {chart.x_labels.map((label, i) =>
        i % axisStep === 0 || i === chart.x_labels.length - 1 ? (
          <text
            key={`xl${i}`}
            x={xAt(i)}
            y={height - 7}
            textAnchor="middle"
            fontSize={10}
            fill="rgb(var(--mentor-muted))"
          >
            {label}
          </text>
        ) : null
      )}
    </svg>
  );
}

function BarChart({ chart, width }: { chart: BookChartData; width: number }) {
  const hasNegative = chart.bars.some((b) => b.value < 0);
  const maxAbs = Math.max(1e-9, ...chart.bars.map((b) => Math.abs(b.value)));
  const labelWidth = Math.min(Math.max(width * 0.34, 70), 150);
  const valueWidth = 54;
  const rowH = 30;
  const trackStart = labelWidth + 8;
  const trackWidth = Math.max(width - trackStart - valueWidth, 40);
  const zero = hasNegative ? trackStart + trackWidth / 2 : trackStart;
  const scale = (hasNegative ? trackWidth / 2 : trackWidth) / maxAbs;
  const height = chart.bars.length * rowH + 6;
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      role="img"
      aria-label={chart.title}
      className="block"
    >
      {hasNegative && (
        <line x1={zero} x2={zero} y1={0} y2={height} className="text-mentor-border" stroke="currentColor" />
      )}
      {chart.bars.map((bar, i) => {
        const y = i * rowH + 4;
        const barWidth = Math.max(Math.abs(bar.value) * scale, 1);
        const x = bar.value < 0 ? zero - barWidth : zero;
        return (
          <g key={bar.label}>
            <text x={labelWidth} y={y + 15} textAnchor="end" fontSize={11} fill="rgb(var(--mentor-fg))">
              {bar.label}
            </text>
            <rect
              x={x}
              y={y + 2}
              width={barWidth}
              height={rowH - 12}
              rx={3}
              className={TONE[bar.tone]}
              fill="currentColor"
              fillOpacity={0.85}
            />
            <text
              x={bar.value < 0 && hasNegative ? zero - barWidth - 4 : zero + barWidth + 4}
              y={y + 15}
              textAnchor={bar.value < 0 && hasNegative ? 'end' : 'start'}
              fontSize={11}
              fontWeight={600}
              fill="rgb(var(--mentor-fg))"
            >
              {formatValue(bar.value, chart.y_format)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function BookChart({ chart }: { chart: BookChartData }) {
  const { ref, width } = useWidth();
  const legend = chart.series.length > 0 && chart.series.length <= 6 ? chart.series : [];
  const dataKind = DATA_KIND[chart.data_kind];

  return (
    <figure className="my-6 rounded-xl border border-mentor-border bg-mentor-panel p-3 sm:p-4 print:break-inside-avoid">
      <figcaption className="text-sm font-medium text-mentor-fg">{chart.title}</figcaption>
      <div className={`mt-1 inline-block rounded border px-1.5 py-0.5 text-[10.5px] ${dataKind.tone}`}>
        {dataKind.label}
      </div>
      <div ref={ref} className="mt-2 overflow-hidden">
        {chart.kind === 'bars' ? (
          <BarChart chart={chart} width={width} />
        ) : (
          <PriceChart chart={chart} width={width} />
        )}
      </div>
      {legend.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-mentor-muted">
          {legend.map((s) => (
            <span key={s.name} className="inline-flex items-center gap-1.5">
              <span className={`inline-block h-2 w-3 rounded-sm ${TONE[s.tone]}`} style={{ backgroundColor: 'currentColor' }} />
              {s.name}
            </span>
          ))}
        </div>
      )}
      {(chart.y_label || chart.x_label) && (
        <p className="mt-1 text-[11px] text-mentor-muted">
          {chart.y_label}
          {chart.y_label && chart.x_label ? ' · ' : ''}
          {chart.x_label ? `Across: ${chart.x_label}` : ''}
        </p>
      )}
      <p className="mt-2 text-xs leading-relaxed text-mentor-muted">{chart.caption}</p>
      {chart.source_note && (
        <p className="mt-1 text-[11px] text-mentor-muted">Source: {chart.source_note}</p>
      )}
    </figure>
  );
}
