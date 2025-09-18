# 🚀 10万件求人データ高速生成システム

PostgreSQLに10万件のリアルな求人データを5分以内で効率的に生成・投入するシステムです。

## 📊 パフォーマンス目標

- **生成速度**: 333 records/sec（5分で10万件）
- **メモリ使用量**: 512MB以下
- **データ品質**: 制約違反0件
- **エラー率**: 0.1%以下

## 🏗️ アーキテクチャ設計

### データ生成戦略
- **バッチ処理**: 5,000件ずつ20バッチに分割
- **バルクインサート**: PostgreSQL COPY FROMで高速投入
- **並列処理**: 4ワーカーでの並列実行
- **メモリ効率**: ストリーミング生成でメモリ最適化

### データパターン
- **地域分布**: 東京25%, 大阪15%, 愛知8%（人口比ベース）
- **雇用形態**: アルバイト40%, パート35%, 派遣15%
- **給与分布**: 900-3000円の現実的な時給分布
- **fee分布**: 500-5000円（制約条件満たす）

## 📁 ファイル構成

```
scripts/
├── generate_job_data.py           # メインデータ生成スクリプト
├── setup_master_data.py           # マスターデータ事前投入
├── benchmark_data_generation.py   # パフォーマンス検証
├── run_data_generation.sh         # 統合実行スクリプト
├── requirements_data_generation.txt # Python依存関係
└── README_data_generation.md      # このファイル
```

## 🔧 セットアップ

### 1. 依存関係インストール

```bash
# Python仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r scripts/requirements_data_generation.txt
```

### 2. 環境変数設定

```bash
# .env.dev ファイル作成
cat > .env.dev << 'EOF'
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mail_score_dev
DB_USER=postgres
DB_PASSWORD=password
EOF
```

### 3. データベース準備

```bash
# マイグレーション実行（既にスキーマ作成済みの場合）
psql -h localhost -U postgres -d mail_score_dev -f migrations/001_initial_schema.sql
```

## 🚀 実行方法

### クイックスタート（推奨）

```bash
# 統合スクリプトで一括実行
./scripts/run_data_generation.sh dev 100000

# ベンチマーク付き実行
./scripts/run_data_generation.sh dev 100000 --benchmark
```

### 個別実行

```bash
# 1. マスターデータセットアップ
python3 scripts/setup_master_data.py

# 2. 求人データ生成
python3 scripts/generate_job_data.py

# 3. パフォーマンス検証
python3 scripts/benchmark_data_generation.py
```

## 📈 パフォーマンス最適化

### バッチ処理設定

```python
BATCH_CONFIG = {
    'batch_size': 5000,        # 最適バッチサイズ
    'parallel_workers': 4,     # CPU並列度
    'use_copy_from': True,     # PostgreSQL COPY使用
    'memory_limit_mb': 512,    # メモリ制限
}
```

### データベース最適化

```sql
-- インデックス一時無効化（生成中）
DROP INDEX CONCURRENTLY idx_jobs_location;

-- 生成後に再作成
CREATE INDEX CONCURRENTLY idx_jobs_location ON jobs(pref_cd, city_cd, is_active);
```

## 🎯 データ品質保証

### 制約チェック

- **fee制約**: fee > 500 AND fee <= 5000
- **外部キー**: prefecture_master, city_master参照整合性
- **必須項目**: endcl_cd, company_name, application_name等
- **生成フィールド**: has_high_income等の自動計算

### 分布検証

```sql
-- 地域分布確認
SELECT pref_cd, COUNT(*)
FROM jobs
GROUP BY pref_cd
ORDER BY COUNT(*) DESC;

-- 給与分布確認
SELECT
    CASE
        WHEN min_salary < 1200 THEN '基本時給'
        WHEN min_salary < 1500 THEN '標準時給'
        WHEN min_salary < 2000 THEN '高時給'
        ELSE '特別高時給'
    END as salary_range,
    COUNT(*)
FROM jobs
GROUP BY 1;
```

## 📊 監視・ログ

### ログファイル

```
logs/
├── data_generation_dev_20250918_143022.log  # 実行ログ
├── jobs_backup_20250918_143022.sql          # バックアップ（本番のみ）
└── /tmp/benchmark_results/                  # ベンチマーク結果
    ├── benchmark_results.csv
    ├── benchmark_summary.md
    └── performance_charts.png
```

### 進捗監視

```bash
# リアルタイム進捗確認
tail -f logs/data_generation_dev_*.log

# パフォーマンス監視
top -p $(pgrep -f generate_job_data.py)
```

## 🔍 トラブルシューティング

### よくある問題

#### 1. メモリ不足
```
ERROR: out of memory
```
**解決策**: batch_sizeを3000に削減

#### 2. 接続エラー
```
ERROR: could not connect to server
```
**解決策**: データベース設定・接続情報確認

#### 3. 制約違反
```
ERROR: new row for relation "jobs" violates check constraint
```
**解決策**: データ生成ロジックのfee範囲確認

### パフォーマンス改善

#### 速度向上
1. **batch_size増加**: 5000 → 7500
2. **並列度調整**: CPU数に応じて2-8
3. **インデックス無効化**: 生成中は最小限に

#### メモリ最適化
1. **ストリーミング生成**: バッチごとに解放
2. **接続プール**: 同一接続の再利用
3. **ガベージコレクション**: 明示的なメモリ解放

## 🎪 使用例

### 開発環境（1万件テスト）

```bash
./scripts/run_data_generation.sh dev 10000
```

### ステージング環境（5万件）

```bash
./scripts/run_data_generation.sh staging 50000
```

### 本番環境（10万件）

```bash
# バックアップ付き本番実行
./scripts/run_data_generation.sh production 100000
```

## 📝 カスタマイズ

### データ分布変更

```python
# generate_job_data.py 内
'prefecture_weights': {
    '13': 30.0,  # 東京都を30%に変更
    '27': 20.0,  # 大阪府を20%に変更
    # ...
}
```

### 新しい特徴追加

```python
# feature_master に新特徴追加後
'feature_probabilities': {
    'D01': 0.35,  # 日払い
    'NEW01': 0.25,  # 新特徴
    # ...
}
```

## 🛡️ セキュリティ・運用

### 本番環境実行時の注意
- **データバックアップ**: 自動実行
- **実行確認**: 対話的確認プロンプト
- **ロールバック**: 失敗時の復旧手順

### 監査ログ
- **実行者記録**: 実行ユーザー・時刻
- **変更追跡**: 影響レコード数
- **品質メトリクス**: 制約違反・エラー数

## 📞 サポート

### 問題報告
- **ログファイル**: 必須添付
- **環境情報**: OS, PostgreSQL版本
- **実行パラメータ**: レコード数、バッチサイズ

### パフォーマンス相談
- **ベンチマーク結果**: CSV・レポート添付
- **リソース制約**: CPU、メモリ仕様
- **目標設定**: 要求速度・制約条件