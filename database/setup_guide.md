# 🚀 データベースセットアップガイド

## 📋 概要

バイト求人マッチングシステムのデータベース環境を構築するためのガイドです。
PostgreSQL 15（Supabase）上に14個のコアテーブル、65個のインデックス、20個のスコアリング関数を設定します。

## 🔧 前提条件

- PostgreSQL 15以上（推奨：Supabase）
- psql CLIツール または Supabase Dashboard
- 管理者権限を持つデータベースユーザー
- 最低8GB RAM（10万件のデータ処理用）

## 📂 ファイル構成

```
database/
├── migrations/
│   ├── 001_create_tables.sql     # 14テーブル + 6マスター + 3ビュー
│   ├── 002_create_indexes.sql    # 65個の最適化インデックス
│   └── 003_create_functions.sql  # 20個のスコアリング関数
├── seeds/
│   └── 001_master_data.sql       # マスターデータ（212レコード）
└── setup_guide.md                 # このファイル
```

## 🎯 セットアップ手順

### 1️⃣ Supabaseプロジェクトの作成（新規の場合）

```bash
# Supabase CLIのインストール（未インストールの場合）
npm install -g supabase

# ログイン
supabase login

# プロジェクト初期化
supabase init

# プロジェクト開始
supabase start
```

### 2️⃣ データベース接続設定

#### オプションA: Supabase Cloud使用時

