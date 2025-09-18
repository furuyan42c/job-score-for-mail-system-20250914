import { useCallback, useEffect, useMemo } from 'react';
import { useFilterStore, filterSelectors } from '../stores/filterStore';
import { useUserStore, userSelectors } from '../stores/userStore';
import { JobFilters, SavedSearch } from '../lib/types';

export const useFilters = () => {
  const store = useFilterStore();
  const user = useUserStore(userSelectors.user);

  // Selectors
  const activeFilters = useFilterStore(filterSelectors.activeFilters);
  const pendingFilters = useFilterStore(filterSelectors.pendingFilters);
  const searchQuery = useFilterStore(filterSelectors.searchQuery);
  const searchHistory = useFilterStore(filterSelectors.searchHistory);
  const recentSearches = useFilterStore(filterSelectors.recentSearches);
  const savedSearches = useFilterStore(filterSelectors.savedSearches);
  const activeSavedSearch = useFilterStore(filterSelectors.activeSavedSearch);
  const quickFilters = useFilterStore(filterSelectors.quickFilters);
  const advancedFiltersVisible = useFilterStore(filterSelectors.advancedFiltersVisible);
  const selectedSkills = useFilterStore(filterSelectors.selectedSkills);
  const selectedLocations = useFilterStore(filterSelectors.selectedLocations);
  const selectedCompanies = useFilterStore(filterSelectors.selectedCompanies);
  const salaryRange = useFilterStore(filterSelectors.salaryRange);
  const filterHistory = useFilterStore(filterSelectors.filterHistory);

  // Actions
  const {
    setSearchQuery,
    setFilters,
    setPendingFilters,
    applyPendingFilters,
    resetPendingFilters,
    clearAllFilters,
    loadSavedSearches,
    saveCurrentSearch,
    applySavedSearch,
    updateSavedSearch,
    deleteSavedSearch,
    setQuickFilter,
    toggleAdvancedFilters,
    setSalaryRange,
    addSkill,
    removeSkill,
    addLocation,
    removeLocation,
    addCompany,
    removeCompany,
    addToSearchHistory,
    clearSearchHistory,
    revertToFilterHistory,
    clearFilterHistory,
    getFilterSummary,
    hasActiveFilters,
    resetStore,
  } = store;

  // Async action states
  const loadSavedSearchesAction = useFilterStore(filterSelectors.loadSavedSearchesAction);
  const saveSearchAction = useFilterStore(filterSelectors.saveSearchAction);
  const updateSearchAction = useFilterStore(filterSelectors.updateSearchAction);
  const deleteSearchAction = useFilterStore(filterSelectors.deleteSearchAction);

  // Initialize saved searches on mount
  useEffect(() => {
    if (user?.id && savedSearches.length === 0 && !loadSavedSearchesAction.isLoading) {
      loadSavedSearches(user.id);
    }
  }, [user?.id, savedSearches.length, loadSavedSearchesAction.isLoading, loadSavedSearches]);

  // Enhanced filter actions with error handling
  const applyFilters = useCallback(async (filters: Partial<JobFilters>) => {
    try {
      setFilters(filters);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to apply filters'
      };
    }
  }, [setFilters]);

  const saveSearch = useCallback(async (name: string, alertsEnabled = false) => {
    if (!user?.id) {
      return { success: false, error: 'User must be logged in to save searches' };
    }

    try {
      await saveCurrentSearch(name, alertsEnabled);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to save search'
      };
    }
  }, [saveCurrentSearch, user?.id]);

  const updateSearch = useCallback(async (id: string, updates: Partial<SavedSearch>) => {
    try {
      await updateSavedSearch(id, updates);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update search'
      };
    }
  }, [updateSavedSearch]);

  const deleteSearch = useCallback(async (id: string) => {
    try {
      await deleteSavedSearch(id);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete search'
      };
    }
  }, [deleteSavedSearch]);

  // Quick filter shortcuts
  const setRemoteOnly = useCallback((remote: boolean) => {
    setQuickFilter('remote', remote);
  }, [setQuickFilter]);

  const setFullTimeOnly = useCallback((fullTime: boolean) => {
    setQuickFilter('fullTime', fullTime);
  }, [setQuickFilter]);

  const setPartTimeOnly = useCallback((partTime: boolean) => {
    setQuickFilter('partTime', partTime);
  }, [setQuickFilter]);

  const setRecentlyPosted = useCallback((recent: boolean) => {
    setQuickFilter('recentlyPosted', recent);
  }, [setQuickFilter]);

  const setHighSalaryOnly = useCallback((highSalary: boolean) => {
    setQuickFilter('highSalary', highSalary);
  }, [setQuickFilter]);

  // Skill management
  const toggleSkill = useCallback((skill: string) => {
    if (selectedSkills.includes(skill)) {
      removeSkill(skill);
    } else {
      addSkill(skill);
    }
  }, [selectedSkills, addSkill, removeSkill]);

  const clearSkills = useCallback(() => {
    selectedSkills.forEach(skill => removeSkill(skill));
  }, [selectedSkills, removeSkill]);

  // Location management
  const toggleLocation = useCallback((location: string) => {
    if (selectedLocations.includes(location)) {
      removeLocation(location);
    } else {
      addLocation(location);
    }
  }, [selectedLocations, addLocation, removeLocation]);

  const clearLocations = useCallback(() => {
    selectedLocations.forEach(location => removeLocation(location));
  }, [selectedLocations, removeLocation]);

  // Company management
  const toggleCompany = useCallback((company: string) => {
    if (selectedCompanies.includes(company)) {
      removeCompany(company);
    } else {
      addCompany(company);
    }
  }, [selectedCompanies, addCompany, removeCompany]);

  const clearCompanies = useCallback(() => {
    selectedCompanies.forEach(company => removeCompany(company));
  }, [selectedCompanies, removeCompany]);

  // Salary range helpers
  const setSalaryMin = useCallback((min: number) => {
    setSalaryRange(min, salaryRange.max);
  }, [setSalaryRange, salaryRange.max]);

  const setSalaryMax = useCallback((max: number) => {
    setSalaryRange(salaryRange.min, max);
  }, [setSalaryRange, salaryRange.min]);

  const clearSalaryRange = useCallback(() => {
    setSalaryRange(0, 200000);
  }, [setSalaryRange]);

  // Search functionality
  const search = useCallback((query: string) => {
    setSearchQuery(query);
    addToSearchHistory(query);
  }, [setSearchQuery, addToSearchHistory]);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
  }, [setSearchQuery]);

  // Filter state helpers
  const hasPendingChanges = useMemo(() => {
    return JSON.stringify(activeFilters) !== JSON.stringify(pendingFilters);
  }, [activeFilters, pendingFilters]);

  const filterCount = useMemo(() => {
    let count = 0;

    if (searchQuery) count++;
    if (selectedSkills.length) count++;
    if (selectedLocations.length) count++;
    if (selectedCompanies.length) count++;
    if (activeFilters.jobType?.length) count++;
    if (activeFilters.experienceLevel?.length) count++;
    if (activeFilters.isRemote) count++;
    if (activeFilters.salaryMin || activeFilters.salaryMax) count++;
    if (activeFilters.postedWithin) count++;

    return count;
  }, [searchQuery, selectedSkills, selectedLocations, selectedCompanies, activeFilters]);

  const canApplyFilters = useMemo(() => {
    return hasPendingChanges;
  }, [hasPendingChanges]);

  const canResetFilters = useMemo(() => {
    return hasActiveFilters();
  }, [hasActiveFilters]);

  // Quick preset filters
  const applyPresetFilter = useCallback((preset: string) => {
    switch (preset) {
      case 'remote-full-time':
        setFilters({
          isRemote: true,
          jobType: ['full-time'],
        });
        break;
      case 'senior-high-salary':
        setFilters({
          experienceLevel: ['senior', 'lead'],
          salaryMin: 120000,
        });
        break;
      case 'entry-level':
        setFilters({
          experienceLevel: ['entry', 'junior'],
        });
        break;
      case 'recent-posts':
        setFilters({
          postedWithin: 'week',
        });
        break;
      default:
        break;
    }
  }, [setFilters]);

  return {
    // Filter state
    activeFilters,
    pendingFilters,
    searchQuery,
    searchHistory,
    recentSearches,
    savedSearches,
    activeSavedSearch,
    quickFilters,
    advancedFiltersVisible,
    selectedSkills,
    selectedLocations,
    selectedCompanies,
    salaryRange,
    filterHistory,

    // Computed state
    filterCount,
    filterSummary: getFilterSummary(),
    hasFilters: hasActiveFilters(),
    hasPendingChanges,
    canApplyFilters,
    canResetFilters,

    // Loading states
    isLoadingSavedSearches: loadSavedSearchesAction.isLoading,
    isSavingSearch: saveSearchAction.isLoading,
    isUpdatingSearch: updateSearchAction.isLoading,
    isDeletingSearch: deleteSearchAction.isLoading,

    // Basic actions
    setSearchQuery,
    setFilters: applyFilters,
    setPendingFilters,
    applyPendingFilters,
    resetPendingFilters,
    clearAllFilters,
    toggleAdvancedFilters,

    // Search actions
    search,
    clearSearch,
    addToSearchHistory,
    clearSearchHistory,

    // Saved search actions
    loadSavedSearches,
    saveSearch,
    applySavedSearch,
    updateSearch,
    deleteSearch,

    // Quick filter actions
    setRemoteOnly,
    setFullTimeOnly,
    setPartTimeOnly,
    setRecentlyPosted,
    setHighSalaryOnly,
    setQuickFilter,

    // Skill actions
    addSkill,
    removeSkill,
    toggleSkill,
    clearSkills,

    // Location actions
    addLocation,
    removeLocation,
    toggleLocation,
    clearLocations,

    // Company actions
    addCompany,
    removeCompany,
    toggleCompany,
    clearCompanies,

    // Salary actions
    setSalaryRange,
    setSalaryMin,
    setSalaryMax,
    clearSalaryRange,

    // History actions
    revertToFilterHistory,
    clearFilterHistory,

    // Preset filters
    applyPresetFilter,

    // Store management
    resetStore,

    // Async action states
    loadSavedSearchesAction,
    saveSearchAction,
    updateSearchAction,
    deleteSearchAction,
  };
};

