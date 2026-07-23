/**
 * Trade plan — the "what should I do right now" endpoint. Composes the
 * champion's direction read, the volatility-based stop, and position
 * sizing into one actionable (or honestly non-actionable) plan.
 */
import { z } from 'zod';

import { apiGet } from './client';

const decimalStr = z.string();

const levels = z.object({
  entry: decimalStr,
  stop: decimalStr,
  target: decimalStr,
  stop_pips: decimalStr,
  target_pips: decimalStr,
  risk_reward: decimalStr,
});
export type TradePlanLevels = z.infer<typeof levels>;

const size = z.object({
  lots: decimalStr,
  units: decimalStr,
  money_at_risk: decimalStr,
  risk_currency: z.string(),
  pip_value: decimalStr,
  notes: z.array(z.string()),
});
export type TradePlanSize = z.infer<typeof size>;

const management = z.object({
  break_even_price: decimalStr,
  break_even_pips: decimalStr,
  trail_distance_pips: decimalStr,
  partial_close_price: decimalStr,
  partial_close_fraction: decimalStr,
  time_stop_bars: z.number(),
  rules: z.array(z.string()),
});
export type TradeManagement = z.infer<typeof management>;

const realism = z.object({
  stop_sigma: decimalStr,
  target_sigma: decimalStr,
  reward_risk: decimalStr,
  breakeven_win_rate: decimalStr,
  random_walk_hit_rate: decimalStr,
  model_win_rate: decimalStr.nullable(),
  has_edge: z.boolean().nullable(),
  note: z.string(),
});
export type TargetRealism = z.infer<typeof realism>;

const tradePlan = z.object({
  stance: z.enum(['long', 'short', 'stand_aside']),
  headline: z.string(),
  symbol: z.string(),
  timeframe: z.string(),
  horizon_bars: z.number(),
  asof: z.string(),
  model_name: z.string(),
  p_up: decimalStr,
  confidence: decimalStr,
  reasoning: z.string(),
  vol_regime: z.string(),
  expected_move_pips: decimalStr,
  range_low_pips: decimalStr.nullable(),
  range_high_pips: decimalStr.nullable(),
  range_coverage: decimalStr.nullable(),
  vol_percentile: decimalStr,
  event_freeze: z.boolean(),
  levels: levels.nullable(),
  size: size.nullable(),
  management: management.nullable(),
  realism: realism.nullable(),
  data_age_minutes: z.number(),
  data_stale: z.boolean(),
  warnings: z.array(z.string()),
  checklist: z.array(z.string()),
  disclaimer: z.string(),
});
export type TradePlan = z.infer<typeof tradePlan>;

export function fetchTradePlan(params: {
  balance: number;
  riskPercent: number;
  rewardMultiple: number;
}): Promise<TradePlan> {
  const q = new URLSearchParams({
    balance: String(params.balance),
    risk_percent: String(params.riskPercent),
    reward_multiple: String(params.rewardMultiple),
  });
  return apiGet(`/forecasting/trade-plan?${q.toString()}`, tradePlan);
}
