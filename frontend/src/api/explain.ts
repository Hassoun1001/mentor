import { z } from 'zod';

import { apiPost } from './client';

export const supportedTopic = z.enum([
  'position-size',
  'pip-value',
  'pip-distance',
  'risk-reward',
  'money-at-risk',
  'expectancy',
  'r-multiple',
  'win-rate',
  'profit-factor',
  'guardrails',
  'atr-stop',
]);
export type SupportedTopic = z.infer<typeof supportedTopic>;

const explainResponse = z.object({
  topic: supportedTopic,
  explanation: z.string(),
  source: z.string(),
});
export type ExplainResponse = z.infer<typeof explainResponse>;

export type ExplainStyle = 'concise' | 'thorough' | 'socratic';

export async function explainMetric(
  topic: SupportedTopic,
  context: Record<string, unknown> = {},
  style: ExplainStyle = 'concise'
): Promise<ExplainResponse> {
  return apiPost('/explain', { topic, context, style }, explainResponse);
}
