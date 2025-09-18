import { create } from 'zustand';
import { createStoreWithMiddleware, type StoreCreator } from '../lib/utils/store-middleware';
import { Toast, Modal, LoadingState, ErrorState } from '../lib/types';

interface UIState {
  // Toast notifications
  toasts: Toast[];

  // Modal management
  modals: Record<string, Modal>;
  modalStack: string[]; // Track modal opening order

  // Loading states for different operations
  loading: LoadingState;

  // Error states
  errors: ErrorState;

  // Theme and appearance
  theme: 'light' | 'dark' | 'system';
  sidebarCollapsed: boolean;
  compactMode: boolean;

  // Navigation state
  currentPage: string;
  breadcrumbs: Array<{ label: string; href?: string }>;

  // Search UI state
  searchBarFocused: boolean;
  searchSuggestions: string[];
  showSearchHistory: boolean;

  // Filter panel state
  filterPanelOpen: boolean;
  activeFilterTabs: string[];

  // Job view preferences
  jobViewMode: 'list' | 'grid' | 'card';
  jobSortBy: 'relevance' | 'date' | 'score' | 'salary';
  jobSortOrder: 'asc' | 'desc';

  // Pagination UI
  itemsPerPage: number;
  showPaginationInfo: boolean;

  // Notification preferences
  notificationsEnabled: boolean;
  soundEnabled: boolean;

  // Keyboard shortcuts
  keyboardShortcutsEnabled: boolean;
  shortcutHelpVisible: boolean;

  // Performance and accessibility
  animationsEnabled: boolean;
  highContrastMode: boolean;
  fontSize: 'small' | 'medium' | 'large';

  // Mobile responsiveness
  isMobile: boolean;
  mobileMenuOpen: boolean;

  // Actions
  showToast: (toast: Omit<Toast, 'id'>) => string;
  hideToast: (id: string) => void;
  clearAllToasts: () => void;
  openModal: (modal: Omit<Modal, 'isOpen'>) => void;
  closeModal: (id: string) => void;
  closeAllModals: () => void;
  setLoading: (key: string, loading: boolean) => void;
  clearAllLoading: () => void;
  setError: (key: string, error: string | null) => void;
  clearError: (key: string) => void;
  clearAllErrors: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCompactMode: (compact: boolean) => void;
  setCurrentPage: (page: string) => void;
  setBreadcrumbs: (breadcrumbs: Array<{ label: string; href?: string }>) => void;
  setSearchBarFocused: (focused: boolean) => void;
  setSearchSuggestions: (suggestions: string[]) => void;
  setShowSearchHistory: (show: boolean) => void;
  setFilterPanelOpen: (open: boolean) => void;
  toggleFilterTab: (tab: string) => void;
  setJobViewMode: (mode: 'list' | 'grid' | 'card') => void;
  setJobSort: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  setItemsPerPage: (count: number) => void;
  setNotificationsEnabled: (enabled: boolean) => void;
  setSoundEnabled: (enabled: boolean) => void;
  setKeyboardShortcutsEnabled: (enabled: boolean) => void;
  toggleShortcutHelp: () => void;
  setAnimationsEnabled: (enabled: boolean) => void;
  setHighContrastMode: (enabled: boolean) => void;
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
  setMobile: (isMobile: boolean) => void;
  setMobileMenuOpen: (open: boolean) => void;
  resetUIState: () => void;
}

const initialState: Omit<UIState, keyof UIActions> = {
  toasts: [],
  modals: {},
  modalStack: [],
  loading: {},
  errors: {},
  theme: 'system',
  sidebarCollapsed: false,
  compactMode: false,
  currentPage: '/',
  breadcrumbs: [],
  searchBarFocused: false,
  searchSuggestions: [],
  showSearchHistory: false,
  filterPanelOpen: false,
  activeFilterTabs: ['location', 'salary'],
  jobViewMode: 'list',
  jobSortBy: 'relevance',
  jobSortOrder: 'desc',
  itemsPerPage: 20,
  showPaginationInfo: true,
  notificationsEnabled: true,
  soundEnabled: false,
  keyboardShortcutsEnabled: true,
  shortcutHelpVisible: false,
  animationsEnabled: true,
  highContrastMode: false,
  fontSize: 'medium',
  isMobile: false,
  mobileMenuOpen: false,
};

