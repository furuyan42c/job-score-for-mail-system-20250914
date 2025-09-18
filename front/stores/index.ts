// Export all stores
export { useUserStore, userSelectors } from './userStore';
export { useJobStore, jobSelectors } from './jobStore';
export { useScoreStore, scoreSelectors } from './scoreStore';
export { useUIStore, uiSelectors, uiUtils } from './uiStore';
export { useFilterStore, filterSelectors } from './filterStore';

// Export store types
export type {
  UserState,
  JobState,
  ScoreState,
  UIState,
  FilterState
} from './userStore';

// Store management utilities
import { useUserStore } from './userStore';
import { useJobStore } from './jobStore';
import { useScoreStore } from './scoreStore';
import { useUIStore } from './uiStore';
import { useFilterStore } from './filterStore';

export const resetAllStores = () => {
  useUserStore.getState().resetStore();
  useJobStore.getState().resetStore();
  useScoreStore.getState().resetStore();
  useUIStore.getState().resetUIState();
  useFilterStore.getState().resetStore();
};

export const getStoreVersions = () => {
  return {
    user: 1,
    job: 1,
    score: 1,
    ui: 1,
    filter: 1,
  };
};

// Store hydration utilities
export const waitForHydration = (): Promise<void> => {
  return new Promise((resolve) => {
    const checkHydration = () => {
      // Check if stores are hydrated (this is a simplified check)
      // In a real implementation, you'd check the actual hydration state
      const stores = [
        useUserStore.getState(),
        useJobStore.getState(),
        useScoreStore.getState(),
        useUIStore.getState(),
        useFilterStore.getState(),
      ];

      // Simple check - if all stores are defined, consider them hydrated
      if (stores.every(store => store !== undefined)) {
        resolve();
      } else {
        setTimeout(checkHydration, 100);
      }
    };

    checkHydration();
  });
};

// Store state debugging utilities (development only)
export const getStoreStates = () => {
  if (process.env.NODE_ENV !== 'development') {
    return {};
  }

  return {
    user: useUserStore.getState(),
    job: useJobStore.getState(),
    score: useScoreStore.getState(),
    ui: useUIStore.getState(),
    filter: useFilterStore.getState(),
  };
};

export const logStoreStates = () => {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  console.group('Store States');
  console.log('User Store:', useUserStore.getState());
  console.log('Job Store:', useJobStore.getState());
  console.log('Score Store:', useScoreStore.getState());
  console.log('UI Store:', useUIStore.getState());
  console.log('Filter Store:', useFilterStore.getState());
  console.groupEnd();
};

// Store performance monitoring
export const monitorStorePerformance = () => {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  const stores = [
    { name: 'user', store: useUserStore },
    { name: 'job', store: useJobStore },
    { name: 'score', store: useScoreStore },
    { name: 'ui', store: useUIStore },
    { name: 'filter', store: useFilterStore },
  ];

  stores.forEach(({ name, store }) => {
    const originalSubscribe = store.subscribe;

    store.subscribe = ((listener) => {
      const startTime = performance.now();

      const wrappedListener = (...args: any[]) => {
        const listenerStartTime = performance.now();
        listener(...args);
        const listenerEndTime = performance.now();

        if (listenerEndTime - listenerStartTime > 16) { // More than one frame
          console.warn(`Slow ${name} store listener:`, listenerEndTime - listenerStartTime, 'ms');
        }
      };

      return originalSubscribe(wrappedListener);
    }) as any;
  });
};

// Initialize performance monitoring in development
if (process.env.NODE_ENV === 'development') {
  monitorStorePerformance();
}