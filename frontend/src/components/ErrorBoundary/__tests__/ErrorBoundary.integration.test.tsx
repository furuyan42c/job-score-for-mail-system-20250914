import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary from '../index';
import { errorHandler, ApiError, NetworkError } from '../../utils/errorHandler';

// Mock console methods
const originalConsoleError = console.error;
const originalConsoleGroup = console.group;
const originalConsoleGroupEnd = console.groupEnd;
const originalConsoleLog = console.log;

beforeAll(() => {
  console.error = jest.fn();
  console.group = jest.fn();
  console.groupEnd = jest.fn();
  console.log = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
  console.group = originalConsoleGroup;
  console.groupEnd = originalConsoleGroupEnd;
  console.log = originalConsoleLog;
});

// Mock fetch for error reporting
global.fetch = jest.fn();

// Component that simulates real-world error scenarios
const ApiComponent: React.FC<{ endpoint: string; shouldFail?: boolean }> = ({
  endpoint,
  shouldFail = false,
}) => {
  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        if (shouldFail) {
          if (endpoint === '/api/auth') {
            throw new ApiError('Unauthorized', 401, 'UNAUTHORIZED');
          } else if (endpoint === '/api/network') {
            throw new NetworkError('Connection failed');
          } else {
            throw new Error('Unexpected error occurred');
          }
        }

        // Simulate successful API call
        setData({ message: `Data from ${endpoint}` });
      } catch (error) {
        // Re-throw to be caught by ErrorBoundary
        throw error;
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint, shouldFail]);

  if (loading) {
    return <div data-testid="loading">Loading...</div>;
  }

  return <div data-testid="api-data">{data?.message}</div>;
};

// Component that uses async operations
const AsyncComponent: React.FC<{ shouldReject?: boolean }> = ({ shouldReject = false }) => {
  const [result, setResult] = React.useState<string>('');

  const handleAsyncOperation = async () => {
    try {
      const promise = new Promise((resolve, reject) => {
        setTimeout(() => {
          if (shouldReject) {
            reject(new Error('Async operation failed'));
          } else {
            resolve('Async operation succeeded');
          }
        }, 100);
      });

      const result = await promise;
      setResult(result as string);
    } catch (error) {
      // Use error handler to process the error
      errorHandler.handleError(error, {
        component: 'AsyncComponent',
        action: 'async_operation',
      });
      throw error; // Re-throw to be caught by ErrorBoundary
    }
  };

  React.useEffect(() => {
    handleAsyncOperation();
  }, [shouldReject]);

  return <div data-testid="async-result">{result}</div>;
};

// Component that handles form validation
const FormComponent: React.FC<{ invalidData?: boolean }> = ({ invalidData = false }) => {
  const [formData, setFormData] = React.useState({ email: '', password: '' });

  const validateForm = () => {
    if (invalidData) {
      if (!formData.email.includes('@')) {
        const validationError = new Error('Invalid email format');
        validationError.name = 'ValidationError';
        throw validationError;
      }
    }
    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      validateForm();
      // Form is valid
    } catch (error) {
      errorHandler.handleError(error, {
        component: 'FormComponent',
        action: 'form_validation',
      });
      throw error;
    }
  };

  React.useEffect(() => {
    if (invalidData) {
      setFormData({ email: 'invalid-email', password: 'test' });
      // Trigger validation on mount
      try {
        validateForm();
      } catch (error) {
        throw error;
      }
    }
  }, [invalidData]);

  return (
    <form onSubmit={handleSubmit} data-testid="form">
      <input
        type="email"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        data-testid="email-input"
      />
      <button type="submit" data-testid="submit-button">
        Submit
      </button>
    </form>
  );
};

