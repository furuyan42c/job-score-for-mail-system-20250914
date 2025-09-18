-- T021: 基礎スコア計算用テーブル作成
-- 作成日: 2025-09-18
-- 目的: エリア統計、企業人気度、ユーザーアクション追跡のためのテーブル

-- 1. エリア給与統計テーブル
CREATE TABLE IF NOT EXISTS area_salary_stats (
    id SERIAL PRIMARY KEY,
    prefecture_code VARCHAR(3) NOT NULL,
    city_code VARCHAR(10),
    avg_salary DECIMAL(10,2) NOT NULL,
    std_salary DECIMAL(10,2) NOT NULL,
    job_count INTEGER NOT NULL,
    salary_type VARCHAR(20) DEFAULT 'hourly',
    employment_type_filter VARCHAR(50) DEFAULT '1,3,6,8',
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prefecture_code, city_code, salary_type)
);

-- インデックス作成
CREATE INDEX idx_area_salary_stats_location
    ON area_salary_stats(prefecture_code, city_code);

CREATE INDEX idx_area_salary_stats_updated
    ON area_salary_stats(updated_at DESC);

-- 2. ユーザーアクション履歴テーブル（360日データ保持用）
CREATE TABLE IF NOT EXISTS user_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    job_id INTEGER,
    endcl_cd VARCHAR(50),
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('view', 'apply', 'application', 'click', 'favorite')),
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    device_type VARCHAR(20),
    referrer VARCHAR(200),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成（高速検索用）
CREATE INDEX idx_user_actions_endcl_timestamp
    ON user_actions(endcl_cd, action_timestamp DESC);

CREATE INDEX idx_user_actions_user_timestamp
    ON user_actions(user_id, action_timestamp DESC);

CREATE INDEX idx_user_actions_type_timestamp
    ON user_actions(action_type, action_timestamp DESC);

CREATE INDEX idx_user_actions_job_id
    ON user_actions(job_id) WHERE job_id IS NOT NULL;

-- パーティショニング用のインデックス（大規模データ対応）
CREATE INDEX idx_user_actions_timestamp_partition
    ON user_actions(action_timestamp)
    WHERE action_timestamp > CURRENT_DATE - INTERVAL '365 days';

-- 3. 企業人気度キャッシュテーブル
CREATE TABLE IF NOT EXISTS company_popularity_cache (
    endcl_cd VARCHAR(50) PRIMARY KEY,
    views_360d INTEGER DEFAULT 0,
    applications_360d INTEGER DEFAULT 0,
    applications_7d INTEGER DEFAULT 0,
    applications_30d INTEGER DEFAULT 0,
    application_rate_360d DECIMAL(5,4) DEFAULT 0,
    application_rate_30d DECIMAL(5,4) DEFAULT 0,
    popularity_score DECIMAL(5,2) DEFAULT 0,
    rank_in_prefecture INTEGER,
    rank_overall INTEGER,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_company_popularity_score
    ON company_popularity_cache(popularity_score DESC);

CREATE INDEX idx_company_popularity_updated
    ON company_popularity_cache(updated_at DESC);

CREATE INDEX idx_company_popularity_ranks
    ON company_popularity_cache(rank_overall, rank_in_prefecture);

-- 4. 求人フィー統計テーブル（fee分析用）
CREATE TABLE IF NOT EXISTS job_fee_stats (
    id SERIAL PRIMARY KEY,
    prefecture_code VARCHAR(3),
    city_code VARCHAR(10),
    occupation_cd1 INTEGER,
    occupation_cd2 INTEGER,
    avg_fee DECIMAL(10,2) NOT NULL,
    median_fee DECIMAL(10,2) NOT NULL,
    min_fee DECIMAL(10,2) NOT NULL,
    max_fee DECIMAL(10,2) NOT NULL,
    std_fee DECIMAL(10,2),
    job_count INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prefecture_code, city_code, occupation_cd1, occupation_cd2)
);

