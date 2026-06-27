import { z } from 'zod';

import { apiGet, apiPost } from './client';

const category = z.enum([
  'macro',
  'regulatory',
  'geopolitical',
  'risk-off',
  'hype',
  'other',
]);

const classification = z.object({
  category,
  impact: z.string(),
  confidence: z.string(),
  rationale: z.string(),
});
export type NewsClassification = z.infer<typeof classification>;

const newsItem = z.object({
  id: z.string().uuid(),
  source: z.string(),
  url: z.string(),
  ts: z.string(),
  headline: z.string(),
  summary: z.string().nullable(),
  classification: classification.nullable(),
});
export type NewsItem = z.infer<typeof newsItem>;

const ingestResponse = z.object({
  fetched: z.number(),
  inserted: z.number(),
  classified: z.number(),
});
export type IngestResponse = z.infer<typeof ingestResponse>;

export async function listNews(opts: {
  limit?: number;
  onlyClassified?: boolean;
  minImpact?: string;
} = {}): Promise<NewsItem[]> {
  const params = new URLSearchParams();
  if (opts.limit) params.set('limit', String(opts.limit));
  if (opts.onlyClassified) params.set('only_classified', 'true');
  if (opts.minImpact) params.set('min_impact', opts.minImpact);
  const qs = params.toString();
  return apiGet(qs ? `/news?${qs}` : '/news', z.array(newsItem));
}

export async function ingestNews(query: string, hoursBack = 24): Promise<IngestResponse> {
  return apiPost(
    '/news/ingest',
    { query, hours_back: hoursBack },
    ingestResponse
  );
}
