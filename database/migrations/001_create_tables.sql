-- ============================================================================
-- バイト求人マッチングシステム データベース定義
-- Version: 1.1.0
-- Database: PostgreSQL 15 (Supabase)
-- Created: 2025-09-18
-- ============================================================================

-- ============================================================================
-- SECTION 1: MASTER DATA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1.1 prefecture_master: 都道府県マスター
-- ----------------------------------------------------------------------------
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
COMMENT ON COLUMN prefecture_master.region IS '地方区分（関東、関西など）';

-- ----------------------------------------------------------------------------
-- 1.2 city_master: 市区町村マスター
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS city_master (
    code VARCHAR(5) PRIMARY KEY,
    pref_cd CHAR(2) NOT NULL REFERENCES prefecture_master(code),
    name VARCHAR(50) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    nearby_city_codes VARCHAR(5)[], -- 隣接市区町村
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cities_prefecture ON city_master(pref_cd);
CREATE INDEX idx_cities_location ON city_master(latitude, longitude) WHERE latitude IS NOT NULL;

COMMENT ON TABLE city_master IS '市区町村マスターデータ';
COMMENT ON COLUMN city_master.nearby_city_codes IS '隣接市区町村コードの配列';

-- ----------------------------------------------------------------------------
-- 1.3 occupation_master: 職種マスター
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE occupation_master IS '職種マスター（大分類・中分類含む）';

-- ----------------------------------------------------------------------------
-- 1.4 employment_type_master: 雇用形態マスター
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employment_type_master (
    code INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    is_valid_for_matching BOOLEAN DEFAULT FALSE, -- マッチング対象（アルバイト・パート）
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE employment_type_master IS '雇用形態マスター';
COMMENT ON COLUMN employment_type_master.is_valid_for_matching IS 'マッチング対象フラグ（1:アルバイト、3:パートのみtrue）';

-- ----------------------------------------------------------------------------
-- 1.5 feature_master: 特徴マスター
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE feature_master IS '求人特徴マスター（日払い、高時給など）';

-- ----------------------------------------------------------------------------
-- 1.6 semrush_keywords: SEOキーワードマスター
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS semrush_keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL UNIQUE,
    search_volume INTEGER,
    difficulty FLOAT,
    cpc DECIMAL(10, 2),
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_keywords_volume ON semrush_keywords(search_volume DESC);
CREATE INDEX idx_keywords_category ON semrush_keywords(category);

COMMENT ON TABLE semrush_keywords IS 'SEOキーワードマスター（SEMrushデータ）';

-- ============================================================================
-- SECTION 2: CORE ENTITIES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 jobs: 求人情報テーブル（10万件規模）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    job_id BIGSERIAL PRIMARY KEY,
    endcl_cd VARCHAR(20) NOT NULL,  -- エンドクライアント（企業）コード
    company_name VARCHAR(255) NOT NULL,
    application_id VARCHAR(100) UNIQUE,
    application_name TEXT NOT NULL,

    -- 場所情報
    pref_cd CHAR(2) REFERENCES prefecture_master(code),
    city_cd VARCHAR(5) REFERENCES city_master(code),
    station_name_eki VARCHAR(100),
    address VARCHAR(500),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),

    -- 給与情報
    salary_type VARCHAR(20) CHECK (salary_type IN ('hourly', 'daily', 'monthly')),
    min_salary INTEGER CHECK (min_salary >= 0),
    max_salary INTEGER CHECK (max_salary >= min_salary),
    fee INTEGER CHECK (fee >= 0 AND fee <= 5000),  -- 応募促進費用

    -- 勤務条件
    hours TEXT,
    work_days VARCHAR(200),
    shift_flexibility VARCHAR(100),

    -- カテゴリ
    occupation_cd1 INTEGER,  -- 大分類
    occupation_cd2 INTEGER,  -- 中分類
    employment_type_cd INTEGER REFERENCES employment_type_master(code),

    -- 特徴（カンマ区切りから配列型へ）
    feature_codes VARCHAR(3)[] DEFAULT '{}',

    -- 特徴フラグ（feature_codesから派生）
    has_daily_payment BOOLEAN GENERATED ALWAYS AS (
        'D01' = ANY(feature_codes)
    ) STORED,
    has_weekly_payment BOOLEAN GENERATED ALWAYS AS (
        'W01' = ANY(feature_codes)
    ) STORED,
    has_no_experience BOOLEAN GENERATED ALWAYS AS (
        'N01' = ANY(feature_codes)
    ) STORED,
    has_student_welcome BOOLEAN GENERATED ALWAYS AS (
        'S01' = ANY(feature_codes)
    ) STORED,
    has_remote_work BOOLEAN GENERATED ALWAYS AS (
        'R01' = ANY(feature_codes)
    ) STORED,
    has_transportation BOOLEAN GENERATED ALWAYS AS (
        'T01' = ANY(feature_codes)
    ) STORED,
    has_high_income BOOLEAN GENERATED ALWAYS AS (
        CASE
            WHEN salary_type = 'hourly' THEN min_salary >= 1500
            WHEN salary_type = 'daily' THEN min_salary >= 12000
            ELSE FALSE
        END
    ) STORED,

    -- SEO関連
    search_keywords TEXT[],
    description TEXT,
    benefits TEXT,

    -- メタデータ
    posting_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_at TIMESTAMPTZ,  -- 掲載終了日（v5.1準拠）
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- 制約
    CONSTRAINT check_salary_range CHECK (
        (min_salary IS NULL AND max_salary IS NULL) OR
        (min_salary IS NOT NULL AND max_salary IS NOT NULL)
    ),
    CONSTRAINT check_fee_required CHECK (fee > 500)
);

