import { AxiosError } from 'axios';

// Custom Error Classes
export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly details?: any;

  constructor(message: string, status: number, code: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class ValidationError extends Error {
  public readonly field: string;
  public readonly value?: any;

  constructor(message: string, field: string, value?: any) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.value = value;
  }
}

export class AuthenticationError extends Error {
  public readonly redirectTo?: string;

  constructor(message: string = 'Authentication required', redirectTo?: string) {
    super(message);
    this.name = 'AuthenticationError';
    this.redirectTo = redirectTo;
  }
}

export class AuthorizationError extends Error {
  public readonly requiredPermission?: string;

  constructor(message: string = 'Access denied', requiredPermission?: string) {
    super(message);
    this.name = 'AuthorizationError';
    this.requiredPermission = requiredPermission;
  }
}

export class NetworkError extends Error {
  public readonly offline: boolean;

  constructor(message: string = 'Network connection failed', offline: boolean = false) {
    super(message);
    this.name = 'NetworkError';
    this.offline = offline;
  }
}

export class BusinessLogicError extends Error {
  public readonly errorCode: string;

  constructor(message: string, errorCode: string) {
    super(message);
    this.name = 'BusinessLogicError';
    this.errorCode = errorCode;
  }
}

// Error Type Definitions
export type ErrorType =
  | 'API_ERROR'
  | 'VALIDATION_ERROR'
  | 'AUTHENTICATION_ERROR'
  | 'AUTHORIZATION_ERROR'
  | 'NETWORK_ERROR'
  | 'BUSINESS_LOGIC_ERROR'
  | 'UNKNOWN_ERROR';

export interface ErrorContext {
  timestamp: string;
  url: string;
  userAgent: string;
  userId?: string;
  sessionId?: string;
  component?: string;
  action?: string;
  metadata?: Record<string, any>;
}

export interface ErrorReport {
  id: string;
  type: ErrorType;
  message: string;
  stack?: string;
  context: ErrorContext;
  severity: 'low' | 'medium' | 'high' | 'critical';
  recovered: boolean;
}

// Error Handler Class
export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorQueue: ErrorReport[] = [];
  private maxQueueSize = 100;
  private reportingEndpoint = '/api/errors';

  private constructor() {}

  public static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  // Main error handling method
  public handleError(error: unknown, context?: Partial<ErrorContext>): ErrorReport {
    const errorReport = this.createErrorReport(error, context);

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      this.logErrorToConsole(errorReport);
    }

    // Add to queue for reporting
    this.addToQueue(errorReport);

    // Send to logging service (async)
    this.reportError(errorReport);

    return errorReport;
  }

  // Create standardized error report
  private createErrorReport(error: unknown, context?: Partial<ErrorContext>): ErrorReport {
    const baseContext: ErrorContext = {
      timestamp: new Date().toISOString(),
      url: typeof window !== 'undefined' ? window.location.href : '',
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
      userId: typeof localStorage !== 'undefined' ? localStorage.getItem('userId') || undefined : undefined,
      sessionId: typeof localStorage !== 'undefined' ? localStorage.getItem('sessionId') || undefined : undefined,
      ...context,
    };

    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    if (error instanceof Error) {
      return {
        id: errorId,
        type: this.getErrorType(error),
        message: error.message,
        stack: error.stack,
        context: baseContext,
        severity: this.getErrorSeverity(error),
        recovered: false,
      };
    }

    // Handle non-Error objects
    return {
      id: errorId,
      type: 'UNKNOWN_ERROR',
      message: String(error),
      context: baseContext,
      severity: 'medium',
      recovered: false,
    };
  }

  // Determine error type
  private getErrorType(error: Error): ErrorType {
    if (error instanceof ApiError) return 'API_ERROR';
    if (error instanceof ValidationError) return 'VALIDATION_ERROR';
    if (error instanceof AuthenticationError) return 'AUTHENTICATION_ERROR';
    if (error instanceof AuthorizationError) return 'AUTHORIZATION_ERROR';
    if (error instanceof NetworkError) return 'NETWORK_ERROR';
    if (error instanceof BusinessLogicError) return 'BUSINESS_LOGIC_ERROR';

    // Check by name for external errors
    if (error.name === 'ChunkLoadError') return 'NETWORK_ERROR';
    if (error.message.includes('Network Error')) return 'NETWORK_ERROR';

    return 'UNKNOWN_ERROR';
  }

  // Determine error severity
  private getErrorSeverity(error: Error): 'low' | 'medium' | 'high' | 'critical' {
    if (error instanceof AuthenticationError || error instanceof AuthorizationError) {
      return 'high';
    }
    if (error instanceof ApiError) {
      if (error.status >= 500) return 'critical';
      if (error.status >= 400) return 'medium';
      return 'low';
    }
    if (error instanceof NetworkError) {
      return error.offline ? 'critical' : 'high';
    }
    if (error instanceof ValidationError) {
      return 'low';
    }
    if (error instanceof BusinessLogicError) {
      return 'medium';
    }

    // Default severity based on error characteristics
    if (error.stack?.includes('chunk')) return 'medium';
    if (error.message.includes('timeout')) return 'medium';

    return 'medium';
  }

  // Log error to console with nice formatting
  private logErrorToConsole(errorReport: ErrorReport): void {
    const style = this.getConsoleStyle(errorReport.severity);

    console.group(`🚨 ${errorReport.type} [${errorReport.severity.toUpperCase()}]`);
    console.log(`%c${errorReport.message}`, style);
    console.log('Error ID:', errorReport.id);
    console.log('Timestamp:', errorReport.context.timestamp);
    console.log('Context:', errorReport.context);
    if (errorReport.stack) {
      console.log('Stack:', errorReport.stack);
    }
    console.groupEnd();
  }

  private getConsoleStyle(severity: string): string {
    switch (severity) {
      case 'critical': return 'color: white; background: #dc2626; padding: 2px 4px; border-radius: 2px;';
      case 'high': return 'color: white; background: #ea580c; padding: 2px 4px; border-radius: 2px;';
      case 'medium': return 'color: white; background: #d97706; padding: 2px 4px; border-radius: 2px;';
      case 'low': return 'color: white; background: #65a30d; padding: 2px 4px; border-radius: 2px;';
      default: return 'color: #374151;';
    }
  }

  // Add error to reporting queue
  private addToQueue(errorReport: ErrorReport): void {
    this.errorQueue.push(errorReport);

    // Maintain queue size
    if (this.errorQueue.length > this.maxQueueSize) {
      this.errorQueue.shift();
    }
  }

  // Send error to logging service
  private async reportError(errorReport: ErrorReport): Promise<void> {
    try {
      // Skip reporting in development or if no endpoint configured
      if (process.env.NODE_ENV === 'development' || !this.reportingEndpoint) {
        return;
      }

      await fetch(this.reportingEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport),
      });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  // Get queued errors (for debugging or manual reporting)
  public getQueuedErrors(): ErrorReport[] {
    return [...this.errorQueue];
  }

  // Clear error queue
  public clearQueue(): void {
    this.errorQueue = [];
  }

  // Mark error as recovered
  public markAsRecovered(errorId: string): void {
    const error = this.errorQueue.find(e => e.id === errorId);
    if (error) {
      error.recovered = true;
    }
  }
}

