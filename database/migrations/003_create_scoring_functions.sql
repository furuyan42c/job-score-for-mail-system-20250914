-- =====================================================================================
-- Migration 003: Create Scoring Functions for Job Matching System
-- =====================================================================================
-- Version: 1.0
-- Created: 2025-09-18
-- Description: Creates comprehensive scoring functions for the 3-stage scoring system
-- Dependencies: 001_create_tables.sql, 002_create_indexes.sql
-- =====================================================================================

-- Import the scoring functions
\i 'database/functions/scoring_functions.sql'

-- =====================================================================================
-- Additional Performance Indexes for Scoring Operations
-- =====================================================================================

-- Index for fee-based filtering (basic scoring requirement)
CREATE INDEX IF NOT EXISTS idx_jobs_fee_filter ON jobs (fee) WHERE fee > 500 AND is_active = TRUE;

-- Index for salary normalization queries
CREATE INDEX IF NOT EXISTS idx_jobs_salary_stats ON jobs (pref_cd, city_cd, min_salary, max_salary) WHERE is_active = TRUE AND min_salary IS NOT NULL;

-- Index for SEO keyword matching
CREATE INDEX IF NOT EXISTS idx_semrush_keywords_volume ON semrush_keywords (search_volume DESC, keyword_difficulty) WHERE search_volume > 0;

-- Index for collaborative filtering queries
CREATE INDEX IF NOT EXISTS idx_user_actions_collab ON user_actions (endcl_cd, action_type, action_timestamp) WHERE action_timestamp > CURRENT_DATE - INTERVAL '90 days';

-- Index for user location-based scoring
CREATE INDEX IF NOT EXISTS idx_users_location_coords ON users (pref_cd, city_cd) WHERE is_active = TRUE;

-- Index for behavioral clustering
CREATE INDEX IF NOT EXISTS idx_user_profiles_cluster ON user_profiles (behavioral_cluster, engagement_score) WHERE behavioral_cluster IS NOT NULL;

-- =====================================================================================
-- Create Materialized Views for Performance Optimization
-- =====================================================================================

