# 🚀 次世代AI開発ワークフロー完全マニュアル v2.2
## Spec-Kit × Claude Code + Super Claude Framework

> **仕様駆動開発の究極形**: 要件定義から実装・検証まで、Claude Codeが主導する完全自動化ワークフロー

## 📊 ワークフロー概要

```mermaid
graph LR
    A[🎯 要件定義] -->|仕様化| B[📝 Spec-Kit]
    B -->|計画| C[📋 実装計画]
    C -->|タスク化| D[✅ タスク分解]
    D -->|実装| E[🔨 Claude Code実装]
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
- **チーム協調**: Claude Codeを中心とした効率的な開発
- **継続的改善**: セッション管理による学習と最適化

## 📋 目次
- [メインワークフロー](#メインワークフロー)
- [Phase 0: 準備と分析](#phase-0-準備と分析)
- [Phase 1: 仕様作成](#phase-1-仕様作成-specify)
  - [/specify よくある質問（Q&A）](#specify-よくある質問qa)
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
| **実装** | Claude Code | TodoWrite + 実装 | tasks.md | コード | 30分-2時間 |
| **検証** | Claude Code | `/verify-and-pr` | 実装 | レポート+PR | 10分 |
| **最終判断** | 人間 | - | レポート | マージ判断 | 5分 |

### 📌 Super Claude強化ポイント
- **仕様作成**: 要件が曖昧な場合は自動的に`--brainstorm`モード起動
- **計画策定**: MCP統合（Context7、Serena）でアーキテクチャ最適化
- **タスク生成**: 3つ以上のタスクは自動的に並列最適化
- **実装**: TodoWriteによる進捗管理とMCP活用
- **検証**: Sequential MCPで深層分析、Playwright MCPでE2Eテスト

## Quick Start（最速実行パス）

### 基本的な開発フロー（推奨）
```bash
# 1. 新機能の準備（3分）
./scripts/create-new-feature.sh "ユーザー認証"
cd specs/001-user-auth/

# 2. 仕様から計画まで（15-20分）
/specify                    # 仕様生成
/plan                      # 計画策定  
/tasks --task-manage       # タスク生成（TodoWrite管理）

# 3. Claude Codeで実装（30分-2時間）
# Claude Codeプロンプト：
specs/001-user-auth/tasks.mdを読み込んで実装を開始します
--seq --morph --magic      # MCP活用で効率化

# 4. 品質検証とPR作成（10分）
/verify-and-pr 001-user-auth --comprehensive
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

#### Claude Codeプロンプト例
```markdown
# 包括的品質分析
プロジェクト全体の品質分析を実行してください
--seq    # Sequential MCPで深層分析
--serena # Serenaでシンボル解析

# 技術負債評価  
技術負債のリスクマトリクスとROI分析を作成してください
--serena # 既存コードのシンボル解析
--think-hard # 深層分析モード

# 依存関係分析
循環依存の検出とセキュリティに焦点を当てた依存関係分析を実行してください
グラフで視覚化してください

# セキュリティ監査
プロジェクト全体のセキュリティ監査を実行してください
OWASPトップ10に準拠したチェックを含めてください

# 戦略的提案生成
現在のコードベースに基づいて、次の開発戦略を提案してください
ビジネス価値を考慮した優先順位付けをお願いします
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

### Claude Codeプロンプト例（拡充版）

#### 基本的な仕様作成
```markdown
# シンプルな仕様作成
/specify "ユーザー認証システムを実装したい"
以下の観点を含めて仕様を作成してください：
- ユーザーストーリー
- 機能要件と非機能要件
- 受け入れ基準
- 技術的制約
```

#### 要件探索型の仕様作成
```markdown
# 対話的な要件探索
/specify --brainstorm
「ECサイトのユーザー管理機能が必要ですが、詳細はまだ決まっていません」

以下の点について一緒に検討しましょう：
1. ターゲットユーザーとペルソナ
2. 必須機能と任意機能の切り分け
3. セキュリティレベルの要求
4. 既存システムとの統合要件
5. パフォーマンス目標
```

#### MCP統合型の仕様作成
```markdown
# ベストプラクティスを参照した仕様作成
/specify "JWT認証システム" 
--c7    # Context7でJWT公式実装パターンを参照
--serena # 既存の認証コードとの整合性確認

