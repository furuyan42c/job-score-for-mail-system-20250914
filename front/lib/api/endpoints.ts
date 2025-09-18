import { apiClient } from './client';
import {
  User,
  UserProfile,
  UserPreferences,
  Job,
  JobSearchParams,
  JobScore,
  JobApplication,
  SavedSearch,
  ApiResponse,
  PaginatedResponse,
  AuthState,
  ScoreBreakdown,
  UserJobScore
} from '../types';

// Authentication endpoints
export const authApi = {
  login: async (email: string, password: string): Promise<ApiResponse<AuthState>> => {
    return apiClient.post('/auth/login', { email, password }, { withAuth: false });
  },

  register: async (userData: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    username: string;
  }): Promise<ApiResponse<AuthState>> => {
    return apiClient.post('/auth/register', userData, { withAuth: false });
  },

  logout: async (): Promise<ApiResponse<void>> => {
    return apiClient.post('/auth/logout');
  },

  refreshToken: async (refreshToken: string): Promise<ApiResponse<{
    accessToken: string;
    refreshToken: string;
    expiresAt: string;
  }>> => {
    return apiClient.post('/auth/refresh', { refreshToken }, { withAuth: false });
  },

  verifyEmail: async (token: string): Promise<ApiResponse<void>> => {
    return apiClient.post('/auth/verify-email', { token }, { withAuth: false });
  },

  forgotPassword: async (email: string): Promise<ApiResponse<void>> => {
    return apiClient.post('/auth/forgot-password', { email }, { withAuth: false });
  },

  resetPassword: async (token: string, newPassword: string): Promise<ApiResponse<void>> => {
    return apiClient.post('/auth/reset-password', { token, newPassword }, { withAuth: false });
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<ApiResponse<void>> => {
    return apiClient.post('/auth/change-password', { currentPassword, newPassword });
  },
};

// User endpoints
export const userApi = {
  getCurrentUser: async (): Promise<ApiResponse<{ user: User; profile: UserProfile | null }>> => {
    return apiClient.get('/users/me', { cache: true });
  },

  updateUser: async (userData: Partial<User>): Promise<ApiResponse<User>> => {
    return apiClient.patch('/users/me', userData);
  },

  deleteUser: async (): Promise<ApiResponse<void>> => {
    return apiClient.delete('/users/me');
  },

  uploadAvatar: async (file: File): Promise<ApiResponse<{ avatarUrl: string }>> => {
    return apiClient.uploadFile('/users/me/avatar', file);
  },
};

