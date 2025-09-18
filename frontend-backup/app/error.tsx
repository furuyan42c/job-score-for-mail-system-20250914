/**
 * Global Error Boundary
 * Handles unhandled errors in the application
 */

'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log error to monitoring service
    console.error('Application error:', error);

    // Report to error monitoring service
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'exception', {
        description: error.message,
        fatal: false,
      });
    }
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-6">
        {/* Error Icon */}
        <div className="flex justify-center">
          <div className="bg-destructive/10 p-4 rounded-full">
            <AlertTriangle className="h-12 w-12 text-destructive" />
          </div>
        </div>

        {/* Error Message */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">
            Something went wrong
          </h1>
          <p className="text-muted-foreground">
            We encountered an unexpected error. This has been logged and our team will investigate.
          </p>

          {/* Error Details (development only) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4 text-left">
              <summary className="cursor-pointer text-sm font-medium">
                Error Details
              </summary>
              <div className="mt-2 p-3 bg-muted rounded-md text-xs font-mono break-all">
                <p><strong>Message:</strong> {error.message}</p>
                {error.digest && (
                  <p><strong>Digest:</strong> {error.digest}</p>
                )}
                {error.stack && (
                  <div className="mt-2">
                    <strong>Stack:</strong>
                    <pre className="mt-1 whitespace-pre-wrap">{error.stack}</pre>
                  </div>
                )}
              </div>
            </details>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={reset}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </Button>

          <Button
            variant="outline"
            onClick={() => window.location.href = '/'}
            className="flex items-center gap-2"
          >
            <Home className="h-4 w-4" />
            Go home
          </Button>
        </div>

        {/* Help Text */}
        <div className="text-sm text-muted-foreground space-y-1">
          <p>
            If this problem persists, please{' '}
            <a
              href="/contact"
              className="text-primary hover:underline"
            >
              contact support
            </a>
            .
          </p>
          <p>Error ID: {error.digest || 'N/A'}</p>
        </div>
      </div>
    </div>
  );
}