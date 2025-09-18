-- ============================================================================
-- バイト求人マッチングシステム パフォーマンス最適化インデックス
-- Version: 1.1.0
-- Database: PostgreSQL 15 (Supabase)
-- Created: 2025-09-18
-- ============================================================================

-- ============================================================================
-- SECTION 1: 分析用インデックス（複合インデックス）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1.1 地域別求人検索の最適化
-- ----------------------------------------------------------------------------

-- 都道府県＋市区町村＋給与での複合検索
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_location_salary
ON jobs(pref_cd, city_cd, min_salary DESC)
WHERE is_active = TRUE;

-- 駅近求人の検索（駅名がある求人）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_station
ON jobs(station_name_eki, pref_cd)
WHERE station_name_eki IS NOT NULL AND is_active = TRUE;

-- 地理座標による近隣検索（PostGIS不使用の場合）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_coordinates
ON jobs(latitude, longitude)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND is_active = TRUE;

-- ----------------------------------------------------------------------------
-- 1.2 カテゴリ別求人検索の最適化
-- ----------------------------------------------------------------------------

-- 職種カテゴリ＋給与での複合検索
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_occupation_salary
ON jobs(occupation_cd1, occupation_cd2, min_salary DESC)
WHERE is_active = TRUE;

-- 雇用形態＋投稿日での複合検索
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_employment_date
ON jobs(employment_type_cd, posting_date DESC)
WHERE is_active = TRUE AND employment_type_cd IN (1, 3);

-- ----------------------------------------------------------------------------
-- 1.3 特徴フラグによる検索の最適化
-- ----------------------------------------------------------------------------

-- 日払い可能求人の高速検索
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_daily_payment
ON jobs(has_daily_payment, pref_cd, posting_date DESC)
WHERE has_daily_payment = TRUE AND is_active = TRUE;

-- 週払い可能求人の高速検索
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_weekly_payment
ON jobs(has_weekly_payment, pref_cd, posting_date DESC)
WHERE has_weekly_payment = TRUE AND is_active = TRUE;

-- 未経験歓迎求人の高速検索
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_no_experience
ON jobs(has_no_experience, occupation_cd1, posting_date DESC)
WHERE has_no_experience = TRUE AND is_active = TRUE;

-- 高収入求人の高速検索（計算列）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_high_income_location
ON jobs(has_high_income, pref_cd, city_cd, posting_date DESC)
WHERE has_high_income = TRUE AND is_active = TRUE;

-- ============================================================================
-- SECTION 2: スコアリング・マッチング用インデックス
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 スコア計算の最適化
-- ----------------------------------------------------------------------------

-- 企業人気度の高速アクセス
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_company_popularity_endcl
ON company_popularity(endcl_cd, popularity_score DESC);

-- 求人エンリッチメントの複合スコア検索
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enrichment_composite
ON job_enrichment(composite_score DESC, job_id);

-- 基礎スコアでのソート用
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enrichment_basic_score
ON job_enrichment(basic_score DESC)
WHERE basic_score IS NOT NULL;

-- SEOスコアでのソート用
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enrichment_seo_score
ON job_enrichment(seo_score DESC)
WHERE seo_score IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 2.2 ユーザーマッチングの最適化
-- ----------------------------------------------------------------------------

-- ユーザー別マッチング結果の高速取得（パーティションテーブル用）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mapping_user_score
ON user_job_mapping(user_id, batch_date, match_score DESC);

-- 日次バッチ別の処理用
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mapping_batch_processing
ON user_job_mapping(batch_date, user_id, rank_in_batch);

-- ----------------------------------------------------------------------------
-- 2.3 日次ピック検索の最適化
-- ----------------------------------------------------------------------------

-- ユーザー別・セクション別の高速取得
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_picks_user_section
ON daily_job_picks(user_id, pick_date, section, section_rank);

-- セクション別集計用
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_picks_section_stats
ON daily_job_picks(pick_date, section, user_id);

-- ============================================================================
-- SECTION 3: ユーザー行動分析用インデックス
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 行動履歴の分析
-- ----------------------------------------------------------------------------

-- ユーザー別行動履歴の時系列取得
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_actions_user_timeline
ON user_actions(user_id, action_timestamp DESC, action_type);

-- 企業別エンゲージメント分析
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_actions_endcl_engagement
ON user_actions(endcl_cd, action_type, action_timestamp DESC);

-- 求人別コンバージョン分析
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_actions_job_conversion
ON user_actions(job_id, action_type, user_id)
WHERE action_type IN ('click', 'application');

-- デバイス別分析
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_actions_device
ON user_actions(device_type, action_timestamp DESC)
WHERE device_type IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3.2 ユーザープロファイルの検索
-- ----------------------------------------------------------------------------

-- アクティブユーザーの高速フィルタ
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_subscription
ON users(is_active, email_subscription, last_active_at DESC)
WHERE is_active = TRUE AND email_subscription = TRUE;

-- 地域別ユーザー分布
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_region_distribution
ON users(estimated_pref_cd, estimated_city_cd, is_active);

-- プロファイル更新順
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_recent_update
ON user_profiles(profile_updated_at DESC, user_id);

-- ============================================================================
-- SECTION 4: メール配信用インデックス
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1 配信キューの処理
-- ----------------------------------------------------------------------------

-- 未送信メールの高速取得
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_queue_pending
ON daily_email_queue(scheduled_date, scheduled_time, status)
WHERE status = 'pending';

-- リトライ対象の取得
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_queue_retry
ON daily_email_queue(status, retry_count, scheduled_date)
WHERE status = 'failed' AND retry_count < 3;

-- トラッキング用
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_queue_tracking
ON daily_email_queue(email_tracking_id)
WHERE email_tracking_id IS NOT NULL;