type UIActions = Pick<UIState,
  | 'showToast'
  | 'hideToast'
  | 'clearAllToasts'
  | 'openModal'
  | 'closeModal'
  | 'closeAllModals'
  | 'setLoading'
  | 'clearAllLoading'
  | 'setError'
  | 'clearError'
  | 'clearAllErrors'
  | 'setTheme'
  | 'toggleSidebar'
  | 'setSidebarCollapsed'
  | 'setCompactMode'
  | 'setCurrentPage'
  | 'setBreadcrumbs'
  | 'setSearchBarFocused'
  | 'setSearchSuggestions'
  | 'setShowSearchHistory'
  | 'setFilterPanelOpen'
  | 'toggleFilterTab'
  | 'setJobViewMode'
  | 'setJobSort'
  | 'setItemsPerPage'
  | 'setNotificationsEnabled'
  | 'setSoundEnabled'
  | 'setKeyboardShortcutsEnabled'
  | 'toggleShortcutHelp'
  | 'setAnimationsEnabled'
  | 'setHighContrastMode'
  | 'setFontSize'
  | 'setMobile'
  | 'setMobileMenuOpen'
  | 'resetUIState'
>;

const uiStoreCreator: StoreCreator<UIState> = (set, get) => ({
  ...initialState,

  showToast: (toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration || 5000,
    };

    set((state) => {
      state.toasts.push(newToast);

      // Limit to 5 toasts maximum
      if (state.toasts.length > 5) {
        state.toasts = state.toasts.slice(-5);
      }
    });

    // Auto-hide toast after duration
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        get().hideToast(id);
      }, newToast.duration);
    }

    return id;
  },

  hideToast: (id: string) => {
    set((state) => {
      state.toasts = state.toasts.filter(toast => toast.id !== id);
    });
  },

  clearAllToasts: () => {
    set((state) => {
      state.toasts = [];
    });
  },

  openModal: (modal: Omit<Modal, 'isOpen'>) => {
    set((state) => {
      const modalWithDefaults: Modal = {
        ...modal,
        isOpen: true,
        size: modal.size || 'md',
        closeable: modal.closeable !== false,
      };

      state.modals[modal.id] = modalWithDefaults;

      // Add to stack if not already there
      if (!state.modalStack.includes(modal.id)) {
        state.modalStack.push(modal.id);
      }
    });
  },

  closeModal: (id: string) => {
    set((state) => {
      if (state.modals[id]) {
        state.modals[id].isOpen = false;
      }

      // Remove from stack
      state.modalStack = state.modalStack.filter(modalId => modalId !== id);

      // Clean up closed modals after a delay to allow animations
      setTimeout(() => {
        set((state) => {
          delete state.modals[id];
        });
      }, 300);
    });
  },

  closeAllModals: () => {
    set((state) => {
      Object.keys(state.modals).forEach(id => {
        if (state.modals[id]) {
          state.modals[id].isOpen = false;
        }
      });

      state.modalStack = [];

      // Clean up after animation delay
      setTimeout(() => {
        set((state) => {
          state.modals = {};
        });
      }, 300);
    });
  },

  setLoading: (key: string, loading: boolean) => {
    set((state) => {
      if (loading) {
        state.loading[key] = true;
      } else {
        delete state.loading[key];
      }
    });
  },

  clearAllLoading: () => {
    set((state) => {
      state.loading = {};
    });
  },

  setError: (key: string, error: string | null) => {
    set((state) => {
      if (error) {
        state.errors[key] = error;
      } else {
        delete state.errors[key];
      }
    });
  },

  clearError: (key: string) => {
    set((state) => {
      delete state.errors[key];
    });
  },

  clearAllErrors: () => {
    set((state) => {
      state.errors = {};
    });
  },

  setTheme: (theme: 'light' | 'dark' | 'system') => {
    set((state) => {
      state.theme = theme;
    });

    // Apply theme to document
    if (typeof window !== 'undefined') {
      const root = window.document.documentElement;

      if (theme === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        root.classList.remove('light', 'dark');
        root.classList.add(systemTheme);
      } else {
        root.classList.remove('light', 'dark');
        root.classList.add(theme);
      }
    }
  },

  toggleSidebar: () => {
    set((state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    });
  },

  setSidebarCollapsed: (collapsed: boolean) => {
    set((state) => {
      state.sidebarCollapsed = collapsed;
    });
  },

  setCompactMode: (compact: boolean) => {
    set((state) => {
      state.compactMode = compact;
    });
  },

  setCurrentPage: (page: string) => {
    set((state) => {
      state.currentPage = page;
    });
  },

  setBreadcrumbs: (breadcrumbs: Array<{ label: string; href?: string }>) => {
    set((state) => {
      state.breadcrumbs = breadcrumbs;
    });
  },

  setSearchBarFocused: (focused: boolean) => {
    set((state) => {
      state.searchBarFocused = focused;

      // Clear suggestions when losing focus
      if (!focused) {
        state.searchSuggestions = [];
        state.showSearchHistory = false;
      }
    });
  },

  setSearchSuggestions: (suggestions: string[]) => {
    set((state) => {
      state.searchSuggestions = suggestions;
    });
  },

  setShowSearchHistory: (show: boolean) => {
    set((state) => {
      state.showSearchHistory = show;
    });
  },

  setFilterPanelOpen: (open: boolean) => {
    set((state) => {
      state.filterPanelOpen = open;
    });
  },

  toggleFilterTab: (tab: string) => {
    set((state) => {
      const index = state.activeFilterTabs.indexOf(tab);
      if (index === -1) {
        state.activeFilterTabs.push(tab);
      } else {
        state.activeFilterTabs.splice(index, 1);
      }
    });
  },

  setJobViewMode: (mode: 'list' | 'grid' | 'card') => {
    set((state) => {
      state.jobViewMode = mode;
    });
  },

  setJobSort: (sortBy: string, sortOrder: 'asc' | 'desc') => {
    set((state) => {
      state.jobSortBy = sortBy as any;
      state.jobSortOrder = sortOrder;
    });
  },

  setItemsPerPage: (count: number) => {
    set((state) => {
      state.itemsPerPage = count;
    });
  },

  setNotificationsEnabled: (enabled: boolean) => {
    set((state) => {
      state.notificationsEnabled = enabled;
    });
  },

  setSoundEnabled: (enabled: boolean) => {
    set((state) => {
      state.soundEnabled = enabled;
    });
  },

  setKeyboardShortcutsEnabled: (enabled: boolean) => {
    set((state) => {
      state.keyboardShortcutsEnabled = enabled;
    });
  },

  toggleShortcutHelp: () => {
    set((state) => {
      state.shortcutHelpVisible = !state.shortcutHelpVisible;
    });
  },

  setAnimationsEnabled: (enabled: boolean) => {
    set((state) => {
      state.animationsEnabled = enabled;
    });

    // Apply to document for CSS animations
    if (typeof window !== 'undefined') {
      const root = window.document.documentElement;
      if (enabled) {
        root.classList.remove('reduce-motion');
      } else {
        root.classList.add('reduce-motion');
      }
    }
  },

  setHighContrastMode: (enabled: boolean) => {
    set((state) => {
      state.highContrastMode = enabled;
    });

    // Apply to document
    if (typeof window !== 'undefined') {
      const root = window.document.documentElement;
      if (enabled) {
        root.classList.add('high-contrast');
      } else {
        root.classList.remove('high-contrast');
      }
    }
  },

  setFontSize: (size: 'small' | 'medium' | 'large') => {
    set((state) => {
      state.fontSize = size;
    });

    // Apply to document
    if (typeof window !== 'undefined') {
      const root = window.document.documentElement;
      root.classList.remove('font-small', 'font-medium', 'font-large');
      root.classList.add(`font-${size}`);
    }
  },

  setMobile: (isMobile: boolean) => {
    set((state) => {
      state.isMobile = isMobile;

      // Close mobile menu when switching to desktop
      if (!isMobile) {
        state.mobileMenuOpen = false;
      }
    });
  },

  setMobileMenuOpen: (open: boolean) => {
    set((state) => {
      state.mobileMenuOpen = open;
    });
  },

  resetUIState: () => {
    set((state) => {
      Object.assign(state, initialState);
    });
  },
});

