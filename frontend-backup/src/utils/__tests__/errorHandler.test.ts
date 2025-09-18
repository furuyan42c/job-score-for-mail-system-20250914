import {
  ApiError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NetworkError,
  BusinessLogicError,
  ErrorHandler,
  handleAxiosError,
  handlePromiseRejection,
  setupGlobalErrorHandling,
  createErrorBoundaryProps,
  withErrorHandling,
  errorHandler,
} from '../errorHandler';
import { AxiosError } from 'axios';

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

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock navigator
Object.defineProperty(navigator, 'userAgent', {
  value: 'test-user-agent',
  writable: true,
});

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000/test',
  },
  writable: true,
});

describe('Custom Error Classes', () => {
  describe('ApiError', () => {
    it('creates ApiError with correct properties', () => {
      const error = new ApiError('API failed', 404, 'NOT_FOUND', { resource: 'user' });

      expect(error.name).toBe('ApiError');
      expect(error.message).toBe('API failed');
      expect(error.status).toBe(404);
      expect(error.code).toBe('NOT_FOUND');
      expect(error.details).toEqual({ resource: 'user' });
      expect(error).toBeInstanceOf(Error);
    });
  });

  describe('ValidationError', () => {
    it('creates ValidationError with correct properties', () => {
      const error = new ValidationError('Invalid email', 'email', 'invalid@');

      expect(error.name).toBe('ValidationError');
      expect(error.message).toBe('Invalid email');
      expect(error.field).toBe('email');
      expect(error.value).toBe('invalid@');
      expect(error).toBeInstanceOf(Error);
    });
  });

  describe('AuthenticationError', () => {
    it('creates AuthenticationError with default message', () => {
      const error = new AuthenticationError();

      expect(error.name).toBe('AuthenticationError');
      expect(error.message).toBe('Authentication required');
      expect(error.redirectTo).toBeUndefined();
    });

    it('creates AuthenticationError with custom message and redirect', () => {
      const error = new AuthenticationError('Session expired', '/login');

      expect(error.message).toBe('Session expired');
      expect(error.redirectTo).toBe('/login');
    });
  });

  describe('AuthorizationError', () => {
    it('creates AuthorizationError with default message', () => {
      const error = new AuthorizationError();

      expect(error.name).toBe('AuthorizationError');
      expect(error.message).toBe('Access denied');
      expect(error.requiredPermission).toBeUndefined();
    });

    it('creates AuthorizationError with required permission', () => {
      const error = new AuthorizationError('Admin access required', 'admin');

      expect(error.message).toBe('Admin access required');
      expect(error.requiredPermission).toBe('admin');
    });
  });

  describe('NetworkError', () => {
    it('creates NetworkError with default message', () => {
      const error = new NetworkError();

      expect(error.name).toBe('NetworkError');
      expect(error.message).toBe('Network connection failed');
      expect(error.offline).toBe(false);
    });

    it('creates NetworkError with offline status', () => {
      const error = new NetworkError('You are offline', true);

      expect(error.message).toBe('You are offline');
      expect(error.offline).toBe(true);
    });
  });

  describe('BusinessLogicError', () => {
    it('creates BusinessLogicError with error code', () => {
      const error = new BusinessLogicError('Insufficient funds', 'INSUFFICIENT_FUNDS');

      expect(error.name).toBe('BusinessLogicError');
      expect(error.message).toBe('Insufficient funds');
      expect(error.errorCode).toBe('INSUFFICIENT_FUNDS');
    });
  });
});