-- Materialized view for area salary statistics (refreshed daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_area_salary_stats AS
SELECT
    pref_cd,
    city_cd,
    AVG((min_salary + max_salary) / 2)::INTEGER as avg_salary,
    STDDEV((min_salary + max_salary) / 2) as std_salary,
    MIN(min_salary) as min_salary,
    MAX(max_salary) as max_salary,
    COUNT(*) as job_count
FROM active_jobs
WHERE min_salary IS NOT NULL AND max_salary IS NOT NULL AND min_salary > 0
GROUP BY pref_cd, city_cd;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_area_salary_stats_location ON mv_area_salary_stats (pref_cd, city_cd);

-- Materialized view for company popularity metrics (refreshed daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_company_popularity_current AS
SELECT
    cp.*,
    PERCENT_RANK() OVER (ORDER BY cp.application_rate) * 100 as popularity_percentile
FROM company_popularity cp
WHERE cp.total_applications_360d > 0;

-- Create unique index on company popularity view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_company_popularity_endcl ON mv_company_popularity_current (endcl_cd);

-- =====================================================================================
-- Create Helper Procedures for Batch Operations
-- =====================================================================================

-- Procedure to refresh materialized views (call daily)
CREATE OR REPLACE FUNCTION refresh_scoring_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_area_salary_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_company_popularity_current;

    -- Update statistics for better query planning
    ANALYZE mv_area_salary_stats;
    ANALYZE mv_company_popularity_current;

    RAISE NOTICE 'Scoring materialized views refreshed at %', CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Procedure to update all job enrichment scores in batches
CREATE OR REPLACE FUNCTION daily_scoring_update(
    p_batch_size INTEGER DEFAULT 1000,
    p_max_jobs INTEGER DEFAULT 50000
) RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    -- Log start of batch update
    INSERT INTO batch_jobs (job_type, job_name, status, started_at, total_records)
    VALUES ('scoring', 'Daily Scoring Update', 'running', CURRENT_TIMESTAMP, p_max_jobs);

    -- Refresh materialized views first
    PERFORM refresh_scoring_materialized_views();

    -- Update job enrichment scores
    updated_count := batch_update_enrichment_scores(
        NULL, -- Process all jobs that need updating
        FALSE, -- Don't force recalculation unless needed
        p_batch_size
    );

    -- Update batch job record
    UPDATE batch_jobs
    SET
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP,
        processed_records = updated_count,
        success_count = updated_count
    WHERE job_type = 'scoring'
        AND job_name = 'Daily Scoring Update'
        AND status = 'running'
        AND started_at::DATE = CURRENT_DATE;

    RAISE NOTICE 'Daily scoring update completed. Updated % jobs.', updated_count;

    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================================
-- Create Triggers for Automatic Score Updates
-- =====================================================================================

-- Trigger function to mark jobs for score recalculation when updated
CREATE OR REPLACE FUNCTION mark_job_for_score_recalculation()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark for recalculation if key scoring fields changed
    IF (OLD.min_salary IS DISTINCT FROM NEW.min_salary OR
        OLD.max_salary IS DISTINCT FROM NEW.max_salary OR
        OLD.fee IS DISTINCT FROM NEW.fee OR
        OLD.application_name IS DISTINCT FROM NEW.application_name OR
        OLD.description IS DISTINCT FROM NEW.description OR
        OLD.benefits IS DISTINCT FROM NEW.benefits OR
        OLD.feature_codes IS DISTINCT FROM NEW.feature_codes OR
        OLD.occupation_cd1 IS DISTINCT FROM NEW.occupation_cd1) THEN

        UPDATE job_enrichment
        SET needs_recalculation = TRUE
        WHERE job_id = NEW.job_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on jobs table
CREATE TRIGGER trigger_mark_job_score_recalc
    AFTER UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION mark_job_for_score_recalculation();

-- Trigger function to recalculate user profile scores when actions change
CREATE OR REPLACE FUNCTION update_user_scoring_profile()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user profile scoring-related fields
    UPDATE user_profiles up
    SET
        profile_updated_at = CURRENT_TIMESTAMP,
        -- Increment action counts
        application_count = up.application_count + CASE WHEN NEW.action_type = 'application' THEN 1 ELSE 0 END,
        click_count = up.click_count + CASE WHEN NEW.action_type = 'click' THEN 1 ELSE 0 END,
        -- Update last application date
        last_application_date = CASE
            WHEN NEW.action_type = 'application' AND NEW.action_timestamp::DATE > COALESCE(up.last_application_date, '1900-01-01'::DATE)
            THEN NEW.action_timestamp::DATE
            ELSE up.last_application_date
        END
    WHERE up.user_id = NEW.user_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on user_actions table (if not already exists)
DROP TRIGGER IF EXISTS trigger_update_user_scoring_profile ON user_actions;
CREATE TRIGGER trigger_update_user_scoring_profile
    AFTER INSERT ON user_actions
    FOR EACH ROW
    EXECUTE FUNCTION update_user_scoring_profile();

-- =====================================================================================
-- Create Sample Data for Testing (Optional)
-- =====================================================================================

-- Function to generate test scoring data
CREATE OR REPLACE FUNCTION generate_test_scoring_data()
RETURNS VOID AS $$
BEGIN
    -- Insert sample SEMrush keywords if table is empty
    INSERT INTO semrush_keywords (keyword, search_volume, keyword_difficulty, category)
    SELECT * FROM (VALUES
        ('アルバイト', 50000, 45.5, 'job_type'),
        ('パート', 35000, 42.0, 'job_type'),
        ('高時給', 15000, 38.2, 'salary'),
        ('日払い', 25000, 35.8, 'payment'),
        ('週払い', 8000, 32.1, 'payment'),
        ('未経験歓迎', 18000, 28.9, 'experience'),
        ('学生歓迎', 12000, 26.5, 'target'),
        ('シフト自由', 22000, 31.7, 'flexibility'),
        ('交通費支給', 9500, 29.3, 'benefits'),
        ('リモートワーク', 45000, 52.1, 'work_style'),
        ('在宅勤務', 38000, 48.7, 'work_style'),
        ('短期バイト', 16000, 33.4, 'duration'),
        ('単発バイト', 11000, 30.2, 'duration'),
        ('深夜バイト', 7500, 41.8, 'time'),
        ('土日のみ', 13500, 27.6, 'schedule')
    ) AS t(keyword, search_volume, keyword_difficulty, category)
    WHERE NOT EXISTS (SELECT 1 FROM semrush_keywords LIMIT 1);

    -- Insert sample company popularity data if table is empty
    INSERT INTO company_popularity (endcl_cd, company_name, total_applications_360d, total_clicks_360d, total_views_360d)
    SELECT
        'EX' || LPAD(generate_series(1000000, 1000100)::TEXT, 8, '0'),
        'テスト企業' || generate_series(1000000, 1000100),
        (RANDOM() * 500)::INTEGER + 10,
        (RANDOM() * 2000)::INTEGER + 50,
        (RANDOM() * 10000)::INTEGER + 200
    WHERE NOT EXISTS (SELECT 1 FROM company_popularity LIMIT 1);

    RAISE NOTICE 'Test scoring data generated successfully';
END;
$$ LANGUAGE plpgsql;

-- =====================================================================================
-- Create Performance Monitoring Views
-- =====================================================================================

-- View for scoring performance monitoring
CREATE OR REPLACE VIEW v_scoring_performance AS
SELECT
    'total_jobs' as metric,
    COUNT(*)::TEXT as value
FROM jobs WHERE is_active = TRUE
UNION ALL
SELECT
    'jobs_with_enrichment' as metric,
    COUNT(*)::TEXT as value
FROM job_enrichment je
JOIN jobs j ON je.job_id = j.job_id
WHERE j.is_active = TRUE
UNION ALL
SELECT
    'jobs_need_recalc' as metric,
    COUNT(*)::TEXT as value
FROM job_enrichment
WHERE needs_recalculation = TRUE
UNION ALL
SELECT
    'avg_basic_score' as metric,
    ROUND(AVG(basic_score), 2)::TEXT as value
FROM job_enrichment
WHERE basic_score IS NOT NULL
UNION ALL
SELECT
    'avg_seo_score' as metric,
    ROUND(AVG(seo_score), 2)::TEXT as value
FROM job_enrichment
WHERE seo_score IS NOT NULL
UNION ALL
SELECT
    'avg_composite_score' as metric,
    ROUND(AVG(composite_score), 2)::TEXT as value
FROM job_enrichment
WHERE composite_score IS NOT NULL;

-- =====================================================================================
-- Grant Necessary Permissions
-- =====================================================================================

-- Grant execute permissions on scoring functions (adjust roles as needed)
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO scoring_service_role;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO scoring_read_role;
-- GRANT UPDATE ON job_enrichment TO scoring_update_role;

-- =====================================================================================
-- Migration Completion
-- =====================================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 003 completed successfully at %', CURRENT_TIMESTAMP;
    RAISE NOTICE 'Scoring functions created and ready for use';
    RAISE NOTICE 'Run daily_scoring_update() to process all jobs';
    RAISE NOTICE 'Run generate_test_scoring_data() to create sample data for testing';
END
$$;

-- =====================================================================================
-- END OF MIGRATION
-- =====================================================================================