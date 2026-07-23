import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State {
  error: Error | null;
  componentStack: string | null;
}

/**
 * Stops one screen's runtime error from blanking the whole app. Key it by
 * the active page so navigating away resets it.
 *
 * The message alone is not diagnosable. "Cannot read properties of
 * undefined" names a symptom that could belong to any of a dozen
 * components, and hunting it by reading source is slow and frequently
 * wrong. The component stack says exactly which one, so it is shown here
 * rather than buried in the console — a solo operator should be able to
 * report a fault completely without being told to open developer tools.
 */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  override state: State = { error: null, componentStack: null };

  static getDerivedStateFromError(error: Error): State {
    return { error, componentStack: null };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('page render error', error, info.componentStack);
    this.setState({ componentStack: info.componentStack ?? null });
  }

  private details(): string {
    const { error, componentStack } = this.state;
    return [
      error?.message ?? 'unknown error',
      '',
      error?.stack ?? '(no stack)',
      '',
      'Component stack:',
      componentStack ?? '(unavailable)',
    ].join('\n');
  }

  override render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="panel-pad space-y-3">
        <div className="text-sm font-medium text-mentor-danger">
          Something broke on this screen.
        </div>
        <p className="font-mono text-xs text-mentor-muted">{error.message}</p>

        <details className="rounded-lg border border-mentor-border bg-mentor-panelLight/40 p-3">
          <summary className="cursor-pointer text-xs text-mentor-muted">
            Show details — which component, and where
          </summary>
          <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-mentor-fg/80">
            {this.details()}
          </pre>
        </details>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn-ghost"
            onClick={() => this.setState({ error: null, componentStack: null })}
          >
            Try again
          </button>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => void navigator.clipboard?.writeText(this.details())}
          >
            Copy details
          </button>
        </div>
      </div>
    );
  }
}
