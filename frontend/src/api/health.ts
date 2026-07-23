import { z } from 'zod';

import { apiGet } from './client';

const integration = z.object({
  key: z.string(),
  label: z.string(),
  configured: z.boolean(),
  env_var: z.string(),
  why: z.string(),
});
export type Integration = z.infer<typeof integration>;

const integrations = z.object({ integrations: z.array(integration) });

/**
 * Which optional data sources are configured.
 *
 * The UI needs this to distinguish "nothing happened in this window" from
 * "this has never been able to run" — otherwise an empty panel invites the
 * user to press a Refresh button that can only fail.
 */
export async function getIntegrations(): Promise<Integration[]> {
  const r = await apiGet('/health/integrations', integrations);
  return r.integrations;
}
