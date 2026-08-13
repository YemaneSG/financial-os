import { Component, type ReactNode, type ErrorInfo } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  errorCode: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, errorCode: "" };

  static getDerivedStateFromError(): State {
    return { hasError: true, errorCode: "RENDER_ERROR" };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Log safe error code only — no stack or component tree in production.
    void error;
    void info;
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div role="alert" className="error-boundary">
            <p>Something went wrong. Please reload the page.</p>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