-- インデックス作成
CREATE INDEX idx_job_fee_stats_location
    ON job_fee_stats(prefecture_code, city_code);

CREATE INDEX idx_job_fee_stats_occupation
    ON job_fee_stats(occupation_cd1, occupation_cd2);

-- 5. スコアリング実行ログテーブル（監視・デバッグ用）
CREATE TABLE IF NOT EXISTS scoring_execution_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    job_id INTEGER,
    scoring_version VARCHAR(10) DEFAULT 'T021',
    basic_score DECIMAL(5,2),
    location_score DECIMAL(5,2),
    category_score DECIMAL(5,2),
    salary_score DECIMAL(5,2),
    feature_score DECIMAL(5,2),
    preference_score DECIMAL(5,2),
    popularity_score DECIMAL(5,2),
    composite_score DECIMAL(5,2),
    execution_time_ms INTEGER,
    used_cache BOOLEAN DEFAULT FALSE,
    fallback_used BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_scoring_log_user_job
    ON scoring_execution_log(user_id, job_id);

CREATE INDEX idx_scoring_log_created
    ON scoring_execution_log(created_at DESC);

CREATE INDEX idx_scoring_log_version
    ON scoring_execution_log(scoring_version);

-- 6. データ初期化関数

-- エリア統計を計算して挿入する関数
CREATE OR REPLACE FUNCTION populate_area_salary_stats()
RETURNS void AS $$
BEGIN
    INSERT INTO area_salary_stats (
        prefecture_code,
        city_code,
        avg_salary,
        std_salary,
        job_count,
        salary_type
    )
    SELECT
        jl.prefecture_code,
        jl.city_code,
        AVG(CASE
            WHEN j.salary_type = 'hourly' THEN (j.min_salary + j.max_salary) / 2
            WHEN j.salary_type = 'daily' THEN (j.min_salary + j.max_salary) / 2 / 8
            WHEN j.salary_type = 'monthly' THEN (j.min_salary + j.max_salary) / 2 / 160
            ELSE (j.min_salary + j.max_salary) / 2
        END) as avg_salary,
        STDDEV(CASE
            WHEN j.salary_type = 'hourly' THEN (j.min_salary + j.max_salary) / 2
            WHEN j.salary_type = 'daily' THEN (j.min_salary + j.max_salary) / 2 / 8
            WHEN j.salary_type = 'monthly' THEN (j.min_salary + j.max_salary) / 2 / 160
            ELSE (j.min_salary + j.max_salary) / 2
        END) as std_salary,
        COUNT(*) as job_count,
        'hourly' as salary_type
    FROM jobs j
    JOIN job_locations jl ON j.job_id = jl.job_id
    WHERE j.min_salary > 0
        AND j.max_salary > 0
        AND j.employment_type_cd IN (1, 3, 6, 8)
        AND j.is_active = true
    GROUP BY jl.prefecture_code, jl.city_code
    ON CONFLICT (prefecture_code, city_code, salary_type)
    DO UPDATE SET
        avg_salary = EXCLUDED.avg_salary,
        std_salary = EXCLUDED.std_salary,
        job_count = EXCLUDED.job_count,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- 企業人気度を計算して挿入する関数
