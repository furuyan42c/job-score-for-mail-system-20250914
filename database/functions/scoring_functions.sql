-- =====================================================================================
-- Job Matching System - PostgreSQL Scoring Functions
-- =====================================================================================
-- Version: 1.0
-- Database: PostgreSQL 15+ (Supabase compatible)
-- Created: 2025-09-18
--
-- This file contains comprehensive scoring functions for the 3-stage scoring system:
-- 1. Basic Score Calculation (fee, hourly wage normalization, company popularity)
-- 2. SEO Score Calculation (keyword matching with semrush_keywords)
-- 3. Personalized Score Calculation (user preferences, collaborative filtering)
-- 4. Composite Score Calculation (weighted combination)
-- 5. Helper Functions (distance calculation, area stats, keyword extraction)
--
-- Performance optimized for 100,000 jobs × 10,000 users processing
-- =====================================================================================

-- =====================================================================================
-- SECTION 1: HELPER FUNCTIONS
-- =====================================================================================

-- 1.1 Calculate distance between two coordinates (Haversine formula)
-- Returns distance in kilometers
CREATE OR REPLACE FUNCTION calculate_distance_km(
    lat1 DECIMAL(10,8),
    lon1 DECIMAL(11,8),
    lat2 DECIMAL(10,8),
    lon2 DECIMAL(11,8)
) RETURNS DECIMAL(8,2) AS $$
DECLARE
    earth_radius CONSTANT DECIMAL := 6371; -- Earth radius in km
    lat1_rad DECIMAL;
    lat2_rad DECIMAL;
    delta_lat DECIMAL;
    delta_lon DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    -- Handle NULL coordinates
    IF lat1 IS NULL OR lon1 IS NULL OR lat2 IS NULL OR lon2 IS NULL THEN
        RETURN NULL;
    END IF;

    -- Convert degrees to radians
    lat1_rad := RADIANS(lat1);
    lat2_rad := RADIANS(lat2);
    delta_lat := RADIANS(lat2 - lat1);
    delta_lon := RADIANS(lon2 - lon1);

    -- Haversine formula
    a := SIN(delta_lat/2) * SIN(delta_lat/2) +
         COS(lat1_rad) * COS(lat2_rad) *
         SIN(delta_lon/2) * SIN(delta_lon/2);
    c := 2 * ATAN2(SQRT(a), SQRT(1-a));

    RETURN ROUND((earth_radius * c)::DECIMAL, 2);
EXCEPTION
    WHEN OTHERS THEN
        -- Return large distance on calculation error
        RETURN 999.99;
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- 1.2 Calculate area salary statistics for normalization
-- Returns statistics for a given area (prefecture or city level)
CREATE OR REPLACE FUNCTION calculate_area_salary_stats(
    p_pref_cd CHAR(2) DEFAULT NULL,
    p_city_cd VARCHAR(5) DEFAULT NULL,
    p_granularity VARCHAR(20) DEFAULT 'prefecture' -- 'prefecture' or 'city'
) RETURNS TABLE (
    avg_salary INTEGER,
    std_salary DECIMAL(10,2),
    min_salary INTEGER,
    max_salary Integer,
    sample_count INTEGER
) AS $$
BEGIN
    -- Calculate salary statistics based on granularity
    IF p_granularity = 'city' AND p_city_cd IS NOT NULL THEN
        -- City-level statistics
        RETURN QUERY
        SELECT
            COALESCE(AVG((j.min_salary + j.max_salary) / 2)::INTEGER, 1200) as avg_salary,
            COALESCE(STDDEV((j.min_salary + j.max_salary) / 2), 200.0) as std_salary,
            COALESCE(MIN(j.min_salary), 800) as min_salary,
            COALESCE(MAX(j.max_salary), 2000) as max_salary,
            COUNT(*)::INTEGER as sample_count
        FROM active_jobs j
        WHERE j.city_cd = p_city_cd
            AND j.min_salary IS NOT NULL
            AND j.max_salary IS NOT NULL
            AND j.min_salary > 0;
    ELSE
        -- Prefecture-level statistics (default)
        RETURN QUERY
        SELECT
            COALESCE(AVG((j.min_salary + j.max_salary) / 2)::INTEGER, 1200) as avg_salary,
            COALESCE(STDDEV((j.min_salary + j.max_salary) / 2), 200.0) as std_salary,
            COALESCE(MIN(j.min_salary), 800) as min_salary,
            COALESCE(MAX(j.max_salary), 2000) as max_salary,
            COUNT(*)::INTEGER as sample_count
        FROM active_jobs j
        WHERE j.pref_cd = COALESCE(p_pref_cd, '13') -- Default to Tokyo
            AND j.min_salary IS NOT NULL
            AND j.max_salary IS NOT NULL
            AND j.min_salary > 0;
    END IF;

    -- If no data found, return default values
    IF NOT FOUND THEN
        RETURN QUERY SELECT 1200, 200.0, 800, 2000, 0;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 1.3 Extract keywords from job text content
-- Returns array of extracted keywords for SEO matching
CREATE OR REPLACE FUNCTION extract_job_keywords(
    p_application_name TEXT,
    p_description TEXT DEFAULT NULL,
    p_benefits TEXT DEFAULT NULL
) RETURNS TEXT[] AS $$
DECLARE
    combined_text TEXT;
    keywords TEXT[] := '{}';
    word_parts TEXT[];
    i INTEGER;
