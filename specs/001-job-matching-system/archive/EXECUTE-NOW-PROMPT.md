# 🚀 即実行用プロンプト - Job Matching System完全実装

> ⚠️ **非推奨**: このファイルは古いバージョンです。  
> 📌 **最新版を使用してください**: [`ULTIMATE-IMPLEMENTATION-GUIDE.md`](./ULTIMATE-IMPLEMENTATION-GUIDE.md)

---

**このファイルの使い方**: 
1. 以下のプロンプトブロックをコピー
2. Claude Codeに貼り付けて実行
3. 自動的に全工程が開始されます

---

## 📋 COPY & EXECUTE: 完全自動実装プロンプト

```markdown
=========================================
🎯 Job Matching System 完全実装を開始
=========================================

プロジェクトパス: /Users/naoki/000_PROJECT/job-score-for-mail-system-20250914/
仕様書パス: specs/001-job-matching-system/

【実装概要】
10万件のバイト求人から1万人のユーザーに最適な40件を毎日選定し、
6セクション構成のパーソナライズメールを生成するシステムを構築します。

=========================================
PHASE 0: 初期化とコンテキスト読み込み
=========================================

/sc:load

以下の仕様書を全て読み込んで、システムの完全な理解を構築してください：
1. specs/001-job-matching-system/comprehensive_integrated_specification_final_v5.0.md
2. specs/001-job-matching-system/data-model.md
3. specs/001-job-matching-system/answers.md
4. specs/001-job-matching-system/implementation-workflow.md
--think-hard --seq

理解した内容に基づいて、実装の実現可能性とリスクを評価してください。

=========================================
PHASE 1: 仕様確定と計画策定（15分）
=========================================

# 1.1 仕様の最終化
/specify --think-hard --ultrathink
タイトル: バイト求人マッチングシステム
要件:
- 10万件×1万人のスケール処理
- 3段階スコアリング（基礎・SEO・パーソナライズ）
- 6セクション構成メール生成
- 30分以内のバッチ処理
- リアルタイムSQL実行画面
技術: FastAPI, Next.js 14, Supabase, GPT-5 nano

# 1.2 実装計画の生成
/plan --optimize-parallel --research-heavy --c7
入力: 生成されたspec.md
並列化方針: データ基盤、バックエンド、フロントエンドの並列開発

# 1.3 タスク分解
/tasks --parallel-optimization --mcp-strategy --methodology=tdd
入力: 生成されたplan.md
出力形式: 並列実行可能なタスクグループとして整理

TodoWriteで全タスクの進捗管理を開始してください。

=========================================
PHASE 2: データ基盤構築（4-6時間）
=========================================

# 2.1 プロジェクト構造作成
以下のディレクトリ構造を作成：
furuya-job-matching-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── services/
│   │   ├── routers/
│   │   └── batch/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   └── package.json
└── database/
    └── migrations/
--serena

# 2.2 Supabaseデータベース構築
specs/001-job-matching-system/data-model.mdに基づいて、
以下のテーブルを並列で作成：
- jobs（100+フィールド）
- users
- user_profiles
- user_job_mapping
- daily_job_picks
- daily_email_queue
- 各種マスターテーブル
--serena --parallel

適切なインデックスを作成してパフォーマンスを最適化。

# 2.3 Pydanticモデル実装
backend/app/models/に全データモデルを実装：
- jobs.py
- users.py
- scoring.py
- email.py
--serena --parallel

=========================================
PHASE 3: コア機能実装（8-10時間）
=========================================

# 3.1 スコアリングエンジン実装
backend/app/services/scoring_engine.pyを作成：

specs/001-job-matching-system/answers.mdを参照して、
以下の3段階スコアリングを実装：

1. 基礎スコア（fee重視）
   - fee（応募促進費用）: 0-5000円を正規化
   - 給与の魅力度
   - 勤務地アクセス

2. SEOスコア（マッチング）
   - 地域マッチング
   - 職種マッチング
   - 勤務条件適合

3. パーソナライズスコア
   - ユーザー行動履歴
   - クリック率予測
   - 応募確率推定
--seq --think-hard

# 3.2 最適化選定アルゴリズム
backend/app/services/job_selector.pyを実装：
- 10万件×1万人のマトリックス処理
- 上位40件の効率的選定
- カテゴリ分散の考慮
--seq --parallel

# 3.3 メール生成サービス
backend/app/services/email_generator.pyを実装：
6セクション構成（specs/001-job-matching-system/comprehensive_integrated_specification_final_v5.0.mdの
セクション7参照）
- GPT-5 nano統合（件名生成）
- HTMLテンプレート生成
--magic --c7

# 3.4 バッチ処理パイプライン
backend/app/batch/daily_batch.pyを実装：
- APSchedulerによるスケジューリング
- 並列処理制御
- エラーハンドリング
--seq --serena

=========================================
PHASE 4: フロントエンド構築（6-8時間）
=========================================

以下のコンポーネントを並列で開発：

# 4.1 SQL実行画面（最優先）
frontend/app/monitoring/page.tsxを作成：
- リアルタイムSQL実行インターフェース
- 結果のテーブル表示
- CSVエクスポート機能
--magic --c7

# 4.2 管理ダッシュボード
frontend/app/dashboard/page.tsxを作成：
- バッチ処理状況
- エラーログ表示
- パフォーマンスメトリクス
--magic --parallel

# 4.3 APIクライアント
frontend/lib/api/client.tsを実装：
- TypeScript型定義
- エラーハンドリング
- 自動リトライ
--c7 --serena

=========================================
PHASE 5: 統合・検証（4-6時間）
=========================================

# 5.1 統合テスト作成
tests/integration/にE2Eテストを作成：
- 全処理フローのテスト
- 30分以内完了の検証
- 10万件×1万人のスケールテスト
--play --seq

# 5.2 パフォーマンステスト
- クエリ最適化
- インデックス調整
- 並列度の最適化
--seq --think-hard

# 5.3 品質検証
/verify-and-pr 001-job-matching-system --comprehensive --play
全テストの実行と品質レポート生成

=========================================
PHASE 6: 最適化と本番準備（4時間）
=========================================

# 6.1 システム最適化
/sc:optimize --target performance
/sc:optimize --target security

# 6.2 ビジネス価値検証
/sc:business-panel @specs/001-job-matching-system/spec.md --mode discussion

# 6.3 最終確認
- 全機能の動作確認
- ドキュメント整備
- デプロイ準備

/sc:checkpoint "本番準備完了"
/sc:save

=========================================
実装管理ルール
=========================================

1. TodoWriteで全タスクを管理
2. 30分ごとに/sc:checkpointで進捗保存
3. 各フェーズ完了時にgit commit
4. 並列実行可能なタスクは積極的に並列化
5. MCP活用: --seq --serena --magic --c7 --play

開始してください。
```