既存のコードベースを分析し、以下を含めた仕様を作成してください：
- 現在の認証実装との互換性
- JWT実装のベストプラクティス
- セキュリティ考慮事項
- 移行計画
```

#### ビジネス要件統合型
```markdown
# ビジネスパネル分析付き仕様作成
/specify "Eコマース決済システム" --business-panel

以下の観点から専門家パネルによる分析を含めてください：
- Porter: 競争優位性の観点
- Christensen: 顧客が解決したいジョブ
- Drucker: ビジネス価値とROI
- Taleb: リスクと反脆弱性

技術仕様とビジネス戦略を統合した包括的な仕様書を作成してください。
```

#### 段階的詳細化型
```markdown
# イテレーティブな仕様作成
/specify "認証システム" --iterative

Phase 1: 概要レベルの仕様
- 基本的な要件とゴール
- 主要なユーザーストーリー

Phase 2: 詳細仕様
- 具体的な機能要件
- API設計
- データモデル

Phase 3: 実装仕様
- 技術スタック選定
- セキュリティ実装詳細
- テスト戦略

各フェーズで確認を取りながら進めてください。
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

#### Claude Codeプロンプト例
```markdown
# 論理整合性チェック
spec.mdの論理整合性を検証してください
矛盾点や不明確な点を指摘してください

# 実現可能性評価
spec.mdの実現可能性を評価してください
技術的リスクと対策を提案してください

# ステークホルダー影響分析
spec.mdに基づいてステークホルダーマッピングを作成してください
各ステークホルダーへの影響を分析してください
```

## 📌 /specify よくある質問（Q&A）

### Q1: /specifyで出力された仕様書を修正したい場合はどうすればよいか？

#### A: 直接編集が推奨されます

**仕様書の修正方法**
```markdown
# 方法1: 直接編集（推奨）
specs/001-feature/spec.mdを直接修正してください
特別なコマンドは不要です

# 方法2: Claude Codeで修正依頼
spec.mdに以下の要件を追加してください：
- 新しい機能要件
- パフォーマンス目標の更新
- セキュリティ要件の強化
```

**精度を高める方法**
```markdown
# 初回生成時の精度向上
/specify --think-hard        # 深層分析
/specify --business-panel    # ビジネス価値分析
/specify --brainstorm        # 対話的要件探索

# 反復的な改善（推奨）
1. /specify "基本要件"
2. spec.mdをレビューして修正
3. 論理整合性を検証 --seq
```

### Q2: 途中で新規機能や修正が必要になった場合の対処法は？

#### A: 変更の規模によって対応を分けます

**小規模な修正・追加の場合**
```markdown
# 既存spec.mdを更新
specs/001-auth/spec.mdに以下を追加してください：
- パスワードリセット機能
- Remember Meオプション

# 変更履歴を記録
## Version History
- v1.0: 初期仕様
- v1.1: パスワードリセット追加
- v1.2: Remember Me追加
```

**大規模な新機能の場合**
```bash
# 新規仕様書として作成
./scripts/create-new-feature.sh "追加機能"
cd specs/002-additional-feature/

/specify
"001の拡張として、ソーシャル認証を追加"
```

**マージ戦略**
```markdown
# 関連性が高い場合 → 同一PR
/verify-and-pr 001-auth "feat: 認証機能（基本+拡張）"

# 独立性が高い場合 → 別PR
/verify-and-pr 001-auth "feat: 基本認証"
/verify-and-pr 002-social "feat: ソーシャル認証"
```

**精度向上のためのコマンド活用**
```markdown
# 依存関係の明確化
## Dependencies
- Requires: 001-auth
- Extends: User model
- Conflicts: None

# 影響分析の実施
既存機能への影響を分析してください
--serena  # シンボル解析
--seq     # 深層分析
```

### 仕様管理のベストプラクティス

**推奨フロー**
```markdown
1. 初期仕様作成
   /specify --brainstorm

2. 詳細化と検証
   spec.md詳細化 → 論理整合性チェック

3. 変更管理
   小規模 → 既存更新
   大規模 → 新規作成

4. バージョン管理
   変更履歴を必ず記録
```

