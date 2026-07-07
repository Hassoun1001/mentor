import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';

import {
  type LessonStatus,
  type ModuleSummary,
  type QuizQuestion,
  getLesson,
  getOverview,
  markLesson,
} from '../api/curriculum';
import { LessonFigure } from '../components/lessons/LessonFigure';

export function LessonsPage() {
  const [openSlug, setOpenSlug] = useState<string | null>(null);

  const overview = useQuery({ queryKey: ['curriculum', 'overview'], queryFn: getOverview });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">Lessons</h1>
        <p className="max-w-2xl text-sm text-mentor-muted">
          The mentor IS the product. Forecasting is a feature inside a teaching
          tool — work through the modules in order. Risk first, prediction last.
        </p>
      </header>

      {overview.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}

      <div className="space-y-6">
        {(overview.data ?? []).map((m) => (
          <ModuleCard key={m.id} module={m} onOpen={setOpenSlug} />
        ))}
      </div>

      {openSlug && <LessonModal slug={openSlug} onClose={() => setOpenSlug(null)} />}
    </section>
  );
}

function ModuleCard({
  module,
  onOpen,
}: {
  module: ModuleSummary;
  onOpen: (slug: string) => void;
}) {
  const pct = module.total_count
    ? Math.round((module.completed_count / module.total_count) * 100)
    : 0;
  return (
    <div className="panel-pad">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-mentor-muted">
              0{module.order}
            </span>
            <h2 className="text-lg font-medium">{module.title}</h2>
            {module.is_complete && (
              <span className="pill border-mentor-accent/40 text-mentor-accentSoft">
                complete
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-mentor-muted">{module.summary}</p>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase tracking-wider text-mentor-muted">
            Progress
          </div>
          <div className="mt-1 font-mono text-lg">
            {module.completed_count}/{module.total_count}
          </div>
          <div className="text-xs text-mentor-muted">{module.est_minutes} min</div>
        </div>
      </div>

      <div className="mt-3 h-1 overflow-hidden rounded-full bg-mentor-panelLight">
        <div
          className="h-full bg-mentor-accent transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>

      <ul className="mt-4 divide-y divide-mentor-border">
        {module.lessons.map((l) => (
          <li key={l.slug}>
            <button
              type="button"
              onClick={() => onOpen(l.slug)}
              className="flex w-full items-start justify-between gap-4 py-3 text-left hover:bg-mentor-panelLight/50"
            >
              <div className="flex items-start gap-3">
                <StatusDot status={l.status} />
                <div>
                  <div className="text-sm font-medium">{l.title}</div>
                  <div className="mt-0.5 text-xs text-mentor-muted">{l.summary}</div>
                </div>
              </div>
              <span className="text-xs text-mentor-muted whitespace-nowrap">
                {l.est_minutes} min
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatusDot({ status }: { status: LessonStatus }) {
  const tone =
    status === 'completed'
      ? 'bg-mentor-accent'
      : status === 'in_progress'
        ? 'bg-mentor-warn'
        : 'bg-mentor-border';
  return (
    <span
      className={`mt-1.5 inline-block h-2 w-2 flex-shrink-0 rounded-full ${tone}`}
      aria-label={status}
    />
  );
}

function LessonModal({ slug, onClose }: { slug: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const lesson = useQuery({
    queryKey: ['curriculum', 'lesson', slug],
    queryFn: () => getLesson(slug),
  });

  const mark = useMutation({
    mutationFn: (status: LessonStatus) => markLesson(slug, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['curriculum'] });
    },
  });

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-mentor-bg/80 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[88vh] w-full max-w-3xl overflow-y-auto rounded-xl border border-mentor-border bg-mentor-panel shadow-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-mentor-border bg-mentor-panel/95 px-6 py-3 backdrop-blur">
          <div className="text-xs uppercase tracking-wider text-mentor-muted">
            {lesson.data?.module_id}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg"
          >
            Close
          </button>
        </div>

        {lesson.isLoading && <p className="p-8 text-mentor-muted">Loading…</p>}

        {lesson.data && (
          <article className="px-8 py-6">
            <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">{lesson.data.title}</h1>
            <p className="mt-2 text-sm italic text-mentor-muted">{lesson.data.summary}</p>

            {lesson.data.figures.length > 0 && (
              <div className="mt-6 space-y-4">
                {lesson.data.figures.map((f) => (
                  <LessonFigure key={f.key} figureKey={f.key} caption={f.caption} />
                ))}
              </div>
            )}

            <div className="prose prose-invert mt-6 max-w-none text-mentor-fg
              prose-h3:font-medium prose-h3:text-mentor-fg/95
              prose-p:leading-relaxed prose-li:leading-relaxed
              prose-strong:text-mentor-fg prose-code:rounded prose-code:bg-mentor-panelLight prose-code:px-1.5 prose-code:py-0.5 prose-code:text-mentor-accentSoft
              prose-pre:rounded-lg prose-pre:bg-mentor-panelLight prose-pre:text-xs">
              <ReactMarkdown>{lesson.data.body_md}</ReactMarkdown>
            </div>

            {lesson.data.quiz.length > 0 && <LessonQuiz questions={lesson.data.quiz} />}

            <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-mentor-border pt-4">
              <div className="text-xs text-mentor-muted">
                {lesson.data.est_minutes} min · concepts:{' '}
                {lesson.data.key_concepts.join(', ')}
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={mark.isPending}
                  onClick={() => mark.mutate('in_progress')}
                  className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1.5 text-xs hover:text-mentor-fg"
                >
                  Mark in progress
                </button>
                <button
                  type="button"
                  disabled={mark.isPending || lesson.data.status === 'completed'}
                  onClick={() => mark.mutate('completed')}
                  className="rounded-md bg-mentor-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
                >
                  {lesson.data.status === 'completed' ? 'Completed ✓' : 'Mark complete'}
                </button>
              </div>
            </div>
          </article>
        )}
      </div>
    </div>
  );
}

// ---------- quiz ----------

function LessonQuiz({ questions }: { questions: QuizQuestion[] }) {
  return (
    <div className="mt-8 space-y-4 border-t border-mentor-border pt-6">
      <h2 className="text-lg font-medium text-mentor-fg">Check yourself</h2>
      <p className="text-xs text-mentor-muted">
        Active recall beats re-reading. Pick an answer to see if it&apos;s right.
      </p>
      {questions.map((q, i) => (
        <QuizItem key={i} q={q} index={i} />
      ))}
    </div>
  );
}

function QuizItem({ q, index }: { q: QuizQuestion; index: number }) {
  const [picked, setPicked] = useState<number | null>(null);
  const answered = picked !== null;
  const correct = picked === q.correct_index;

  return (
    <div className="rounded-xl border border-mentor-border bg-mentor-panelLight/40 p-4">
      <div className="text-sm font-medium text-mentor-fg">
        {index + 1}. {q.prompt}
      </div>
      <div className="mt-3 space-y-2">
        {q.options.map((opt, i) => {
          const isCorrect = i === q.correct_index;
          const isPicked = i === picked;
          const tone = !answered
            ? 'border-mentor-border hover:border-mentor-accent/60 text-mentor-fg'
            : isCorrect
              ? 'border-mentor-accent/60 bg-mentor-accent/10 text-mentor-accentSoft'
              : isPicked
                ? 'border-mentor-danger/60 bg-mentor-danger/10 text-mentor-danger'
                : 'border-mentor-border text-mentor-muted';
          return (
            <button
              key={i}
              type="button"
              disabled={answered}
              onClick={() => setPicked(i)}
              className={`flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm ${tone} disabled:cursor-default`}
            >
              <span className="font-mono text-xs">{String.fromCharCode(65 + i)}</span>
              <span>{opt}</span>
              {answered && isCorrect && <span className="ml-auto">✓</span>}
              {answered && isPicked && !isCorrect && <span className="ml-auto">✗</span>}
            </button>
          );
        })}
      </div>
      {answered && (
        <div className="mt-3 space-y-2">
          <div className={`text-xs font-medium ${correct ? 'text-mentor-accentSoft' : 'text-mentor-danger'}`}>
            {correct ? 'Correct.' : 'Not quite.'}
          </div>
          <p className="text-xs leading-relaxed text-mentor-muted">{q.explanation}</p>
          <button
            type="button"
            onClick={() => setPicked(null)}
            className="text-xs text-mentor-muted underline hover:text-mentor-fg"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  );
}
