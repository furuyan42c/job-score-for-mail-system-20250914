-- =====================================================================================
-- Job Matching System - Scoring Functions Usage Examples
-- =====================================================================================
-- Version: 1.0
-- Created: 2025-09-18
-- Description: Comprehensive examples showing how to use the scoring functions
-- =====================================================================================

-- =====================================================================================
-- SECTION 1: BASIC SCORE CALCULATION EXAMPLES
-- =====================================================================================

-- Example 1.1: Calculate basic score for a specific job
-- This demonstrates fee, hourly wage, and company popularity scoring
SELECT
    j.job_id,
    j.application_name,
    j.company_name,
    j.min_salary,
    j.max_salary,
    j.fee,
    calculate_basic_score(j.job_id) as basic_score,
    -- Component breakdown for analysis
    normalize_hourly_wage_score((j.min_salary + j.max_salary) / 2, j.pref_cd, j.city_cd) as wage_score,
    normalize_fee_score(j.fee) as fee_score,
    calculate_company_popularity_score(j.endcl_cd) as popularity_score
FROM jobs j
WHERE j.is_active = TRUE
    AND j.fee > 500  -- Business rule: fee must be > 500
LIMIT 10;

-- Example 1.2: Find high-scoring jobs by basic criteria
-- Jobs with fee > 500, good wage for area, and popular companies
SELECT
    j.job_id,
    j.application_name,
    j.company_name,
    j.pref_cd,
    CONCAT(j.min_salary, '-', j.max_salary, '円') as salary_range,
    j.fee || '円' as fee,
    calculate_basic_score(j.job_id) as basic_score
FROM jobs j
WHERE j.is_active = TRUE
    AND j.fee > 500
    AND calculate_basic_score(j.job_id) >= 70  -- High basic score threshold
ORDER BY calculate_basic_score(j.job_id) DESC
LIMIT 20;

-- Example 1.3: Area salary comparison
-- Compare average salaries across different prefectures
SELECT
    pm.name as prefecture,
    stats.avg_salary,
    stats.std_salary,
    stats.sample_count,
    -- Show how a 1500 yen wage would score in this area
    normalize_hourly_wage_score(1500, pm.code, NULL) as wage_1500_score
FROM prefecture_master pm
CROSS JOIN LATERAL calculate_area_salary_stats(pm.code, NULL, 'prefecture') stats
WHERE stats.sample_count > 10  -- Only areas with sufficient data
ORDER BY stats.avg_salary DESC;

-- =====================================================================================
-- SECTION 2: SEO SCORE CALCULATION EXAMPLES
-- =====================================================================================

-- Example 2.1: Calculate SEO scores for jobs with keyword analysis
SELECT
    j.job_id,
    j.application_name,
    j.company_name,
    calculate_seo_score(j.job_id) as seo_score,
    -- Show extracted keywords
    extract_job_keywords(j.application_name, j.description, j.benefits) as extracted_keywords,
    -- Calculate keyword density
    calculate_keyword_density_score(j.job_id) as density_score
FROM jobs j
WHERE j.is_active = TRUE
    AND LENGTH(j.application_name) > 10  -- Jobs with substantial content
LIMIT 15;

-- Example 2.2: Jobs with high SEO potential
-- Find jobs that match popular keywords
SELECT
    j.job_id,
    j.application_name,
    j.company_name,
    calculate_seo_score(j.job_id) as seo_score,
    -- Count matching SEMrush keywords
    (SELECT COUNT(*)
     FROM semrush_keywords sk
     WHERE LOWER(j.application_name) LIKE '%' || sk.keyword || '%'
        OR LOWER(j.description) LIKE '%' || sk.keyword || '%') as keyword_matches
FROM jobs j
WHERE j.is_active = TRUE
    AND calculate_seo_score(j.job_id) >= 50  -- Good SEO score threshold
ORDER BY calculate_seo_score(j.job_id) DESC
LIMIT 20;

-- Example 2.3: Keyword performance analysis
-- Analyze which keywords appear most in high-scoring jobs
SELECT
    sk.keyword,
    sk.search_volume,
    sk.category,
    COUNT(*) as job_count,
    AVG(calculate_seo_score(j.job_id)) as avg_seo_score
FROM semrush_keywords sk
CROSS JOIN jobs j
WHERE j.is_active = TRUE
    AND (LOWER(j.application_name) LIKE '%' || sk.keyword || '%'
         OR LOWER(j.description) LIKE '%' || sk.keyword || '%')