describe('ErrorHandler', () => {
  let errorHandlerInstance: ErrorHandler;

  beforeEach(() => {
    errorHandlerInstance = ErrorHandler.getInstance();
    errorHandlerInstance.clearQueue();
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockImplementation((key: string) => {
      if (key === 'userId') return 'test-user-123';
      if (key === 'sessionId') return 'session-456';
      return null;
    });
  });

  describe('getInstance', () => {
    it('returns singleton instance', () => {
      const instance1 = ErrorHandler.getInstance();
      const instance2 = ErrorHandler.getInstance();

      expect(instance1).toBe(instance2);
    });
  });

  describe('handleError', () => {
    it('handles Error objects correctly', () => {
      const error = new Error('Test error');
      const errorReport = errorHandlerInstance.handleError(error);

      expect(errorReport.type).toBe('UNKNOWN_ERROR');
      expect(errorReport.message).toBe('Test error');
      expect(errorReport.stack).toBe(error.stack);
      expect(errorReport.severity).toBe('medium');
      expect(errorReport.context.timestamp).toBeDefined();
      expect(errorReport.context.url).toBe('http://localhost:3000/test');
      expect(errorReport.context.userAgent).toBe('test-user-agent');
      expect(errorReport.context.userId).toBe('test-user-123');
    });

    it('handles custom error types correctly', () => {
      const apiError = new ApiError('API failed', 500, 'INTERNAL_ERROR');
      const errorReport = errorHandlerInstance.handleError(apiError);

      expect(errorReport.type).toBe('API_ERROR');
      expect(errorReport.severity).toBe('critical');
    });

    it('handles non-Error objects', () => {
      const errorReport = errorHandlerInstance.handleError('String error');

      expect(errorReport.type).toBe('UNKNOWN_ERROR');
      expect(errorReport.message).toBe('String error');
      expect(errorReport.stack).toBeUndefined();
    });

    it('includes custom context', () => {
      const error = new Error('Test error');
      const customContext = {
        component: 'TestComponent',
        action: 'submit_form',
      };

      const errorReport = errorHandlerInstance.handleError(error, customContext);

      expect(errorReport.context.component).toBe('TestComponent');
      expect(errorReport.context.action).toBe('submit_form');
    });

    it('logs error to console in development', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      const error = new Error('Test error');
      errorHandlerInstance.handleError(error);

      expect(console.group).toHaveBeenCalled();
      expect(console.log).toHaveBeenCalled();

      process.env.NODE_ENV = originalEnv;
    });
  });

  describe('error type detection', () => {
    it('correctly identifies API errors', () => {
      const apiError = new ApiError('API failed', 404, 'NOT_FOUND');
      const errorReport = errorHandlerInstance.handleError(apiError);

      expect(errorReport.type).toBe('API_ERROR');
    });

    it('correctly identifies validation errors', () => {
      const validationError = new ValidationError('Invalid input', 'email');
      const errorReport = errorHandlerInstance.handleError(validationError);

      expect(errorReport.type).toBe('VALIDATION_ERROR');
    });

    it('correctly identifies chunk load errors', () => {
      const chunkError = new Error('Loading chunk 2 failed');
      chunkError.name = 'ChunkLoadError';
      const errorReport = errorHandlerInstance.handleError(chunkError);

      expect(errorReport.type).toBe('NETWORK_ERROR');
    });

    it('correctly identifies network errors by message', () => {
      const networkError = new Error('Network Error: Failed to fetch');
      const errorReport = errorHandlerInstance.handleError(networkError);

      expect(errorReport.type).toBe('NETWORK_ERROR');
    });
  });

  describe('error severity detection', () => {
    it('assigns correct severity to API errors', () => {
      const serverError = new ApiError('Server error', 500, 'INTERNAL_ERROR');
      const clientError = new ApiError('Not found', 404, 'NOT_FOUND');
      const infoError = new ApiError('Moved', 301, 'MOVED');

      expect(errorHandlerInstance.handleError(serverError).severity).toBe('critical');
      expect(errorHandlerInstance.handleError(clientError).severity).toBe('medium');
      expect(errorHandlerInstance.handleError(infoError).severity).toBe('low');
    });

    it('assigns high severity to auth errors', () => {
      const authError = new AuthenticationError();
      const authzError = new AuthorizationError();

      expect(errorHandlerInstance.handleError(authError).severity).toBe('high');
      expect(errorHandlerInstance.handleError(authzError).severity).toBe('high');
    });

    it('assigns correct severity to network errors', () => {
      const offlineError = new NetworkError('Offline', true);
      const networkError = new NetworkError('Connection failed', false);

      expect(errorHandlerInstance.handleError(offlineError).severity).toBe('critical');
      expect(errorHandlerInstance.handleError(networkError).severity).toBe('high');
    });
  });

  describe('error queue management', () => {
    it('adds errors to queue', () => {
      const error = new Error('Test error');
      errorHandlerInstance.handleError(error);

      const queuedErrors = errorHandlerInstance.getQueuedErrors();
      expect(queuedErrors).toHaveLength(1);
      expect(queuedErrors[0].message).toBe('Test error');
    });

    it('maintains queue size limit', () => {
      // Add more than max queue size
      for (let i = 0; i < 105; i++) {
        errorHandlerInstance.handleError(new Error(`Error ${i}`));
      }

      const queuedErrors = errorHandlerInstance.getQueuedErrors();
      expect(queuedErrors).toHaveLength(100); // max queue size
    });

    it('clears queue', () => {
      errorHandlerInstance.handleError(new Error('Test error'));
      expect(errorHandlerInstance.getQueuedErrors()).toHaveLength(1);

      errorHandlerInstance.clearQueue();
      expect(errorHandlerInstance.getQueuedErrors()).toHaveLength(0);
    });

    it('marks errors as recovered', () => {
      const errorReport = errorHandlerInstance.handleError(new Error('Test error'));
      expect(errorReport.recovered).toBe(false);

      errorHandlerInstance.markAsRecovered(errorReport.id);

      const queuedErrors = errorHandlerInstance.getQueuedErrors();
      expect(queuedErrors[0].recovered).toBe(true);
    });
  });

  describe('error reporting', () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockClear();
    });

    it('skips reporting in development', async () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      errorHandlerInstance.handleError(new Error('Test error'));

      // Wait for async reporting
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(global.fetch).not.toHaveBeenCalled();

      process.env.NODE_ENV = originalEnv;
    });

    it('reports errors in production', async () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      errorHandlerInstance.handleError(new Error('Test error'));

      // Wait for async reporting
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(global.fetch).toHaveBeenCalledWith('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('Test error'),
      });

      process.env.NODE_ENV = originalEnv;
    });

    it('handles reporting failures gracefully', async () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network failed'));

      // Should not throw
      expect(() => {
        errorHandlerInstance.handleError(new Error('Test error'));
      }).not.toThrow();

      process.env.NODE_ENV = originalEnv;
    });
  });
});

