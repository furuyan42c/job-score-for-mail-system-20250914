# 🚀 Job Matching System 実装ワークフロー完全ガイド v3.0

**作成日**: 2025-09-17  
**対象システム**: バイト求人マッチングシステム（10万件×1万人）  
**ベース**: Super Claude Framework v2.3 + Spec-Kit  
**目的**: 仕様書から本番デプロイまでの完全自動化実装

---

## 📊 プロジェクト状況サマリー

### 既存資産
```yaml
仕様書:
  - comprehensive_integrated_specification_final_v5.0.md  # 統合仕様
  - data-model.md                                        # データモデル定義
  - 20250904_er_complete_v2.0.mmd                       # ERD
  - answers.md / asks.md                                # Q&A形式の実装詳細
  - implementation-workflow.md                          # 実装フロー

技術スタック:
  backend: Python 3.11 + FastAPI + Supabase
  frontend: Next.js 14 + TypeScript 5
  ai: GPT-5 nano（メール件名生成）
  batch: APScheduler
  monitoring: SQL実行画面（リアルタイム）
```

---

## 🎯 実装フローの全体像（推定所要時間: 28-36時間）

### Phase構成
1. **Phase 0**: 初期設定＆環境構築（2時間）
2. **Phase 1**: データ基盤構築（4-6時間）  
3. **Phase 2**: コア機能実装（8-10時間）
4. **Phase 3**: フロントエンド構築（6-8時間）
5. **Phase 4**: 統合・検証（4-6時間）
6. **Phase 5**: 最適化・本番準備（4時間）

---

## 📝 実行プロンプト集

### 🚦 STEP 0: プロジェクト初期化（すぐに実行）

```markdown
# セッション開始とコンテキスト読み込み
/sc:load

# 既存仕様書の深層分析と統合
以下の仕様書を読み込んで、Job Matching Systemの全体像を理解してください：
- specs/001-job-matching-system/comprehensive_integrated_specification_final_v5.0.md
- specs/001-job-matching-system/data-model.md  
- specs/001-job-matching-system/answers.md
--think-hard --seq

理解した内容を基に、実装可能性とリスクを評価してください。
```

### 🏗️ STEP 1: 仕様の最終化と計画策定

```markdown
# 仕様の最終確認と補完
/specify --think-hard --ultrathink
タイトル: バイト求人マッチングシステム
概要: 毎日10万件の求人から1万人に最適な40件を選定しメール生成
要件:
- 3段階スコアリング（基礎・SEO・パーソナライズ）
- 6セクション構成メール生成  
- 30分以内のバッチ処理完了
- リアルタイムSQL実行画面
参照: specs/001-job-matching-system/comprehensive_integrated_specification_final_v5.0.md

# 実装計画の策定（並列処理最適化）
/plan --optimize-parallel --research-heavy --c7
入力: specs/001-job-matching-system/spec.md
フレームワーク: FastAPI, Next.js 14, Supabase
制約: 30分以内処理、10万件×1万人スケール

# タスク分解（MCP戦略付き）
/tasks --parallel-optimization --mcp-strategy --methodology=tdd
入力: specs/001-job-matching-system/plan.md
並列化方針:
- Group A: データ基盤（DB、モデル、インポート）
- Group B: コア機能（スコアリング、マッチング、メール生成）
- Group C: フロントエンド（モニタリング画面、管理画面）
```

### 💾 STEP 2: データ基盤構築

```markdown
# Phase 1: データベース構築（並列実行可能）
specs/001-job-matching-system/tasks.mdのPhase 1タスクを実装してください。

## 2.1 Supabaseセットアップ
以下を並列で実行してください：
1. Supabaseプロジェクト作成と接続設定
2. data-model.mdに基づいたテーブル定義（14テーブル）
3. インデックス作成（パフォーマンス最適化）
--serena --parallel

## 2.2 データモデル実装
backend/app/models/にPydanticモデルを作成：
- jobs.py（100+フィールド）
- users.py
- user_job_mapping.py
- daily_job_picks.py
- daily_email_queue.py
--seq --serena

## 2.3 データインポート機能
backend/app/batch/csv_importer.pyを実装：
- 10万件CSVの高速インポート
- バルクインサート最適化
- エラーハンドリング
--think-hard --serena
```

