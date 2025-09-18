// Export React Query client and utilities
export { queryClient, queryKeys, invalidateQueries, optimisticUpdates, prefetchQueries, backgroundSync, cacheUtils } from './client';

// Export all hooks
export * from './hooks';

// Re-export React Query components and utilities
export {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useMutation,
  useInfiniteQuery,
  useQueryClient,
  useIsFetching,
  useIsMutating,
} from '@tanstack/react-query';

// React Query DevTools (only in development)
export { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Provider component for React Query
import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './client';

interface QueryProviderProps {
  children: React.ReactNode;
}

export const QueryProvider: React.FC<QueryProviderProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

// Error boundary for React Query errors
import { Component, ReactNode } from 'react';
import { ApiError } from '../api/client';

interface QueryErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

interface QueryErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error) => ReactNode;
  onError?: (error: Error) => void;
}

export class QueryErrorBoundary extends Component<QueryErrorBoundaryProps, QueryErrorBoundaryState> {
  constructor(props: QueryErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): QueryErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    if (this.props.onError) {
      this.props.onError(error);
    }

    // Handle specific API errors
    if (error instanceof ApiError) {
      switch (error.status) {
        case 401:
          // Redirect to login on authentication error
          window.location.href = '/login';
          break;
        case 403:
          // Show access denied message
          console.error('Access denied:', error.message);
          break;
        case 500:
          // Show server error message
          console.error('Server error:', error.message);
          break;
      }
    }
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error);
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg
                  className="h-8 w-8 text-red-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Something went wrong
                </h3>
              </div>
            </div>
            <div className="text-sm text-gray-600 mb-4">
              {this.state.error instanceof ApiError
                ? this.state.error.message
                : 'An unexpected error occurred. Please try again.'}
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => this.setState({ hasError: false, error: undefined })}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Try again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Reload page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hooks for common query patterns
export const useInvalidateQueries = () => {
  const queryClient = useQueryClient();

  return {
    invalidateUser: () => invalidateQueries.user(),
    invalidateJobs: () => invalidateQueries.jobs(),
    invalidateJob: (jobId: string) => invalidateQueries.job(jobId),
    invalidateApplications: () => invalidateQueries.applications(),
    invalidateScores: () => invalidateQueries.scores(),
    invalidateSavedJobs: () => invalidateQueries.savedJobs(),
    invalidateSavedSearches: () => invalidateQueries.savedSearches(),
    invalidateNotifications: () => invalidateQueries.notifications(),
    invalidateAnalytics: () => invalidateQueries.analytics(),
    invalidateAll: () => queryClient.invalidateQueries(),
  };
};

// Hook for optimistic updates
export const useOptimisticUpdates = () => {
  return {
    toggleJobSave: optimisticUpdates.toggleJobSave,
    updateApplicationStatus: optimisticUpdates.updateApplicationStatus,
    markNotificationAsRead: optimisticUpdates.markNotificationAsRead,
  };
};

// Hook for prefetching
export const usePrefetch = () => {
  return {
    jobDetails: prefetchQueries.jobDetails,
    userRelatedData: prefetchQueries.userRelatedData,
    jobScores: prefetchQueries.jobScores,
  };
};

// Custom hook for managing cache
export const useQueryCache = () => {
  return {
    getCachedData: cacheUtils.getCachedData,
    setCachedData: cacheUtils.setCachedData,
    removeQuery: cacheUtils.removeQuery,
    clearAll: cacheUtils.clearAll,
    getCacheSize: cacheUtils.getCacheSize,
  };
};

// Utility hook for online/offline state
import { useEffect, useState } from 'react';

export const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    // Resume queries when coming back online
    if (isOnline) {
      queryClient.resumePausedMutations();
      queryClient.invalidateQueries();
    }
  }, [isOnline]);

  return isOnline;
};

// Hook for managing focus refetching
export const useFocusRefetch = (enabled = true) => {
  useEffect(() => {
    if (!enabled) return;

    const handleFocus = () => {
      queryClient.invalidateQueries({ refetchType: 'active' });
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [enabled]);
};

// Hook for managing network state
export const useNetworkState = () => {
  const [networkState, setNetworkState] = useState(() => {
    if (typeof navigator === 'undefined') {
      return { online: true, downlink: undefined, effectiveType: undefined };
    }

    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

    return {
      online: navigator.onLine,
      downlink: connection?.downlink,
      effectiveType: connection?.effectiveType,
    };
  });

  useEffect(() => {
    const updateNetworkState = () => {
      const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

      setNetworkState({
        online: navigator.onLine,
        downlink: connection?.downlink,
        effectiveType: connection?.effectiveType,
      });
    };

    window.addEventListener('online', updateNetworkState);
    window.addEventListener('offline', updateNetworkState);

    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    if (connection) {
      connection.addEventListener('change', updateNetworkState);
    }

    return () => {
      window.removeEventListener('online', updateNetworkState);
      window.removeEventListener('offline', updateNetworkState);

      if (connection) {
        connection.removeEventListener('change', updateNetworkState);
      }
    };
  }, []);

  return networkState;
};