// Axios error handler
export const handleAxiosError = (error: AxiosError): ApiError => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    const message = (data as any)?.message || error.message || 'API request failed';
    const code = (data as any)?.code || `HTTP_${status}`;

    return new ApiError(message, status, code, data);
  } else if (error.request) {
    // Request made but no response
    return new NetworkError('No response from server');
  } else {
    // Request setup error
    return new ApiError(error.message, 0, 'REQUEST_SETUP_ERROR');
  }
};

// Promise error handler
export const handlePromiseRejection = (reason: any): void => {
  const errorHandler = ErrorHandler.getInstance();
  errorHandler.handleError(reason, {
    component: 'PromiseRejectionHandler',
    action: 'unhandled_promise_rejection',
  });
};

// Global error handler setup
export const setupGlobalErrorHandling = (): void => {
  // Handle unhandled promise rejections
  if (typeof window !== 'undefined') {
    window.addEventListener('unhandledrejection', (event) => {
      handlePromiseRejection(event.reason);
    });

    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      const errorHandler = ErrorHandler.getInstance();
      errorHandler.handleError(event.error, {
        component: 'GlobalErrorHandler',
        action: 'javascript_error',
        metadata: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      });
    });
  }
};

// Utility functions
export const createErrorBoundaryProps = (component: string) => ({
  onError: (error: Error, errorInfo: any, errorId: string) => {
    const errorHandler = ErrorHandler.getInstance();
    errorHandler.handleError(error, {
      component,
      action: 'component_error',
      metadata: {
        errorInfo,
        errorId,
      },
    });
  },
});

export const withErrorHandling = <T extends (...args: any[]) => any>(
  fn: T,
  context?: Partial<ErrorContext>
): T => {
  return ((...args: any[]) => {
    try {
      const result = fn(...args);

      // Handle async functions
      if (result instanceof Promise) {
        return result.catch((error) => {
          const errorHandler = ErrorHandler.getInstance();
          errorHandler.handleError(error, context);
          throw error;
        });
      }

      return result;
    } catch (error) {
      const errorHandler = ErrorHandler.getInstance();
      errorHandler.handleError(error, context);
      throw error;
    }
  }) as T;
};

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();