BEGIN
    -- Combine all text fields
    combined_text := COALESCE(p_application_name, '') || ' ' ||
                    COALESCE(p_description, '') || ' ' ||
                    COALESCE(p_benefits, '');

    -- Remove HTML tags and normalize text
    combined_text := REGEXP_REPLACE(combined_text, '<[^>]*>', '', 'g');
    combined_text := LOWER(TRIM(combined_text));

    -- Split into words and filter meaningful keywords
    word_parts := STRING_TO_ARRAY(combined_text, ' ');

    FOR i IN 1..ARRAY_LENGTH(word_parts, 1) LOOP
        -- Only include words longer than 2 characters
        IF LENGTH(word_parts[i]) > 2 THEN
            keywords := ARRAY_APPEND(keywords, word_parts[i]);
        END IF;
    END LOOP;

    -- Remove duplicates and return first 20 keywords
    SELECT ARRAY_AGG(DISTINCT keyword ORDER BY keyword)
    INTO keywords
    FROM UNNEST(keywords) as keyword
    LIMIT 20;

    RETURN COALESCE(keywords, '{}');
EXCEPTION
    WHEN OTHERS THEN
        RETURN '{}';
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- =====================================================================================
-- SECTION 2: BASIC SCORE CALCULATION FUNCTIONS
-- =====================================================================================

