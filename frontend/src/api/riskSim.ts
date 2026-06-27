import { z } from 'zod';

import { apiPost } from './client';

const monteCarloResponse = z.object({
  n_runs: z.number(),
  n_trades: z.number(),
  sample_size: z.number(),
  risk_per_trade_pct: z.string(),
  starting_balance: z.string(),
  ruin_threshold: z.string(),
  probability_of_ruin: z.string(),
  median_terminal: z.string(),
  p5_terminal: z.string(),
  p95_terminal: z.string(),
  median_max_drawdown_pct: z.string(),
  p95_max_drawdown_pct: z.string(),
  expected_terminal: z.string(),
  used_journal: z.boolean(),
});
export type MonteCarloResponse = z.infer<typeof monteCarloResponse>;

export interface MonteCarloRequest {
  starting_balance: string;
  risk_per_trade_percent: string;
  n_trades: number;
  n_runs: number;
  ruin_fraction: string;
  use_journal: boolean;
  fallback_distribution?: string[];
}

export async function runMonteCarlo(body: MonteCarloRequest): Promise<MonteCarloResponse> {
  return apiPost('/risk/monte-carlo', body, monteCarloResponse);
}
