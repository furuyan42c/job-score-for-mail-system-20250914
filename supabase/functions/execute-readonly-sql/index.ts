/**
 * T069 GREEN Phase: Supabase Edge Function for safe SQL execution
 * このEdge Functionは読み取り専用のSQLクエリを安全に実行します
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse request body
    const { sql_query } = await req.json()

    if (!sql_query || typeof sql_query !== 'string') {
      return new Response(
        JSON.stringify({ error: 'SQL query is required' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      )
    }

    // Security: Only allow SELECT queries
    const trimmedQuery = sql_query.trim().toLowerCase()
    if (!trimmedQuery.startsWith('select')) {
      return new Response(
        JSON.stringify({ error: 'Only SELECT queries are allowed' }),
        {
          status: 403,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      )
    }

    // Check for dangerous keywords
    const dangerousKeywords = ['drop', 'delete', 'update', 'insert', 'create', 'alter', 'truncate']
    for (const keyword of dangerousKeywords) {
      if (trimmedQuery.includes(keyword)) {
        return new Response(
          JSON.stringify({ error: `Keyword '${keyword}' is not allowed` }),
          {
            status: 403,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          }
        )
      }
    }

    // Create Supabase client with service role key for database access
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Execute the SQL query using raw SQL execution
    // Note: This uses rpc to execute raw SQL safely
    const { data, error } = await supabase.rpc('execute_sql_query', {
      query_text: sql_query
    })

    if (error) {
      return new Response(
        JSON.stringify({ error: error.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      )
    }

    return new Response(
      JSON.stringify(data),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )
  }
})