GROUP BY sk.keyword, sk.search_volume, sk.category
HAVING COUNT(*) >= 5  -- Keywords appearing in at least 5 jobs
ORDER BY avg_seo_score DESC, job_count DESC
LIMIT 30;

-- =====================================================================================
-- SECTION 3: PERSONALIZED SCORE CALCULATION EXAMPLES
-- =====================================================================================

-- Example 3.1: Calculate personalized scores for a specific user
-- Shows how jobs are scored differently for different users
WITH user_scores AS (
    SELECT
        j.job_id,
        j.application_name,
        j.company_name,
        j.occupation_cd1,
        calculate_personalized_score(1001, j.job_id) as personalized_score,
        -- Component breakdown
        calculate_user_preference_score(1001, j.job_id) as preference_score,
        calculate_collaborative_filtering_score(1001, j.job_id) as collab_score,
        calculate_location_proximity_score(1001, j.job_id) as location_score
    FROM jobs j
    WHERE j.is_active = TRUE
    LIMIT 50
)
SELECT *
FROM user_scores
WHERE personalized_score > 0
ORDER BY personalized_score DESC
LIMIT 20;

-- Example 3.2: Compare personalization across different users
-- Shows how the same jobs score differently for different user profiles
SELECT
    j.job_id,
    j.application_name,
    j.pref_cd,
    calculate_personalized_score(1001, j.job_id) as user_1001_score,
    calculate_personalized_score(1002, j.job_id) as user_1002_score,
    calculate_personalized_score(1003, j.job_id) as user_1003_score,
    -- Show the difference in personalization
    ABS(calculate_personalized_score(1001, j.job_id) - calculate_personalized_score(1002, j.job_id)) as score_variance
FROM jobs j
WHERE j.is_active = TRUE
    AND j.job_id IN (
        SELECT job_id FROM jobs WHERE is_active = TRUE ORDER BY RANDOM() LIMIT 20
    )
ORDER BY score_variance DESC;

-- Example 3.3: Location-based scoring analysis
-- Show how distance affects job scoring
SELECT
    j.job_id,
    j.application_name,
    j.pref_cd,
    j.city_cd,
    j.latitude,
    j.longitude,
    -- Calculate distance and location score for specific user
    calculate_distance_km(
        j.latitude, j.longitude,
        (SELECT cm.latitude FROM users u JOIN city_master cm ON u.city_cd = cm.code WHERE u.user_id = 1001),
        (SELECT cm.longitude FROM users u JOIN city_master cm ON u.city_cd = cm.code WHERE u.user_id = 1001)
    ) as distance_km,
    calculate_location_proximity_score(1001, j.job_id) as location_score
FROM jobs j
WHERE j.is_active = TRUE
    AND j.latitude IS NOT NULL
    AND j.longitude IS NOT NULL
ORDER BY distance_km
LIMIT 25;

-- =====================================================================================
-- SECTION 4: COMPOSITE SCORE CALCULATION EXAMPLES
-- =====================================================================================

-- Example 4.1: Calculate composite scores with default weights
-- Shows the final combined scoring for user-job pairs
SELECT
    j.job_id,
    j.application_name,
    j.company_name,
    j.fee,
    -- Individual component scores
    calculate_basic_score(j.job_id) as basic_score,
    calculate_seo_score(j.job_id) as seo_score,
    calculate_personalized_score(1001, j.job_id) as personalized_score,
    -- Final composite score (Basic: 30%, SEO: 20%, Personal: 50%)
    calculate_composite_score(j.job_id, 1001) as composite_score
FROM jobs j
WHERE j.is_active = TRUE
    AND j.fee > 500
ORDER BY calculate_composite_score(j.job_id, 1001) DESC
LIMIT 25;

