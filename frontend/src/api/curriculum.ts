import { z } from 'zod';

import { apiGet, apiPost } from './client';

const status = z.enum(['not_started', 'in_progress', 'completed']);
export type LessonStatus = z.infer<typeof status>;

const lessonSummary = z.object({
  slug: z.string(),
  title: z.string(),
  summary: z.string(),
  est_minutes: z.number(),
  order_in_module: z.number(),
  key_concepts: z.array(z.string()),
  status,
  last_seen_at: z.string().nullable(),
});
export type LessonSummary = z.infer<typeof lessonSummary>;

const moduleSummary = z.object({
  id: z.string(),
  order: z.number(),
  part_id: z.string(),
  title: z.string(),
  summary: z.string(),
  est_minutes: z.number(),
  completed_count: z.number(),
  total_count: z.number(),
  is_complete: z.boolean(),
  lessons: z.array(lessonSummary),
});
export type ModuleSummary = z.infer<typeof moduleSummary>;

const part = z.object({
  id: z.string(),
  order: z.number(),
  stage: z.string(),
  title: z.string(),
  summary: z.string(),
});
export type BookPart = z.infer<typeof part>;

const tone = z.enum(['fg', 'muted', 'accent', 'accentSoft', 'warn', 'danger']);
export type ChartTone = z.infer<typeof tone>;
const panel = z.enum(['main', 'lower']);

const chart = z.object({
  title: z.string(),
  caption: z.string(),
  data_kind: z.enum(['illustrative', 'calculated', 'published']),
  kind: z.enum(['candles', 'lines', 'bars']),
  place: z.enum(['explain', 'example']),
  candles: z.array(z.tuple([z.number(), z.number(), z.number(), z.number()])),
  series: z.array(
    z.object({
      name: z.string(),
      values: z.array(z.number().nullable()),
      tone,
      style: z.enum(['line', 'dashed', 'area', 'bars']),
      panel,
    })
  ),
  hlines: z.array(z.object({ y: z.number(), label: z.string(), tone, panel })),
  zones: z.array(
    z.object({
      y0: z.number(),
      y1: z.number(),
      label: z.string(),
      tone,
      x0: z.number().nullable(),
      x1: z.number().nullable(),
    })
  ),
  marks: z.array(
    z.object({
      x: z.number(),
      y: z.number(),
      label: z.string(),
      tone,
      shape: z.enum(['dot', 'up', 'down']),
    })
  ),
  segments: z.array(
    z.object({
      x0: z.number(),
      y0: z.number(),
      x1: z.number(),
      y1: z.number(),
      label: z.string(),
      tone,
    })
  ),
  bars: z.array(z.object({ label: z.string(), value: z.number(), tone })),
  x_labels: z.array(z.string()),
  x_label: z.string(),
  y_label: z.string(),
  y_format: z.enum(['price', 'pct', 'plain', 'r', 'usd']),
  lower_title: z.string(),
  source_note: z.string(),
});
export type BookChart = z.infer<typeof chart>;

const lessonResponse = z.object({
  slug: z.string(),
  module_id: z.string(),
  order_in_module: z.number(),
  title: z.string(),
  summary: z.string(),
  body_md: z.string(),
  est_minutes: z.number(),
  key_concepts: z.array(z.string()),
  figures: z.array(z.object({ key: z.string(), caption: z.string() })),
  quiz: z.array(
    z.object({
      prompt: z.string(),
      options: z.array(z.string()),
      correct_index: z.number(),
      explanation: z.string(),
    })
  ),
  status,
  goal: z.string(),
  charts: z.array(chart),
  steps: z.array(z.string()),
  example_md: z.string(),
  mistakes: z.array(z.string()),
  evidence: z.object({ verdict: z.string(), text_md: z.string() }).nullable(),
  try_it: z.string(),
  takeaways: z.array(z.string()),
  sources: z.array(z.string()),
});
export type LessonResponse = z.infer<typeof lessonResponse>;
export type LessonFigureData = LessonResponse['figures'][number];
export type QuizQuestion = LessonResponse['quiz'][number];

const searchHit = z.object({
  slug: z.string(),
  title: z.string(),
  summary: z.string(),
  snippet: z.string(),
});
export type SearchHit = z.infer<typeof searchHit>;

const glossaryTerm = z.object({ term: z.string(), definition: z.string() });
export type GlossaryTerm = z.infer<typeof glossaryTerm>;

const source = z.object({
  key: z.string(),
  authors: z.string(),
  year: z.string(),
  title: z.string(),
  url: z.string(),
  note: z.string(),
  topic: z.string(),
  checked: z.boolean(),
});
export type BookSource = z.infer<typeof source>;

export async function getOverview(): Promise<ModuleSummary[]> {
  return apiGet('/curriculum/overview', z.array(moduleSummary));
}

export async function getParts(): Promise<BookPart[]> {
  return apiGet('/curriculum/parts', z.array(part));
}

export async function getLesson(slug: string): Promise<LessonResponse> {
  return apiGet(`/curriculum/lessons/${slug}`, lessonResponse);
}

export async function getPartLessons(partId: string): Promise<LessonResponse[]> {
  return apiGet(`/curriculum/parts/${partId}/lessons`, z.array(lessonResponse));
}

export async function searchLessons(query: string): Promise<SearchHit[]> {
  return apiGet(`/curriculum/search?q=${encodeURIComponent(query)}`, z.array(searchHit));
}

export async function getGlossary(): Promise<GlossaryTerm[]> {
  return apiGet('/curriculum/glossary', z.array(glossaryTerm));
}

export async function getSources(): Promise<BookSource[]> {
  return apiGet('/curriculum/sources', z.array(source));
}

export async function markLesson(
  slug: string,
  newStatus: LessonStatus
): Promise<LessonResponse> {
  return apiPost(
    `/curriculum/lessons/${slug}/progress`,
    { status: newStatus },
    lessonResponse
  );
}
