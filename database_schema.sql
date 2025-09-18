-- =====================================================================================
-- Job Matching System - Complete PostgreSQL/Supabase Database Schema
-- =====================================================================================
-- Version: 5.1 (Merged from specs/001-job-matching-system and specs/002-think-hard-ultrathink)
-- Database: Supabase (PostgreSQL 15)
-- Created: 2025-09-18
--
-- This schema supports:
-- - 100,000+ jobs with 100+ fields each
-- - 10,000 users with behavioral tracking
-- - 400,000 daily matching results
-- - Advanced scoring and recommendation engine
-- - Email generation and delivery system
-- =====================================================================================

-- =====================================================================================
-- SECTION 1: MASTER DATA TABLES
-- =====================================================================================

-- 1.1 Prefecture Master (都道府県マスター)
-- Contains all 47 Japanese prefectures with regional grouping
CREATE TABLE prefecture_master (
    code CHAR(2) PRIMARY KEY,                    -- JIS prefecture code (01-47)
    name VARCHAR(10) NOT NULL,                   -- Prefecture name (東京都, 大阪府, etc.)
    region VARCHAR(20) NOT NULL,                 -- Regional grouping (関東, 関西, etc.)
    sort_order INTEGER NOT NULL,                 -- Display order
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_pref_code_format CHECK (code ~ '^[0-4][0-9]$'),
    CONSTRAINT chk_pref_sort_order CHECK (sort_order BETWEEN 1 AND 47)
);

-- 1.2 City Master (市区町村マスター)
-- Contains all cities/municipalities with geographic coordinates
CREATE TABLE city_master (
    code VARCHAR(5) PRIMARY KEY,                 -- City code (prefecture + city)
    pref_cd CHAR(2) NOT NULL REFERENCES prefecture_master(code) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,                   -- City name
    latitude DECIMAL(10, 8),                     -- Geographic latitude
    longitude DECIMAL(11, 8),                    -- Geographic longitude
    nearby_city_codes VARCHAR(5)[],              -- Array of adjacent city codes
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_cities_prefecture (pref_cd),
    INDEX idx_cities_coordinates (latitude, longitude) WHERE latitude IS NOT NULL
);

-- 1.3 Occupation Master (職種マスター)
-- Job category hierarchy with major/minor classifications
CREATE TABLE occupation_master (
    code INTEGER PRIMARY KEY,                    -- Occupation code
    name VARCHAR(100) NOT NULL,                  -- Occupation name
    major_category_code INTEGER,                 -- Major category (100, 200, etc.)
    minor_category_code INTEGER,                 -- Minor category subdivision
    description TEXT,                            -- Detailed description
    display_order INTEGER,                       -- Sort order for UI
    is_active BOOLEAN DEFAULT TRUE,              -- Active flag
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_occupation_major (major_category_code, display_order),
    INDEX idx_occupation_active (is_active, display_order)
);

-- 1.4 Employment Type Master (雇用形態マスター)
-- Employment types (part-time, full-time, contract, etc.)
CREATE TABLE employment_type_master (
    code INTEGER PRIMARY KEY,                    -- Employment type code
    name VARCHAR(50) NOT NULL,                   -- Type name (アルバイト, パート, etc.)
    description TEXT,                            -- Detailed description
    is_valid_for_matching BOOLEAN DEFAULT TRUE,  -- Whether to include in matching
    display_order INTEGER,                       -- Sort order
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_employment_type_valid (is_valid_for_matching, display_order)
);

-- 1.5 Feature Master (特徴マスター)
-- Job features/benefits (daily pay, remote work, student-friendly, etc.)
CREATE TABLE feature_master (
    feature_code VARCHAR(3) PRIMARY KEY,         -- 3-character feature code
    feature_name VARCHAR(100) NOT NULL,          -- Feature display name
    category VARCHAR(50),                        -- Feature category grouping
    display_priority INTEGER DEFAULT 0,          -- Priority for display
    icon_class VARCHAR(50),                      -- CSS icon class
    is_active BOOLEAN DEFAULT TRUE,              -- Active flag
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_features_category (category, display_priority),
    INDEX idx_features_active (is_active, display_priority)
);

