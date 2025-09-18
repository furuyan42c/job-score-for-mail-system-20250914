# バイト求人マッチングシステム - Backend API

## 概要

10万件×1万人のスケーラブルなバイト求人マッチングシステムのバックエンドAPI。FastAPIとPostgreSQL（Supabase）を使用した高性能なRESTful APIを提供します。

## 主な機能

- **求人管理**: 10万件規模の求人データ管理
- **ユーザー管理**: 1万人規模のユーザープロファイル
- **AI マッチング**: 高度なスコアリングエンジンによる求人推薦
- **バッチ処理**: 大規模データ処理とメール配信
- **リアルタイム分析**: KPIダッシュボードと分析機能

## 技術スタック

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Validation**: Pydantic 2.0
- **Cache**: Redis
- **Background Tasks**: Celery
- **Testing**: pytest + AsyncIO
- **Documentation**: OpenAPI/Swagger

## アーキテクチャ

```
backend/
├── app/
│   ├── main.py              # FastAPIアプリケーション
│   ├── core/
│   │   ├── config.py        # 設定管理
│   │   └── database.py      # DB接続設定
│   ├── models/              # Pydanticモデル
│   │   ├── jobs.py         # 求人関連モデル
│   │   ├── users.py        # ユーザー関連モデル
│   │   ├── matching.py     # マッチング関連モデル
│   │   ├── analytics.py    # 分析関連モデル
│   │   └── batch.py        # バッチ処理関連モデル
│   ├── routers/            # APIエンドポイント
│   │   ├── jobs.py         # 求人API
│   │   ├── users.py        # ユーザーAPI
│   │   ├── matching.py     # マッチングAPI
│   │   ├── analytics.py    # 分析API
│   │   └── batch.py        # バッチAPI
│   └── services/           # ビジネスロジック
│       ├── scoring.py      # スコアリングエンジン
│       ├── jobs.py         # 求人サービス
│       ├── users.py        # ユーザーサービス
│       ├── matching.py     # マッチングサービス
│       ├── analytics.py    # 分析サービス
│       └── batch.py        # バッチサービス
├── tests/                  # テストスイート
├── requirements.txt        # 依存関係
└── .env.example           # 環境変数テンプレート
```

## セットアップ

### 1. 環境構築

```bash
# リポジトリクローン
git clone <repository-url>
cd backend

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
# 環境変数ファイル作成
cp .env.example .env

# .envファイルを編集して実際の値を設定
vi .env
```

必須の環境変数：
- `DATABASE_URL`: PostgreSQL接続URL
- `SUPABASE_URL`: SupabaseプロジェクトURL
- `SUPABASE_ANON_KEY`: Supabase匿名キー
- `SECRET_KEY`: JWT署名用シークレットキー
- `REDIS_URL`: Redis接続URL

### 3. データベース設定

```bash
# データベーススキーマ適用
psql -d your_database -f ../database/migrations/001_create_tables.sql

# マスターデータ投入（オプション）
psql -d your_database -f ../database/seeds/master_data.sql
```

### 4. アプリケーション起動

```bash
# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# または
python -m uvicorn app.main:app --reload
```

### 5. API動作確認

ブラウザで以下のURLにアクセス：
- API文書: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- ヘルスチェック: http://localhost:8000/health

## API エンドポイント

### 求人管理 (`/api/v1/jobs`)

- `GET /` - 求人検索
- `GET /{job_id}` - 求人詳細取得
- `POST /` - 求人作成
- `PUT /{job_id}` - 求人更新
- `DELETE /{job_id}` - 求人削除
- `POST /{job_id}/activate` - 求人有効化
- `POST /{job_id}/deactivate` - 求人無効化
- `GET /{job_id}/recommendations` - 類似求人推薦
- `POST /bulk-operations` - 一括操作

### ユーザー管理 (`/api/v1/users`)

- `GET /` - ユーザー検索
- `GET /{user_id}` - ユーザー詳細取得
- `POST /` - ユーザー作成
- `PUT /{user_id}` - ユーザー更新
- `POST /{user_id}/actions` - 行動記録
- `GET /{user_id}/profile` - プロファイル取得

### マッチング (`/api/v1/matching`)

