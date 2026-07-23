import { z } from 'zod';

import { apiGet, apiPost } from './client';

const decimalStr = z.string();

export const timeframeEnum = z.enum(['1m', '5m', '1h', '1d']);
export type Timeframe = z.infer<typeof timeframeEnum>;

const barSchema = z.object({
  ts: z.string(),
  open: decimalStr,
  high: decimalStr,
  low: decimalStr,
  close: decimalStr,
  volume: decimalStr.nullable(),
  source: z.string(),
});
export type Bar = z.infer<typeof barSchema>;

const gapSchema = z.object({
  expected_after: z.string(),
  next_seen: z.string(),
  missing_bars: z.number(),
});
export type Gap = z.infer<typeof gapSchema>;

const pricesSchema = z.object({
  symbol: z.string(),
  timeframe: timeframeEnum,
  bars: z.array(barSchema),
  gaps: z.array(gapSchema),
  last_seen_at: z.string().nullable(),
});
export type PricesResponse = z.infer<typeof pricesSchema>;

export async function getPrices(opts: {
  symbol: string;
  timeframe: Timeframe;
  start?: string;
  end?: string;
}): Promise<PricesResponse> {
  const params = new URLSearchParams({ timeframe: opts.timeframe });
  if (opts.start) params.set('start', opts.start);
  if (opts.end) params.set('end', opts.end);
  return apiGet(
    `/prices/${encodeURIComponent(opts.symbol)}?${params.toString()}`,
    pricesSchema
  );
}

// ---------- data health: coverage, cross-source, ingest ----------

const coverageRow = z.object({
  timeframe: z.string(),
  bars: z.number(),
  first_ts: z.string().nullable(),
  last_ts: z.string().nullable(),
  sources: z.record(z.string(), z.number()),
  future_bars: z.number(),
  newest_is_forming: z.boolean(),
});
export type CoverageRow = z.infer<typeof coverageRow>;

const coverageSchema = z.object({
  symbol: z.string(),
  coverage: z.array(coverageRow),
});
export type CoverageResponse = z.infer<typeof coverageSchema>;

export async function getCoverage(symbol: string): Promise<CoverageResponse> {
  return apiGet(`/prices/${encodeURIComponent(symbol)}/coverage`, coverageSchema);
}

const crossSourceSchema = z.object({
  symbol: z.string(),
  timeframe: timeframeEnum,
  source_a: z.string(),
  source_b: z.string(),
  bars_a: z.number(),
  bars_b: z.number(),
  overlapping: z.number(),
  max_abs_diff: decimalStr,
  mean_abs_diff: decimalStr,
  max_diff_pips: z.number(),
  mean_diff_pips: z.number(),
  agree: z.boolean(),
});
export type CrossSourceResponse = z.infer<typeof crossSourceSchema>;

export async function getCrossSource(
  symbol: string,
  timeframe: Timeframe = '1d',
  daysBack = 45
): Promise<CrossSourceResponse> {
  return apiGet(
    `/prices/${encodeURIComponent(symbol)}/cross-source?timeframe=${timeframe}&days_back=${daysBack}`,
    crossSourceSchema
  );
}

const ingestSchema = z.object({
  symbol: z.string(),
  timeframe: timeframeEnum,
  source: z.string(),
  fetched: z.number(),
  persisted: z.number(),
});
export type IngestResponse = z.infer<typeof ingestSchema>;

export async function ingestPrices(
  symbol: string,
  body: { timeframe: Timeframe; days_back: number; source: 'failover' | 'twelve_data' | 'yahoo' }
): Promise<IngestResponse> {
  return apiPost(`/prices/${encodeURIComponent(symbol)}/ingest`, body, ingestSchema);
}