**精度向上チェックリスト**
```markdown
□ ユーザーストーリーが明確
□ 受け入れ基準が定量的
□ エッジケースを網羅
□ 非機能要件を定義
□ 依存関係を明記
□ 変更履歴を記録
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

# MCPサーバー活用
/plan --mcp=context7,serena

# 深層分析モード
/plan --think-hard

# ビジネス戦略分析付き
/plan --business-panel
```

### Claude Codeプロンプト例（拡充版）

#### 基本的な計画策定
```markdown
# 標準的な実装計画
/plan specs/001-auth/spec.md

以下を含む実装計画を作成してください：
1. 技術スタックの選定理由
2. フェーズごとの実装順序
3. 各フェーズのマイルストーン
4. リスクと対策
5. テスト戦略
```

#### アーキテクチャ重視の計画
```markdown
# システム設計を含む計画
/plan specs/001-auth/spec.md
--seq    # アーキテクチャの深層分析
--serena # 既存コードベースとの統合分析

以下の観点から計画を策定してください：
- システムアーキテクチャ図（mermaid）
- コンポーネント間の依存関係
- データフローダイアグラム
- API設計（OpenAPI仕様）
- データベーススキーマ
```

#### 並列処理最適化計画
```markdown
# 効率的な実装のための並列化計画
/plan specs/001-auth/spec.md --orchestrate

並列実行可能なタスクを識別し、以下を作成してください：
1. 依存関係マトリックス
2. クリティカルパス分析
3. 並列実行スケジュール
4. リソース割り当て計画
5. 推定時間短縮効果

--delegate auto  # タスク自動分配
--concurrency 5  # 並列度指定
```

#### リサーチ重視の計画
```markdown
# 技術調査を含む詳細計画
/plan specs/001-auth/spec.md --research-heavy

実装前に以下の調査を含めてください：
1. 利用可能なライブラリの比較
   --c7 # 公式ドキュメントを参照
2. セキュリティベストプラクティス
3. パフォーマンスベンチマーク
4. 既存実装のケーススタディ
5. 技術選定マトリックス

research.mdに詳細をまとめてください。
```

#### 段階的実装計画
```markdown
# MVP → 本番への段階的計画
/plan specs/001-auth/spec.md --incremental

以下の段階で計画を作成してください：

Phase 0: MVP (1日)
- 最小限の認証機能
- ローカル環境のみ

Phase 1: 基本実装 (3日)
- 完全な認証フロー
- 基本的なセキュリティ

Phase 2: 本番対応 (1週間)
- スケーラビリティ対応
- 監視とロギング
- セキュリティ強化

各フェーズの成果物を明確にしてください。
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

# チーム割り当て付き
/tasks --team-allocation
```

### Claude Codeプロンプト例（拡充版）

#### 基本的なタスク生成
```markdown
# 標準的なタスク分解
/tasks specs/001-auth/plan.md

以下の粒度でタスクを作成してください：
- 各タスクは2-4時間で完了可能
- 明確な成果物を定義
- テスト可能な完了基準
- 依存関係を明記
```

#### TodoWrite統合型タスク管理
```markdown
# タスク管理ツール統合
/tasks specs/001-auth/plan.md --task-manage

TodoWriteツールを使用して以下を実行してください：
1. タスクリストの作成
2. 優先順位の設定
3. 依存関係の定義
4. 進捗追跡の設定

実装時は各タスクの状態を更新しながら進めます。
```

#### 並列実行最適化タスク
```markdown
# 効率的な並列実行計画
/tasks specs/001-auth/plan.md
--parallel-optimization  # 並列実行可能なタスクを識別
--uc  # トークン効率化

以下の形式でタスクを整理してください：

## 並列実行グループ
Group A (独立実行可能):
- [ ] T001 [P] データモデル定義
- [ ] T002 [P] APIスキーマ定義
- [ ] T003 [P] フロントエンドモックアップ

Group B (Group A完了後):
- [ ] T004 API実装
- [ ] T005 フロントエンド実装

[P] = 並列実行可能
```

#### テスト駆動開発タスク
```markdown
# TDD方式のタスク生成
/tasks specs/001-auth/plan.md --methodology=tdd

以下の順序でタスクを生成してください：

1. テスト作成タスク
   - [ ] T001: ユニットテスト作成
   - [ ] T002: 統合テスト作成
   - [ ] T003: E2Eテストシナリオ作成

2. 実装タスク（テストを満たすように）
   - [ ] T004: テストを通す最小実装
   - [ ] T005: リファクタリング
   - [ ] T006: 最適化

各タスクにテストファイルパスを含めてください。
```

