import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  type BookPart,
  type LessonStatus,
  type LessonSummary,
  type ModuleSummary,
  getGlossary,
  getLesson,
  getOverview,
  getPartLessons,
  getParts,
  getSources,
  markLesson,
  searchLessons,
} from '../api/curriculum';
import { LessonBody } from '../components/lessons/LessonView';

type View =
  | { name: 'home' }
  | { name: 'lesson'; slug: string }
  | { name: 'glossary' }
  | { name: 'sources' }
  | { name: 'print'; partId: string };

type Flat = LessonSummary & { moduleTitle: string; partId: string };

function flatten(modules: ModuleSummary[]): Flat[] {
  return modules.flatMap((m) =>
    m.lessons.map((l) => ({ ...l, moduleTitle: m.title, partId: m.part_id }))
  );
}

export function LessonsPage() {
  const [view, setView] = useState<View>({ name: 'home' });
  const overview = useQuery({ queryKey: ['curriculum', 'overview'], queryFn: getOverview });
  const parts = useQuery({ queryKey: ['curriculum', 'parts'], queryFn: getParts, staleTime: Infinity });
  const lessons = useMemo(() => flatten(overview.data ?? []), [overview.data]);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [view]);

  if (view.name === 'lesson') {
    return (
      <Reader
        key={view.slug}
        slug={view.slug}
        lessons={lessons}
        onOpen={(slug) => setView({ name: 'lesson', slug })}
        onHome={() => setView({ name: 'home' })}
      />
    );
  }
  if (view.name === 'glossary') return <Glossary onHome={() => setView({ name: 'home' })} />;
  if (view.name === 'sources') return <Sources onHome={() => setView({ name: 'home' })} />;
  if (view.name === 'print') {
    return <PrintView partId={view.partId} parts={parts.data ?? []} onHome={() => setView({ name: 'home' })} />;
  }

  return (
    <Home
      modules={overview.data ?? []}
      parts={parts.data ?? []}
      lessons={lessons}
      isLoading={overview.isLoading || parts.isLoading}
      onView={setView}
    />
  );
}

// ---------- home: roadmap, search, progress ----------

function Home({
  modules,
  parts,
  lessons,
  isLoading,
  onView,
}: {
  modules: ModuleSummary[];
  parts: BookPart[];
  lessons: Flat[];
  isLoading: boolean;
  onView: (view: View) => void;
}) {
  const done = lessons.filter((l) => l.status === 'completed').length;
  const pct = lessons.length ? Math.round((done / lessons.length) * 100) : 0;
  const continueLesson = useMemo(() => {
    const started = lessons
      .filter((l) => l.status === 'in_progress' && l.last_seen_at)
      .sort((a, b) => (b.last_seen_at ?? '').localeCompare(a.last_seen_at ?? ''));
    return started[0] ?? lessons.find((l) => l.status !== 'completed') ?? null;
  }, [lessons]);
  const openLesson = (slug: string) => onView({ name: 'lesson', slug });

  return (
    <section className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-medium tracking-tight text-mentor-fg">The trading book</h1>
        <p className="mt-1 text-sm leading-relaxed text-mentor-muted">
          From your first price to running trading as a professional. Any market. Every method
          tested honestly, in plain English.
        </p>
      </header>

      <div className="rounded-xl border border-mentor-warn/40 bg-mentor-warn/5 px-4 py-3 text-sm leading-relaxed text-mentor-fg">
        <strong className="font-semibold">Read this first.</strong> Most retail traders lose money.
        This is education, not financial advice, and nothing here tells you what to trade. This
        app&apos;s own forecasts are unproven and have recently been weak.
      </div>

      <div className="panel-pad">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wider text-mentor-muted">Your progress</div>
            <div className="mt-1 font-mono text-lg text-mentor-fg">
              {done} / {lessons.length} lessons
            </div>
          </div>
          {continueLesson && (
            <button type="button" className="btn-primary" onClick={() => openLesson(continueLesson.slug)}>
              {done === 0 && continueLesson.status === 'not_started' ? 'Start reading' : 'Continue reading'}
            </button>
          )}
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-mentor-panelLight">
          <div className="h-full bg-mentor-accent transition-all" style={{ width: `${pct}%` }} />
        </div>
        {continueLesson && (
          <div className="mt-2 text-xs text-mentor-muted">
            Next: {continueLesson.title} · {continueLesson.moduleTitle}
          </div>
        )}
      </div>

      <SearchBox onOpen={openLesson} />

      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-ghost" onClick={() => onView({ name: 'glossary' })}>
          Glossary
        </button>
        <button type="button" className="btn-ghost" onClick={() => onView({ name: 'sources' })}>
          Sources
        </button>
      </div>

      {isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}

      <div>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mentor-muted">
          The roadmap: beginner to professional
        </h2>
        <ol className="space-y-3">
          {parts.map((part) => (
            <PartRow
              key={part.id}
              part={part}
              modules={modules.filter((m) => m.part_id === part.id)}
              onOpen={openLesson}
              onPrint={() => onView({ name: 'print', partId: part.id })}
            />
          ))}
        </ol>
      </div>
    </section>
  );
}

