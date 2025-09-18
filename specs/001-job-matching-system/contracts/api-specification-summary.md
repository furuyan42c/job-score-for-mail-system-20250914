# バイト求人マッチングシステム API仕様書 詳細サマリー

## 📋 概要

本ドキュメントは、バイト求人マッチングシステムの詳細なAPI仕様を定義したOpenAPI 3.0仕様書の要約です。

### 📈 スケール要件
- **求人データ**: 10万件/日
- **ユーザー**: 1万人
- **メール生成**: 1万通/日（6セクション×40求人）
- **処理時間**: 30分以内完了

---

## 🚀 API 設計原則

### RESTful設計
- リソースベースのURL設計
- 適切なHTTPメソッドの使用
- 統一された応答形式
- エラーハンドリングの標準化

### パフォーマンス最適化
- ページネーション対応
- フィルタリング・検索機能
- 並列処理サポート
- キャッシュ戦略

### セキュリティ
- APIキー認証
- JWT認証サポート
- レート制限
- SQL インジェクション対策

---

## 📊 API カテゴリ別詳細

## 1. 求人管理API（Jobs）

### 🎯 主要機能
- **CRUD操作**: 求人の作成、読取、更新、削除
- **高度検索**: キーワード、地理的検索、スコア範囲指定
- **一括処理**: CSV/JSONによる大量データ処理（最大10万件）
- **スコアリング**: 3段階スコア（基礎・SEO・パーソナライズ）の計算
- **カテゴリ分類**: 14ニーズ×12職種カテゴリへの自動分類

### 🔧 主要エンドポイント
```
GET    /jobs                 # 求人一覧（検索・フィルタ・ページネーション）
POST   /jobs                 # 求人作成
GET    /jobs/{id}            # 求人詳細取得
PUT    /jobs/{id}            # 求人更新
DELETE /jobs/{id}            # 求人削除（論理削除）
POST   /jobs/bulk            # 一括作成/更新（CSV/JSON）
POST   /jobs/search          # 高度検索（全文検索・地理的検索）
POST   /jobs/{id}/scoring    # 個別スコア再計算
POST   /jobs/{id}/categorize # 個別カテゴリ再分類
```

### 🎨 特徴的な機能
- **地理的検索**: 緯度経度と半径による検索
- **全文検索**: タイトル、説明、会社名での横断検索
- **スコア範囲検索**: 各種スコアでの絞り込み
- **バルク処理**: バリデーション専用モード
- **リアルタイムスコアリング**: API経由での即座なスコア更新

---

## 2. ユーザー管理API（Users）

### 🎯 主要機能
- **プロファイル管理**: 基本情報、職歴、希望条件
- **行動履歴**: クリック、応募、メール開封の追跡
- **設定管理**: 通知設定、プライバシー設定
- **分析データ**: エンゲージメント、マッチング精度の可視化

### 🔧 主要エンドポイント
```
GET    /users                        # ユーザー一覧
POST   /users                        # ユーザー作成
GET    /users/{id}                   # ユーザー詳細
PUT    /users/{id}                   # ユーザー更新
DELETE /users/{id}                   # ユーザー削除
GET    /users/{id}/profile           # プロファイル取得
PUT    /users/{id}/profile           # プロファイル更新
GET    /users/{id}/behavior          # 行動履歴取得
POST   /users/{id}/behavior          # 行動記録
GET    /users/{id}/preferences       # 設定取得
PUT    /users/{id}/preferences       # 設定更新
GET    /users/{id}/analytics         # 分析データ取得
```

### 🎨 特徴的な機能
- **詳細プロファイル**: 職歴、スキル、希望条件の構造化管理
- **行動追跡**: 8種類の行動タイプ（email_open, job_apply等）
- **プライバシー制御**: トラッキング、表示設定の細かな制御
- **エンゲージメント分析**: セッション、CTR、コンバージョン率の計測

---

## 3. マッチングAPI（Matching）

### 🎯 主要機能
- **個人推薦**: リアルタイム・キャッシュ・ハイブリッド推薦
- **類似求人**: 協調フィルタリング、コンテンツベース類似性
- **バッチスコアリング**: 全求人の3段階スコア一括計算
- **マトリックス構築**: 協調フィルタリング用ユーザー×求人マトリックス