-- インデックス
CREATE INDEX idx_jobs_location ON jobs(pref_cd, city_cd, is_active);
CREATE INDEX idx_jobs_category ON jobs(occupation_cd1, employment_type_cd, is_active);
CREATE INDEX idx_jobs_active_date ON jobs(is_active, posting_date DESC);
CREATE INDEX idx_jobs_endcl ON jobs(endcl_cd, posting_date DESC);
CREATE INDEX idx_jobs_fee ON jobs(fee DESC) WHERE is_active = TRUE;
CREATE INDEX idx_jobs_high_income ON jobs(has_high_income) WHERE has_high_income = TRUE;
CREATE INDEX idx_jobs_features ON jobs USING GIN(feature_codes);

COMMENT ON TABLE jobs IS '求人情報マスター（10万件規模、100+フィールド）';
COMMENT ON COLUMN jobs.fee IS '応募促進費用（500円以上必須）';
COMMENT ON COLUMN jobs.end_at IS '掲載終了日（v5.1仕様準拠）';

-- ----------------------------------------------------------------------------
-- 2.2 users: ユーザー情報テーブル（1万人規模）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_hash VARCHAR(256) GENERATED ALWAYS AS (
        encode(sha256(email::bytea), 'hex')
    ) STORED,

    -- 基本情報
    age_group VARCHAR(20),  -- '10代', '20代前半', '20代後半', etc.
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other', NULL)),

    -- 居住地（応募履歴から推定）
    estimated_pref_cd CHAR(2) REFERENCES prefecture_master(code),
    estimated_city_cd VARCHAR(5) REFERENCES city_master(code),

    -- 希望条件
    preferred_work_styles VARCHAR(50)[] DEFAULT '{}',
    preferred_categories INTEGER[] DEFAULT '{}',  -- occupation_codes
    preferred_salary_min INTEGER,

    -- ステータス
    registration_date DATE DEFAULT CURRENT_DATE,
    last_login_date TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    email_subscription BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_users_location ON users(estimated_pref_cd, estimated_city_cd);
CREATE INDEX idx_users_active ON users(is_active, email_subscription);
CREATE INDEX idx_users_last_active ON users(last_active_at DESC) WHERE is_active = TRUE;

