/**
 * Supabase Client Configuration
 *
 * This module provides configured Supabase clients for both server and browser contexts.
 * It handles authentication, real-time subscriptions, and proper TypeScript typing.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { Database } from './types';

// Environment validation
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

/**
 * Browser client for client-side operations
 * Handles authentication state, real-time subscriptions
 */
export const supabase: SupabaseClient<Database> = createClient<Database>(
  supabaseUrl,
  supabaseAnonKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      flowType: 'pkce',
    },
    realtime: {
      params: {
        eventsPerSecond: 10,
      },
    },
    db: {
      schema: 'public',
    },
    global: {
      headers: {
        'X-Client-Info': 'job-matching-frontend',
      },
    },
  }
);

/**
 * Server client for server-side operations (SSR, API routes)
 * Properly handles cookies and server-side authentication
 */
export function createServerSupabaseClient() {
  const cookieStore = cookies();

  return createServerClient<Database>(
    supabaseUrl,
    supabaseAnonKey,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
        set(name: string, value: string, options) {
          cookieStore.set(name, value, options);
        },
        remove(name: string, options) {
          cookieStore.delete(name);
        },
      },
    }
  );
}

/**
 * Service role client for admin operations
 * Only available server-side with elevated permissions
 */
export function createServiceRoleClient() {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!serviceRoleKey) {
    throw new Error('Service role key not available');
  }

  return createClient<Database>(supabaseUrl, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}

/**
 * Real-time subscription utilities
 */
export class RealtimeManager {
  private subscriptions = new Map<string, any>();

  /**
   * Subscribe to batch execution status changes
   */
  subscribeToBatchStatus(
    batchId: string,
    callback: (payload: any) => void
  ) {
    const subscription = supabase
      .channel(`batch-${batchId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'batch_executions',
          filter: `batch_id=eq.${batchId}`,
        },
        callback
      )
      .subscribe();

    this.subscriptions.set(`batch-${batchId}`, subscription);
    return subscription;
  }

  /**
   * Subscribe to system logs for monitoring
   */
  subscribeToLogs(callback: (payload: any) => void) {
    const subscription = supabase
      .channel('system-logs')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'system_logs',
        },
        callback
      )
      .subscribe();

    this.subscriptions.set('system-logs', subscription);
    return subscription;
  }

  /**
   * Subscribe to scoring progress updates
   */
  subscribeToScoringProgress(callback: (payload: any) => void) {
    const subscription = supabase
      .channel('scoring-progress')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'scoring_calculation_results',
        },
        callback
      )
      .subscribe();

    this.subscriptions.set('scoring-progress', subscription);
    return subscription;
  }

  /**
   * Unsubscribe from a specific channel
   */
  unsubscribe(channelId: string) {
    const subscription = this.subscriptions.get(channelId);
    if (subscription) {
      subscription.unsubscribe();
      this.subscriptions.delete(channelId);
    }
  }

  /**
   * Unsubscribe from all channels
   */
  unsubscribeAll() {
    for (const [channelId, subscription] of this.subscriptions) {
      subscription.unsubscribe();
    }
    this.subscriptions.clear();
  }
}

// Global realtime manager instance
export const realtimeManager = new RealtimeManager();

/**
 * Authentication utilities
 */
export class AuthManager {
  /**
   * Get current user session
   */
  static async getCurrentUser() {
    const { data: { user }, error } = await supabase.auth.getUser();
    return { user, error };
  }

  /**
   * Sign in with email and password
   */
  static async signIn(email: string, password: string) {
    return await supabase.auth.signInWithPassword({
      email,
      password,
    });
  }

  /**
   * Sign up with email and password
   */
  static async signUp(email: string, password: string, metadata?: object) {
    return await supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata,
      },
    });
  }

  /**
   * Sign out current user
   */
  static async signOut() {
    return await supabase.auth.signOut();
  }

  /**
   * Listen to auth state changes
   */
  static onAuthStateChange(callback: (event: string, session: any) => void) {
    return supabase.auth.onAuthStateChange(callback);
  }
}

/**
 * Database utilities
 */
export class DatabaseUtils {
  /**
   * Test database connection
   */
  static async testConnection() {
    try {
      const { data, error } = await supabase
        .from('prefecture_master')
        .select('count(*)')
        .single();

      return { success: !error, error };
    } catch (error) {
      return { success: false, error };
    }
  }

  /**
   * Execute raw SQL query (admin only)
   */
  static async executeRawSQL(query: string) {
    const { data, error } = await supabase.rpc('execute_sql', {
      query_text: query,
    });

    return { data, error };
  }

  /**
   * Get database health metrics
   */
  static async getHealthMetrics() {
    const { data, error } = await supabase.rpc('get_database_health');
    return { data, error };
  }
}

// Export configured clients
export { supabase as default };