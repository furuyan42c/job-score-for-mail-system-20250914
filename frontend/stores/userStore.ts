import { create } from 'zustand';
import { createStoreWithMiddleware, type StoreCreator, handleAsyncError, createAsyncAction } from '../lib/utils/store-middleware';
import {
  User,
  UserProfile,
  AuthState,
  UserPreferences,
  AsyncAction,
  ApiResponse
} from '../lib/types';

// API functions (to be implemented separately)
const userApi = {
  login: async (email: string, password: string): Promise<ApiResponse<AuthState>> => {
    // Mock implementation - replace with actual API call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            user: {
              id: '1',
              email,
              username: email.split('@')[0],
              firstName: 'John',
              lastName: 'Doe',
              role: 'candidate',
              isEmailVerified: true,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            },
            profile: null,
            isAuthenticated: true,
            isLoading: false,
            accessToken: 'mock-access-token',
            refreshToken: 'mock-refresh-token',
            sessionExpiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          }
        });
      }, 1000);
    });
  },

  logout: async (): Promise<ApiResponse<void>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ status: 'success', data: undefined });
      }, 500);
    });
  },

  register: async (userData: Partial<User>): Promise<ApiResponse<AuthState>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            user: {
              id: Math.random().toString(),
              email: userData.email!,
              username: userData.username!,
              firstName: userData.firstName!,
              lastName: userData.lastName!,
              role: 'candidate',
              isEmailVerified: false,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            },
            profile: null,
            isAuthenticated: true,
            isLoading: false,
            accessToken: 'mock-access-token',
            refreshToken: 'mock-refresh-token',
            sessionExpiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          }
        });
      }, 1000);
    });
  },

  updateProfile: async (profileData: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            id: '1',
            userId: '1',
            bio: profileData.bio || '',
            location: profileData.location || '',
            website: profileData.website || '',
            linkedinUrl: profileData.linkedinUrl || '',
            githubUrl: profileData.githubUrl || '',
            experience: profileData.experience || 'mid',
            skills: profileData.skills || [],
            preferences: profileData.preferences || {
              jobTypes: ['full-time'],
              salaryRange: { min: 50000, max: 100000, currency: 'USD' },
              locations: [],
              remoteWork: true,
              emailNotifications: true,
              pushNotifications: true,
              theme: 'system',
            },
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
        });
      }, 1000);
    });
  },

  updatePreferences: async (preferences: Partial<UserPreferences>): Promise<ApiResponse<UserPreferences>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            jobTypes: ['full-time'],
            salaryRange: { min: 50000, max: 100000, currency: 'USD' },
            locations: [],
            remoteWork: true,
            emailNotifications: true,
            pushNotifications: true,
            theme: 'system',
            ...preferences,
          }
        });
      }, 1000);
    });
  },

  refreshToken: async (refreshToken: string): Promise<ApiResponse<{ accessToken: string; expiresAt: string }>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            accessToken: 'new-mock-access-token',
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          }
        });
      }, 500);
    });
  },

  getCurrentUser: async (): Promise<ApiResponse<{ user: User; profile: UserProfile | null }>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          data: {
            user: {
              id: '1',
              email: 'user@example.com',
              username: 'user',
              firstName: 'John',
              lastName: 'Doe',
              role: 'candidate',
              isEmailVerified: true,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            },
            profile: null,
          }
        });
      }, 500);
    });
  },
};

interface UserState extends AuthState {
  // Action history
  actionHistory: Array<{
    action: string;
    timestamp: string;
    details?: any;
  }>;

  // Async action states
  loginAction: AsyncAction;
  registerAction: AsyncAction;
  updateProfileAction: AsyncAction;
  updatePreferencesAction: AsyncAction;

  // Session management
  sessionTimeout: NodeJS.Timeout | null;
  isSessionExpired: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (userData: Partial<User>) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (profileData: Partial<UserProfile>) => Promise<void>;
  updatePreferences: (preferences: Partial<UserPreferences>) => Promise<void>;
  refreshAuthToken: () => Promise<void>;
  checkSession: () => void;
  clearError: (actionType: string) => void;
  addToHistory: (action: string, details?: any) => void;
  clearHistory: () => void;
  initializeAuth: () => Promise<void>;
  setUser: (user: User | null) => void;
  setProfile: (profile: UserProfile | null) => void;
  resetStore: () => void;
}

