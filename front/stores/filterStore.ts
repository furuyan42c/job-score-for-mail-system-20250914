import { create } from 'zustand';
import { createStoreWithMiddleware, type StoreCreator, handleAsyncError } from '../lib/utils/store-middleware';
import {
  JobFilters,
  JobSearchParams,
  SavedSearch,
  SearchHistory,
  JobType,
  ExperienceLevel,
  AsyncAction,
  ApiResponse
} from '../lib/types';

// Mock API for saved searches
const savedSearchApi = {
  getSavedSearches: async (userId: string): Promise<ApiResponse<SavedSearch[]>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: [
            {
              id: 'search-1',
              userId,
              name: 'Frontend Developer Jobs',
              filters: {
                query: 'frontend developer',
                skills: ['React', 'TypeScript', 'JavaScript'],
                jobType: ['full-time'],
                experienceLevel: ['mid', 'senior'],
                isRemote: true,
                sortBy: 'relevance',
                sortOrder: 'desc',
              },
              alertsEnabled: true,
              lastRunAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
              createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
              updatedAt: new Date().toISOString(),
            },
            {
              id: 'search-2',
              userId,
              name: 'Remote Senior Roles',
              filters: {
                experienceLevel: ['senior', 'lead'],
                isRemote: true,
                salaryMin: 120000,
                jobType: ['full-time'],
                sortBy: 'salary',
                sortOrder: 'desc',
              },
              alertsEnabled: false,
              createdAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
              updatedAt: new Date().toISOString(),
            },
          ]
        });
      }, 800);
    });
  },

  saveSearch: async (search: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt'>): Promise<ApiResponse<SavedSearch>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            ...search,
            id: `search-${Date.now()}`,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
        });
      }, 1000);
    });
  },

  updateSearch: async (id: string, updates: Partial<SavedSearch>): Promise<ApiResponse<SavedSearch>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            id,
            userId: 'user-1',
            name: 'Updated Search',
            filters: {},
            alertsEnabled: false,
            createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            updatedAt: new Date().toISOString(),
            ...updates,
          }
        });
      }, 800);
    });
  },

  deleteSearch: async (id: string): Promise<ApiResponse<void>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ status: 'success', data: undefined });
      }, 500);
    });
  },
};

interface FilterState {
  // Active filters
  activeFilters: JobFilters;
  pendingFilters: JobFilters; // Filters being modified before applying

  // Search state
  searchQuery: string;
  searchHistory: SearchHistory[];
  recentSearches: string[];
  searchSuggestions: string[];

  // Saved searches
  savedSearches: SavedSearch[];
  activeSavedSearchId: string | null;

  // Quick filters
  quickFilters: {
    remote: boolean;
    partTime: boolean;
    fullTime: boolean;
    recentlyPosted: boolean;
    highSalary: boolean;
  };

  // Advanced filter state
  advancedFiltersVisible: boolean;
  salaryRange: { min: number; max: number };
  selectedSkills: string[];
  skillSuggestions: string[];
  selectedLocations: string[];
  locationSuggestions: string[];
  selectedCompanies: string[];
  companySuggestions: string[];

  // Filter application history
  filterHistory: Array<{
    filters: JobFilters;
    timestamp: string;
    resultsCount?: number;
  }>;

  // Async actions
  loadSavedSearchesAction: AsyncAction<SavedSearch[]>;
  saveSearchAction: AsyncAction<SavedSearch>;
  updateSearchAction: AsyncAction<SavedSearch>;
  deleteSearchAction: AsyncAction<void>;