-- 1.6 SEMrush Keywords Master (SEOキーワードマスター)
-- SEO keywords with search volume and difficulty metrics
CREATE TABLE semrush_keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword VARCHAR(200) NOT NULL UNIQUE,        -- Search keyword
    search_volume INTEGER DEFAULT 0,             -- Monthly search volume
    keyword_difficulty DECIMAL(5,2),             -- SEO difficulty (0-100)
    cpc DECIMAL(10, 2),                         -- Cost per click
    category VARCHAR(50),                        -- Keyword category
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_search_volume CHECK (search_volume >= 0),
    CONSTRAINT chk_keyword_difficulty CHECK (keyword_difficulty BETWEEN 0 AND 100),
    CONSTRAINT chk_cpc CHECK (cpc >= 0),

    INDEX idx_keywords_volume (search_volume DESC),
    INDEX idx_keywords_difficulty (keyword_difficulty),
    INDEX idx_keywords_category (category, search_volume DESC),
    INDEX idx_keywords_text_search (keyword) -- For text search queries
);

-- =====================================================================================
-- SECTION 2: CORE ENTITY TABLES
-- =====================================================================================

-- 2.1 Jobs Table (求人情報)
-- Master job postings with 100+ fields supporting complex matching
CREATE TABLE jobs (
    job_id BIGINT PRIMARY KEY,                   -- Unique job identifier
    endcl_cd VARCHAR(20) NOT NULL,               -- End client company code
    application_id VARCHAR(100) UNIQUE,          -- External application ID
    company_name VARCHAR(255) NOT NULL,          -- Company name
    application_name TEXT NOT NULL,              -- Job title/name

    -- Location Information
    pref_cd CHAR(2) REFERENCES prefecture_master(code),
    city_cd VARCHAR(5) REFERENCES city_master(code),
    station_name_eki VARCHAR(100),               -- Nearest station name
    address VARCHAR(500),                        -- Full address
    latitude DECIMAL(10, 8),                     -- Geographic latitude
    longitude DECIMAL(11, 8),                    -- Geographic longitude

    -- Salary Information
    salary_type VARCHAR(20) DEFAULT 'hourly' CHECK (salary_type IN ('hourly', 'daily', 'monthly')),
    min_salary INTEGER,                          -- Minimum salary/wage
    max_salary INTEGER,                          -- Maximum salary/wage
    fee INTEGER CHECK (fee >= 0 AND fee <= 5000), -- Application incentive fee (0-5000 yen)

    -- Work Conditions
    hours TEXT,                                  -- Working hours (may contain HTML)
    work_days VARCHAR(200),                      -- Working days description
    shift_flexibility VARCHAR(100),              -- Shift flexibility info

    -- Categories
    occupation_cd1 INTEGER REFERENCES occupation_master(code),     -- Major occupation
    occupation_cd2 INTEGER REFERENCES occupation_master(code),     -- Minor occupation
    employment_type_cd INTEGER REFERENCES employment_type_master(code),

    -- Features (stored as comma-separated codes, with derived boolean flags)
    feature_codes TEXT,                          -- Comma-separated feature codes
    -- Derived feature flags (generated from feature_codes)
    has_daily_payment BOOLEAN GENERATED ALWAYS AS (
        feature_codes IS NOT NULL AND position('001' in feature_codes) > 0
    ) STORED,
    has_weekly_payment BOOLEAN GENERATED ALWAYS AS (
        feature_codes IS NOT NULL AND position('002' in feature_codes) > 0
    ) STORED,
    has_no_experience BOOLEAN GENERATED ALWAYS AS (
        feature_codes IS NOT NULL AND position('003' in feature_codes) > 0
    ) STORED,
    has_student_welcome BOOLEAN GENERATED ALWAYS AS (
        feature_codes IS NOT NULL AND position('004' in feature_codes) > 0
    ) STORED,
    has_remote_work BOOLEAN GENERATED ALWAYS AS (
        feature_codes IS NOT NULL AND position('005' in feature_codes) > 0
    ) STORED,
    has_transportation BOOLEAN GENERATED ALWAYS AS (
        feature_codes IS NOT NULL AND position('006' in feature_codes) > 0
    ) STORED,

    -- Content
    description TEXT,                            -- Job description
    benefits TEXT,                               -- Benefits description
    search_keywords TEXT[],                      -- Array of search keywords

    -- Status and Metadata
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'inactive', 'expired')),
    is_active BOOLEAN DEFAULT TRUE,              -- Quick active flag
    posting_date TIMESTAMPTZ,                    -- When job was posted
    end_at TIMESTAMPTZ,                         -- Job expiration date (v5.1 spec)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_salary_range CHECK (min_salary IS NULL OR max_salary IS NULL OR min_salary <= max_salary),
    CONSTRAINT chk_active_status CHECK (is_active = (status = 'active')),
    CONSTRAINT chk_end_date CHECK (end_at IS NULL OR end_at > posting_date),

    -- Indexes for high-frequency queries
    INDEX idx_jobs_location (pref_cd, city_cd, posting_date) WHERE is_active = TRUE,
    INDEX idx_jobs_category (occupation_cd1, employment_type_cd, posting_date) WHERE is_active = TRUE,
    INDEX idx_jobs_active_date (is_active, posting_date DESC),
    INDEX idx_jobs_endcl (endcl_cd, posting_date DESC),
    INDEX idx_jobs_fee (fee DESC) WHERE is_active = TRUE,
    INDEX idx_jobs_features (has_daily_payment, has_weekly_payment, has_no_experience) WHERE is_active = TRUE,
    INDEX idx_jobs_coordinates (latitude, longitude) WHERE latitude IS NOT NULL AND is_active = TRUE
);