COMMENT ON TABLE users IS 'ユーザーマスター（1万人規模）';
COMMENT ON COLUMN users.estimated_pref_cd IS '応募履歴から推定した居住都道府県';

-- ----------------------------------------------------------------------------
-- 2.3 user_actions: ユーザー行動履歴
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_actions (
    action_id BIGSERIAL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT REFERENCES jobs(job_id) ON DELETE CASCADE,
    endcl_cd VARCHAR(20),  -- 非正規化（パフォーマンス向上）

    action_type VARCHAR(50) NOT NULL CHECK (
        action_type IN ('view', 'click', 'apply', 'application', 'email_open', 'favorite', 'save', 'share', 'email_click')
    ),
    action_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- コンテキスト情報
    source VARCHAR(50),  -- 'email', 'web', 'app'
    session_id VARCHAR(100),
    device_type VARCHAR(20),

    -- 追加データ
    action_metadata JSONB DEFAULT '{}',

    -- パーティションキーを含む複合PRIMARY KEY
    PRIMARY KEY (action_id, action_timestamp)
) PARTITION BY RANGE (action_timestamp);  -- 月単位パーティション

-- インデックス（パーティションテーブル用）
CREATE INDEX idx_actions_user ON user_actions(user_id, action_timestamp DESC);
CREATE INDEX idx_actions_job ON user_actions(job_id, action_type);
CREATE INDEX idx_actions_endcl ON user_actions(endcl_cd, action_type, action_timestamp DESC);

-- 初期パーティション作成（例：2025年9月）
CREATE TABLE user_actions_2025_09 PARTITION OF user_actions
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

COMMENT ON TABLE user_actions IS 'ユーザー行動履歴（パーティション化）';

-- ----------------------------------------------------------------------------
-- 2.4 user_profiles: ユーザープロファイル（集計データ）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- 応募傾向スコア
    preference_scores JSONB DEFAULT '{}',  -- {"hourly_work": 0.8, "remote": 0.6, ...}

    -- カテゴリ別関心度
    category_interests JSONB DEFAULT '{}',  -- {"100": 0.9, "200": 0.3, ...}

    -- 地域選好
    location_preference_radius INTEGER DEFAULT 10,  -- km
    preferred_areas VARCHAR(5)[] DEFAULT '{}',  -- city_codes

    -- 行動パターン
    avg_salary_preference INTEGER,
    application_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    last_application_date DATE,

    -- 協調フィルタリング用（implicit ALS）
    latent_factors FLOAT[] DEFAULT '{}',  -- 50次元ベクトル

    profile_updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_profiles_user ON user_profiles(user_id);
CREATE INDEX idx_profiles_updated ON user_profiles(profile_updated_at DESC);

COMMENT ON TABLE user_profiles IS 'ユーザープロファイル（集計・分析データ）';
COMMENT ON COLUMN user_profiles.latent_factors IS '協調フィルタリング用の潜在因子（50次元）';

-- ============================================================================
-- SECTION 3: PROCESSING ENTITIES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 company_popularity: 企業人気度
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_popularity (
    endcl_cd VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255),

    -- 集計データ
    total_views INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_applications INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,

    -- 期間別集計
    views_7d INTEGER DEFAULT 0,
    views_30d INTEGER DEFAULT 0,
    applications_7d INTEGER DEFAULT 0,
    applications_30d INTEGER DEFAULT 0,

    -- 計算値は後で個別に定義
    application_rate DECIMAL(5,4) DEFAULT 0,

    -- 人気度スコア（GENERATED COLUMNではなく通常のカラムとして定義）
    popularity_score DECIMAL(10,2) DEFAULT 0,

    -- タイムスタンプ
    last_calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_popularity_score ON company_popularity(popularity_score DESC);
CREATE INDEX idx_popularity_rate ON company_popularity(application_rate DESC);

COMMENT ON TABLE company_popularity IS '企業人気度（360日統計）';