### ⚙️ STEP 3: コア機能実装（最重要）

```markdown
# Phase 2: スコアリングとマッチング実装
specs/001-job-matching-system/tasks.mdのPhase 2を実装

## 3.1 スコアリングエンジン（詳細はanswers.md参照）
backend/app/services/scoring_engine.pyを実装：

### 基礎スコア計算（fee重視）
```python
def calculate_base_score(job):
    # fee（応募促進費用）を正規化
    fee_score = job.fee / 5000 * 0.5  # 最大50点
    # その他の要素...
```

### SEOスコア計算
```python  
def calculate_seo_score(job, user):
    # 地域マッチング、職種マッチング等
```

### パーソナライズスコア
```python
def calculate_personal_score(job, user):
    # ユーザー行動履歴ベース
```

--seq --think-hard

## 3.2 最適化選定アルゴリズム
backend/app/services/job_selector.pyを実装：
- 各ユーザー×10万求人のスコア計算
- 上位40件の選定ロジック
- カテゴリ分散の考慮
--seq --parallel

## 3.3 メール生成サービス
backend/app/services/email_generator.pyを実装：
- 6セクション構成
- GPT-5 nano統合（件名生成）
- HTMLテンプレート生成
--magic --c7
```

### 🖥️ STEP 4: フロントエンド構築

```markdown
# Phase 3: モニタリング画面実装
specs/001-job-matching-system/tasks.mdのPhase 3を並列実装

## 4.1 SQL実行画面（最優先）
frontend/app/monitoring/にNext.jsページを作成：
- リアルタイムSQL実行
- 結果のテーブル表示
- エクスポート機能
--magic --c7 --parallel

## 4.2 ダッシュボード
frontend/app/dashboard/に管理画面を実装：
- バッチ実行状況
- エラーログ
- パフォーマンスメトリクス
--magic --parallel

## 4.3 APIクライアント
frontend/lib/api/にAPIクライアントを実装：
- FastAPIとの通信
- エラーハンドリング
- 型安全性（TypeScript）
--c7 --serena
```

### ✅ STEP 5: 統合・検証

```markdown
# Phase 4: システム統合とテスト
TodoWriteでテスト進捗を管理しながら実施

## 5.1 統合テスト
tests/integration/に統合テストを作成：
- バッチ処理のE2Eテスト
- 30分以内完了の検証
- 10万件×1万人のスケールテスト
--play --seq

## 5.2 パフォーマンステスト
- データベースクエリ最適化
- インデックス調整
- 並列処理の効率測定
--seq --think-hard

## 5.3 品質検証
/verify-and-pr 001-job-matching-system --comprehensive --play
- 全テスト実行
- カバレッジ確認
- セキュリティスキャン
```

### 🚀 STEP 6: 最適化と本番準備

```markdown
# Phase 5: 本番デプロイ準備

## 6.1 パフォーマンス最適化
/sc:optimize --target performance
- クエリ最適化
- キャッシュ戦略
- 非同期処理の活用

## 6.2 セキュリティ強化  
/sc:optimize --target security
- 認証・認可
- SQLインジェクション対策
- データ暗号化

## 6.3 ビジネス価値検証
/sc:business-panel @specs/001-job-matching-system/spec.md --mode discussion
- ROI分析
- スケーラビリティ評価
- 運用コスト試算

## 6.4 最終チェックと保存
/sc:checkpoint "本番準備完了"
/sc:save
```

---

## 🔥 並列実行戦略（効率化の鍵）

