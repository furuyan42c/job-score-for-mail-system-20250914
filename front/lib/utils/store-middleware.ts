import { StateCreator, StoreMutatorIdentifier } from 'zustand';
import { persist, PersistOptions, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware';

// Type for our enhanced store with all middleware
type StoreApi<T> = {
  setState: (
    partial: T | Partial<T> | ((state: T) => T | Partial<T>),
    replace?: boolean | undefined
  ) => void;
  getState: () => T;
  subscribe: (listener: (state: T, prevState: T) => void) => () => void;
};

// Middleware types
type Immer = ['zustand/immer', never];
type Persist = ['zustand/persist', unknown];
type Devtools = ['zustand/devtools', never];
type SubscribeWithSelector = ['zustand/subscribeWithSelector', never];

// Combined middleware type
type Middleware = [Immer, Persist, Devtools, SubscribeWithSelector];

// Helper type for creating store with all middleware
export type StoreCreator<T> = StateCreator<
  T,
  Middleware,
  [],
  T
>;

// Storage configuration
const storage = typeof window !== 'undefined'
  ? createJSONStorage(() => localStorage)
  : createJSONStorage(() => ({
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {},
    }));

// Create persist options
export const createPersistOptions = <T>(
  name: string,
  partialize?: (state: T) => Partial<T>,
  version?: number
): PersistOptions<T> => ({
  name,
  storage,
  partialize,
  version: version || 1,
  migrate: (persistedState: any, version: number) => {
    // Handle migration logic here if needed
    return persistedState;
  },
  onRehydrateStorage: (name) => {
    console.log(`Hydrating store: ${name}`);
    return (state, error) => {
      if (error) {
        console.error(`Error hydrating store ${name}:`, error);
      } else {
        console.log(`Successfully hydrated store: ${name}`);
      }
    };
  },
});

// Devtools configuration
export const createDevtoolsOptions = (name: string) => ({
  name,
  enabled: process.env.NODE_ENV === 'development',
});

// Cache utility for optimistic updates
export class OptimisticCache<T> {
  private cache = new Map<string, T>();
  private pendingActions = new Map<string, {
    optimisticData: T;
    rollbackData?: T;
    timestamp: number;
  }>();

  set(key: string, value: T, rollback?: T): void {
    this.cache.set(key, value);
    if (rollback !== undefined) {
      this.pendingActions.set(key, {
        optimisticData: value,
        rollbackData: rollback,
        timestamp: Date.now(),
      });
    }
  }

  get(key: string): T | undefined {
    return this.cache.get(key);
  }

  confirm(key: string): void {
    this.pendingActions.delete(key);
  }

  rollback(key: string): T | undefined {
    const pending = this.pendingActions.get(key);
    if (pending?.rollbackData) {
      this.cache.set(key, pending.rollbackData);
      this.pendingActions.delete(key);
      return pending.rollbackData;
    }
    return undefined;
  }

  clear(): void {
    this.cache.clear();
    this.pendingActions.clear();
  }

  // Clean up old pending actions (older than 5 minutes)
  cleanup(): void {
    const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
    for (const [key, action] of this.pendingActions.entries()) {
      if (action.timestamp < fiveMinutesAgo) {
        this.rollback(key);
      }
    }
  }
}

// WebSocket manager for real-time updates
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners = new Map<string, Set<(data: any) => void>>();

  connect(url: string): void {
    if (typeof window === 'undefined') return;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  }

  private handleMessage(message: any): void {
    const { type, payload } = message;
    const typeListeners = this.listeners.get(type);

    if (typeListeners) {
      typeListeners.forEach(listener => listener(payload));
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      setTimeout(() => {
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        // Note: You'd need to store the URL to reconnect
      }, delay);
    }
  }

  subscribe(type: string, listener: (data: any) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }

    this.listeners.get(type)!.add(listener);

    return () => {
      const typeListeners = this.listeners.get(type);
      if (typeListeners) {
        typeListeners.delete(listener);
        if (typeListeners.size === 0) {
          this.listeners.delete(type);
        }
      }
    };
  }

  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Error boundary helper
export const handleAsyncError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message);
  }

  return 'An unexpected error occurred';
};

// Async action wrapper
export const createAsyncAction = <T, Args extends any[]>(
  action: (...args: Args) => Promise<T>
) => {
  return async (...args: Args): Promise<{ data?: T; error?: string }> => {
    try {
      const data = await action(...args);
      return { data };
    } catch (error) {
      return { error: handleAsyncError(error) };
    }
  };
};

// Cache invalidation utility
export class CacheManager {
  private static instance: CacheManager;
  private invalidationCallbacks = new Map<string, Set<() => void>>();

  static getInstance(): CacheManager {
    if (!CacheManager.instance) {
      CacheManager.instance = new CacheManager();
    }
    return CacheManager.instance;
  }

  addInvalidationCallback(key: string, callback: () => void): () => void {
    if (!this.invalidationCallbacks.has(key)) {
      this.invalidationCallbacks.set(key, new Set());
    }

    this.invalidationCallbacks.get(key)!.add(callback);

    return () => {
      const callbacks = this.invalidationCallbacks.get(key);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.invalidationCallbacks.delete(key);
        }
      }
    };
  }

  invalidate(key: string): void {
    const callbacks = this.invalidationCallbacks.get(key);
    if (callbacks) {
      callbacks.forEach(callback => callback());
    }
  }

  invalidatePattern(pattern: RegExp): void {
    for (const key of this.invalidationCallbacks.keys()) {
      if (pattern.test(key)) {
        this.invalidate(key);
      }
    }
  }
}

// Utility for creating stores with standard middleware
export const createStoreWithMiddleware = <T>(
  creator: StoreCreator<T>,
  options: {
    name: string;
    persist?: {
      partialize?: (state: T) => Partial<T>;
      version?: number;
    };
  }
) => {
  const { name, persist: persistOptions } = options;

  let store = creator;

  // Apply immer middleware
  store = immer(store);

  // Apply persist middleware if configured
  if (persistOptions) {
    store = persist(
      store,
      createPersistOptions(name, persistOptions.partialize, persistOptions.version)
    ) as any;
  }

  // Apply devtools middleware
  store = devtools(store, createDevtoolsOptions(name)) as any;

  // Apply subscribeWithSelector middleware
  store = subscribeWithSelector(store) as any;

  return store;
};