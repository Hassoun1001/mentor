/**
 * Strategy lab API: every trading idea the system has tested, its verdict on
 * history, and — for the few that pass — its paper-trading record.
 * Read-only: evaluation and paper trading run on the server's schedule.
 */
import { z } from 'zod';

import { apiGet } from './client';

const num = z.number();
const maybeNum = z.number().nullable();

const position = z.object({
  status: z.string(),
  direction: z.string(),
  reason: z.string(),
  signal_ts: z.string(),
  entry_ts: z.string().nullable(),
  entry_price: maybeNum,
  stop_price: num,
  target_price: maybeNum,
  suggested_lots: maybeNum,
  bars_held: num,
  exit_ts: z.string().nullable(),
  exit_price: maybeNum,
  exit_reason: z.string().nullable(),
  realised_r: maybeNum,
  note: z.string().nullable(),
});
export type PaperPosition = z.infer<typeof position>;

const tradeStats = z.object({
  n: num,
  mean_r: num,
  sd_r: num.optional(),
  win_rate: maybeNum,
  breakeven_win_rate: maybeNum,
  score: num.optional(),
  ci_low: num.optional(),
  ci_high: num.optional(),
});
export type TradeStats = z.infer<typeof tradeStats>;

const fold = z.object({
  index: num,
  test_start: z.string(),
  test_end: z.string(),
  trades: num,
  mean_r: maybeNum,
});

// Evidence is written by the server's gate; unknown extra keys are tolerated.
const evidence = z
  .object({
    passed: z.boolean().optional(),
    reasons: z.array(z.string()).optional(),
    grid_size: num.optional(),
    n_trials: num.optional(),
    bar: num.optional(),
    score: num.optional(),
    probability: num.optional(),
    in_sample_mean_r: maybeNum.optional(),
    out_of_sample: tradeStats.optional(),
    holdout: tradeStats.optional(),
    folds: z.array(fold).optional(),
    data: z
      .object({
        start: z.string().nullable(),
        holdout_start: z.string().nullable(),
        end: z.string().nullable(),
        bars: num,
      })
      .optional(),
  })
  .passthrough();
export type LabEvidence = z.infer<typeof evidence>;

const paperRecord = z.object({
  trades: num,
  mean_r: maybeNum,
  win_rate: maybeNum,
  breakeven_win_rate: maybeNum,
  ci_low: maybeNum,
  ci_high: maybeNum,
  verdict: z.string(),
  next_check_at: num,
  open_position: position.nullable(),
  pending_order: position.nullable(),
  last_bar_ts: z.string().nullable(),
});
export type PaperRecord = z.infer<typeof paperRecord>;

const candidate = z.object({
  key: z.string(),
  title: z.string(),
  family: z.string(),
  timeframe: z.string(),
  hypothesis: z.string(),
  status: z.enum(['rejected', 'paper', 'recommended', 'demoted', 'retired']),
  status_reason: z.string(),
  evaluated_at: z.string(),
  n_trials_at_evaluation: num,
  plan: z
    .object({ config_key: z.string(), plan: z.string() })
    .passthrough()
    .nullable(),
  evidence,
  clears_todays_bar: z.boolean(),
  paper_started_at: z.string().nullable(),
  promoted_at: z.string().nullable(),
  demoted_at: z.string().nullable(),
  retired_at: z.string().nullable(),
  paper: paperRecord.nullable(),
});
export type LabCandidate = z.infer<typeof candidate>;
export type LabStatus = LabCandidate['status'];

const lab = z.object({
  trials_ever: num,
  dispersion: num,
  bar_now: num,
  paper_account: z.string(),
  counts: z.object({
    evaluated: num,
    passed_backtest: num,
    paper: num,
    recommended: num,
    retired: num,
  }),
  candidates: z.array(candidate),
  waiting: z.array(z.string()),
  changed: z.array(z.string()),
  events_week: z.array(
    z.object({ key: z.string(), kind: z.string(), at: z.string(), detail: z.string() })
  ),
});
export type StrategyLab = z.infer<typeof lab>;

const positions = z.object({ key: z.string(), positions: z.array(position) });

export function fetchStrategyLab(): Promise<StrategyLab> {
  return apiGet('/strategy-lab', lab);
}

export async function fetchPaperPositions(key: string): Promise<PaperPosition[]> {
  const res = await apiGet(`/strategy-lab/${encodeURIComponent(key)}/positions`, positions);
  return res.positions;
}