### 並列実行可能なタスクグループ

```yaml
Group A（データ基盤）:  # 開始可能
  - Supabaseセットアップ
  - テーブル作成
  - Pydanticモデル定義
  MCP: --serena --parallel

Group B（バックエンド）: # Group A完了後
  - スコアリングエンジン
  - 選定アルゴリズム  
  - APIエンドポイント
  MCP: --seq --serena --parallel

Group C（フロントエンド）: # 独立実行可能
  - SQL実行画面
  - ダッシュボード
  - コンポーネント
  MCP: --magic --c7 --parallel

Group D（バッチ処理）: # Group B完了後
  - CSVインポート
  - スケジューラ
  - エラーハンドリング
  MCP: --seq --serena
```

### MCP活用マトリクス

| タスク種別 | 推奨MCP | 効果 | 並列可能 |
|-----------|---------|------|----------|
| 深層分析 | Sequential | 複雑なロジック理解 | ❌ |
| UI生成 | Magic | 高品質コンポーネント | ✅ |
| コード探索 | Serena | シンボル操作 | ✅ |
| ドキュメント | Context7 | 公式パターン準拠 | ✅ |
| E2Eテスト | Playwright | 実ブラウザ検証 | ✅ |

---

## 📊 進捗管理とチェックポイント

### タスク管理コマンド
```markdown
# タスク開始時
TodoWriteで以下を管理：
- [ ] Phase 0: 環境構築
- [ ] Phase 1: データ基盤  
- [ ] Phase 2: コア機能
- [ ] Phase 3: フロントエンド
- [ ] Phase 4: 統合・検証
- [ ] Phase 5: 最適化

# 30分ごとのチェックポイント
/sc:checkpoint "Phase X 進行中"

# フェーズ完了時
git commit -m "feat(phase-X): 完了内容"
/sc:save
```

### 品質ゲート
```yaml
各フェーズ完了条件:
  Phase 1: 全テーブル作成、インポート成功
  Phase 2: スコアリング精度90%以上
  Phase 3: UI/UXテスト合格
  Phase 4: 30分以内処理確認
  Phase 5: 本番環境ready
```

---

## ⚡ Quick Start（今すぐ開始）

```bash
# 1. このプロンプトをコピー
# 2. Claude Codeで実行

/sc:load
仕様書群を読み込んで、Job Matching Systemの実装を開始します。
specs/001-job-matching-system/にある全仕様書を参照し、
このimplementation-workflow-prompt.mdに従って段階的に実装を進めてください。

最初にPhase 0の環境構築から開始し、TodoWriteで進捗管理しながら、
--think-hard --seq --serena --magic --c7 --playを活用して
効率的に開発を進めます。

並列実行可能なタスクは積極的に並列化し、30分ごとに/sc:checkpointで
進捗を保存してください。
```

---

## 🆘 トラブルシューティング

### よくある問題と対処法

```markdown
Q: Supabase接続エラー
A: .env.localにSUPABASE_URL, SUPABASE_ANON_KEYを設定

Q: 処理が30分を超える
A: インデックス確認、バルクインサート最適化、並列度調整

Q: メモリ不足
A: チャンク処理、ストリーミング、ページネーション実装

Q: テスト失敗
A: モックデータ確認、非同期処理のawait確認、タイムアウト調整
```

---

## 📝 補足情報

### 非推奨事項
- Morphllm MCPは使用しない（v2.3で廃止）
- 順次実行のみの実装（必ず並列化を検討）
- テスト無しでのマージ（必ず品質検証）

### 推奨事項
- 早期からTodoWrite活用
- 30分ごとの進捗保存
- MCP積極活用（特にSequential, Serena, Magic）
- ビジネス価値の定期確認

---

*このワークフローはSuper Claude Framework v2.3準拠で作成されています*
*問題や質問は https://github.com/anthropics/claude-code/issues へ*