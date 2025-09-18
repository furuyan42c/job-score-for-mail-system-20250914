/**
 * Enhanced Error Boundary Component
 *
 * Provides comprehensive error handling for React components with:
 * - Error categorization and classification
 * - Automatic error reporting to monitoring services
 * - Contextual fallback UI based on error type
 * - Retry mechanisms and recovery options
 * - Development vs production behavior
 * - Error context preservation
 *
 * Usage:
 * <ErrorBoundary fallback={<CustomFallback />} onError={handleError}>
 *   <YourComponent />
 * </ErrorBoundary>
 */

'use client';

import React, { Component, ReactNode, ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, Wifi, Database, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
  retryCount: number;
  lastErrorTime: number;
}

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo, errorContext: ErrorContext) => void;
  enableRetry?: boolean;
  maxRetries?: number;
  resetOnPropsChange?: boolean;
  isolateErrors?: boolean;
  errorTypes?: ErrorType[];
  context?: string;
  level?: 'page' | 'section' | 'component';
}

export interface ErrorContext {
  componentStack: string;
  errorBoundary: string;
  context?: string;
  level: 'page' | 'section' | 'component';
  userId?: string;
  sessionId?: string;
  timestamp: number;
  retryCount: number;
  userAgent: string;
  url: string;
}

export enum ErrorType {
  NETWORK = 'network',
  AUTH = 'auth',
  PERMISSION = 'permission',
  VALIDATION = 'validation',
  RUNTIME = 'runtime',
  CHUNK = 'chunk',
  TIMEOUT = 'timeout',
  UNKNOWN = 'unknown'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// ============================================================================
// ERROR CLASSIFICATION
// ============================================================================

export class ErrorClassifier {
  static classify(error: Error): { type: ErrorType; severity: ErrorSeverity; isRecoverable: boolean } {
    const message = error.message?.toLowerCase() || '';
    const stack = error.stack?.toLowerCase() || '';

    // Network errors
    if (
      message.includes('network') ||
      message.includes('fetch') ||
      message.includes('connection') ||
      message.includes('timeout') ||
      error.name === 'NetworkError'
    ) {
      return {
        type: ErrorType.NETWORK,
        severity: ErrorSeverity.MEDIUM,
        isRecoverable: true
      };
    }

    // Authentication errors
    if (
      message.includes('unauthorized') ||
      message.includes('auth') ||
      message.includes('token') ||
      message.includes('401') ||
      message.includes('403')
    ) {
      return {
        type: ErrorType.AUTH,
        severity: ErrorSeverity.HIGH,
        isRecoverable: false
      };
    }

    // Permission errors
    if (
      message.includes('permission') ||
      message.includes('forbidden') ||
      message.includes('access denied')
    ) {
      return {
        type: ErrorType.PERMISSION,
        severity: ErrorSeverity.HIGH,
        isRecoverable: false
      };
    }

    // Validation errors
    if (
      message.includes('validation') ||
      message.includes('invalid') ||
      message.includes('required') ||
      message.includes('format')
    ) {
      return {
        type: ErrorType.VALIDATION,
        severity: ErrorSeverity.LOW,
        isRecoverable: true
      };
    }

    // Chunk loading errors (common in SPAs)
    if (
      message.includes('chunk') ||
      message.includes('loading') ||
      message.includes('module') ||
      stack.includes('webpack')
    ) {
      return {
        type: ErrorType.CHUNK,
        severity: ErrorSeverity.MEDIUM,
        isRecoverable: true
      };
    }

    // Timeout errors
    if (message.includes('timeout') || message.includes('timed out')) {
      return {
        type: ErrorType.TIMEOUT,
        severity: ErrorSeverity.MEDIUM,
        isRecoverable: true
      };
    }

    // Runtime errors
    if (
      message.includes('undefined') ||
      message.includes('null') ||
      message.includes('reference') ||
      error.name === 'TypeError' ||
      error.name === 'ReferenceError'
    ) {
      return {
        type: ErrorType.RUNTIME,
        severity: ErrorSeverity.HIGH,
        isRecoverable: false
      };
    }

    // Default to unknown
    return {
      type: ErrorType.UNKNOWN,
      severity: ErrorSeverity.MEDIUM,
      isRecoverable: false
    };
  }

  static getIcon(type: ErrorType) {
    switch (type) {
      case ErrorType.NETWORK:
        return Wifi;
      case ErrorType.AUTH:
      case ErrorType.PERMISSION:
        return Shield;
      case ErrorType.VALIDATION:
        return AlertTriangle;
      case ErrorType.CHUNK:
      case ErrorType.TIMEOUT:
        return Database;
      case ErrorType.RUNTIME:
        return Bug;
      default:
        return AlertTriangle;
    }
  }

