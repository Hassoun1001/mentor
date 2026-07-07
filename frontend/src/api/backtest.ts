import { z } from 'zod';

import { apiGet, apiPost } from './client';
import { timeframeEnum } from './prices';

const decimalStr = z.string();

const equityPoint = z.object({ ts: z.string(), balance: decimalStr });
export type EquityPoint = z.infer<typeof equityPoint>;

const closedTrade = z.object({
  direction: z.string(),
  size_lots: decimalStr,
  entry_price: decimalStr,
  exit_price: decimalStr,
  entry_ts: z.string(),
  exit_ts: z.string(),
  realised_pnl: decimalStr,
  realised_r: decimalStr,
  costs_paid: decimalStr,
  exit_reason: z.string(),
  reason: z.string(),
});
export type ClosedTrade = z.infer<typeof closedTrade>;

const metrics = z.object({
  total_return_pct: decimalStr,
  max_drawdown_pct: decimalStr,
  max_drawdown_duration_bars: z.number(),
  bars_evaluated: z.number(),
  trade_count: z.number(),
  win_rate_pct: decimalStr,
  expectancy_r: decimalStr,
  profit_factor: decimalStr.nullable(),
  total_costs_paid: decimalStr,
  avg_win_r: decimalStr,
  avg_loss_r: decimalStr,
  largest_win_r: decimalStr,
  largest_loss_r: decimalStr,
  sharpe_like: decimalStr,
  forced_closes: z.number(),
});
export type BacktestMetrics = z.infer<typeof metrics>;

const walkForwardWindow = z.object({
  index: z.number(),
  train_metrics: metrics,
  test_metrics: metrics,
  train_bars: z.number(),
  test_bars: z.number(),
});
export type WalkForwardWindow = z.infer<typeof walkForwardWindow>;

const walkForward = z.object({
  windows: z.array(walkForwardWindow),
  in_sample_avg_expectancy_r: decimalStr,
  out_of_sample_avg_expectancy_r: decimalStr,
  degradation_pct: decimalStr.nullable(),
  is_overfit_signal: z.boolean(),
});
export type WalkForward = z.infer<typeof walkForward>;

const backtestResponse = z.object({
  strategy: z.string(),
  symbol: z.string(),
  starting_balance: decimalStr,
  ending_balance: decimalStr,
  currency: z.string(),
  equity_curve: z.array(equityPoint),
  closed_trades: z.array(closedTrade),
  metrics: metrics,
  walk_forward: walkForward.nullable(),
});
export type BacktestResponse = z.infer<typeof backtestResponse>;

const strategyInfo = z.object({ name: z.string() });
export type StrategyInfo = z.infer<typeof strategyInfo>;

export async function listStrategies(): Promise<StrategyInfo[]> {
  return apiGet('/backtest/strategies', z.array(strategyInfo));
}

export interface BacktestRequest {
  symbol: string;
  timeframe: z.infer<typeof timeframeEnum>;
  start: string;
  end: string;
  strategy: string;
  strategy_params: Record<string, unknown>;
  starting_balance: { amount: string; currency: string };
  risk_per_trade_percent: string;
  cost_model: {
    spread_pips: string;
    slippage_pips: string;
    commission_per_lot_round_trip: string;
  };
  do_walk_forward: boolean;
  walk_forward_windows: number;
}

export async function runBacktest(body: BacktestRequest): Promise<BacktestResponse> {
  return apiPost('/backtest', body, backtestResponse);
}

// ---------- compare (strategies side by side, same window) ----------

const compareEntry = z.object({
  strategy: z.string(),
  label: z.string(),
  ending_balance: decimalStr,
  equity_curve: z.array(equityPoint),
  metrics,
});
export type CompareEntry = z.infer<typeof compareEntry>;

const compareResponse = z.object({
  symbol: z.string(),
  currency: z.string(),
  starting_balance: decimalStr,
  entries: z.array(compareEntry),
});
export type CompareResponse = z.infer<typeof compareResponse>;

export interface CompareRequest {
  symbol: string;
  timeframe: z.infer<typeof timeframeEnum>;
  start: string;
  end: string;
  strategies: { strategy: string; strategy_params: Record<string, unknown>; label?: string }[];
  starting_balance: { amount: string; currency: string };
  risk_per_trade_percent: string;
  cost_model: {
    spread_pips: string;
    slippage_pips: string;
    commission_per_lot_round_trip: string;
  };
}

export async function compareStrategies(body: CompareRequest): Promise<CompareResponse> {
  return apiPost('/backtest/compare', body, compareResponse);
}
