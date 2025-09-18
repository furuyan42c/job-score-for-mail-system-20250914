import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary, { useErrorBoundary, withErrorBoundary } from '../index';

// Mock console methods to avoid noise in tests
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

// Mock window.location
const mockLocation = {
  href: 'http://localhost:3000/test',
  reload: jest.fn(),
};

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Component that throws an error
const ThrowErrorComponent: React.FC<{ shouldThrow?: boolean; errorType?: string }> = ({
  shouldThrow = false,
  errorType = 'generic',
}) => {
  if (shouldThrow) {
    switch (errorType) {
      case 'chunk':
        const chunkError = new Error('Loading chunk 2 failed');
        chunkError.name = 'ChunkLoadError';
        throw chunkError;
      case 'network':
        throw new Error('Network Error: Failed to fetch');
      case 'auth':
        const authError = new Error('User not authenticated');
        authError.name = 'Authentication';
        throw authError;
      case 'validation':
        const validationError = new Error('Invalid input data');
        validationError.name = 'ValidationError';
        throw validationError;
      default:
        throw new Error('Test error');
    }
  }
  return <div data-testid="success-component">Success Component</div>;
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockImplementation((key: string) => {
      if (key === 'userId') return 'test-user-123';
      if (key === 'sessionId') return 'session-456';
      return null;
    });
  });

  describe('when no error occurs', () => {
    it('renders children normally', () => {
      render(
        <ErrorBoundary>
          <ThrowErrorComponent />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('success-component')).toBeInTheDocument();
    });
  });

  describe('when an error occurs', () => {
    it('catches errors and displays error UI', () => {
      render(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText(/An unexpected error occurred/)).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
      expect(screen.getByText('Reload Page')).toBeInTheDocument();
      expect(screen.getByText('Go to Home')).toBeInTheDocument();
    });

    it('displays specific error messages for different error types', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow errorType="chunk" />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Failed to load application resources/)).toBeInTheDocument();

      rerender(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow errorType="network" />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Network connection issue/)).toBeInTheDocument();

      rerender(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow errorType="auth" />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Authentication error/)).toBeInTheDocument();

      rerender(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow errorType="validation" />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Invalid data detected/)).toBeInTheDocument();
    });

    it('calls onError callback when provided', () => {
      const onErrorMock = jest.fn();

      render(
        <ErrorBoundary onError={onErrorMock}>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      expect(onErrorMock).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        }),
        expect.any(String)
      );
    });

    it('shows different title for global error boundary', () => {
      render(
        <ErrorBoundary level="global">
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      expect(screen.getByText('Application Error')).toBeInTheDocument();
    });

    it('handles retry functionality', async () => {
      let shouldThrow = true;
      const TestComponent = () => {
        if (shouldThrow) {
          throw new Error('Test error');
        }
        return <div data-testid="success-after-retry">Success after retry</div>;
      };

      render(
        <ErrorBoundary>
          <TestComponent />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Simulate fixing the error
      shouldThrow = false;

      // Click retry button
      fireEvent.click(screen.getByText(/Try Again/));

      await waitFor(() => {
        expect(screen.getByTestId('success-after-retry')).toBeInTheDocument();
      });
    });

    it('disables retry button after max retries', () => {
      render(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      // Click retry 3 times (max retries)
      const retryButton = screen.getByText(/Try Again/);

      fireEvent.click(retryButton);
      expect(screen.getByText(/2 attempts left/)).toBeInTheDocument();

      fireEvent.click(screen.getByText(/Try Again/));
      expect(screen.getByText(/1 attempts left/)).toBeInTheDocument();

      fireEvent.click(screen.getByText(/Try Again/));

      // After max retries, button should be disabled
      expect(screen.queryByText(/Try Again/)).not.toBeInTheDocument();
    });

    it('handles reload page button', () => {
      render(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      fireEvent.click(screen.getByText('Reload Page'));

      expect(mockLocation.reload).toHaveBeenCalled();
    });

    it('handles go to home button', () => {
      render(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      fireEvent.click(screen.getByText('Go to Home'));

      expect(mockLocation.href).toBe('/');
    });
  });

  describe('error details', () => {
    it('shows error details in development mode', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary showDetails>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Technical Details/)).toBeInTheDocument();

      process.env.NODE_ENV = originalEnv;
    });

    it('hides error details in production mode', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      render(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      expect(screen.queryByText(/Technical Details/)).not.toBeInTheDocument();

      process.env.NODE_ENV = originalEnv;
    });

    it('expands error details when clicked', () => {
      render(
        <ErrorBoundary showDetails>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      const detailsElement = screen.getByText(/Technical Details/);
      fireEvent.click(detailsElement);

      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  describe('custom fallback', () => {
    it('renders custom fallback when provided', () => {
      const customFallback = <div data-testid="custom-fallback">Custom Error UI</div>;

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });
  });

  describe('error reporting', () => {
    it('logs error details to console in development', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      );

      expect(console.group).toHaveBeenCalledWith(
        expect.stringContaining('Error Boundary Caught Error')
      );
      expect(console.error).toHaveBeenCalledWith('Error:', expect.any(Error));

      process.env.NODE_ENV = originalEnv;
    });
  });
});

describe('useErrorBoundary hook', () => {
  const TestComponent: React.FC<{ triggerError?: boolean }> = ({ triggerError = false }) => {
    const { captureError, resetError } = useErrorBoundary();

    React.useEffect(() => {
      if (triggerError) {
        captureError(new Error('Hook triggered error'));
      }
    }, [triggerError, captureError]);

    return (
      <div>
        <button onClick={() => captureError(new Error('Button clicked error'))}>
          Trigger Error
        </button>
        <button onClick={resetError}>Reset Error</button>
        <div data-testid="hook-component">Hook Component</div>
      </div>
    );
  };

  it('provides error capture functionality', () => {
    render(
      <ErrorBoundary>
        <TestComponent />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('hook-component')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Trigger Error'));

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('triggers error on component mount', () => {
    render(
      <ErrorBoundary>
        <TestComponent triggerError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });
});

describe('withErrorBoundary HOC', () => {
  const TestComponent: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow = false }) => {
    if (shouldThrow) {
      throw new Error('HOC component error');
    }
    return <div data-testid="hoc-component">HOC Component</div>;
  };

  it('wraps component with error boundary', () => {
    const WrappedComponent = withErrorBoundary(TestComponent);

    render(<WrappedComponent />);

    expect(screen.getByTestId('hoc-component')).toBeInTheDocument();
  });

  it('catches errors in wrapped component', () => {
    const WrappedComponent = withErrorBoundary(TestComponent);

    render(<WrappedComponent shouldThrow />);

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('passes props to wrapped component', () => {
    const WrappedComponent = withErrorBoundary(TestComponent, {
      level: 'component',
    });

    render(<WrappedComponent />);

    expect(screen.getByTestId('hoc-component')).toBeInTheDocument();
  });

  it('sets correct display name', () => {
    const TestComponentWithName = () => <div>Test</div>;
    TestComponentWithName.displayName = 'TestComponentWithName';

    const WrappedComponent = withErrorBoundary(TestComponentWithName);

    expect(WrappedComponent.displayName).toBe('withErrorBoundary(TestComponentWithName)');
  });
});

describe('accessibility', () => {
  it('has proper ARIA attributes', () => {
    render(
      <ErrorBoundary>
        <ThrowErrorComponent shouldThrow />
      </ErrorBoundary>
    );

    const alertElement = screen.getByRole('button', { name: /Try Again/ });
    expect(alertElement).toBeInTheDocument();
  });

  it('maintains focus management', () => {
    render(
      <ErrorBoundary>
        <ThrowErrorComponent shouldThrow />
      </ErrorBoundary>
    );

    const retryButton = screen.getByText(/Try Again/);
    retryButton.focus();
    expect(document.activeElement).toBe(retryButton);
  });
});

describe('responsive design', () => {
  it('renders properly on different screen sizes', () => {
    render(
      <ErrorBoundary>
        <ThrowErrorComponent shouldThrow />
      </ErrorBoundary>
    );

    const container = screen.getByText('Something went wrong').closest('div');
    expect(container).toHaveClass('max-w-md');
  });
});

describe('dark mode support', () => {
  it('applies dark mode classes', () => {
    render(
      <div className="dark">
        <ErrorBoundary>
          <ThrowErrorComponent shouldThrow />
        </ErrorBoundary>
      </div>
    );

    const errorContainer = screen.getByText('Something went wrong').closest('div');
    expect(errorContainer).toHaveClass('dark:bg-gray-800');
  });
});