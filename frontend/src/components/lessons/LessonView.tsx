/**
 * One lesson, drawn section by section in the book's fixed order.
 */
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import type { LessonResponse, QuizQuestion } from '../../api/curriculum';
import { BookChart } from './BookChart';
import { LessonFigure } from './LessonFigure';
import { VERDICT } from './verdict';

const PROSE =
  'book-prose prose max-w-none text-[1.0625rem] leading-[1.75] dark:prose-invert ' +
  'prose-headings:font-medium prose-headings:text-mentor-fg prose-h3:mt-6 prose-h3:text-lg ' +
  'prose-p:text-mentor-fg prose-li:text-mentor-fg prose-li:my-1 ' +
  'prose-strong:text-mentor-fg prose-strong:font-semibold ' +
  'prose-th:text-mentor-fg prose-td:text-mentor-fg ' +
  'prose-a:text-mentor-accent ' +
  'prose-code:rounded prose-code:bg-mentor-panelLight prose-code:px-1 prose-code:py-0.5 prose-code:text-sm prose-code:font-normal prose-code:text-mentor-accent ' +
  'prose-code:before:content-none prose-code:after:content-none ' +
  'prose-blockquote:border-mentor-accent prose-blockquote:text-mentor-fg ' +
  'prose-pre:bg-mentor-panelLight prose-pre:text-mentor-fg';

function Prose({ children }: { children: string }) {
  return (
    <div className={PROSE}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children: inner }) => (
            <div className="overflow-x-auto">
              <table>{inner}</table>
            </div>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

function Section({
  title,
  children,
  id,
}: {
  title: string;
  id?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-9" id={id}>
      <h2 className="mb-3 border-b border-mentor-border pb-1.5 text-xs font-semibold uppercase tracking-wider text-mentor-muted">
        {title}
      </h2>
      {children}
    </section>
  );
}

export function LessonBody({
  lesson,
  showQuizAnswers = false,
}: {
  lesson: LessonResponse;
  showQuizAnswers?: boolean;
}) {
  const explainCharts = lesson.charts.filter((c) => c.place === 'explain');
  const exampleCharts = lesson.charts.filter((c) => c.place === 'example');
  const verdict = lesson.evidence ? (VERDICT[lesson.evidence.verdict] ?? VERDICT.fact) : null;

  return (
    <div>
      <div className="mt-5 rounded-xl border border-mentor-accent/30 bg-mentor-accent/5 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-mentor-accent">
          The goal
        </div>
        <p className="mt-1 text-[1.0625rem] leading-relaxed text-mentor-fg">{lesson.goal}</p>
      </div>

      <Section title="Explained simply">
        <Prose>{lesson.body_md}</Prose>
        {explainCharts.map((chart) => (
          <BookChart key={chart.title} chart={chart} />
        ))}
        {lesson.figures.map((figure) => (
          <div key={figure.key} className="my-6">
            <LessonFigure figureKey={figure.key} caption={figure.caption} />
          </div>
        ))}
      </Section>

      <Section title="Step by step">
        <ol className="space-y-2.5">
          {lesson.steps.map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-mentor-panelLight font-mono text-xs text-mentor-muted">
                {i + 1}
              </span>
              <span className="leading-relaxed text-mentor-fg">{step}</span>
            </li>
          ))}
        </ol>
      </Section>

      <Section title="Worked example">
        <div className="rounded-xl bg-mentor-panelLight/60 p-4">
          <Prose>{lesson.example_md}</Prose>
        </div>
        {exampleCharts.map((chart) => (
          <BookChart key={chart.title} chart={chart} />
        ))}
      </Section>

      <Section title="Common mistakes">
        <ul className="space-y-2">
          {lesson.mistakes.map((mistake, i) => (
            <li key={i} className="flex gap-2.5 leading-relaxed text-mentor-fg">
              <span className="mt-0.5 text-mentor-danger" aria-hidden>
                ✕
              </span>
              <span>{mistake}</span>
            </li>
          ))}
        </ul>
      </Section>

      {lesson.evidence && verdict && (
        <Section title="Does it actually work?">
          <div className="rounded-xl border border-mentor-border p-4">
            <div className={`mb-2 inline-block rounded border px-2 py-0.5 text-xs font-medium ${verdict.tone}`}>
              {verdict.label}
            </div>
            <p className="mb-3 text-xs text-mentor-muted">{verdict.hint}</p>
            <Prose>{lesson.evidence.text_md}</Prose>
          </div>
        </Section>
      )}

      <Section title="Try it yourself">
        <div className="rounded-xl border border-dashed border-mentor-accent/40 p-4 leading-relaxed text-mentor-fg">
          {lesson.try_it}
        </div>
      </Section>

      {lesson.quiz.length > 0 && (
        <Section title="Check yourself">
          <div className="space-y-4 print:hidden">
            {lesson.quiz.map((question, i) => (
              <QuizItem key={i} question={question} index={i} />
            ))}
          </div>
          {showQuizAnswers && <PrintedQuiz questions={lesson.quiz} />}
        </Section>
      )}

      <Section title="Key takeaways">
        <ul className="space-y-1.5">
          {lesson.takeaways.map((item, i) => (
            <li key={i} className="flex gap-2.5 font-medium leading-relaxed text-mentor-fg">
              <span className="text-mentor-accentSoft" aria-hidden>
                ✓
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

function PrintedQuiz({ questions }: { questions: QuizQuestion[] }) {
  return (
    <div className="hidden space-y-3 print:block">
      {questions.map((question, i) => (
        <div key={i}>
          <div className="font-medium">
            {i + 1}. {question.prompt}
          </div>
          <div className="mt-1 text-sm">Answer: {question.options[question.correct_index]}</div>
          <div className="text-sm text-mentor-muted">{question.explanation}</div>
        </div>
      ))}
    </div>
  );
}

function QuizItem({ question, index }: { question: QuizQuestion; index: number }) {
  const [picked, setPicked] = useState<number | null>(null);
  const answered = picked !== null;
  const correct = picked === question.correct_index;

  return (
    <div className="rounded-xl border border-mentor-border bg-mentor-panelLight/40 p-4">
      <div className="font-medium leading-snug text-mentor-fg">
        {index + 1}. {question.prompt}
      </div>
      <div className="mt-3 space-y-2">
        {question.options.map((option, i) => {
          const isCorrect = i === question.correct_index;
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
              className={`flex w-full items-center gap-2 rounded-lg border px-3 py-2.5 text-left text-sm ${tone} disabled:cursor-default`}
            >
              <span className="font-mono text-xs">{String.fromCharCode(65 + i)}</span>
              <span>{option}</span>
              {answered && isCorrect && <span className="ml-auto">✓</span>}
              {answered && isPicked && !isCorrect && <span className="ml-auto">✗</span>}
            </button>
          );
        })}
      </div>
      {answered && (
        <div className="mt-3 space-y-2">
          <div className={`text-sm font-medium ${correct ? 'text-mentor-accentSoft' : 'text-mentor-danger'}`}>
            {correct ? 'Correct.' : 'Not quite.'}
          </div>
          <p className="text-sm leading-relaxed text-mentor-muted">{question.explanation}</p>
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
