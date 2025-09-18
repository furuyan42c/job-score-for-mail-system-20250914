import { useCallback, useEffect, useMemo } from 'react';
import { useScoreStore, scoreSelectors } from '../stores/scoreStore';
import { useUserStore, userSelectors } from '../stores/userStore';
import { JobScore, UserJobScore, ScoreBreakdown } from '../lib/types';

export const useScores = () => {
  const store = useScoreStore();
  const user = useUserStore(userSelectors.user);

  // Selectors
  const jobScores = useScoreStore(scoreSelectors.jobScores);
  const rankedJobs = useScoreStore(scoreSelectors.rankedJobs);
  const scoreHistory = useScoreStore(scoreSelectors.scoreHistory);
  const scoreWeights = useScoreStore(scoreSelectors.scoreWeights);
  const lastCalculationTime = useScoreStore(scoreSelectors.lastCalculationTime);

  // Actions
  const {
    calculateJobScore,
    calculateBatchScores,
    getRankedJobs,
    getScoreHistory,
    updateScoreWeights,
    getJobScore,
    getScoreBreakdown,
    invalidateScore,
    invalidateAllScores,
    setScoreWeights,
    resetStore,
  } = store;

  // Async action states
  const calculateScoreAction = useScoreStore(scoreSelectors.calculateScoreAction);
  const getBatchScoresAction = useScoreStore(scoreSelectors.getBatchScoresAction);
  const getRankedJobsAction = useScoreStore(scoreSelectors.getRankedJobsAction);
  const getScoreHistoryAction = useScoreStore(scoreSelectors.getScoreHistoryAction);
  const updateWeightsAction = useScoreStore(scoreSelectors.updateWeightsAction);

  // Status checkers
  const isCalculating = useScoreStore(scoreSelectors.isCalculating);
  const hasScore = useScoreStore(scoreSelectors.hasScore);

  // Calculate score for a single job
  const calculateScore = useCallback(async (jobId: string, useCache = true) => {
    if (!user?.id) {
      throw new Error('User must be logged in to calculate scores');
    }

    try {
      await calculateJobScore(jobId, user.id, useCache);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Score calculation failed'
      };
    }
  }, [calculateJobScore, user?.id]);

  // Calculate scores for multiple jobs
  const calculateMultipleScores = useCallback(async (jobIds: string[]) => {
    if (!user?.id) {
      throw new Error('User must be logged in to calculate scores');
    }

    try {
      await calculateBatchScores(jobIds, user.id);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Batch score calculation failed'
      };
    }
  }, [calculateBatchScores, user?.id]);

  // Get ranked jobs
  const loadRankedJobs = useCallback(async (limit = 20) => {
    if (!user?.id) {
      throw new Error('User must be logged in to get ranked jobs');
    }

    try {
      await getRankedJobs(user.id, limit);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load ranked jobs'
      };
    }
  }, [getRankedJobs, user?.id]);

  // Load score history
  const loadScoreHistory = useCallback(async () => {
    if (!user?.id) {
      throw new Error('User must be logged in to view score history');
    }

    try {
      await getScoreHistory(user.id);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load score history'
      };
    }
  }, [getScoreHistory, user?.id]);

  // Update scoring weights
  const updateWeights = useCallback(async (weights: Partial<Record<string, number>>) => {
    try {
      await updateScoreWeights(weights);
      return { success: true, error: null };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update weights'
      };
    }
  }, [updateScoreWeights]);

  // Get score for a specific job
  const getScore = useCallback((jobId: string): JobScore | null => {
    return getJobScore(jobId);
  }, [getJobScore]);

  // Get score breakdown for a specific job
  const getBreakdown = useCallback((jobId: string): ScoreBreakdown[] | null => {
    return getScoreBreakdown(jobId);
  }, [getScoreBreakdown]);

  // Calculate score percentage for display
  const getScorePercentage = useCallback((score: number): number => {
    return Math.round(score);
  }, []);

  // Get score color class based on score value
  const getScoreColor = useCallback((score: number): string => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 45) return 'text-orange-600';
    return 'text-red-600';
  }, []);

  // Get score label based on score value
  const getScoreLabel = useCallback((score: number): string => {
    if (score >= 90) return 'Excellent Match';
    if (score >= 75) return 'Great Match';
    if (score >= 60) return 'Good Match';
    if (score >= 45) return 'Fair Match';
    return 'Poor Match';
  }, []);

  // Initialize ranked jobs on mount
  useEffect(() => {
    if (user?.id && rankedJobs.length === 0 && !getRankedJobsAction.isLoading) {
      loadRankedJobs();
    }
  }, [user?.id, rankedJobs.length, getRankedJobsAction.isLoading, loadRankedJobs]);

  // Computed values
  const totalScores = Object.keys(jobScores).length;
  const averageScore = useMemo(() => {
    const scores = Object.values(jobScores);
    if (scores.length === 0) return 0;
    return scores.reduce((sum, score) => sum + score.overallScore, 0) / scores.length;
  }, [jobScores]);

  const topMatches = useMemo(() => {
    return rankedJobs.slice(0, 5);
  }, [rankedJobs]);

  const scoreDistribution = useMemo(() => {
    const scores = Object.values(jobScores);
    const distribution = {
      excellent: 0, // 90+
      great: 0,     // 75-89
      good: 0,      // 60-74
      fair: 0,      // 45-59
      poor: 0,      // <45
    };

    scores.forEach(score => {
      const value = score.overallScore;
      if (value >= 90) distribution.excellent++;
      else if (value >= 75) distribution.great++;
      else if (value >= 60) distribution.good++;
      else if (value >= 45) distribution.fair++;
      else distribution.poor++;
    });

    return distribution;
  }, [jobScores]);

  return {
    // Score data
    jobScores,
    rankedJobs,
    scoreHistory,
    scoreWeights,
    lastCalculationTime,

    // Computed values
    totalScores,
    averageScore,
    topMatches,
    scoreDistribution,

    // State
    isCalculatingAny: getBatchScoresAction.isLoading,
    isLoadingRanked: getRankedJobsAction.isLoading,
    isLoadingHistory: getScoreHistoryAction.isLoading,
    isUpdatingWeights: updateWeightsAction.isLoading,

    // Actions
    calculateScore,
    calculateMultipleScores,
    loadRankedJobs,
    loadScoreHistory,
    updateWeights,
    invalidateScore,
    invalidateAllScores,
    setScoreWeights,
    resetStore,

    // Async action states
    calculateScoreAction,
    getBatchScoresAction,
    getRankedJobsAction,
    getScoreHistoryAction,
    updateWeightsAction,

    // Utility functions
    getScore,
    getBreakdown,
    getScorePercentage,
    getScoreColor,
    getScoreLabel,
    isCalculating,
    hasScore,

    // User context
    isLoggedIn: !!user,
  };
};

