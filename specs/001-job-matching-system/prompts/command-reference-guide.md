# 📚 Job Matching System - コマンドリファレンス＆実行ガイド

**作成日**: 2025-09-17  
**Framework**: Super Claude v2.3 + Spec-Kit  
**目的**: 効率的な開発のためのコマンド一覧と最適な使用方法

---

## 🎯 コマンド体系図

```mermaid
graph TB
    A[開始] --> B[/sc:load]
    B --> C{仕様段階}
    C -->|新規| D[/specify --think-hard]
    C -->|既存| E[仕様書読込]
    D --> F[/plan --optimize-parallel]
    E --> F
    F --> G[/tasks --mcp-strategy]
    G --> H[TodoWrite実装]
    H --> I{検証}
    I -->|品質| J[/verify-and-pr]
    I -->|ビジネス| K[/sc:business-panel]
    J --> L[/sc:save]
    K --> L
```

---

## 📋 コマンド詳細リファレンス

### 🔧 基本コマンド（Spec-Kit）

| コマンド | 用途 | 推奨フラグ | 出力 |
|---------|------|-----------|------|
| `/specify` | 仕様書生成 | `--think-hard --ultrathink` | spec.md |
| `/plan` | 実装計画 | `--optimize-parallel --research-heavy` | plan.md, research.md |
| `/tasks` | タスク分解 | `--parallel-optimization --mcp-strategy` | tasks.md |
| `/verify-and-pr` | 品質検証 | `--comprehensive --play` | review.md, PR作成 |

### 🚀 Super Claudeコマンド

| コマンド | 用途 | 使用タイミング | 効果 |
|---------|------|---------------|------|
| `/sc:load` | セッション開始 | 作業開始時 | コンテキスト復元 |
| `/sc:save` | セッション保存 | 作業終了時 | 状態永続化 |
| `/sc:checkpoint` | チェックポイント | 30分ごと | 進捗保存 |
| `/sc:business-panel` | ビジネス分析 | 重要機能完了時 | 価値検証 |
| `/sc:optimize` | 最適化実行 | Phase 5 | 性能改善 |
| `/sc:analyze` | 包括的分析 | デバッグ時 | 問題特定 |

### 🤖 MCP活用フラグ

| フラグ | MCP Server | 最適な用途 | 並列可能 |
|--------|-----------|-----------|----------|
| `--seq` | Sequential | 複雑な分析・推論 | ❌ |
| `--serena` | Serena | シンボル操作・探索 | ✅ |
| `--magic` | Magic | UI/UXコンポーネント | ✅ |
| `--c7` | Context7 | 公式ドキュメント参照 | ✅ |
| `--play` | Playwright | E2Eテスト | ✅ |
| `--all-mcp` | 全サーバー | 複雑なタスク | ー |

---

## 🔄 実行フローパターン

### Pattern 1: 新規開発（仕様から）
```bash
# フル仕様駆動開発
/sc:load
/specify --think-hard --ultrathink
/plan --optimize-parallel --research-heavy --c7
/tasks --parallel-optimization --mcp-strategy --methodology=tdd
TodoWriteで実装管理
/verify-and-pr <slug> --comprehensive --play
/sc:business-panel @spec.md
/sc:save
```

### Pattern 2: 既存仕様からの実装
```bash
# 既存仕様書ベース
/sc:load
仕様書群を読み込み --seq --think-hard
/plan --optimize-parallel  # 既存仕様を入力
/tasks --mcp-strategy
TodoWriteで実装管理 --serena --magic --c7
/verify-and-pr <slug> --comprehensive
/sc:save
```

### Pattern 3: 緊急修正・ホットフィックス
```bash
# 最小限の修正フロー
/sc:load
問題分析 --seq
修正実装 --serena
/verify-and-pr <slug> --simple
git commit -m "hotfix: 説明"
/sc:save
```

### Pattern 4: パフォーマンス最適化
```bash
# 最適化特化フロー
/sc:load
/sc:analyze . --focus performance
/sc:optimize --target performance
並列化実装 --parallel --delegate
ベンチマーク実行 --seq
/verify-and-pr <slug> --performance
/sc:save
```

---

## 🎮 TodoWrite活用ガイド

### 基本的な使い方
```markdown
# タスク開始時
TodoWriteで以下のタスクを管理：
1. データベース構築
2. APIエンドポイント実装
3. フロントエンド開発
4. テスト作成
5. ドキュメント更新

# 実装中の更新
タスク1を完了、タスク2を開始

# 並列実行の明示
タスク2,3,4を並列で開始 --parallel
```