### 🔧 主要エンドポイント
```
GET    /matching/users/{id}/recommendations  # ユーザー推薦取得
POST   /matching/users/{id}/recommendations  # ユーザー推薦実行
GET    /matching/jobs/{id}/similar           # 類似求人取得
POST   /matching/scoring/batch               # バッチスコアリング
POST   /matching/categorization/batch        # バッチカテゴリ分類
POST   /matching/matrix/build                # マッチングマトリックス構築
```

### 🎨 特徴的な機能
- **6セクション推薦**: TOP5、地域、近場、特典、新着の構造化推薦
- **アルゴリズム選択**: 協調フィルタリング、コンテンツベース、ハイブリッド
- **推薦理由**: マッチング要因の説明付き推薦
- **並列処理**: 最大8ワーカーでの並列スコアリング

---

## 4. バッチ処理API（Batch）

### 🎯 主要機能
- **ジョブ管理**: 作成、監視、キャンセル、再実行
- **スケジューリング**: Cron形式での定期実行
- **進捗監視**: リアルタイム進捗とログ確認
- **エラーハンドリング**: リトライ、チェックポイント復旧

### 🔧 主要エンドポイント
```
GET    /batch/jobs                    # バッチジョブ一覧
POST   /batch/jobs                    # バッチジョブ作成
GET    /batch/jobs/{id}               # ジョブ詳細（ログ付き）
PUT    /batch/jobs/{id}               # ジョブ更新
DELETE /batch/jobs/{id}               # ジョブキャンセル
POST   /batch/jobs/{id}/restart       # ジョブ再実行
GET    /batch/schedules               # スケジュール一覧
POST   /batch/schedules               # スケジュール作成
```

### 🎨 特徴的な機能
- **8種類のジョブタイプ**: data_import, scoring, matching, email_generation等
- **優先度制御**: critical, high, normal, lowの4段階
- **チェックポイント**: 失敗時の部分復旧機能
- **リソース監視**: CPU、メモリ、ディスク使用量の追跡

---

## 5. モニタリングAPI（Monitoring）

### 🎯 主要機能
- **ヘルスチェック**: システム全体とコンポーネント別の健全性確認
- **メトリクス取得**: API、バッチ、ユーザー、マッチング精度の指標
- **アラート管理**: 重要度別アラートの作成・管理・解決
- **ログ検索**: システムログの検索・フィルタリング
- **SQLクエリ実行**: 読み取り専用での直接データ確認

### 🔧 主要エンドポイント
```
GET    /monitoring/health             # 基本ヘルスチェック
GET    /monitoring/health/detailed    # 詳細ヘルスチェック
GET    /monitoring/metrics            # システムメトリクス
GET    /monitoring/alerts             # アラート一覧
POST   /monitoring/alerts             # アラート作成
PUT    /monitoring/alerts/{id}        # アラート更新
POST   /monitoring/query              # SQLクエリ実行
GET    /monitoring/logs               # システムログ検索
```

### 🎨 特徴的な機能
- **多層ヘルスチェック**: DB、外部API、バッチ処理の個別監視
- **時系列メトリクス**: 分・時・日単位でのデータ粒度選択
- **アラート分類**: system, api, database, batch, externalの5カテゴリ
- **安全なSQL実行**: SELECT文のみ、タイムアウト、結果件数制限

---

## 6. メール生成・配信管理API（Email）

### 🎯 主要機能
- **個別メール生成**: 6セクション構成のパーソナライズドメール
- **一括メール生成**: 1万人分の並列メール生成
- **テンプレート管理**: メールテンプレートの管理
- **配信履歴**: メール送信状況と開封・クリック追跡

### 🔧 主要エンドポイント
```
GET    /email/templates               # テンプレート一覧
POST   /email/generate                # 個別メール生成
POST   /email/batch-generate          # 一括メール生成
GET    /email/deliveries              # 配信履歴取得
```

