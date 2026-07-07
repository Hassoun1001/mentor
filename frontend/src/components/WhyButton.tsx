import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { type ExplainStyle, type SupportedTopic, explainMetric } from '../api/explain';

interface WhyButtonProps {
  topic: SupportedTopic;
  context: Record<string, unknown>;
  label?: string;
}

/**
 * "Why did you say that?" — Principle 02 from the plan.
 *
 * Hangs off any metric. Click to fetch an LLM (or templated fallback)
 * explanation that uses the *actual* values currently on screen.
 */
export function WhyButton({ topic, context, label = 'Why?' }: WhyButtonProps) {
  const [open, setOpen] = useState(false);
  const [style, setStyle] = useState<ExplainStyle>('concise');
  const mutation = useMutation({
    mutationFn: (s: ExplainStyle) => explainMetric(topic, context, s),
  });

  const toggle = () => {
    if (!open && !mutation.data && !mutation.isPending) {
      mutation.mutate(style);
    }
    setOpen(!open);
  };

  const ask = (s: ExplainStyle) => {
    setStyle(s);
    mutation.mutate(s);
  };

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={toggle}
        className="inline-flex items-center gap-1 rounded-full border border-mentor-border bg-mentor-panelLight px-2 py-0.5 text-[10px] uppercase tracking-wider text-mentor-muted transition-colors hover:text-mentor-fg"
      >
        {label}
      </button>
      {open && (
        <div className="absolute right-0 top-full z-20 mt-2 w-80 rounded-lg border border-mentor-border bg-mentor-panel p-4 text-xs leading-relaxed text-mentor-fg shadow-panel">
          {mutation.isPending && <span className="text-mentor-muted">thinking…</span>}
          {mutation.error && (
            <span className="text-mentor-danger">
              Couldn't explain — backend unreachable.
            </span>
          )}
          {mutation.data && (
            <>
              <p className="whitespace-pre-wrap">{mutation.data.explanation}</p>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex gap-2">
                  {(['concise', 'thorough', 'socratic'] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      disabled={mutation.isPending}
                      onClick={() => ask(s)}
                      className={
                        'rounded px-1.5 py-0.5 text-[10px] capitalize ' +
                        (s === style
                          ? 'bg-mentor-accent/20 text-mentor-accentSoft'
                          : 'text-mentor-muted hover:text-mentor-fg')
                      }
                    >
                      {s}
                    </button>
                  ))}
                </div>
                <span className="text-[10px] uppercase tracking-wider text-mentor-muted">
                  {mutation.data.source}
                </span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
