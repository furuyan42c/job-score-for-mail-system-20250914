-- ============================================================================
-- Supabase Migration: Job Matching System Schema
-- Migration: 20250917000001_job_matching_schema.sql
-- Source: backend/migrations/001_initial_schema.sql
-- Description: Complete job matching system with 20 tables
-- ============================================================================

-- ============================================================================
-- SECTION 1: MASTER DATA TABLES (5 tables)
-- ============================================================================

-- 1.1 prefecture_master: 都道府県マスター
CREATE TABLE IF NOT EXISTS prefecture_master (
    code CHAR(2) PRIMARY KEY,
    name VARCHAR(10) NOT NULL,
    region VARCHAR(20),
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE prefecture_master IS '都道府県マスターデータ';
COMMENT ON COLUMN prefecture_master.code IS '都道府県コード（JIS X 0401準拠）';

-- 1.2 city_master: 市区町村マスター
CREATE TABLE IF NOT EXISTS city_master (
    code VARCHAR(5) PRIMARY KEY,
    pref_cd CHAR(2) NOT NULL REFERENCES prefecture_master(code),
    name VARCHAR(50) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    nearby_city_codes VARCHAR(5)[],
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cities_prefecture ON city_master(pref_cd);
CREATE INDEX idx_cities_location ON city_master(latitude, longitude) WHERE latitude IS NOT NULL;

-- 1.3 occupation_master: 職種マスター
CREATE TABLE IF NOT EXISTS occupation_master (
    code INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    major_category_code INTEGER,
    major_category_name VARCHAR(100),
    minor_category_code INTEGER,
    minor_category_name VARCHAR(100),
    description TEXT,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_occupation_category ON occupation_master(major_category_code, minor_category_code);
CREATE INDEX idx_occupation_active ON occupation_master(is_active, display_order);

-- 1.4 employment_type_master: 雇用形態マスター
CREATE TABLE IF NOT EXISTS employment_type_master (
    code INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    is_valid_for_matching BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.5 feature_master: 特徴マスター
CREATE TABLE IF NOT EXISTS feature_master (
    feature_code VARCHAR(3) PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    display_priority INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feature_category ON feature_master(category, display_priority);

-- ============================================================================
-- SECTION 2: CORE DATA TABLES (3 tables)
-- ============================================================================

-- 2.1 job_data: 求人データ（メインテーブル）
CREATE TABLE IF NOT EXISTS job_data (
    job_id BIGSERIAL PRIMARY KEY,
    endcl_cd VARCHAR(20) NOT NULL,
    fee INTEGER,
    hourly_wage INTEGER,
    application_name VARCHAR(200),
    employment_type_code INTEGER REFERENCES employment_type_master(code),
    prefecture_cd CHAR(2) REFERENCES prefecture_master(code),
    city_cd VARCHAR(5) REFERENCES city_master(code),
    occupation_code INTEGER REFERENCES occupation_master(code),
    work_place VARCHAR(500),
    work_content TEXT,
    qualifications TEXT,
    benefits TEXT,
    work_hours VARCHAR(200),
    work_period VARCHAR(200),
    holiday VARCHAR(200),
    features VARCHAR(3)[],
    application_url TEXT,
    application_tel VARCHAR(20),
    application_email VARCHAR(100),
    company_name VARCHAR(200),
    recruiter_name VARCHAR(100),
    recruiter_tel VARCHAR(20),
    recruiter_email VARCHAR(100),
    import_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- job_data indexes
CREATE INDEX idx_job_endcl_cd ON job_data(endcl_cd);
CREATE INDEX idx_job_location ON job_data(prefecture_cd, city_cd);
CREATE INDEX idx_job_occupation ON job_data(occupation_code);
CREATE INDEX idx_job_employment_type ON job_data(employment_type_code);
CREATE INDEX idx_job_fee ON job_data(fee) WHERE fee IS NOT NULL;
CREATE INDEX idx_job_hourly_wage ON job_data(hourly_wage) WHERE hourly_wage IS NOT NULL;
CREATE INDEX idx_job_import_date ON job_data(import_date);
CREATE INDEX idx_job_features ON job_data USING GIN(features);

-- 2.2 user_actions: ユーザー行動履歴
CREATE TABLE IF NOT EXISTS user_actions (
    action_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    job_id BIGINT REFERENCES job_data(job_id),
    endcl_cd VARCHAR(20),
    action_type VARCHAR(20) NOT NULL,
    action_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    device_type VARCHAR(20),
    user_agent TEXT,
    ip_address INET,
    referrer TEXT,
    additional_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- user_actions indexes
CREATE INDEX idx_user_actions_user_id ON user_actions(user_id);
CREATE INDEX idx_user_actions_job_id ON user_actions(job_id);
CREATE INDEX idx_user_actions_endcl_cd ON user_actions(endcl_cd);
CREATE INDEX idx_user_actions_timestamp ON user_actions(action_timestamp);
CREATE INDEX idx_user_actions_type ON user_actions(action_type);
CREATE INDEX idx_user_actions_session ON user_actions(session_id);

-- 2.3 matching_results: マッチング結果
CREATE TABLE IF NOT EXISTS matching_results (
    matching_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    job_id BIGINT REFERENCES job_data(job_id),
    endcl_cd VARCHAR(20),
    section_type VARCHAR(20) NOT NULL,
    total_score DECIMAL(10,4),
    basic_score DECIMAL(10,4),
    seo_score DECIMAL(10,4),
    personalized_score DECIMAL(10,4),
    final_rank INTEGER,
    section_rank INTEGER,
    matching_date DATE DEFAULT CURRENT_DATE,
    batch_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- matching_results indexes
CREATE INDEX idx_matching_user_id ON matching_results(user_id);
CREATE INDEX idx_matching_job_id ON matching_results(job_id);
CREATE INDEX idx_matching_section ON matching_results(section_type);
CREATE INDEX idx_matching_date ON matching_results(matching_date);
CREATE INDEX idx_matching_batch ON matching_results(batch_id);
CREATE INDEX idx_matching_scores ON matching_results(total_score DESC, final_rank);

-- ============================================================================
-- SECTION 3: SCORING TABLES (4 tables)
-- ============================================================================

-- 3.1 basic_scoring: 基礎スコア
CREATE TABLE IF NOT EXISTS basic_scoring (
    scoring_id BIGSERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES job_data(job_id),
    endcl_cd VARCHAR(20),
    fee_score DECIMAL(6,4),
    hourly_wage_score DECIMAL(6,4),
    company_popularity_score DECIMAL(6,4),
    total_basic_score DECIMAL(6,4),
    calculation_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_basic_scoring_job_id ON basic_scoring(job_id);
CREATE INDEX idx_basic_scoring_date ON basic_scoring(calculation_date);
CREATE INDEX idx_basic_scoring_total ON basic_scoring(total_basic_score DESC);

-- 3.2 seo_scoring: SEOスコア
CREATE TABLE IF NOT EXISTS seo_scoring (
    scoring_id BIGSERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES job_data(job_id),
    endcl_cd VARCHAR(20),
    matched_keywords TEXT[],
    search_volume_total INTEGER,
    seo_score DECIMAL(6,4),
    calculation_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_seo_scoring_job_id ON seo_scoring(job_id);
CREATE INDEX idx_seo_scoring_date ON seo_scoring(calculation_date);
CREATE INDEX idx_seo_scoring_score ON seo_scoring(seo_score DESC);

-- 3.3 personalized_scoring: パーソナライズスコア
CREATE TABLE IF NOT EXISTS personalized_scoring (
    scoring_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    job_id BIGINT REFERENCES job_data(job_id),
    endcl_cd VARCHAR(20),
    personalized_score DECIMAL(6,4),
    calculation_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_personalized_scoring_user_id ON personalized_scoring(user_id);
CREATE INDEX idx_personalized_scoring_job_id ON personalized_scoring(job_id);
CREATE INDEX idx_personalized_scoring_date ON personalized_scoring(calculation_date);

-- 3.4 keyword_scoring: キーワードスコア詳細
CREATE TABLE IF NOT EXISTS keyword_scoring (
    scoring_id BIGSERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES job_data(job_id),
    endcl_cd VARCHAR(20),
    keyword VARCHAR(200) NOT NULL,
    field_name VARCHAR(50),
    search_volume INTEGER,
    weight_factor DECIMAL(4,2),
    score_contribution DECIMAL(8,4),
    calculation_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_keyword_scoring_job_id ON keyword_scoring(job_id);
CREATE INDEX idx_keyword_scoring_keyword ON keyword_scoring(keyword);
CREATE INDEX idx_keyword_scoring_date ON keyword_scoring(calculation_date);

-- ============================================================================
-- SECTION 4: BATCH PROCESSING TABLES (2 tables)
-- ============================================================================

-- 4.1 batch_jobs: バッチジョブ管理
CREATE TABLE IF NOT EXISTS batch_jobs (
    batch_id VARCHAR(50) PRIMARY KEY,
    batch_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    success_records INTEGER DEFAULT 0,
    error_records INTEGER DEFAULT 0,
    error_details JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_batch_jobs_type ON batch_jobs(batch_type);
CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX idx_batch_jobs_start_time ON batch_jobs(start_time);

-- 4.2 processing_logs: 処理ログ
CREATE TABLE IF NOT EXISTS processing_logs (
    log_id BIGSERIAL PRIMARY KEY,
    batch_id VARCHAR(50) REFERENCES batch_jobs(batch_id),
    process_type VARCHAR(30),
    entity_id VARCHAR(50),
    status VARCHAR(20),
    processing_time_ms INTEGER,
    error_message TEXT,
    additional_info JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_processing_logs_batch_id ON processing_logs(batch_id);
CREATE INDEX idx_processing_logs_type ON processing_logs(process_type);
CREATE INDEX idx_processing_logs_status ON processing_logs(status);

-- ============================================================================
-- SECTION 5: EMAIL SYSTEM TABLES (3 tables)
-- ============================================================================

-- 5.1 email_sections: メールセクション定義
CREATE TABLE IF NOT EXISTS email_sections (
    section_id INTEGER PRIMARY KEY,
    section_name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    job_count INTEGER DEFAULT 5,
    selection_logic TEXT,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5.2 section_jobs: セクション別求人配置
CREATE TABLE IF NOT EXISTS section_jobs (
    placement_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    section_id INTEGER REFERENCES email_sections(section_id),
    job_id BIGINT REFERENCES job_data(job_id),
    endcl_cd VARCHAR(20),
    placement_rank INTEGER,
    total_score DECIMAL(10,4),
    placement_date DATE DEFAULT CURRENT_DATE,
    batch_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_section_jobs_user_id ON section_jobs(user_id);
CREATE INDEX idx_section_jobs_section_id ON section_jobs(section_id);
CREATE INDEX idx_section_jobs_date ON section_jobs(placement_date);

-- 5.3 email_generation_logs: メール生成ログ
CREATE TABLE IF NOT EXISTS email_generation_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    email_type VARCHAR(30),
    generation_status VARCHAR(20),
    subject_line TEXT,
    content_preview TEXT,
    generation_time_ms INTEGER,
    error_message TEXT,
    batch_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_email_generation_user_id ON email_generation_logs(user_id);
CREATE INDEX idx_email_generation_batch_id ON email_generation_logs(batch_id);

-- ============================================================================
-- SECTION 6: STATISTICS & MONITORING TABLES (3 tables)
-- ============================================================================

-- 6.1 user_statistics: ユーザー統計
CREATE TABLE IF NOT EXISTS user_statistics (
    stat_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    stat_date DATE DEFAULT CURRENT_DATE,
    total_applications INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    unique_companies_applied INTEGER DEFAULT 0,
    avg_hourly_wage_applied DECIMAL(8,2),
    preferred_occupation_codes INTEGER[],
    preferred_prefecture_codes CHAR(2)[],
    last_activity_date DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_statistics_user_id ON user_statistics(user_id);
CREATE INDEX idx_user_statistics_date ON user_statistics(stat_date);

-- 6.2 semrush_keywords: SEMrushキーワードデータ
CREATE TABLE IF NOT EXISTS semrush_keywords (
    keyword_id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(200) NOT NULL,
    search_volume INTEGER,
    keyword_difficulty DECIMAL(4,2),
    cpc DECIMAL(6,2),
    competition_level VARCHAR(20),
    related_keywords TEXT[],
    import_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_semrush_keywords_keyword ON semrush_keywords(keyword);
CREATE INDEX idx_semrush_keywords_volume ON semrush_keywords(search_volume DESC);
CREATE INDEX idx_semrush_keywords_import_date ON semrush_keywords(import_date);

-- 6.3 system_metrics: システムメトリクス
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(20),
    measurement_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    additional_tags JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_time ON system_metrics(measurement_time);

-- ============================================================================
-- TRIGGERS & FUNCTIONS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to tables with updated_at column
CREATE TRIGGER update_prefecture_master_updated_at BEFORE UPDATE ON prefecture_master FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_city_master_updated_at BEFORE UPDATE ON city_master FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_occupation_master_updated_at BEFORE UPDATE ON occupation_master FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_employment_type_master_updated_at BEFORE UPDATE ON employment_type_master FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feature_master_updated_at BEFORE UPDATE ON feature_master FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_job_data_updated_at BEFORE UPDATE ON job_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_sections_updated_at BEFORE UPDATE ON email_sections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_statistics_updated_at BEFORE UPDATE ON user_statistics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_batch_jobs_updated_at BEFORE UPDATE ON batch_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MIGRATION COMPLETE: 20 Tables Created
-- ============================================================================
-- Master Tables: 5 (prefecture_master, city_master, occupation_master, employment_type_master, feature_master)
-- Core Tables: 3 (job_data, user_actions, matching_results)
-- Scoring Tables: 4 (basic_scoring, seo_scoring, personalized_scoring, keyword_scoring)
-- Batch Tables: 2 (batch_jobs, processing_logs)
-- Email Tables: 3 (email_sections, section_jobs, email_generation_logs)
-- Statistics Tables: 3 (user_statistics, semrush_keywords, system_metrics)
-- Total: 20 Tables + Indexes + Triggers + Functions
-- ============================================================================