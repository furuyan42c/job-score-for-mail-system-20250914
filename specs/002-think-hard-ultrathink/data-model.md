# データモデル設計: バイト求人マッチングシステム

**作成日**: 2025-09-17
**関連仕様**: `/specs/002-think-hard-ultrathink/spec.md`
**ER図参照**: `/specs/001-job-matching-system/20250904_er_complete_v2.0.mmd`

## 概要

本データモデルは、10万件の求人と1万人のユーザーを効率的にマッチングするための構造を定義します。既存ER図を基に、パフォーマンスとスケーラビリティを考慮した設計となっています。

## コアエンティティ

### 1. jobs (求人情報)
```sql
CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    endcl_cd VARCHAR(50) NOT NULL,  -- 企業コード
    application_id VARCHAR(100) UNIQUE NOT NULL,
    application_name TEXT NOT NULL,
    employment_type_cd INTEGER NOT NULL,  -- 1=アルバイト, 3=パート
    occupation_cd INTEGER,  -- 職種コード
    min_salary INTEGER,
    max_salary INTEGER,
    fee INTEGER NOT NULL CHECK (fee > 500),  -- 応募単価報酬
    pref_cd INTEGER NOT NULL,  -- 都道府県コード
    city_cd INTEGER,  -- 市区町村コード
    station_cd INTEGER,  -- 最寄り駅
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',

    -- インデックス
    INDEX idx_jobs_endcl (endcl_cd, status, created_at),
    INDEX idx_jobs_location (pref_cd, city_cd),
    INDEX idx_jobs_fee (fee DESC),
    INDEX idx_jobs_created (created_at DESC)
);
```

### 2. users (ユーザー情報)
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email_hash VARCHAR(256) UNIQUE NOT NULL,  -- ハッシュ化メールアドレス
    estimated_pref_cd INTEGER,  -- 推定居住都道府県
    estimated_city_cd INTEGER,  -- 推定居住市区町村
    last_active_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,

    -- インデックス
    INDEX idx_users_location (estimated_pref_cd, estimated_city_cd),
    INDEX idx_users_active (is_active, last_active_at)
);
```

### 3. job_scores (求人スコア)
```sql
CREATE TABLE job_scores (
    score_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(job_id),
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    basic_score DECIMAL(5,2) NOT NULL CHECK (basic_score >= 0 AND basic_score <= 100),
    seo_score DECIMAL(5,2) NOT NULL CHECK (seo_score >= 0 AND seo_score <= 100),
    personalized_score DECIMAL(5,2) NOT NULL CHECK (personalized_score >= 0 AND personalized_score <= 100),
    total_score DECIMAL(5,2) GENERATED ALWAYS AS (
        (basic_score * 0.3 + seo_score * 0.2 + personalized_score * 0.5)
    ) STORED,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 複合主キー代替
    UNIQUE(job_id, user_id),

    -- インデックス
    INDEX idx_scores_user_total (user_id, total_score DESC),
    INDEX idx_scores_job (job_id)
);
```

### 4. user_actions (ユーザー行動履歴)
```sql
CREATE TABLE user_actions (
    action_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    job_id INTEGER NOT NULL REFERENCES jobs(job_id),
    endcl_cd VARCHAR(50) NOT NULL,
    action_type VARCHAR(20) NOT NULL,  -- 'view', 'click', 'apply'
    action_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- インデックス
    INDEX idx_actions_user_recent (user_id, action_at DESC),
    INDEX idx_actions_endcl (endcl_cd, action_type, action_at),
    INDEX idx_actions_job (job_id, action_type)
);
```

### 5. email_sections (メールセクション)
```sql
CREATE TABLE email_sections (
    section_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    batch_id INTEGER NOT NULL REFERENCES batch_jobs(batch_id),
    section_type VARCHAR(30) NOT NULL,  -- 'editorial_picks', 'top5', 'regional', 'nearby', 'high_income', 'new'
    section_order INTEGER NOT NULL CHECK (section_order BETWEEN 1 AND 6),
    job_ids INTEGER[] NOT NULL,  -- PostgreSQL配列型
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- インデックス
    INDEX idx_sections_user_batch (user_id, batch_id),
    INDEX idx_sections_batch (batch_id, section_type)
);
```

### 6. batch_jobs (バッチジョブ)
```sql
CREATE TABLE batch_jobs (
    batch_id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,  -- 'daily_matching', 'scoring', 'email_generation'
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'running',  -- 'running', 'completed', 'failed'
    total_records INTEGER,
    processed_records INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    error_logs JSONB,

    -- インデックス
    INDEX idx_batch_status (status, started_at DESC),
    INDEX idx_batch_type (job_type, started_at DESC)
);
```

### 7. company_popularity (企業人気度)
```sql
CREATE TABLE company_popularity (
    endcl_cd VARCHAR(50) PRIMARY KEY,
    total_views_360d INTEGER NOT NULL DEFAULT 0,
    total_applications_360d INTEGER NOT NULL DEFAULT 0,
    application_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE
            WHEN total_views_360d > 0 THEN total_applications_360d::DECIMAL / total_views_360d
            ELSE 0
        END
    ) STORED,
    last_calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- インデックス
    INDEX idx_popularity_rate (application_rate DESC)
);
```

### 8. semrush_keywords (SEOキーワード)
```sql
CREATE TABLE semrush_keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword VARCHAR(200) NOT NULL UNIQUE,
    search_volume INTEGER NOT NULL,
    keyword_difficulty DECIMAL(5,2),
    category VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- インデックス
    INDEX idx_keywords_volume (search_volume DESC),
    INDEX idx_keywords_text (keyword)  -- フルテキスト検索用
);
```

### 9. job_keywords (求人-キーワード関連)
```sql
CREATE TABLE job_keywords (
    job_id INTEGER NOT NULL REFERENCES jobs(job_id),
    keyword_id INTEGER NOT NULL REFERENCES semrush_keywords(keyword_id),
    match_count INTEGER DEFAULT 1,

    PRIMARY KEY (job_id, keyword_id),

    -- インデックス
    INDEX idx_job_keywords_job (job_id),
    INDEX idx_job_keywords_keyword (keyword_id)
);
```

## マスタデータ

### occupation_view (職種マスタ)
```sql
CREATE TABLE occupation_view (
    occupation_cd INTEGER PRIMARY KEY,
    occupation_name VARCHAR(100) NOT NULL,
    category_cd INTEGER,
    category_name VARCHAR(100),
    display_order INTEGER
);
```

### employment_type_view (雇用形態マスタ)
```sql
CREATE TABLE employment_type_view (
    employment_type_cd INTEGER PRIMARY KEY,
    employment_type_name VARCHAR(50) NOT NULL,
    is_valid BOOLEAN DEFAULT true  -- アルバイト・パートのみtrue
);
```

### prefecture_master (都道府県マスタ)
```sql
CREATE TABLE prefecture_master (
    pref_cd INTEGER PRIMARY KEY,
    pref_name VARCHAR(20) NOT NULL,
    region_cd INTEGER,
    region_name VARCHAR(20)
);
```

### city_master (市区町村マスタ)
```sql
CREATE TABLE city_master (
    city_cd INTEGER PRIMARY KEY,
    city_name VARCHAR(50) NOT NULL,
    pref_cd INTEGER NOT NULL REFERENCES prefecture_master(pref_cd),
    nearby_city_cds INTEGER[]  -- 隣接市区町村
);
```

## ビジネスルール

### 求人フィルタリング
```sql
-- 有効な求人の定義
CREATE VIEW valid_jobs AS
SELECT * FROM jobs
WHERE status = 'active'
  AND employment_type_cd IN (1, 3)  -- アルバイト・パートのみ
  AND fee > 500
  AND created_at > CURRENT_DATE - INTERVAL '30 days';