  static getMessage(type: ErrorType): { title: string; description: string } {
    switch (type) {
      case ErrorType.NETWORK:
        return {
          title: 'ネットワークエラー',
          description: 'インターネット接続を確認して、もう一度お試しください。'
        };
      case ErrorType.AUTH:
        return {
          title: '認証エラー',
          description: 'セッションが期限切れです。再ログインしてください。'
        };
      case ErrorType.PERMISSION:
        return {
          title: 'アクセス権限がありません',
          description: 'この機能を利用する権限がありません。'
        };
      case ErrorType.VALIDATION:
        return {
          title: '入力エラー',
          description: '入力内容を確認して、もう一度お試しください。'
        };
      case ErrorType.CHUNK:
        return {
          title: 'アプリの読み込みエラー',
          description: 'ページを再読み込みしてください。'
        };
      case ErrorType.TIMEOUT:
        return {
          title: 'タイムアウトエラー',
          description: '処理に時間がかかっています。もう一度お試しください。'
        };
      case ErrorType.RUNTIME:
        return {
          title: 'アプリケーションエラー',
          description: '予期しないエラーが発生しました。'
        };
      default:
        return {
          title: '不明なエラー',
          description: '予期しないエラーが発生しました。サポートにお問い合わせください。'
        };
    }
  }
}

// ============================================================================
// ERROR REPORTER
// ============================================================================

export class ErrorReporter {
  static async report(error: Error, errorContext: ErrorContext): Promise<void> {
    try {
      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group('🚨 Error Boundary Report');
        console.error('Error:', error);
        console.log('Context:', errorContext);
        console.groupEnd();
      }

      // Report to analytics (Google Analytics)
      if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('event', 'exception', {
          description: error.message,
          fatal: false,
          custom_map: {
            error_boundary: errorContext.errorBoundary,
            error_level: errorContext.level,
            retry_count: errorContext.retryCount
          }
        });
      }

      // Report to external monitoring service
      await this.reportToMonitoringService(error, errorContext);

      // Report to backend API
      await this.reportToBackend(error, errorContext);

    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  private static async reportToMonitoringService(error: Error, context: ErrorContext): Promise<void> {
    // Implement Sentry, LogRocket, or other monitoring service integration
    try {
      if (typeof window !== 'undefined' && (window as any).Sentry) {
        (window as any).Sentry.captureException(error, {
          tags: {
            component: context.errorBoundary,
            level: context.level
          },
          extra: context
        });
      }
    } catch (e) {
      console.warn('Monitoring service reporting failed:', e);
    }
  }

  private static async reportToBackend(error: Error, context: ErrorContext): Promise<void> {
    try {
      const errorReport = {
        message: error.message,
        stack: error.stack,
        name: error.name,
        context,
        timestamp: Date.now(),
        environment: process.env.NODE_ENV
      };

      // Only report in production or when explicitly enabled
      if (process.env.NODE_ENV === 'production' || process.env.NEXT_PUBLIC_ENABLE_ERROR_REPORTING === 'true') {
        await fetch('/api/errors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(errorReport)
        });
      }
    } catch (e) {
      console.warn('Backend error reporting failed:', e);
    }
  }
}

