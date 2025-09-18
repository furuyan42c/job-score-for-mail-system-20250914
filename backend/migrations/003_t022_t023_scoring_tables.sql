-- T022 & T023: SEO and Personalized Scoring Tables
-- Creation Date: 2025-09-18
-- Purpose: Complete scoring infrastructure per v5.0 specification

-- ============================================
-- 1. KEYWORD SCORING TABLE (T022 REQUIREMENT)
-- ============================================
CREATE TABLE IF NOT EXISTS keyword_scoring (
    id SERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL,
    keyword_id INTEGER NOT NULL,
    processed_keyword VARCHAR(255) NOT NULL,
    matched_field VARCHAR(50) NOT NULL,
    base_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    field_weight DECIMAL(3,2) NOT NULL DEFAULT 1.0,
    match_position INTEGER,
    volume INTEGER,
    intent VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Composite primary key for uniqueness
    CONSTRAINT uq_keyword_scoring UNIQUE(job_id, keyword_id, matched_field)
);

-- High-performance indexes for keyword scoring
CREATE INDEX idx_keyword_scoring_job ON keyword_scoring(job_id);
CREATE INDEX idx_keyword_scoring_keyword ON keyword_scoring(keyword_id);
CREATE INDEX idx_keyword_scoring_field ON keyword_scoring(matched_field);
CREATE INDEX idx_keyword_scoring_score ON keyword_scoring(base_score DESC);
CREATE INDEX idx_keyword_scoring_created ON keyword_scoring(created_at DESC);

-- ============================================
-- 2. ADJACENT CITIES TABLE (LOCATION EXPANSION)
-- ============================================
CREATE TABLE IF NOT EXISTS adjacent_cities (
    id SERIAL PRIMARY KEY,
    city_code VARCHAR(10) NOT NULL,
    adjacent_city_code VARCHAR(10) NOT NULL,
    distance_km DECIMAL(5,2),
    travel_time_minutes INTEGER,
    transportation_type VARCHAR(20), -- 'train', 'bus', 'walking'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_adjacent_cities UNIQUE(city_code, adjacent_city_code)
);

-- Indexes for adjacency lookups
CREATE INDEX idx_adjacent_cities_city ON adjacent_cities(city_code);
CREATE INDEX idx_adjacent_cities_adjacent ON adjacent_cities(adjacent_city_code);
CREATE INDEX idx_adjacent_cities_distance ON adjacent_cities(distance_km);

