import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
}

export class MapErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Map error:", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="bg-neutral-900 rounded-lg p-4 text-center" style={{ height: '500px' }}>
          <AlertTriangle className="mx-auto mb-4 text-red-500" size={48} />
          <h3 className="text-xl mb-2">Map Error</h3>
          <p className="text-neutral-400 mb-4">
            We couldn't load the map. Please refresh the page to try again.
          </p>
          <button 
            className="bg-primary-500 text-white px-4 py-2 rounded-md"
            onClick={() => this.setState({ hasError: false })}
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default MapErrorBoundary;