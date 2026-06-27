import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { type SupportedTopic, explainMetric } from '../api/explain';

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
  const mutation = useMutation({
    mutationFn: () => explainMetric(topic, context),
  });

  const toggle = () => {
    if (!open && !mutation.data && !mutation.isPending) {
      mutation.mutate();
    }
    setOpen(!open);
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
              <p className="mt-3 text-[10px] uppercase tracking-wider text-mentor-muted">
                source · {mutation.data.source}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