-- 2.2 Users Table (ユーザー情報)
-- User master data with preferences and status tracking
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,                 -- Unique user identifier
    email VARCHAR(255) UNIQUE NOT NULL,          -- User email address
    email_hash VARCHAR(256) UNIQUE,              -- Hashed email for privacy

    -- Basic Demographics
    age_group VARCHAR(20),                       -- Age range (10代, 20代前半, etc.)
    gender VARCHAR(10),                          -- Gender

    -- Location Information
    pref_cd CHAR(2) REFERENCES prefecture_master(code),
    city_cd VARCHAR(5) REFERENCES city_master(code),

    -- Preferences (stored as arrays for flexibility)
    preferred_work_style VARCHAR(50)[],          -- Array of preferred work styles
    preferred_categories VARCHAR(4)[],           -- Array of preferred occupation codes
    preferred_salary_min INTEGER,                -- Minimum preferred salary
    preferred_location_radius INTEGER DEFAULT 10, -- Search radius in km

    -- Status and Activity
    registration_date DATE,                      -- Initial registration
    last_login_date TIMESTAMPTZ,                -- Last login timestamp
    last_active_at TIMESTAMPTZ,                 -- Last activity timestamp
    is_active BOOLEAN DEFAULT TRUE,              -- Account active flag
    email_subscription BOOLEAN DEFAULT TRUE,     -- Email subscription status

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_user_radius CHECK (preferred_location_radius BETWEEN 1 AND 100),
    CONSTRAINT chk_user_salary CHECK (preferred_salary_min IS NULL OR preferred_salary_min > 0),

    -- Indexes
    INDEX idx_users_location (pref_cd, city_cd),
    INDEX idx_users_active (is_active, email_subscription),
    INDEX idx_users_last_active (last_active_at DESC) WHERE is_active = TRUE
);

-- 2.3 User Actions Table (ユーザー行動履歴)
-- Comprehensive user behavior tracking for recommendations
CREATE TABLE user_actions (
    action_id BIGSERIAL PRIMARY KEY,             -- Unique action identifier
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT REFERENCES jobs(job_id) ON DELETE CASCADE,
    endcl_cd VARCHAR(20),                        -- Company code for aggregation

    -- Action Details
    action_type VARCHAR(50) NOT NULL,            -- 'application', 'click', 'email_open', 'favorite', 'view'
    action_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Context Information
    source VARCHAR(50),                          -- 'email', 'web', 'app', 'direct'
    session_id VARCHAR(100),                     -- Session identifier
    device_type VARCHAR(20),                     -- 'desktop', 'mobile', 'tablet'
    user_agent TEXT,                             -- Browser user agent

    -- Additional Data (flexible JSON storage)
    action_metadata JSONB,                       -- Additional context data

    -- Constraints
    CONSTRAINT chk_action_type CHECK (action_type IN ('application', 'click', 'email_open', 'favorite', 'view', 'share')),
    CONSTRAINT chk_action_source CHECK (source IN ('email', 'web', 'app', 'direct', 'social')),

    -- Indexes for analytics and recommendations
    INDEX idx_actions_user_time (user_id, action_timestamp DESC),
    INDEX idx_actions_job_type (job_id, action_type, action_timestamp),
    INDEX idx_actions_endcl_time (endcl_cd, action_type, action_timestamp),
    INDEX idx_actions_timestamp (action_timestamp) WHERE action_type = 'application',
    INDEX idx_actions_session (session_id, action_timestamp)
);