-- Example 4.2: A/B test different scoring weights
-- Compare results with different weight configurations
WITH weight_comparison AS (
    SELECT
        j.job_id,
        j.application_name,
        -- Default weights (30/20/50)
        calculate_composite_score(j.job_id, 1001, 0.30, 0.20, 0.50) as default_score,
        -- Basic-heavy weights (50/20/30)
        calculate_composite_score(j.job_id, 1001, 0.50, 0.20, 0.30) as basic_heavy_score,
        -- SEO-heavy weights (20/40/40)
        calculate_composite_score(j.job_id, 1001, 0.20, 0.40, 0.40) as seo_heavy_score,
        -- Personal-heavy weights (20/10/70)
        calculate_composite_score(j.job_id, 1001, 0.20, 0.10, 0.70) as personal_heavy_score
    FROM jobs j
    WHERE j.is_active = TRUE
        AND j.fee > 500
    LIMIT 100
)
SELECT
    job_id,
    application_name,
    default_score,
    basic_heavy_score,
    seo_heavy_score,
    personal_heavy_score,
    -- Show which weight configuration ranks this job highest
    CASE
        WHEN default_score >= basic_heavy_score AND default_score >= seo_heavy_score AND default_score >= personal_heavy_score THEN 'default'
        WHEN basic_heavy_score >= seo_heavy_score AND basic_heavy_score >= personal_heavy_score THEN 'basic_heavy'
        WHEN seo_heavy_score >= personal_heavy_score THEN 'seo_heavy'
        ELSE 'personal_heavy'
    END as best_weight_config
FROM weight_comparison
ORDER BY default_score DESC
LIMIT 20;

-- =====================================================================================
-- SECTION 5: BATCH PROCESSING EXAMPLES
-- =====================================================================================

-- Example 5.1: Batch calculate scores for multiple jobs
-- Efficiently process many jobs at once
SELECT *
FROM batch_calculate_scores(
    -- Use array of job IDs (replace with actual IDs)
    ARRAY[
        (SELECT job_id FROM jobs WHERE is_active = TRUE ORDER BY posting_date DESC LIMIT 1 OFFSET 0),
        (SELECT job_id FROM jobs WHERE is_active = TRUE ORDER BY posting_date DESC LIMIT 1 OFFSET 1),
        (SELECT job_id FROM jobs WHERE is_active = TRUE ORDER BY posting_date DESC LIMIT 1 OFFSET 2),
        (SELECT job_id FROM jobs WHERE is_active = TRUE ORDER BY posting_date DESC LIMIT 1 OFFSET 3),
        (SELECT job_id FROM jobs WHERE is_active = TRUE ORDER BY posting_date DESC LIMIT 1 OFFSET 4)
    ],
    1001,  -- User ID
    ARRAY['basic', 'seo', 'personalized', 'composite']  -- Score types to calculate
);

-- Example 5.2: Process all active jobs for enrichment scoring
-- Update job_enrichment table with latest scores
SELECT
    'Jobs processed: ' || batch_update_enrichment_scores(
        NULL,    -- Process all jobs that need updating
        FALSE,   -- Don't force recalculation
        100      -- Batch size
    ) as result;

-- Example 5.3: Identify jobs that need score recalculation
-- Find jobs that haven't been scored recently or need updates
SELECT
    j.job_id,
    j.application_name,
    j.updated_at as job_updated,
    je.calculated_at as last_scored,
    je.needs_recalculation,
    CASE
        WHEN je.job_id IS NULL THEN 'Never scored'
        WHEN je.needs_recalculation THEN 'Flagged for recalc'
        WHEN je.calculated_at < CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'Stale score'
        ELSE 'Up to date'
    END as score_status
FROM jobs j
LEFT JOIN job_enrichment je ON j.job_id = je.job_id
WHERE j.is_active = TRUE
    AND (je.job_id IS NULL
         OR je.needs_recalculation = TRUE
         OR je.calculated_at < CURRENT_TIMESTAMP - INTERVAL '7 days')
ORDER BY j.updated_at DESC
LIMIT 50;

-- =====================================================================================
-- SECTION 6: PERFORMANCE MONITORING EXAMPLES
-- =====================================================================================

-- Example 6.1: Scoring performance statistics
-- Monitor the health and performance of the scoring system
SELECT * FROM get_scoring_performance_stats()
ORDER BY metric_name;

-- Example 6.2: Score distribution analysis
-- Understand how scores are distributed across the job database
SELECT
    'Basic Score Distribution' as metric_type,
    CASE
        WHEN basic_score >= 80 THEN '80-100 (Excellent)'
        WHEN basic_score >= 60 THEN '60-79 (Good)'
        WHEN basic_score >= 40 THEN '40-59 (Average)'
        WHEN basic_score >= 20 THEN '20-39 (Below Average)'
        ELSE '0-19 (Poor)'
    END as score_range,
    COUNT(*) as job_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM job_enrichment
WHERE basic_score IS NOT NULL
GROUP BY
    CASE
        WHEN basic_score >= 80 THEN '80-100 (Excellent)'
        WHEN basic_score >= 60 THEN '60-79 (Good)'
        WHEN basic_score >= 40 THEN '40-59 (Average)'
        WHEN basic_score >= 20 THEN '20-39 (Below Average)'
        ELSE '0-19 (Poor)'
    END
