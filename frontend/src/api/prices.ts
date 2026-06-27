import { z } from 'zod';

import { apiGet } from './client';

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