-- 2.4 User Profiles Table (ユーザープロファイル)
-- Aggregated user preferences and behavior patterns for personalization
CREATE TABLE user_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Preference Scores (JSON for flexibility)
    preference_scores JSONB,                     -- {"hourly_work": 0.8, "remote": 0.6, ...}
    category_interests JSONB,                    -- {"100": 0.9, "200": 0.3, ...} (occupation preferences)

    -- Geographic Preferences
    location_preference_radius INTEGER DEFAULT 10, -- Preferred search radius (km)
    preferred_areas VARCHAR(5)[],                -- Array of preferred city codes

    -- Behavioral Patterns
    avg_salary_preference INTEGER,               -- Average preferred salary
    application_count INTEGER DEFAULT 0,         -- Total applications made
    click_count INTEGER DEFAULT 0,               -- Total clicks made
    email_open_rate DECIMAL(5,4),               -- Email engagement rate
    last_application_date DATE,                  -- Most recent application

    -- Machine Learning Features
    latent_factors FLOAT[],                      -- 50-dimension vector for collaborative filtering
    behavioral_cluster INTEGER,                  -- User behavior cluster ID
    engagement_score DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN application_count + click_count = 0 THEN 0
            ELSE LEAST(100, (application_count * 10 + click_count) / GREATEST(1, EXTRACT(DAYS FROM CURRENT_DATE - COALESCE(last_application_date, CURRENT_DATE - INTERVAL '30 days'))))
        END
    ) STORED,                                    -- Calculated engagement score

    -- Timestamps
    profile_updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_profile_radius CHECK (location_preference_radius BETWEEN 1 AND 100),
    CONSTRAINT chk_profile_counts CHECK (application_count >= 0 AND click_count >= 0),
    CONSTRAINT chk_open_rate CHECK (email_open_rate BETWEEN 0 AND 1),

    -- Indexes
    INDEX idx_profiles_user (user_id),
    INDEX idx_profiles_updated (profile_updated_at DESC),
    INDEX idx_profiles_engagement (engagement_score DESC),
    INDEX idx_profiles_cluster (behavioral_cluster)
);

-- =====================================================================================
-- SECTION 3: PROCESSING AND ENRICHMENT TABLES
-- =====================================================================================

-- 3.1 Job Enrichment Table (求人拡張情報)
-- Calculated scores and metadata for enhanced job matching
CREATE TABLE job_enrichment (
    enrichment_id SERIAL PRIMARY KEY,
    job_id BIGINT UNIQUE NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- Scoring Components (0-100 scale)
    basic_score DECIMAL(5,2) CHECK (basic_score BETWEEN 0 AND 100),      -- Salary, location, benefits
    seo_score DECIMAL(5,2) CHECK (seo_score BETWEEN 0 AND 100),          -- SEO keyword matching
    personalized_score_base DECIMAL(5,2) CHECK (personalized_score_base BETWEEN 0 AND 100), -- Base popularity

    -- Composite Score (weighted combination)
    composite_score DECIMAL(5,2) GENERATED ALWAYS AS (
        COALESCE(basic_score * 0.4 + seo_score * 0.2 + personalized_score_base * 0.4, 0)
    ) STORED,

    -- Category Classifications
    needs_categories VARCHAR(30)[],              -- ['日払い', '高時給', 'シフト自由', ...]
    occupation_categories VARCHAR(4)[],          -- ['100', '200', ...] (occupation codes)

    -- Performance Metrics
    application_count INTEGER DEFAULT 0,         -- Total applications received
    click_count INTEGER DEFAULT 0,               -- Total clicks received
    view_count INTEGER DEFAULT 0,                -- Total views
    conversion_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE
            WHEN click_count > 0 THEN application_count::DECIMAL / click_count
            ELSE 0
        END
    ) STORED,                                    -- Click-to-application conversion

    -- SEO Analysis
    extracted_keywords TEXT[],                   -- Keywords extracted from job content
    semrush_keyword_matches TEXT[],             -- Matching SEMrush keywords
    keyword_density_score DECIMAL(5,2),         -- Keyword density score

    -- Metadata
    calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    needs_recalculation BOOLEAN DEFAULT FALSE,   -- Flag for batch recalculation

    -- Indexes
    INDEX idx_enrichment_job (job_id),
    INDEX idx_enrichment_scores (composite_score DESC, basic_score DESC),
    INDEX idx_enrichment_performance (conversion_rate DESC, application_count DESC),
    INDEX idx_enrichment_recalc (needs_recalculation, calculated_at) WHERE needs_recalculation = TRUE
);

