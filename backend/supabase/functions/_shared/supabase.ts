/**
 * Shared Supabase client utilities for Edge Functions
 */

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

export function createSupabaseClient(req: Request) {
  const supabaseUrl = Deno.env.get('SUPABASE_URL')!
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

  // Get auth header for user context
  const authorization = req.headers.get('Authorization')

  return createClient(supabaseUrl, supabaseKey, {
    global: {
      headers: authorization ? { authorization } : {},
    },
  })
}

export function createAdminClient() {
  const supabaseUrl = Deno.env.get('SUPABASE_URL')!
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

  return createClient(supabaseUrl, supabaseKey)
}