CREATE OR REPLACE FUNCTION populate_company_popularity_cache()
RETURNS void AS $$
BEGIN
    INSERT INTO company_popularity_cache (
        endcl_cd,
        views_360d,
        applications_360d,
        applications_7d,
        applications_30d,
        application_rate_360d,
        application_rate_30d,
        popularity_score
    )
    SELECT
        endcl_cd,
        COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END) as views_360d,
        COUNT(DISTINCT CASE WHEN action_type IN ('apply', 'application') THEN user_id END) as applications_360d,
        COUNT(DISTINCT CASE
            WHEN action_type IN ('apply', 'application')
            AND action_timestamp > CURRENT_DATE - INTERVAL '7 days'
            THEN user_id
        END) as applications_7d,
        COUNT(DISTINCT CASE
            WHEN action_type IN ('apply', 'application')
            AND action_timestamp > CURRENT_DATE - INTERVAL '30 days'
            THEN user_id
        END) as applications_30d,
        CASE
            WHEN COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END) > 0
            THEN COUNT(DISTINCT CASE WHEN action_type IN ('apply', 'application') THEN user_id END)::decimal /
                 COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END)
            ELSE 0
        END as application_rate_360d,
        CASE
            WHEN COUNT(DISTINCT CASE
                    WHEN action_type = 'view'
                    AND action_timestamp > CURRENT_DATE - INTERVAL '30 days'
                    THEN user_id
                END) > 0
            THEN COUNT(DISTINCT CASE
                    WHEN action_type IN ('apply', 'application')
                    AND action_timestamp > CURRENT_DATE - INTERVAL '30 days'
                    THEN user_id
                END)::decimal /
                 COUNT(DISTINCT CASE
                    WHEN action_type = 'view'
                    AND action_timestamp > CURRENT_DATE - INTERVAL '30 days'
                    THEN user_id
                END)
            ELSE 0
        END as application_rate_30d,
        -- 人気度スコア計算（応募率ベース）
        CASE
            WHEN COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END) > 0
            THEN LEAST(100,
                (COUNT(DISTINCT CASE WHEN action_type IN ('apply', 'application') THEN user_id END)::decimal /
                 COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END)) * 100 * 6.67
            )
            ELSE 30
        END as popularity_score
    FROM user_actions
    WHERE action_timestamp > CURRENT_DATE - INTERVAL '360 days'
        AND endcl_cd IS NOT NULL
    GROUP BY endcl_cd
    ON CONFLICT (endcl_cd)
    DO UPDATE SET
        views_360d = EXCLUDED.views_360d,
        applications_360d = EXCLUDED.applications_360d,
        applications_7d = EXCLUDED.applications_7d,
        applications_30d = EXCLUDED.applications_30d,
        application_rate_360d = EXCLUDED.application_rate_360d,
        application_rate_30d = EXCLUDED.application_rate_30d,
        popularity_score = EXCLUDED.popularity_score,
        updated_at = CURRENT_TIMESTAMP;

    -- ランキング更新
    WITH ranked AS (
        SELECT
            endcl_cd,
            ROW_NUMBER() OVER (ORDER BY popularity_score DESC) as overall_rank
        FROM company_popularity_cache
    )
    UPDATE company_popularity_cache c
    SET rank_overall = r.overall_rank
    FROM ranked r
    WHERE c.endcl_cd = r.endcl_cd;
END;
$$ LANGUAGE plpgsql;

-- 7. 定期更新用のトリガー関数
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- トリガー作成
CREATE TRIGGER update_area_salary_stats_timestamp
    BEFORE UPDATE ON area_salary_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_company_popularity_timestamp
    BEFORE UPDATE ON company_popularity_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- 8. データクリーンアップ関数（古いデータ削除）
CREATE OR REPLACE FUNCTION cleanup_old_user_actions()
RETURNS void AS $$
BEGIN
    -- 365日より古いデータを削除
    DELETE FROM user_actions
    WHERE action_timestamp < CURRENT_DATE - INTERVAL '365 days';

    -- ログテーブルの古いデータも削除（30日保持）
    DELETE FROM scoring_execution_log
    WHERE created_at < CURRENT_DATE - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- 9. 初期データ投入の実行
-- 注意: 本番環境では実行時間がかかる可能性があります

-- エリア統計の初期計算
-- SELECT populate_area_salary_stats();

-- 企業人気度の初期計算
-- SELECT populate_company_popularity_cache();

-- 10. 定期実行用のコメント（cronジョブなどで使用）
-- 毎日深夜に実行することを推奨
-- 0 2 * * * psql -d your_database -c "SELECT populate_area_salary_stats(); SELECT populate_company_popularity_cache(); SELECT cleanup_old_user_actions();"