function SearchBox({ onOpen }: { onOpen: (slug: string) => void }) {
  const [text, setText] = useState('');
  const [query, setQuery] = useState('');
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(text.trim()), 200);
    return () => window.clearTimeout(timer);
  }, [text]);
  const results = useQuery({
    queryKey: ['curriculum', 'search', query],
    queryFn: () => searchLessons(query),
    enabled: query.length >= 2,
  });
  return (
    <div>
      <label className="sr-only" htmlFor="book-search">
        Search the book
      </label>
      <input
        id="book-search"
        type="search"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Search the book: Fibonacci, position size, carry…"
        className="w-full rounded-lg border border-mentor-border bg-mentor-panel px-3 py-2.5 text-base text-mentor-fg placeholder:text-mentor-muted focus:border-mentor-accent focus:outline-none"
      />
      {query.length >= 2 && (
        <div className="mt-2 rounded-xl border border-mentor-border bg-mentor-panel">
          {results.isLoading && <p className="p-3 text-sm text-mentor-muted">Searching…</p>}
          {results.data?.length === 0 && (
            <p className="p-3 text-sm text-mentor-muted">Nothing found for “{query}”.</p>
          )}
          <ul className="divide-y divide-mentor-border">
            {results.data?.map((hit) => (
              <li key={hit.slug}>
                <button
                  type="button"
                  onClick={() => onOpen(hit.slug)}
                  className="w-full p-3 text-left hover:bg-mentor-panelLight/60"
                >
                  <div className="text-sm font-medium text-mentor-fg">{hit.title}</div>
                  <div className="mt-0.5 text-xs leading-relaxed text-mentor-muted">{hit.snippet}</div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PartRow({
  part,
  modules,
  onOpen,
  onPrint,
}: {
  part: BookPart;
  modules: ModuleSummary[];
  onOpen: (slug: string) => void;
  onPrint: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const total = modules.reduce((sum, m) => sum + m.total_count, 0);
  const done = modules.reduce((sum, m) => sum + m.completed_count, 0);
  const minutes = modules.reduce((sum, m) => sum + m.est_minutes, 0);
  const pct = total ? Math.round((done / total) * 100) : 0;
  return (
    <li className="panel">
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        aria-expanded={expanded}
        className="w-full p-4 text-left"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="font-mono text-xs text-mentor-muted">{part.stage}</div>
            <div className="text-base font-medium text-mentor-fg">{part.title}</div>
            <div className="mt-0.5 text-sm leading-snug text-mentor-muted">{part.summary}</div>
          </div>
          <div className="flex-shrink-0 text-right text-xs text-mentor-muted">
            <div className="font-mono text-sm text-mentor-fg">
              {done}/{total}
            </div>
            <div>{minutes} min</div>
          </div>
        </div>
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-mentor-panelLight">
          <div className="h-full bg-mentor-accent" style={{ width: `${pct}%` }} />
        </div>
      </button>
      {expanded && (
        <div className="border-t border-mentor-border px-4 pb-4 pt-2">
          {modules.map((m) => (
            <div key={m.id} className="mt-3">
              <div className="text-sm font-medium text-mentor-fg">{m.title}</div>
              <div className="text-xs text-mentor-muted">{m.summary}</div>
              <ul className="mt-1.5">
                {m.lessons.map((lesson) => (
                  <li key={lesson.slug}>
                    <button
                      type="button"
                      onClick={() => onOpen(lesson.slug)}
                      className="flex w-full items-start justify-between gap-3 rounded-md px-1.5 py-2 text-left hover:bg-mentor-panelLight/60"
                    >
                      <span className="flex min-w-0 items-start gap-2.5">
                        <StatusDot status={lesson.status} />
                        <span className="text-sm text-mentor-fg">{lesson.title}</span>
                      </span>
                      <span className="whitespace-nowrap text-xs text-mentor-muted">
                        {lesson.est_minutes} min
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <button
            type="button"
            onClick={onPrint}
            className="mt-3 text-xs text-mentor-muted underline hover:text-mentor-fg"
          >
            Print this stage or save it as a PDF
          </button>
        </div>
      )}
    </li>
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
      aria-label={status.replace('_', ' ')}
    />
  );
}

// ---------- reader ----------

function Reader({
  slug,
  lessons,
  onOpen,
  onHome,
}: {
  slug: string;
  lessons: Flat[];
  onOpen: (slug: string) => void;
  onHome: () => void;
}) {
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
  const markStarted = useRef(false);
  const { mutate } = mark;
  useEffect(() => {
    if (lesson.data?.status === 'not_started' && !markStarted.current) {
      markStarted.current = true;
      mutate('in_progress');
    }
  }, [lesson.data?.status, mutate]);

  const index = lessons.findIndex((l) => l.slug === slug);
  const previous = index > 0 ? lessons[index - 1] : undefined;
  const next = index >= 0 && index < lessons.length - 1 ? lessons[index + 1] : undefined;
  const scrolled = useReadingProgress(slug);

  return (
    <div className="mx-auto max-w-2xl">
      <div className="sticky top-14 z-20 -mx-3 lg:top-0 border-b border-mentor-border bg-mentor-bg/95 px-3 py-2 backdrop-blur print:hidden sm:mx-0 sm:rounded-b-lg sm:px-4">
        <div className="flex items-center justify-between gap-3">
          <button type="button" onClick={onHome} className="text-sm text-mentor-muted hover:text-mentor-fg">
            ← All lessons
          </button>
          {index >= 0 && (
            <span className="font-mono text-xs text-mentor-muted">
              {index + 1} / {lessons.length}
            </span>
          )}
        </div>
        <div className="mt-1.5 h-0.5 overflow-hidden rounded-full bg-mentor-panelLight">
          <div className="h-full bg-mentor-accent" style={{ width: `${scrolled}%` }} />
        </div>
      </div>

      {lesson.isLoading && <p className="p-8 text-mentor-muted">Loading…</p>}

      {lesson.data && (
        <article className="pb-10 pt-6">
          <div className="text-xs uppercase tracking-wider text-mentor-muted">
            {index >= 0 ? lessons[index]?.moduleTitle : lesson.data.module_id}
          </div>
          <h1 className="mt-1 text-[1.6rem] font-medium leading-tight tracking-tight text-mentor-fg">
            {lesson.data.title}
          </h1>
          <p className="mt-2 text-sm text-mentor-muted">
            {lesson.data.summary} · {lesson.data.est_minutes} min read
          </p>

          <LessonBody lesson={lesson.data} />

          <div className="mt-10 border-t border-mentor-border pt-5">
            <button
              type="button"
              disabled={mark.isPending}
              onClick={() => {
                if (lesson.data.status !== 'completed') mark.mutate('completed');
                if (next) onOpen(next.slug);
              }}
              className="btn-primary w-full justify-center disabled:opacity-50"
            >
              {lesson.data.status === 'completed'
                ? next
                  ? 'Next lesson →'
                  : 'Completed ✓'
                : next
                  ? 'Mark complete and continue →'
                  : 'Mark complete'}
            </button>
            <div className="mt-4 flex items-start justify-between gap-4 text-sm">
              {previous ? (
                <button
                  type="button"
                  onClick={() => onOpen(previous.slug)}
                  className="min-w-0 text-left text-mentor-muted hover:text-mentor-fg"
                >
                  <div className="text-xs">← Previous</div>
                  <div className="truncate">{previous.title}</div>
                </button>
              ) : (
                <span />
              )}
              {next && (
                <button
                  type="button"
                  onClick={() => onOpen(next.slug)}
                  className="min-w-0 text-right text-mentor-muted hover:text-mentor-fg"
                >
                  <div className="text-xs">Next →</div>
                  <div className="truncate">{next.title}</div>
                </button>
              )}
            </div>
          </div>
        </article>
      )}
    </div>
  );
}

function useReadingProgress(resetKey: string): number {
  const [pct, setPct] = useState(0);
  useEffect(() => {
    const update = () => {
      const scrollable = document.documentElement.scrollHeight - window.innerHeight;
      setPct(scrollable > 0 ? Math.min(100, Math.round((window.scrollY / scrollable) * 100)) : 0);
    };
    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update);
      window.removeEventListener('resize', update);
    };
  }, [resetKey]);
  return pct;
}

// ---------- glossary, sources, print ----------

function BackHeader({ title, onHome, children }: { title: string; onHome: () => void; children?: React.ReactNode }) {
  return (
    <header className="print:hidden">
      <button type="button" onClick={onHome} className="text-sm text-mentor-muted hover:text-mentor-fg">
        ← All lessons
      </button>
      <h1 className="mt-2 text-2xl font-medium tracking-tight text-mentor-fg">{title}</h1>
      {children}
    </header>
  );
}

function Glossary({ onHome }: { onHome: () => void }) {
  const glossary = useQuery({ queryKey: ['curriculum', 'glossary'], queryFn: getGlossary, staleTime: Infinity });
  const [filter, setFilter] = useState('');
  const term = filter.trim().toLowerCase();
  const shown = (glossary.data ?? []).filter(
    (t) => !term || t.term.toLowerCase().includes(term) || t.definition.toLowerCase().includes(term)
  );
  return (
    <section className="mx-auto max-w-2xl space-y-4">
      <BackHeader title="Glossary" onHome={onHome} />
      <input
        type="search"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter terms…"
        className="w-full rounded-lg border border-mentor-border bg-mentor-panel px-3 py-2.5 text-base text-mentor-fg placeholder:text-mentor-muted focus:border-mentor-accent focus:outline-none"
      />
      <dl className="divide-y divide-mentor-border rounded-xl border border-mentor-border bg-mentor-panel">
        {shown.map((t) => (
          <div key={t.term} className="p-3">
            <dt className="font-medium text-mentor-fg">{t.term}</dt>
            <dd className="mt-0.5 text-sm leading-relaxed text-mentor-muted">{t.definition}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function Sources({ onHome }: { onHome: () => void }) {
  const sources = useQuery({ queryKey: ['curriculum', 'sources'], queryFn: getSources, staleTime: Infinity });
  const topics = [...new Set((sources.data ?? []).map((s) => s.topic))];
  return (
    <section className="mx-auto max-w-2xl space-y-5">
      <BackHeader title="Sources" onHome={onHome}>
        <p className="mt-1 text-sm leading-relaxed text-mentor-muted">
          Where the claims in this book come from. Everything is written in the book&apos;s own
          words. A source marked &quot;not re-checked&quot; is cited from general knowledge.
        </p>
      </BackHeader>
      {topics.map((topic) => (
        <div key={topic}>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-mentor-muted">{topic}</h2>
          <ul className="space-y-2">
            {(sources.data ?? [])
              .filter((s) => s.topic === topic)
              .map((s) => (
                <li key={s.key} className="rounded-xl border border-mentor-border bg-mentor-panel p-3">
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-sm font-medium text-mentor-accent hover:underline"
                  >
                    {s.title}
                  </a>
                  <div className="mt-0.5 text-xs text-mentor-muted">
                    {s.authors} · {s.year}
                    {!s.checked && ' · not re-checked'}
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-mentor-fg">{s.note}</p>
                </li>
              ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function PrintView({
  partId,
  parts,
  onHome,
}: {
  partId: string;
  parts: BookPart[];
  onHome: () => void;
}) {
  const lessons = useQuery({
    queryKey: ['curriculum', 'part-lessons', partId],
    queryFn: () => getPartLessons(partId),
  });
  const part = parts.find((p) => p.id === partId);
  return (
    <section className="mx-auto max-w-2xl">
      <BackHeader title={part ? `${part.stage}: ${part.title}` : 'Book'} onHome={onHome}>
        <button type="button" className="btn-primary mt-3" onClick={() => window.print()}>
          Print or save as PDF
        </button>
      </BackHeader>
      {lessons.isLoading && <p className="mt-6 text-mentor-muted">Loading…</p>}
      <div id="book-print">
        {part && (
          <div className="mb-8 hidden print:block">
            <h1 className="text-3xl font-medium">
              {part.stage}: {part.title}
            </h1>
            <p className="mt-2">{part.summary}</p>
            <p className="mt-4 text-sm">
              Education only. Not financial advice. Most retail traders lose money. Charts are
              labelled as illustrative, calculated or published.
            </p>
          </div>
        )}
        {lessons.data?.map((lesson) => (
          <article key={lesson.slug} className="mt-10 border-t border-mentor-border pt-6 print:break-before-page">
            <h2 className="text-2xl font-medium text-mentor-fg">{lesson.title}</h2>
            <p className="mt-1 text-sm text-mentor-muted">{lesson.summary}</p>
            <LessonBody lesson={lesson} showQuizAnswers />
          </article>
        ))}
      </div>
    </section>
  );
}
