'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, Home, RefreshCw, Bug } from 'lucide-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo, errorId: string) => void;
  showDetails?: boolean;
  level?: 'page' | 'component' | 'global';
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryCount = 0;
  private maxRetries = 3;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { onError } = this.props;
    const { errorId } = this.state;

    this.setState({
      error,
      errorInfo,
    });

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 Error Boundary Caught Error [${errorId}]`);
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Component Stack:', errorInfo.componentStack);
      console.groupEnd();
    }

    // Report error to logging service
    this.reportError(error, errorInfo, errorId);

    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo, errorId);
    }
  }

  private reportError = async (error: Error, errorInfo: ErrorInfo, errorId: string) => {
    try {
      // In a real application, you would send this to your logging service
      // e.g., Sentry, LogRocket, or custom analytics
      const errorReport = {
        errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        userId: localStorage.getItem('userId') || 'anonymous',
        level: this.props.level || 'component',
      };

      // Simulate error reporting
      console.log('📊 Error reported:', errorReport);

      // Uncomment and configure for your error reporting service
      // await fetch('/api/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorReport),
      // });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private handleRetry = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: '',
      });
    }
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleReload = () => {
    window.location.reload();
  };

  private getErrorMessage = (error: Error): string => {
    // Custom error messages based on error types
    if (error.name === 'ChunkLoadError') {
      return 'Failed to load application resources. Please refresh the page.';
    }
    if (error.message.includes('Network Error')) {
      return 'Network connection issue. Please check your internet connection.';
    }
    if (error.message.includes('Authentication')) {
      return 'Authentication error. Please sign in again.';
    }
    if (error.name === 'ValidationError') {
      return 'Invalid data detected. Please check your input and try again.';
    }

    return 'An unexpected error occurred. Our team has been notified.';
  };

  private renderErrorDetails = () => {
    const { error, errorInfo, errorId } = this.state;
    const { showDetails = process.env.NODE_ENV === 'development' } = this.props;

    if (!showDetails || !error) return null;

    return (
      <details className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <summary className="cursor-pointer font-medium text-gray-700 dark:text-gray-300 mb-2">
          <Bug className="inline w-4 h-4 mr-2" />
          Technical Details (Error ID: {errorId})
        </summary>
        <div className="mt-3 space-y-3 text-sm">
          <div>
            <strong className="text-gray-900 dark:text-gray-100">Error:</strong>
            <pre className="mt-1 p-3 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 rounded overflow-x-auto">
              {error.toString()}
            </pre>
          </div>
          {error.stack && (
            <div>
              <strong className="text-gray-900 dark:text-gray-100">Stack Trace:</strong>
              <pre className="mt-1 p-3 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded text-xs overflow-x-auto max-h-32">
                {error.stack}
              </pre>
            </div>
          )}
          {errorInfo?.componentStack && (
            <div>
              <strong className="text-gray-900 dark:text-gray-100">Component Stack:</strong>
              <pre className="mt-1 p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 rounded text-xs overflow-x-auto max-h-32">
                {errorInfo.componentStack}
              </pre>
            </div>
          )}
        </div>
      </details>
    );
  };

  render() {
    const { hasError, error } = this.state;
    const { children, fallback, level = 'component' } = this.props;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Default error UI
      const canRetry = this.retryCount < this.maxRetries;
      const errorMessage = this.getErrorMessage(error);

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-900">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="text-center">
              <AlertTriangle className="mx-auto h-16 w-16 text-red-500 mb-4" />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                {level === 'global' ? 'Application Error' : 'Something went wrong'}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {errorMessage}
              </p>

              <div className="space-y-3">
                {canRetry && (
                  <button
                    onClick={this.handleRetry}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Try Again ({this.maxRetries - this.retryCount} attempts left)
                  </button>
                )}

                <button
                  onClick={this.handleReload}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reload Page
                </button>

                <button
                  onClick={this.handleGoHome}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  <Home className="w-4 h-4" />
                  Go to Home
                </button>
              </div>

              {this.renderErrorDetails()}

              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  If this problem persists, please contact support with the error ID shown above.
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;

// Hook version for functional components
export const useErrorBoundary = () => {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  const captureError = React.useCallback((error: Error) => {
    setError(error);
  }, []);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { captureError, resetError };
};

// Higher-order component for easy wrapping
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
};