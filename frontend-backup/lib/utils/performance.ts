/**
 * Performance Optimization Utilities
 * Tools for monitoring and optimizing application performance
 */

import React from 'react';
import { NextRequest, NextResponse } from 'next/server';

// Performance monitoring
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Map<string, number[]> = new Map();

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Start performance measurement
   */
  start(label: string): () => void {
    const startTime = performance.now();

    return () => {
      const duration = performance.now() - startTime;
      this.recordMetric(label, duration);
    };
  }

  /**
   * Record a performance metric
   */
  recordMetric(label: string, value: number): void {
    if (!this.metrics.has(label)) {
      this.metrics.set(label, []);
    }

    const values = this.metrics.get(label)!;
    values.push(value);

    // Keep only last 100 measurements
    if (values.length > 100) {
      values.shift();
    }
  }

  /**
   * Get performance metrics
   */
  getMetrics(label: string): {
    count: number;
    average: number;
    min: number;
    max: number;
    p95: number;
  } | null {
    const values = this.metrics.get(label);
    if (!values || values.length === 0) return null;

    const sorted = [...values].sort((a, b) => a - b);
    const sum = values.reduce((acc, val) => acc + val, 0);

    return {
      count: values.length,
      average: sum / values.length,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      p95: sorted[Math.floor(sorted.length * 0.95)],
    };
  }

  /**
   * Get all metrics
   */
  getAllMetrics(): Record<string, ReturnType<typeof this.getMetrics>> {
    const result: Record<string, ReturnType<typeof this.getMetrics>> = {};

    for (const label of this.metrics.keys()) {
      result[label] = this.getMetrics(label);
    }

    return result;
  }
}

/**
 * HOC for measuring component render time
 */
export function withPerformanceMonitoring<T extends object>(
  Component: React.ComponentType<T>,
  componentName: string
) {
  return function PerformanceMonitoredComponent(props: T) {
    const monitor = PerformanceMonitor.getInstance();
    const endMeasurement = monitor.start(`render:${componentName}`);

    React.useEffect(() => {
      endMeasurement();
    });

    return <Component {...props} />;
  };
}

/**
 * Hook for measuring operation performance
 */
export function usePerformanceMonitoring() {
  const monitor = PerformanceMonitor.getInstance();

  return {
    measureAsync: async <T>(
      label: string,
      operation: () => Promise<T>
    ): Promise<T> => {
      const endMeasurement = monitor.start(label);
      try {
        const result = await operation();
        return result;
      } finally {
        endMeasurement();
      }
    },

    measure: <T>(label: string, operation: () => T): T => {
      const endMeasurement = monitor.start(label);
      try {
        return operation();
      } finally {
        endMeasurement();
      }
    },

    getMetrics: (label: string) => monitor.getMetrics(label),
    getAllMetrics: () => monitor.getAllMetrics(),
  };
}

/**
 * API route performance middleware
 */
export function withApiPerformanceMonitoring(
  handler: (req: NextRequest, context?: any) => Promise<NextResponse>,
  routeName: string
) {
  return async (req: NextRequest, context?: any): Promise<NextResponse> => {
    const monitor = PerformanceMonitor.getInstance();
    const endMeasurement = monitor.start(`api:${routeName}`);

    const startTime = Date.now();

    try {
      const response = await handler(req, context);

      // Add performance headers
      response.headers.set('X-Response-Time', `${Date.now() - startTime}ms`);
      response.headers.set('X-Route', routeName);

      return response;
    } finally {
      endMeasurement();
    }
  };
}

/**
 * Client-side performance tracking
 */
export class ClientPerformanceTracker {
  private static instance: ClientPerformanceTracker;

  static getInstance(): ClientPerformanceTracker {
    if (typeof window === 'undefined') {
      throw new Error('ClientPerformanceTracker can only be used on the client side');
    }

    if (!ClientPerformanceTracker.instance) {
      ClientPerformanceTracker.instance = new ClientPerformanceTracker();
    }

    return ClientPerformanceTracker.instance;
  }

  /**
   * Track Core Web Vitals
   */
  trackWebVitals(): void {
    if (typeof window === 'undefined') return;

    // Track LCP (Largest Contentful Paint)
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1] as PerformanceEntry;