#### 詳細な実装タスク
```markdown
# ファイルレベルの詳細タスク
/tasks specs/001-auth/plan.md --granular

以下の詳細度でタスクを作成してください：

## Phase 3.1: データ層実装
- [ ] T001: `models/user.ts` - Userエンティティ定義
- [ ] T002: `models/session.ts` - Sessionエンティティ定義
- [ ] T003: `repositories/userRepository.ts` - ユーザーリポジトリ
- [ ] T004: `migrations/001_create_users.sql` - DBマイグレーション

## Phase 3.2: ビジネスロジック層
- [ ] T005: `services/authService.ts` - 認証サービス
- [ ] T006: `services/tokenService.ts` - JWTトークン管理
- [ ] T007: `middleware/authMiddleware.ts` - 認証ミドルウェア

各タスクに推定時間と依存関係を含めてください。
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

[P] = 並列実行可能
```

---

# Phase 4: 実装 (Implementation)

## 🚀 Claude Code実装（メイン推奨）

超重要：実装の前に、"@フォルダを読み込んで、最適な実装コマンド、プロンプトを検討してください"を聞く、その上で実行

### 実装開始のプロンプト例（拡充版）

#### 基本的な実装開始
```markdown
# タスクリストに基づく実装
specs/001-auth/tasks.mdを読み込んで実装を開始してください。

実装手順：
1. TodoWriteツールでタスク管理
2. 各タスクを順次実装
3. 完了したタスクは即座にマーク
4. テストを実行して検証
```

#### MCP活用型実装
```markdown
# Super Claude機能をフル活用した実装
specs/001-auth/tasks.mdを読み込んで実装を開始します。

以下のMCPサーバーを活用してください：
--seq    # 複雑なロジックの分析と設計
--serena # シンボル操作と依存関係管理
--magic  # UIコンポーネント生成
--morph  # 一括コード変換

実装フロー：
1. /sc:load でプロジェクトコンテキスト読込
2. TodoWriteでタスクリスト管理
3. 並列実行可能なタスクは同時に処理
4. MultiEditで複数ファイルを効率的に編集
5. 各タスク完了時にテスト実行
```

#### 段階的実装
```markdown
# MVP → 完全実装への段階的アプローチ
specs/001-auth/tasks.mdのPhase 1（MVP）から実装を開始してください。

Phase 1: MVP実装（基本機能）
- シンプルな認証フロー
- 最小限のエラーハンドリング
- ローカル環境での動作確認

完了後、Phase 2に進む前に動作確認をします。
```

#### テスト駆動実装
```markdown
# TDDアプローチでの実装
specs/001-auth/tasks.mdを確認し、まずテストから実装してください。

1. テストファイルの作成
   - ユニットテスト: `tests/unit/`
   - 統合テスト: `tests/integration/`
   - E2Eテスト: `tests/e2e/`

2. レッドフェーズ（失敗するテスト）
3. グリーンフェーズ（テストを通す最小実装）
4. リファクタリング

--play # E2Eテストの実行にPlaywright MCPを使用
```

#### 並列実装
```markdown
# 効率的な並列処理実装
specs/001-auth/tasks.mdの並列実行可能タスク[P]を同時に処理してください。

並列実行戦略：
1. 独立したファイルの同時作成
   - models/user.ts
   - models/session.ts
   - utils/validators.ts

2. MultiEditツールで一括編集
3. 並列でテスト実行

トークン効率化のため --uc フラグを使用してください。
```

#### インタラクティブ実装
```markdown
# 対話的な実装プロセス
specs/001-auth/tasks.mdを読み込み、実装を開始します。

各重要な設計判断で確認を取ります：
1. データベーススキーマの設計
2. API エンドポイントの命名
3. エラーハンドリング戦略
4. セキュリティ実装の詳細

不明な点があれば質問してください。
```

### 実装中のサポートプロンプト

#### エラー対応
```markdown
# エラーが発生した場合
認証テストが失敗しています。エラーメッセージ：
"TypeError: Cannot read property 'id' of undefined at auth.service.ts:45"

以下を実行してください：
1. エラーの根本原因分析 --seq
2. 関連するコードの確認 --serena
3. 修正案の提示
4. テストの再実行
```

