import type { InputHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';

import { Tooltip } from './Tooltip';

interface FieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'className'> {
  label: ReactNode;
  hint?: ReactNode;
  explainer?: ReactNode;
  suffix?: ReactNode;
  error?: string | null;
}

export function Field({ label, hint, explainer, suffix, error, ...inputProps }: FieldProps) {
  return (
    <div>
      <label className="label">
        {explainer ? <Tooltip label={explainer}>{label}</Tooltip> : <span>{label}</span>}
        {hint && <span className="font-normal normal-case tracking-normal text-mentor-muted/80">· {hint}</span>}
      </label>
      <div className="relative">
        <input
          {...inputProps}
          className={clsx('input', error && 'border-mentor-danger', suffix && 'pr-12')}
        />
        {suffix && (
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-mentor-muted">
            {suffix}
          </span>
        )}
      </div>
      {error && <p className="mt-1 text-xs text-mentor-danger">{error}</p>}
    </div>
  );
}
