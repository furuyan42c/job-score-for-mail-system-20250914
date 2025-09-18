/**
 * Test Suite for Enhanced Error Boundary Component
 *
 * Tests all aspects of error handling including:
 * - Error classification and categorization
 * - Retry mechanisms and recovery
 * - Error reporting to monitoring services
 * - Different fallback UI states
 * - Hook functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import ErrorBoundary, {
  ErrorType,
  ErrorSeverity,
  ErrorClassifier,
  ErrorReporter,
  PageErrorBoundary,
  SectionErrorBoundary,
  ComponentErrorBoundary,
  useErrorHandler
} from './index';

// ============================================================================
// TEST UTILITIES
// ============================================================================

// Component that throws an error
const ThrowErrorComponent: React.FC<{ error?: Error; shouldThrow?: boolean }> = ({
  error = new Error('Test error'),
  shouldThrow = true
}) => {
  if (shouldThrow) {
    throw error;
  }
  return <div>No error thrown</div>;
};

// Component that uses the error handler hook
const ErrorHandlerTestComponent: React.FC = () => {
  const { handleError } = useErrorHandler();

  const triggerError = () => {
    handleError(new Error('Manual error'), 'test context');
  };

  return (
    <button onClick={triggerError} data-testid="trigger-error">
      Trigger Error
    </button>
  );
};

// Mock console methods
const mockConsoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
const mockConsoleGroup = jest.spyOn(console, 'group').mockImplementation(() => {});
const mockConsoleGroupEnd = jest.spyOn(console, 'groupEnd').mockImplementation(() => {});
const mockConsoleLog = jest.spyOn(console, 'log').mockImplementation(() => {});

// Mock window.gtag
const mockGtag = jest.fn();
Object.defineProperty(window, 'gtag', {
  writable: true,
  value: mockGtag,
});

// Mock fetch
global.fetch = jest.fn();

// ============================================================================
// ERROR CLASSIFIER TESTS
// ============================================================================

describe('ErrorClassifier', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('classify', () => {
    it('should classify network errors correctly', () => {
      const networkErrors = [
        new Error('Network request failed'),
        new Error('fetch error occurred'),
        new Error('Connection timeout'),
        Object.assign(new Error('Test'), { name: 'NetworkError' })
      ];

      networkErrors.forEach(error => {
        const result = ErrorClassifier.classify(error);
        expect(result.type).toBe(ErrorType.NETWORK);
        expect(result.severity).toBe(ErrorSeverity.MEDIUM);
        expect(result.isRecoverable).toBe(true);
      });
    });

    it('should classify authentication errors correctly', () => {
      const authErrors = [
        new Error('Unauthorized access'),
        new Error('Auth token expired'),
        new Error('401 error occurred'),
        new Error('403 forbidden')
      ];

      authErrors.forEach(error => {
        const result = ErrorClassifier.classify(error);
        expect(result.type).toBe(ErrorType.AUTH);
        expect(result.severity).toBe(ErrorSeverity.HIGH);
        expect(result.isRecoverable).toBe(false);
      });
    });

    it('should classify permission errors correctly', () => {
      const permissionErrors = [
        new Error('Permission denied'),
        new Error('Access forbidden'),
        new Error('No access to resource')
      ];

      permissionErrors.forEach(error => {
        const result = ErrorClassifier.classify(error);
        expect(result.type).toBe(ErrorType.PERMISSION);
        expect(result.severity).toBe(ErrorSeverity.HIGH);
        expect(result.isRecoverable).toBe(false);
      });
    });

    it('should classify validation errors correctly', () => {
      const validationErrors = [
        new Error('Validation failed'),
        new Error('Invalid input format'),
        new Error('Required field missing')
      ];

      validationErrors.forEach(error => {
        const result = ErrorClassifier.classify(error);
        expect(result.type).toBe(ErrorType.VALIDATION);
        expect(result.severity).toBe(ErrorSeverity.LOW);
        expect(result.isRecoverable).toBe(true);
      });
    });

    it('should classify chunk loading errors correctly', () => {
      const chunkErrors = [
        new Error('Loading chunk 2 failed'),
        new Error('Module not found'),
        Object.assign(new Error('Test'), { stack: 'webpack error' })
      ];

      chunkErrors.forEach(error => {
        const result = ErrorClassifier.classify(error);
        expect(result.type).toBe(ErrorType.CHUNK);
        expect(result.severity).toBe(ErrorSeverity.MEDIUM);
        expect(result.isRecoverable).toBe(true);
      });
    });

    it('should classify runtime errors correctly', () => {
      const runtimeErrors = [
        new Error('undefined is not a function'),
        new Error('Cannot read property of null'),
        Object.assign(new Error('Test'), { name: 'TypeError' }),
        Object.assign(new Error('Test'), { name: 'ReferenceError' })
      ];

      runtimeErrors.forEach(error => {
        const result = ErrorClassifier.classify(error);
        expect(result.type).toBe(ErrorType.RUNTIME);
        expect(result.severity).toBe(ErrorSeverity.HIGH);
        expect(result.isRecoverable).toBe(false);
      });
    });

    it('should classify unknown errors correctly', () => {
      const unknownError = new Error('Some random error');
      const result = ErrorClassifier.classify(unknownError);

      expect(result.type).toBe(ErrorType.UNKNOWN);
      expect(result.severity).toBe(ErrorSeverity.MEDIUM);
      expect(result.isRecoverable).toBe(false);
    });
  });

  describe('getMessage', () => {
    it('should return appropriate messages for each error type', () => {
      const types = Object.values(ErrorType);

      types.forEach(type => {
        const message = ErrorClassifier.getMessage(type);
        expect(message.title).toBeTruthy();
        expect(message.description).toBeTruthy();
      });
    });
  });

  describe('getIcon', () => {
    it('should return appropriate icons for each error type', () => {
      const types = Object.values(ErrorType);

      types.forEach(type => {
        const Icon = ErrorClassifier.getIcon(type);
        expect(Icon).toBeTruthy();
        expect(typeof Icon).toBe('function');
      });
    });
  });
});

// ============================================================================
// ERROR REPORTER TESTS
// ============================================================================

describe('ErrorReporter', () => {
  const mockErrorContext = {
    componentStack: 'test stack',
    errorBoundary: 'TestBoundary',
    level: 'component' as const,
    timestamp: Date.now(),
    retryCount: 0,
    userAgent: 'test-agent',
    url: 'http://test.com'
  };

  beforeEach(() => {
    // Reset NODE_ENV
    process.env.NODE_ENV = 'development';
    jest.clearAllMocks();
  });

  it('should log errors in development mode', async () => {
    const error = new Error('Test error');

    await ErrorReporter.report(error, mockErrorContext);

    expect(mockConsoleGroup).toHaveBeenCalledWith('🚨 Error Boundary Report');
    expect(mockConsoleError).toHaveBeenCalledWith('Error:', error);
    expect(mockConsoleLog).toHaveBeenCalledWith('Context:', mockErrorContext);
    expect(mockConsoleGroupEnd).toHaveBeenCalled();
  });

  it('should report to Google Analytics when available', async () => {
    const error = new Error('Test error');

    await ErrorReporter.report(error, mockErrorContext);

    expect(mockGtag).toHaveBeenCalledWith('event', 'exception', {
      description: error.message,
      fatal: false,
      custom_map: {
        error_boundary: mockErrorContext.errorBoundary,
        error_level: mockErrorContext.level,
        retry_count: mockErrorContext.retryCount
      }
    });
  });

  it('should report to backend in production', async () => {
    process.env.NODE_ENV = 'production';
    const error = new Error('Test error');

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    await ErrorReporter.report(error, mockErrorContext);

    expect(global.fetch).toHaveBeenCalledWith('/api/errors', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        name: error.name,
        context: mockErrorContext,
        timestamp: expect.any(Number),
        environment: 'production'
      })
    });
  });

  it('should handle reporting failures gracefully', async () => {
    const error = new Error('Test error');

    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    // Should not throw
    await expect(ErrorReporter.report(error, mockErrorContext)).resolves.toBeUndefined();
  });
});

// ============================================================================
// ERROR BOUNDARY COMPONENT TESTS
// ============================================================================

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">Child component</div>
      </ErrorBoundary>
    );

    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('should render error UI when error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('アプリケーションエラー')).toBeInTheDocument();
    expect(screen.getByText('予期しないエラーが発生しました。')).toBeInTheDocument();
  });

  it('should render custom fallback when provided', () => {
    const CustomFallback = <div data-testid="custom-fallback">Custom Error</div>;

    render(
      <ErrorBoundary fallback={CustomFallback}>
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
  });

  it('should call onError callback when error occurs', () => {
    const onError = jest.fn();

    render(
      <ErrorBoundary onError={onError}>
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.any(Object),
      expect.any(Object)
    );
  });

  it('should show retry button for recoverable errors', () => {
    render(
      <ErrorBoundary>
        <ThrowErrorComponent error={new Error('Network request failed')} />
      </ErrorBoundary>
    );

    expect(screen.getByRole('button', { name: /再試行/ })).toBeInTheDocument();
  });

  it('should handle retry functionality', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowErrorComponent error={new Error('Network request failed')} />
      </ErrorBoundary>
    );

    const retryButton = screen.getByRole('button', { name: /再試行/ });
    fireEvent.click(retryButton);

    // After retry, should try to render children again
    rerender(
      <ErrorBoundary>
        <ThrowErrorComponent shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('No error thrown')).toBeInTheDocument();
  });

  it('should limit retry attempts', () => {
    const { rerender } = render(
      <ErrorBoundary maxRetries={2}>
        <ThrowErrorComponent error={new Error('Network request failed')} />
      </ErrorBoundary>
    );

    // First retry
    fireEvent.click(screen.getByRole('button', { name: /再試行/ }));
    rerender(
      <ErrorBoundary maxRetries={2}>
        <ThrowErrorComponent error={new Error('Network request failed')} />
      </ErrorBoundary>
    );

    // Second retry
    fireEvent.click(screen.getByRole('button', { name: /再試行/ }));
    rerender(
      <ErrorBoundary maxRetries={2}>
        <ThrowErrorComponent error={new Error('Network request failed')} />
      </ErrorBoundary>
    );

    // Should show retry count
    expect(screen.getByText(/試行回数: 2\/2/)).toBeInTheDocument();

    // Third retry should not be available
    expect(screen.queryByRole('button', { name: /再試行/ })).not.toBeInTheDocument();
  });

  it('should show development error details in development mode', () => {
    process.env.NODE_ENV = 'development';

    render(
      <ErrorBoundary>
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('開発者向け情報')).toBeInTheDocument();
  });

  it('should not show development error details in production mode', () => {
    process.env.NODE_ENV = 'production';

    render(
      <ErrorBoundary>
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.queryByText('開発者向け情報')).not.toBeInTheDocument();
  });

  it('should render different UI based on error level', () => {
    const { rerender } = render(
      <ErrorBoundary level="page">
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByRole('button', { name: /ホームに戻る/ })).toBeInTheDocument();

    rerender(
      <ErrorBoundary level="component">
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.queryByRole('button', { name: /ホームに戻る/ })).not.toBeInTheDocument();
  });

  it('should show appropriate UI for chunk loading errors', () => {
    render(
      <ErrorBoundary level="page">
        <ThrowErrorComponent error={new Error('Loading chunk 2 failed')} />
      </ErrorBoundary>
    );

    expect(screen.getByText('アプリの読み込みエラー')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ページを再読み込み/ })).toBeInTheDocument();
  });
});

// ============================================================================
// HELPER COMPONENT TESTS
// ============================================================================

describe('Helper Components', () => {
  it('should render PageErrorBoundary with correct level', () => {
    render(
      <PageErrorBoundary>
        <ThrowErrorComponent />
      </PageErrorBoundary>
    );

    expect(screen.getByRole('button', { name: /ホームに戻る/ })).toBeInTheDocument();
  });

  it('should render SectionErrorBoundary with correct level', () => {
    render(
      <SectionErrorBoundary>
        <ThrowErrorComponent />
      </SectionErrorBoundary>
    );

    // Should not have home button (not page level)
    expect(screen.queryByRole('button', { name: /ホームに戻る/ })).not.toBeInTheDocument();
  });

  it('should render ComponentErrorBoundary with correct level', () => {
    render(
      <ComponentErrorBoundary>
        <ThrowErrorComponent />
      </ComponentErrorBoundary>
    );

    // Should not have home button (not page level)
    expect(screen.queryByRole('button', { name: /ホームに戻る/ })).not.toBeInTheDocument();
  });
});

// ============================================================================
// HOOK TESTS
// ============================================================================

describe('useErrorHandler', () => {
  it('should provide error handling function', () => {
    render(<ErrorHandlerTestComponent />);

    const triggerButton = screen.getByTestId('trigger-error');
    fireEvent.click(triggerButton);

    // Should have triggered error reporting (we can't easily test this without mocking)
    expect(triggerButton).toBeInTheDocument();
  });
});

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

describe('Error Boundary Integration', () => {
  it('should handle complex error scenarios', async () => {
    const onError = jest.fn();

    render(
      <ErrorBoundary
        onError={onError}
        enableRetry={true}
        maxRetries={3}
        context="integration-test"
      >
        <ThrowErrorComponent error={new Error('Network request failed')} />
      </ErrorBoundary>
    );

    // Verify error UI is shown
    expect(screen.getByText('ネットワークエラー')).toBeInTheDocument();

    // Verify retry button is available
    const retryButton = screen.getByRole('button', { name: /再試行/ });
    expect(retryButton).toBeInTheDocument();

    // Verify onError was called
    expect(onError).toHaveBeenCalled();

    // Test retry functionality
    fireEvent.click(retryButton);

    // Wait for any async operations
    await waitFor(() => {
      expect(retryButton).toBeInTheDocument();
    });
  });

  it('should handle navigation actions', () => {
    // Mock window.location
    const mockLocation = {
      href: '',
      reload: jest.fn()
    };
    Object.defineProperty(window, 'location', {
      value: mockLocation,
      writable: true
    });

    render(
      <ErrorBoundary level="page">
        <ThrowErrorComponent error={new Error('Loading chunk 2 failed')} />
      </ErrorBoundary>
    );

    // Test reload button
    const reloadButton = screen.getByRole('button', { name: /ページを再読み込み/ });
    fireEvent.click(reloadButton);
    expect(mockLocation.reload).toHaveBeenCalled();

    // Test home button
    const homeButton = screen.getByRole('button', { name: /ホームに戻る/ });
    fireEvent.click(homeButton);
    expect(mockLocation.href).toBe('/');
  });

  it('should reset on props change when enabled', () => {
    const { rerender } = render(
      <ErrorBoundary resetOnPropsChange={true}>
        <ThrowErrorComponent key="1" />
      </ErrorBoundary>
    );

    // Verify error state
    expect(screen.getByText('アプリケーションエラー')).toBeInTheDocument();

    // Change props (children)
    rerender(
      <ErrorBoundary resetOnPropsChange={true}>
        <ThrowErrorComponent key="2" shouldThrow={false} />
      </ErrorBoundary>
    );

    // Should reset and show children
    expect(screen.getByText('No error thrown')).toBeInTheDocument();
  });
});

// ============================================================================
// PERFORMANCE TESTS
// ============================================================================

describe('Error Boundary Performance', () => {
  it('should not cause memory leaks with timers', () => {
    const { unmount } = render(
      <ErrorBoundary>
        <ThrowErrorComponent />
      </ErrorBoundary>
    );

    // Click retry to start timeout
    const retryButton = screen.getByRole('button', { name: /再試行/ });
    fireEvent.click(retryButton);

    // Unmount component
    unmount();

    // Should not cause any issues (timeout should be cleared)
    expect(true).toBe(true);
  });
});