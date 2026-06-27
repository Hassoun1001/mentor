import { useState, type ReactNode } from 'react';

/**
 * Lightweight hover/focus tooltip — the "contextual explainer" from the plan.
 *
 * Per Principle 01 (the mentor is the product), every metric is tappable for
 * a plain-language explanation. We use plain CSS rather than a library so the
 * teaching layer never depends on a heavyweight tooltip framework.
 */
export function Tooltip({ label, children }: { label: ReactNode; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        className="cursor-help border-b border-dotted border-mentor-muted/60 text-left"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        aria-describedby="tooltip"
      >
        {children}
      </button>
      {open && (
        <span
          id="tooltip"
          role="tooltip"
          className="absolute left-0 top-full z-30 mt-2 w-72 rounded-lg border border-mentor-border
            bg-mentor-panelLight p-3 text-xs leading-relaxed text-mentor-fg shadow-panel"
        >
          {label}
        </span>
      )}
    </span>
  );
}