  // Actions
  setSearchQuery: (query: string) => void;
  setFilters: (filters: Partial<JobFilters>) => void;
  setPendingFilters: (filters: Partial<JobFilters>) => void;
  applyPendingFilters: () => void;
  resetPendingFilters: () => void;
  clearAllFilters: () => void;
  loadSavedSearches: (userId: string) => Promise<void>;
  saveCurrentSearch: (name: string, alertsEnabled?: boolean) => Promise<void>;
  applySavedSearch: (searchId: string) => void;
  updateSavedSearch: (id: string, updates: Partial<SavedSearch>) => Promise<void>;
  deleteSavedSearch: (id: string) => Promise<void>;
  setQuickFilter: (filter: keyof FilterState['quickFilters'], value: boolean) => void;
  toggleAdvancedFilters: () => void;
  setSalaryRange: (min: number, max: number) => void;
  addSkill: (skill: string) => void;
  removeSkill: (skill: string) => void;
  setSkillSuggestions: (suggestions: string[]) => void;
  addLocation: (location: string) => void;
  removeLocation: (location: string) => void;
  setLocationSuggestions: (suggestions: string[]) => void;
  addCompany: (company: string) => void;
  removeCompany: (company: string) => void;
  setCompanySuggestions: (suggestions: string[]) => void;
  addToSearchHistory: (query: string, resultsCount?: number) => void;
  clearSearchHistory: () => void;
  addToFilterHistory: (filters: JobFilters, resultsCount?: number) => void;
  revertToFilterHistory: (index: number) => void;
  clearFilterHistory: () => void;
  getFilterSummary: () => string;
  hasActiveFilters: () => boolean;
  resetStore: () => void;
}

const defaultFilters: JobFilters = {
  sortBy: 'relevance',
  sortOrder: 'desc',
};

const initialState: Omit<FilterState, keyof FilterActions> = {
  activeFilters: defaultFilters,
  pendingFilters: defaultFilters,
  searchQuery: '',
  searchHistory: [],
  recentSearches: [],
  searchSuggestions: [],
  savedSearches: [],
  activeSavedSearchId: null,
  quickFilters: {
    remote: false,
    partTime: false,
    fullTime: false,
    recentlyPosted: false,
    highSalary: false,
  },
  advancedFiltersVisible: false,
  salaryRange: { min: 0, max: 200000 },
  selectedSkills: [],
  skillSuggestions: [],
  selectedLocations: [],
  locationSuggestions: [],
  selectedCompanies: [],
  companySuggestions: [],
  filterHistory: [],
  loadSavedSearchesAction: { isLoading: false, error: null, data: null, lastFetch: null },
  saveSearchAction: { isLoading: false, error: null, data: null, lastFetch: null },
  updateSearchAction: { isLoading: false, error: null, data: null, lastFetch: null },
  deleteSearchAction: { isLoading: false, error: null, data: null, lastFetch: null },
};

type FilterActions = Pick<FilterState,
  | 'setSearchQuery'
  | 'setFilters'
  | 'setPendingFilters'
  | 'applyPendingFilters'
  | 'resetPendingFilters'
  | 'clearAllFilters'
  | 'loadSavedSearches'
  | 'saveCurrentSearch'
  | 'applySavedSearch'
  | 'updateSavedSearch'
  | 'deleteSavedSearch'
  | 'setQuickFilter'
  | 'toggleAdvancedFilters'
  | 'setSalaryRange'
  | 'addSkill'
  | 'removeSkill'
  | 'setSkillSuggestions'
  | 'addLocation'
  | 'removeLocation'
  | 'setLocationSuggestions'
  | 'addCompany'
  | 'removeCompany'
  | 'setCompanySuggestions'
  | 'addToSearchHistory'
  | 'clearSearchHistory'
  | 'addToFilterHistory'
  | 'revertToFilterHistory'
  | 'clearFilterHistory'
  | 'getFilterSummary'
  | 'hasActiveFilters'
  | 'resetStore'
>;