#### コードレビュー
```markdown
# 実装済みコードのレビュー
src/services/authService.tsをレビューしてください。

以下の観点で評価：
- セキュリティ脆弱性
- パフォーマンス問題
- コード品質（SOLID原則）
- テストカバレッジ

改善点があれば修正してください。
```

#### パフォーマンス最適化
```markdown
# ボトルネックの特定と改善
認証処理が遅いので最適化してください。

1. プロファイリング実行
2. ボトルネック特定
3. 最適化案の提示
4. 実装と計測
5. ビフォーアフターの比較
```

#### UI生成
```markdown
# UIコンポーネントの作成
認証フォームのUIを作成してください。

要件：
- レスポンシブデザイン
- アクセシビリティ対応
- エラー表示
- ローディング状態

--magic # 21st.devのパターンを使用
--play  # ブラウザでの動作確認
```

### 進捗管理プロンプト

#### 日次進捗確認
```markdown
# 進捗レポート生成
本日の実装進捗をまとめてください。

含める内容：
- 完了したタスク
- 進行中のタスク
- ブロッカー
- 明日の予定
- 全体の進捗率
```

#### セッション管理
```markdown
# 作業セッションの保存
現在の作業状態を保存してください。

/sc:save
--serena # プロジェクトメモリに保存

含める内容：
- 現在のタスク状態
- 未解決の問題
- 次回の開始点
```

## 📊 実装のベストプラクティス

### 効率的な実装フロー
```markdown
1. コンテキスト読込
   /sc:load
   specs/*/tasks.md確認

2. タスク管理設定
   TodoWriteで全タスク登録
   優先順位と依存関係設定

3. 並列処理活用
   独立タスクは同時実行
   MultiEditで一括変更

4. 継続的検証
   各タスク完了時にテスト
   lint/typecheckの実行

5. 進捗管理
   完了タスクは即座に更新
   30分ごとにチェックポイント
```

---

# Phase 5: 検証 (Verification)

## 🔍 /verify-and-pr コマンド

### 基本使用法
```markdown
/verify-and-pr 001-auth "feat: 認証機能実装"
```

### 高度な検証（Super Claude拡張）
```markdown
# 包括的検証
/verify-and-pr 001-auth "feat: 認証機能実装" --comprehensive

# E2Eテスト
/verify-and-pr 001-auth "feat: 認証機能実装" --play

# セキュリティ監査
/verify-and-pr 001-auth "feat: 認証機能実装" --seq --security-focus

# ビジネス価値検証
/verify-and-pr 001-auth "feat: 認証機能実装" --business-panel
```

### Claude Codeプロンプト例（拡充版）

#### 基本的な検証
```markdown
# 標準検証とPR作成
/verify-and-pr 001-auth "feat: 認証機能実装"

以下の項目を検証してください：
1. 仕様書(spec.md)との適合性
2. 全タスクの完了状態
3. テストの実行と成功
4. コード品質（lint、typecheck）
5. セキュリティ基本チェック

問題がなければPRを作成してください。
```

#### 包括的品質検証
```markdown
# 詳細な品質分析
/verify-and-pr 001-auth "feat: 認証機能実装" --comprehensive

以下の詳細検証を実行してください：

## コード品質
- 複雑度分析
- 重複コード検出
- SOLID原則準拠
- デザインパターン適用

## セキュリティ
--seq # 深層セキュリティ分析
- OWASP Top 10チェック
- 認証フローの脆弱性
- データ暗号化確認
- インジェクション対策

## パフォーマンス
- レスポンスタイム測定
- メモリ使用量
- データベースクエリ最適化
- N+1問題の検出

## テストカバレッジ
- ユニットテスト: 目標90%
- 統合テスト: 主要フロー網羅
- E2Eテスト: ユーザージャーニー
```

#### E2Eテスト実行
```markdown
# ブラウザテストを含む検証
/verify-and-pr 001-auth "feat: 認証機能実装" --play

Playwright MCPを使用して以下をテスト：

1. ユーザー登録フロー
   - フォーム入力
   - バリデーション
   - 成功/失敗ケース

2. ログインフロー
   - 正常ログイン
   - エラーハンドリング
   - セッション管理

3. パスワードリセット
   - メール送信
   - トークン検証
   - パスワード更新

スクリーンショットを含むレポートを作成してください。
```

