# 🚀 最適化版実行プロンプト - Job Matching System

> ⚠️ **非推奨**: このファイルは古いバージョンです。  
> 📌 **最新版を使用してください**: [`ULTIMATE-IMPLEMENTATION-GUIDE.md`](./ULTIMATE-IMPLEMENTATION-GUIDE.md)

---

**作成日**: 2025-09-17  
**バージョン**: 3.0（エージェント並列実行対応）  
**推定時間**: 28-36時間（4日分割実行）

---

## 📋 Day 1: 準備とデータ基盤（8時間）

### Step 1: 手動準備（1時間）
```markdown
【必須手動作業チェックリスト】
□ Supabaseプロジェクト作成（https://supabase.com）
□ API KEY取得して.envに記載
□ OpenAI API KEY取得（GPT-5 nano利用）
□ Python 3.11環境構築
□ Node.js 20 LTS環境構築

完了後、以下を確認：
- SUPABASE_URL
- SUPABASE_ANON_KEY  
- OPENAI_API_KEY
```

### Step 2: DB構築プロンプト（Claude Code: 2時間）
```markdown
=========================================
Day 1 - Phase 1: データベース構築
=========================================

/sc:load

specs/001-job-matching-system/data-model.mdを読み込んで、
以下のSQLファイルを生成してください：

database/
├── migrations/
│   ├── 001_create_tables.sql     # 全テーブル定義
│   ├── 002_create_indexes.sql    # インデックス
│   └── 003_create_functions.sql  # ストアドファンクション
├── seeds/
│   └── 001_master_data.sql       # マスターデータ
└── setup_supabase.md             # 実行手順書

--serena --seq

生成後、setup_supabase.mdの手順を表示してください。
```

### Step 3: バックエンド基礎（Claude Code: 5時間）
```markdown
=========================================
Day 1 - Phase 2: バックエンド基礎実装
=========================================

Task toolで以下のエージェントを並列実行：

【並列グループA】
1. backend-architect: 
   - FastAPIプロジェクト構造設計
   - backend/app/main.py, config.py作成
   - ルーター構成設計

2. python-expert:
   - Pydanticモデル実装（backend/app/models/）
   - データバリデーション設計
   - 型安全性確保

3. requirements-analyst:
   - requirements.txt生成
   - 依存関係の最適化
   - バージョン管理

TodoWriteでタスク管理しながら、
backend/ディレクトリ全体を構築してください。

/sc:checkpoint "Day1完了"
```

---

## 📋 Day 2: コア機能実装（8時間）

### Step 4: スコアリングエンジン（Claude Code: 4時間）
```markdown
=========================================
Day 2 - Phase 3: スコアリングエンジン
=========================================

/sc:load  # 前日の続きから

specs/001-job-matching-system/answers.mdを参照して、
Task toolで以下を並列実行：

【並列グループB】
1. python-expert:
   backend/app/services/scoring_engine.py実装
   - calculate_base_score（fee重視: 0-5000円）
   - calculate_seo_score（マッチング）
   - calculate_personal_score（履歴ベース）

2. performance-engineer:
   - NumPy/Pandasでベクトル化
   - メモリ効率最適化
   - 処理時間測定

3. quality-engineer:
   tests/test_scoring.py作成
   - 各スコア関数のユニットテスト
   - エッジケース検証

目標: 1ユーザー180ms以内で処理
```

### Step 5: マッチング＆バッチ（Claude Code: 4時間）
```markdown
=========================================
Day 2 - Phase 3.2: マッチング実装
=========================================

Task toolで並列実行：

【並列グループC】
1. backend-architect + python-expert:
   backend/app/services/job_selector.py
   - 10万件から40件選定アルゴリズム
   - カテゴリ分散考慮

2. backend-architect:
   backend/app/batch/daily_batch.py
   - APSchedulerでスケジューリング
   - 並列処理制御

3. quality-engineer:
   tests/integration/test_pipeline.py
   - E2Eテスト作成

/sc:checkpoint "Day2完了"
```

