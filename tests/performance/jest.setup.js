/**
 * Jest setup file for performance tests
 */

// Global test timeout for performance tests (10 minutes default)
jest.setTimeout(600000);

// Mock console methods to reduce noise during tests
const originalConsoleLog = console.log;
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

// Only show errors and warnings during tests, suppress info logs
console.log = jest.fn();
console.warn = originalConsoleWarn;
console.error = originalConsoleError;

// Restore console.log for specific test debugging if needed
global.enableConsoleLog = () => {
  console.log = originalConsoleLog;
};

// Global beforeAll setup
beforeAll(async () => {
  // Set environment variables for tests
  process.env.NODE_ENV = 'test';
  process.env.API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

  // Enable garbage collection for memory tests
  if (global.gc) {
    global.gc();
  }
});

// Global afterAll cleanup
afterAll(async () => {
  // Force garbage collection after tests
  if (global.gc) {
    global.gc();
  }

  // Small delay to ensure cleanup
  await new Promise(resolve => setTimeout(resolve, 1000));
});

// Handle unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});

// Performance test utilities
global.performanceTestUtils = {
  // Wait for a condition to be true
  waitFor: async (condition, timeout = 30000) => {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      if (await condition()) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    throw new Error(`Timeout waiting for condition after ${timeout}ms`);
  },

  // Generate random test data
  generateRandomString: (length = 10) => {
    return Math.random().toString(36).substring(2, 2 + length);
  },

  // Memory usage helper
  getMemoryUsage: () => {
    const usage = process.memoryUsage();
    return {
      rss: Math.round(usage.rss / 1024 / 1024), // MB
      heapTotal: Math.round(usage.heapTotal / 1024 / 1024), // MB
      heapUsed: Math.round(usage.heapUsed / 1024 / 1024), // MB
      external: Math.round(usage.external / 1024 / 1024), // MB
    };
  },

  // Performance measurement helper
  measurePerformance: async (fn, name = 'operation') => {
    const startTime = process.hrtime.bigint();
    const startMemory = process.memoryUsage();

    const result = await fn();

    const endTime = process.hrtime.bigint();
    const endMemory = process.memoryUsage();

    const duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds
    const memoryDelta = {
      rss: endMemory.rss - startMemory.rss,
      heapUsed: endMemory.heapUsed - startMemory.heapUsed,
    };

    return {
      result,
      metrics: {
        duration,
        memoryDelta,
        name,
      }
    };
  }
};