#### 自動修正付き検証
```markdown
# 問題の自動修正
/verify-and-pr 001-auth "feat: 認証機能実装" --auto-fix

検証中に以下の問題を発見した場合、自動修正：
1. Lintエラー
2. 型エラー
3. 軽微なセキュリティ問題
4. パフォーマンス最適化可能箇所

修正内容を記録し、修正後に再検証してください。
--validate  # 修正前に検証
--safe-mode # 安全モードで実行
```

#### ビジネス価値検証
```markdown
# ビジネス観点からの検証
/verify-and-pr 001-auth "feat: 認証機能実装" --business-panel

ビジネスパネルで以下を評価：
1. 仕様書のビジネス要件達成度
2. ユーザー価値の提供
3. 競争優位性への貢献
4. ROIの妥当性
5. スケーラビリティ

技術実装とビジネス価値の整合性を確認してください。
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

---

# 🎯 実践シナリオ

## Scenario 1: 新機能開発（ゼロから）

### Claude Codeプロンプト例
```markdown
# Step 1: プロジェクト準備
./scripts/create-new-feature.sh "ECレコメンド"を実行してください

# Step 2: 要件探索と仕様作成
/specify --brainstorm
「ECサイトにレコメンド機能を追加したい」
以下について対話的に探索してください：
- ユーザーの購買履歴分析
- レコメンドアルゴリズム選択
- パーソナライゼーション戦略

# Step 3: ビジネス価値分析
仕様書をビジネスパネルで分析してください
--business-panel
ROIと競争優位性の観点から評価

# Step 4: 実装計画とタスク生成
/plan --architecture=microservices
マイクロサービスアーキテクチャで設計

/tasks --parallel-optimization
並列実行可能なタスクに最適化

# Step 5: Claude Codeで実装
tasks.mdを読み込んで実装開始
TodoWriteでタスク管理
--seq --magic --serena # MCP活用

# Step 6: 品質検証とPR作成
/verify-and-pr recommendation "feat: レコメンド機能実装" --comprehensive
```

## Scenario 2: レガシーコード改善

### Claude Codeプロンプト例
```markdown
# Step 1: 現状分析（包括的）
プロジェクト全体の品質分析を実行してください
--seq    # 深層分析
--serena # シンボル解析

技術負債のリスクマトリクスを作成
循環依存を検出して視覚化

# Step 2: 改善戦略策定
リファクタリング計画を作成してください
/plan refactoring --incremental

優先順位：
1. 高リスク・高影響の部分
2. 頻繁に変更される部分
3. パフォーマンスボトルネック

# Step 3: 段階的リファクタリング
各モジュールを順次改善：

auth モジュール:
- SOLIDパターンを適用
- テストを追加
- パフォーマンス最適化

user モジュール:
- 同様の改善を実施

payment モジュール:
- 特にセキュリティに注意

# Step 4: 検証とPR
/verify-and-pr refactoring "refactor: SOLIDパターン適用" --comprehensive
リファクタリング前後の比較レポート作成
```

## Scenario 3: 緊急バグ修正

### Claude Codeプロンプト例
```markdown
# Step 1: 問題分析（迅速）
「認証が突然失敗する」問題を調査してください
--seq # 根本原因分析

デバッグ手順：
1. エラーログ確認
2. 最近の変更確認
3. 影響範囲特定

# Step 2: 影響範囲評価
auth-moduleの依存関係を分析
--serena # シンボル解析で影響範囲特定

影響を受けるコンポーネント：
- APIエンドポイント
- フロントエンド
- 他のサービス

# Step 3: 修正と検証
問題を修正してください
1. タイムアウト設定の調整
2. エラーハンドリング改善
3. テスト追加

即座にテスト実行して確認

# Step 4: 緊急PR作成
/verify-and-pr auth-fix "fix: 認証タイムアウトの修正" --security-focus
セキュリティへの影響を重点的に確認
```

## Scenario 4: パフォーマンス最適化

### Claude Codeプロンプト例
```markdown
# Step 1: パフォーマンス分析
アプリケーションのボトルネックを分析してください

