import { create } from 'zustand';
import { createStoreWithMiddleware, type StoreCreator, handleAsyncError } from '../lib/utils/store-middleware';
import {
  JobScore,
  ScoreBreakdown,
  UserJobScore,
  Job,
  AsyncAction,
  ApiResponse,
  CacheEntry
} from '../lib/types';

// Mock API functions
const scoreApi = {
  calculateJobScore: async (jobId: string, userId: string): Promise<ApiResponse<JobScore>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const score = 65 + Math.random() * 30; // Random score between 65-95
        resolve({
          status: 'success',
          data: {
            id: `score-${jobId}-${userId}`,
            userId,
            jobId,
            overallScore: Number(score.toFixed(1)),
            skillsScore: Number((score * 0.9 + Math.random() * 10).toFixed(1)),
            experienceScore: Number((score * 0.8 + Math.random() * 20).toFixed(1)),
            locationScore: Number((score * 1.1 - Math.random() * 10).toFixed(1)),
            salaryScore: Number((score * 0.95 + Math.random() * 10).toFixed(1)),
            cultureScore: Number((score * 0.85 + Math.random() * 15).toFixed(1)),
            reasons: [
              'Strong skill match with React and TypeScript',
              'Experience level aligns with requirements',
              'Location preference matches',
              'Salary expectation within range'
            ],
            recommendations: [
              'Highlight your React projects in your application',
              'Mention your TypeScript experience',
              'Emphasize remote work capabilities',
              'Showcase relevant industry experience'
            ],
            calculatedAt: new Date().toISOString(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
        });
      }, 1500);
    });
  },

  getJobScores: async (userId: string, jobIds: string[]): Promise<ApiResponse<JobScore[]>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const scores = jobIds.map(jobId => {
          const score = 65 + Math.random() * 30;
          return {
            id: `score-${jobId}-${userId}`,
            userId,
            jobId,
            overallScore: Number(score.toFixed(1)),
            skillsScore: Number((score * 0.9 + Math.random() * 10).toFixed(1)),
            experienceScore: Number((score * 0.8 + Math.random() * 20).toFixed(1)),
            locationScore: Number((score * 1.1 - Math.random() * 10).toFixed(1)),
            salaryScore: Number((score * 0.95 + Math.random() * 10).toFixed(1)),
            cultureScore: Number((score * 0.85 + Math.random() * 15).toFixed(1)),
            reasons: ['Good match based on profile analysis'],
            recommendations: ['Tailor your application to highlight relevant skills'],
            calculatedAt: new Date().toISOString(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };
        });

        resolve({
          status: 'success',
          data: scores
        });
      }, 2000);
    });
  },

  getRankedJobs: async (userId: string, limit?: number): Promise<ApiResponse<UserJobScore[]>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockRankedJobs: UserJobScore[] = Array.from({ length: limit || 10 }, (_, i) => {
          const score = 95 - (i * 3) + Math.random() * 2;
          const jobId = `job-${i + 1}`;

          return {
            job: {
              id: jobId,
              title: `Top Match Job ${i + 1}`,
              company: `Company ${i + 1}`,
              description: `High-scoring job opportunity ${i + 1}`,
              requirements: ['JavaScript', 'React', 'TypeScript'],
              responsibilities: ['Development', 'Code reviews', 'Testing'],
              location: 'San Francisco, CA',
              isRemote: true,
              jobType: 'full-time',
              experienceLevel: 'mid',
              salaryRange: {
                min: 100000 + (i * 10000),
                max: 140000 + (i * 10000),
                currency: 'USD'
              },
              skills: ['JavaScript', 'React', 'TypeScript', 'Node.js'],
              benefits: ['Health insurance', '401k', 'Stock options'],
              status: 'active',
              applicantCount: Math.floor(Math.random() * 50),
              viewCount: Math.floor(Math.random() * 500),
              postedBy: 'recruiter-1',
              createdAt: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
              updatedAt: new Date().toISOString(),
            },
            score: {
              id: `score-${jobId}-user-1`,
              userId: 'user-1',
              jobId,
              overallScore: Number(score.toFixed(1)),
              skillsScore: Number((score * 0.95).toFixed(1)),
              experienceScore: Number((score * 0.9).toFixed(1)),
              locationScore: Number((score * 1.05).toFixed(1)),
              salaryScore: Number((score * 0.98).toFixed(1)),
              cultureScore: Number((score * 0.88).toFixed(1)),
              reasons: [
                'Excellent skill alignment',
                'Perfect experience match',
                'Ideal location preference',
                'Competitive salary range'
              ],
              recommendations: [
                'Apply as soon as possible',
                'Highlight relevant projects',
                'Mention specific technical skills',
                'Show enthusiasm for the role'
              ],
              calculatedAt: new Date().toISOString(),
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            },
            breakdown: [
              { category: 'Skills', score: Number((score * 0.95).toFixed(1)), weight: 0.3, explanation: 'Strong match with required technical skills' },
              { category: 'Experience', score: Number((score * 0.9).toFixed(1)), weight: 0.25, explanation: 'Experience level aligns well with job requirements' },
              { category: 'Location', score: Number((score * 1.05).toFixed(1)), weight: 0.15, explanation: 'Perfect location preference match' },
              { category: 'Salary', score: Number((score * 0.98).toFixed(1)), weight: 0.2, explanation: 'Salary expectations align with offer' },
              { category: 'Culture', score: Number((score * 0.88).toFixed(1)), weight: 0.1, explanation: 'Good cultural fit based on company values' },
            ],
            ranking: i + 1,
          };
        });

        resolve({
          status: 'success',
          data: mockRankedJobs
        });
      }, 1800);
    });
  },

  getScoreHistory: async (userId: string): Promise<ApiResponse<JobScore[]>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: []
        });
      }, 1000);
    });
  },

  updateScoreWeights: async (userId: string, weights: Record<string, number>): Promise<ApiResponse<void>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ status: 'success', data: undefined });
      }, 800);
    });
  }
};

