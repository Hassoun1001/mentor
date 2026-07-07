import { z } from 'zod';

import { apiGet, apiPost } from './client';
import { timeframeEnum } from './prices';

const decimalStr = z.string();
const direction = z.enum(['long', 'short', 'neutral']);

const featureMap = z.record(z.string(), decimalStr);

const predictResponse = z.object({
  prediction_id: z.string().uuid(),
  symbol: z.string(),
  timeframe: timeframeEnum,
  asof: z.string(),
  asof_close: decimalStr,
  horizon_bars: z.number(),
  p_up: decimalStr,
  confidence: decimalStr,
  direction,
  model_name: z.string(),
  reasoning: z.string(),
  features: featureMap,
});
export type PredictResponse = z.infer<typeof predictResponse>;

const snapshotResponse = z.object({
  forecast: predictResponse,
  horizon_at: z.string(),
});
export type SnapshotResponse = z.infer<typeof snapshotResponse>;

export interface SnapshotRequest {
  symbol: string;
  timeframe: z.infer<typeof timeframeEnum>;
  model_name?: string;
  horizon_bars?: number;
}

export async function fetchForecastSnapshot(body: SnapshotRequest): Promise<SnapshotResponse> {
  return apiPost(
    '/forecasting/snapshot',
    { model_name: 'baseline', horizon_bars: 24, ...body },
    snapshotResponse
  );
}

// ---------- volatility (predict the range, not the arrow) ----------

const volRegime = z.enum(['calm', 'normal', 'wide']);

const volForecast = z.object({
  symbol: z.string(),
  timeframe: timeframeEnum,
  asof: z.string(),
  asof_close: decimalStr,
  horizon_bars: z.number(),
  expected_vol: decimalStr,
  expected_range_pips: decimalStr,
  percentile_vs_history: decimalStr,
  regime: volRegime,
  model_name: z.string(),
  reasoning: z.string(),
  range_low_pips: decimalStr.nullable().optional(),
  range_high_pips: decimalStr.nullable().optional(),
  coverage: decimalStr.nullable().optional(),
});
export type VolForecast = z.infer<typeof volForecast>;

const volEval = z.object({
  n_test: z.number(),
  ml_mae: z.number(),
  ewma_mae: z.number(),
  ml_qlike: z.number(),
  ewma_qlike: z.number(),
  ml_r2: z.number(),
  r2_vs_ewma: z.number(),
  beats_ewma: z.boolean(),
  verdict: z.string(),
  feature_importances: z.record(z.string(), z.number()),
});
export type VolEval = z.infer<typeof volEval>;

const volGuidance = z.object({
  suggested_stop_pips: decimalStr,
  event_freeze: z.boolean(),
  rationale: z.string(),
});
export type VolGuidance = z.infer<typeof volGuidance>;

const volResponse = z.object({
  forecast: volForecast,
  baseline: volForecast,
  guidance: volGuidance,
  eval: volEval.nullable(),
});
export type VolResponse = z.infer<typeof volResponse>;

export async function fetchVolatility(body: {
  symbol: string;
  timeframe: z.infer<typeof timeframeEnum>;
  horizon_bars: number;
  model?: 'ewma' | 'ml';
}): Promise<VolResponse> {
  return apiPost('/forecasting/volatility', { model: 'ewma', ...body }, volResponse);
}

const trainReport = z.object({
  name: z.string(),
  horizon_bars: z.number(),
  n_samples: z.number(),
  n_train: z.number(),
  n_test: z.number(),
  train_accuracy: z.number(),
  test_accuracy: z.number(),
  test_log_loss: z.number(),
  test_brier: z.number(),
  feature_importances: z.record(z.string(), z.number()),
  ece: z.number(),
  ece_uncalibrated: z.number(),
  test_brier_uncalibrated: z.number(),
  calibration_applied: z.boolean(),
  n_calibration: z.number(),
});
export type TrainReport = z.infer<typeof trainReport>;

export async function listModels(): Promise<TrainReport[]> {
  return apiGet('/forecasting/models', z.array(trainReport));
}

export async function trainModel(body: {
  symbol: string;
  timeframe: z.infer<typeof timeframeEnum>;
  start: string;
  end: string;
  horizon_bars: number;
  model_name: string;
}): Promise<TrainReport> {
  return apiPost('/forecasting/train', body, trainReport);
}

