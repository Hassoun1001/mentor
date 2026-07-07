import { z } from 'zod';

import { apiGet, apiPost } from './client';

const decimalStr = z.string();

const ingestedTip = z.object({
  ticker: z.string(),
  category: z.string(),
  action: z.string(),
  conviction: z.string(),
  mention_price: decimalStr.nullable(),
});

const ingestResponse = z.object({
  tipster: z.string(),
  parsed: z.number(),
  priced: z.number(),
  unpriced_tickers: z.array(z.string()),
  tips: z.array(ingestedTip),
});
export type IngestTipsResponse = z.infer<typeof ingestResponse>;

export async function ingestTips(body: {
  tipster: string;
  text: string;
}): Promise<IngestTipsResponse> {
  return apiPost('/tips/ingest', body, ingestResponse);
}

const outcome = z.object({
  ticker: z.string(),
  category: z.string(),
  action: z.string(),
  conviction: z.string(),
  note: z.string(),
  days_held: z.number(),
  mention_price: decimalStr,
  current_price: decimalStr,
  return_pct: decimalStr,
  max_drawup_pct: decimalStr,
  max_drawdown_pct: decimalStr,
  dipped: z.boolean().nullable(),
  expected_move_pct: decimalStr.nullable(),
  vol_regime: z.enum(['calm', 'normal', 'wide']).nullable(),
  at_or_below_entry: z.boolean(),
  daily_change_pct: decimalStr.nullable(),
});
export type TipOutcome = z.infer<typeof outcome>;

const bucket = z.object({
  key: z.string(),
  count: z.number(),
  mean_return_pct: decimalStr,
  win_rate: decimalStr,
  avg_days_held: decimalStr,
  best_ticker: z.string().nullable(),
  best_return_pct: decimalStr,
  worst_ticker: z.string().nullable(),
  worst_return_pct: decimalStr,
});
export type Bucket = z.infer<typeof bucket>;

const scorecard = z.object({
  tipster: z.string(),
  total: z.number(),
  overall: bucket,
  by_category: z.array(bucket),
  by_action: z.array(bucket),
  dip_accuracy: decimalStr.nullable(),
  headline: z.string(),
});
export type Scorecard = z.infer<typeof scorecard>;

const scoredResponse = z.object({
  tipster: z.string(),
  scorecard,
  outcomes: z.array(outcome),
  unpriced: z.array(z.string()),
});
export type ScoredResponse = z.infer<typeof scoredResponse>;

export async function getScored(tipster?: string): Promise<ScoredResponse> {
  const q = tipster ? `?tipster=${encodeURIComponent(tipster)}` : '';
  return apiGet(`/tips/scored${q}`, scoredResponse);
}

export async function getTipsters(): Promise<string[]> {
  return apiGet('/tips/tipsters', z.array(z.string()));
}

// ---------- leaderboard ----------

const leaderboardRow = z.object({
  tipster: z.string(),
  tracked_calls: z.number(),
  mean_return_pct: decimalStr,
  win_rate: decimalStr,
  return_stdev: decimalStr,
  risk_adjusted: decimalStr,
  best_ticker: z.string().nullable(),
  best_return_pct: decimalStr,
  avg_days_held: decimalStr,
});
export type LeaderboardRow = z.infer<typeof leaderboardRow>;

export async function getLeaderboard(): Promise<LeaderboardRow[]> {
  return apiGet('/tips/leaderboard', z.array(leaderboardRow));
}

// ---------- "follow him" backtest ----------

const followTrade = z.object({
  ticker: z.string(),
  mentioned_at: z.string(),
  entry_price: decimalStr,
  exit_fill: decimalStr,
  stop_price: decimalStr,
  shares: decimalStr,
  risk_amount: decimalStr,
  pnl: decimalStr,
  r_multiple: decimalStr,
  return_pct: decimalStr,
  days_held: z.number(),
  stopped_out: z.boolean(),
  won: z.boolean(),
});
export type FollowTrade = z.infer<typeof followTrade>;

const equityPoint = z.object({
  label: z.string(),
  at: z.string(),
  equity: decimalStr,
});

const backtestResponse = z.object({
  tipster: z.string(),
  starting_equity: decimalStr,
  ending_equity: decimalStr,
  risk_pct: decimalStr,
  stop_pct: decimalStr,
  apply_stop: z.boolean(),
  n_trades: z.number(),
  total_return_pct: decimalStr,
  max_drawdown_pct: decimalStr,
  expectancy_r: decimalStr,
  win_rate: decimalStr,
  avg_days_held: decimalStr,
  equity_curve: z.array(equityPoint),
  trades: z.array(followTrade),
  headline: z.string(),
  disclaimer: z.string(),
});
export type BacktestResponse = z.infer<typeof backtestResponse>;

export async function runFollowBacktest(body: {
  tipster: string;
  risk_pct?: number;
  stop_pct?: number;
  apply_stop?: boolean;
}): Promise<BacktestResponse> {
  return apiPost('/tips/backtest', body, backtestResponse);
}

// ---------- analyst coverage ----------

const analystRating = z.object({
  firm: z.string(),
  rating: z.string(),
  action: z.string(),
  date: z.string(),
});
export type AnalystRating = z.infer<typeof analystRating>;

const analystConsensus = z.object({
  target_mean: decimalStr.nullable(),
  target_high: decimalStr.nullable(),
  target_low: decimalStr.nullable(),
  upside_pct: decimalStr.nullable(),
  rating_key: z.string().nullable(),
  num_analysts: z.number().nullable(),
  strong_buy: z.number(),
  buy: z.number(),
  hold: z.number(),
  sell: z.number(),
  strong_sell: z.number(),
});

const analystSnapshot = z.object({
  ticker: z.string(),
  available: z.boolean(),
  current_price: decimalStr.nullable(),
  consensus: analystConsensus.nullable(),
  ratings: z.array(analystRating),
  note: z.string(),
});
export type AnalystSnapshot = z.infer<typeof analystSnapshot>;

export async function getAnalyst(ticker: string): Promise<AnalystSnapshot> {
  return apiGet(`/tips/analyst/${encodeURIComponent(ticker)}`, analystSnapshot);
}
