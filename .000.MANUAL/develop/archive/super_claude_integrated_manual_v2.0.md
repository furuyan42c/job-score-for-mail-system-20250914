# 🚀 次世代AI開発ワークフロー完全マニュアル v2.1
## Spec-Kit × Claude Code × Codex + Super Claude Framework

> **仕様駆動開発の究極形**: 要件定義から実装・検証まで、AIエージェントが協調する完全自動化ワークフロー

## 📊 ワークフロー概要

```mermaid
graph LR
    A[🎯 要件定義] -->|仕様化| B[📝 Spec-Kit]
    B -->|計画| C[📋 実装計画]
    C -->|タスク化| D[✅ タスク分解]
    D -->|実装| E[🔨 Codex実装]
    E -->|検証| F[🔍 品質保証]
    F -->|完了| G[🚀 リリース]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#fff3e0
    style G fill:#e1f5fe
```

### 🎯 このマニュアルの価値
- **開発速度3倍**: 仕様から実装まで完全自動化
- **品質保証**: 各フェーズでの自動検証
- **チーム協調**: AI-人間-AIの最適な役割分担
- **継続的改善**: セッション管理による学習と最適化

## 📋 目次
- [メインワークフロー](#メインワークフロー)
- [Phase 0: 準備と分析](#phase-0-準備と分析)
- [Phase 1: 仕様作成](#phase-1-仕様作成-specify)
- [Phase 2: 実装計画](#phase-2-実装計画-plan)
- [Phase 3: タスク生成](#phase-3-タスク生成-tasks)
- [Phase 4: 実装](#phase-4-実装-implementation)
- [Phase 5: 検証](#phase-5-検証-verification)
- [実践シナリオ](#実践シナリオ)
- [コマンドリファレンス](#コマンドリファレンス)
- [高度な設定](#高度な設定とカスタマイズ)
- [トラブルシューティング](#トラブルシューティング)

---

# 📊 メインワークフロー

## 責務分担表

| フェーズ | 担当 | コマンド | 入力 | 出力 | 所要時間 |
|---------|------|----------|------|------|----------|
| **準備** | 人間+スクリプト | `create-new-feature.sh` | 機能説明 | ブランチ+ディレクトリ | 1分 |
| **仕様作成** | Claude Code | `/specify` | 要件 | spec.md | 5分 |
| **計画策定** | Claude Code | `/plan` | spec.md | plan.md, research.md | 10分 |
| **タスク生成** | Claude Code | `/tasks` | plan.md | tasks.md | 5分 |
| **実装** | Claude Code または Codex | `/implement` or `/handoff-to-codex` | tasks.md | コード+PR | 30分-3時間 |
| **検証** | Claude Code | `/verify-and-pr` | 実装 | レポート+PR | 10分 |
| **最終判断** | 人間 | - | レポート | マージ判断 | 5分 |

### 📌 Super Claude強化ポイント
- **仕様作成**: 要件が曖昧な場合は自動的に`--brainstorm`モード起動
- **計画策定**: MCP統合（Context7、Serena）でアーキテクチャ最適化
- **タスク生成**: 3つ以上のタスクは自動的に並列最適化
- **実装**: `/handoff-to-codex`でセッション保持付き引き継ぎ
- **検証**: Sequential MCPで深層分析、Playwright MCPでE2Eテスト

## Quick Start（最速実行パス）

### パターン1: Claude Code継続実装（推奨）
```bash
# 1. 新機能の準備（3分）
./scripts/create-new-feature.sh "ユーザー認証"
cd specs/001-user-auth/

# 2. 仕様から実装まで一気に実行（30-60分）
/specify                    # 仕様生成
/plan                      # 計画策定  
/tasks --task-manage       # タスク生成（TodoWrite管理）

# Claude Codeで継続実装
specs/001-user-auth/tasks.mdを読み込んで実装を開始します
--seq --morph --magic      # MCP活用で効率化

# 3. 品質検証とPR作成（10分）
/verify-and-pr 001-user-auth --comprehensive
```

### パターン2: Codex引き継ぎ（大規模プロジェクト）
```bash
# 1. 新機能の準備（3分）
./scripts/create-new-feature.sh "ユーザー認証"
cd specs/001-user-auth/

# 2. 仕様から実装まで（1-3時間）
/specify                         # 仕様生成
/plan                           # 計画策定  
/tasks                          # タスク生成
/handoff-to-codex 001-user-auth # Codexへ引き継ぎ

# 3. 品質検証とPR作成（10分）
/verify-and-pr 001-user-auth
```

### 💡 Super Claude活用のポイント
- **自動モード選択**: 要件が曖昧な場合は自動的にbrainstormモードが起動
- **並列処理最適化**: 3つ以上のタスクは自動的に並列化
- **セッション管理**: 作業状態が自動保存され、中断後も継続可能
- **MCP統合**: 各フェーズで最適なMCPサーバーが自動選択

---

# Phase 0: 準備と分析

## 🎯 プロジェクトセットアップ

### 基本セットアップ
```bash
# 機能ブランチとディレクトリを自動作成
./scripts/create-new-feature.sh "機能名"

# 出力:
# ✅ Branch: feature/001-function-name
# ✅ Directory: specs/001-function-name/
# ✅ Template: spec-template.md copied
```

### 高度なセットアップ（エンタープライズ）
```bash
./scripts/create-new-feature.sh "エンタープライズ認証" \
  --complexity=high \
  --security=enterprise \
  --team-size=8
```

## 🔍 プロジェクト分析（Super Claude強化）

### 現状分析コマンド群
```markdown
# 包括的品質分析（Sequential MCPで深層分析）
/metrics --comprehensive --predictive

# 技術負債評価（Serena MCPでシンボル解析）  
/tech-debt --risk-matrix --roi-analysis

# 依存関係分析（循環依存検出）
/dependencies --circular-detection --security-focus

# セキュリティ監査
/security-audit project-wide --compliance-check

# 戦略的提案生成（ビジネスパネル分析）
/suggest-next --strategic-focus
```

### 分析結果の活用
```yaml
# 自動生成される分析レポート例
Project Health: 8.2/10
├── Code Quality: 8.5/10
├── Performance: 7.8/10  
├── Security: 9.2/10
└── Recommendations:
    - Immediate: 認証モジュールの複雑度改善
    - Short-term: パフォーマンススケーリング計画
    - Strategic: セキュリティ依存関係の更新
```

---

# Phase 1: 仕様作成 (Specify)

## 📝 /specify コマンド

### 基本使用法
```markdown
/specify

ユーザー認証システムを作成してください。
要件:
- メール/パスワード認証
- OAuth2.0対応（Google, GitHub）
- JWT使用
- 2要素認証
```

### 高度な使用法（Super Claude拡張）
```markdown
# 要件が曖昧な場合（自動的にbrainstormモード起動）
/specify --brainstorm
"認証システムが必要だが詳細は未定"

# ビジネス検証付き仕様生成
/specify --business-panel
"ROIを考慮したエンタープライズ認証システム"

# 深層分析付き（Sequential MCP使用）
/specify --think-hard
"高セキュリティ・高可用性の認証基盤"
```

### Claude Codeプロンプト例
```markdown
# 基本的な仕様作成
/specify "ユーザー認証システムを実装したい"
ユーザーストーリーと要件を詳細に定義してください。

# Super Claude拡張付き
/specify "JWT認証システム" --think-hard
--seq   # 複雑な仕様の深層分析
--c7    # ベストプラクティス参照
--serena # 既存システムとの整合性確認

# ビジネス要件分析込み
/specify "Eコマース決済システム" --business-panel
ビジネス戦略と技術要件を統合して分析してください。
```

## 📋 生成される仕様書の構造

```markdown
# Feature Specification: [機能名]

## Executive Summary
[ビジネス価値と目的]

## User Scenarios
### Primary User Story
As a [user type]
I want to [action]
So that [benefit]

### Acceptance Criteria
- Given [前提条件]
- When [アクション]
- Then [期待結果]

## Functional Requirements
- FR-001: システムは[機能]を提供する
- FR-002: [具体的な要件]
[NEEDS CLARIFICATION: 不明な点]

## Non-Functional Requirements  
- Performance: [目標値]
- Security: [要件]
- Scalability: [要件]

## Key Entities
- User: [属性]
- Session: [関係性]
```

### ✅ 仕様検証（Super Claude）
```markdown
# 論理整合性チェック
/validate-spec --logical-consistency

# 実現可能性評価
/validate-spec --feasibility-check

# ステークホルダー影響分析
/dependencies --stakeholder-mapping
```

---

# Phase 2: 実装計画 (Plan)

## 📋 /plan コマンド

### 基本使用法
```markdown
/plan
# spec.mdを自動的に読み込んで計画を生成
```

### 高度な使用法（Super Claude拡張）
```markdown
# アーキテクチャ指定
/plan --architecture=microservices

# MCPサーバー活用（Context7で最新パターン取得）
/plan --mcp=context7,serena

# 深層分析モード
/plan --think-hard

# ビジネス戦略分析付き
/plan --business-panel
```

### Claude Codeプロンプト例
```markdown
# 基本的な計画策定
/plan specs/001-auth/spec.md
技術スタックの選定とフェーズ分割を行ってください。

# Super Claude拡張付き
/plan specs/001-auth/spec.md --ultrathink
--seq    # アーキテクチャ深層分析
--serena # 既存コードベース調査
--c7     # フレームワークベストプラクティス

# 並列処理最適化計画
/plan specs/001-auth/spec.md --orchestrate
--delegate auto  # タスク自動分配
--concurrency 5  # 並列度指定
```

## 🏗️ 生成される実装計画

```markdown
# Implementation Plan: [機能名]

## Technical Context
**Language**: TypeScript/Python
**Framework**: Next.js/FastAPI
**Database**: PostgreSQL  
**Testing**: Jest/pytest

## Architecture Decision Record (ADR)
### Decision: [アーキテクチャ選択]
### Rationale: [選択理由]
### Consequences: [影響]

## Phase Breakdown
### Phase 0: Research & Setup
- 技術調査
- 環境構築
- 依存関係設定

### Phase 1: Core Implementation
- データモデル設計
- API設計
- コア機能実装

### Phase 2: Testing & Optimization
- テスト実装
- パフォーマンス最適化
- セキュリティ強化
```

### 📊 自動生成される成果物
```
specs/001-auth/
├── spec.md           # 仕様書（Phase 1）
├── plan.md          # 実装計画（このフェーズ）
├── research.md      # 技術調査結果
├── data-model.md    # データモデル
├── architecture.md  # アーキテクチャ図
└── contracts/       # API仕様
    ├── openapi.yaml
    └── schemas.json
```
---

# Phase 3: タスク生成 (Tasks)

## ✅ /tasks コマンド

### 基本使用法
```markdown
/tasks
# plan.mdから自動的にタスクを生成
```

### 高度な使用法（Super Claude拡張）
```markdown
# TDD方式でタスク生成
/tasks --methodology=tdd

# 並列実行最適化
/tasks --parallel-optimization

# Codex用に最適化
/enhance-tasks-for-codex 001-auth

# チーム割り当て付き
/tasks --team-allocation
```

### Claude Codeプロンプト例
```markdown
# 基本的なタスク生成
/tasks specs/001-auth/plan.md
実装可能な粒度でタスクを分解してください。

# Super Claude拡張付き
/tasks specs/001-auth/plan.md --task-manage
TodoWriteで自動的にタスク管理を行います。
--parallel-optimization  # 並列実行可能なタスクを識別
--uc  # トークン効率化

# Codex最適化（引き継ぎする場合）
/enhance-tasks-for-codex 001-auth
--concurrency 5  # 並列度指定
--atomic         # 原子的タスクに分解
```

## 📋 生成されるタスク構造

```markdown
# Tasks: [機能名]

## Overview
- Total Tasks: 45
- Estimated: 2 weeks
- Critical Path: 12 tasks
- Parallel Capacity: 67%

## Phase 3.1: Setup (Day 1)
- [ ] T001 プロジェクト構造作成
- [ ] T002 [P] 依存関係インストール
- [ ] T003 [P] 開発環境設定

## Phase 3.2: Tests First (Day 2-3) ⚠️ CRITICAL
- [ ] T004 [P] APIコントラクトテスト
- [ ] T005 [P] 統合テスト
- [ ] T006 [P] E2Eテストシナリオ

## Phase 3.3: Implementation (Day 4-8)
- [ ] T007 データモデル実装
- [ ] T008 認証サービス実装
- [ ] T009 [P] APIエンドポイント実装
- [ ] T010 [P] フロントエンド実装

## Dependencies
- T004-T006 → T007-T010 (テスト先行)
- T007 → T008 (データモデル依存)

[P] = 並列実行可能
```

### ⚡ タスク最適化（Super Claude）
```markdown
# 実行時間見積もり（モンテカルロ法）
/estimate 001-auth --monte-carlo

# リソース最適化
/optimize tasks --resource-allocation

# 依存関係の最小化
/dependencies --minimize --visualize
```
---

# Phase 4: 実装 (Implementation)

## 🚀 実装パスの選択（Super Claude対応）

### パス1: Claude Code継続実装（推奨）
**適用場面**:
- 中小規模プロジェクト（〜50ファイル）
- 複雑なビジネスロジック
- 高度なアーキテクチャ判断が必要
- インタラクティブな開発が必要

#### Claude Codeプロンプト例
```markdown
# タスクベース実装
specs/001-auth/tasks.mdを読み込んで実装を開始します。
Super Claudeモードを活用して効率的に実装してください。

# 実装フロー
1. /sc:load でプロジェクトコンテキスト読込
2. TodoWriteでタスクリスト管理
3. 並列実行で効率化
   - 独立したファイルは並列で実装
   - MultiEditで一括編集
4. 各タスク完了時に検証

# MCP活用例
--seq    # 複雑なロジック分析
--morph  # 一括コード変換
--magic  # UIコンポーネント生成
--serena # シンボル操作と依存関係管理
```

### パス2: Codex引き継ぎ（オプション）
**適用場面**:
- 大規模プロジェクト（50ファイル以上）
- 定型的・反復的なタスク
- 並列実装が必要
- 時間制約が厳しい

#### 引き継ぎコマンド
```markdown
# 基本的な引き継ぎ
/handoff-to-codex 001-auth

# Super Claude拡張オプション
/handoff-to-codex 001-auth --session-preserve  # セッション保持
/handoff-to-codex 001-auth --full-context      # フルコンテキスト
/handoff-to-codex 001-auth --error-recovery    # エラー回復
```

#### Codex実装プロンプト例
```markdown
specs/001-auth/tasks.mdを読み込んで実装を開始してください。

実装手順:
1. 関連ファイルの読み込み
2. ドラフトPR作成
3. tasks.mdをPRコメントに投稿
4. T001から順次実装

各タスク完了時:
- テストが通る状態でコミット
- conventional commits形式
- PRに進捗コメント投稿
```

## 📊 実装パス選択ガイド

| 基準 | Claude Code継続 | Codex引き継ぎ |
|------|----------------|---------------|
| プロジェクト規模 | 〜50ファイル | 50ファイル以上 |
| タスクの性質 | 複雑・創造的 | 定型的・反復的 |
| 実装速度 | 標準 | 高速（並列実行） |
| インタラクション | 必要 | 最小限 |
| コンテキスト管理 | 自動（Serena） | 手動引き継ぎ |
| エラー対応 | リアルタイム | バッチ処理 |

## 🔄 実装中のAI協調（Super Claude）

### リアルタイムサポート
```markdown
# エラー発生時の自動デバッグ
/debug "Authentication failed: invalid token"

# コードレビュー（PR作成時）
/review PR#123 --security-focus

# パフォーマンス最適化
/optimize src/auth/service.ts

# UI生成（Magic MCP）
/ui "ログインフォーム" --accessible
```

### 進捗モニタリング
```markdown
# 日次進捗レポート
/progress --daily-report

# ボトルネック検出
/metrics --bottleneck-analysis

# 品質メトリクス
/metrics --quality-gates
```
---

# Phase 5: 検証 (Verification)

## 🔍 /verify-and-pr コマンド

### 基本使用法
```markdown
/verify-and-pr 001-auth "feat: 認証機能実装"

# 以下の観点で自動検査:
1. 仕様準拠
2. コード品質
3. セキュリティ
4. パフォーマンス
5. テストカバレッジ
```

### 高度な検証（Super Claude拡張）
```markdown
# 包括的検証（全MCP活用）
/verify-and-pr 001-auth "feat: 認証機能実装" --comprehensive

# E2Eテスト（Playwright MCP）
/verify-and-pr 001-auth "feat: 認証機能実装" --play

# セキュリティ監査（Sequential深層分析）
/verify-and-pr 001-auth "feat: 認証機能実装" --seq --security-focus

# ビジネス価値検証
/verify-and-pr 001-auth "feat: 認証機能実装" --business-panel
```

### Claude Codeプロンプト例
```markdown
# 基本的な検証
/verify-and-pr 001-auth "feat: 認証機能実装"
仕様との適合性を検査し、問題がなければPRを作成してください。

# Super Claude拡張検証
/verify-and-pr 001-auth "feat: 認証機能実装" --comprehensive
--play   # E2Eテスト実行
--seq    # セキュリティ深層分析
--serena # コードベース全体の影響分析

# 自動修正付き検証
/verify-and-pr 001-auth "feat: 認証機能実装" --auto-fix
問題を検出した場合、自動的に修正してからPRを作成します。
--validate  # 修正前に検証
--safe-mode # 安全モードで実行
```

## 📊 検証レポート構造

```markdown
# Verification Report: 001-auth

## Summary
- 🟢 仕様準拠: 95%
- 🟢 コード品質: A
- 🟢 セキュリティ: Pass
- 🟡 パフォーマンス: 1 issue
- 🟢 カバレッジ: 92%

## Details

### ✅ Passed
- JWT実装が仕様通り
- エラーハンドリング完備
- テスト充実

### ⚠️ Issues
1. **Performance**: N+1問題
   - Location: src/api/users.ts:45
   - Fix: Eager loading追加
   - Priority: Medium

### 🎯 Recommendations
- Redis caching追加でレスポンス改善
- rate limiting実装推奨

## Conclusion
✅ 軽微な修正後、本番デプロイ可能
```

### 🚀 検証後のアクション
```markdown
# 問題の自動修正
/fix-issues 001-auth --auto-pr

# 最終確認
/final-check 001-auth

# デプロイ準備
/prepare-deployment 001-auth
```
---

# 🎯 実践シナリオ

## Scenario 1: 新機能開発（ゼロから）

```markdown
# 1. プロジェクト準備（3分）
./scripts/create-new-feature.sh "ECレコメンド"

# 2. 要件探索（曖昧な場合は自動でbrainstormモード）
/specify --brainstorm
"ECサイトにレコメンド機能を追加したい"

# 3. ビジネス検証（オプション）
/sc:business-panel @specs/recommendation/spec.md
"ROIと競争優位性を分析"

# 4. 実装計画
/plan --architecture=microservices

# 5. タスク生成と最適化
/tasks --parallel-optimization
/enhance-tasks-for-codex recommendation

# 6. 実装
/handoff-to-codex recommendation --session-preserve

# 7. 検証とPR作成
/verify-and-pr recommendation "feat: レコメンド機能実装" --comprehensive
```

## Scenario 2: レガシーコード改善

```markdown
# 1. 現状分析（15分）
/metrics --comprehensive
/tech-debt --risk-matrix
/dependencies --circular-detection

# 2. 改善戦略策定
/suggest-next --optimization-focus

# 3. リファクタリング計画
/plan refactoring --incremental

# 4. 段階的実装
for module in auth user payment:
  /refactor $module --pattern=solid
  /test $module --regression
  /optimize $module
done

# 5. 検証とPR作成
/verify-and-pr refactoring "refactor: SOLIDパターン適用" --comprehensive
```

## Scenario 3: 緊急バグ修正

```markdown
# 1. 問題分析（5分）
/debug "認証が突然失敗する" --root-cause

# 2. 影響範囲特定
/dependencies auth-module --impact-analysis

# 3. 修正と検証
/fix-bug auth-timeout --auto-test
/verify-and-pr auth "fix: 認証タイムアウトの修正" --security-focus
```

## Scenario 4: パフォーマンス最適化

```markdown
# 1. ボトルネック分析
/metrics --performance-analysis
/profile application --cpu --memory

# 2. 最適化実装
/optimize critical-path --parallel-edits
/cache-strategy implement --redis

# 3. 検証
/load-test --scenarios=peak
/metrics --before-after
/verify-and-pr performance "perf: クリティカルパスの最適化" --performance-focus
```

---

# 📚 コマンドリファレンス

## ⚠️ 重要：実装状況について
- ✅ = 実装済み（実際に動作するコマンド）
- ❌ = 未実装（概念的なコマンド、自然言語で代替）

## 基本コマンド（Spec-Kit）

| コマンド | 状態 | 実装場所 | 説明 | 実際の使用例 |
|---------|------|---------|------|-------------|
| `/specify` | ✅ | プロジェクト/.claude/commands/ | 仕様書生成 | `/specify "認証システム"` |
| `/plan` | ✅ | プロジェクト/.claude/commands/ | 実装計画作成 | `/plan` (spec.mdを自動読込) |
| `/tasks` | ✅ | プロジェクト/.claude/commands/ | タスク分解 | `/tasks` (plan.mdを自動読込) |

## 検証・PR作成コマンド（実装済み）

| コマンド | 状態 | 実装場所 | 説明 | 使用例 |
|---------|------|---------|------|---------|
| `/verify-and-pr` | ✅ | .claude/commands/ | 実装検証→合格時自動PR作成 | `/verify-and-pr auth "feat: 認証機能実装"` |

## Super Claude専用コマンド（実装済み）

| コマンド | 状態 | 説明 | 使用例（日本語での依頼） |
|---------|------|------|------------------------|
| `/sc:load` | ✅ | プロジェクトコンテキストとメモリを読み込んでセッション開始 | `/sc:load` "プロジェクトのコンテキストを読み込んで作業を開始" |
| `/sc:save` | ✅ | 現在の作業状態とメモリを保存してチェックポイント作成 | `/sc:save` "現在の進捗を保存してください" |
| `/sc:business-panel` | ✅ | 複数のビジネス専門家による戦略分析とディスカッション | `/sc:business-panel` "@仕様書.md" "ROIと競争優位性を分析" |
| `/sc:analyze` | ✅ | コード品質・セキュリティ・パフォーマンス・アーキテクチャの包括的分析 | `/sc:analyze` "src/" "セキュリティ重視で分析してください" |
| `/sc:brainstorm` | ✅ | 要件探索と創造的アイデア出しのための対話型ブレインストーミング | `/sc:brainstorm` "新機能のアイデアを一緒に考えましょう" |
| `/sc:build` | ✅ | プロジェクトのビルドとコンパイル、最適化処理の実行 | `/sc:build` "--production" "本番用にビルドしてください" |
| `/sc:cleanup` | ✅ | 不要ファイル削除、依存関係整理、コードベースのクリーンアップ | `/sc:cleanup` "一時ファイルと未使用の依存関係を削除" |
| `/sc:design` | ✅ | システム設計、アーキテクチャ設計、API設計の作成と検証 | `/sc:design` "マイクロサービス" "認証システムの設計を作成" |
| `/sc:document` | ✅ | README、API、アーキテクチャドキュメントの自動生成と更新 | `/sc:document` "src/api" "APIドキュメントを生成してください" |
| `/sc:estimate` | ✅ | タスクの工数見積もり、リソース計画、スケジュール策定 | `/sc:estimate` "認証機能の実装にかかる時間を見積もって" |
| `/sc:explain` | ✅ | コード、アーキテクチャ、ビジネスロジックの詳細説明 | `/sc:explain` "auth.js" "認証フローを分かりやすく説明して" |
| `/sc:git` | ✅ | Git操作の自動化（コミット、ブランチ管理、マージ戦略） | `/sc:git` "feature/auth" "変更をコミットしてPRを作成" |
| `/sc:implement` | ✅ | 機能実装、コンポーネント開発、API開発の統合的実行 | `/sc:implement` "ユーザー認証" "JWT認証を実装してください" |
| `/sc:improve` | ✅ | コード改善、パフォーマンス最適化、リファクタリングの実施 | `/sc:improve` "src/api" "レスポンス速度を改善してください" |
| `/sc:index` | ✅ | プロジェクト構造の解析とナビゲーション用インデックス生成 | `/sc:index` "." "プロジェクト全体の構造図を作成" |
| `/sc:reflect` | ✅ | 開発プロセスの振り返り、学習ポイントの抽出、改善提案 | `/sc:reflect` "今週の開発を振り返って改善点を提案" |
| `/sc:select-tool` | ✅ | タスクに最適なツール、フレームワーク、ライブラリの選択支援 | `/sc:select-tool` "状態管理" "最適なツールを提案して" |
| `/sc:spawn` | ✅ | サブタスクの生成、並列処理の設定、エージェント委譲 | `/sc:spawn` "認証実装" "並列実行可能なタスクに分解" |
| `/sc:task` | ✅ | タスク管理、優先順位設定、進捗追跡の統合管理 | `/sc:task` "優先度の高いタスクから順に整理してください" |
| `/sc:test` | ✅ | テスト作成、実行、カバレッジ分析、E2Eテストの実施 | `/sc:test` "src/auth" "単体テストとE2Eテストを作成" |
| `/sc:troubleshoot` | ✅ | エラー診断、デバッグ、問題解決、根本原因分析 | `/sc:troubleshoot` "認証エラー" "原因を特定して修正案を提示" |
| `/sc:workflow` | ✅ | 開発ワークフローの設計、CI/CD設定、プロセス最適化 | `/sc:workflow` "CI/CDパイプラインを設計してください" |

## フラグ・オプション

| フラグ | 効果 | 使用場面 | 使用例 |
|-------|------|----------|--------|
| `--brainstorm` | 要件探索モード | 要件が曖昧 | `/specify --brainstorm "認証機能が必要だが詳細は未定"` |
| `--think-hard` | 深層分析 | 複雑な問題 | `/verify-and-pr auth "feat: 認証実装" --think-hard` |
| `--business-panel` | ビジネス検証 | 戦略的判断 | `/specify --business-panel "ROIを考慮した決済システム"` |
| `--parallel-optimization` | 並列処理最適化 | マルチタスク | `/tasks --parallel-optimization` |
| `--session-preserve` | セッション保持 | 長時間作業 | `/verify-and-pr payment "feat: 決済機能" --session-preserve` |
| `--comprehensive` | 包括的分析 | 最終検証 | `/verify-and-pr auth "feat: 認証実装" --comprehensive` |
| `--mcp=<servers>` | MCPサーバー指定 | 特定機能強化 | `/specify --mcp=sequential,context7,serena` |
| `--seq` | Sequential MCP（複雑な推論） | 深層分析、デバッグ | `/specify "認証フロー" --seq` |
| `--c7` | Context7 MCP（公式ドキュメント） | ベストプラクティス参照 | `/plan --c7 # React公式パターン参照` |
| `--serena` | Serena MCP（シンボル解析） | 既存システムとの整合性確認 | `/verify-and-pr api "feat: API拡張" --serena` |
| `--magic` | Magic MCP（UI生成） | UIコンポーネント作成 | `/ui "ログインフォーム" --magic` |
| `--morph` | Morphllm MCP（パターン編集） | 一括コード変換 | `/refactor --morph # クラスからフックへ` |
| `--play` | Playwright MCP（E2Eテスト） | ブラウザテスト実行 | `/verify-and-pr ui "feat: UI改善" --play` |
| `--all-mcp` | 全MCPサーバー有効化 | 最大機能活用 | `/specify "エンタープライズ認証" --all-mcp` |
| `--no-mcp` | MCPサーバー無効化 | ネイティブツールのみ使用 | `/verify-and-pr simple "fix: 軽微な修正" --no-mcp` |

## MCPサーバー選択ガイド

| MCPサーバー | 特徴 | 適用場面 |
|------------|------|----------|
| **Sequential** | 多段階推論 | 深層分析、デバッグ |
| **Context7** | 公式ドキュメント | フレームワーク参照 |
| **Magic** | UIコンポーネント | フロントエンド開発 |
| **Serena** | シンボル操作 | コード解析、リファクタリング |
| **Morphllm** | パターン編集 | 一括変更 |
| **Playwright** | ブラウザテスト | E2Eテスト |

## MCPフラグ組み合わせ使用例

### 包括的仕様作成
```bash
/specify "認証システム" --seq --c7 --serena
# Sequential: 認証フローの多段階分析
# Context7: JWT/OAuth2の公式実装パターン参照
# Serena: 既存認証コードとの整合性確認
```

### 高品質実装検証
```bash
/verify-and-pr auth "feat: 認証機能実装" --comprehensive --seq --play
# Comprehensive: 全項目詳細検証
# Sequential: 複雑なロジックの深層分析
# Playwright: E2Eテストの自動実行
```

### UI機能の完全実装
```bash
/specify "ダッシュボード" --magic --c7 --business-panel
# Magic: UIコンポーネント生成
# Context7: React/Vue公式パターン
# Business Panel: UXのビジネス価値分析
```

### レガシーコード改善
```bash
/plan refactoring --serena --morph --think-hard
# Serena: 既存コードのシンボル解析
# Morphllm: パターンベース一括変換計画
# Think-hard: リファクタリング戦略の深層分析
```
---

# 🔧 高度な設定とカスタマイズ

## Super Claude設定ファイル

```yaml
# .super-claude/config.yml
modes:
  default: orchestrate
  auto_switch: true
  context_preservation: true

mcp_servers:
  sequential:
    auto_enable: true
    thinking_depth: hard
  context7:
    cache: true
    versions: latest
  serena:
    project_memory: true
    session_persistence: true
  magic:
    ui_framework: react
    style: tailwind
  
business_panel:
  default_experts: [porter, christensen, drucker]
  output_format: synthesis
  debate_threshold: 0.7

optimization:
  token_efficiency: auto
  parallel_threshold: 3
  batch_size: optimal
```

## プロジェクト別設定

```yaml
# specs/.claude-config.yml
project:
  type: enterprise
  team_size: 8
  complexity: high

workflow:
  phases:
    - brainstorm: always
    - business_panel: strategic_only  
    - specify: template=enterprise
    - plan: architecture=microservices
    - tasks: parallel_optimize
    - implement: codex_handoff
    - verify: comprehensive

quality_gates:
  coverage: 95
  security: owasp_top10
  performance: 
    latency: 50ms
    throughput: 10000

automation:
  pr_review: auto
  security_audit: on_commit
  performance_test: daily
```

---

# 🔧 トラブルシューティング

## よくある問題と解決策

### コマンド関連

| 問題 | 原因 | 解決策 |
|------|------|--------|
| コマンドが動作しない | 未実装 | `spec-command-make.md`を参照して実装 |
| 仕様書が生成されない | テンプレートなし | `spec-template.md`を配置 |
| タスクが並列化されない | 依存関係 | `--parallel-optimization`追加 |

### セッション関連

| 問題 | 原因 | 解決策 |
|------|------|--------|
| セッション消失 | タイムアウト | `/sc:save`を定期実行 |
| コンテキスト不足 | メモリ未保存 | `/sc:memory write`活用 |
| MCP接続エラー | サーバー未起動 | `--no-mcp`で回避 |

### パフォーマンス問題

```markdown
# トークン使用量が多い場合
--uc --token-efficient
/optimize context --compression

# 処理が遅い場合
--orchestrate --parallel
/batch-operations enable

# メモリ不足
/sc:memory cleanup
/cache clear
```

### 統合エラー

```markdown
# Codex引き継ぎ失敗
/sync-context --force
/handoff-to-codex --retry --verbose

# MCP競合
--mcp=none  # 一時的に無効化
/debug mcp-conflict --isolate

# 検証失敗
/verify-and-pr auth "feat: 認証実装" --partial
/test --specific-module
```

---

# 🌟 ベストプラクティス

## ワークフロー最適化

### ✅ 推奨事項
1. **セッション管理**: 30分ごとに`/sc:save`
2. **モード選択**: タスクに最適なモードを自動選択
3. **MCP活用**: 専門タスクには専用MCPを使用
4. **並列処理**: 3つ以上のタスクは並列化
5. **品質ゲート**: 各フェーズで検証実施

### ❌ アンチパターン
1. 全タスクで`--all-mcp`使用（リソース無駄）
2. セッション保存なしで長時間作業
3. エラー時の`--no-mcp`常用
4. ビジネス分析なしでの実装開始
5. 検証フェーズのスキップ

## 成功指標

| 指標 | 目標 | 測定方法 |
|------|------|----------|
| **開発速度** | 3倍向上 | タスク完了時間 |
| **品質** | バグ率 <1% | 検証レポート |
| **自動化率** | >80% | 手動作業時間 |
| **満足度** | >90% | チーム評価 |
---

# 📊 Quick Reference Card

## 最頻出コマンド
```bash
# プロジェクト開始
./scripts/create-new-feature.sh "機能名"

# 仕様作成
/specify

# 実装準備
/plan
/tasks --enhance-for-codex

# Codex引き継ぎ（オプション）
/handoff-to-codex <slug>

# 品質検証とPR作成
/verify-and-pr <slug> "feat: 機能実装"
```

## 問題別コマンド選択
```
要件不明 → /specify --brainstorm
戦略判断 → /sc:business-panel
エラー解析 → /debug --root-cause
パフォーマンス → /optimize
セキュリティ → /security-audit
```

## MCP選択ガイド
```
深い分析 → sequential
ドキュメント → context7
UI生成 → magic
コード解析 → serena
一括編集 → morphllm
E2Eテスト → playwright
```

---

# 📞 サポートとリソース

## 公式リソース
- [Super Claude Documentation](https://docs.anthropic.com/super-claude)
- [Spec-Kit GitHub](https://github.com/spec-kit)
- [MCP Server Guide](https://mcp.anthropic.com)

## コミュニティ
- Discord: Super Claude Community
- GitHub Issues: バグ報告・機能要望

## 更新履歴
- v2.1.0 (2024-09): `/verify-and-pr`統合、MCPフラグ拡充
- v2.0.0 (2024-09): Super Claude統合
- v1.5.0 (2024-08): MCP対応
- v1.0.0 (2024-07): 初版リリース

---

**💡 Pro Tip**: このマニュアルは進化し続けます。`/suggest-next --manual-improvements`で改善提案を生成できます。