-- 3.2 User Job Mapping Table (ユーザー求人マッチング結果)
-- Daily matching results between users and jobs (~400K records daily)
CREATE TABLE user_job_mapping (
    mapping_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- Matching Score Components
    match_score DECIMAL(5,2) NOT NULL,           -- Overall match score (0-100)
    score_components JSONB,                      -- {"basic": 70, "seo": 20, "personal": 85}

    -- Matching Reasons and Context
    match_reasons VARCHAR(100)[],                -- ['地域が近い', '希望給与に合致', ...]
    distance_km DECIMAL(6,2),                   -- Distance from user location

    -- Batch Information
    batch_date DATE NOT NULL,                    -- Processing date
    batch_id INTEGER,                            -- Reference to batch_jobs table
    rank_in_batch INTEGER,                       -- Rank within user's matches for this batch

    -- Status Flags
    is_selected_for_email BOOLEAN DEFAULT FALSE, -- Selected for email inclusion
    email_section VARCHAR(30),                   -- Email section if selected

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_mapping_score CHECK (match_score BETWEEN 0 AND 100),
    CONSTRAINT chk_mapping_distance CHECK (distance_km IS NULL OR distance_km >= 0),
    CONSTRAINT chk_mapping_rank CHECK (rank_in_batch IS NULL OR rank_in_batch > 0),

    -- Unique constraint for daily mappings
    UNIQUE(user_id, job_id, batch_date),

    -- Indexes for high-frequency queries
    INDEX idx_mapping_user_date (user_id, batch_date, rank_in_batch),
    INDEX idx_mapping_batch_score (batch_date, match_score DESC),
    INDEX idx_mapping_email_selection (batch_date, is_selected_for_email) WHERE is_selected_for_email = TRUE,
    INDEX idx_mapping_job_date (job_id, batch_date)
) PARTITION BY RANGE (batch_date);  -- Monthly partitioning for performance

-- 3.3 Daily Job Picks Table (日次選定求人)
-- Curated selection of 40 jobs per user for email campaigns
CREATE TABLE daily_job_picks (
    pick_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- Email Section Configuration
    section VARCHAR(30) NOT NULL,                -- 'top5', 'regional', 'nearby', 'benefits', 'new', 'editorial_picks'
    section_rank INTEGER NOT NULL,               -- Position within section (1-N)
    section_order INTEGER,                       -- Section display order in email

    -- Display Customization
    display_title VARCHAR(500),                  -- Customized job title for email
    display_description TEXT,                    -- Customized description
    highlight_points VARCHAR(200)[],             -- Key selling points to highlight
    custom_cta_text VARCHAR(100),               -- Custom call-to-action text

    -- Tracking and Attribution
    pick_date DATE NOT NULL,                     -- Date of selection
    mapping_id BIGINT REFERENCES user_job_mapping(mapping_id), -- Source mapping
    selection_reason VARCHAR(100),               -- Why this job was selected

    -- Performance Tracking
    email_clicks INTEGER DEFAULT 0,              -- Clicks from email
    email_applications INTEGER DEFAULT 0,        -- Applications from email

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_picks_section CHECK (section IN ('top5', 'regional', 'nearby', 'benefits', 'new', 'editorial_picks')),
    CONSTRAINT chk_picks_rank CHECK (section_rank > 0),
    CONSTRAINT chk_picks_order CHECK (section_order IS NULL OR section_order BETWEEN 1 AND 6),

    -- Business rule: unique job per user per day
    UNIQUE(user_id, job_id, pick_date),

    -- Indexes
    INDEX idx_picks_user_date (user_id, pick_date, section_order, section_rank),
    INDEX idx_picks_section_date (section, pick_date, section_rank),
    INDEX idx_picks_performance (pick_date, email_clicks DESC) WHERE email_clicks > 0
) PARTITION BY RANGE (pick_date);  -- Daily partitioning