interface ScoreState {
  // Score data
  jobScores: Record<string, JobScore>; // jobId -> score
  scoreCache: Map<string, CacheEntry<JobScore>>;
  rankedJobs: UserJobScore[];
  scoreHistory: JobScore[];

  // User scoring preferences
  scoreWeights: {
    skills: number;
    experience: number;
    location: number;
    salary: number;
    culture: number;
  };

  // Calculation state
  calculatingJobIds: Set<string>;
  lastCalculationTime: string | null;

  // Async actions
  calculateScoreAction: AsyncAction<JobScore>;
  getBatchScoresAction: AsyncAction<JobScore[]>;
  getRankedJobsAction: AsyncAction<UserJobScore[]>;
  getScoreHistoryAction: AsyncAction<JobScore[]>;
  updateWeightsAction: AsyncAction<void>;

  // Actions
  calculateJobScore: (jobId: string, userId: string, useCache?: boolean) => Promise<void>;
  calculateBatchScores: (jobIds: string[], userId: string) => Promise<void>;
  getRankedJobs: (userId: string, limit?: number) => Promise<void>;
  getScoreHistory: (userId: string) => Promise<void>;
  updateScoreWeights: (weights: Partial<Record<string, number>>) => Promise<void>;
  getJobScore: (jobId: string) => JobScore | null;
  getScoreBreakdown: (jobId: string) => ScoreBreakdown[] | null;
  invalidateScore: (jobId: string) => void;
  invalidateAllScores: () => void;
  setScoreWeights: (weights: Partial<Record<string, number>>) => void;
  clearCalculatingState: (jobId: string) => void;
  resetStore: () => void;
}

const defaultWeights = {
  skills: 0.3,
  experience: 0.25,
  location: 0.15,
  salary: 0.2,
  culture: 0.1,
};

const initialState: Omit<ScoreState, keyof ScoreActions> = {
  jobScores: {},
  scoreCache: new Map(),
  rankedJobs: [],
  scoreHistory: [],
  scoreWeights: defaultWeights,
  calculatingJobIds: new Set(),
  lastCalculationTime: null,
  calculateScoreAction: { isLoading: false, error: null, data: null, lastFetch: null },
  getBatchScoresAction: { isLoading: false, error: null, data: null, lastFetch: null },
  getRankedJobsAction: { isLoading: false, error: null, data: null, lastFetch: null },
  getScoreHistoryAction: { isLoading: false, error: null, data: null, lastFetch: null },
  updateWeightsAction: { isLoading: false, error: null, data: null, lastFetch: null },
};

type ScoreActions = Pick<ScoreState,
  | 'calculateJobScore'
  | 'calculateBatchScores'
  | 'getRankedJobs'
  | 'getScoreHistory'
  | 'updateScoreWeights'
  | 'getJobScore'
  | 'getScoreBreakdown'
  | 'invalidateScore'
  | 'invalidateAllScores'
  | 'setScoreWeights'
  | 'clearCalculatingState'
  | 'resetStore'
>;