// ============================================================================
// ERROR BOUNDARY COMPONENT
// ============================================================================

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      retryCount: 0,
      lastErrorTime: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    return {
      hasError: true,
      error,
      errorId,
      lastErrorTime: Date.now()
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });

    const errorContext: ErrorContext = {
      componentStack: errorInfo.componentStack,
      errorBoundary: this.props.context || this.constructor.name,
      context: this.props.context,
      level: this.props.level || 'component',
      timestamp: Date.now(),
      retryCount: this.state.retryCount,
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown'
    };

    // Report error
    ErrorReporter.report(error, errorContext);

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo, errorContext);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    // Reset error state when props change (if enabled)
    if (hasError && resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetErrorBoundary();
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      window.clearTimeout(this.resetTimeoutId);
    }
  }

  resetErrorBoundary = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      retryCount: 0,
      lastErrorTime: 0
    });
  };

  handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount < maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));

      // Auto-reset after a delay if error persists
      this.resetTimeoutId = window.setTimeout(() => {
        if (this.state.hasError) {
          this.resetErrorBoundary();
        }
      }, 5000);
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  handleNavigateHome = () => {
    window.location.href = '/';
  };

  render() {
    const { hasError, error, errorInfo, errorId, retryCount } = this.state;
    const { children, fallback, enableRetry = true, maxRetries = 3, level = 'component' } = this.props;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Classify error
      const { type, severity, isRecoverable } = ErrorClassifier.classify(error);
      const Icon = ErrorClassifier.getIcon(type);
      const { title, description } = ErrorClassifier.getMessage(type);

      // Determine container classes based on level
      const containerClasses = level === 'page'
        ? 'min-h-screen flex items-center justify-center p-4'
        : 'flex items-center justify-center p-4 min-h-[200px]';

      return (
        <div className={containerClasses}>
          <div className="max-w-md w-full text-center space-y-6">
            {/* Error Icon */}
            <div className="flex justify-center">
              <div className={`p-4 rounded-full ${
                severity === ErrorSeverity.CRITICAL ? 'bg-red-100' :
                severity === ErrorSeverity.HIGH ? 'bg-orange-100' :
                severity === ErrorSeverity.MEDIUM ? 'bg-yellow-100' :
                'bg-blue-100'
              }`}>
                <Icon className={`h-8 w-8 ${
                  severity === ErrorSeverity.CRITICAL ? 'text-red-600' :
                  severity === ErrorSeverity.HIGH ? 'text-orange-600' :
                  severity === ErrorSeverity.MEDIUM ? 'text-yellow-600' :
                  'text-blue-600'
                }`} />
              </div>
            </div>

            {/* Error Message */}
            <div className="space-y-2">
              <h2 className={`font-bold tracking-tight ${
                level === 'page' ? 'text-2xl' : 'text-lg'
              }`}>
                {title}
              </h2>
              <p className="text-muted-foreground text-sm">
                {description}
              </p>

              {/* Retry information */}
              {retryCount > 0 && (
                <p className="text-xs text-muted-foreground">
                  試行回数: {retryCount}/{maxRetries}
                </p>
              )}

              {/* Development Error Details */}
              {process.env.NODE_ENV === 'development' && errorInfo && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm font-medium">
                    開発者向け情報
                  </summary>
                  <div className="mt-2 p-3 bg-muted rounded-md text-xs font-mono break-all space-y-2">
                    <div>
                      <strong>エラーID:</strong> {errorId}
                    </div>
                    <div>
                      <strong>メッセージ:</strong> {error.message}
                    </div>
                    <div>
                      <strong>タイプ:</strong> {type} ({severity})
                    </div>
                    {error.stack && (
                      <div>
                        <strong>スタックトレース:</strong>
                        <pre className="mt-1 whitespace-pre-wrap text-xs">{error.stack}</pre>
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {/* Retry Button */}
              {enableRetry && isRecoverable && retryCount < maxRetries && (
                <Button
                  onClick={this.handleRetry}
                  size={level === 'page' ? 'default' : 'sm'}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  再試行
                </Button>
              )}

              {/* Reload Button for critical errors */}
              {(severity === ErrorSeverity.CRITICAL || type === ErrorType.CHUNK) && level === 'page' && (
                <Button
                  onClick={this.handleReload}
                  variant="outline"
                  size={level === 'page' ? 'default' : 'sm'}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  ページを再読み込み
                </Button>
              )}

              {/* Home Button for page-level errors */}
              {level === 'page' && (
                <Button
                  onClick={this.handleNavigateHome}
                  variant="outline"
                  size="default"
                  className="flex items-center gap-2"
                >
                  <Home className="h-4 w-4" />
                  ホームに戻る
                </Button>
              )}
            </div>

            {/* Error ID and Support Info */}
            <div className="text-xs text-muted-foreground space-y-1">
              <p>エラーID: {errorId}</p>
              {level === 'page' && (
                <p>
                  問題が続く場合は{' '}
                  <a
                    href="/contact"
                    className="text-primary hover:underline"
                  >
                    サポート
                  </a>
                  までお問い合わせください。
                </p>
              )}
            </div>
          </div>
        </div>
      );
    }

    return children;
  }
}

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

export const PageErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'level'>> = (props) => (
  <ErrorBoundary {...props} level="page" />
);

export const SectionErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'level'>> = (props) => (
  <ErrorBoundary {...props} level="section" />
);

export const ComponentErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'level'>> = (props) => (
  <ErrorBoundary {...props} level="component" />
);

// ============================================================================
// HOOKS
// ============================================================================

export const useErrorHandler = () => {
  const handleError = React.useCallback((error: Error, context?: string) => {
    const errorContext: ErrorContext = {
      componentStack: 'Manual error from useErrorHandler',
      errorBoundary: 'useErrorHandler',
      context,
      level: 'component',
      timestamp: Date.now(),
      retryCount: 0,
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown'
    };

    ErrorReporter.report(error, errorContext);
  }, []);

  return { handleError };
};

// ============================================================================
// EXPORTS
// ============================================================================

export default ErrorBoundary;
export {
  ErrorType,
  ErrorSeverity,
  ErrorClassifier,
  ErrorReporter
};