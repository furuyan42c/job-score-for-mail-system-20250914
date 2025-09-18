/**
 * T072: Supabase Auth Integration
 * Authentication utilities and hooks for the frontend
 */

import { createClientComponentClient } from '@supabase/ssr'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import type { User, Session } from '@supabase/supabase-js'

// Types
export interface AuthUser {
  id: string
  email: string
  fullName?: string
  role?: 'user' | 'manager' | 'admin'
  department?: string
  avatarUrl?: string
}

export interface SignUpData {
  email: string
  password: string
  fullName?: string
  department?: string
}

export interface SignInData {
  email: string
  password: string
}

// Create Supabase client
const supabase = createClientComponentClient()

/**
 * Auth service class for managing authentication
 */
export class AuthService {
  /**
   * Sign up a new user
   */
  static async signUp(data: SignUpData) {
    try {
      const { data: authData, error } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
        options: {
          data: {
            full_name: data.fullName,
            department: data.department
          }
        }
      })

      if (error) throw error

      return {
        success: true,
        user: authData.user,
        session: authData.session,
        error: null
      }
    } catch (error: any) {
      return {
        success: false,
        user: null,
        session: null,
        error: error.message || 'Sign up failed'
      }
    }
  }

  /**
   * Sign in an existing user
   */
  static async signIn(data: SignInData) {
    try {
      const { data: authData, error } = await supabase.auth.signInWithPassword({
        email: data.email,
        password: data.password
      })

      if (error) throw error

      // Log sign in event
      if (authData.user) {
        await supabase.rpc('log_auth_event', {
          p_user_id: authData.user.id,
          p_action: 'login',
          p_metadata: { email: data.email }
        })
      }

      return {
        success: true,
        user: authData.user,
        session: authData.session,
        error: null
      }
    } catch (error: any) {
      return {
        success: false,
        user: null,
        session: null,
        error: error.message || 'Sign in failed'
      }
    }
  }

  /**
   * Sign out the current user
   */
  static async signOut() {
    try {
      const { data: { user } } = await supabase.auth.getUser()

      if (user) {
        // Log sign out event
        await supabase.rpc('log_auth_event', {
          p_user_id: user.id,
          p_action: 'logout'
        })
      }

      const { error } = await supabase.auth.signOut()
      if (error) throw error

      return { success: true, error: null }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Sign out failed'
      }
    }
  }

  /**
   * Get the current user
   */
  static async getCurrentUser(): Promise<User | null> {
    try {
      const { data: { user }, error } = await supabase.auth.getUser()
      if (error) throw error
      return user
    } catch (error) {
      console.error('Error getting current user:', error)
      return null
    }
  }

  /**
   * Get the current session
   */
  static async getSession(): Promise<Session | null> {
    try {
      const { data: { session }, error } = await supabase.auth.getSession()
      if (error) throw error
      return session
    } catch (error) {
      console.error('Error getting session:', error)
      return null
    }
  }

  /**
   * Request password reset
   */
  static async requestPasswordReset(email: string) {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`
      })

      if (error) throw error

      return {
        success: true,
        error: null
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Password reset request failed'
      }
    }
  }

  /**
   * Update user password
   */
  static async updatePassword(newPassword: string) {
    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword
      })

      if (error) throw error

      return {
        success: true,
        error: null
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Password update failed'
      }
    }
  }

  /**
   * Get user profile with preferences
   */
  static async getUserProfile(userId: string) {
    try {
      const { data, error } = await supabase.rpc('get_user_profile', {
        p_user_id: userId
      })

      if (error) throw error

      return {
        success: true,
        profile: data?.[0] || null,
        error: null
      }
    } catch (error: any) {
      return {
        success: false,
        profile: null,
        error: error.message || 'Failed to get user profile'
      }
    }
  }

  /**
   * Update user profile
   */
  static async updateProfile(userId: string, updates: Partial<AuthUser>) {
    try {
      const { error } = await supabase
        .from('profiles')
        .update({
          full_name: updates.fullName,
          department: updates.department,
          avatar_url: updates.avatarUrl
        })
        .eq('id', userId)

      if (error) throw error

      return {
        success: true,
        error: null
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Profile update failed'
      }
    }
  }

  /**
   * Check if user has specific role
   */
  static async userHasRole(userId: string, role: 'user' | 'manager' | 'admin') {
    try {
      const { data, error } = await supabase.rpc('user_has_role', {
        p_user_id: userId,
        p_role: role
      })

      if (error) throw error

      return data === true
    } catch (error) {
      console.error('Error checking user role:', error)
      return false
    }
  }
}

/**
 * Hook for managing authentication state
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        setSession(session)
        setUser(session?.user || null)
      } catch (err) {
        setError('Failed to get session')
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event)
        setSession(session)
        setUser(session?.user || null)

        // Handle auth events
        switch (event) {
          case 'SIGNED_IN':
            router.refresh()
            break
          case 'SIGNED_OUT':
            router.push('/auth/login')
            break
          case 'TOKEN_REFRESHED':
            console.log('Token refreshed')
            break
          case 'USER_UPDATED':
            router.refresh()
            break
        }
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [router])

  const signIn = async (data: SignInData) => {
    setLoading(true)
    setError(null)

    const result = await AuthService.signIn(data)

    if (result.success) {
      setUser(result.user)
      setSession(result.session)
    } else {
      setError(result.error)
    }

    setLoading(false)
    return result
  }

  const signUp = async (data: SignUpData) => {
    setLoading(true)
    setError(null)

    const result = await AuthService.signUp(data)

    if (result.success) {
      setUser(result.user)
      setSession(result.session)
    } else {
      setError(result.error)
    }

    setLoading(false)
    return result
  }

  const signOut = async () => {
    setLoading(true)
    const result = await AuthService.signOut()

    if (result.success) {
      setUser(null)
      setSession(null)
    }

    setLoading(false)
    return result
  }

  return {
    user,
    session,
    loading,
    error,
    isAuthenticated: !!user,
    signIn,
    signUp,
    signOut
  }
}

/**
 * Hook for protecting routes that require authentication
 */
export function useRequireAuth(redirectTo: string = '/auth/login') {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push(redirectTo)
    }
  }, [user, loading, router, redirectTo])

  return { user, loading }
}

/**
 * Hook for role-based access control
 */
export function useRequireRole(
  requiredRole: 'user' | 'manager' | 'admin',
  redirectTo: string = '/unauthorized'
) {
  const { user, loading } = useAuth()
  const [hasRole, setHasRole] = useState(false)
  const [checking, setChecking] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const checkRole = async () => {
      if (user) {
        const authorized = await AuthService.userHasRole(user.id, requiredRole)
        setHasRole(authorized)

        if (!authorized) {
          router.push(redirectTo)
        }
      }
      setChecking(false)
    }

    if (!loading) {
      checkRole()
    }
  }, [user, loading, requiredRole, router, redirectTo])

  return {
    user,
    hasRole,
    loading: loading || checking
  }
}

/**
 * Hook for user preferences
 */
export function useUserPreferences() {
  const { user } = useAuth()
  const [preferences, setPreferences] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPreferences = async () => {
      if (user) {
        const { data } = await supabase
          .from('user_preferences')
          .select('*')
          .eq('user_id', user.id)
          .single()

        setPreferences(data)
      }
      setLoading(false)
    }

    fetchPreferences()
  }, [user])

  const updatePreferences = async (updates: any) => {
    if (!user) return

    const { error } = await supabase
      .from('user_preferences')
      .update(updates)
      .eq('user_id', user.id)

    if (!error) {
      setPreferences({ ...preferences, ...updates })
    }

    return { success: !error, error }
  }

  return {
    preferences,
    loading,
    updatePreferences
  }
}