-- 2.1 Normalize hourly wage based on area statistics
-- Returns score 0-100 based on Z-score normalization
CREATE OR REPLACE FUNCTION normalize_hourly_wage_score(
    p_wage INTEGER,
    p_pref_cd CHAR(2) DEFAULT '13',
    p_city_cd VARCHAR(5) DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    area_stats RECORD;
    z_score DECIMAL(10,4);
    normalized_score DECIMAL(5,2);
BEGIN
    -- Handle null or invalid wage
    IF p_wage IS NULL OR p_wage <= 0 THEN
        RETURN 0;
    END IF;

    -- Get area salary statistics
    SELECT * INTO area_stats
    FROM calculate_area_salary_stats(p_pref_cd, p_city_cd,
        CASE WHEN p_city_cd IS NOT NULL THEN 'city' ELSE 'prefecture' END);

    -- Calculate Z-score: (wage - mean) / std_dev
    IF area_stats.std_salary > 0 THEN
        z_score := (p_wage - area_stats.avg_salary)::DECIMAL / area_stats.std_salary;
    ELSE
        z_score := 0;
    END IF;

    -- Normalize to 0-100 scale: (z_score + 2) * 25
    -- This maps -2σ to 0, mean to 50, +2σ to 100
    normalized_score := (z_score + 2) * 25;

    -- Clamp to valid range
    RETURN GREATEST(0, LEAST(100, normalized_score));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 25; -- Return below-average score on error
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 2.2 Normalize fee score (application incentive)
-- Returns score 0-100 based on fee amount (500-5000 yen range)
CREATE OR REPLACE FUNCTION normalize_fee_score(
    p_fee INTEGER
) RETURNS DECIMAL(5,2) AS $$
BEGIN
    -- Handle null or invalid fee
    IF p_fee IS NULL THEN
        RETURN 0;
    END IF;

    -- Fees <= 500 yen get 0 points (business rule)
    IF p_fee <= 500 THEN
        RETURN 0;
    END IF;

    -- Fees >= 5000 yen get 100 points
    IF p_fee >= 5000 THEN
        RETURN 100;
    END IF;

    -- Linear mapping for 500-5000 yen range
    RETURN ((p_fee - 500)::DECIMAL / (5000 - 500)) * 100;
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- 2.3 Calculate company popularity score
-- Returns score 0-100 based on 360-day application rate
CREATE OR REPLACE FUNCTION calculate_company_popularity_score(
    p_endcl_cd VARCHAR(20)
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    company_stats RECORD;
    percentile_rank DECIMAL(5,4);
BEGIN
    -- Get company popularity data
    SELECT
        cp.total_applications_360d,
        cp.application_rate,
        cp.popularity_score,
        cp.overall_rank
    INTO company_stats
    FROM company_popularity cp
    WHERE cp.endcl_cd = p_endcl_cd;

    -- If company not found, return default low score
    IF NOT FOUND THEN
        RETURN 20;
    END IF;

    -- Use pre-calculated popularity score if available
    IF company_stats.popularity_score IS NOT NULL THEN
        RETURN company_stats.popularity_score;
    END IF;

    -- Calculate percentile rank of application rate
    SELECT
        PERCENT_RANK() OVER (ORDER BY application_rate) * 100
    INTO percentile_rank
    FROM company_popularity cp2
    WHERE cp2.endcl_cd = p_endcl_cd;

    RETURN COALESCE(percentile_rank, 20);
EXCEPTION
    WHEN OTHERS THEN
        RETURN 20;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 2.4 Calculate access convenience score
-- Returns score 0-100 based on distance from user location and public transportation
CREATE OR REPLACE FUNCTION calculate_access_convenience_score(
    p_job_lat DECIMAL(10,8),
    p_job_lon DECIMAL(11,8),
    p_user_lat DECIMAL(10,8),
    p_user_lon DECIMAL(11,8),
    p_station_name VARCHAR(100) DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    distance_km DECIMAL(8,2);
    access_score DECIMAL(5,2) := 0;
BEGIN
    -- Calculate distance if coordinates are available
    IF p_job_lat IS NOT NULL AND p_job_lon IS NOT NULL AND
       p_user_lat IS NOT NULL AND p_user_lon IS NOT NULL THEN

        distance_km := calculate_distance_km(p_job_lat, p_job_lon, p_user_lat, p_user_lon);

        -- Distance-based scoring (closer = higher score)
        CASE
            WHEN distance_km <= 1 THEN access_score := 100;
            WHEN distance_km <= 2 THEN access_score := 90;
            WHEN distance_km <= 5 THEN access_score := 70;
            WHEN distance_km <= 10 THEN access_score := 50;
            WHEN distance_km <= 20 THEN access_score := 30;
            WHEN distance_km <= 50 THEN access_score := 10;
            ELSE access_score := 0;
        END CASE;
    ELSE
        -- Default moderate score if no coordinates
        access_score := 50;
    END IF;

    -- Bonus for stations (indicates good public transportation)
    IF p_station_name IS NOT NULL AND LENGTH(TRIM(p_station_name)) > 0 THEN
        access_score := access_score + 10;
    END IF;

    -- Clamp to valid range
    RETURN GREATEST(0, LEAST(100, access_score));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 50;
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- 2.5 Main basic score calculation function
-- Combines fee (30%), hourly wage (40%), and company popularity (30%)
CREATE OR REPLACE FUNCTION calculate_basic_score(
    p_job_id BIGINT,
    p_min_salary INTEGER DEFAULT NULL,
    p_max_salary INTEGER DEFAULT NULL,
    p_fee INTEGER DEFAULT NULL,
    p_endcl_cd VARCHAR(20) DEFAULT NULL,
    p_pref_cd CHAR(2) DEFAULT NULL,
    p_city_cd VARCHAR(5) DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    job_data RECORD;
    avg_wage INTEGER;
    hourly_wage_score DECIMAL(5,2);
    fee_score DECIMAL(5,2);
    popularity_score DECIMAL(5,2);
    basic_score DECIMAL(5,2);
BEGIN
    -- Get job data if not provided as parameters
    IF p_min_salary IS NULL OR p_max_salary IS NULL OR p_fee IS NULL OR p_endcl_cd IS NULL THEN
        SELECT
            j.min_salary, j.max_salary, j.fee, j.endcl_cd, j.pref_cd, j.city_cd
        INTO job_data
        FROM jobs j
        WHERE j.job_id = p_job_id;

        -- Use job data if parameters not provided
        p_min_salary := COALESCE(p_min_salary, job_data.min_salary);
        p_max_salary := COALESCE(p_max_salary, job_data.max_salary);
        p_fee := COALESCE(p_fee, job_data.fee);
        p_endcl_cd := COALESCE(p_endcl_cd, job_data.endcl_cd);
        p_pref_cd := COALESCE(p_pref_cd, job_data.pref_cd);
        p_city_cd := COALESCE(p_city_cd, job_data.city_cd);
    END IF;

    -- Business rule: jobs with fee <= 500 get score 0
    IF p_fee IS NOT NULL AND p_fee <= 500 THEN
        RETURN 0;
    END IF;

    -- Calculate average wage
    avg_wage := CASE
        WHEN p_min_salary IS NOT NULL AND p_max_salary IS NOT NULL
        THEN (p_min_salary + p_max_salary) / 2
        WHEN p_min_salary IS NOT NULL
        THEN p_min_salary
        WHEN p_max_salary IS NOT NULL
        THEN p_max_salary
        ELSE 1200 -- Default minimum wage
    END;

    -- Calculate component scores
    hourly_wage_score := normalize_hourly_wage_score(avg_wage, p_pref_cd, p_city_cd);
    fee_score := normalize_fee_score(p_fee);
    popularity_score := calculate_company_popularity_score(p_endcl_cd);

    -- Weighted combination: hourly_wage(40%) + fee(30%) + popularity(30%)
    basic_score := (hourly_wage_score * 0.40) + (fee_score * 0.30) + (popularity_score * 0.30);

    -- Clamp to valid range
    RETURN GREATEST(0, LEAST(100, basic_score));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- =====================================================================================
-- SECTION 3: SEO SCORE CALCULATION FUNCTIONS
-- =====================================================================================

-- 3.1 Calculate keyword match score for a single keyword
-- Returns weighted score based on search volume, intent, and field importance
CREATE OR REPLACE FUNCTION calculate_keyword_match_score(
    p_keyword VARCHAR(200),
    p_search_volume INTEGER,
    p_intent VARCHAR(50),
    p_match_field VARCHAR(100),
    p_match_count INTEGER DEFAULT 1
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    base_score DECIMAL(5,2) := 0;
    field_multiplier DECIMAL(3,2) := 1.0;
    intent_multiplier DECIMAL(3,2) := 1.0;
    frequency_bonus DECIMAL(5,2) := 0;
BEGIN
    -- Base score based on search volume
    CASE
        WHEN p_search_volume >= 10000 THEN base_score := 15;
        WHEN p_search_volume >= 5000 THEN base_score := 12;
        WHEN p_search_volume >= 1000 THEN base_score := 10;
        WHEN p_search_volume >= 500 THEN base_score := 8;
        WHEN p_search_volume >= 100 THEN base_score := 5;
        ELSE base_score := 3;
    END CASE;

    -- Field importance multiplier
    CASE p_match_field
        WHEN 'application_name' THEN field_multiplier := 2.0;  -- Title is most important
        WHEN 'description' THEN field_multiplier := 1.5;       -- Description is important
        WHEN 'benefits' THEN field_multiplier := 1.2;          -- Benefits are moderately important
        WHEN 'company_name' THEN field_multiplier := 1.1;      -- Company name is less important
        ELSE field_multiplier := 1.0;
    END CASE;

    -- Intent importance multiplier
    CASE LOWER(COALESCE(p_intent, 'informational'))
        WHEN 'transactional' THEN intent_multiplier := 1.5;    -- High intent to act
        WHEN 'commercial' THEN intent_multiplier := 1.3;       -- Commercial intent
        WHEN 'navigational' THEN intent_multiplier := 1.1;     -- Looking for specific thing
        ELSE intent_multiplier := 1.0;                         -- Informational
    END CASE;

    -- Frequency bonus (multiple mentions increase relevance)
    frequency_bonus := LEAST(5, (p_match_count - 1) * 1.5);

    -- Calculate final score
    RETURN ROUND(
        (base_score * field_multiplier * intent_multiplier) + frequency_bonus,
        2
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- 3.2 Calculate SEO score for a job based on keyword matching
-- Matches job content against semrush_keywords table
CREATE OR REPLACE FUNCTION calculate_seo_score(
    p_job_id BIGINT,
    p_application_name TEXT DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_benefits TEXT DEFAULT NULL,
    p_company_name VARCHAR(255) DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    job_data RECORD;
    keyword_rec RECORD;
    total_score DECIMAL(10,2) := 0;
    max_possible_score DECIMAL(10,2) := 100;
    normalized_score DECIMAL(5,2);
    match_count INTEGER;
    field_texts JSONB;
BEGIN
    -- Get job data if not provided
    IF p_application_name IS NULL OR p_description IS NULL THEN
        SELECT
            j.application_name, j.description, j.benefits, j.company_name
        INTO job_data
        FROM jobs j
        WHERE j.job_id = p_job_id;

        p_application_name := COALESCE(p_application_name, job_data.application_name);
        p_description := COALESCE(p_description, job_data.description);
        p_benefits := COALESCE(p_benefits, job_data.benefits);
        p_company_name := COALESCE(p_company_name, job_data.company_name);
    END IF;

    -- Prepare field texts for searching (normalize and clean)
    field_texts := jsonb_build_object(
        'application_name', LOWER(COALESCE(p_application_name, '')),
        'description', LOWER(REGEXP_REPLACE(COALESCE(p_description, ''), '<[^>]*>', '', 'g')),
        'benefits', LOWER(REGEXP_REPLACE(COALESCE(p_benefits, ''), '<[^>]*>', '', 'g')),
        'company_name', LOWER(COALESCE(p_company_name, ''))
    );

    -- Check each SEO keyword against job content
    FOR keyword_rec IN
        SELECT
            sk.keyword,
            sk.search_volume,
            sk.category as intent,
            sk.keyword_difficulty
        FROM semrush_keywords sk
        WHERE sk.search_volume > 0
        ORDER BY sk.search_volume DESC
        LIMIT 1000  -- Limit to top keywords for performance
    LOOP
        -- Check each field for keyword matches
        FOR match_count IN
            SELECT (
                -- Count occurrences in each field
                CASE WHEN field_texts->>'application_name' LIKE '%' || keyword_rec.keyword || '%' THEN
                    calculate_keyword_match_score(keyword_rec.keyword, keyword_rec.search_volume, keyword_rec.intent, 'application_name', 1)
                ELSE 0 END +
                CASE WHEN field_texts->>'description' LIKE '%' || keyword_rec.keyword || '%' THEN
                    calculate_keyword_match_score(keyword_rec.keyword, keyword_rec.search_volume, keyword_rec.intent, 'description', 1)
                ELSE 0 END +
                CASE WHEN field_texts->>'benefits' LIKE '%' || keyword_rec.keyword || '%' THEN
                    calculate_keyword_match_score(keyword_rec.keyword, keyword_rec.search_volume, keyword_rec.intent, 'benefits', 1)
                ELSE 0 END +
                CASE WHEN field_texts->>'company_name' LIKE '%' || keyword_rec.keyword || '%' THEN
                    calculate_keyword_match_score(keyword_rec.keyword, keyword_rec.search_volume, keyword_rec.intent, 'company_name', 1)
                ELSE 0 END
            )::INTEGER
        LOOP
            total_score := total_score + match_count;
        END LOOP;
    END LOOP;

    -- Normalize score to 0-100 range
    -- Assume max possible is getting 50 high-value keyword matches
    max_possible_score := 50 * 15 * 2.0; -- 50 keywords * 15 points * 2.0 title multiplier
    normalized_score := LEAST(100, (total_score / max_possible_score) * 100);

    RETURN ROUND(normalized_score, 2);
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 3.3 Calculate keyword density score for job content
-- Analyzes keyword density and relevance in job text
CREATE OR REPLACE FUNCTION calculate_keyword_density_score(
    p_job_id BIGINT,
    p_target_keywords TEXT[] DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    job_data RECORD;
    combined_text TEXT;
    word_count INTEGER;
    keyword_count INTEGER := 0;
    density_score DECIMAL(5,2);
    keyword TEXT;
BEGIN
    -- Get job content
    SELECT
        j.application_name, j.description, j.benefits
    INTO job_data
    FROM jobs j
    WHERE j.job_id = p_job_id;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    -- Combine all text content
    combined_text := COALESCE(job_data.application_name, '') || ' ' ||
                    COALESCE(job_data.description, '') || ' ' ||
                    COALESCE(job_data.benefits, '');

    -- Clean HTML and normalize
    combined_text := REGEXP_REPLACE(combined_text, '<[^>]*>', '', 'g');
    combined_text := LOWER(TRIM(combined_text));

    -- Count total words
    word_count := ARRAY_LENGTH(STRING_TO_ARRAY(combined_text, ' '), 1);

    IF word_count = 0 THEN
        RETURN 0;
    END IF;

    -- Use extracted keywords if target keywords not provided
    IF p_target_keywords IS NULL THEN
        p_target_keywords := extract_job_keywords(job_data.application_name, job_data.description, job_data.benefits);
    END IF;

    -- Count keyword occurrences
    FOREACH keyword IN ARRAY p_target_keywords
    LOOP
        keyword_count := keyword_count +
            (LENGTH(combined_text) - LENGTH(REPLACE(combined_text, keyword, ''))::INTEGER) / LENGTH(keyword);
    END LOOP;

    -- Calculate density score (aim for 2-8% keyword density)
    density_score := (keyword_count::DECIMAL / word_count) * 100;

    -- Optimal density range scoring
    CASE
        WHEN density_score BETWEEN 2 AND 8 THEN RETURN 100;
        WHEN density_score BETWEEN 1 AND 2 OR density_score BETWEEN 8 AND 12 THEN RETURN 80;
        WHEN density_score BETWEEN 0.5 AND 1 OR density_score BETWEEN 12 AND 15 THEN RETURN 60;
        WHEN density_score > 0 THEN RETURN 40;
        ELSE RETURN 0;
    END CASE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- =====================================================================================
-- SECTION 4: PERSONALIZED SCORE CALCULATION FUNCTIONS
-- =====================================================================================

-- 4.1 Calculate user preference match score
-- Compares job attributes with user preference profile
CREATE OR REPLACE FUNCTION calculate_user_preference_score(
    p_user_id INTEGER,
    p_job_id BIGINT,
    p_occupation_cd1 INTEGER DEFAULT NULL,
    p_occupation_cd2 INTEGER DEFAULT NULL,
    p_feature_codes TEXT DEFAULT NULL,
    p_min_salary INTEGER DEFAULT NULL,
    p_max_salary INTEGER DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    user_profile RECORD;
    job_data RECORD;
    preference_score DECIMAL(10,2) := 0;
    category_score DECIMAL(5,2) := 0;
    salary_score DECIMAL(5,2) := 0;
    feature_score DECIMAL(5,2) := 0;
    total_weight DECIMAL(3,1) := 0;
BEGIN
    -- Get user profile
    SELECT
        up.preference_scores,
        up.category_interests,
        up.avg_salary_preference,
        u.preferred_categories,
        u.preferred_salary_min
    INTO user_profile
    FROM user_profiles up
    JOIN users u ON up.user_id = u.user_id
    WHERE up.user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN 25; -- Default neutral score for users without profiles
    END IF;

    -- Get job data if not provided
    IF p_occupation_cd1 IS NULL OR p_feature_codes IS NULL THEN
        SELECT
            j.occupation_cd1, j.occupation_cd2, j.feature_codes, j.min_salary, j.max_salary
        INTO job_data
        FROM jobs j
        WHERE j.job_id = p_job_id;

        p_occupation_cd1 := COALESCE(p_occupation_cd1, job_data.occupation_cd1);
        p_occupation_cd2 := COALESCE(p_occupation_cd2, job_data.occupation_cd2);
        p_feature_codes := COALESCE(p_feature_codes, job_data.feature_codes);
        p_min_salary := COALESCE(p_min_salary, job_data.min_salary);
        p_max_salary := COALESCE(p_max_salary, job_data.max_salary);
    END IF;

    -- 1. Category preference matching (40% weight)
    IF user_profile.category_interests IS NOT NULL AND p_occupation_cd1 IS NOT NULL THEN
        category_score := COALESCE(
            (user_profile.category_interests->>p_occupation_cd1::TEXT)::DECIMAL * 100,
            25
        );
        preference_score := preference_score + (category_score * 0.4);
        total_weight := total_weight + 0.4;
    END IF;

    -- 2. Salary preference matching (30% weight)
    IF user_profile.avg_salary_preference IS NOT NULL AND p_min_salary IS NOT NULL THEN
        -- Score based on how close job salary is to user's preferred salary
        DECLARE
            job_avg_salary INTEGER := (p_min_salary + COALESCE(p_max_salary, p_min_salary)) / 2;
            salary_diff DECIMAL(5,2);
        BEGIN
            salary_diff := ABS(job_avg_salary - user_profile.avg_salary_preference)::DECIMAL / user_profile.avg_salary_preference;
            salary_score := GREATEST(0, 100 - (salary_diff * 100));
            preference_score := preference_score + (salary_score * 0.3);
            total_weight := total_weight + 0.3;
        END;
    END IF;

    -- 3. Feature preference matching (30% weight)
    IF user_profile.preference_scores IS NOT NULL AND p_feature_codes IS NOT NULL THEN
        DECLARE
            features TEXT[];
            feature TEXT;
            feature_pref DECIMAL(3,2);
        BEGIN
            features := STRING_TO_ARRAY(p_feature_codes, ',');

            FOREACH feature IN ARRAY features
            LOOP
                feature_pref := COALESCE(
                    (user_profile.preference_scores->>('feature_' || feature))::DECIMAL,
                    0.5
                );
                feature_score := feature_score + (feature_pref * 20); -- Each feature up to 20 points
            END LOOP;

            feature_score := LEAST(100, feature_score); -- Cap at 100
            preference_score := preference_score + (feature_score * 0.3);
            total_weight := total_weight + 0.3;
        END;
    END IF;

    -- Normalize by total weight
    IF total_weight > 0 THEN
        preference_score := preference_score / total_weight;
    ELSE
        preference_score := 25; -- Default score if no preferences available
    END IF;

    RETURN GREATEST(0, LEAST(100, preference_score));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 25;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 4.2 Calculate collaborative filtering base score
-- Uses user behavioral patterns to score jobs
CREATE OR REPLACE FUNCTION calculate_collaborative_filtering_score(
    p_user_id INTEGER,
    p_job_id BIGINT,
    p_endcl_cd VARCHAR(20) DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    user_cluster INTEGER;
    similar_users INTEGER[];
    job_data RECORD;
    collab_score DECIMAL(10,4) := 0;
    similar_user_count INTEGER := 0;
    action_weight DECIMAL(3,2);
BEGIN
    -- Get user's behavioral cluster
    SELECT up.behavioral_cluster INTO user_cluster
    FROM user_profiles up
    WHERE up.user_id = p_user_id;

    -- Get job company if not provided
    IF p_endcl_cd IS NULL THEN
        SELECT j.endcl_cd INTO p_endcl_cd
        FROM jobs j
        WHERE j.job_id = p_job_id;
    END IF;

    -- Find similar users (same cluster or similar engagement patterns)
    SELECT ARRAY_AGG(DISTINCT up2.user_id)
    INTO similar_users
    FROM user_profiles up2
    WHERE (up2.behavioral_cluster = user_cluster OR
           ABS(up2.engagement_score - (SELECT engagement_score FROM user_profiles WHERE user_id = p_user_id)) <= 10)
        AND up2.user_id != p_user_id
    LIMIT 100; -- Limit to 100 similar users for performance

    -- Calculate collaborative score based on similar users' actions
    IF similar_users IS NOT NULL THEN
        FOR similar_user_count IN
            SELECT COUNT(DISTINCT ua.user_id)
            FROM user_actions ua
            WHERE ua.user_id = ANY(similar_users)
                AND (ua.job_id = p_job_id OR ua.endcl_cd = p_endcl_cd)
                AND ua.action_timestamp > CURRENT_DATE - INTERVAL '90 days'
        LOOP
            -- Weight different action types
            SELECT
                SUM(CASE ua.action_type
                    WHEN 'application' THEN 1.0
                    WHEN 'favorite' THEN 0.8
                    WHEN 'click' THEN 0.5
                    WHEN 'view' THEN 0.3
                    ELSE 0.1
                END) / GREATEST(1, ARRAY_LENGTH(similar_users, 1))
            INTO action_weight
            FROM user_actions ua
            WHERE ua.user_id = ANY(similar_users)
                AND (ua.job_id = p_job_id OR ua.endcl_cd = p_endcl_cd)
                AND ua.action_timestamp > CURRENT_DATE - INTERVAL '90 days';

            collab_score := COALESCE(action_weight, 0) * 100;
        END LOOP;
    END IF;

    -- Boost score for jobs from companies the user has interacted with before
    IF EXISTS (
        SELECT 1 FROM user_actions ua2
        WHERE ua2.user_id = p_user_id
            AND ua2.endcl_cd = p_endcl_cd
            AND ua2.action_type IN ('application', 'click', 'favorite')
    ) THEN
        collab_score := collab_score + 15;
    END IF;

    RETURN GREATEST(0, LEAST(100, collab_score));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 4.3 Calculate location proximity score
-- Scores based on distance between job and user location
CREATE OR REPLACE FUNCTION calculate_location_proximity_score(
    p_user_id INTEGER,
    p_job_id BIGINT,
    p_job_lat DECIMAL(10,8) DEFAULT NULL,
    p_job_lon DECIMAL(11,8) DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    user_location RECORD;
    job_location RECORD;
    distance_km DECIMAL(8,2);
    proximity_score DECIMAL(5,2) := 0;
BEGIN
    -- Get user location
    SELECT
        cm.latitude as user_lat,
        cm.longitude as user_lon,
        u.preferred_location_radius
    INTO user_location
    FROM users u
    LEFT JOIN city_master cm ON u.city_cd = cm.code
    WHERE u.user_id = p_user_id;

    IF NOT FOUND OR user_location.user_lat IS NULL THEN
        RETURN 50; -- Default moderate score if no user location
    END IF;

    -- Get job location if not provided
    IF p_job_lat IS NULL OR p_job_lon IS NULL THEN
        SELECT j.latitude, j.longitude
        INTO job_location
        FROM jobs j
        WHERE j.job_id = p_job_id;

        p_job_lat := COALESCE(p_job_lat, job_location.latitude);
        p_job_lon := COALESCE(p_job_lon, job_location.longitude);
    END IF;

    IF p_job_lat IS NULL OR p_job_lon IS NULL THEN
        RETURN 50; -- Default moderate score if no job location
    END IF;

    -- Calculate distance
    distance_km := calculate_distance_km(
        user_location.user_lat, user_location.user_lon,
        p_job_lat, p_job_lon
    );

    -- Score based on distance and user's preferred radius
    DECLARE
        preferred_radius INTEGER := COALESCE(user_location.preferred_location_radius, 10);
    BEGIN
        CASE
            WHEN distance_km <= preferred_radius * 0.5 THEN proximity_score := 100;
            WHEN distance_km <= preferred_radius THEN proximity_score := 80;
            WHEN distance_km <= preferred_radius * 1.5 THEN proximity_score := 60;
            WHEN distance_km <= preferred_radius * 2 THEN proximity_score := 40;
            WHEN distance_km <= preferred_radius * 3 THEN proximity_score := 20;
            ELSE proximity_score := 0;
        END CASE;
    END;

    RETURN proximity_score;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 50;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 4.4 Main personalized score calculation function
-- Combines user preferences (40%), collaborative filtering (30%), location (30%)
CREATE OR REPLACE FUNCTION calculate_personalized_score(
    p_user_id INTEGER,
    p_job_id BIGINT
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    preference_score DECIMAL(5,2);
    collab_score DECIMAL(5,2);
    location_score DECIMAL(5,2);
    personalized_score DECIMAL(5,2);
BEGIN
    -- Calculate component scores
    preference_score := calculate_user_preference_score(p_user_id, p_job_id);
    collab_score := calculate_collaborative_filtering_score(p_user_id, p_job_id);
    location_score := calculate_location_proximity_score(p_user_id, p_job_id);

    -- Weighted combination: preference(40%) + collaborative(30%) + location(30%)
    personalized_score := (preference_score * 0.4) + (collab_score * 0.3) + (location_score * 0.3);

    RETURN GREATEST(0, LEAST(100, personalized_score));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 25;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- =====================================================================================
-- SECTION 5: COMPOSITE SCORE CALCULATION
-- =====================================================================================

-- 5.1 Calculate final composite score with configurable weights
-- Combines basic (30%), SEO (20%), and personalized (50%) scores
CREATE OR REPLACE FUNCTION calculate_composite_score(
    p_job_id BIGINT,
    p_user_id INTEGER DEFAULT NULL,
    p_basic_weight DECIMAL(3,2) DEFAULT 0.30,
    p_seo_weight DECIMAL(3,2) DEFAULT 0.20,
    p_personalized_weight DECIMAL(3,2) DEFAULT 0.50
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    basic_score DECIMAL(5,2);
    seo_score DECIMAL(5,2);
    personalized_score DECIMAL(5,2);
    composite_score DECIMAL(5,2);
    total_weight DECIMAL(3,2);
BEGIN
    -- Validate weights sum to 1.0
    total_weight := p_basic_weight + p_seo_weight + p_personalized_weight;
    IF ABS(total_weight - 1.0) > 0.01 THEN
        RAISE EXCEPTION 'Score weights must sum to 1.0, got %', total_weight;
    END IF;

    -- Calculate component scores
    basic_score := calculate_basic_score(p_job_id);
    seo_score := calculate_seo_score(p_job_id);

    -- Personalized score only if user provided
    IF p_user_id IS NOT NULL THEN
        personalized_score := calculate_personalized_score(p_user_id, p_job_id);
    ELSE
        -- Use basic score as fallback for personalized component
        personalized_score := basic_score;
    END IF;

    -- Calculate weighted composite score
    composite_score := (basic_score * p_basic_weight) +
                      (seo_score * p_seo_weight) +
                      (personalized_score * p_personalized_weight);

    RETURN GREATEST(0, LEAST(100, composite_score));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- 5.2 Batch calculate scores for multiple jobs
-- Optimized function for calculating scores for many jobs at once
CREATE OR REPLACE FUNCTION batch_calculate_scores(
    p_job_ids BIGINT[],
    p_user_id INTEGER DEFAULT NULL,
    p_score_types TEXT[] DEFAULT ARRAY['basic', 'seo', 'personalized', 'composite']
) RETURNS TABLE (
    job_id BIGINT,
    basic_score DECIMAL(5,2),
    seo_score DECIMAL(5,2),
    personalized_score DECIMAL(5,2),
    composite_score DECIMAL(5,2)
) AS $$
DECLARE
    job_id_val BIGINT;
    basic_val DECIMAL(5,2);
    seo_val DECIMAL(5,2);
    personal_val DECIMAL(5,2);
    composite_val DECIMAL(5,2);
BEGIN
    -- Loop through provided job IDs
    FOREACH job_id_val IN ARRAY p_job_ids
    LOOP
        -- Initialize scores
        basic_val := NULL;
        seo_val := NULL;
        personal_val := NULL;
        composite_val := NULL;

        -- Calculate requested score types
        IF 'basic' = ANY(p_score_types) THEN
            basic_val := calculate_basic_score(job_id_val);
        END IF;

        IF 'seo' = ANY(p_score_types) THEN
            seo_val := calculate_seo_score(job_id_val);
        END IF;

        IF 'personalized' = ANY(p_score_types) AND p_user_id IS NOT NULL THEN
            personal_val := calculate_personalized_score(p_user_id, job_id_val);
        END IF;

        IF 'composite' = ANY(p_score_types) THEN
            composite_val := calculate_composite_score(job_id_val, p_user_id);
        END IF;

        -- Return results
        RETURN QUERY SELECT job_id_val, basic_val, seo_val, personal_val, composite_val;
    END LOOP;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;

-- =====================================================================================
-- SECTION 6: SCORE UPDATE AND MAINTENANCE FUNCTIONS
-- =====================================================================================

-- 6.1 Update enrichment scores for a job
-- Updates job_enrichment table with calculated scores
CREATE OR REPLACE FUNCTION update_job_enrichment_scores(
    p_job_id BIGINT,
    p_force_recalculate BOOLEAN DEFAULT FALSE
) RETURNS BOOLEAN AS $$
DECLARE
    current_enrichment RECORD;
    new_basic_score DECIMAL(5,2);
    new_seo_score DECIMAL(5,2);
    new_personalized_base DECIMAL(5,2);
BEGIN
    -- Check if enrichment record exists and needs update
    SELECT * INTO current_enrichment
    FROM job_enrichment je
    WHERE je.job_id = p_job_id;

    -- Skip if recently calculated and not forcing recalculation
    IF FOUND AND NOT p_force_recalculate AND
       current_enrichment.calculated_at > CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN
        RETURN FALSE;
    END IF;

    -- Calculate new scores
    new_basic_score := calculate_basic_score(p_job_id);
    new_seo_score := calculate_seo_score(p_job_id);

    -- For personalized base, use collaborative filtering without specific user
    new_personalized_base := calculate_collaborative_filtering_score(NULL, p_job_id);

    -- Insert or update enrichment record
    INSERT INTO job_enrichment (
        job_id,
        basic_score,
        seo_score,
        personalized_score_base,
        calculated_at,
        needs_recalculation
    ) VALUES (
        p_job_id,
        new_basic_score,
        new_seo_score,
        new_personalized_base,
        CURRENT_TIMESTAMP,
        FALSE
    )
    ON CONFLICT (job_id) DO UPDATE SET
        basic_score = new_basic_score,
        seo_score = new_seo_score,
        personalized_score_base = new_personalized_base,
        calculated_at = CURRENT_TIMESTAMP,
        needs_recalculation = FALSE;

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Mark for recalculation on error
        UPDATE job_enrichment
        SET needs_recalculation = TRUE
        WHERE job_id = p_job_id;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- 6.2 Batch update enrichment scores
-- Updates scores for multiple jobs efficiently
CREATE OR REPLACE FUNCTION batch_update_enrichment_scores(
    p_job_ids BIGINT[] DEFAULT NULL,
    p_force_recalculate BOOLEAN DEFAULT FALSE,
    p_batch_size INTEGER DEFAULT 100
) RETURNS INTEGER AS $$
DECLARE
    job_ids_to_process BIGINT[];
    processed_count INTEGER := 0;
    batch_start INTEGER := 1;
    batch_end INTEGER;
    current_job_id BIGINT;
BEGIN
    -- Get job IDs to process
    IF p_job_ids IS NOT NULL THEN
        job_ids_to_process := p_job_ids;
    ELSE
        -- Process jobs that need recalculation or haven't been calculated recently
        SELECT ARRAY_AGG(j.job_id)
        INTO job_ids_to_process
        FROM jobs j
        LEFT JOIN job_enrichment je ON j.job_id = je.job_id
        WHERE j.is_active = TRUE
            AND (je.job_id IS NULL
                 OR je.needs_recalculation = TRUE
                 OR (p_force_recalculate AND je.calculated_at < CURRENT_TIMESTAMP - INTERVAL '1 day')
                 OR je.calculated_at < CURRENT_TIMESTAMP - INTERVAL '7 days')
        LIMIT 10000; -- Prevent runaway queries
    END IF;

    -- Process in batches
    WHILE batch_start <= ARRAY_LENGTH(job_ids_to_process, 1) LOOP
        batch_end := LEAST(batch_start + p_batch_size - 1, ARRAY_LENGTH(job_ids_to_process, 1));

        -- Process current batch
        FOR i IN batch_start..batch_end LOOP
            current_job_id := job_ids_to_process[i];

            IF update_job_enrichment_scores(current_job_id, p_force_recalculate) THEN
                processed_count := processed_count + 1;
            END IF;
        END LOOP;

        batch_start := batch_end + 1;

        -- Commit batch and provide feedback
        COMMIT;
        RAISE NOTICE 'Processed batch ending at position %, total processed: %', batch_end, processed_count;
    END LOOP;

    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================================
-- SECTION 7: PERFORMANCE AND MONITORING FUNCTIONS
-- =====================================================================================

-- 7.1 Get scoring performance statistics
-- Returns performance metrics for scoring functions
CREATE OR REPLACE FUNCTION get_scoring_performance_stats()
RETURNS TABLE (
    metric_name VARCHAR(50),
    metric_value DECIMAL(10,2),
    metric_unit VARCHAR(20)
) AS $$
BEGIN
    -- Jobs with enrichment data
    RETURN QUERY
    SELECT
        'jobs_with_enrichment'::VARCHAR(50),
        COUNT(*)::DECIMAL(10,2),
        'count'::VARCHAR(20)
    FROM job_enrichment;

    -- Average scores
    RETURN QUERY
    SELECT
        'avg_basic_score'::VARCHAR(50),
        AVG(basic_score)::DECIMAL(10,2),
        'score'::VARCHAR(20)
    FROM job_enrichment WHERE basic_score IS NOT NULL;

    RETURN QUERY
    SELECT
        'avg_seo_score'::VARCHAR(50),
        AVG(seo_score)::DECIMAL(10,2),
        'score'::VARCHAR(20)
    FROM job_enrichment WHERE seo_score IS NOT NULL;

    RETURN QUERY
    SELECT
        'avg_composite_score'::VARCHAR(50),
        AVG(composite_score)::DECIMAL(10,2),
        'score'::VARCHAR(20)
    FROM job_enrichment WHERE composite_score IS NOT NULL;

    -- Jobs needing recalculation
    RETURN QUERY
    SELECT
        'jobs_need_recalc'::VARCHAR(50),
        COUNT(*)::DECIMAL(10,2),
        'count'::VARCHAR(20)
    FROM job_enrichment WHERE needs_recalculation = TRUE;

    -- Score distribution
    RETURN QUERY
    SELECT
        'high_scoring_jobs'::VARCHAR(50),
        COUNT(*)::DECIMAL(10,2),
        'count'::VARCHAR(20)
    FROM job_enrichment WHERE composite_score >= 80;

END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================================
-- SECTION 8: EXAMPLE USAGE AND TESTING
-- =====================================================================================

-- Example usage queries (commented out for production)
/*
-- Calculate basic score for a specific job
SELECT calculate_basic_score(123456);

-- Calculate SEO score for a job
SELECT calculate_seo_score(123456);

-- Calculate personalized score for user-job pair
SELECT calculate_personalized_score(1001, 123456);

-- Calculate composite score with custom weights
SELECT calculate_composite_score(123456, 1001, 0.25, 0.25, 0.50);

-- Batch calculate scores for multiple jobs
SELECT * FROM batch_calculate_scores(
    ARRAY[123456, 123457, 123458],
    1001,
    ARRAY['basic', 'seo', 'composite']
);

-- Update enrichment scores for a job
SELECT update_job_enrichment_scores(123456, TRUE);

-- Batch update enrichment scores
SELECT batch_update_enrichment_scores(NULL, FALSE, 50);

-- Get performance statistics
SELECT * FROM get_scoring_performance_stats();

-- Find jobs with highest composite scores for a user
SELECT
    j.job_id,
    j.application_name,
    j.company_name,
    calculate_composite_score(j.job_id, 1001) as score
FROM active_jobs j
ORDER BY score DESC
LIMIT 10;
*/

-- =====================================================================================
-- END OF SCORING FUNCTIONS
-- =====================================================================================

-- Comments:
-- 1. All functions are marked as PARALLEL SAFE for performance optimization
-- 2. Comprehensive error handling prevents function failures from affecting batch operations
-- 3. Configurable weights allow for A/B testing and algorithm tuning
-- 4. Batch processing functions optimize for high-volume operations (100K jobs × 10K users)
-- 5. Performance monitoring functions help track algorithm effectiveness
-- 6. Functions integrate seamlessly with existing table structure
-- 7. SEO keyword matching uses optimized LIKE queries for PostgreSQL performance
-- 8. Collaborative filtering considers behavioral clusters and engagement patterns
-- 9. Location scoring uses Haversine formula for accurate distance calculation
-- 10. Score normalization ensures consistent 0-100 range across all components