---

## 📋 Day 3: フロントエンド＆統合（8時間）

### Step 6: UI実装（Claude Code: 4時間）
```markdown
=========================================
Day 3 - Phase 4: フロントエンド
=========================================

Task toolで並列実行：

【並列グループD】
1. frontend-architect + Magic MCP:
   frontend/app/monitoring/page.tsx
   - SQL実行画面（最優先）
   - リアルタイム結果表示
   - CSVエクスポート

2. frontend-architect:
   frontend/app/dashboard/page.tsx
   - バッチ状況表示
   - エラーログビューア

3. frontend-architect:
   frontend/lib/api/client.ts
   - TypeScript型定義
   - Supabaseクライアント

--magic --c7 --parallel
```

### Step 7: 統合テスト（Claude Code: 4時間）
```markdown
=========================================
Day 3 - Phase 5: 統合テスト
=========================================

Task toolで並列実行：

【並列グループE】
1. quality-engineer + Playwright MCP:
   - E2Eテスト実装
   - ブラウザ自動テスト

2. performance-engineer:
   - 負荷テスト
   - 30分以内完了検証

3. security-engineer:
   - セキュリティ監査
   - SQLインジェクション対策確認

/verify-and-pr 001-job-matching --comprehensive --play

/sc:checkpoint "Day3完了"
```

---

## 📋 Day 4: 最適化＆本番準備（6時間）

### Step 8: 最適化（Claude Code: 3時間）
```markdown
=========================================
Day 4 - Phase 6: 最適化
=========================================

Task toolで並列実行：

【並列グループF】
1. performance-engineer:
   /sc:optimize --target performance
   - クエリ最適化
   - キャッシュ戦略

2. security-engineer:
   /sc:optimize --target security
   - 認証実装
   - データ暗号化

3. refactoring-expert:
   - コード品質向上
   - 技術負債解消
```

### Step 9: ビジネス検証（Claude Code: 3時間）
```markdown
=========================================
Day 4 - ビジネス価値検証
=========================================

/sc:business-panel @specs/001-job-matching-system/spec.md --mode discussion

以下の観点で分析：
- ROI評価
- スケーラビリティ
- 運用コスト
- ビジネスインパクト

最終ドキュメント生成：
- README.md
- DEPLOYMENT.md
- OPERATION.md

/sc:save
git commit -m "feat: Job Matching System v1.0完成"
```

---

## 🚨 エラー時の対処プロンプト

### データベース接続エラー
```markdown
root-cause-analystで原因分析：
- Supabase接続情報確認
- 環境変数チェック
- ネットワーク設定確認
```

### パフォーマンス問題
```markdown
performance-engineerで最適化：
- ボトルネック特定
- インデックス追加
- クエリ改善
```

### テスト失敗
```markdown
quality-engineerで修正：
- 失敗原因分析
- テストケース修正
- リグレッションテスト
```

---

## ✅ 実行前チェックリスト

### 環境準備
- [ ] Supabaseプロジェクト作成済み
- [ ] API KEY設定済み（.env）
- [ ] Python/Node.js環境構築済み
- [ ] Git初期化済み

### 仕様理解
- [ ] comprehensive_integrated_specification_final_v5.0.md読み込み
- [ ] data-model.md理解
- [ ] answers.md確認

### 実行計画
- [ ] 4日間の時間確保
- [ ] 各Day後の動作確認時間
- [ ] エラー対処の余裕時間

---

## 🎯 Quick Start（今すぐ開始）

```markdown
# このプロンプトをコピーして実行
/sc:load

Job Matching Systemの実装を開始します。
OPTIMIZED-EXECUTION-PROMPT.mdのDay 1から順番に実行してください。

Task toolでエージェントを並列実行し、
TodoWriteで進捗管理しながら効率的に開発を進めます。

まずDay 1のStep 2（DB構築）から開始してください。
```

---

*エージェント並列実行により、実装時間を大幅に短縮できます*
*必ず手動準備を完了してから実装を開始してください*