---

## 🎯 簡易版: 最速MVP実装（8時間）

```markdown
=========================================
MVP版 Job Matching System 実装
=========================================

/sc:load

# Step 1: 既存仕様の理解（30分）
specs/001-job-matching-system/の全仕様書を読み込み --seq --think-hard

# Step 2: MVP計画（30分）
/plan --optimize-parallel
MVP範囲: 
- 基本的なスコアリング
- 1000件×100人でのテスト
- シンプルなSQL実行画面

# Step 3: 基本実装（6時間）
以下を並列で実装：

Group A: バックエンド
- FastAPIセットアップ
- 基礎スコアリング実装
- 簡易バッチ処理
--serena --seq

Group B: フロントエンド  
- SQL実行画面
- 結果表示
--magic --c7

Group C: データベース
- Supabase基本テーブル
- サンプルデータ投入
--serena

# Step 4: 検証（1時間）
/verify-and-pr 001-job-matching-mvp --simple

/sc:save

完了！
```

---

## ⚡ 緊急対応版: 特定機能のみ実装（2時間）

```markdown
=========================================
SQL実行画面のみ緊急実装
=========================================

/sc:load

# SQL実行画面の実装
frontend/app/monitoring/にSQL実行画面を作成 --magic --c7
要件:
- Supabaseへの接続
- SQL実行
- 結果表示
- エラーハンドリング

バックエンドAPIエンドポイントを作成 --serena
- POST /api/execute-sql
- セキュリティ対策

テストと検証 --play

git commit -m "feat: SQL実行画面の実装"
/sc:save
```

---

## 📝 注意事項

1. **必ず最初に/sc:loadを実行**してコンテキストを読み込む
2. **TodoWriteで進捗を常に管理**する
3. **30分ごとに/sc:checkpoint**で状態を保存
4. **並列実行可能なタスクは--parallelフラグ**を使用
5. **MCPを積極的に活用**して効率化

---

## 🆘 問題発生時の対処

```markdown
# エラーが発生した場合
エラーの詳細を分析 --seq --think-hard
根本原因を特定して修正案を提示

# パフォーマンス問題
/sc:analyze . --focus performance
ボトルネックを特定して最適化

# 仕様の不明点
specs/001-job-matching-system/asks.mdとanswers.mdを再確認
不明な点は仮定を置いて進め、後で調整
```

---

*このプロンプトをコピーして、Claude Codeで即座に実行開始！*
*問題があれば implementation-workflow-prompt.md を参照*