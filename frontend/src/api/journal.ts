import { z } from 'zod';

import { apiGet, apiPost } from './client';

const decimalStr = z.string();
const money = z.object({ amount: decimalStr, currency: z.string() });
const direction = z.enum(['long', 'short']);
const status = z.enum(['planned', 'open', 'closed', 'cancelled']);

export const tradeSchema = z.object({
  id: z.string().uuid(),
  symbol: z.string(),
  direction,
  status,
  size_lots: decimalStr,
  planned_entry: decimalStr,
  planned_stop: decimalStr,
  planned_target: decimalStr.nullable(),
  actual_entry: decimalStr.nullable(),
  actual_exit: decimalStr.nullable(),
  entry_ts: z.string().nullable(),
  exit_ts: z.string().nullable(),
  initial_risk: money,
  realised_pnl: money.nullable(),
  realised_r: decimalStr.nullable(),
  reason: z.string(),
  mistake_tags: z.array(z.string()),
  emotion: z.string().nullable(),
  notes: z.string().nullable(),
});
export type Trade = z.infer<typeof tradeSchema>;

export interface PlanTradeRequest {
  symbol: string;
  direction: 'long' | 'short';
  size_lots: string;
  entry: string;
  stop: string;
  target?: string | null;
  initial_risk: { amount: string; currency: string };
  reason: string;
}

export async function planTrade(body: PlanTradeRequest): Promise<Trade> {
  return apiPost('/trades', body, tradeSchema);
}

export async function listTrades(symbol?: string): Promise<Trade[]> {
  const path = symbol ? `/trades?symbol=${encodeURIComponent(symbol)}` : '/trades';
  return apiGet(path, z.array(tradeSchema));
}

export async function openTrade(id: string, fillPrice: string): Promise<Trade> {
  return apiPost(`/trades/${id}/open`, { fill_price: fillPrice }, tradeSchema);
}

export async function closeTrade(
  id: string,
  exitPrice: string,
  opts: { mistake_tags?: string[]; emotion?: string | null; notes?: string | null } = {}
): Promise<Trade> {
  return apiPost(
    `/trades/${id}/close`,
    { exit_price: exitPrice, ...opts },
    tradeSchema
  );
}

export async function cancelTrade(id: string): Promise<Trade> {
  return apiPost(`/trades/${id}/cancel`, {}, tradeSchema);
}

// ---------- analytics ----------

const analyticsSchema = z.object({
  sample_size: z.number(),
  wins: z.number(),
  losses: z.number(),
  breakeven: z.number(),
  win_rate_percent: decimalStr,
  avg_win_r: decimalStr,
  avg_loss_r: decimalStr,
  expectancy_r: decimalStr,
  profit_factor: decimalStr.nullable(),
  largest_win_r: decimalStr,
  largest_loss_r: decimalStr,
  total_r: decimalStr,
  interpretation: z.string(),
});
export type Analytics = z.infer<typeof analyticsSchema>;

export async function getAnalytics(symbol?: string): Promise<Analytics> {
  const path = symbol
    ? `/journal/analytics?symbol=${encodeURIComponent(symbol)}`
    : '/journal/analytics';
  return apiGet(path, analyticsSchema);
}

// ---------- checklist ----------

const checklistItem = z.object({
  key: z.string(),
  label: z.string(),
  passed: z.boolean(),
  detail: z.string().nullable(),
});
const checklistSchema = z.object({
  passed: z.boolean(),
  items: z.array(checklistItem),
  failed_keys: z.array(z.string()),
});
export type ChecklistResponse = z.infer<typeof checklistSchema>;
export type ChecklistItem = z.infer<typeof checklistItem>;

export interface ChecklistRequest {
  symbol: string;
  direction: 'long' | 'short';
  size_lots: string;
  entry: string;
  stop: string;
  target?: string | null;
  initial_risk_amount: string;
  risk_currency: string;
  reason: string;
  account_balance?: string | null;
  max_risk_per_trade_percent?: string | null;
  max_open_risk_percent?: string | null;
  daily_loss_limit_percent?: string | null;
}

export async function evaluateChecklist(body: ChecklistRequest): Promise<ChecklistResponse> {
  return apiPost('/checklist/pre-trade', body, checklistSchema);
}

// ---------- loss root causes ----------

const mistakeDefinition = z.object({
  tag: z.string(),
  label: z.string(),
  question: z.string(),
  fix: z.string(),
  is_process_error: z.boolean(),
});
export type MistakeDefinition = z.infer<typeof mistakeDefinition>;

const rootCause = z.object({
  tag: z.string(),
  label: z.string(),
  fix: z.string(),
  is_process_error: z.boolean(),
  occurrences: z.number(),
  r_lost: decimalStr,
});
export type RootCause = z.infer<typeof rootCause>;

const rootCauseReview = z.object({
  closed_losses: z.number(),
  tagged_losses: z.number(),
  untagged_losses: z.number(),
  process_error_losses: z.number(),
  good_process_losses: z.number(),
  causes: z.array(rootCause),
  verdict: z.string(),
});
export type RootCauseReview = z.infer<typeof rootCauseReview>;

export async function getMistakeCatalog(): Promise<MistakeDefinition[]> {
  return apiGet('/trades/mistakes/catalog', z.array(mistakeDefinition));
}

export async function getRootCauseReview(): Promise<RootCauseReview> {
  return apiGet('/trades/mistakes/review', rootCauseReview);
}