// Specialized hook for search functionality
export const useSearch = () => {
  const {
    searchQuery,
    searchHistory,
    recentSearches,
    search,
    clearSearch,
    addToSearchHistory,
    clearSearchHistory,
  } = useFilters();

  const getPopularSearches = useMemo(() => {
    // Count frequency of searches
    const frequency: Record<string, number> = {};
    searchHistory.forEach(item => {
      frequency[item.query] = (frequency[item.query] || 0) + 1;
    });

    // Sort by frequency and return top 10
    return Object.entries(frequency)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([query]) => query);
  }, [searchHistory]);

  return {
    searchQuery,
    searchHistory,
    recentSearches,
    popularSearches: getPopularSearches,
    search,
    clearSearch,
    addToSearchHistory,
    clearSearchHistory,
    hasSearchHistory: searchHistory.length > 0,
    hasRecentSearches: recentSearches.length > 0,
  };
};

// Hook for saved searches management
export const useSavedSearches = () => {
  const {
    savedSearches,
    activeSavedSearch,
    loadSavedSearches,
    saveSearch,
    applySavedSearch,
    updateSearch,
    deleteSearch,
    isLoadingSavedSearches,
    isSavingSearch,
    isUpdatingSearch,
    isDeletingSearch,
  } = useFilters();

  const user = useUserStore(userSelectors.user);

  const refreshSavedSearches = useCallback(async () => {
    if (user?.id) {
      await loadSavedSearches(user.id);
    }
  }, [loadSavedSearches, user?.id]);

  const toggleSearchAlerts = useCallback(async (searchId: string, enabled: boolean) => {
    return await updateSearch(searchId, { alertsEnabled: enabled });
  }, [updateSearch]);

  const searchesWithAlerts = useMemo(() => {
    return savedSearches.filter(search => search.alertsEnabled);
  }, [savedSearches]);

  return {
    savedSearches,
    activeSavedSearch,
    searchesWithAlerts,
    isLoading: isLoadingSavedSearches,
    isSaving: isSavingSearch,
    isUpdating: isUpdatingSearch,
    isDeleting: isDeletingSearch,
    saveSearch,
    applySavedSearch,
    updateSearch,
    deleteSearch,
    toggleSearchAlerts,
    refreshSavedSearches,
    hasSavedSearches: savedSearches.length > 0,
    hasActiveSearch: !!activeSavedSearch,
  };
};

// Hook for quick filters
export const useQuickFilters = () => {
  const {
    quickFilters,
    setRemoteOnly,
    setFullTimeOnly,
    setPartTimeOnly,
    setRecentlyPosted,
    setHighSalaryOnly,
    applyPresetFilter,
  } = useFilters();

  const clearQuickFilters = useCallback(() => {
    setRemoteOnly(false);
    setFullTimeOnly(false);
    setPartTimeOnly(false);
    setRecentlyPosted(false);
    setHighSalaryOnly(false);
  }, [setRemoteOnly, setFullTimeOnly, setPartTimeOnly, setRecentlyPosted, setHighSalaryOnly]);

  const activeQuickFiltersCount = useMemo(() => {
    return Object.values(quickFilters).filter(Boolean).length;
  }, [quickFilters]);

  return {
    quickFilters,
    activeCount: activeQuickFiltersCount,
    hasActiveQuickFilters: activeQuickFiltersCount > 0,
    setRemoteOnly,
    setFullTimeOnly,
    setPartTimeOnly,
    setRecentlyPosted,
    setHighSalaryOnly,
    clearQuickFilters,
    applyPresetFilter,
  };
};