#!/usr/bin/env node
/**
 * Test script for T068: v0 Frontend Supabase Integration
 * Tests the Supabase client connection and query execution
 */

const { createClient } = require('@supabase/supabase-js')

// Supabase configuration (same as in supabase status output)
const supabaseUrl = 'http://127.0.0.1:54321'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'

// Create Supabase client
const supabase = createClient(supabaseUrl, supabaseAnonKey)

console.log('=' + '='.repeat(59))
console.log('🧪 T068: FRONTEND SUPABASE INTEGRATION TEST')
console.log('=' + '='.repeat(59))

async function runTests() {
  let testsPass = 0
  let testsTotal = 0

  // Test 1: Basic connection test
  console.log('\n📝 Test 1: Basic Supabase connection')
  testsTotal++
  try {
    const { data, error } = await supabase
      .from('prefecture_master')
      .select('count')
      .limit(1)

    if (error) throw error
    console.log('✅ Successfully connected to Supabase')
    testsPass++
  } catch (error) {
    console.log('❌ Failed to connect:', error.message)
  }

  // Test 2: Fetch table data
  console.log('\n📝 Test 2: Fetch table data')
  testsTotal++
  try {
    const { data, error } = await supabase
      .from('job_data')
      .select('*')
      .limit(5)

    if (error) throw error
    console.log(`✅ Successfully fetched ${data.length} rows from job_data table`)
    testsPass++
  } catch (error) {
    console.log('❌ Failed to fetch data:', error.message)
  }

  // Test 3: Execute SQL using RPC
  console.log('\n📝 Test 3: Execute SQL query via RPC')
  testsTotal++
  try {
    const query = 'SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = \'public\''
    const { data, error } = await supabase.rpc('execute_readonly_sql', {
      sql_query: query
    })

    if (error) throw error
    console.log('✅ Successfully executed SQL query via RPC')
    if (data && data.length > 0) {
      console.log(`   Tables in database: ${data[0].table_count}`)
    }
    testsPass++
  } catch (error) {
    console.log('❌ Failed to execute SQL:', error.message)
  }

  // Test 4: Test security restrictions
  console.log('\n📝 Test 4: Security restriction test (should fail)')
  testsTotal++
  try {
    const dangerousQuery = 'DROP TABLE test_table'
    const { data, error } = await supabase.rpc('execute_readonly_sql', {
      sql_query: dangerousQuery
    })

    if (error) {
      console.log('✅ Security check passed - dangerous query blocked')
      console.log(`   Error: ${error.message}`)
      testsPass++
    } else {
      console.log('❌ SECURITY ISSUE: Dangerous query was not blocked!')
    }
  } catch (error) {
    console.log('✅ Security check passed - dangerous query blocked')
    testsPass++
  }

  // Test 5: Query all 20 tables
  console.log('\n📝 Test 5: Query all 20 expected tables')
  testsTotal++
  try {
    const tables = [
      'prefecture_master', 'city_master', 'occupation_master', 'employment_type_master', 'feature_master',
      'job_data', 'user_actions', 'matching_results',
      'basic_scoring', 'seo_scoring', 'personalized_scoring', 'keyword_scoring',
      'batch_jobs', 'processing_logs',
      'email_sections', 'section_jobs', 'email_generation_logs',
      'user_statistics', 'semrush_keywords', 'system_metrics'
    ]

    let tablesFound = 0
    for (const table of tables) {
      const { error } = await supabase.from(table).select('*').limit(1)
      if (!error) tablesFound++
    }

    if (tablesFound === 20) {
      console.log(`✅ All 20 tables are accessible (${tablesFound}/20)`)
      testsPass++
    } else {
      console.log(`⚠️ Only ${tablesFound}/20 tables are accessible`)
    }
  } catch (error) {
    console.log('❌ Failed to query tables:', error.message)
  }

  // Summary
  console.log('\n' + '=' + '='.repeat(59))
  console.log('📊 TEST SUMMARY')
  console.log('=' + '='.repeat(59))
  console.log(`Tests passed: ${testsPass}/${testsTotal}`)

  if (testsPass === testsTotal) {
    console.log('\n✅ T068: Frontend Supabase integration is COMPLETE!')
    console.log('👉 The v0 frontend can now execute queries against Supabase')
    return 0
  } else {
    console.log('\n⚠️ Some tests failed. Please check the configuration.')
    return 1
  }
}

// Run tests
runTests().then(process.exit)