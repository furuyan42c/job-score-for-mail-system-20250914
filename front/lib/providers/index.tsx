'use client';

import React, { ReactNode, useEffect } from 'react';
import { QueryProvider, QueryErrorBoundary } from '../query';
import { wsClient, setupGlobalErrorHandling } from '../api/client';
import { useUIStore } from '../../stores/uiStore';
import { useUserStore } from '../../stores/userStore';
import { backgroundSync } from '../query/client';

interface AppProvidersProps {
  children: ReactNode;
}

// WebSocket Provider
const WebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user, isAuthenticated } = useUserStore();

  useEffect(() => {
    let cleanup: (() => void) | undefined;

    if (isAuthenticated && user) {
      // Connect to WebSocket when user is authenticated
      wsClient.connect().then(() => {
        console.log('WebSocket connected');

        // Subscribe to user-specific events
        const unsubscribeScore = wsClient.subscribe('score_updated', (data) => {
          console.log('Score updated:', data);
          // You could update the score store here
        });

        const unsubscribeApplication = wsClient.subscribe('application_status_changed', (data) => {
          console.log('Application status changed:', data);
          // Update application status in cache
        });

        const unsubscribeNotification = wsClient.subscribe('notification', (data) => {
          console.log('New notification:', data);
          // Show toast notification
          useUIStore.getState().showToast({
            type: 'info',
            title: 'New Notification',
            description: data.message,
          });
        });

        cleanup = () => {
          unsubscribeScore();
          unsubscribeApplication();
          unsubscribeNotification();
          wsClient.disconnect();
        };
      }).catch((error) => {
        console.error('WebSocket connection failed:', error);
      });
    }

    return cleanup;
  }, [isAuthenticated, user]);

  return <>{children}</>;
};

// Background Sync Provider
const BackgroundSyncProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useUserStore();

  useEffect(() => {
    if (!isAuthenticated) return;

    // Start background sync for notifications and applications
    const stopNotificationSync = backgroundSync.startNotificationSync();
    const stopApplicationSync = backgroundSync.startApplicationSync();

    return () => {
      stopNotificationSync();
      stopApplicationSync();
    };
  }, [isAuthenticated]);

  return <>{children}</>;
};

// Theme Provider
const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { theme } = useUIStore();

  useEffect(() => {
    const root = window.document.documentElement;

    // Remove existing theme classes
    root.classList.remove('light', 'dark');

    if (theme === 'system') {
      // Use system preference
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);

      // Listen for system theme changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e: MediaQueryListEvent) => {
        root.classList.remove('light', 'dark');
        root.classList.add(e.matches ? 'dark' : 'light');
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      // Use explicit theme
      root.classList.add(theme);
    }
  }, [theme]);

  return <>{children}</>;
};

// Global Error Handler Provider
const ErrorHandlerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { showToast } = useUIStore();

  useEffect(() => {
    // Setup global API error handling
    setupGlobalErrorHandling((error) => {
      // Show toast notification for API errors
      showToast({
        type: 'error',
        title: 'Error',
        description: error.message,
        duration: 0, // Don't auto-hide error toasts
      });
    });

    // Global error handler for unhandled promise rejections
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      console.error('Unhandled promise rejection:', event.reason);
      showToast({
        type: 'error',
        title: 'Unexpected Error',
        description: 'An unexpected error occurred. Please try again.',
      });
    };

    // Global error handler for unhandled errors
    const handleError = (event: ErrorEvent) => {
      console.error('Unhandled error:', event.error);
      showToast({
        type: 'error',
        title: 'Unexpected Error',
        description: 'An unexpected error occurred. Please try again.',
      });
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('error', handleError);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('error', handleError);
    };
  }, [showToast]);

  return <>{children}</>;
};

// Mobile Detection Provider
const MobileDetectionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { setMobile } = useUIStore();

  useEffect(() => {
    const checkIsMobile = () => {
      setMobile(window.innerWidth < 768);
    };

    // Check on mount
    checkIsMobile();

    // Listen for resize events
    window.addEventListener('resize', checkIsMobile);
    return () => window.removeEventListener('resize', checkIsMobile);
  }, [setMobile]);

  return <>{children}</>;
};

// Analytics Provider
const AnalyticsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user, isAuthenticated } = useUserStore();

  useEffect(() => {
    // Initialize analytics when user logs in
    if (isAuthenticated && user) {
      // Track user login
      console.log('User logged in:', user.id);
    }
  }, [isAuthenticated, user]);

  return <>{children}</>;
};