const filterStoreCreator: StoreCreator<FilterState> = (set, get) => ({
  ...initialState,

  setSearchQuery: (query: string) => {
    set((state) => {
      state.searchQuery = query;
      state.activeFilters.query = query || undefined;

      // Add to recent searches if not empty and not already present
      if (query.trim() && !state.recentSearches.includes(query)) {
        state.recentSearches.unshift(query);
        // Keep only last 10 searches
        if (state.recentSearches.length > 10) {
          state.recentSearches = state.recentSearches.slice(0, 10);
        }
      }
    });
  },

  setFilters: (filters: Partial<JobFilters>) => {
    set((state) => {
      state.activeFilters = { ...state.activeFilters, ...filters };
      state.pendingFilters = { ...state.activeFilters };
      state.activeSavedSearchId = null; // Clear active saved search when filters change
    });

    // Add to filter history
    get().addToFilterHistory(get().activeFilters);
  },

  setPendingFilters: (filters: Partial<JobFilters>) => {
    set((state) => {
      state.pendingFilters = { ...state.pendingFilters, ...filters };
    });
  },

  applyPendingFilters: () => {
    set((state) => {
      state.activeFilters = { ...state.pendingFilters };
      state.activeSavedSearchId = null;
    });

    get().addToFilterHistory(get().activeFilters);
  },

  resetPendingFilters: () => {
    set((state) => {
      state.pendingFilters = { ...state.activeFilters };
    });
  },

  clearAllFilters: () => {
    set((state) => {
      state.activeFilters = defaultFilters;
      state.pendingFilters = defaultFilters;
      state.searchQuery = '';
      state.activeSavedSearchId = null;
      state.selectedSkills = [];
      state.selectedLocations = [];
      state.selectedCompanies = [];
      state.quickFilters = {
        remote: false,
        partTime: false,
        fullTime: false,
        recentlyPosted: false,
        highSalary: false,
      };
      state.salaryRange = { min: 0, max: 200000 };
    });
  },

  loadSavedSearches: async (userId: string) => {
    set((state) => {
      state.loadSavedSearchesAction.isLoading = true;
      state.loadSavedSearchesAction.error = null;
    });

    try {
      const response = await savedSearchApi.getSavedSearches(userId);

      if (response.status === 'success') {
        set((state) => {
          state.savedSearches = response.data;
          state.loadSavedSearchesAction.isLoading = false;
          state.loadSavedSearchesAction.data = response.data;
          state.loadSavedSearchesAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      set((state) => {
        state.loadSavedSearchesAction.isLoading = false;
        state.loadSavedSearchesAction.error = handleAsyncError(error);
      });
    }
  },

  saveCurrentSearch: async (name: string, alertsEnabled = false) => {
    set((state) => {
      state.saveSearchAction.isLoading = true;
      state.saveSearchAction.error = null;
    });

    try {
      const response = await savedSearchApi.saveSearch({
        userId: 'user-1', // This should come from user store
        name,
        filters: get().activeFilters,
        alertsEnabled,
      });

      if (response.status === 'success') {
        set((state) => {
          state.savedSearches.push(response.data);
          state.activeSavedSearchId = response.data.id;
          state.saveSearchAction.isLoading = false;
          state.saveSearchAction.data = response.data;
          state.saveSearchAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      set((state) => {
        state.saveSearchAction.isLoading = false;
        state.saveSearchAction.error = handleAsyncError(error);
      });
    }
  },

  applySavedSearch: (searchId: string) => {
    const savedSearch = get().savedSearches.find(search => search.id === searchId);
    if (!savedSearch) return;

    set((state) => {
      state.activeFilters = { ...savedSearch.filters };
      state.pendingFilters = { ...savedSearch.filters };
      state.searchQuery = savedSearch.filters.query || '';
      state.activeSavedSearchId = searchId;

      // Apply filter components
      state.selectedSkills = savedSearch.filters.skills || [];
      state.selectedLocations = savedSearch.filters.location ? [savedSearch.filters.location] : [];

      if (savedSearch.filters.salaryMin || savedSearch.filters.salaryMax) {
        state.salaryRange = {
          min: savedSearch.filters.salaryMin || 0,
          max: savedSearch.filters.salaryMax || 200000,
        };
      }

      // Apply quick filters
      state.quickFilters.remote = !!savedSearch.filters.isRemote;
      state.quickFilters.fullTime = savedSearch.filters.jobType?.includes('full-time') || false;
      state.quickFilters.partTime = savedSearch.filters.jobType?.includes('part-time') || false;
    });

    get().addToFilterHistory(savedSearch.filters);
  },

  updateSavedSearch: async (id: string, updates: Partial<SavedSearch>) => {
    set((state) => {
      state.updateSearchAction.isLoading = true;
      state.updateSearchAction.error = null;
    });

    try {
      const response = await savedSearchApi.updateSearch(id, updates);

      if (response.status === 'success') {
        set((state) => {
          const index = state.savedSearches.findIndex(search => search.id === id);
          if (index !== -1) {
            state.savedSearches[index] = response.data;
          }
          state.updateSearchAction.isLoading = false;
          state.updateSearchAction.data = response.data;
          state.updateSearchAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      set((state) => {
        state.updateSearchAction.isLoading = false;
        state.updateSearchAction.error = handleAsyncError(error);
      });
    }
  },

  deleteSavedSearch: async (id: string) => {
    set((state) => {
      state.deleteSearchAction.isLoading = true;
      state.deleteSearchAction.error = null;
    });

    try {
      const response = await savedSearchApi.deleteSearch(id);

      if (response.status === 'success') {
        set((state) => {
          state.savedSearches = state.savedSearches.filter(search => search.id !== id);
          if (state.activeSavedSearchId === id) {
            state.activeSavedSearchId = null;
          }
          state.deleteSearchAction.isLoading = false;
          state.deleteSearchAction.data = response.data;
          state.deleteSearchAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      set((state) => {
        state.deleteSearchAction.isLoading = false;
        state.deleteSearchAction.error = handleAsyncError(error);
      });
    }
  },

  setQuickFilter: (filter: keyof FilterState['quickFilters'], value: boolean) => {
    set((state) => {
      state.quickFilters[filter] = value;
      state.activeSavedSearchId = null;

      // Apply quick filter to actual filters
      const filters = { ...state.activeFilters };

      switch (filter) {
        case 'remote':
          filters.isRemote = value || undefined;
          break;
        case 'fullTime':
          if (value) {
            filters.jobType = [...(filters.jobType || []), 'full-time'];
          } else {
            filters.jobType = (filters.jobType || []).filter(type => type !== 'full-time');
          }
          break;
        case 'partTime':
          if (value) {
            filters.jobType = [...(filters.jobType || []), 'part-time'];
          } else {
            filters.jobType = (filters.jobType || []).filter(type => type !== 'part-time');
          }
          break;
        case 'recentlyPosted':
          if (value) {
            filters.postedWithin = 'week';
          } else {
            delete filters.postedWithin;
          }
          break;
        case 'highSalary':
          if (value) {
            filters.salaryMin = 100000;
          } else {
            delete filters.salaryMin;
          }
          break;
      }

      state.activeFilters = filters;
      state.pendingFilters = filters;
    });
  },

  toggleAdvancedFilters: () => {
    set((state) => {
      state.advancedFiltersVisible = !state.advancedFiltersVisible;
    });
  },

  setSalaryRange: (min: number, max: number) => {
    set((state) => {
      state.salaryRange = { min, max };
      state.activeFilters.salaryMin = min > 0 ? min : undefined;
      state.activeFilters.salaryMax = max < 200000 ? max : undefined;
      state.pendingFilters = { ...state.activeFilters };
      state.activeSavedSearchId = null;
    });
  },

  addSkill: (skill: string) => {
    set((state) => {
      if (!state.selectedSkills.includes(skill)) {
        state.selectedSkills.push(skill);
        state.activeFilters.skills = [...state.selectedSkills];
        state.pendingFilters = { ...state.activeFilters };
        state.activeSavedSearchId = null;
      }
    });
  },

  removeSkill: (skill: string) => {
    set((state) => {
      state.selectedSkills = state.selectedSkills.filter(s => s !== skill);
      state.activeFilters.skills = state.selectedSkills.length > 0 ? [...state.selectedSkills] : undefined;
      state.pendingFilters = { ...state.activeFilters };
      state.activeSavedSearchId = null;
    });
  },

  setSkillSuggestions: (suggestions: string[]) => {
    set((state) => {
      state.skillSuggestions = suggestions;
    });
  },

  addLocation: (location: string) => {
    set((state) => {
      if (!state.selectedLocations.includes(location)) {
        state.selectedLocations.push(location);
        state.activeFilters.location = state.selectedLocations[0]; // For now, use first location
        state.pendingFilters = { ...state.activeFilters };
        state.activeSavedSearchId = null;
      }
    });
  },

  removeLocation: (location: string) => {
    set((state) => {
      state.selectedLocations = state.selectedLocations.filter(l => l !== location);
      state.activeFilters.location = state.selectedLocations[0] || undefined;
      state.pendingFilters = { ...state.activeFilters };
      state.activeSavedSearchId = null;
    });
  },

  setLocationSuggestions: (suggestions: string[]) => {
    set((state) => {
      state.locationSuggestions = suggestions;
    });
  },

  addCompany: (company: string) => {
    set((state) => {
      if (!state.selectedCompanies.includes(company)) {
        state.selectedCompanies.push(company);
        state.activeFilters.company = state.selectedCompanies[0]; // For now, use first company
        state.pendingFilters = { ...state.activeFilters };
        state.activeSavedSearchId = null;
      }
    });
  },

  removeCompany: (company: string) => {
    set((state) => {
      state.selectedCompanies = state.selectedCompanies.filter(c => c !== company);
      state.activeFilters.company = state.selectedCompanies[0] || undefined;
      state.pendingFilters = { ...state.activeFilters };
      state.activeSavedSearchId = null;
    });
  },

  setCompanySuggestions: (suggestions: string[]) => {
    set((state) => {
      state.companySuggestions = suggestions;
    });
  },

  addToSearchHistory: (query: string, resultsCount?: number) => {
    set((state) => {
      // Remove existing entry if present
      state.searchHistory = state.searchHistory.filter(item => item.query !== query);

      // Add new entry at the beginning
      state.searchHistory.unshift({
        query,
        timestamp: new Date().toISOString(),
        resultsCount: resultsCount || 0,
      });

      // Keep only last 50 searches
      if (state.searchHistory.length > 50) {
        state.searchHistory = state.searchHistory.slice(0, 50);
      }
    });
  },

  clearSearchHistory: () => {
    set((state) => {
      state.searchHistory = [];
      state.recentSearches = [];
    });
  },

  addToFilterHistory: (filters: JobFilters, resultsCount?: number) => {
    set((state) => {
      state.filterHistory.unshift({
        filters: { ...filters },
        timestamp: new Date().toISOString(),
        resultsCount,
      });

      // Keep only last 20 filter states
      if (state.filterHistory.length > 20) {
        state.filterHistory = state.filterHistory.slice(0, 20);
      }
    });
  },

  revertToFilterHistory: (index: number) => {
    const historyItem = get().filterHistory[index];
    if (!historyItem) return;

    set((state) => {
      state.activeFilters = { ...historyItem.filters };
      state.pendingFilters = { ...historyItem.filters };
      state.searchQuery = historyItem.filters.query || '';
      state.activeSavedSearchId = null;
    });
  },

  clearFilterHistory: () => {
    set((state) => {
      state.filterHistory = [];
    });
  },

  getFilterSummary: () => {
    const { activeFilters, selectedSkills, selectedLocations } = get();
    const parts: string[] = [];

    if (activeFilters.query) {
      parts.push(`"${activeFilters.query}"`);
    }

    if (selectedSkills.length > 0) {
      parts.push(`Skills: ${selectedSkills.join(', ')}`);
    }

    if (selectedLocations.length > 0) {
      parts.push(`Location: ${selectedLocations.join(', ')}`);
    }

    if (activeFilters.jobType && activeFilters.jobType.length > 0) {
      parts.push(`Type: ${activeFilters.jobType.join(', ')}`);
    }

    if (activeFilters.experienceLevel && activeFilters.experienceLevel.length > 0) {
      parts.push(`Experience: ${activeFilters.experienceLevel.join(', ')}`);
    }

    if (activeFilters.isRemote) {
      parts.push('Remote');
    }

    if (activeFilters.salaryMin || activeFilters.salaryMax) {
      const min = activeFilters.salaryMin ? `$${activeFilters.salaryMin.toLocaleString()}` : '';
      const max = activeFilters.salaryMax ? `$${activeFilters.salaryMax.toLocaleString()}` : '';
      parts.push(`Salary: ${min}${min && max ? ' - ' : ''}${max}`);
    }

    return parts.length > 0 ? parts.join(' • ') : 'No filters applied';
  },

  hasActiveFilters: () => {
    const { activeFilters, selectedSkills, selectedLocations } = get();

    return !!(
      activeFilters.query ||
      selectedSkills.length > 0 ||
      selectedLocations.length > 0 ||
      activeFilters.jobType?.length ||
      activeFilters.experienceLevel?.length ||
      activeFilters.isRemote ||
      activeFilters.salaryMin ||
      activeFilters.salaryMax ||
      activeFilters.company ||
      activeFilters.postedWithin
    );
  },

  resetStore: () => {
    set((state) => {
      Object.assign(state, initialState);
    });
  },
});

export const useFilterStore = create(
  createStoreWithMiddleware(filterStoreCreator, {
    name: 'filter-store',
    persist: {
      partialize: (state) => ({
        recentSearches: state.recentSearches,
        searchHistory: state.searchHistory.slice(0, 20), // Only persist recent history
        quickFilters: state.quickFilters,
        advancedFiltersVisible: state.advancedFiltersVisible,
        salaryRange: state.salaryRange,
      }),
      version: 1,
    },
  })
);

// Selectors
export const filterSelectors = {
  activeFilters: (state: FilterState) => state.activeFilters,
  pendingFilters: (state: FilterState) => state.pendingFilters,
  searchQuery: (state: FilterState) => state.searchQuery,
  searchHistory: (state: FilterState) => state.searchHistory,
  recentSearches: (state: FilterState) => state.recentSearches,
  savedSearches: (state: FilterState) => state.savedSearches,
  activeSavedSearch: (state: FilterState) =>
    state.activeSavedSearchId
      ? state.savedSearches.find(search => search.id === state.activeSavedSearchId)
      : null,
  quickFilters: (state: FilterState) => state.quickFilters,
  advancedFiltersVisible: (state: FilterState) => state.advancedFiltersVisible,
  selectedSkills: (state: FilterState) => state.selectedSkills,
  selectedLocations: (state: FilterState) => state.selectedLocations,
  selectedCompanies: (state: FilterState) => state.selectedCompanies,
  salaryRange: (state: FilterState) => state.salaryRange,
  filterHistory: (state: FilterState) => state.filterHistory,
  skillSuggestions: (state: FilterState) => state.skillSuggestions,
  locationSuggestions: (state: FilterState) => state.locationSuggestions,
  companySuggestions: (state: FilterState) => state.companySuggestions,
  loadSavedSearchesAction: (state: FilterState) => state.loadSavedSearchesAction,
  saveSearchAction: (state: FilterState) => state.saveSearchAction,
  updateSearchAction: (state: FilterState) => state.updateSearchAction,
  deleteSearchAction: (state: FilterState) => state.deleteSearchAction,
};