1. [Supabase Dashboard](https://app.supabase.com)にログイン
2. Settings → Database → Connection stringをコピー
3. 環境変数に設定:

```bash
export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
```

#### オプションB: ローカルSupabase使用時

```bash
# デフォルト接続情報
export DATABASE_URL="postgresql://postgres:postgres@localhost:54322/postgres"
```

### ⚠️ 既知の問題と対処法

#### URLエンコード
特殊文字を含むパスワードの場合、URLエンコードが必要です:
- 例: `jfv!edu@QKX*gva9mhq` → `jfv%21edu%40QKX%2Agva9mhq`

#### パーティションテーブルのPRIMARY KEY
- PostgreSQL 15では、パーティションテーブルのPRIMARY KEYにパーティションキーを含める必要があります
- 本SQLファイルは修正済みです

### 3️⃣ マイグレーション実行

#### 方法1: psqlを使用（推奨）

```bash
# 作業ディレクトリに移動
cd database/

# 1. テーブル作成
psql $DATABASE_URL -f migrations/001_create_tables.sql

# 2. インデックス作成（5-10分かかる場合があります）
psql $DATABASE_URL -f migrations/002_create_indexes.sql

# 3. 関数作成
psql $DATABASE_URL -f migrations/003_create_functions.sql

# 4. マスターデータ投入
psql $DATABASE_URL -f seeds/001_master_data.sql
```

#### 方法2: Supabase Dashboard使用

1. SQL Editorを開く
2. 各SQLファイルの内容をコピー＆ペースト
3. 順番に実行:
   - 001_create_tables.sql
   - 002_create_indexes.sql
   - 003_create_functions.sql
   - 001_master_data.sql

#### 方法3: 一括実行スクリプト

```bash
# setup.sh スクリプト作成
cat << 'EOF' > setup.sh
#!/bin/bash
set -e

echo "🚀 データベースセットアップ開始..."

echo "📦 [1/4] テーブル作成中..."
psql $DATABASE_URL -f migrations/001_create_tables.sql

echo "🔍 [2/4] インデックス作成中（時間がかかります）..."
psql $DATABASE_URL -f migrations/002_create_indexes.sql

echo "⚡ [3/4] 関数作成中..."
psql $DATABASE_URL -f migrations/003_create_functions.sql

echo "📝 [4/4] マスターデータ投入中..."
psql $DATABASE_URL -f seeds/001_master_data.sql

echo "✅ セットアップ完了！"
EOF

chmod +x setup.sh
./setup.sh
```

### 4️⃣ セットアップ検証

```sql
-- テーブル数確認（20テーブル）
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- インデックス数確認（65個以上）
SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';

-- 関数数確認（20個以上）
SELECT COUNT(*) FROM information_schema.routines
WHERE routine_schema = 'public';

-- マスターデータ確認
SELECT 'prefecture_master' as table_name, COUNT(*) as count FROM prefecture_master
UNION ALL
SELECT 'city_master', COUNT(*) FROM city_master
UNION ALL
SELECT 'occupation_master', COUNT(*) FROM occupation_master
UNION ALL
SELECT 'employment_type_master', COUNT(*) FROM employment_type_master
UNION ALL
SELECT 'feature_master', COUNT(*) FROM feature_master
UNION ALL
SELECT 'semrush_keywords', COUNT(*) FROM semrush_keywords;
```

期待される結果:
- prefecture_master: 47件
- city_master: 51件
- occupation_master: 40件
- employment_type_master: 10件
- feature_master: 29件
- semrush_keywords: 40件

### 5️⃣ パーティション設定（日次運用）

```sql
-- 日次パーティション作成（例：2025年9月19日）
CREATE TABLE user_actions_2025_09_19 PARTITION OF user_actions
    FOR VALUES FROM ('2025-09-19') TO ('2025-09-20');

CREATE TABLE user_job_mapping_2025_09_19 PARTITION OF user_job_mapping
    FOR VALUES FROM ('2025-09-19') TO ('2025-09-20');

CREATE TABLE daily_job_picks_2025_09_19 PARTITION OF daily_job_picks
    FOR VALUES FROM ('2025-09-19') TO ('2025-09-20');
```

## 🧪 動作確認

### 基本的な動作テスト

```sql
-- 1. サンプル求人データ挿入
INSERT INTO jobs (
    endcl_cd, company_name, application_name,
    pref_cd, city_cd, min_salary, max_salary,
    fee, salary_type, employment_type_cd,
    feature_codes, posting_date
) VALUES (
    'TEST001', 'テスト企業株式会社', 'カフェスタッフ募集',
    '13', '13104', 1200, 1500,
    1000, 'hourly', 1,
    ARRAY['D01', 'S01', 'N01'], CURRENT_TIMESTAMP
);

-- 2. サンプルユーザー挿入
INSERT INTO users (
    email, age_group, gender,
    estimated_pref_cd, estimated_city_cd,
    preferred_salary_min
) VALUES (
    'test@example.com', '20代前半', 'female',
    '13', '13104', 1100
);

-- 3. スコア計算テスト
SELECT calculate_composite_score(
    (SELECT job_id FROM jobs LIMIT 1),
    (SELECT user_id FROM users LIMIT 1)
) as test_score;

-- 4. 企業人気度更新
SELECT update_company_popularity();

-- 5. バッチ処理テスト（小規模）
SELECT batch_calculate_scores(1, 10);
```

### パフォーマンステスト

```sql
-- インデックス使用状況確認
SELECT * FROM index_usage_stats ORDER BY index_scans DESC LIMIT 10;

-- スロークエリ確認
SELECT * FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC LIMIT 5;

-- テーブルサイズ確認
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🔄 日次メンテナンス

### 自動化スクリプト（cron設定）

```bash
# daily_maintenance.sh
#!/bin/bash

# 1. 古いパーティション削除（30日以前）
psql $DATABASE_URL -c "DROP TABLE IF EXISTS user_actions_$(date -d '30 days ago' +%Y_%m_%d);"
psql $DATABASE_URL -c "DROP TABLE IF EXISTS user_job_mapping_$(date -d '30 days ago' +%Y_%m_%d);"
psql $DATABASE_URL -c "DROP TABLE IF EXISTS daily_job_picks_$(date -d '7 days ago' +%Y_%m_%d);"

# 2. 明日のパーティション作成
TOMORROW=$(date -d 'tomorrow' +%Y-%m-%d)
TOMORROW_LABEL=$(date -d 'tomorrow' +%Y_%m_%d)
DAY_AFTER=$(date -d '2 days' +%Y-%m-%d)

psql $DATABASE_URL << EOF
CREATE TABLE IF NOT EXISTS user_actions_${TOMORROW_LABEL} PARTITION OF user_actions
    FOR VALUES FROM ('${TOMORROW}') TO ('${DAY_AFTER}');

CREATE TABLE IF NOT EXISTS user_job_mapping_${TOMORROW_LABEL} PARTITION OF user_job_mapping
    FOR VALUES FROM ('${TOMORROW}') TO ('${DAY_AFTER}');

CREATE TABLE IF NOT EXISTS daily_job_picks_${TOMORROW_LABEL} PARTITION OF daily_job_picks
    FOR VALUES FROM ('${TOMORROW}') TO ('${DAY_AFTER}');
EOF

# 3. 統計情報更新
psql $DATABASE_URL -c "ANALYZE;"

# 4. インデックス再構築（週末のみ）
if [ $(date +%u) -eq 6 ]; then
    psql $DATABASE_URL -c "REINDEX DATABASE postgres;"
fi
```

### Crontab設定

```bash
# 毎日AM 2:00にメンテナンス実行
0 2 * * * /path/to/daily_maintenance.sh >> /var/log/db_maintenance.log 2>&1

# 毎日AM 3:00にスコアリング更新
0 3 * * * psql $DATABASE_URL -c "SELECT daily_scoring_update(1000, 50000);" >> /var/log/scoring.log 2>&1
```

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. インデックス作成が遅い

```sql
-- 並列度を上げる
SET max_parallel_workers_per_gather = 4;
SET max_parallel_workers = 8;

-- その後インデックス作成を再実行
```

#### 2. メモリ不足エラー

```sql
-- work_memを一時的に増やす
SET work_mem = '256MB';
SET maintenance_work_mem = '1GB';
```

#### 3. ロック競合

```sql
-- 長時間ロックを保持しているクエリを確認
SELECT pid, usename, query, state, wait_event_type, wait_event
FROM pg_stat_activity
WHERE state != 'idle' AND wait_event_type IS NOT NULL;

-- 必要に応じてキャンセル
SELECT pg_cancel_backend(pid);
```

#### 4. パーティションエラー

```sql
-- パーティション範囲の確認
SELECT
    parent.relname AS parent,
    child.relname AS partition,
    pg_get_expr(child.relpartbound, child.oid) AS bounds
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname IN ('user_actions', 'user_job_mapping', 'daily_job_picks')
ORDER BY parent.relname, child.relname;
```

## 📊 モニタリング

### Supabase Dashboard活用

1. **Database Health**: リアルタイムのCPU、メモリ、ディスク使用率
2. **Query Performance**: スロークエリの特定
3. **Table Sizes**: テーブルサイズの監視

### カスタムモニタリングビュー

```sql
-- システムヘルスチェック
CREATE VIEW system_health AS
SELECT
    (SELECT COUNT(*) FROM jobs WHERE is_active = TRUE) as active_jobs,
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users,
    (SELECT COUNT(*) FROM batch_jobs WHERE status = 'running') as running_batches,
    (SELECT MAX(completed_at) FROM batch_jobs WHERE job_type = 'scoring') as last_scoring,
    (SELECT pg_database_size(current_database())) as db_size_bytes;
```

## 🔐 セキュリティ設定

### Row Level Security (RLS) 設定例

```sql
-- RLS有効化
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_email_queue ENABLE ROW LEVEL SECURITY;

-- ポリシー作成
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid()::text = email);