// Keyboard Shortcuts Provider
const KeyboardShortcutsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { keyboardShortcutsEnabled, toggleShortcutHelp } = useUIStore();

  useEffect(() => {
    if (!keyboardShortcutsEnabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Global keyboard shortcuts
      if (event.metaKey || event.ctrlKey) {
        switch (event.key) {
          case 'k':
            // Open search (Cmd/Ctrl + K)
            event.preventDefault();
            // Focus search input
            const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
            if (searchInput) {
              searchInput.focus();
            }
            break;
          case '/':
            // Open search (Cmd/Ctrl + /)
            event.preventDefault();
            const searchInput2 = document.querySelector('input[type="search"]') as HTMLInputElement;
            if (searchInput2) {
              searchInput2.focus();
            }
            break;
          case '?':
            // Show keyboard shortcuts help
            event.preventDefault();
            toggleShortcutHelp();
            break;
        }
      }

      // Escape key shortcuts
      if (event.key === 'Escape') {
        // Close modals, clear search, etc.
        const { closeAllModals, setSearchBarFocused } = useUIStore.getState();
        closeAllModals();
        setSearchBarFocused(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [keyboardShortcutsEnabled, toggleShortcutHelp]);

  return <>{children}</>;
};

// Auth Initialization Provider
const AuthInitProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { initializeAuth, isAuthenticated, isLoading } = useUserStore();

  useEffect(() => {
    // Initialize authentication on app startup
    if (!isAuthenticated && !isLoading) {
      initializeAuth();
    }
  }, [initializeAuth, isAuthenticated, isLoading]);

  return <>{children}</>;
};

// Performance Monitor Provider (development only)
const PerformanceMonitorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    // Monitor performance
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'measure') {
          console.log(`Performance: ${entry.name} took ${entry.duration}ms`);
        }
      });
    });

    observer.observe({ entryTypes: ['measure'] });

    return () => observer.disconnect();
  }, []);

  return <>{children}</>;
};

// Accessibility Provider
const AccessibilityProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { highContrastMode, animationsEnabled, fontSize } = useUIStore();

  useEffect(() => {
    const root = document.documentElement;

    // Apply accessibility settings
    if (highContrastMode) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    if (!animationsEnabled) {
      root.classList.add('reduce-motion');
    } else {
      root.classList.remove('reduce-motion');
    }

    // Apply font size
    root.classList.remove('font-small', 'font-medium', 'font-large');
    root.classList.add(`font-${fontSize}`);
  }, [highContrastMode, animationsEnabled, fontSize]);

  return <>{children}</>;
};

// Custom Error Boundary
const AppErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <QueryErrorBoundary
      fallback={(error) => (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <svg
                  className="h-6 w-6 text-red-600"
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
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Application Error
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Something went wrong. Please refresh the page or try again later.
              </p>
              <div className="flex space-x-3 justify-center">
                <button
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Refresh Page
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      onError={(error) => {
        console.error('Application error:', error);
        // You could send error to monitoring service here
      }}
    >
      {children}
    </QueryErrorBoundary>
  );
};

// Main App Providers Component
export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <AppErrorBoundary>
      <QueryProvider>
        <ErrorHandlerProvider>
          <ThemeProvider>
            <AccessibilityProvider>
              <MobileDetectionProvider>
                <KeyboardShortcutsProvider>
                  <AuthInitProvider>
                    <WebSocketProvider>
                      <BackgroundSyncProvider>
                        <AnalyticsProvider>
                          {process.env.NODE_ENV === 'development' && (
                            <PerformanceMonitorProvider>
                              {children}
                            </PerformanceMonitorProvider>
                          )}
                          {process.env.NODE_ENV === 'production' && children}
                        </AnalyticsProvider>
                      </BackgroundSyncProvider>
                    </WebSocketProvider>
                  </AuthInitProvider>
                </KeyboardShortcutsProvider>
              </MobileDetectionProvider>
            </AccessibilityProvider>
          </ThemeProvider>
        </ErrorHandlerProvider>
      </QueryProvider>
    </AppErrorBoundary>
  );
};

// Export individual providers for testing or specific use cases
export {
  WebSocketProvider,
  BackgroundSyncProvider,
  ThemeProvider,
  ErrorHandlerProvider,
  MobileDetectionProvider,
  AnalyticsProvider,
  KeyboardShortcutsProvider,
  AuthInitProvider,
  PerformanceMonitorProvider,
  AccessibilityProvider,
  AppErrorBoundary,
};

// Context for accessing provider state
import { createContext, useContext } from 'react';

interface AppContextValue {
  isInitialized: boolean;
  version: string;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within AppProviders');
  }
  return context;
};

// Enhanced App Providers with context
export const AppProvidersWithContext: React.FC<AppProvidersProps> = ({ children }) => {
  const contextValue: AppContextValue = {
    isInitialized: true,
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  };

  return (
    <AppContext.Provider value={contextValue}>
      <AppProviders>{children}</AppProviders>
    </AppContext.Provider>
  );
};