UNION ALL
SELECT
    'SEO Score Distribution' as metric_type,
    CASE
        WHEN seo_score >= 80 THEN '80-100 (Excellent)'
        WHEN seo_score >= 60 THEN '60-79 (Good)'
        WHEN seo_score >= 40 THEN '40-59 (Average)'
        WHEN seo_score >= 20 THEN '20-39 (Below Average)'
        ELSE '0-19 (Poor)'
    END as score_range,
    COUNT(*) as job_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM job_enrichment
WHERE seo_score IS NOT NULL
GROUP BY
    CASE
        WHEN seo_score >= 80 THEN '80-100 (Excellent)'
        WHEN seo_score >= 60 THEN '60-79 (Good)'
        WHEN seo_score >= 40 THEN '40-59 (Average)'
        WHEN seo_score >= 20 THEN '20-39 (Below Average)'
        ELSE '0-19 (Poor)'
    END
ORDER BY metric_type, score_range;

-- Example 6.3: Scoring function performance analysis
-- Measure how long scoring functions take to execute
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    j.job_id,
    calculate_basic_score(j.job_id) as basic_score,
    calculate_seo_score(j.job_id) as seo_score,
    calculate_personalized_score(1001, j.job_id) as personalized_score
FROM jobs j
WHERE j.is_active = TRUE
LIMIT 100;

-- =====================================================================================
-- SECTION 7: REAL-WORLD WORKFLOW EXAMPLES
-- =====================================================================================

-- Example 7.1: Daily scoring workflow
-- Complete workflow for daily batch processing
DO $$
DECLARE
    processed_count INTEGER;
BEGIN
    -- Step 1: Refresh materialized views
    PERFORM refresh_scoring_materialized_views();
    RAISE NOTICE 'Materialized views refreshed';

    -- Step 2: Update job enrichment scores
    processed_count := daily_scoring_update(1000, 50000);
    RAISE NOTICE 'Updated scores for % jobs', processed_count;

    -- Step 3: Analyze score distribution
    RAISE NOTICE 'Current scoring statistics:';
    FOR rec IN SELECT * FROM get_scoring_performance_stats() LOOP
        RAISE NOTICE '  %: % %', rec.metric_name, rec.metric_value, rec.metric_unit;
    END LOOP;
END
$$;

-- Example 7.2: User-specific job recommendations
-- Generate personalized job recommendations for a user
WITH user_recommendations AS (
    SELECT
        j.job_id,
        j.application_name,
        j.company_name,
        j.pref_cd,
        j.min_salary,
        j.max_salary,
        j.fee,
        calculate_composite_score(j.job_id, 1001) as score,
        calculate_distance_km(
            j.latitude, j.longitude,
            (SELECT cm.latitude FROM users u JOIN city_master cm ON u.city_cd = cm.code WHERE u.user_id = 1001),
            (SELECT cm.longitude FROM users u JOIN city_master cm ON u.city_cd = cm.code WHERE u.user_id = 1001)
        ) as distance_km
    FROM active_jobs j
    WHERE j.fee > 500  -- Business rule
        AND NOT EXISTS (
            -- Exclude companies user applied to recently
            SELECT 1 FROM user_actions ua
            WHERE ua.user_id = 1001
                AND ua.endcl_cd = j.endcl_cd
                AND ua.action_type = 'application'
                AND ua.action_timestamp > CURRENT_DATE - INTERVAL '14 days'
        )
    ORDER BY score DESC
    LIMIT 100
)
SELECT
    job_id,
    application_name,
    company_name,
    pref_cd,
    CONCAT(min_salary, '-', max_salary, '円') as salary_range,
    fee || '円' as application_fee,
    ROUND(score, 1) as score,
    COALESCE(ROUND(distance_km, 1)::TEXT || 'km', 'Distance unknown') as distance,
    -- Rank within results
    ROW_NUMBER() OVER (ORDER BY score DESC) as recommendation_rank
FROM user_recommendations
WHERE score >= 40  -- Minimum quality threshold
ORDER BY score DESC
LIMIT 20;