-- ----------------------------------------------------------------------------
-- 3.2 job_enrichment: 求人拡張情報（スコアリング結果）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_enrichment (
    enrichment_id SERIAL PRIMARY KEY,
    job_id BIGINT UNIQUE NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- スコア（0-100）
    basic_score FLOAT CHECK (basic_score >= 0 AND basic_score <= 100),
    seo_score FLOAT CHECK (seo_score >= 0 AND seo_score <= 100),
    personalized_score_base FLOAT CHECK (personalized_score_base >= 0 AND personalized_score_base <= 100),

    -- 総合スコア（重み付け）
    composite_score FLOAT GENERATED ALWAYS AS (
        basic_score * 0.3 +
        seo_score * 0.2 +
        personalized_score_base * 0.5
    ) STORED,

    -- カテゴリ分類（14ニーズカテゴリ）
    needs_categories VARCHAR(30)[] DEFAULT '{}',  -- ['daily_payment', 'high_income', ...]
    occupation_categories INTEGER[] DEFAULT '{}',  -- occupation_codes

    -- 集計データ
    application_count_30d INTEGER DEFAULT 0,
    click_count_30d INTEGER DEFAULT 0,
    view_count_30d INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE
            WHEN click_count_30d > 0
            THEN LEAST(application_count_30d::DECIMAL / click_count_30d, 1.0)
            ELSE 0
        END
    ) STORED,

    -- キーワード分析
    extracted_keywords TEXT[] DEFAULT '{}',
    semrush_keyword_matches TEXT[] DEFAULT '{}',
    keyword_match_count INTEGER DEFAULT 0,

    calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_enrichment_job ON job_enrichment(job_id);
CREATE INDEX idx_enrichment_scores ON job_enrichment(composite_score DESC);
CREATE INDEX idx_enrichment_basic ON job_enrichment(basic_score DESC);
CREATE INDEX idx_enrichment_categories ON job_enrichment USING GIN(needs_categories);

COMMENT ON TABLE job_enrichment IS '求人拡張情報（スコアリング・分類結果）';

-- ----------------------------------------------------------------------------
-- 3.3 job_keywords: 求人-キーワード関連テーブル
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_keywords (
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    keyword_id INTEGER NOT NULL REFERENCES semrush_keywords(keyword_id) ON DELETE CASCADE,
    match_count INTEGER DEFAULT 1,
    match_locations TEXT[] DEFAULT '{}',  -- ['title', 'description', 'benefits']

    PRIMARY KEY (job_id, keyword_id)
);

CREATE INDEX idx_job_keywords_job ON job_keywords(job_id);
CREATE INDEX idx_job_keywords_keyword ON job_keywords(keyword_id);
CREATE INDEX idx_job_keywords_count ON job_keywords(match_count DESC);

COMMENT ON TABLE job_keywords IS '求人とSEOキーワードの関連';

-- ----------------------------------------------------------------------------
-- 3.4 user_job_mapping: マッチング結果（日次40万件規模）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_job_mapping (
    mapping_id BIGSERIAL,
    batch_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- スコアリング結果
    composite_score DECIMAL(5,2),
    rank_in_batch INTEGER,
    percentile DECIMAL(5,2),

    -- タイムスタンプ
    batch_date DATE NOT NULL DEFAULT CURRENT_DATE,
    calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- パーティションキーを含む複合PRIMARY KEY
    PRIMARY KEY (mapping_id, batch_date)
) PARTITION BY RANGE (batch_date);  -- 日次パーティション

-- インデックス
CREATE INDEX idx_map_batch ON user_job_mapping(batch_id, user_id);
CREATE INDEX idx_map_user_score ON user_job_mapping(user_id, composite_score DESC);
CREATE INDEX idx_map_job_score ON user_job_mapping(job_id, composite_score DESC);