```

### 重複制御
```sql
-- 2週間以内の応募企業
CREATE VIEW recent_applications AS
SELECT DISTINCT user_id, endcl_cd
FROM user_actions
WHERE action_type = 'apply'
  AND action_at > CURRENT_DATE - INTERVAL '14 days';
```

### パフォーマンス統計
```sql
-- バッチ処理のパフォーマンス監視
CREATE VIEW batch_performance AS
SELECT
    job_type,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_duration_min,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
    MAX(completed_at) as last_run
FROM batch_jobs
WHERE started_at > CURRENT_DATE - INTERVAL '7 days'
GROUP BY job_type;
```

## 状態遷移

### バッチジョブの状態遷移
```
[pending] → [running] → [completed]
                ↓
            [failed]
```

### 求人の状態遷移
```
[draft] → [active] → [inactive]
             ↓
         [expired]
```

## データ整合性制約

### 外部キー制約
- job_scores.job_id → jobs.job_id (CASCADE DELETE)
- job_scores.user_id → users.user_id (CASCADE DELETE)
- user_actions.user_id → users.user_id (CASCADE DELETE)
- email_sections.user_id → users.user_id (CASCADE DELETE)

### チェック制約
- scores: 0 ≤ score ≤ 100
- fee: > 500円
- section_order: 1-6の範囲
- employment_type_cd: IN (1, 3)

### 一意制約
- users.email_hash
- jobs.application_id
- (job_id, user_id) in job_scores
- (job_id, keyword_id) in job_keywords

## インデックス戦略

### 頻繁なクエリパターン用
1. **ユーザー別スコア取得**: idx_scores_user_total
2. **地域別求人検索**: idx_jobs_location
3. **企業別応募履歴**: idx_actions_endcl
4. **新着求人取得**: idx_jobs_created
5. **高収入求人検索**: idx_jobs_fee

### パーティショニング検討
- user_actions: 月別パーティション（大量データ対策）
- job_scores: ユーザーIDレンジパーティション

## データ保持ポリシー

### 保持期間
- jobs: 90日（inactive後）
- user_actions: 365日
- job_scores: 30日
- email_sections: 7日
- batch_jobs: 30日

### アーカイブ戦略
- 古いデータは月次でアーカイブテーブルへ移動
- 集計データは別途集計テーブルで保持