-- Example 7.3: A/B testing framework for scoring algorithms
-- Compare performance of different scoring approaches
WITH scoring_variants AS (
    SELECT
        j.job_id,
        j.application_name,
        -- Variant A: Default weights
        calculate_composite_score(j.job_id, 1001, 0.30, 0.20, 0.50) as variant_a_score,
        -- Variant B: Basic-heavy
        calculate_composite_score(j.job_id, 1001, 0.50, 0.20, 0.30) as variant_b_score,
        -- Variant C: Personal-heavy
        calculate_composite_score(j.job_id, 1001, 0.20, 0.15, 0.65) as variant_c_score
    FROM active_jobs j
    WHERE j.fee > 500
    LIMIT 1000
),
variant_rankings AS (
    SELECT
        job_id,
        application_name,
        variant_a_score,
        variant_b_score,
        variant_c_score,
        ROW_NUMBER() OVER (ORDER BY variant_a_score DESC) as rank_a,
        ROW_NUMBER() OVER (ORDER BY variant_b_score DESC) as rank_b,
        ROW_NUMBER() OVER (ORDER BY variant_c_score DESC) as rank_c
    FROM scoring_variants
)
SELECT
    'Variant A (Default)' as variant,
    COUNT(*) FILTER (WHERE rank_a <= 10) as top_10_jobs,
    AVG(variant_a_score) as avg_score,
    STDDEV(variant_a_score) as score_stddev
FROM variant_rankings
UNION ALL
SELECT
    'Variant B (Basic-heavy)',
    COUNT(*) FILTER (WHERE rank_b <= 10),
    AVG(variant_b_score),
    STDDEV(variant_b_score)
FROM variant_rankings
UNION ALL
SELECT
    'Variant C (Personal-heavy)',
    COUNT(*) FILTER (WHERE rank_c <= 10),
    AVG(variant_c_score),
    STDDEV(variant_c_score)
FROM variant_rankings;

-- =====================================================================================
-- SECTION 8: DEBUGGING AND TROUBLESHOOTING EXAMPLES
-- =====================================================================================

-- Example 8.1: Debug scoring issues for specific jobs
-- Detailed breakdown of scoring components for troubleshooting
SELECT
    j.job_id,
    j.application_name,
    j.company_name,
    j.fee,
    j.min_salary,
    j.max_salary,
    j.endcl_cd,
    -- Component scores with explanations
    calculate_basic_score(j.job_id) as basic_score,
    normalize_fee_score(j.fee) as fee_component,
    normalize_hourly_wage_score((j.min_salary + j.max_salary)/2, j.pref_cd) as wage_component,
    calculate_company_popularity_score(j.endcl_cd) as popularity_component,
    calculate_seo_score(j.job_id) as seo_score,
    -- Error conditions
    CASE
        WHEN j.fee <= 500 THEN 'Fee too low (≤500)'
        WHEN j.min_salary IS NULL THEN 'Missing salary data'
        WHEN j.endcl_cd IS NULL THEN 'Missing company code'
        ELSE 'OK'
    END as potential_issues
FROM jobs j
WHERE j.job_id IN (
    -- Replace with problematic job IDs
    SELECT job_id FROM jobs WHERE is_active = TRUE LIMIT 10
);

-- Example 8.2: Identify scoring anomalies
-- Find jobs with unusual scoring patterns
SELECT
    j.job_id,
    j.application_name,
    j.fee,
    je.basic_score,
    je.seo_score,
    je.composite_score,
    -- Flag unusual patterns
    CASE
        WHEN je.basic_score > 90 AND j.fee <= 1000 THEN 'High basic score with low fee'
        WHEN je.seo_score = 0 AND LENGTH(j.application_name) > 50 THEN 'Zero SEO score with long title'
        WHEN je.basic_score < 10 AND j.fee > 2000 THEN 'Low basic score with high fee'
        WHEN ABS(je.basic_score - je.seo_score) > 50 THEN 'Large basic-SEO score gap'
        ELSE 'Normal'
    END as anomaly_type
FROM jobs j
JOIN job_enrichment je ON j.job_id = je.job_id
WHERE j.is_active = TRUE
    AND (je.basic_score > 90 AND j.fee <= 1000
         OR je.seo_score = 0 AND LENGTH(j.application_name) > 50
         OR je.basic_score < 10 AND j.fee > 2000
         OR ABS(je.basic_score - je.seo_score) > 50)
ORDER BY je.calculated_at DESC
LIMIT 20;

-- =====================================================================================
-- END OF EXAMPLES
-- =====================================================================================

-- Note: These examples demonstrate real-world usage patterns for the scoring system.
-- Adjust job IDs, user IDs, and parameters according to your actual data.
-- Performance may vary based on data volume and hardware specifications.