describe('Axios Error Handler', () => {
  it('handles response errors', () => {
    const axiosError = {
      response: {
        status: 404,
        data: { message: 'User not found', code: 'USER_NOT_FOUND' },
      },
      message: 'Request failed with status code 404',
      config: {},
      isAxiosError: true,
    } as AxiosError;

    const apiError = handleAxiosError(axiosError);

    expect(apiError).toBeInstanceOf(ApiError);
    expect(apiError.message).toBe('User not found');
    expect(apiError.status).toBe(404);
    expect(apiError.code).toBe('USER_NOT_FOUND');
  });

  it('handles request errors', () => {
    const axiosError = {
      request: {},
      message: 'Network Error',
      config: {},
      isAxiosError: true,
    } as AxiosError;

    const networkError = handleAxiosError(axiosError);

    expect(networkError).toBeInstanceOf(NetworkError);
    expect(networkError.message).toBe('No response from server');
  });

  it('handles setup errors', () => {
    const axiosError = {
      message: 'Request setup failed',
      config: {},
      isAxiosError: true,
    } as AxiosError;

    const apiError = handleAxiosError(axiosError);

    expect(apiError).toBeInstanceOf(ApiError);
    expect(apiError.message).toBe('Request setup failed');
    expect(apiError.code).toBe('REQUEST_SETUP_ERROR');
  });
});

describe('Promise Rejection Handler', () => {
  it('handles promise rejections', () => {
    const error = new Error('Promise rejected');

    expect(() => {
      handlePromiseRejection(error);
    }).not.toThrow();

    // Verify error was handled
    const queuedErrors = errorHandler.getQueuedErrors();
    expect(queuedErrors.some(e => e.message === 'Promise rejected')).toBe(true);
  });
});

describe('Global Error Handling Setup', () => {
  let addEventListenerSpy: jest.SpyInstance;

  beforeEach(() => {
    addEventListenerSpy = jest.spyOn(window, 'addEventListener');
  });

  afterEach(() => {
    addEventListenerSpy.mockRestore();
  });

  it('sets up global error handlers', () => {
    setupGlobalErrorHandling();

    expect(addEventListenerSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));
    expect(addEventListenerSpy).toHaveBeenCalledWith('error', expect.any(Function));
  });
});