const initialState: Omit<UserState, keyof UserActions> = {
  user: null,
  profile: null,
  isAuthenticated: false,
  isLoading: false,
  accessToken: null,
  refreshToken: null,
  sessionExpiresAt: null,
  actionHistory: [],
  loginAction: { isLoading: false, error: null, data: null, lastFetch: null },
  registerAction: { isLoading: false, error: null, data: null, lastFetch: null },
  updateProfileAction: { isLoading: false, error: null, data: null, lastFetch: null },
  updatePreferencesAction: { isLoading: false, error: null, data: null, lastFetch: null },
  sessionTimeout: null,
  isSessionExpired: false,
};

type UserActions = Pick<UserState,
  | 'login'
  | 'register'
  | 'logout'
  | 'updateProfile'
  | 'updatePreferences'
  | 'refreshAuthToken'
  | 'checkSession'
  | 'clearError'
  | 'addToHistory'
  | 'clearHistory'
  | 'initializeAuth'
  | 'setUser'
  | 'setProfile'
  | 'resetStore'
>;

const userStoreCreator: StoreCreator<UserState> = (set, get) => ({
  ...initialState,

  login: async (email: string, password: string) => {
    set((state) => {
      state.loginAction.isLoading = true;
      state.loginAction.error = null;
    });

    try {
      const response = await userApi.login(email, password);

      if (response.status === 'success') {
        set((state) => {
          const { user, profile, accessToken, refreshToken, sessionExpiresAt } = response.data;
          state.user = user;
          state.profile = profile;
          state.isAuthenticated = true;
          state.accessToken = accessToken;
          state.refreshToken = refreshToken;
          state.sessionExpiresAt = sessionExpiresAt;
          state.loginAction.isLoading = false;
          state.loginAction.data = response.data;
          state.loginAction.lastFetch = new Date().toISOString();
        });

        get().addToHistory('login', { email });
        get().checkSession();
      }
    } catch (error) {
      set((state) => {
        state.loginAction.isLoading = false;
        state.loginAction.error = handleAsyncError(error);
      });
    }
  },

  register: async (userData: Partial<User>) => {
    set((state) => {
      state.registerAction.isLoading = true;
      state.registerAction.error = null;
    });

    try {
      const response = await userApi.register(userData);

      if (response.status === 'success') {
        set((state) => {
          const { user, profile, accessToken, refreshToken, sessionExpiresAt } = response.data;
          state.user = user;
          state.profile = profile;
          state.isAuthenticated = true;
          state.accessToken = accessToken;
          state.refreshToken = refreshToken;
          state.sessionExpiresAt = sessionExpiresAt;
          state.registerAction.isLoading = false;
          state.registerAction.data = response.data;
          state.registerAction.lastFetch = new Date().toISOString();
        });

        get().addToHistory('register', { email: userData.email });
        get().checkSession();
      }
    } catch (error) {
      set((state) => {
        state.registerAction.isLoading = false;
        state.registerAction.error = handleAsyncError(error);
      });
    }
  },

  logout: async () => {
    try {
      await userApi.logout();

      set((state) => {
        if (state.sessionTimeout) {
          clearTimeout(state.sessionTimeout);
        }
        state.user = null;
        state.profile = null;
        state.isAuthenticated = false;
        state.accessToken = null;
        state.refreshToken = null;
        state.sessionExpiresAt = null;
        state.sessionTimeout = null;
        state.isSessionExpired = false;
        // Reset async actions
        state.loginAction = { isLoading: false, error: null, data: null, lastFetch: null };
        state.registerAction = { isLoading: false, error: null, data: null, lastFetch: null };
        state.updateProfileAction = { isLoading: false, error: null, data: null, lastFetch: null };
        state.updatePreferencesAction = { isLoading: false, error: null, data: null, lastFetch: null };
      });

      get().addToHistory('logout');
    } catch (error) {
      console.error('Logout error:', error);
    }
  },

  updateProfile: async (profileData: Partial<UserProfile>) => {
    set((state) => {
      state.updateProfileAction.isLoading = true;
      state.updateProfileAction.error = null;
    });

    try {
      const response = await userApi.updateProfile(profileData);

      if (response.status === 'success') {
        set((state) => {
          state.profile = response.data;
          state.updateProfileAction.isLoading = false;
          state.updateProfileAction.data = response.data;
          state.updateProfileAction.lastFetch = new Date().toISOString();
        });

        get().addToHistory('updateProfile', profileData);
      }
    } catch (error) {
      set((state) => {
        state.updateProfileAction.isLoading = false;
        state.updateProfileAction.error = handleAsyncError(error);
      });
    }
  },

  updatePreferences: async (preferences: Partial<UserPreferences>) => {
    set((state) => {
      state.updatePreferencesAction.isLoading = true;
      state.updatePreferencesAction.error = null;
    });

    try {
      const response = await userApi.updatePreferences(preferences);

      if (response.status === 'success') {
        set((state) => {
          if (state.profile) {
            state.profile.preferences = response.data;
          }
          state.updatePreferencesAction.isLoading = false;
          state.updatePreferencesAction.data = response.data;
          state.updatePreferencesAction.lastFetch = new Date().toISOString();
        });

        get().addToHistory('updatePreferences', preferences);
      }
    } catch (error) {
      set((state) => {
        state.updatePreferencesAction.isLoading = false;
        state.updatePreferencesAction.error = handleAsyncError(error);
      });
    }
  },

  refreshAuthToken: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return;

    try {
      const response = await userApi.refreshToken(refreshToken);

      if (response.status === 'success') {
        set((state) => {
          state.accessToken = response.data.accessToken;
          state.sessionExpiresAt = response.data.expiresAt;
          state.isSessionExpired = false;
        });

        get().checkSession();
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      get().logout();
    }
  },

  checkSession: () => {
    const { sessionExpiresAt, sessionTimeout } = get();

    if (sessionTimeout) {
      clearTimeout(sessionTimeout);
    }

    if (!sessionExpiresAt) return;

    const expiresAt = new Date(sessionExpiresAt).getTime();
    const now = Date.now();
    const timeUntilExpiry = expiresAt - now;

    if (timeUntilExpiry <= 0) {
      set((state) => {
        state.isSessionExpired = true;
      });
      get().logout();
    } else {
      // Refresh token 5 minutes before expiry
      const refreshTime = Math.max(timeUntilExpiry - 5 * 60 * 1000, 0);

      const timeout = setTimeout(() => {
        get().refreshAuthToken();
      }, refreshTime);

      set((state) => {
        state.sessionTimeout = timeout;
      });
    }
  },

  clearError: (actionType: string) => {
    set((state) => {
      const action = state[`${actionType}Action` as keyof UserState] as AsyncAction;
      if (action) {
        action.error = null;
      }
    });
  },

  addToHistory: (action: string, details?: any) => {
    set((state) => {
      state.actionHistory.unshift({
        action,
        timestamp: new Date().toISOString(),
        details,
      });

      // Keep only last 50 actions
      if (state.actionHistory.length > 50) {
        state.actionHistory = state.actionHistory.slice(0, 50);
      }
    });
  },

  clearHistory: () => {
    set((state) => {
      state.actionHistory = [];
    });
  },

  initializeAuth: async () => {
    set((state) => {
      state.isLoading = true;
    });

    try {
      const response = await userApi.getCurrentUser();

      if (response.status === 'success') {
        set((state) => {
          state.user = response.data.user;
          state.profile = response.data.profile;
          state.isAuthenticated = true;
          state.isLoading = false;
        });

        get().checkSession();
      }
    } catch (error) {
      set((state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
      });
    }
  },

  setUser: (user: User | null) => {
    set((state) => {
      state.user = user;
      state.isAuthenticated = !!user;
    });
  },

  setProfile: (profile: UserProfile | null) => {
    set((state) => {
      state.profile = profile;
    });
  },

  resetStore: () => {
    set((state) => {
      if (state.sessionTimeout) {
        clearTimeout(state.sessionTimeout);
      }
      Object.assign(state, initialState);
    });
  },
});

export const useUserStore = create(
  createStoreWithMiddleware(userStoreCreator, {
    name: 'user-store',
    persist: {
      partialize: (state) => ({
        user: state.user,
        profile: state.profile,
        isAuthenticated: state.isAuthenticated,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        sessionExpiresAt: state.sessionExpiresAt,
        actionHistory: state.actionHistory.slice(0, 10), // Only persist last 10 actions
      }),
      version: 1,
    },
  })
);

// Selectors for optimized re-renders
export const userSelectors = {
  user: (state: UserState) => state.user,
  profile: (state: UserState) => state.profile,
  isAuthenticated: (state: UserState) => state.isAuthenticated,
  isLoading: (state: UserState) => state.isLoading,
  preferences: (state: UserState) => state.profile?.preferences,
  actionHistory: (state: UserState) => state.actionHistory,
  loginAction: (state: UserState) => state.loginAction,
  registerAction: (state: UserState) => state.registerAction,
  updateProfileAction: (state: UserState) => state.updateProfileAction,
  updatePreferencesAction: (state: UserState) => state.updatePreferencesAction,
  isSessionExpired: (state: UserState) => state.isSessionExpired,
};