プロファイリング実行：
- CPU使用率
- メモリ使用量
- データベースクエリ
- ネットワークレイテンシ

視覚的なレポート作成

# Step 2: 最適化戦略
クリティカルパスを特定して最適化計画作成

優先順位：
1. データベースクエリ最適化（N+1問題）
2. キャッシング戦略（Redis導入）
3. 非同期処理の導入
4. フロントエンド最適化

# Step 3: 実装
最適化を段階的に実装：

Phase 1: クイックウィン
- インデックス追加
- 単純なキャッシング

Phase 2: 構造的改善
- クエリ最適化
- Redis統合

MultiEditで効率的に実装

# Step 4: 計測と検証
最適化前後のパフォーマンス比較
/verify-and-pr performance "perf: クリティカルパス最適化" --performance-focus

ベンチマーク結果：
- レスポンスタイム: -60%
- スループット: +150%
```

---

# 📚 コマンドリファレンス

## ⚠️ 重要：実装状況について
- ✅ = 実装済み（実際に動作するコマンド）
- ❌ = 未実装（Claude Codeプロンプトで代替）

## 基本コマンド（Spec-Kit）

| コマンド | 状態 | 説明 | Claude Code代替方法 |
|---------|------|------|---------------------|
| `/specify` | ✅ | 仕様書生成 | `/specify "認証システム"` |
| `/plan` | ✅ | 実装計画作成 | `/plan` (spec.mdを自動読込) |
| `/tasks` | ✅ | タスク分解 | `/tasks` (plan.mdを自動読込) |
| `/verify-and-pr` | ✅ | 実装検証→PR作成 | `/verify-and-pr auth "feat: 認証機能実装"` |

## 分析・調査コマンド（Claude Code実行）

| タスク | Claude Codeプロンプト例 |
|--------|------------------------|
| **品質分析** | プロジェクト全体の品質分析を実行してください<br>--seq --serena |
| **技術負債評価** | 技術負債のリスクマトリクスとROI分析を作成してください |
| **依存関係分析** | 循環依存を検出し、グラフで視覚化してください |
| **セキュリティ監査** | OWASPトップ10に準拠したセキュリティ監査を実行してください |
| **パフォーマンス分析** | ボトルネック分析とプロファイリングを実行してください |

## Super Claude専用コマンド（Claude Code実行）

| タスク | Claude Codeプロンプト例 | 説明 |
|--------|------------------------|------|
| **セッション開始** | `/sc:load`<br>プロジェクトコンテキストを読み込んでください | セッション開始時の状態復元 |
| **セッション保存** | `/sc:save`<br>現在の作業状態を保存してください | 進捗のチェックポイント作成 |
| **ビジネス分析** | 仕様書をビジネスパネルで分析してください<br>--business-panel | 専門家による戦略分析 |
| **ブレインストーミング** | 要件を一緒に探索しましょう<br>--brainstorm | 対話的な要件定義 |
| **コード改善** | src/api/を改善してください<br>レスポンス速度を重視 | リファクタリングと最適化 |

## MCPサーバー活用ガイド

| MCPサーバー | 用途 | Claude Codeプロンプト例 |
|------------|------|------------------------|
| **Sequential** | 深層分析 | 複雑なバグの根本原因を分析してください<br>--seq |
| **Context7** | 公式ドキュメント | React Hooksのベストプラクティスを参照して実装<br>--c7 |
| **Serena** | シンボル操作 | 既存コードとの整合性を確認しながら実装<br>--serena |
| **Magic** | UI生成 | ログインフォームを作成してください<br>--magic |
| **Morphllm** | 一括変換 | 全てのクラスコンポーネントをフックに変換<br>--morph |
| **Playwright** | E2Eテスト | ユーザーフローをブラウザでテスト<br>--play |

## フラグ・オプション活用例

### 要件定義フェーズ
```markdown
# 曖昧な要件の探索
/specify --brainstorm
「何か便利な機能が欲しい」

# ビジネス価値を含む仕様
/specify --business-panel
「ROIを重視したシステム」

# 深い技術分析付き
/specify --think-hard
「複雑なリアルタイムシステム」
```

### 実装フェーズ
```markdown
# 並列処理で効率化
タスクを並列実行可能に最適化してください
--parallel-optimization