describe('Error Boundary Props Creator', () => {
  it('creates error boundary props with onError handler', () => {
    const props = createErrorBoundaryProps('TestComponent');

    expect(props.onError).toBeInstanceOf(Function);

    // Test the onError function
    const error = new Error('Test error');
    const errorInfo = { componentStack: 'Component stack' };
    const errorId = 'test-error-id';

    props.onError(error, errorInfo, errorId);

    const queuedErrors = errorHandler.getQueuedErrors();
    expect(queuedErrors.some(e => e.message === 'Test error')).toBe(true);
  });
});

describe('withErrorHandling HOF', () => {
  it('wraps synchronous functions', () => {
    const fn = jest.fn().mockReturnValue('success');
    const wrappedFn = withErrorHandling(fn, { component: 'TestComponent' });

    const result = wrappedFn('arg1', 'arg2');

    expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
    expect(result).toBe('success');
  });

  it('catches synchronous errors', () => {
    const fn = jest.fn().mockImplementation(() => {
      throw new Error('Sync error');
    });
    const wrappedFn = withErrorHandling(fn);

    expect(() => wrappedFn()).toThrow('Sync error');

    // Verify error was handled
    const queuedErrors = errorHandler.getQueuedErrors();
    expect(queuedErrors.some(e => e.message === 'Sync error')).toBe(true);
  });

  it('wraps asynchronous functions', async () => {
    const fn = jest.fn().mockResolvedValue('async success');
    const wrappedFn = withErrorHandling(fn);

    const result = await wrappedFn();

    expect(result).toBe('async success');
  });

  it('catches asynchronous errors', async () => {
    const fn = jest.fn().mockRejectedValue(new Error('Async error'));
    const wrappedFn = withErrorHandling(fn);

    await expect(wrappedFn()).rejects.toThrow('Async error');

    // Verify error was handled
    const queuedErrors = errorHandler.getQueuedErrors();
    expect(queuedErrors.some(e => e.message === 'Async error')).toBe(true);
  });

  it('includes custom context in error reports', () => {
    const fn = jest.fn().mockImplementation(() => {
      throw new Error('Context error');
    });
    const wrappedFn = withErrorHandling(fn, { component: 'TestComponent' });

    expect(() => wrappedFn()).toThrow('Context error');

    const queuedErrors = errorHandler.getQueuedErrors();
    const errorReport = queuedErrors.find(e => e.message === 'Context error');
    expect(errorReport?.context.component).toBe('TestComponent');
  });
});

describe('Edge Cases', () => {
  it('handles null and undefined errors', () => {
    const nullReport = errorHandler.handleError(null);
    const undefinedReport = errorHandler.handleError(undefined);

    expect(nullReport.message).toBe('null');
    expect(undefinedReport.message).toBe('undefined');
    expect(nullReport.type).toBe('UNKNOWN_ERROR');
    expect(undefinedReport.type).toBe('UNKNOWN_ERROR');
  });

  it('handles errors without stack traces', () => {
    const error = new Error('No stack');
    delete error.stack;

    const errorReport = errorHandler.handleError(error);

    expect(errorReport.stack).toBeUndefined();
    expect(errorReport.message).toBe('No stack');
  });

  it('handles server-side environment', () => {
    // Mock server-side environment
    const originalWindow = global.window;
    const originalNavigator = global.navigator;
    const originalLocalStorage = global.localStorage;

    // @ts-ignore
    delete global.window;
    // @ts-ignore
    delete global.navigator;
    // @ts-ignore
    delete global.localStorage;

    const error = new Error('Server error');
    const errorReport = errorHandler.handleError(error);

    expect(errorReport.context.url).toBe('');
    expect(errorReport.context.userAgent).toBe('');
    expect(errorReport.context.userId).toBeUndefined();

    // Restore globals
    global.window = originalWindow;
    global.navigator = originalNavigator;
    global.localStorage = originalLocalStorage;
  });
});