export const useUIStore = create(
  createStoreWithMiddleware(uiStoreCreator, {
    name: 'ui-store',
    persist: {
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        compactMode: state.compactMode,
        jobViewMode: state.jobViewMode,
        jobSortBy: state.jobSortBy,
        jobSortOrder: state.jobSortOrder,
        itemsPerPage: state.itemsPerPage,
        notificationsEnabled: state.notificationsEnabled,
        soundEnabled: state.soundEnabled,
        keyboardShortcutsEnabled: state.keyboardShortcutsEnabled,
        animationsEnabled: state.animationsEnabled,
        highContrastMode: state.highContrastMode,
        fontSize: state.fontSize,
        activeFilterTabs: state.activeFilterTabs,
      }),
      version: 1,
    },
  })
);

// Selectors
export const uiSelectors = {
  toasts: (state: UIState) => state.toasts,
  modals: (state: UIState) => state.modals,
  activeModals: (state: UIState) => Object.values(state.modals).filter(modal => modal.isOpen),
  topModal: (state: UIState) => {
    const topId = state.modalStack[state.modalStack.length - 1];
    return topId ? state.modals[topId] : null;
  },
  loading: (state: UIState) => state.loading,
  errors: (state: UIState) => state.errors,
  isLoading: (state: UIState) => (key: string) => !!state.loading[key],
  hasError: (state: UIState) => (key: string) => !!state.errors[key],
  getError: (state: UIState) => (key: string) => state.errors[key] || null,
  theme: (state: UIState) => state.theme,
  sidebarCollapsed: (state: UIState) => state.sidebarCollapsed,
  compactMode: (state: UIState) => state.compactMode,
  currentPage: (state: UIState) => state.currentPage,
  breadcrumbs: (state: UIState) => state.breadcrumbs,
  searchBarFocused: (state: UIState) => state.searchBarFocused,
  searchSuggestions: (state: UIState) => state.searchSuggestions,
  showSearchHistory: (state: UIState) => state.showSearchHistory,
  filterPanelOpen: (state: UIState) => state.filterPanelOpen,
  activeFilterTabs: (state: UIState) => state.activeFilterTabs,
  jobViewMode: (state: UIState) => state.jobViewMode,
  jobSortBy: (state: UIState) => state.jobSortBy,
  jobSortOrder: (state: UIState) => state.jobSortOrder,
  itemsPerPage: (state: UIState) => state.itemsPerPage,
  notificationsEnabled: (state: UIState) => state.notificationsEnabled,
  soundEnabled: (state: UIState) => state.soundEnabled,
  keyboardShortcutsEnabled: (state: UIState) => state.keyboardShortcutsEnabled,
  shortcutHelpVisible: (state: UIState) => state.shortcutHelpVisible,
  animationsEnabled: (state: UIState) => state.animationsEnabled,
  highContrastMode: (state: UIState) => state.highContrastMode,
  fontSize: (state: UIState) => state.fontSize,
  isMobile: (state: UIState) => state.isMobile,
  mobileMenuOpen: (state: UIState) => state.mobileMenuOpen,
};

// Utility functions for common UI patterns
export const uiUtils = {
  showSuccessToast: (message: string, description?: string) => {
    return useUIStore.getState().showToast({
      type: 'success',
      title: message,
      description,
    });
  },

  showErrorToast: (message: string, description?: string) => {
    return useUIStore.getState().showToast({
      type: 'error',
      title: message,
      description,
      duration: 0, // Don't auto-hide error toasts
    });
  },

  showInfoToast: (message: string, description?: string) => {
    return useUIStore.getState().showToast({
      type: 'info',
      title: message,
      description,
    });
  },

  showWarningToast: (message: string, description?: string) => {
    return useUIStore.getState().showToast({
      type: 'warning',
      title: message,
      description,
    });
  },

  confirmModal: (title: string, message: string): Promise<boolean> => {
    return new Promise((resolve) => {
      const modalId = `confirm-${Date.now()}`;

      useUIStore.getState().openModal({
        id: modalId,
        title,
        size: 'sm',
      });

      // This would typically be handled by a modal component
      // For now, we'll resolve immediately as true
      // In a real implementation, you'd wait for user interaction
      setTimeout(() => {
        useUIStore.getState().closeModal(modalId);
        resolve(true);
      }, 1000);
    });
  },
};