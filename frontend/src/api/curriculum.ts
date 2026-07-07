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
});
export type LessonSummary = z.infer<typeof lessonSummary>;

const moduleSummary = z.object({
  id: z.string(),
  order: z.number(),
  title: z.string(),
  summary: z.string(),
  est_minutes: z.number(),
  completed_count: z.number(),
  total_count: z.number(),
  is_complete: z.boolean(),
  lessons: z.array(lessonSummary),
});
export type ModuleSummary = z.infer<typeof moduleSummary>;

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
});
export type LessonResponse = z.infer<typeof lessonResponse>;
export type LessonFigureData = LessonResponse['figures'][number];
export type QuizQuestion = LessonResponse['quiz'][number];

export async function getOverview(): Promise<ModuleSummary[]> {
  return apiGet('/curriculum/overview', z.array(moduleSummary));
}

export async function getLesson(slug: string): Promise<LessonResponse> {
  return apiGet(`/curriculum/lessons/${slug}`, lessonResponse);
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