-- ============================================
-- 3. USER BEHAVIOR AGGREGATES (T023 REQUIREMENT)
-- ============================================
CREATE TABLE IF NOT EXISTS user_behavior_aggregates (
    user_id INTEGER PRIMARY KEY,
    -- Application behavior (過去360日)
    total_applications INTEGER DEFAULT 0,
    application_categories TEXT, -- "code:count,code:count" format
    avg_salary_applied DECIMAL(10,2),

    -- Click behavior (過去360日)
    total_clicks INTEGER DEFAULT 0,
    click_categories TEXT, -- "code:count,code:count" format
    click_patterns JSONB DEFAULT '{}',

    -- Location preferences
    preferred_prefectures TEXT, -- "code:count,code:count" format
    preferred_cities TEXT, -- "code:count,code:count" format

    -- Temporal patterns
    preferred_time_slots TEXT, -- "hour:count,hour:count" format
    preferred_days_of_week TEXT, -- "day:count,day:count" format

    -- ALS model factors (50次元)
    latent_factors FLOAT[] DEFAULT ARRAY[]::FLOAT[],

    -- Metadata
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_version VARCHAR(10) DEFAULT 'v1.0',

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for behavior lookups
CREATE INDEX idx_user_behavior_aggregates_updated ON user_behavior_aggregates(last_calculated DESC);
CREATE INDEX idx_user_behavior_aggregates_applications ON user_behavior_aggregates(total_applications DESC);

-- ============================================
-- 4. ALS MODEL METADATA (T023 REQUIREMENT)
-- ============================================
CREATE TABLE IF NOT EXISTS als_model_metadata (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(20) NOT NULL,
    factors INTEGER DEFAULT 50,
    regularization DECIMAL(5,4) DEFAULT 0.01,
    iterations INTEGER DEFAULT 15,
    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    training_duration_seconds INTEGER,
    num_users INTEGER,
    num_items INTEGER,
    num_interactions INTEGER,
    rmse DECIMAL(5,4),
    map_at_k DECIMAL(5,4),
    model_path VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE,
    notes TEXT,

    CONSTRAINT uq_als_model_version UNIQUE(model_version)
);

-- Index for active model lookup
CREATE INDEX idx_als_model_active ON als_model_metadata(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_als_model_date ON als_model_metadata(training_date DESC);

-- ============================================
-- 5. COMPANY POPULARITY 360D (T021 ENHANCEMENT)
-- ============================================
CREATE TABLE IF NOT EXISTS company_popularity_360d (
    endcl_cd VARCHAR(50) PRIMARY KEY,

    -- 360-day metrics
    views_360d INTEGER DEFAULT 0,
    unique_viewers_360d INTEGER DEFAULT 0,
    applications_360d INTEGER DEFAULT 0,
    unique_applicants_360d INTEGER DEFAULT 0,
    application_rate_360d DECIMAL(5,4) DEFAULT 0, -- applications/views

    -- 30-day metrics (for trend analysis)
    views_30d INTEGER DEFAULT 0,
    applications_30d INTEGER DEFAULT 0,
    application_rate_30d DECIMAL(5,4) DEFAULT 0,

    -- 7-day metrics (for recency)
    views_7d INTEGER DEFAULT 0,
    applications_7d INTEGER DEFAULT 0,

    -- Weighted popularity score (0-100)
    popularity_score DECIMAL(5,2) DEFAULT 0,
    popularity_rank INTEGER,
    popularity_percentile DECIMAL(5,2),

    -- Category-specific popularity
    category_popularity JSONB DEFAULT '{}', -- {"category_code": score}

    -- Metadata
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_version VARCHAR(10) DEFAULT 'v1.0'
);

-- Indexes for popularity lookups
CREATE INDEX idx_company_popularity_360d_score ON company_popularity_360d(popularity_score DESC);
CREATE INDEX idx_company_popularity_360d_rank ON company_popularity_360d(popularity_rank);
CREATE INDEX idx_company_popularity_360d_updated ON company_popularity_360d(last_calculated DESC);

-- ============================================
-- 6. SCORING PERFORMANCE METRICS
-- ============================================
CREATE TABLE IF NOT EXISTS scoring_performance_metrics (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    scoring_type VARCHAR(20) NOT NULL, -- 'basic', 'seo', 'personalized', 'composite'
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    avg_score DECIMAL(5,2),
    min_score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    percentile_25 DECIMAL(5,2),
    percentile_50 DECIMAL(5,2),
    percentile_75 DECIMAL(5,2),
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    error_messages TEXT,

    CONSTRAINT uq_scoring_metrics UNIQUE(batch_id, scoring_type)
);

-- Indexes for performance monitoring
CREATE INDEX idx_scoring_performance_batch ON scoring_performance_metrics(batch_id);
CREATE INDEX idx_scoring_performance_type ON scoring_performance_metrics(scoring_type);
CREATE INDEX idx_scoring_performance_time ON scoring_performance_metrics(start_time DESC);

-- ============================================
-- 7. CRITICAL PERFORMANCE INDEXES
-- ============================================

-- Composite index for job filtering (T021 requirement)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_scoring_composite
ON jobs(employment_type_cd, fee, pref_cd, posting_date DESC)
WHERE fee > 500 AND employment_type_cd IN (1, 3, 6, 8);

-- User actions index for behavior analysis (T023 requirement)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_actions_behavior
ON user_actions(user_id, action_type, action_timestamp DESC)
WHERE action_timestamp > CURRENT_DATE - INTERVAL '360 days';

-- Job enrichment scoring index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_enrichment_scores
ON job_enrichment(job_id, basic_score DESC, seo_score DESC, personalized_score DESC)
WHERE created_date = CURRENT_DATE;

-- ============================================
-- 8. HELPER FUNCTIONS
-- ============================================

-- Function to parse frequency strings ("code:count,code:count")
CREATE OR REPLACE FUNCTION parse_frequency_string(freq_string TEXT)
RETURNS TABLE(code VARCHAR, count INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT
        split_part(item, ':', 1) AS code,
        split_part(item, ':', 2)::INTEGER AS count
    FROM
        unnest(string_to_array(freq_string, ',')) AS item
    WHERE
        item LIKE '%:%';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to update company popularity 360d
CREATE OR REPLACE FUNCTION update_company_popularity_360d(target_endcl_cd VARCHAR DEFAULT NULL)
RETURNS void AS $$
BEGIN
    INSERT INTO company_popularity_360d (
        endcl_cd,
        views_360d, unique_viewers_360d,
        applications_360d, unique_applicants_360d,
        application_rate_360d,
        views_30d, applications_30d, application_rate_30d,
        views_7d, applications_7d,
        popularity_score,
        last_calculated
    )
    SELECT
        ua.endcl_cd,
        COUNT(CASE WHEN ua.action_type = 'view' THEN 1 END) as views_360d,
        COUNT(DISTINCT CASE WHEN ua.action_type = 'view' THEN ua.user_id END) as unique_viewers_360d,
        COUNT(CASE WHEN ua.action_type IN ('apply', 'application') THEN 1 END) as applications_360d,
        COUNT(DISTINCT CASE WHEN ua.action_type IN ('apply', 'application') THEN ua.user_id END) as unique_applicants_360d,
        CASE
            WHEN COUNT(CASE WHEN ua.action_type = 'view' THEN 1 END) > 0 THEN
                COUNT(CASE WHEN ua.action_type IN ('apply', 'application') THEN 1 END)::DECIMAL /
                COUNT(CASE WHEN ua.action_type = 'view' THEN 1 END)
            ELSE 0
        END as application_rate_360d,
        COUNT(CASE WHEN ua.action_type = 'view' AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as views_30d,
        COUNT(CASE WHEN ua.action_type IN ('apply', 'application') AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as applications_30d,
        CASE
            WHEN COUNT(CASE WHEN ua.action_type = 'view' AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days' THEN 1 END) > 0 THEN
                COUNT(CASE WHEN ua.action_type IN ('apply', 'application') AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days' THEN 1 END)::DECIMAL /
                COUNT(CASE WHEN ua.action_type = 'view' AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days' THEN 1 END)
            ELSE 0
        END as application_rate_30d,
        COUNT(CASE WHEN ua.action_type = 'view' AND ua.action_timestamp > CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as views_7d,
        COUNT(CASE WHEN ua.action_type IN ('apply', 'application') AND ua.action_timestamp > CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as applications_7d,
        -- Popularity score calculation (weighted formula)
        LEAST(100, (
            -- 360-day application rate (40% weight)
            CASE
                WHEN COUNT(CASE WHEN ua.action_type = 'view' THEN 1 END) > 0 THEN
                    (COUNT(CASE WHEN ua.action_type IN ('apply', 'application') THEN 1 END)::DECIMAL /
                     COUNT(CASE WHEN ua.action_type = 'view' THEN 1 END)) * 100 * 0.4
                ELSE 0
            END +
            -- 30-day recency (30% weight)
            LEAST(30, COUNT(CASE WHEN ua.action_type IN ('apply', 'application') AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days' THEN 1 END) * 0.5) +
            -- 7-day hot trend (30% weight)
            LEAST(30, COUNT(CASE WHEN ua.action_type IN ('apply', 'application') AND ua.action_timestamp > CURRENT_DATE - INTERVAL '7 days' THEN 1 END) * 2)
        )) as popularity_score,
        CURRENT_TIMESTAMP as last_calculated
    FROM user_actions ua
    WHERE ua.action_timestamp > CURRENT_DATE - INTERVAL '360 days'
    AND ua.endcl_cd IS NOT NULL
    AND (target_endcl_cd IS NULL OR ua.endcl_cd = target_endcl_cd)
    GROUP BY ua.endcl_cd
    ON CONFLICT (endcl_cd)
    DO UPDATE SET
        views_360d = EXCLUDED.views_360d,
        unique_viewers_360d = EXCLUDED.unique_viewers_360d,
        applications_360d = EXCLUDED.applications_360d,
        unique_applicants_360d = EXCLUDED.unique_applicants_360d,
        application_rate_360d = EXCLUDED.application_rate_360d,
        views_30d = EXCLUDED.views_30d,
        applications_30d = EXCLUDED.applications_30d,
        application_rate_30d = EXCLUDED.application_rate_30d,
        views_7d = EXCLUDED.views_7d,
        applications_7d = EXCLUDED.applications_7d,
        popularity_score = EXCLUDED.popularity_score,
        last_calculated = EXCLUDED.last_calculated;

    -- Update popularity rankings
    WITH ranked AS (
        SELECT
            endcl_cd,
            ROW_NUMBER() OVER (ORDER BY popularity_score DESC) as rank,
            PERCENT_RANK() OVER (ORDER BY popularity_score) * 100 as percentile
        FROM company_popularity_360d
    )
    UPDATE company_popularity_360d cp
    SET
        popularity_rank = r.rank,
        popularity_percentile = r.percentile
    FROM ranked r
    WHERE cp.endcl_cd = r.endcl_cd;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 9. INITIAL DATA POPULATION (OPTIONAL)
-- ============================================

-- Populate adjacent cities (example for Tokyo area)
INSERT INTO adjacent_cities (city_code, adjacent_city_code, distance_km, travel_time_minutes, transportation_type)
VALUES
    ('13101', '13102', 2.5, 10, 'train'),  -- 千代田区 → 中央区
    ('13101', '13103', 3.0, 12, 'train'),  -- 千代田区 → 港区
    ('13101', '13104', 2.8, 11, 'train'),  -- 千代田区 → 新宿区
    ('13104', '13105', 2.0, 8, 'train'),   -- 新宿区 → 文京区
    ('13104', '13113', 3.5, 15, 'train')   -- 新宿区 → 渋谷区
ON CONFLICT (city_code, adjacent_city_code) DO NOTHING;

-- ============================================
-- 10. MAINTENANCE SCRIPTS
-- ============================================

-- Daily maintenance procedure
CREATE OR REPLACE FUNCTION daily_scoring_maintenance()
RETURNS void AS $$
BEGIN
    -- Update company popularity
    PERFORM update_company_popularity_360d();

    -- Clean old scoring performance metrics (keep 30 days)
    DELETE FROM scoring_performance_metrics
    WHERE start_time < CURRENT_DATE - INTERVAL '30 days';

    -- Clean old keyword scoring (keep 7 days)
    DELETE FROM keyword_scoring
    WHERE created_at < CURRENT_DATE - INTERVAL '7 days';

    -- Vacuum analyze for performance
    ANALYZE keyword_scoring;
    ANALYZE company_popularity_360d;
    ANALYZE user_behavior_aggregates;
END;
$$ LANGUAGE plpgsql;

-- Schedule: Run daily at 02:00 AM JST
-- 0 2 * * * psql -d your_database -c "SELECT daily_scoring_maintenance();"