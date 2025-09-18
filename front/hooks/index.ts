// Export all custom hooks
export { useUser, useAuth, useProfile, useUserPreferences } from './useUser';
export {
  useJobs,
  useJobDetails,
  useJobApplications,
  useSavedJobs,
  useJobSearch
} from './useJobs';
export {
  useScores,
  useJobScore,
  useScoreWeights,
  useRankedJobs
} from './useScores';
export {
  useFilters,
  useSearch,
  useSavedSearches,
  useQuickFilters
} from './useFilters';

// Combined hooks for complex use cases
import { useUser } from './useUser';
import { useJobs } from './useJobs';
import { useScores } from './useScores';
import { useFilters } from './useFilters';
import { useUIStore } from '../stores/uiStore';
import { useCallback } from 'react';

// Hook for job discovery workflow
export const useJobDiscovery = () => {
  const { user, isAuthenticated } = useUser();
  const {
    jobs,
    searchJobs,
    isLoadingJobs,
    hasJobs,
    pagination,
    loadMore
  } = useJobs();
  const {
    calculateMultipleScores,
    rankedJobs,
    loadRankedJobs,
    isCalculatingAny
  } = useScores();
  const {
    activeFilters,
    searchQuery,
    hasFilters,
    applyFilters
  } = useFilters();

  const discoverJobs = useCallback(async () => {
    if (!isAuthenticated) return;

    // First, search for jobs based on current filters
    await searchJobs();

    // If we have jobs, calculate scores for them
    if (jobs.length > 0) {
      const jobIds = jobs.map(job => job.id);
      await calculateMultipleScores(jobIds);
    }

    // Load ranked jobs for the user
    await loadRankedJobs();
  }, [
    isAuthenticated,
    searchJobs,
    jobs,
    calculateMultipleScores,
    loadRankedJobs
  ]);

  return {
    // State
    jobs,
    rankedJobs,
    isLoading: isLoadingJobs || isCalculatingAny,
    hasJobs,
    pagination,

    // Current search context
    searchQuery,
    activeFilters,
    hasFilters,

    // Actions
    discoverJobs,
    searchJobs,
    loadMore,
    applyFilters,

    // User context
    isAuthenticated,
    user,
  };
};

// Hook for job application workflow
export const useJobApplicationWorkflow = () => {
  const { user, isAuthenticated, profile } = useUser();
  const {
    applyToJob,
    applications,
    isJobApplied,
    applyToJobAction
  } = useJobs();
  const { getScore, calculateScore } = useScores();
  const { showToast } = useUIStore();

  const applyWithScore = useCallback(async (
    jobId: string,
    applicationData: any
  ) => {
    if (!isAuthenticated) {
      showToast({
        type: 'error',
        title: 'Authentication Required',
        description: 'Please log in to apply for jobs',
      });
      return { success: false, error: 'Not authenticated' };
    }

    if (!profile?.preferences) {
      showToast({
        type: 'warning',
        title: 'Complete Your Profile',
        description: 'Please complete your profile before applying',
      });
      return { success: false, error: 'Incomplete profile' };
    }

    try {
      // Calculate score first if not available
      let score = getScore(jobId);
      if (!score) {
        await calculateScore(jobId);
        score = getScore(jobId);
      }

      // Apply to the job
      const result = await applyToJob(jobId, applicationData);

      if (result.success) {
        showToast({
          type: 'success',
          title: 'Application Submitted',
          description: score
            ? `Your compatibility score: ${score.overallScore}%`
            : 'Your application has been submitted successfully',
        });
      }

      return result;
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Application Failed',
        description: error instanceof Error ? error.message : 'Failed to submit application',
      });
      return { success: false, error: error instanceof Error ? error.message : 'Application failed' };
    }
  }, [
    isAuthenticated,
    profile,
    applyToJob,
    getScore,
    calculateScore,
    showToast
  ]);

  return {
    // State
    applications,
    isApplying: applyToJobAction.isLoading,

    // Actions
    applyWithScore,
    isJobApplied,

    // User context
    isAuthenticated,
    user,
    profile,
  };
};

// Hook for score-based job recommendations
export const useJobRecommendations = () => {
  const { user, isAuthenticated, preferences } = useUser();
  const {
    rankedJobs,
    loadRankedJobs,
    scoreWeights,
    isLoadingRanked
  } = useScores();
  const { searchJobs, jobs } = useJobs();
  const { applyFilters } = useFilters();

  const getRecommendations = useCallback(async (limit = 10) => {
    if (!isAuthenticated) return [];

    // Load ranked jobs based on user preferences and scores
    await loadRankedJobs(limit);
    return rankedJobs.slice(0, limit);
  }, [isAuthenticated, loadRankedJobs, rankedJobs]);

  const getRecommendationsForPreferences = useCallback(async () => {
    if (!preferences) return [];

    // Apply filters based on user preferences
    await applyFilters({
      jobType: preferences.jobTypes,
      isRemote: preferences.remoteWork,
      salaryMin: preferences.salaryRange?.min,
      salaryMax: preferences.salaryRange?.max,
      location: preferences.locations?.[0],
    });

    // Search with these filters
    await searchJobs();

    return jobs;
  }, [preferences, applyFilters, searchJobs, jobs]);

  const topRecommendations = rankedJobs.slice(0, 5);
  const hasRecommendations = rankedJobs.length > 0;

  return {
    // Recommendations
    recommendations: rankedJobs,
    topRecommendations,
    hasRecommendations,

    // State
    isLoading: isLoadingRanked,
    scoreWeights,

    // Actions
    getRecommendations,
    getRecommendationsForPreferences,

    // User context
    isAuthenticated,
    preferences,
  };
};

// Hook for comprehensive job search with all features
export const useJobSearchExperience = () => {
  const userHook = useUser();
  const jobsHook = useJobs();
  const scoresHook = useScores();
  const filtersHook = useFilters();

  const searchWithScoring = useCallback(async (query?: string) => {
    // Set search query if provided
    if (query) {
      filtersHook.search(query);
    }

    // Search for jobs
    await jobsHook.searchJobs();

    // Calculate scores for the results
    if (jobsHook.jobs.length > 0 && userHook.isAuthenticated) {
      const jobIds = jobsHook.jobs.map(job => job.id);
      await scoresHook.calculateMultipleScores(jobIds);
    }
  }, [filtersHook, jobsHook, scoresHook, userHook.isAuthenticated]);

  return {
    // All hook data combined
    user: userHook,
    jobs: jobsHook,
    scores: scoresHook,
    filters: filtersHook,

    // Enhanced search
    searchWithScoring,

    // Quick status checks
    isLoggedIn: userHook.isAuthenticated,
    hasResults: jobsHook.hasJobs,
    isSearching: jobsHook.isLoadingJobs || scoresHook.isCalculatingAny,
    hasActiveFilters: filtersHook.hasFilters,
  };
};