- `POST /execute` - マッチング実行
- `GET /realtime/{user_id}` - リアルタイム推薦
- `GET /recommendations/{user_id}` - ユーザー推薦取得
- `GET /results` - マッチング結果検索
- `GET /analytics` - マッチング分析

### 分析 (`/api/v1/analytics`)

- `GET /dashboard` - ダッシュボードKPI
- `GET /timeseries/{metric_name}` - 時系列メトリクス
- `GET /performance/categories` - カテゴリ別パフォーマンス
- `GET /performance/locations` - 地域別パフォーマンス
- `POST /reports/generate` - カスタムレポート生成

### バッチ処理 (`/api/v1/batch`)

- `GET /jobs` - バッチジョブ一覧
- `POST /jobs` - バッチジョブ作成
- `GET /jobs/{batch_id}` - バッチジョブ詳細
- `POST /email/generate` - メール生成
- `POST /data/import` - データインポート

## スコアリングシステム

高性能なマッチングスコアリングエンジンを搭載：

### スコア計算要素

1. **基本スコア** (25%): 求人の基本的な魅力度
2. **立地スコア** (15%): 通勤の便利さ
3. **カテゴリスコア** (20%): 職種の適合度
4. **給与スコア** (15%): 給与の魅力度
5. **特徴スコア** (10%): 求人特徴の魅力度
6. **嗜好スコア** (10%): 個人の好みとの適合度
7. **人気度スコア** (5%): 求人・企業の人気度

### 高速化対応

- 並列スコア計算
- キャッシュ活用
- バッチ処理対応
- インデックス最適化

## テスト

```bash
# 全テスト実行
pytest

# 単体テストのみ
pytest tests/unit/

# 統合テストのみ
pytest tests/integration/

# カバレッジレポート生成
pytest --cov=app --cov-report=html
```

### テスト種類

- **単体テスト**: 個別機能のテスト
- **統合テスト**: API エンドポイントのテスト
- **パフォーマンステスト**: 大量データでの性能テスト

## 本番デプロイ

### Docker使用

```bash
# Dockerイメージビルド
docker build -t job-matching-backend .

# コンテナ起動
docker run -p 8000:8000 --env-file .env job-matching-backend
```

### 本番設定

```bash
# 本番サーバー起動
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

環境変数の設定：
- `ENVIRONMENT=production`
- `DEBUG=False`
- `ALLOWED_HOSTS=your-domain.com`

## パフォーマンス

### スケーラビリティ対応

- **求人データ**: 10万件までスケール対応
- **ユーザー数**: 1万人までスケール対応
- **スコアリング**: 毎日100万件の組み合わせ処理
- **API応答**: 平均200ms以下
- **バッチ処理**: 1時間以内完了

### 最適化施策

- データベースインデックス最適化
- 接続プール設定
- Redis キャッシュ活用
- 非同期処理活用
- バッチサイズ調整

## 監視・ログ

### メトリクス

- API応答時間
- エラー率
- スループット
- データベース性能
- スコアリング処理時間

### ログ

- 構造化ログ（JSON形式）
- レベル別ログ出力
- エラー詳細記録
- パフォーマンス記録

## 開発ガイド

### コード規約

```bash
# コードフォーマット
black app/ tests/
isort app/ tests/

# リンティング
flake8 app/ tests/
mypy app/

# プリコミットフック設定
pre-commit install
```

### 新機能追加手順

1. モデル定義 (`app/models/`)
2. サービス実装 (`app/services/`)
3. API エンドポイント追加 (`app/routers/`)
4. テスト作成 (`tests/`)
5. ドキュメント更新

## トラブルシューティング

### よくある問題

1. **データベース接続エラー**
   - DATABASE_URL の確認
   - Supabase接続情報の確認

2. **スコアリング処理が遅い**
   - バッチサイズの調整
   - インデックスの確認

3. **メモリ使用量が多い**
   - 接続プールサイズの調整
   - キャッシュ設定の見直し

### ログ確認

```bash
# アプリケーションログ
tail -f logs/app.log

# エラーログ
tail -f logs/error.log

# パフォーマンスログ
tail -f logs/performance.log
```

## ライセンス

このプロジェクトは内部使用のためのプロプライエタリソフトウェアです。

## サポート

技術的な質問や問題報告は、開発チームまでお問い合わせください。