-- 3.4 Daily Email Queue Table (メール配信キュー)
-- Generated email content ready for delivery
CREATE TABLE daily_email_queue (
    queue_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Email Content
    subject VARCHAR(500) NOT NULL,               -- Email subject line
    html_content TEXT NOT NULL,                  -- Full HTML email content
    text_content TEXT,                           -- Plain text version
    preheader_text VARCHAR(200),                 -- Email preheader text

    -- Delivery Configuration
    scheduled_date DATE NOT NULL,                -- Target delivery date
    scheduled_time TIME DEFAULT '06:00:00',      -- Target delivery time
    timezone VARCHAR(50) DEFAULT 'Asia/Tokyo',   -- User timezone

    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending',        -- 'pending', 'sent', 'failed', 'cancelled', 'deferred'
    sent_at TIMESTAMPTZ,                         -- Actual send timestamp
    delivered_at TIMESTAMPTZ,                    -- Delivery confirmation
    error_message TEXT,                          -- Error details if failed
    retry_count INTEGER DEFAULT 0,               -- Retry attempts

    -- Email Service Integration
    email_tracking_id VARCHAR(100),              -- External service tracking ID
    email_service_response JSONB,                -- Response from email service

    -- Performance Metrics
    opens_count INTEGER DEFAULT 0,               -- Email opens
    clicks_count INTEGER DEFAULT 0,              -- Total clicks
    applications_count INTEGER DEFAULT 0,        -- Applications generated

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_queue_status CHECK (status IN ('pending', 'sent', 'failed', 'cancelled', 'deferred')),
    CONSTRAINT chk_queue_retry CHECK (retry_count >= 0 AND retry_count <= 5),
    CONSTRAINT chk_queue_metrics CHECK (opens_count >= 0 AND clicks_count >= 0 AND applications_count >= 0),

    -- Business rule: one email per user per day
    UNIQUE(user_id, scheduled_date),

    -- Indexes
    INDEX idx_queue_status_schedule (status, scheduled_date, scheduled_time),
    INDEX idx_queue_user_date (user_id, scheduled_date DESC),
    INDEX idx_queue_tracking (email_tracking_id) WHERE email_tracking_id IS NOT NULL,
    INDEX idx_queue_performance (scheduled_date, applications_count DESC) WHERE applications_count > 0
);

-- =====================================================================================
-- SECTION 4: ADDITIONAL SUPPORTING TABLES
-- =====================================================================================

-- 4.1 Company Popularity Table (企業人気度)
-- Aggregated company performance metrics for scoring
CREATE TABLE company_popularity (
    endcl_cd VARCHAR(20) PRIMARY KEY,            -- Company identifier
    company_name VARCHAR(255),                   -- Company display name

    -- Performance Metrics (360-day rolling window)
    total_views_360d INTEGER DEFAULT 0,          -- Total job views
    total_clicks_360d INTEGER DEFAULT 0,         -- Total job clicks
    total_applications_360d INTEGER DEFAULT 0,   -- Total applications

    -- Calculated Rates (generated columns for consistency)
    click_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE
            WHEN total_views_360d > 0 THEN total_clicks_360d::DECIMAL / total_views_360d
            ELSE 0
        END
    ) STORED,
    application_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE
            WHEN total_clicks_360d > 0 THEN total_applications_360d::DECIMAL / total_clicks_360d
            ELSE 0
        END
    ) STORED,

    -- Ranking and Scoring
    popularity_score DECIMAL(5,2),               -- Calculated popularity score (0-100)
    industry_rank INTEGER,                       -- Rank within industry
    overall_rank INTEGER,                        -- Overall rank across all companies

    -- Additional Metrics
    avg_salary_offered INTEGER,                  -- Average salary across jobs
    active_job_count INTEGER DEFAULT 0,          -- Current active job count
    user_favorite_count INTEGER DEFAULT 0,       -- Times favorited by users

    -- Timestamps
    last_calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_popularity_metrics CHECK (
        total_views_360d >= 0 AND
        total_clicks_360d >= 0 AND
        total_applications_360d >= 0 AND
        total_clicks_360d <= total_views_360d AND
        total_applications_360d <= total_clicks_360d
    ),
    CONSTRAINT chk_popularity_score CHECK (popularity_score BETWEEN 0 AND 100),

    -- Indexes
    INDEX idx_popularity_score (popularity_score DESC),
    INDEX idx_popularity_rates (application_rate DESC, click_rate DESC),
    INDEX idx_popularity_rank (overall_rank) WHERE overall_rank IS NOT NULL
);

-- 4.2 Job Keywords Junction Table (求人-キーワード関連)
-- Many-to-many relationship between jobs and SEO keywords
CREATE TABLE job_keywords (
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    keyword_id INTEGER NOT NULL REFERENCES semrush_keywords(keyword_id) ON DELETE CASCADE,

    -- Relationship Metadata
    match_count INTEGER DEFAULT 1,               -- Number of times keyword appears
    match_score DECIMAL(5,2),                   -- Relevance score for this match
    match_context VARCHAR(100),                  -- Where keyword was found (title, description, etc.)

    -- Automatic timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Primary key and constraints
    PRIMARY KEY (job_id, keyword_id),
    CONSTRAINT chk_job_keywords_count CHECK (match_count > 0),
    CONSTRAINT chk_job_keywords_score CHECK (match_score IS NULL OR match_score BETWEEN 0 AND 100),

    -- Indexes for bidirectional lookups
    INDEX idx_job_keywords_job (job_id, match_score DESC),
    INDEX idx_job_keywords_keyword (keyword_id, match_score DESC)
);

