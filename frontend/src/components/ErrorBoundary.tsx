import { Component, type ReactNode } from 'react';

interface State {
  error: Error | null;
}

/**
 * Stops one screen's runtime error from blanking the whole app. Key it by
 * the active page so navigating away resets it.
 */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error): void {
    console.error('page render error', error);
  }

  override render(): ReactNode {
    const { error } = this.state;
    if (error) {
      return (
        <div className="panel-pad space-y-2">
          <div className="text-sm font-medium text-mentor-danger">
            Something broke on this screen.
          </div>
          <p className="font-mono text-xs text-mentor-muted">{error.message}</p>
          <button type="button" className="btn-ghost" onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