const scoreStoreCreator: StoreCreator<ScoreState> = (set, get) => ({
  ...initialState,

  calculateJobScore: async (jobId: string, userId: string, useCache = true) => {
    // Check cache first
    if (useCache) {
      const cached = get().scoreCache.get(jobId);
      if (cached && Date.now() - cached.timestamp < cached.ttl) {
        set((state) => {
          state.jobScores[jobId] = cached.data;
          state.calculateScoreAction.data = cached.data;
        });
        return;
      }
    }

    // Check if already calculating
    if (get().calculatingJobIds.has(jobId)) {
      return;
    }

    set((state) => {
      state.calculatingJobIds.add(jobId);
      state.calculateScoreAction.isLoading = true;
      state.calculateScoreAction.error = null;
    });

    try {
      const response = await scoreApi.calculateJobScore(jobId, userId);

      if (response.status === 'success') {
        set((state) => {
          state.jobScores[jobId] = response.data;
          state.calculatingJobIds.delete(jobId);
          state.calculateScoreAction.isLoading = false;
          state.calculateScoreAction.data = response.data;
          state.calculateScoreAction.lastFetch = new Date().toISOString();
          state.lastCalculationTime = new Date().toISOString();

          // Cache the score
          state.scoreCache.set(jobId, {
            data: response.data,
            timestamp: Date.now(),
            ttl: 15 * 60 * 1000, // 15 minutes
            key: jobId,
          });
        });
      }
    } catch (error) {
      set((state) => {
        state.calculatingJobIds.delete(jobId);
        state.calculateScoreAction.isLoading = false;
        state.calculateScoreAction.error = handleAsyncError(error);
      });
    }
  },

  calculateBatchScores: async (jobIds: string[], userId: string) => {
    // Filter out jobs already being calculated or recently cached
    const uncachedJobIds = jobIds.filter(jobId => {
      if (get().calculatingJobIds.has(jobId)) return false;

      const cached = get().scoreCache.get(jobId);
      return !cached || Date.now() - cached.timestamp >= cached.ttl;
    });

    if (uncachedJobIds.length === 0) return;

    set((state) => {
      uncachedJobIds.forEach(jobId => state.calculatingJobIds.add(jobId));
      state.getBatchScoresAction.isLoading = true;
      state.getBatchScoresAction.error = null;
    });

    try {
      const response = await scoreApi.getJobScores(userId, uncachedJobIds);

      if (response.status === 'success') {
        set((state) => {
          response.data.forEach(score => {
            state.jobScores[score.jobId] = score;
            state.calculatingJobIds.delete(score.jobId);

            // Cache the score
            state.scoreCache.set(score.jobId, {
              data: score,
              timestamp: Date.now(),
              ttl: 15 * 60 * 1000,
              key: score.jobId,
            });
          });

          state.getBatchScoresAction.isLoading = false;
          state.getBatchScoresAction.data = response.data;
          state.getBatchScoresAction.lastFetch = new Date().toISOString();
          state.lastCalculationTime = new Date().toISOString();
        });
      }
    } catch (error) {
      set((state) => {
        uncachedJobIds.forEach(jobId => state.calculatingJobIds.delete(jobId));
        state.getBatchScoresAction.isLoading = false;
        state.getBatchScoresAction.error = handleAsyncError(error);
      });
    }
  },

  getRankedJobs: async (userId: string, limit = 20) => {
    set((state) => {
      state.getRankedJobsAction.isLoading = true;
      state.getRankedJobsAction.error = null;
    });

    try {
      const response = await scoreApi.getRankedJobs(userId, limit);

      if (response.status === 'success') {
        set((state) => {
          state.rankedJobs = response.data;
          state.getRankedJobsAction.isLoading = false;
          state.getRankedJobsAction.data = response.data;
          state.getRankedJobsAction.lastFetch = new Date().toISOString();

          // Cache the scores from ranked jobs
          response.data.forEach(({ score, job }) => {
            state.jobScores[job.id] = score;
            state.scoreCache.set(job.id, {
              data: score,
              timestamp: Date.now(),
              ttl: 15 * 60 * 1000,
              key: job.id,
            });
          });
        });
      }
    } catch (error) {
      set((state) => {
        state.getRankedJobsAction.isLoading = false;
        state.getRankedJobsAction.error = handleAsyncError(error);
      });
    }
  },

  getScoreHistory: async (userId: string) => {
    set((state) => {
      state.getScoreHistoryAction.isLoading = true;
      state.getScoreHistoryAction.error = null;
    });

    try {
      const response = await scoreApi.getScoreHistory(userId);

      if (response.status === 'success') {
        set((state) => {
          state.scoreHistory = response.data;
          state.getScoreHistoryAction.isLoading = false;
          state.getScoreHistoryAction.data = response.data;
          state.getScoreHistoryAction.lastFetch = new Date().toISOString();
        });
      }
    } catch (error) {
      set((state) => {
        state.getScoreHistoryAction.isLoading = false;
        state.getScoreHistoryAction.error = handleAsyncError(error);
      });
    }
  },

  updateScoreWeights: async (weights: Partial<Record<string, number>>) => {
    // Validate weights sum to 1.0
    const currentWeights = get().scoreWeights;
    const newWeights = { ...currentWeights, ...weights };
    const totalWeight = Object.values(newWeights).reduce((sum, weight) => sum + weight, 0);

    if (Math.abs(totalWeight - 1.0) > 0.01) {
      set((state) => {
        state.updateWeightsAction.error = 'Score weights must sum to 1.0';
      });
      return;
    }

    set((state) => {
      state.updateWeightsAction.isLoading = true;
      state.updateWeightsAction.error = null;
      state.scoreWeights = newWeights;
    });

    try {
      const response = await scoreApi.updateScoreWeights('user-1', newWeights);

      if (response.status === 'success') {
        set((state) => {
          state.updateWeightsAction.isLoading = false;
          state.updateWeightsAction.data = response.data;
          state.updateWeightsAction.lastFetch = new Date().toISOString();
        });

        // Invalidate all scores since weights changed
        get().invalidateAllScores();
      }
    } catch (error) {
      // Rollback weights on error
      set((state) => {
        state.scoreWeights = currentWeights;
        state.updateWeightsAction.isLoading = false;
        state.updateWeightsAction.error = handleAsyncError(error);
      });
    }
  },

  getJobScore: (jobId: string) => {
    return get().jobScores[jobId] || null;
  },

  getScoreBreakdown: (jobId: string) => {
    const score = get().jobScores[jobId];
    if (!score) return null;

    const weights = get().scoreWeights;

    return [
      {
        category: 'Skills',
        score: score.skillsScore,
        weight: weights.skills,
        explanation: 'Match between your skills and job requirements',
      },
      {
        category: 'Experience',
        score: score.experienceScore,
        weight: weights.experience,
        explanation: 'Alignment of your experience level with job expectations',
      },
      {
        category: 'Location',
        score: score.locationScore,
        weight: weights.location,
        explanation: 'Geographic preferences and remote work options',
      },
      {
        category: 'Salary',
        score: score.salaryScore,
        weight: weights.salary,
        explanation: 'Salary range match with your expectations',
      },
      {
        category: 'Culture',
        score: score.cultureScore,
        weight: weights.culture,
        explanation: 'Cultural fit based on company values and work style',
      },
    ];
  },

  invalidateScore: (jobId: string) => {
    set((state) => {
      delete state.jobScores[jobId];
      state.scoreCache.delete(jobId);
    });
  },

  invalidateAllScores: () => {
    set((state) => {
      state.jobScores = {};
      state.scoreCache.clear();
      state.rankedJobs = [];
      state.calculatingJobIds.clear();
    });
  },

  setScoreWeights: (weights: Partial<Record<string, number>>) => {
    set((state) => {
      state.scoreWeights = { ...state.scoreWeights, ...weights };
    });
  },

  clearCalculatingState: (jobId: string) => {
    set((state) => {
      state.calculatingJobIds.delete(jobId);
    });
  },

  resetStore: () => {
    set((state) => {
      Object.assign(state, {
        ...initialState,
        scoreCache: new Map(),
        calculatingJobIds: new Set(),
      });
    });
  },
});