// User Profile endpoints
export const profileApi = {
  getProfile: async (userId?: string): Promise<ApiResponse<UserProfile>> => {
    const endpoint = userId ? `/profiles/${userId}` : '/profiles/me';
    return apiClient.get(endpoint, { cache: true });
  },

  updateProfile: async (profileData: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> => {
    return apiClient.patch('/profiles/me', profileData);
  },

  updatePreferences: async (preferences: Partial<UserPreferences>): Promise<ApiResponse<UserPreferences>> => {
    return apiClient.patch('/profiles/me/preferences', preferences);
  },

  uploadResume: async (file: File): Promise<ApiResponse<{ resumeUrl: string }>> => {
    return apiClient.uploadFile('/profiles/me/resume', file);
  },
};

// Job endpoints
export const jobApi = {
  getJobs: async (params?: JobSearchParams & {
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Job>> => {
    return apiClient.getPaginated('/jobs', params, { cache: true });
  },

  getJobById: async (id: string): Promise<ApiResponse<Job>> => {
    return apiClient.get(`/jobs/${id}`, { cache: true });
  },

  getFeaturedJobs: async (limit = 10): Promise<ApiResponse<Job[]>> => {
    return apiClient.get('/jobs/featured', { cache: true });
  },

  getRecentJobs: async (limit = 20): Promise<ApiResponse<Job[]>> => {
    return apiClient.get(`/jobs/recent?limit=${limit}`, { cache: true });
  },

  getJobsByCompany: async (companyId: string, params?: {
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Job>> => {
    return apiClient.getPaginated(`/jobs/company/${companyId}`, params, { cache: true });
  },

  getJobSkills: async (): Promise<ApiResponse<string[]>> => {
    return apiClient.get('/jobs/skills', { cache: true });
  },

  getJobLocations: async (): Promise<ApiResponse<string[]>> => {
    return apiClient.get('/jobs/locations', { cache: true });
  },

  getJobCompanies: async (): Promise<ApiResponse<Array<{ id: string; name: string; logo?: string }>>> => {
    return apiClient.get('/jobs/companies', { cache: true });
  },

  incrementJobView: async (jobId: string): Promise<ApiResponse<void>> => {
    return apiClient.post(`/jobs/${jobId}/view`);
  },
};

// Job Application endpoints
export const applicationApi = {
  applyToJob: async (jobId: string, applicationData: {
    coverLetter?: string;
    resumeUrl?: string;
    customResponses?: Record<string, string>;
  }): Promise<ApiResponse<JobApplication>> => {
    return apiClient.post(`/jobs/${jobId}/apply`, applicationData);
  },

  getMyApplications: async (params?: {
    status?: JobApplication['status'];
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<JobApplication>> => {
    return apiClient.getPaginated('/applications/me', params);
  },

  getApplicationById: async (id: string): Promise<ApiResponse<JobApplication>> => {
    return apiClient.get(`/applications/${id}`);
  },

  updateApplication: async (id: string, updates: {
    coverLetter?: string;
    customResponses?: Record<string, string>;
    notes?: string;
  }): Promise<ApiResponse<JobApplication>> => {
    return apiClient.patch(`/applications/${id}`, updates);
  },

  withdrawApplication: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.post(`/applications/${id}/withdraw`);
  },

  getApplicationHistory: async (jobId: string): Promise<ApiResponse<JobApplication[]>> => {
    return apiClient.get(`/jobs/${jobId}/applications/history`);
  },
};

// Job Scoring endpoints
export const scoreApi = {
  calculateJobScore: async (jobId: string): Promise<ApiResponse<JobScore>> => {
    return apiClient.post(`/scores/jobs/${jobId}/calculate`);
  },

  getJobScore: async (jobId: string): Promise<ApiResponse<JobScore>> => {
    return apiClient.get(`/scores/jobs/${jobId}`, { cache: true });
  },

  getBatchJobScores: async (jobIds: string[]): Promise<ApiResponse<JobScore[]>> => {
    return apiClient.post('/scores/jobs/batch', { jobIds });
  },

  getRankedJobs: async (params?: {
    limit?: number;
    minScore?: number;
    skills?: string[];
    locations?: string[];
  }): Promise<ApiResponse<UserJobScore[]>> => {
    return apiClient.get('/scores/ranked', { cache: true });
  },

  getScoreHistory: async (params?: {
    page?: number;
    limit?: number;
    dateFrom?: string;
    dateTo?: string;
  }): Promise<PaginatedResponse<JobScore>> => {
    return apiClient.getPaginated('/scores/history', params);
  },

  getScoreBreakdown: async (jobId: string): Promise<ApiResponse<ScoreBreakdown[]>> => {
    return apiClient.get(`/scores/jobs/${jobId}/breakdown`, { cache: true });
  },

  updateScoreWeights: async (weights: Record<string, number>): Promise<ApiResponse<void>> => {
    return apiClient.patch('/scores/weights', { weights });
  },

  getScoreWeights: async (): Promise<ApiResponse<Record<string, number>>> => {
    return apiClient.get('/scores/weights', { cache: true });
  },

  getScoreStats: async (): Promise<ApiResponse<{
    totalScores: number;
    averageScore: number;
    topScore: number;
    scoreDistribution: Record<string, number>;
  }>> => {
    return apiClient.get('/scores/stats', { cache: true });
  },
};

// Saved Jobs endpoints
export const savedJobsApi = {
  getSavedJobs: async (params?: {
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Job>> => {
    return apiClient.getPaginated('/saved-jobs', params);
  },

  saveJob: async (jobId: string): Promise<ApiResponse<void>> => {
    return apiClient.post(`/saved-jobs/${jobId}`);
  },

  unsaveJob: async (jobId: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/saved-jobs/${jobId}`);
  },

  isSaved: async (jobId: string): Promise<ApiResponse<{ isSaved: boolean }>> => {
    return apiClient.get(`/saved-jobs/${jobId}/status`, { cache: true });
  },
};

// Saved Searches endpoints
export const savedSearchesApi = {
  getSavedSearches: async (): Promise<ApiResponse<SavedSearch[]>> => {
    return apiClient.get('/saved-searches');
  },

  createSavedSearch: async (searchData: {
    name: string;
    filters: any;
    alertsEnabled?: boolean;
  }): Promise<ApiResponse<SavedSearch>> => {
    return apiClient.post('/saved-searches', searchData);
  },

  updateSavedSearch: async (id: string, updates: Partial<SavedSearch>): Promise<ApiResponse<SavedSearch>> => {
    return apiClient.patch(`/saved-searches/${id}`, updates);
  },

  deleteSavedSearch: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/saved-searches/${id}`);
  },

  runSavedSearch: async (id: string): Promise<PaginatedResponse<Job>> => {
    return apiClient.post(`/saved-searches/${id}/run`);
  },
};

// Analytics endpoints
export const analyticsApi = {
  getUserAnalytics: async (): Promise<ApiResponse<{
    totalApplications: number;
    totalJobViews: number;
    averageScore: number;
    topSkills: string[];
    applicationSuccess: number;
    weeklyActivity: Array<{ date: string; applications: number; views: number }>;
  }>> => {
    return apiClient.get('/analytics/user');
  },

  getJobAnalytics: async (jobId: string): Promise<ApiResponse<{
    viewCount: number;
    applicationCount: number;
    averageScore: number;
    topSkills: string[];
    demographics: any;
  }>> => {
    return apiClient.get(`/analytics/jobs/${jobId}`);
  },

  trackEvent: async (event: {
    type: string;
    properties?: Record<string, any>;
  }): Promise<ApiResponse<void>> => {
    return apiClient.post('/analytics/events', event);
  },
};

// Notifications endpoints
export const notificationsApi = {
  getNotifications: async (params?: {
    page?: number;
    limit?: number;
    unreadOnly?: boolean;
  }): Promise<PaginatedResponse<{
    id: string;
    type: string;
    title: string;
    message: string;
    isRead: boolean;
    createdAt: string;
    data?: any;
  }>> => {
    return apiClient.getPaginated('/notifications', params);
  },

  markAsRead: async (notificationId: string): Promise<ApiResponse<void>> => {
    return apiClient.patch(`/notifications/${notificationId}/read`);
  },

  markAllAsRead: async (): Promise<ApiResponse<void>> => {
    return apiClient.patch('/notifications/read-all');
  },

  deleteNotification: async (notificationId: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/notifications/${notificationId}`);
  },

  getUnreadCount: async (): Promise<ApiResponse<{ count: number }>> => {
    return apiClient.get('/notifications/unread-count', { cache: true });
  },

  updateNotificationSettings: async (settings: {
    emailNotifications: boolean;
    pushNotifications: boolean;
    jobAlerts: boolean;
    applicationUpdates: boolean;
  }): Promise<ApiResponse<void>> => {
    return apiClient.patch('/notifications/settings', settings);
  },
};

// Company endpoints
export const companyApi = {
  getCompany: async (id: string): Promise<ApiResponse<{
    id: string;
    name: string;
    description: string;
    logo?: string;
    website?: string;
    size?: string;
    industry?: string;
    location?: string;
    founded?: number;
    benefits?: string[];
    culture?: string[];
  }>> => {
    return apiClient.get(`/companies/${id}`, { cache: true });
  },

  getCompanyJobs: async (id: string, params?: {
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Job>> => {
    return apiClient.getPaginated(`/companies/${id}/jobs`, params, { cache: true });
  },

  followCompany: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.post(`/companies/${id}/follow`);
  },

  unfollowCompany: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/companies/${id}/follow`);
  },

  getFollowedCompanies: async (): Promise<ApiResponse<Array<{
    id: string;
    name: string;
    logo?: string;
  }>>> => {
    return apiClient.get('/companies/followed');
  },
};

// Export all APIs
export const api = {
  auth: authApi,
  user: userApi,
  profile: profileApi,
  jobs: jobApi,
  applications: applicationApi,
  scores: scoreApi,
  savedJobs: savedJobsApi,
  savedSearches: savedSearchesApi,
  analytics: analyticsApi,
  notifications: notificationsApi,
  companies: companyApi,
};

export default api;