### 🎨 特徴的な機能
- **AI件名生成**: GPT-4/5 nanoによる自動件名生成
- **6セクション構成**: TOP5、地域、近場、特典、新着、おすすめの構造
- **並列生成**: 最大8ワーカーでの高速一括生成
- **配信追跡**: 送信、配信、開封、クリックの詳細追跡

---

## 🛡️ セキュリティ・認証

### 認証方式
1. **APIキー認証**: `X-API-Key` ヘッダー
2. **JWT認証**: `Authorization: Bearer <token>` ヘッダー

### セキュリティ対策
- **レート制限**: エンドポイント別の呼び出し制限
- **SQLインジェクション対策**: パラメータ化クエリ、SELECT文のみ
- **データバリデーション**: 入力値の厳密な検証
- **監査ログ**: 全API呼び出しの記録

---

## 📊 パフォーマンス仕様

### 応答時間目標
- **基本API**: 95%タイルで200ms以下
- **検索API**: 95%タイルで500ms以下
- **バッチ処理**: 30分以内完了（10万件処理）
- **メール生成**: 1万通を20分以内

### スケーラビリティ
- **並列処理**: 最大8ワーカー
- **ページネーション**: 最大1,000件/ページ
- **バルク処理**: 最大10万件/リクエスト
- **同時接続**: 1,000並列リクエスト

---

## 🔄 エラーハンドリング

### 標準エラーレスポンス
```json
{
  "error": "エラーメッセージ",
  "error_code": "VALIDATION_ERROR",
  "details": ["具体的なエラー詳細"],
  "timestamp": "2025-09-18T10:00:00Z",
  "trace_id": "req_123456789"
}
```

### HTTPステータスコード
- `200` - 成功
- `201` - 作成成功
- `202` - 非同期処理開始
- `400` - リクエストエラー
- `401` - 認証エラー
- `403` - 権限エラー
- `404` - リソース未発見
- `409` - 競合エラー
- `413` - ペイロード過大
- `429` - レート制限
- `500` - サーバーエラー
- `503` - サービス利用不可

---

## 📝 使用例・サンプルコード

### 基本的な求人検索
```bash
curl -X GET "https://api.job-matching.com/v2/jobs?keyword=アルバイト&location=東京&limit=20" \
  -H "X-API-Key: your-api-key"
```

### ユーザー推薦取得
```bash
curl -X GET "https://api.job-matching.com/v2/matching/users/123/recommendations?mode=realtime&limit=40" \
  -H "X-API-Key: your-api-key"
```

### バッチジョブ作成
```bash
curl -X POST "https://api.job-matching.com/v2/batch/jobs" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Matching Process",
    "job_type": "matching",
    "priority": "high",
    "parameters": {
      "batch_date": "2025-09-18",
      "parallel_workers": 4
    }
  }'
```

### メール一括生成
```bash
curl -X POST "https://api.job-matching.com/v2/email/batch-generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_date": "2025-09-18",
    "parallel_workers": 6,
    "options": {
      "generate_ai_subject": true,
      "max_jobs_per_section": 10
    }
  }'
```

---

## 🔧 実装考慮事項

### 技術スタック適合性
- **FastAPI**: 非同期処理、自動バリデーション、OpenAPI連携
- **Supabase**: PostgreSQL、リアルタイム機能
- **Python 3.11**: 型ヒント、パフォーマンス最適化

### 運用考慮事項
- **ログ戦略**: 構造化ログ、トレースID連携
- **監視**: ヘルスチェック、メトリクス、アラート
- **バックアップ**: データ保護、災害復旧
- **スケーリング**: 水平スケーリング対応

### 将来拡張性
- **バージョニング**: `/v2` URL構造
- **新機能追加**: 既存APIとの互換性維持
- **外部連携**: Webhook、第三者API統合
- **AI機能強化**: GPT-5対応、新アルゴリズム追加

---

## 📚 関連ドキュメント

- **OpenAPI仕様書**: `/contracts/detailed-api-spec.yaml`
- **データモデル**: `/data-model.md`
- **実装計画**: `/plan.md`
- **システム仕様書**: `/comprehensive_integrated_specification_final_v5.0.md`

---

*このAPI仕様書は、バイト求人マッチングシステムの包括的な機能を提供し、スケーラブルで保守性の高いシステム構築を支援します。*