describe('ErrorBoundary Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    errorHandler.clearQueue();
    (global.fetch as jest.Mock).mockClear();
  });

  describe('API Error Scenarios', () => {
    it('handles authentication errors gracefully', async () => {
      render(
        <ErrorBoundary level="page">
          <ApiComponent endpoint="/api/auth" shouldFail />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Authentication error/)).toBeInTheDocument();
      });

      expect(screen.getByText('Try Again')).toBeInTheDocument();
      expect(screen.getByText('Go to Home')).toBeInTheDocument();

      // Verify error was logged
      const queuedErrors = errorHandler.getQueuedErrors();
      expect(queuedErrors).toHaveLength(1);
      expect(queuedErrors[0].type).toBe('API_ERROR');
      expect(queuedErrors[0].severity).toBe('critical');
    });

    it('handles network errors with appropriate messaging', async () => {
      render(
        <ErrorBoundary>
          <ApiComponent endpoint="/api/network" shouldFail />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Network connection issue/)).toBeInTheDocument();
      });

      // Verify network error was categorized correctly
      const queuedErrors = errorHandler.getQueuedErrors();
      expect(queuedErrors[0].type).toBe('NETWORK_ERROR');
      expect(queuedErrors[0].severity).toBe('high');
    });
  });

  describe('Async Operation Error Handling', () => {
    it('catches and displays async operation failures', async () => {
      render(
        <ErrorBoundary>
          <AsyncComponent shouldReject />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      });

      // Verify async error context was captured
      const queuedErrors = errorHandler.getQueuedErrors();
      const asyncError = queuedErrors.find(e => e.context.component === 'AsyncComponent');
      expect(asyncError).toBeDefined();
      expect(asyncError?.context.action).toBe('async_operation');
    });

    it('allows successful async operations to complete', async () => {
      render(
        <ErrorBoundary>
          <AsyncComponent shouldReject={false} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Async operation succeeded')).toBeInTheDocument();
      });

      // No errors should be logged
      expect(errorHandler.getQueuedErrors()).toHaveLength(0);
    });
  });

  describe('Form Validation Error Handling', () => {
    it('handles validation errors in forms', async () => {
      render(
        <ErrorBoundary>
          <FormComponent invalidData />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/Invalid data detected/)).toBeInTheDocument();
      });

      // Verify validation error context
      const queuedErrors = errorHandler.getQueuedErrors();
      const validationError = queuedErrors.find(e => e.context.component === 'FormComponent');
      expect(validationError).toBeDefined();
      expect(validationError?.context.action).toBe('form_validation');
    });
  });

  describe('Error Recovery and Retry', () => {
    it('allows recovery after fixing the underlying issue', async () => {
      let shouldFail = true;

      const RecoverableComponent = () => {
        if (shouldFail) {
          throw new Error('Temporary error');
        }
        return <div data-testid="recovered">Component recovered</div>;
      };

      render(
        <ErrorBoundary>
          <RecoverableComponent />
        </ErrorBoundary>
      );

      // Initially shows error
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Fix the issue
      shouldFail = false;

      // Click retry
      fireEvent.click(screen.getByText(/Try Again/));

      await waitFor(() => {
        expect(screen.getByTestId('recovered')).toBeInTheDocument();
      });

      // Error should be marked as recovered
      const queuedErrors = errorHandler.getQueuedErrors();
      expect(queuedErrors.some(e => e.recovered)).toBe(true);
    });

    it('tracks retry attempts correctly', () => {
      render(
        <ErrorBoundary>
          <div>{(() => { throw new Error('Test error'); })()}</div>
        </ErrorBoundary>
      );

      expect(screen.getByText(/3 attempts left/)).toBeInTheDocument();

      fireEvent.click(screen.getByText(/Try Again/));
      expect(screen.getByText(/2 attempts left/)).toBeInTheDocument();

      fireEvent.click(screen.getByText(/Try Again/));
      expect(screen.getByText(/1 attempts left/)).toBeInTheDocument();

      fireEvent.click(screen.getByText(/Try Again/));
      expect(screen.queryByText(/Try Again/)).not.toBeInTheDocument();
    });
  });

  describe('Multiple Error Boundary Levels', () => {
    it('handles nested error boundaries correctly', () => {
      const ComponentLevelError = () => {
        throw new Error('Component level error');
      };

      render(
        <ErrorBoundary level="global">
          <div>
            <h1>App Level</h1>
            <ErrorBoundary level="page">
              <div>
                <h2>Page Level</h2>
                <ErrorBoundary level="component">
                  <ComponentLevelError />
                </ErrorBoundary>
              </div>
            </ErrorBoundary>
          </div>
        </ErrorBoundary>
      );

      // Component level error boundary should catch the error
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText('App Level')).toBeInTheDocument();
      expect(screen.getByText('Page Level')).toBeInTheDocument();
    });

    it('escalates to parent boundary when child boundary fails', () => {
      const ProblematicErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
        // Simulate an error boundary that itself has an error
        throw new Error('Error boundary failed');
      };

      render(
        <ErrorBoundary level="global">
          <ProblematicErrorBoundary>
            <div>This should not render</div>
          </ProblematicErrorBoundary>
        </ErrorBoundary>
      );

      expect(screen.getByText('Application Error')).toBeInTheDocument();
    });
  });

  describe('Error Context and Metadata', () => {
    it('captures comprehensive error context', () => {
      const ContextualComponent = () => {
        throw new Error('Contextual error');
      };

      render(
        <ErrorBoundary
          onError={(error, errorInfo, errorId) => {
            errorHandler.handleError(error, {
              component: 'ContextualComponent',
              action: 'render',
              metadata: {
                props: { test: 'value' },
                state: { loaded: true },
              },
            });
          }}
        >
          <ContextualComponent />
        </ErrorBoundary>
      );

      const queuedErrors = errorHandler.getQueuedErrors();
      const contextualError = queuedErrors.find(e => e.context.component === 'ContextualComponent');

      expect(contextualError).toBeDefined();
      expect(contextualError?.context.action).toBe('render');
      expect(contextualError?.context.metadata).toEqual({
        props: { test: 'value' },
        state: { loaded: true },
      });
    });
  });

  describe('Performance and Memory', () => {
    it('maintains error queue size limits', () => {
      const ErrorGeneratingComponent = ({ errorNumber }: { errorNumber: number }) => {
        throw new Error(`Error ${errorNumber}`);
      };

      // Generate more errors than the queue limit
      for (let i = 0; i < 105; i++) {
        render(
          <ErrorBoundary key={i}>
            <ErrorGeneratingComponent errorNumber={i} />
          </ErrorBoundary>
        );
      }

      const queuedErrors = errorHandler.getQueuedErrors();
      expect(queuedErrors).toHaveLength(100); // Should not exceed max queue size
    });

    it('cleans up error references when needed', () => {
      const TestError = () => {
        throw new Error('Memory test error');
      };

      render(
        <ErrorBoundary>
          <TestError />
        </ErrorBoundary>
      );

      expect(errorHandler.getQueuedErrors()).toHaveLength(1);

      // Clear queue to free memory
      errorHandler.clearQueue();
      expect(errorHandler.getQueuedErrors()).toHaveLength(0);
    });
  });

  describe('Dark Mode and Accessibility', () => {
    it('renders correctly in dark mode', () => {
      render(
        <div className="dark">
          <ErrorBoundary>
            <div>{(() => { throw new Error('Dark mode test'); })()}</div>
          </ErrorBoundary>
        </div>
      );

      const errorContainer = screen.getByText('Something went wrong').closest('div');
      expect(errorContainer).toHaveClass('dark:bg-gray-800');
    });

    it('maintains accessibility standards', () => {
      render(
        <ErrorBoundary>
          <div>{(() => { throw new Error('Accessibility test'); })()}</div>
        </ErrorBoundary>
      );

      // Check for proper button accessibility
      const retryButton = screen.getByRole('button', { name: /Try Again/ });
      expect(retryButton).toBeInTheDocument();
      expect(retryButton).not.toHaveAttribute('aria-disabled');

      const homeButton = screen.getByRole('button', { name: /Go to Home/ });
      expect(homeButton).toBeInTheDocument();

      const reloadButton = screen.getByRole('button', { name: /Reload Page/ });
      expect(reloadButton).toBeInTheDocument();
    });
  });

  describe('Error Reporting Integration', () => {
    it('reports errors to external service in production', async () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      render(
        <ErrorBoundary>
          <div>{(() => { throw new Error('Production error'); })()}</div>
        </ErrorBoundary>
      );

      // Wait for async error reporting
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/errors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('Production error'),
        });
      });

      process.env.NODE_ENV = originalEnv;
    });
  });
});