# MCP統合で品質向上
実装を開始してください
--seq --magic --serena

# トークン効率化
大規模な変更を実施してください
--uc --token-efficient
```

### 検証フェーズ
```markdown
# 包括的な品質検証
/verify-and-pr feature --comprehensive

# E2Eテスト重視
/verify-and-pr ui --play

# セキュリティ重視
/verify-and-pr auth --security-focus
```

---

# 🔧 高度な設定とカスタマイズ

## プロジェクト設定ファイル

```yaml
# .claude-config.yml
project:
  type: enterprise
  team_size: 8
  complexity: high

workflow:
  default_mode: claude_code  # Codexは必要時のみ
  phases:
    - specify: required
    - plan: required
    - tasks: required
    - implement: claude_code  # 基本はClaude Code
    - verify: comprehensive

quality_gates:
  coverage: 90
  security: high
  performance: optimized

mcp_servers:
  sequential: auto
  context7: auto
  serena: always  # セッション管理
  magic: ui_only
  morphllm: refactoring
  playwright: e2e_tests
```

## Claude Code実装設定

```yaml
# claude-code-config.yml
implementation:
  style: progressive  # 段階的実装
  testing: tdd        # テスト駆動
  parallelism: auto   # 自動並列化
  
session_management:
  auto_save: 30min
  checkpoint: task_complete
  memory: persistent

code_quality:
  lint: always
  typecheck: always
  test: after_each_task
  
mcp_strategy:
  analysis: sequential
  ui: magic
  refactoring: morphllm
  testing: playwright
  symbols: serena
```

---

# 🔧 トラブルシューティング

## よくある問題と解決策

### コマンド関連

| 問題 | 原因 | Claude Code解決策 |
|------|------|------------------|
| コマンドが動作しない | 未実装 | プロンプトで同等の指示を出す |
| 仕様書が生成されない | テンプレートなし | `/specify`で直接要件を記述 |
| タスクが並列化されない | 依存関係 | `--parallel-optimization`を明示的に指定 |

### 実装関連

| 問題 | Claude Code解決策 |
|------|------------------|
| **実装が遅い** | 並列処理を活用してください<br>MultiEditで一括編集<br>--orchestrate |
| **メモリ不足** | トークン効率化モードを使用<br>--uc --token-efficient |
| **テスト失敗** | 失敗の根本原因を分析してください<br>--seq<br>修正後、再テスト |
| **依存関係エラー** | package.jsonを確認して依存関係を解決<br>必要なパッケージをインストール |

### セッション関連

| 問題 | Claude Code解決策 |
|------|------------------|
| **セッション消失** | `/sc:save`で定期的に保存<br>30分ごとにチェックポイント |
| **コンテキスト不足** | `/sc:load`でプロジェクト読込<br>関連ファイルを明示的に読込 |
| **作業の継続** | 前回のtasks.mdとTodoWriteの状態を確認<br>中断した箇所から再開 |

---

# 🌟 ベストプラクティス

## Claude Code実装のコツ

### ✅ 推奨事項
1. **TodoWrite活用**: 3つ以上のタスクは必ずTodoWriteで管理
2. **並列処理**: 独立したタスクは常に並列実行
3. **MCP活用**: 適切なMCPサーバーで効率化
4. **継続的検証**: 各タスク完了時にテスト実行
5. **セッション管理**: 30分ごとに`/sc:save`

### ❌ アンチパターン
1. タスク管理なしで実装開始
2. 全て順次実行
3. MCPを使わず手動実装
4. 最後にまとめてテスト
5. セッション保存なし

## 効率的な開発フロー

```markdown
1. 準備
   - プロジェクトセットアップ
   - /sc:load でコンテキスト読込

2. 仕様と計画
   - /specify で要件定義
   - /plan で設計
   - /tasks でタスク分解

3. 実装
   - TodoWriteでタスク管理
   - 並列処理活用
   - MCP統合
   - 継続的テスト

4. 検証
   - /verify-and-pr で品質保証
   - 問題の自動修正
   - PR作成

5. 完了
   - /sc:save で状態保存
   - ドキュメント更新
```

---

**💡 Pro Tip**: このマニュアルは継続的に改善されます。実装で困ったことがあれば、Claude Codeに直接質問してください。自然言語での指示で、ほとんどのタスクが実行可能です。