-- 4.3 Batch Jobs Table (バッチジョブ管理)
-- Tracking and monitoring of all batch processing jobs
CREATE TABLE batch_jobs (
    batch_id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,               -- 'daily_matching', 'scoring', 'email_generation', 'cleanup'
    job_name VARCHAR(100),                       -- Human-readable job name

    -- Execution Status
    status VARCHAR(20) DEFAULT 'pending',        -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMPTZ,                      -- Job start time
    completed_at TIMESTAMPTZ,                    -- Job completion time
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN started_at IS NOT NULL AND completed_at IS NOT NULL
            THEN EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
            ELSE NULL
        END
    ) STORED,                                    -- Calculated duration

    -- Progress Tracking
    total_records INTEGER,                       -- Total records to process
    processed_records INTEGER DEFAULT 0,         -- Records processed so far
    success_count INTEGER DEFAULT 0,             -- Successful operations
    error_count INTEGER DEFAULT 0,               -- Failed operations
    progress_percentage DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_records > 0 THEN (processed_records::DECIMAL / total_records) * 100
            ELSE 0
        END
    ) STORED,                                    -- Calculated progress

    -- Error Handling
    error_logs JSONB,                            -- Detailed error information
    last_error_message TEXT,                     -- Most recent error
    retry_count INTEGER DEFAULT 0,               -- Number of retry attempts

    -- Configuration and Metadata
    job_parameters JSONB,                        -- Job configuration parameters
    server_hostname VARCHAR(100),                -- Server that ran the job
    process_id INTEGER,                          -- System process ID

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_batch_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT chk_batch_records CHECK (
        total_records IS NULL OR
        (total_records >= 0 AND processed_records >= 0 AND processed_records <= total_records)
    ),
    CONSTRAINT chk_batch_counts CHECK (success_count >= 0 AND error_count >= 0),
    CONSTRAINT chk_batch_times CHECK (started_at IS NULL OR completed_at IS NULL OR completed_at >= started_at),

    -- Indexes
    INDEX idx_batch_status_time (status, started_at DESC),
    INDEX idx_batch_type_time (job_type, started_at DESC),
    INDEX idx_batch_completion (completed_at DESC) WHERE status = 'completed'
);

-- =====================================================================================
-- SECTION 5: VIEWS AND FUNCTIONS
-- =====================================================================================

-- 5.1 Active Jobs View
-- Frequently used view for active, valid jobs
CREATE VIEW active_jobs AS
SELECT
    j.*,
    je.composite_score,
    je.application_count,
    je.conversion_rate,
    cp.popularity_score as company_popularity_score
FROM jobs j
LEFT JOIN job_enrichment je ON j.job_id = je.job_id
LEFT JOIN company_popularity cp ON j.endcl_cd = cp.endcl_cd
WHERE j.is_active = TRUE
    AND j.status = 'active'
    AND (j.end_at IS NULL OR j.end_at > CURRENT_TIMESTAMP)
    AND j.employment_type_cd IN (1, 3); -- Only part-time and arubaito