      console.log('LCP:', lastEntry.startTime);
      this.sendMetric('LCP', lastEntry.startTime);
    }).observe({ type: 'largest-contentful-paint', buffered: true });

    // Track FID (First Input Delay)
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry: any) => {
        console.log('FID:', entry.processingStart - entry.startTime);
        this.sendMetric('FID', entry.processingStart - entry.startTime);
      });
    }).observe({ type: 'first-input', buffered: true });

    // Track CLS (Cumulative Layout Shift)
    let clsValue = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as any[]) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
      console.log('CLS:', clsValue);
      this.sendMetric('CLS', clsValue);
    }).observe({ type: 'layout-shift', buffered: true });
  }

  /**
   * Track navigation timing
   */
  trackNavigationTiming(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('load', () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

      const metrics = {
        'DNS Lookup': navigation.domainLookupEnd - navigation.domainLookupStart,
        'TCP Connection': navigation.connectEnd - navigation.connectStart,
        'Request': navigation.responseStart - navigation.requestStart,
        'Response': navigation.responseEnd - navigation.responseStart,
        'DOM Processing': navigation.domContentLoadedEventStart - navigation.responseEnd,
        'Resource Loading': navigation.loadEventStart - navigation.domContentLoadedEventEnd,
        'Total Page Load': navigation.loadEventEnd - navigation.navigationStart,
      };

      Object.entries(metrics).forEach(([name, value]) => {
        console.log(`${name}:`, value);
        this.sendMetric(name, value);
      });
    });
  }

  /**
   * Track resource timing
   */
  trackResourceTiming(): void {
    if (typeof window === 'undefined') return;

    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        const resource = entry as PerformanceResourceTiming;
        console.log(`Resource ${resource.name}:`, resource.duration);
        this.sendMetric('Resource Load', resource.duration);
      });
    }).observe({ type: 'resource', buffered: true });
  }

  /**
   * Send metric to analytics
   */
  private sendMetric(name: string, value: number): void {
    // Send to your analytics service
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'performance_metric', {
        metric_name: name,
        metric_value: Math.round(value),
      });
    }

    // Send to custom analytics endpoint
    fetch('/api/analytics/performance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        metric: name,
        value: value,
        timestamp: Date.now(),
        url: window.location.href,
        userAgent: navigator.userAgent,
      }),
    }).catch(console.error);
  }
}

/**
 * Initialize client-side performance tracking
 */
export function initializePerformanceTracking(): void {
  if (typeof window === 'undefined') return;

  const tracker = ClientPerformanceTracker.getInstance();

  tracker.trackWebVitals();
  tracker.trackNavigationTiming();
  tracker.trackResourceTiming();
}

/**
 * Image optimization utilities
 */
export const imageOptimization = {
  /**
   * Generate responsive image sizes
   */
  generateSizes: (
    maxWidth: number,
    breakpoints: number[] = [640, 768, 1024, 1280, 1536]
  ): string => {
    const sizes = breakpoints
      .filter(bp => bp <= maxWidth)
      .map(bp => `(max-width: ${bp}px) ${bp}px`)
      .join(', ');

    return `${sizes}, ${maxWidth}px`;
  },

  /**
   * Generate srcSet for responsive images
   */
  generateSrcSet: (
    baseSrc: string,
    widths: number[]
  ): string => {
    return widths
      .map(width => `${baseSrc}?w=${width} ${width}w`)
      .join(', ');
  },
};

/**
 * Bundle analysis utilities
 */
export const bundleAnalysis = {
  /**
   * Analyze and log bundle size impact
   */
  logBundleImpact: (componentName: string, size: number): void => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`Bundle impact for ${componentName}:`, `${size} bytes`);
    }
  },

  /**
   * Dynamic import with bundle analysis
   */
  dynamicImportWithAnalysis: async <T>(
    importFn: () => Promise<{ default: T }>,
    componentName: string
  ): Promise<T> => {
    const startTime = performance.now();
    const module = await importFn();
    const loadTime = performance.now() - startTime;

    console.log(`Dynamic import ${componentName} took ${loadTime}ms`);

    return module.default;
  },
};