CREATE POLICY "Users can view own actions" ON user_actions
    FOR SELECT USING (user_id IN (
        SELECT user_id FROM users WHERE auth.uid()::text = email
    ));
```

## 📝 バックアップ戦略

### 自動バックアップ（Supabase Cloud）

- 日次自動バックアップ（過去7日間）
- Point-in-time Recovery（過去30日間）

### 手動バックアップ

```bash
# フルバックアップ
pg_dump $DATABASE_URL -Fc -f backup_$(date +%Y%m%d).dump

# スキーマのみ
pg_dump $DATABASE_URL --schema-only -f schema_$(date +%Y%m%d).sql

# データのみ
pg_dump $DATABASE_URL --data-only -f data_$(date +%Y%m%d).sql
```

### リストア

```bash
# フルリストア
pg_restore -d $DATABASE_URL -c backup_20250918.dump

# テーブル単位のリストア
pg_restore -d $DATABASE_URL -t jobs backup_20250918.dump
```

## 🎉 完了

セットアップが完了しました！次のステップ：

1. ✅ APIエンドポイントの実装（backend/）
2. ✅ フロントエンドの実装（frontend/）
3. ✅ バッチ処理の設定
4. ✅ モニタリングダッシュボードの設定

## 📚 参考資料

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [スコアリングアルゴリズム詳細](../specs/001-job-matching-system/modules/02_scoring.md)
- [データモデル設計書](../specs/001-job-matching-system/archive/data-model.md)