-- 初期パーティション（例：2025年9月）
CREATE TABLE user_job_mapping_2025_09_18 PARTITION OF user_job_mapping
    FOR VALUES FROM ('2025-09-18') TO ('2025-09-19');

COMMENT ON TABLE user_job_mapping IS '日次マッチング結果（1万人×最大100件）';

-- ----------------------------------------------------------------------------
-- 3.5 daily_job_picks: 日次選定求人（6セクション×40件）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_job_picks (
    pick_id BIGSERIAL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- ピック情報
    composite_score DECIMAL(5,2),
    rank_number INTEGER,
    pick_reason VARCHAR(50),

    -- 送信状態
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMPTZ,

    -- タイムスタンプ
    pick_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- パーティションキーを含む複合PRIMARY KEY
    PRIMARY KEY (pick_id, pick_date),

    -- ユニーク制約
    UNIQUE (user_id, job_id, pick_date)
) PARTITION BY RANGE (pick_date);

-- インデックス
CREATE INDEX idx_pick_user_date ON daily_job_picks(user_id, pick_date DESC);
CREATE INDEX idx_pick_date_sent ON daily_job_picks(pick_date, is_sent);
CREATE INDEX idx_pick_score ON daily_job_picks(composite_score DESC);

-- 初期パーティション
CREATE TABLE daily_job_picks_2025_09_18 PARTITION OF daily_job_picks
    FOR VALUES FROM ('2025-09-18') TO ('2025-09-19');

COMMENT ON TABLE daily_job_picks IS '日次選定求人（1万人×40件）';
COMMENT ON COLUMN daily_job_picks.section IS '6セクション分類';

-- ----------------------------------------------------------------------------
-- 3.6 daily_email_queue: メール配信キュー
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_email_queue (
    queue_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- メール内容
    subject VARCHAR(500) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,

    -- 生成メタデータ
    generated_by VARCHAR(50) DEFAULT 'gpt-5-nano',  -- 生成エンジン
    generation_time_ms INTEGER,  -- 生成時間（ミリ秒）

    -- 配信情報
    scheduled_date DATE NOT NULL,
    scheduled_time TIME DEFAULT '06:00:00',

    -- ステータス
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'sent', 'failed', 'cancelled'
    )),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- トラッキング
    email_tracking_id VARCHAR(100),
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ユニーク制約とインデックス
CREATE UNIQUE INDEX idx_queue_unique ON daily_email_queue(user_id, scheduled_date);
CREATE INDEX idx_queue_status_date ON daily_email_queue(status, scheduled_date, scheduled_time);
CREATE INDEX idx_queue_sent ON daily_email_queue(sent_at DESC) WHERE status = 'sent';

COMMENT ON TABLE daily_email_queue IS 'メール配信キュー（1万通/日）';

-- ----------------------------------------------------------------------------
-- 3.7 batch_jobs: バッチジョブ管理
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS batch_jobs (
    batch_id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN (
        'data_import',        -- CSVインポート
        'scoring',           -- スコアリング処理
        'matching',          -- マッチング処理
        'email_generation',  -- メール生成
        'cleanup',           -- データクリーンアップ
        'analytics'          -- 分析処理
    )),

    -- 実行情報
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    execution_time_seconds INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
    ) STORED,

    -- ステータス
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    )),

    -- 進捗
    total_records INTEGER,
    processed_records INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- 詳細情報
    parameters JSONB DEFAULT '{}',
    error_logs JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}',  -- パフォーマンスメトリクス

    -- 監査
    initiated_by VARCHAR(100) DEFAULT 'system',
    notes TEXT
);

-- インデックス
CREATE INDEX idx_batch_status ON batch_jobs(status, started_at DESC);
CREATE INDEX idx_batch_type ON batch_jobs(job_type, started_at DESC);
CREATE INDEX idx_batch_completed ON batch_jobs(completed_at DESC) WHERE completed_at IS NOT NULL;

COMMENT ON TABLE batch_jobs IS 'バッチジョブ実行管理';

