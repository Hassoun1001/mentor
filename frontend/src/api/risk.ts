import { z } from 'zod';

import { apiGet, apiPost } from './client';

// Decimals come over the wire as JSON strings to avoid float noise.
const decimalStr = z.string();

const moneyDTO = z.object({
  amount: decimalStr,
  currency: z.string(),
});

const instrumentDTO = z.object({
  symbol: z.string(),
  base: z.string(),
  quote: z.string(),
  pip_size: decimalStr,
  contract_size: decimalStr,
  min_lot: decimalStr,
  lot_step: decimalStr,
});
export type InstrumentDTO = z.infer<typeof instrumentDTO>;

export async function listInstruments(): Promise<InstrumentDTO[]> {
  return apiGet('/risk/instruments', z.array(instrumentDTO));
}

// ---------- position size ----------

export const directionEnum = z.enum(['long', 'short']);
export type Direction = z.infer<typeof directionEnum>;

const positionSizeResponse = z.object({
  symbol: z.string(),
  direction: directionEnum,
  lots: decimalStr,
  units: decimalStr,
  pip_distance: decimalStr,
  pip_value_in_account: moneyDTO,
  money_at_risk: moneyDTO,
  risk_pct_of_account: decimalStr,
  risk_reward_ratio: decimalStr.nullable(),
  notional_in_quote: decimalStr,
  raw_lots_before_rounding: decimalStr,
  is_aggressive: z.boolean(),
  notes: z.array(z.string()),
});
export type PositionSizeResponse = z.infer<typeof positionSizeResponse>;

export interface PositionSizeRequest {
  symbol: string;
  account: { amount: string; currency: string };
  risk_percent: string;
  direction: Direction;
  entry: string;
  stop: string;
  target?: string | null;
  quote_to_account_rate?: string;
}

export async function calculatePositionSize(
  body: PositionSizeRequest
): Promise<PositionSizeResponse> {
  return apiPost('/risk/position-size', body, positionSizeResponse);
}

// ---------- expectancy ----------

const expectancyResponse = z.object({
  expected_value_r: decimalStr,
  profit_factor: decimalStr.nullable(),
  is_positive: z.boolean(),
  interpretation: z.string(),
});
export type ExpectancyResponse = z.infer<typeof expectancyResponse>;

export interface ExpectancyRequest {
  win_rate_percent: string;
  avg_win_r: string;
  avg_loss_r: string;
  sample_size?: number;
}

export async function calculateExpectancy(body: ExpectancyRequest): Promise<ExpectancyResponse> {
  return apiPost('/risk/expectancy', body, expectancyResponse);
}
