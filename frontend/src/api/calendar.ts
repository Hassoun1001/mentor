import { z } from 'zod';

import { apiGet, apiPost } from './client';

const economicEvent = z.object({
  id: z.string().uuid(),
  source: z.string(),
  ts: z.string(),
  name: z.string(),
  country: z.string(),
  impact: z.number(),
  forecast: z.string().nullable(),
  previous: z.string().nullable(),
  actual: z.string().nullable(),
});
export type EconomicEvent = z.infer<typeof economicEvent>;

const ingestResponse = z.object({
  fetched: z.number(),
  upserted: z.number(),
});
export type CalendarIngestResponse = z.infer<typeof ingestResponse>;

export async function listEvents(opts: {
  hoursBack?: number;
  hoursAhead?: number;
  minImpact?: number;
} = {}): Promise<EconomicEvent[]> {
  const params = new URLSearchParams();
  if (opts.hoursBack !== undefined) params.set('hours_back', String(opts.hoursBack));
  if (opts.hoursAhead !== undefined) params.set('hours_ahead', String(opts.hoursAhead));
  if (opts.minImpact !== undefined) params.set('min_impact', String(opts.minImpact));
  const qs = params.toString();
  return apiGet(qs ? `/calendar?${qs}` : '/calendar', z.array(economicEvent));
}

export async function ingestCalendar(
  hoursBack = 24,
  hoursAhead = 72
): Promise<CalendarIngestResponse> {
  return apiPost(
    '/calendar/ingest',
    { hours_back: hoursBack, hours_ahead: hoursAhead },
    ingestResponse
  );
}