export const useScoreStore = create(
  createStoreWithMiddleware(scoreStoreCreator, {
    name: 'score-store',
    persist: {
      partialize: (state) => ({
        scoreWeights: state.scoreWeights,
        // Don't persist scores as they can become stale
        // jobScores: state.jobScores,
      }),
      version: 1,
    },
  })
);

// Selectors
export const scoreSelectors = {
  jobScores: (state: ScoreState) => state.jobScores,
  rankedJobs: (state: ScoreState) => state.rankedJobs,
  scoreHistory: (state: ScoreState) => state.scoreHistory,
  scoreWeights: (state: ScoreState) => state.scoreWeights,
  isCalculating: (state: ScoreState) => (jobId: string) => state.calculatingJobIds.has(jobId),
  hasScore: (state: ScoreState) => (jobId: string) => !!state.jobScores[jobId],
  getJobScore: (state: ScoreState) => (jobId: string) => state.jobScores[jobId] || null,
  calculateScoreAction: (state: ScoreState) => state.calculateScoreAction,
  getBatchScoresAction: (state: ScoreState) => state.getBatchScoresAction,
  getRankedJobsAction: (state: ScoreState) => state.getRankedJobsAction,
  getScoreHistoryAction: (state: ScoreState) => state.getScoreHistoryAction,
  updateWeightsAction: (state: ScoreState) => state.updateWeightsAction,
  lastCalculationTime: (state: ScoreState) => state.lastCalculationTime,
};