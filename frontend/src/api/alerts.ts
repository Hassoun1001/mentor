import { z } from 'zod';

import { apiGet, apiPost } from './client';

const kind = z.enum(['price_above', 'price_below', 'signal_change', 'event_freeze']);
const status = z.enum(['armed', 'fired', 'disabled']);

const alert = z.object({
  id: z.string().uuid(),
  kind,
  label: z.string(),
  status,
  symbol: z.string().nullable(),
  price_level: z.string().nullable(),
  created_at: z.string(),
  fired_at: z.string().nullable(),
});
export type Alert = z.infer<typeof alert>;

const eventFreeze = z.object({
  triggered: z.boolean(),
  upcoming_count: z.number(),
  soft: z.boolean(),
  blocking_reason: z.string().nullable(),
  label: z.string(),
});
export type EventFreeze = z.infer<typeof eventFreeze>;

export async function listAlerts(): Promise<Alert[]> {
  return apiGet('/alerts', z.array(alert));
}

export async function createPriceAlert(body: {
  symbol: string;
  kind: 'price_above' | 'price_below';
  price_level: string;
  label: string;
}): Promise<Alert> {
  return apiPost('/alerts', body, alert);
}

export async function sweepAlerts(): Promise<{ evaluated: number; fired: number }> {
  return apiPost(
    '/alerts/sweep',
    {},
    z.object({ evaluated: z.number(), fired: z.number() })
  );
}

export async function getEventFreeze(): Promise<EventFreeze> {
  return apiGet('/alerts/event-freeze', eventFreeze);
}
