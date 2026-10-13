/**
 * Autonomous-loop observability API: status + heartbeats, the promotions
 * audit trail, and the paper-trading scoreboard of the loop's own signals.
 */
import { z } from 'zod';

import { apiGet } from './client';

const loopJob = z.object({ id: z.string(), next_run: z.string().nullable() });

const heartbeat = z.object({
  job: z.string(),
  at: z.string(),
  ok: z.boolean(),
  note: z.string(),
});
export type Heartbeat = z.infer<typeof heartbeat>;

const loopEvent = z.object({
  kind: z.string(),
  at: z.string(),
  detail: z.string(),
});
export type LoopEvent = z.infer<typeof loopEvent>;

const loopStatus = z.object({
  enabled: z.boolean(),
  running: z.boolean(),
  symbol: z.string(),
  timeframe: z.string(),
  horizon_bars: z.number(),
  champion: z.string(),
  champion_d1: z.string(),
  jobs: z.array(loopJob),
  heartbeats: z.array(heartbeat),
  events: z.array(loopEvent),
  alerts_enabled: z.boolean(),
});
export type LoopStatus = z.infer<typeof loopStatus>;

export function fetchLoopStatus(): Promise<LoopStatus> {
  return apiGet('/forecasting/loop/status', loopStatus);
}

const promotionEntry = z.object({
  at: z.string(),
  promoted: z.boolean(),
  challenger: z.string(),
  family: z.string(),
  challenger_brier: z.number(),
  champion: z.string().nullable(),
  champion_brier: z.number().nullable(),
  champion_brier_fresh: z.number().nullable(),
  candidates: z.record(z.string(), z.number()),
  reason: z.string(),
});
export type PromotionEntry = z.infer<typeof promotionEntry>;

export function fetchLoopPromotions(): Promise<PromotionEntry[]> {
  return apiGet('/forecasting/loop/promotions', z.array(promotionEntry));
}

const paperPoint = z.object({ ts: z.string(), equity: z.number() });
export type PaperPoint = z.infer<typeof paperPoint>;

const paperReport = z.object({
  trades: z.number(),
  skipped_low_confidence: z.number(),
  skipped_neutral: z.number(),
  wins: z.number(),
  losses: z.number(),
  win_rate: z.number(),
  total_return_pct: z.number(),
  max_drawdown_pct: z.number(),
  avg_trade_pct: z.number(),
  curve: z.array(paperPoint),
  note: z.string(),
  verdict: z.string(),
  win_rate_low: z.number(),
  win_rate_high: z.number(),
  significant: z.boolean(),
  trades_needed: z.number().nullable(),
  independent_trades: z.number(),
  independent_win_rate: z.number(),
  // The rate a call must clear to pay for itself on this lane. The verdict
  // above is graded against this, not 50% — a 51% model beats a coin and
  // still loses money.
  breakeven: z.number(),
  breakeven_measured: z.boolean(),
  breakeven_note: z.string(),
});
export type PaperReport = z.infer<typeof paperReport>;

export function fetchLoopPaper(minConfidence: number): Promise<PaperReport> {
  return apiGet(`/forecasting/loop/paper?min_confidence=${minConfidence}`, paperReport);
}

// ---------- abstention policy ----------

const loopPolicy = z.object({
  model_name: z.string(),
  abstains: z.boolean(),
  abstain_margin: z.number(),
  coverage: z.number(),
  n_covered: z.number(),
  n_test: z.number(),
  brier_all: z.number(),
  brier_covered: z.number(),
  accuracy_covered: z.number(),
  explanation: z.string(),
});
export type LoopPolicy = z.infer<typeof loopPolicy>;

export async function getLoopPolicy(): Promise<LoopPolicy> {
  return apiGet('/forecasting/loop/policy', loopPolicy);
}

// ---------- live recalibration ----------

const calibrationBucket = z.object({
  bucket: z.string(),
  stated_midpoint: z.number(),
  realised_hit_rate: z.number(),
  samples: z.number(),
});
export type CalibrationBucketEntry = z.infer<typeof calibrationBucket>;

const liveCalibration = z.object({
  model_name: z.string(),
  promoted_at: z.string().nullable(),
  // Counted on request: how far the champion has got toward a first check.
  independent_outcomes: z.number(),
  required: z.number(),
  // The decision in force, made at the last retrain.
  decided_at: z.string().nullable(),
  decided_on: z.number().nullable(),
  active: z.boolean(),
  slope: z.number(),
  tried_slope: z.number().nullable(),
  n_fit: z.number(),
  n_holdout: z.number(),
  brier_before: z.number().nullable(),
  brier_after: z.number().nullable(),
  gain: z.number().nullable(),
  example_from: z.number(),
  example_to: z.number(),
  reason: z.string(),
  explanation: z.string(),
  buckets: z.array(calibrationBucket),
  buckets_at: z.string().nullable(),
});
export type LiveCalibration = z.infer<typeof liveCalibration>;

export function fetchLiveCalibration(): Promise<LiveCalibration> {
  return apiGet('/forecasting/loop/live-calibration', liveCalibration);
}