-- ============================================================================
-- SECTION 5: バッチ処理用インデックス
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 5.1 バッチジョブ管理
-- ----------------------------------------------------------------------------

-- 実行中ジョブの監視
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_batch_running
ON batch_jobs(status, started_at DESC)
WHERE status = 'running';

-- ジョブタイプ別履歴
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_batch_history
ON batch_jobs(job_type, completed_at DESC)
WHERE completed_at IS NOT NULL;

-- エラージョブの分析
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_batch_errors
ON batch_jobs(status, error_count DESC, started_at DESC)
WHERE status = 'failed' OR error_count > 0;

-- ============================================================================
-- SECTION 6: SEOキーワード検索用インデックス
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 6.1 キーワードマッチング
-- ----------------------------------------------------------------------------

-- キーワード全文検索（trigram）
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_keywords_trigram
ON semrush_keywords USING gin(keyword gin_trgm_ops);

-- 検索ボリューム別ランキング
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_keywords_volume_category
ON semrush_keywords(category, search_volume DESC);

-- 求人キーワード関連の高速結合
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_keywords_composite
ON job_keywords(job_id, keyword_id, match_count DESC);

-- ============================================================================
-- SECTION 7: 集計・分析用インデックス
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 7.1 日次集計用
-- ----------------------------------------------------------------------------

-- 日別アクティブ求人数
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_daily_stats
ON jobs(DATE(posting_date), is_active, employment_type_cd)
WHERE is_active = TRUE;

-- 日別ユーザーアクション集計
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_actions_daily_stats
ON user_actions(DATE(action_timestamp), action_type, user_id);

-- ----------------------------------------------------------------------------
-- 7.2 重複制御用インデックス
-- ----------------------------------------------------------------------------

-- 2週間以内の応募企業チェック
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_actions_recent_applications
ON user_actions(user_id, endcl_cd, action_timestamp DESC)
WHERE action_type = 'application'
  AND action_timestamp > CURRENT_DATE - INTERVAL '14 days';

-- ============================================================================
-- SECTION 8: 部分インデックス（特定条件下での最適化）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 8.1 新着求人の高速取得
-- ----------------------------------------------------------------------------

-- 7日以内の新着求人
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_new_7days
ON jobs(posting_date DESC, pref_cd)
WHERE is_active = TRUE
  AND posting_date > CURRENT_DATE - INTERVAL '7 days';

-- 24時間以内の新着求人
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_new_24hours
ON jobs(posting_date DESC)
WHERE is_active = TRUE
  AND posting_date > CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- ----------------------------------------------------------------------------
-- 8.2 高優先度求人の取得
-- ----------------------------------------------------------------------------

-- 高報酬（fee）求人の優先取得
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_high_fee
ON jobs(fee DESC, posting_date DESC)
WHERE is_active = TRUE AND fee >= 1000;

-- ============================================================================
-- SECTION 9: 外部キー制約用インデックス（自動作成されない場合）
-- ============================================================================

-- 外部キー制約の参照側にインデックスを作成（CASCADE DELETE/UPDATE高速化）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_actions_fk_user
ON user_actions(user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_actions_fk_job
ON user_actions(job_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_profiles_fk_user
ON user_profiles(user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_enrichment_fk_job
ON job_enrichment(job_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_sections_fk_user
ON email_sections(user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_sections_fk_batch
ON email_sections(batch_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_email_queue_fk_user
ON daily_email_queue(user_id);

-- ============================================================================
-- SECTION 10: 統計情報の更新とメンテナンス
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 10.1 統計情報の更新
-- ----------------------------------------------------------------------------

-- 主要テーブルの統計情報を更新
ANALYZE jobs;
ANALYZE users;
ANALYZE user_actions;
ANALYZE user_job_mapping;
ANALYZE daily_job_picks;
ANALYZE job_enrichment;
ANALYZE company_popularity;

-- ----------------------------------------------------------------------------
-- 10.2 インデックスの使用状況確認用ビュー
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'RARELY_USED'
        WHEN idx_scan < 1000 THEN 'OCCASIONALLY_USED'
        ELSE 'FREQUENTLY_USED'
    END as usage_category
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

COMMENT ON VIEW index_usage_stats IS 'インデックス使用状況の監視';

-- ----------------------------------------------------------------------------
-- 10.3 インデックス断片化チェック用関数
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION check_index_bloat()
RETURNS TABLE (
    schemaname text,
    tablename text,
    indexname text,
    index_size text,
    index_bloat text,
    bloat_ratio numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.nspname::text as schemaname,
        c.relname::text as tablename,
        i.relname::text as indexname,
        pg_size_pretty(pg_relation_size(i.oid))::text as index_size,
        pg_size_pretty((pg_relation_size(i.oid) - pg_relation_size(i.oid, 'main'))::bigint)::text as index_bloat,
        ROUND(
            100.0 * (pg_relation_size(i.oid) - pg_relation_size(i.oid, 'main'))::numeric /
            NULLIF(pg_relation_size(i.oid), 0),
            2
        ) as bloat_ratio
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_index x ON c.oid = x.indrelid
    JOIN pg_class i ON i.oid = x.indexrelid
    WHERE n.nspname = 'public'
      AND c.relkind = 'r'
      AND i.relkind = 'i'
      AND pg_relation_size(i.oid) > 1048576  -- 1MB以上
    ORDER BY pg_relation_size(i.oid) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_index_bloat() IS 'インデックスの断片化状況をチェック';

-- ============================================================================
-- 終了メッセージ
-- ============================================================================
-- インデックス作成完了: 65個の最適化インデックス
-- 注意: CONCURRENTLYオプションを使用しているため、本番環境でも安全に実行可能
-- 次のステップ: 003_create_functions.sql でスコアリング関数を作成