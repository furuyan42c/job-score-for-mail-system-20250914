# クイックスタートガイド: バイト求人マッチングシステム

**所要時間**: 30分
**前提条件**: Python 3.11+, Node.js 20+, PostgreSQL 15+（またはSupabase）

## 📋 概要

このガイドでは、バイト求人マッチングシステムを30分でセットアップし、動作確認まで行います。

## 🚀 セットアップ手順

### 1. リポジトリのクローンと環境準備（5分）

```bash
# リポジトリをクローン（既にある場合はスキップ）
git clone <repository-url>
cd job-matching-system

# ブランチを切り替え
git checkout 002-think-hard-ultrathink

# 環境変数ファイルを作成
cp .env.example .env
```

### 2. データベースセットアップ（5分）

#### オプションA: Supabase使用（推奨）
```bash
# Supabaseプロジェクトを作成
# https://app.supabase.com で新規プロジェクト作成

# .envファイルに接続情報を記載
echo "SUPABASE_URL=your-project-url" >> .env
echo "SUPABASE_KEY=your-anon-key" >> .env
echo "DATABASE_URL=postgresql://..." >> .env
```

#### オプションB: ローカルPostgreSQL
```bash
# PostgreSQLをインストール（macOS）
brew install postgresql@15
brew services start postgresql@15

# データベース作成
createdb job_matching_db

# スキーマを適用
psql job_matching_db < specs/002-think-hard-ultrathink/schema.sql
```

### 3. バックエンドセットアップ（5分）

```bash
# Pythonバックエンドディレクトリへ移動
cd backend

# 仮想環境作成
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# データベースマイグレーション
alembic upgrade head

# サンプルデータ投入
python scripts/seed_data.py

# 開発サーバー起動
uvicorn main:app --reload --port 8000
```

### 4. フロントエンドセットアップ（5分）

```bash
# 新しいターミナルを開く
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

### 5. 動作確認（10分）

#### 5.1 API動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/health

# バッチ処理の手動実行
curl -X POST http://localhost:8000/api/v1/batch/trigger \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"batch_type": "daily_matching"}'

# SQLクエリ実行（モニタリング）
curl -X POST http://localhost:8000/api/v1/sql/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "SELECT COUNT(*) FROM jobs"}'
```

#### 5.2 フロントエンド動作確認
1. ブラウザで http://localhost:3000 を開く
2. SQL実行画面へ移動
3. サンプルクエリを実行:
   ```sql
   SELECT
     j.application_name,
     j.fee,
     j.min_salary,
     j.max_salary
   FROM jobs j
   WHERE j.status = 'active'
   LIMIT 10;
   ```

#### 5.3 メール生成確認
```bash
# 特定ユーザーのメール生成
curl -X POST http://localhost:8000/api/v1/email/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"user_id": 1}'

# メールプレビュー
open http://localhost:8000/api/v1/email/preview/1
```

## 🧪 統合テスト実行

```bash
# バックエンドテスト
cd backend
pytest tests/integration/ -v

# フロントエンドテスト
cd frontend
npm test

# E2Eテスト（両サーバー起動済みの状態で）
npm run test:e2e
```

## 📊 サンプルシナリオ

### シナリオ1: 日次バッチ処理の実行

1. **データインポート**
   ```bash
   # CSVファイルをアップロード
   curl -X POST http://localhost:8000/api/v1/jobs/import \
     -H "X-API-Key: your-api-key" \
     -F "file=@sample_jobs.csv"
   ```

2. **スコアリング実行**
   ```bash
   curl -X POST http://localhost:8000/api/v1/scoring/calculate \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{}'
   ```

3. **マッチング生成**
   ```bash
   curl -X POST http://localhost:8000/api/v1/matching/generate \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{"limit": 40}'
   ```

### シナリオ2: 個別ユーザーのマッチング確認

```python
# Pythonスクリプト例
import requests

API_BASE = "http://localhost:8000/api/v1"
HEADERS = {"X-API-Key": "your-api-key"}

# ユーザー1のマッチング結果を取得
response = requests.get(f"{API_BASE}/matching/user/1", headers=HEADERS)
matching = response.json()

# 各セクションの求人数を表示
for section, jobs in matching['sections'].items():
    print(f"{section}: {len(jobs)}件")

# メール生成
email_response = requests.post(
    f"{API_BASE}/email/generate",
    json={"user_id": 1},
    headers=HEADERS
)
print(f"メール件名: {email_response.json()['subject']}")
```

## 🔍 トラブルシューティング

### データベース接続エラー
```bash
# PostgreSQLサービスの状態確認
brew services list | grep postgresql

# 接続テスト
psql -U postgres -h localhost -d job_matching_db
```

### ポートが既に使用されている
```bash
# 使用中のポート確認
lsof -i :8000  # バックエンド
lsof -i :3000  # フロントエンド

# プロセスを終了
kill -9 <PID>
```

### 依存関係のエラー
```bash
# Python依存関係の再インストール
pip install --upgrade -r requirements.txt

# Node.js依存関係の再インストール
rm -rf node_modules package-lock.json
npm install
```

## 📈 パフォーマンス確認

### メトリクス確認
```bash
# システムメトリクスの取得
curl http://localhost:8000/api/v1/monitoring/metrics \
  -H "X-API-Key: your-api-key" | jq

# エラーログの確認
curl "http://localhost:8000/api/v1/monitoring/errors?level=error" \
  -H "X-API-Key: your-api-key" | jq
```

### 負荷テスト（オプション）
```bash
# Apache Bench使用
ab -n 1000 -c 10 http://localhost:8000/health

# locust使用
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## 🎯 次のステップ

1. **本番環境へのデプロイ準備**
   - 環境変数の本番設定
   - データベースのスケーリング設定
   - CDN/キャッシュの設定

2. **モニタリング設定**
   - Grafanaダッシュボード設定
   - アラート設定
   - ログ集約設定

3. **セキュリティ強化**
   - API認証の強化
   - SQLインジェクション対策の確認
   - レート制限の設定

## 📚 参考資料

- [API仕様書](./contracts/api-spec.yaml)
- [データモデル設計](./data-model.md)
- [技術リサーチ](./research.md)
- [実装詳細](../001-job-matching-system/answers.md)

---

問題が発生した場合は、[Issue](https://github.com/your-repo/issues)を作成してください。