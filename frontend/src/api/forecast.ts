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
  features: featureMap,
});
export type AuditPrediction = z.infer<typeof auditPrediction>;

export async function listAuditLog(limit = 50): Promise<AuditPrediction[]> {
  return apiGet(`/forecasting/audit?limit=${limit}`, z.array(auditPrediction));
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