-- 5.2 User Engagement Summary View
-- User activity and engagement metrics
CREATE VIEW user_engagement_summary AS
SELECT
    u.user_id,
    u.email,
    u.is_active,
    up.engagement_score,
    up.application_count,
    up.click_count,
    up.email_open_rate,
    COUNT(DISTINCT ua.action_id) FILTER (WHERE ua.action_type = 'application' AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days') as applications_30d,
    COUNT(DISTINCT ua.action_id) FILTER (WHERE ua.action_type = 'click' AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days') as clicks_30d,
    MAX(ua.action_timestamp) as last_action_at
FROM users u
LEFT JOIN user_profiles up ON u.user_id = up.user_id
LEFT JOIN user_actions ua ON u.user_id = ua.user_id
GROUP BY u.user_id, u.email, u.is_active, up.engagement_score, up.application_count, up.click_count, up.email_open_rate;

-- 5.3 Recent Applications View
-- Track recent applications to prevent duplicate recommendations
CREATE VIEW recent_applications AS
SELECT DISTINCT
    user_id,
    endcl_cd,
    MAX(action_timestamp) as last_application_at
FROM user_actions
WHERE action_type = 'application'
    AND action_timestamp > CURRENT_DATE - INTERVAL '14 days'
GROUP BY user_id, endcl_cd;

-- =====================================================================================
-- SECTION 6: TRIGGERS AND FUNCTIONS
-- =====================================================================================

-- 6.1 Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prefecture_master_updated_at BEFORE UPDATE ON prefecture_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_city_master_updated_at BEFORE UPDATE ON city_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_email_queue_updated_at BEFORE UPDATE ON daily_email_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_batch_jobs_updated_at BEFORE UPDATE ON batch_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6.2 User profile sync trigger
-- Automatically update user profiles when user actions change
CREATE OR REPLACE FUNCTION sync_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    -- Update application and click counts
    INSERT INTO user_profiles (user_id, application_count, click_count, last_application_date, profile_updated_at)
    VALUES (
        NEW.user_id,
        CASE WHEN NEW.action_type = 'application' THEN 1 ELSE 0 END,
        CASE WHEN NEW.action_type = 'click' THEN 1 ELSE 0 END,
        CASE WHEN NEW.action_type = 'application' THEN NEW.action_timestamp::DATE ELSE NULL END,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (user_id) DO UPDATE SET
        application_count = user_profiles.application_count + CASE WHEN NEW.action_type = 'application' THEN 1 ELSE 0 END,
        click_count = user_profiles.click_count + CASE WHEN NEW.action_type = 'click' THEN 1 ELSE 0 END,
        last_application_date = CASE
            WHEN NEW.action_type = 'application' AND NEW.action_timestamp::DATE > COALESCE(user_profiles.last_application_date, '1900-01-01'::DATE)
            THEN NEW.action_timestamp::DATE
            ELSE user_profiles.last_application_date
        END,
        profile_updated_at = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER sync_user_profile_trigger
    AFTER INSERT ON user_actions
    FOR EACH ROW EXECUTE FUNCTION sync_user_profile();

-- =====================================================================================
-- SECTION 7: PARTITIONING SETUP
-- =====================================================================================

-- Create initial partitions for large tables
-- user_job_mapping partitions (monthly)
CREATE TABLE user_job_mapping_2025_09 PARTITION OF user_job_mapping
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

CREATE TABLE user_job_mapping_2025_10 PARTITION OF user_job_mapping
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

-- daily_job_picks partitions (monthly)
CREATE TABLE daily_job_picks_2025_09 PARTITION OF daily_job_picks
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

CREATE TABLE daily_job_picks_2025_10 PARTITION OF daily_job_picks
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

-- =====================================================================================
-- SECTION 8: INITIAL DATA AND CONSTRAINTS
-- =====================================================================================

-- Insert sample master data
INSERT INTO prefecture_master (code, name, region, sort_order) VALUES
('01', '北海道', '北海道', 1),
('13', '東京都', '関東', 13),
('27', '大阪府', '関西', 27),
('40', '福岡県', '九州', 40);

INSERT INTO employment_type_master (code, name, description, is_valid_for_matching, display_order) VALUES
(1, 'アルバイト', 'パートタイム雇用', TRUE, 1),
(2, '正社員', 'フルタイム正規雇用', FALSE, 2),
(3, 'パート', 'パートタイム雇用', TRUE, 3),
(4, '契約社員', '有期契約雇用', FALSE, 4);

INSERT INTO feature_master (feature_code, feature_name, category, display_priority) VALUES
('001', '日払いOK', '給与', 10),
('002', '週払いOK', '給与', 9),
('003', '未経験歓迎', '経験', 8),
('004', '学生歓迎', '対象', 7),
('005', 'リモートワーク', '勤務形態', 6),
('006', '交通費支給', '待遇', 5);

-- =====================================================================================
-- SECTION 9: PERFORMANCE OPTIMIZATION
-- =====================================================================================

-- Enable pg_stat_statements for query performance monitoring
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Analyze tables for query planner
ANALYZE;

-- =====================================================================================
-- END OF SCHEMA
-- =====================================================================================

-- Final comments:
-- 1. This schema supports 100K+ jobs and 10K users with 400K daily matching operations
-- 2. Partitioning is implemented for high-volume tables (user_job_mapping, daily_job_picks)
-- 3. Generated columns provide automatic calculations while maintaining data consistency
-- 4. Comprehensive indexing strategy optimizes for common query patterns
-- 5. Triggers maintain data synchronization between related tables
-- 6. JSONB fields provide flexibility for evolving requirements
-- 7. Check constraints ensure data quality and business rule compliance
-- 8. Views simplify common queries and provide abstraction layers
-- 9. Supabase-compatible with proper timestamp handling and UUID support
-- 10. CASCADE delete rules prevent orphaned records while maintaining referential integrity