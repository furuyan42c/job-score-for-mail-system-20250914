import { useCallback, useEffect } from 'react';
import { useUserStore, userSelectors } from '../stores/userStore';
import { User, UserProfile, UserPreferences } from '../lib/types';

export const useUser = () => {
  const store = useUserStore();

  // Selectors
  const user = useUserStore(userSelectors.user);
  const profile = useUserStore(userSelectors.profile);
  const isAuthenticated = useUserStore(userSelectors.isAuthenticated);
  const isLoading = useUserStore(userSelectors.isLoading);
  const preferences = useUserStore(userSelectors.preferences);
  const actionHistory = useUserStore(userSelectors.actionHistory);
  const isSessionExpired = useUserStore(userSelectors.isSessionExpired);

  // Actions
  const {
    login,
    register,
    logout,
    updateProfile,
    updatePreferences,
    refreshAuthToken,
    initializeAuth,
    clearError,
    clearHistory,
  } = store;

  // Async action states
  const loginAction = useUserStore(userSelectors.loginAction);
  const registerAction = useUserStore(userSelectors.registerAction);
  const updateProfileAction = useUserStore(userSelectors.updateProfileAction);
  const updatePreferencesAction = useUserStore(userSelectors.updatePreferencesAction);

  // Initialize auth on mount
  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      initializeAuth();
    }
  }, [initializeAuth, isAuthenticated, isLoading]);

  // Auto-refresh token on session expiry warning
  useEffect(() => {
    if (isSessionExpired) {
      refreshAuthToken();
    }
  }, [isSessionExpired, refreshAuthToken]);

  // Utility functions
  const hasPermission = useCallback((permission: string) => {
    if (!user) return false;

    // Basic role-based permissions
    switch (user.role) {
      case 'admin':
        return true;
      case 'recruiter':
        return ['view_jobs', 'create_jobs', 'view_applications'].includes(permission);
      case 'candidate':
        return ['view_jobs', 'apply_jobs', 'view_scores'].includes(permission);
      default:
        return false;
    }
  }, [user]);

  const isEmailVerified = useCallback(() => {
    return user?.isEmailVerified || false;
  }, [user]);

  const getFullName = useCallback(() => {
    if (!user) return '';
    return `${user.firstName} ${user.lastName}`.trim();
  }, [user]);

  const getInitials = useCallback(() => {
    if (!user) return '';
    return `${user.firstName?.[0] || ''}${user.lastName?.[0] || ''}`.toUpperCase();
  }, [user]);

  const hasCompleteProfile = useCallback(() => {
    return !!(
      user &&
      profile &&
      profile.bio &&
      profile.skills?.length &&
      profile.experience &&
      profile.preferences
    );
  }, [user, profile]);

  const getProfileCompleteness = useCallback(() => {
    if (!user || !profile) return 0;

    const fields = [
      !!user.firstName,
      !!user.lastName,
      !!user.email,
      !!profile.bio,
      !!profile.location,
      !!(profile.skills && profile.skills.length > 0),
      !!profile.experience,
      !!profile.preferences?.jobTypes?.length,
      !!profile.preferences?.salaryRange,
    ];

    const completedFields = fields.filter(Boolean).length;
    return Math.round((completedFields / fields.length) * 100);
  }, [user, profile]);

  // Enhanced action wrappers with error handling
  const loginWithErrorHandling = useCallback(async (email: string, password: string) => {
    try {
      await login(email, password);
      return { success: true, error: null };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Login failed' };
    }
  }, [login]);

  const registerWithErrorHandling = useCallback(async (userData: Partial<User>) => {
    try {
      await register(userData);
      return { success: true, error: null };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Registration failed' };
    }
  }, [register]);

  const updateProfileWithErrorHandling = useCallback(async (profileData: Partial<UserProfile>) => {
    try {
      await updateProfile(profileData);
      return { success: true, error: null };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Profile update failed' };
    }
  }, [updateProfile]);

  const updatePreferencesWithErrorHandling = useCallback(async (prefs: Partial<UserPreferences>) => {
    try {
      await updatePreferences(prefs);
      return { success: true, error: null };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Preferences update failed' };
    }
  }, [updatePreferences]);

  return {
    // User data
    user,
    profile,
    preferences,
    isAuthenticated,
    isLoading,
    actionHistory,
    isSessionExpired,

    // Async action states
    loginAction,
    registerAction,
    updateProfileAction,
    updatePreferencesAction,

    // Basic actions
    login: loginWithErrorHandling,
    register: registerWithErrorHandling,
    logout,
    updateProfile: updateProfileWithErrorHandling,
    updatePreferences: updatePreferencesWithErrorHandling,
    refreshAuthToken,
    clearError,
    clearHistory,

    // Utility functions
    hasPermission,
    isEmailVerified,
    getFullName,
    getInitials,
    hasCompleteProfile,
    getProfileCompleteness,

    // Computed values
    isLoggedIn: isAuthenticated && !!user,
    needsEmailVerification: isAuthenticated && !isEmailVerified(),
    profileCompleteness: getProfileCompleteness(),
  };
};

// Specialized hooks for specific use cases
export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    loginAction,
    registerAction,
    isSessionExpired,
    refreshAuthToken,
  } = useUser();

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    loginAction,
    registerAction,
    isSessionExpired,
    refreshAuthToken,
    isLoggedIn: isAuthenticated && !!user,
  };
};

export const useProfile = () => {
  const {
    user,
    profile,
    preferences,
    updateProfile,
    updatePreferences,
    updateProfileAction,
    updatePreferencesAction,
    hasCompleteProfile,
    getProfileCompleteness,
  } = useUser();

  return {
    user,
    profile,
    preferences,
    updateProfile,
    updatePreferences,
    updateProfileAction,
    updatePreferencesAction,
    hasCompleteProfile,
    profileCompleteness: getProfileCompleteness(),
    isProfileComplete: hasCompleteProfile(),
  };
};

export const useUserPreferences = () => {
  const { preferences, updatePreferences, updatePreferencesAction } = useUser();

  const updateTheme = useCallback((theme: 'light' | 'dark' | 'system') => {
    if (!preferences) return;

    updatePreferences({
      ...preferences,
      theme,
    });
  }, [preferences, updatePreferences]);

  const updateNotificationSettings = useCallback((
    emailNotifications: boolean,
    pushNotifications: boolean
  ) => {
    if (!preferences) return;

    updatePreferences({
      ...preferences,
      emailNotifications,
      pushNotifications,
    });
  }, [preferences, updatePreferences]);

  const updateJobPreferences = useCallback((jobPrefs: Partial<UserPreferences>) => {
    if (!preferences) return;

    updatePreferences({
      ...preferences,
      ...jobPrefs,
    });
  }, [preferences, updatePreferences]);

  return {
    preferences,
    updatePreferences,
    updatePreferencesAction,
    updateTheme,
    updateNotificationSettings,
    updateJobPreferences,
    theme: preferences?.theme || 'system',
    emailNotifications: preferences?.emailNotifications ?? true,
    pushNotifications: preferences?.pushNotifications ?? true,
    jobTypes: preferences?.jobTypes || [],
    salaryRange: preferences?.salaryRange,
    locations: preferences?.locations || [],
    remoteWork: preferences?.remoteWork ?? false,
  };
};