### 階層的タスク管理
```yaml
Plan:
  - Phase 1: データ基盤
    - Task 1.1: Supabase設定
    - Task 1.2: テーブル作成
    - Task 1.3: モデル定義
  - Phase 2: コア機能
    - Task 2.1: スコアリング
    - Task 2.2: マッチング
```

---

## 💡 効率化のベストプラクティス

### 1. 並列実行の最大化
```markdown
# Good: 並列実行
以下を並列で実行 --parallel:
- frontend/のUI開発 --magic
- backend/のAPI開発 --serena
- tests/のテスト作成 --play

# Bad: 順次実行
frontend開発を実行
次にbackend開発を実行
最後にテスト作成を実行
```

### 2. MCP最適活用
```markdown
# タスクに応じた最適なMCP選択
UI開発: --magic --c7
複雑なロジック: --seq --think-hard
コード探索・編集: --serena
テスト: --play
ドキュメント参照: --c7
```

### 3. チェックポイント戦略
```markdown
# 定期保存
30分ごと: /sc:checkpoint "進捗説明"
Phase完了: git commit + /sc:save
重要機能: /sc:business-panel

# リスク管理
実験的実装前: git stash または新ブランチ
大規模変更前: /sc:checkpoint "変更前の状態"
```

---

## 🛠️ トラブルシューティングコマンド

### デバッグ＆分析
```bash
# エラー分析
エラーの根本原因を分析 --seq --think-hard

# コード探索
関連コードを検索 --serena
シンボル定義を確認 --serena

# パフォーマンス分析
/sc:analyze . --focus performance
ボトルネック特定 --seq
```

### 修復＆回復
```bash
# セッション回復
/sc:load  # 前回の状態から再開

# Git操作
git status
git diff
git stash  # 一時保存
git checkout -b fix/issue  # 修正ブランチ
```

---

## 📊 コマンド組み合わせ例

### 完全自動化フロー
```bash
# 1行で全工程実行（概念）
/specify --think-hard && /plan --optimize-parallel && \
/tasks --mcp-strategy && 実装 && /verify-and-pr <slug>
```

### 段階的品質向上
```bash
# Step 1: MVP実装
/tasks --methodology=mvp
基本実装 --fast

# Step 2: 品質向上
/tasks --methodology=tdd
テスト追加 --play

# Step 3: 最適化
/sc:optimize --target all
```

---

## 📝 Job Matching System専用コマンド

### データ基盤構築
```bash
# Supabase初期化
Supabaseプロジェクトを作成し、data-model.mdのテーブルを構築 --serena
インデックスとトリガーを最適化 --seq

# モデル定義
backend/app/models/に全Pydanticモデルを生成 --serena --parallel
```

### スコアリング実装
```bash
# 3段階スコアリング
answers.mdのスコアリングロジックを実装 --seq --think-hard
テストケースを作成 --play
パフォーマンステスト --seq
```

### フロントエンド
```bash
# SQL実行画面
frontend/app/monitoring/にSQL実行画面を作成 --magic --c7
リアルタイム更新機能を追加 --magic
```

---

## 🚦 実行優先順位

### Critical（必須）
1. `/sc:load` - セッション開始
2. 仕様理解（既存または新規）
3. TodoWrite - タスク管理
4. `/verify-and-pr` - 品質検証
5. `/sc:save` - セッション保存

### Important（推奨）
- `--think-hard` - 複雑な問題
- `--parallel` - 並列実行
- `/sc:checkpoint` - 定期保存
- MCPフラグ - 効率化

### Nice to Have（オプション）
- `/sc:business-panel` - ビジネス分析
- `/sc:optimize` - 最適化
- `--ultrathink` - 超深層分析

---

## 📌 Quick Reference Card

```yaml
# 必須コマンドセット
start: /sc:load
spec: /specify --think-hard
plan: /plan --optimize-parallel  
tasks: /tasks --mcp-strategy
track: TodoWrite
test: /verify-and-pr
save: /sc:save

# MCP選択ガイド
analysis: --seq
ui: --magic
code: --serena
docs: --c7
test: --play

# 並列化指針
可能: UI, テスト, ドキュメント
不可: 深層分析, 依存関係あり
推奨: 独立タスクは常に並列
```

---

*このガイドはSuper Claude Framework v2.3準拠*
*継続的に更新・改善されます*