const auditPrediction = z.object({
  id: z.string().uuid(),
  symbol: z.string(),
  timeframe: timeframeEnum,
  asof: z.string(),
  horizon_at: z.string(),
  model_name: z.string(),
  p_up: decimalStr,
  confidence: decimalStr,
  direction,
  reasoning: z.string(),
  asof_close: decimalStr,
  realised_close: decimalStr.nullable(),
  realised_outcome: z.number().nullable(),
  correct: z.boolean().nullable(),
  features: featureMap,
});
export type AuditPrediction = z.infer<typeof auditPrediction>;

export async function listAuditLog(limit = 100): Promise<AuditPrediction[]> {
  return apiGet(`/forecasting/audit?limit=${limit}`, z.array(auditPrediction));
}

// ---------- autonomous loop ----------

const replayResponse = z.object({
  symbol: z.string(),
  timeframe: timeframeEnum,
  model_name: z.string(),
  points_evaluated: z.number(),
  predictions_written: z.number(),
  skipped_existing: z.number(),
});
export type ReplayResponse = z.infer<typeof replayResponse>;

export async function replayPredictions(body: {
  symbol: string;
  timeframe: '1m' | '5m' | '1h' | '1d';
  model_name: string;
  horizon_bars: number;
  max_points: number;
}): Promise<ReplayResponse> {
  return apiPost('/forecasting/replay', body, replayResponse);
}

const cycleResponse = z.object({
  predicted: z.boolean(),
  prediction_id: z.string().nullable(),
  resolved: z.number(),
  note: z.string(),
});
export type CycleResponse = z.infer<typeof cycleResponse>;

export async function runLoopOnce(): Promise<CycleResponse> {
  return apiPost('/forecasting/loop/run-once', {}, cycleResponse);
}

export async function retrainPromote(): Promise<{ result: string }> {
  return apiPost('/forecasting/loop/retrain', {}, z.object({ result: z.string() }));
}

const loopStatus = z.object({
  enabled: z.boolean(),
  running: z.boolean(),
  symbol: z.string(),
  timeframe: z.string(),
  horizon_bars: z.number(),
  champion: z.string(),
  jobs: z.array(z.object({ id: z.string(), next_run: z.string().nullable() })),
});
export type LoopStatus = z.infer<typeof loopStatus>;

export async function getLoopStatus(): Promise<LoopStatus> {
  return apiGet('/forecasting/loop/status', loopStatus);
}

const postMortem = z.object({
  sample_size: z.number(),
  directional: z.number(),
  neutral: z.number(),
  hits: z.number(),
  misses: z.number(),
  directional_accuracy: z.number(),
  avg_confidence_on_hits: z.number(),
  avg_confidence_on_misses: z.number(),
  brier_score: z.number(),
  ece: z.number(),
  headline: z.string(),
  feature_contrasts: z.array(
    z.object({
      feature: z.string(),
      mean_on_hits: z.number(),
      mean_on_misses: z.number(),
      gap: z.number(),
    })
  ),
  calibration: z.array(
    z.object({
      bucket: z.string(),
      stated_midpoint: z.number(),
      realised_hit_rate: z.number(),
      samples: z.number(),
    })
  ),
});
export type PostMortem = z.infer<typeof postMortem>;

export async function getPostMortem(): Promise<PostMortem> {
  return apiGet('/forecasting/postmortem', postMortem);
}

const resolverResponse = z.object({
  examined: z.number(),
  resolved: z.number(),
  still_pending: z.number(),
});
export type ResolverResponse = z.infer<typeof resolverResponse>;

export async function resolveAudit(): Promise<ResolverResponse> {
  return apiPost('/forecasting/audit/resolve', {}, resolverResponse);
}

const calibrationBucket = z.object({
  bucket: z.string(),
  samples: z.number(),
  hit_rate: z.number(),
});
export type CalibrationBucket = z.infer<typeof calibrationBucket>;

export async function calibrationSummary(): Promise<CalibrationBucket[]> {
  return apiGet('/forecasting/audit/calibration', z.array(calibrationBucket));
}