// Specialized hook for job score calculation
export const useJobScore = (jobId: string) => {
  const {
    getScore,
    getBreakdown,
    calculateScore,
    isCalculating,
    hasScore,
    getScorePercentage,
    getScoreColor,
    getScoreLabel,
  } = useScores();

  const score = useMemo(() => getScore(jobId), [getScore, jobId]);
  const breakdown = useMemo(() => getBreakdown(jobId), [getBreakdown, jobId]);
  const isJobCalculating = useMemo(() => isCalculating(jobId), [isCalculating, jobId]);
  const hasJobScore = useMemo(() => hasScore(jobId), [hasScore, jobId]);

  const calculate = useCallback(async (useCache = true) => {
    return await calculateScore(jobId, useCache);
  }, [calculateScore, jobId]);

  const scoreData = useMemo(() => {
    if (!score) return null;

    return {
      overall: score.overallScore,
      percentage: getScorePercentage(score.overallScore),
      color: getScoreColor(score.overallScore),
      label: getScoreLabel(score.overallScore),
      breakdown: breakdown || [],
      reasons: score.reasons,
      recommendations: score.recommendations,
    };
  }, [score, breakdown, getScorePercentage, getScoreColor, getScoreLabel]);

  // Auto-calculate score if not present
  useEffect(() => {
    if (jobId && !hasJobScore && !isJobCalculating) {
      calculate();
    }
  }, [jobId, hasJobScore, isJobCalculating, calculate]);

  return {
    score: scoreData,
    isCalculating: isJobCalculating,
    hasScore: hasJobScore,
    calculate,
    rawScore: score,
    breakdown,
  };
};

// Hook for score weights management
export const useScoreWeights = () => {
  const { scoreWeights, updateWeights, updateWeightsAction, setScoreWeights } = useScores();

  const updateWeight = useCallback((category: string, weight: number) => {
    const newWeights = { ...scoreWeights, [category]: weight };
    setScoreWeights(newWeights);
  }, [scoreWeights, setScoreWeights]);

  const saveWeights = useCallback(async () => {
    return await updateWeights(scoreWeights);
  }, [updateWeights, scoreWeights]);

  const resetWeights = useCallback(() => {
    const defaultWeights = {
      skills: 0.3,
      experience: 0.25,
      location: 0.15,
      salary: 0.2,
      culture: 0.1,
    };
    setScoreWeights(defaultWeights);
  }, [setScoreWeights]);

  const validateWeights = useCallback((weights: Record<string, number>) => {
    const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
    return Math.abs(total - 1.0) < 0.01;
  }, []);

  const isValidWeights = useMemo(() => {
    return validateWeights(scoreWeights);
  }, [scoreWeights, validateWeights]);

  return {
    weights: scoreWeights,
    isUpdating: updateWeightsAction.isLoading,
    error: updateWeightsAction.error,
    isValid: isValidWeights,
    updateWeight,
    saveWeights,
    resetWeights,
    validateWeights,
  };
};

// Hook for ranked jobs
export const useRankedJobs = (limit = 20) => {
  const { rankedJobs, loadRankedJobs, getRankedJobsAction } = useScores();

  const refresh = useCallback(async () => {
    return await loadRankedJobs(limit);
  }, [loadRankedJobs, limit]);

  const getJobRank = useCallback((jobId: string) => {
    const index = rankedJobs.findIndex(item => item.job.id === jobId);
    return index !== -1 ? index + 1 : null;
  }, [rankedJobs]);

  return {
    rankedJobs: rankedJobs.slice(0, limit),
    isLoading: getRankedJobsAction.isLoading,
    error: getRankedJobsAction.error,
    refresh,
    getJobRank,
    totalRanked: rankedJobs.length,
  };
};