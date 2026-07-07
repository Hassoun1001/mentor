import { z } from 'zod';

import { apiGet, apiPost } from './client';

const macroPoint = z.object({
  series_id: z.string(),
  day: z.string(),
  value: z.string(),
});
export type MacroPoint = z.infer<typeof macroPoint>;

export async function fetchMacroSeries(limitPerSeries = 10): Promise<MacroPoint[]> {
  return apiGet(`/macro/series?limit_per_series=${limitPerSeries}`, z.array(macroPoint));
}

const macroIngestResponse = z.object({
  series_ids: z.array(z.string()),
  observations_fetched: z.number(),
  rows_written: z.number(),
  counts_by_series: z.record(z.string(), z.number()),
});
export type MacroIngestResponse = z.infer<typeof macroIngestResponse>;

export async function ingestMacro(daysBack = 3650): Promise<MacroIngestResponse> {
  return apiPost('/macro/ingest', { days_back: daysBack }, macroIngestResponse);
}