-- ============================================================================
-- SECTION 4: VIEWS FOR COMMON QUERIES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1 有効な求人ビュー
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW valid_jobs AS
SELECT
    j.job_id,
    j.endcl_cd,
    j.company_name,
    j.application_name,
    j.pref_cd,
    j.city_cd,
    j.min_salary,
    j.max_salary,
    COALESCE(cp.popularity_score, 0) as popularity_score
FROM jobs j
LEFT JOIN company_popularity cp ON j.endcl_cd = cp.endcl_cd
WHERE j.is_active = TRUE;

COMMENT ON VIEW valid_jobs IS 'マッチング対象の有効求人';

-- ----------------------------------------------------------------------------
-- 4.2 最近の応募企業ビュー（重複制御用）
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW recent_applications AS
SELECT DISTINCT
    user_id,
    endcl_cd,
    MAX(action_timestamp) as last_applied
FROM user_actions
WHERE action_type IN ('apply', 'application')
  AND action_timestamp > CURRENT_DATE - INTERVAL '14 days'
GROUP BY user_id, endcl_cd;

COMMENT ON VIEW recent_applications IS '2週間以内の応募企業（重複制御用）';

-- ----------------------------------------------------------------------------
-- 4.3 バッチパフォーマンスビュー
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW batch_performance AS
SELECT
    job_type,
    COUNT(*) as total_runs,
    AVG(execution_time_seconds) as avg_duration_seconds,
    MIN(execution_time_seconds) as min_duration_seconds,
    MAX(execution_time_seconds) as max_duration_seconds,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failure_count,
    ROUND(
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)::NUMERIC /
        COUNT(*)::NUMERIC * 100,
        2
    ) as success_rate,
    MAX(completed_at) as last_completed
FROM batch_jobs
WHERE started_at > CURRENT_DATE - INTERVAL '7 days'
GROUP BY job_type;

COMMENT ON VIEW batch_performance IS '過去7日間のバッチ処理パフォーマンス';

-- ============================================================================
-- SECTION 5: TRIGGERS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 5.1 自動タイムスタンプ更新トリガー
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 各テーブルにトリガーを設定
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prefecture_master_updated_at BEFORE UPDATE ON prefecture_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_city_master_updated_at BEFORE UPDATE ON city_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_occupation_master_updated_at BEFORE UPDATE ON occupation_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employment_type_master_updated_at BEFORE UPDATE ON employment_type_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_master_updated_at BEFORE UPDATE ON feature_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_semrush_keywords_updated_at BEFORE UPDATE ON semrush_keywords
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 5.2 ユーザープロファイル自動更新トリガー
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    -- user_profilesが存在しない場合は作成
    INSERT INTO user_profiles (user_id)
    VALUES (NEW.user_id)
    ON CONFLICT (user_id) DO NOTHING;

    -- 行動カウントを更新
    UPDATE user_profiles
    SET
        application_count = CASE WHEN NEW.action_type = 'application'
                                THEN application_count + 1
                                ELSE application_count END,
        click_count = CASE WHEN NEW.action_type = 'click'
                          THEN click_count + 1
                          ELSE click_count END,
        view_count = CASE WHEN NEW.action_type = 'view'
                         THEN view_count + 1
                         ELSE view_count END,
        last_application_date = CASE WHEN NEW.action_type = 'application'
                                    THEN CURRENT_DATE
                                    ELSE last_application_date END,
        profile_updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;

    -- ユーザーの最終アクティブ時刻を更新
    UPDATE users
    SET last_active_at = NEW.action_timestamp
    WHERE user_id = NEW.user_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_profile
AFTER INSERT ON user_actions
FOR EACH ROW EXECUTE FUNCTION update_user_profile();

-- ============================================================================
-- 終了メッセージ
-- ============================================================================
-- テーブル作成完了: 14個のコアテーブル、6個のマスターテーブル、3個のビュー
-- 次のステップ: 002_create_indexes.sql でパフォーマンス最適化用インデックスを作成