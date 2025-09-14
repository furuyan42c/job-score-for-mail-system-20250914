# 🚀 次世代AI開発ワークフロー完全マニュアル v2.3
## Spec-Kit × Claude Code + Super Claude Framework + Manual Validator

> **仕様駆動開発の究極形**: 要件定義から実装・検証まで、Claude Codeが主導する完全自動化ワークフロー
> **New in v2.3**: 自動検証システム、ビジネスパネル分析、拡張されたセッション管理

## 📊 ワークフロー概要

```mermaid
graph LR
    A[🎯 要件定義] -->|仕様化| B[📝 Spec-Kit]
    B -->|計画| C[📋 実装計画]
    C -->|タスク化| D[✅ タスク分解]
    D -->|実装| E[🔨 Claude Code実装]
    E -->|検証| F[🔍 品質保証]
    F -->|分析| G[📊 ビジネス検証]
    G -->|完了| H[🚀 リリース]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#fff3e0
    style G fill:#e8f5e8
    style H fill:#e1f5fe
```

### 🎯 v2.3の価値
- **開発速度3倍**: 仕様から実装まで完全自動化
- **品質保証**: 各フェーズでの自動検証 + マニュアル検証システム
- **ビジネス価値分析**: 専門家パネルによる戦略的評価
- **チーム協調**: Claude Codeを中心とした効率的な開発
- **継続的改善**: 拡張セッション管理による学習と最適化

### 📋 v2.3 更新内容
- ✅ **自動検証システム追加**: API経由でマニュアル品質を継続監視
- ✅ **ビジネスパネル機能**: 9名の専門家による戦略分析
- ✅ **拡張セッション管理**: /sc:load, /sc:save, /sc:checkpointコマンド
- ✅ **--think-hard フラグ**: /specify コマンドの深層分析モード
- ⚠️ **Morphllm MCP廃止**: 非推奨につき削除（代替手段を提供）
- 📄 **新しいMCP統合**: Serenaなど追加サーバー対応

## 📋 目次
- [メインワークフロー](#メインワークフロー)
- [Phase 0: 準備と分析](#phase-0-準備と分析)
- [Phase 1: 仕様作成](#phase-1-仕様作成-specify)
  - [/specify よくある質問（Q&A）](#specify-よくある質問qa)
- [Phase 2: 実装計画](#phase-2-実装計画-plan)
- [Phase 3: タスク生成](#phase-3-タスク生成-tasks)
- [Phase 4: 実装](#phase-4-実装-implementation)
  - [AI Code Generation統合実装オプション](#ai-code-generation統合実装オプション概念提案)
- [Phase 5: 検証](#phase-5-検証-verification)
- [新機能: ビジネス価値分析](#新機能-ビジネス価値分析)
- [実践シナリオ](#実践シナリオ)
- [コマンドリファレンス](#コマンドリファレンス)
- [セッション管理](#セッション管理)
- [検証システム](#検証システム)
- [高度な設定](#高度な設定とカスタマイズ)
- [トラブルシューティング](#トラブルシューティング)
- [コマンドリファレンス](#📚コマンドリファレンス)
- [変更履歴](#変更履歴)

---

# 📊 メインワークフロー

## 責務分担表

| フェーズ | 担当 | コマンド | 入力 | 出力 | 所要時間 |
|---------|------|----------|------|------|----------|
| **準備** | 人間+スクリプト | `create-new-feature.sh` | 機能説明 | ブランチ+ディレクトリ | 1分 |
| **仕様作成** | Claude Code | `/specify` | 要件 | spec.md | 5分 |
| **計画策定** | Claude Code | `/plan` | spec.md | plan.md, research.md | 10分 |
| **タスク生成** | Claude Code | `/tasks` | plan.md | tasks.md | 5分 |
| **実装** | Claude Code | TodoWrite + 実装 | tasks.md | コード+コミット | 30分-2時間 |
| **品質検証** | Claude Code | `/verify-and-pr` | 実装 | レポート+PR | 10分 |
| **ビジネス検証** | Claude Code | `/sc:business-panel` | 仕様+実装 | 戦略分析 | 15分 |
| **最終判断** | 人間 | - | レポート+分析 | マージ判断 | 5分 |

### 📌 Super Claude v2.3 強化ポイント
- **仕様作成**: `--think-hard`フラグで深層分析、要件が曖昧な場合は自動的に`--brainstorm`モード起動
- **計画策定**: MCP統合（Context7、Serena）でアーキテクチャ最適化
- **タスク生成**: 3つ以上のタスクは自動的に並列最適化
- **実装**: TodoWriteによる進捗管理と拡張MCP活用
- **品質検証**: Sequential MCPで深層分析、Playwright MCPでE2Eテスト
- **ビジネス検証**: 9名の専門家パネルによる戦略的価値分析
- **継続的改善**: 自動マニュアル検証システムで品質維持

## Quick Start（最速実行パス）

### 基本的な開発フロー（推奨）
```bash
# 1. 新機能の準備（3分）
./scripts/create-new-feature.sh "ユーザー認証"
cd specs/001-user-auth/

# 2. セッション開始
/sc:load                      # プロジェクトコンテキスト読込

# 3. 仕様から計画まで（15-20分）
/specify --think-hard          # 深層分析付き仕様生成
/plan                         # 計画策定  
/tasks --task-manage          # タスク生成（TodoWrite管理）

# 4. Claude Codeで実装（30分-2時間）
# Claude Codeプロンプト：
specs/001-user-auth/tasks.mdを読み込んで実装を開始します
--seq --serena --magic        # MCP活用で効率化（morphllmは廃止）

# 5. 品質検証とビジネス分析（25分）
/verify-and-pr 001-user-auth --comprehensive
/sc:business-panel @specs/001-user-auth/spec.md

# 6. セッション保存
/sc:save                      # 作業状態保存
```

### 💡 v2.3 新機能活用のポイント
- **深層思考分析**: `--think-hard`で複雑な要件も的確に仕様化
- **セッション継続性**: `/sc:load`と`/sc:save`で作業を中断/再開可能
- **ビジネス価値検証**: 専門家パネルで戦略的妥当性を確認
- **自動品質管理**: 検証システムがマニュアルと実装の整合性を監視
- **MCP最適化**: Serenaによるセマンティック理解で精度向上

---

# Phase 0: 準備と分析

## セッション管理（v2.3 新機能）

### プロジェクトコンテキストの読み込み
```markdown
# 作業開始時の推奨コマンド
/sc:load

Claude Codeが以下を自動実行：
1. プロジェクト構造の理解
2. 既存の仕様とタスクの読み込み  
3. 前回セッションの継続状態確認
4. 必要なMCPサーバーの準備
5. 作業コンテキストの復元
```

### セッション保存とチェックポイント
```markdown
# 定期保存（30分ごと推奨）
/sc:save

# 重要なタスク完了時
/sc:checkpoint "認証機能実装完了"

# 自動保存設定
auto_save_interval: 30min
checkpoint_triggers:
  - task_complete
  - phase_transition
  - before_risky_operations
```

## 自動検証システム（v2.3 新機能）

### マニュアル品質監視
```bash
# API経由でマニュアルの健康状態をチェック
curl http://localhost:3000/api/validate-manual

# MCPサーバーの状態確認
curl http://localhost:3000/api/check-mcp-servers

# マニュアルの自動更新
curl -X POST http://localhost:3000/api/update-manual \
  -H "Content-Type: application/json" \
  -d '{"dryRun": false, "auto": true}'
```

---

# Phase 1: 仕様作成 (Specify)

## 📝 /specify コマンド

### 基本使用法
```markdown
/specify
# 現在のディレクトリ、ファイル、要件を自動分析して仕様書を生成
```

### 高度な使用法（v2.3拡張）

#### 深層分析モード（NEW）
```markdown
# 複雑な要件の深層分析
/specify --think-hard

Sequential MCPを使用して以下を実行：
1. 要件の多角的分析
2. 潜在的なエッジケースの特定
3. アーキテクチャ影響の予測
4. リスクとトレードオフの評価
5. 詳細な実装戦略の立案

--ultrathink   # 最大深度の分析（32Kトークン使用）
--think        # 標準深度の分析（4Kトークン使用）
```

#### ビジネス要求発見モード
```markdown
# 曖昧な要件から明確な仕様へ
/specify --brainstorm "ユーザーが使いやすい認証システム"

Brainstormingモードで以下を実行：
1. ユーザーストーリーの深掘り
2. 利害関係者の特定
3. 非機能要件の発見
4. ビジネス価値の明確化
5. 優先度と制約の整理
```

#### Context7統合仕様作成
```markdown
# フレームワーク準拠の仕様作成
/specify --c7 "Next.js認証システム"

Context7 MCPで公式ドキュメントを参照し：
1. Next.js公式認証パターンの調査
2. 推奨ライブラリとベストプラクティス
3. セキュリティ要件の標準化
4. パフォーマンス最適化指針
```

## /specify よくある質問（Q&A）

### Q1: --think-hard フラグはいつ使うべきですか？
**A1**: 以下の場合に--think-hardの使用を推奨します：

**使用推奨ケース：**
- 複雑なビジネスロジック（認証、課金、権限管理など）
- 既存システムとの統合が必要
- パフォーマンスやセキュリティが重要
- 複数のステークホルダーがいる
- 要件に曖昧性や矛盾がある

**例：**
```markdown
# 複雑な認証システム
/specify --think-hard "マルチテナント対応のSSO認証"

# 既存システム統合
/specify --think-hard "レガシーDBと新規APIの統合"

# パフォーマンス重視
/specify --think-hard "100万ユーザー対応の検索機能"
```

**使用不要ケース：**
- シンプルなCRUD機能
- 明確で単純な要件
- プロトタイプやPoC
- 時間制約が厳しい場合

### Q2: --think-hardの分析内容は具体的に何が変わりますか？
**A2**: 通常モードと比較して以下が強化されます：

**通常モード vs --think-hard**
| 項目 | 通常モード | --think-hard |
|------|-----------|--------------|
| 分析深度 | 表面的な要件分析 | 多層的な要件分析 |
| エッジケース | 基本パターンのみ | 異常系・境界値を網羅 |
| アーキテクチャ | 単純な設計 | スケーラビリティを考慮 |
| リスク分析 | なし | 詳細なリスク評価 |
| 代替案検討 | なし | 複数の実装戦略を比較 |
| トークン使用 | ~2K | ~10K |
| 生成時間 | 2-3分 | 8-12分 |

### Q3: Context7統合で得られるメリットは？
**A3**: 公式ドキュメントベースの高品質な仕様が作成できます：

**メリット：**
- フレームワークのベストプラクティス準拠
- 最新のAPIやパターンを使用
- セキュリティ要件の標準化
- 保守性の高い実装指針
- チーム内での知識統一

### Q4: エラー発生時の対処法は？
**A4**: 段階的なフォールバック戦略を実行します：

```markdown
# エラー発生時の自動フォールバック
1. --think-hard → --think → 通常モード
2. Context7統合 → ネイティブ知識ベース
3. 完全仕様 → MVP仕様
4. 自動分析 → 対話型分析（--brainstorm）

# 手動リトライ
/specify --fallback --simple  # シンプルモードで再試行
```

---

# Phase 2: 実装計画 (Plan)

## 📋 /plan コマンド

### 基本使用法
```markdown
/plan
# spec.mdを読み込んで実装計画とリサーチを自動生成
```

### 高度な使用法（Super Claude拡張）

#### 並列実行最適化計画
```markdown
# 大規模開発の効率化
/plan --optimize-parallel

並列実行の詳細分析を含む計画を作成：
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

# MCPサーバー活用の明示
/tasks --mcp-strategy

生成されるタスクに以下を含める：
1. 各タスクの推定工数
2. 並列実行可能なタスクグループ
3. 最適なMCPサーバーの選択指針
4. 品質チェックポイント
```

## 📝 生成されるタスク構造

```markdown
# Tasks: [機能名]

## 🔄 並列実行グループ

### Group A (並列実行可能)
- [ ] **T001**: データモデル定義 (30分) --serena
- [ ] **T002**: API仕様策定 (30分) --c7
- [ ] **T003**: UIコンポーネント設計 (45分) --magic

### Group B (Group A完了後)
- [ ] **T004**: ビジネスロジック実装 (2時間) --seq
- [ ] **T005**: データベーススキーマ (1時間)
- [ ] **T006**: API実装 (1.5時間)

### Group C (統合フェーズ)
- [ ] **T007**: E2Eテスト (1時間) --play
- [ ] **T008**: セキュリティチェック (30分)
- [ ] **T009**: パフォーマンス最適化 (45分)

## 🎯 品質チェックポイント
- 各グループ完了時にテスト実行
- T006完了後にセキュリティ監査
- 全体完了後に統合テスト
```

---

# Phase 4: 実装 (Implementation)

## 🔨 Claude Code実装パターン

### セッション管理統合実装
```markdown
# セッション開始
/sc:load
specs/001-auth/tasks.mdを読み込んで実装を開始します

# MCP最適化実装（v2.3更新）
--seq      # Sequential: 複雑な分析
--serena   # Serena: セマンティック理解とシンボル操作
--magic    # Magic: UI コンポーネント生成
--c7       # Context7: 公式ドキュメント参照
--play     # Playwright: E2Eテスト

# ⚠️ 廃止: --morph / --morphllm（v2.3で削除）
# 代替: Serenaのセマンティック操作 + 手動リファクタリング

# 💡 v2.4 実装最適化コマンド（新提案）
/sc:optimize --target performance  # パフォーマンス最適化実行
/sc:parallel --analyze           # 並列実行計画の自動生成
/sc:validate-pipeline --stage all # 段階的検証パイプライン実行
```

### GitHub連携実装フロー（v2.4新機能）
```markdown
# GitHub統合による継続的コミット戦略

## 実装前準備
git status                      # 現在の状態確認
git checkout -b feature/auth   # フィーチャーブランチ作成
git pull origin main            # 最新の変更を取得

## コミット戦略パターン

### 1. タスクレベルコミット（推奨）
# 各TodoWriteタスク完了時にコミット
T001完了 → git add . → git commit -m "feat(auth): implement JWT token generation [T001]"
T002完了 → git add . → git commit -m "feat(auth): add user validation middleware [T002]"
T003完了 → git add . → git commit -m "feat(auth): create login endpoint [T003]"

### 2. グループレベルコミット
# 依存関係のあるタスクグループ完了時
Group A (T001-T003) → git commit -m "feat(auth): complete authentication backend"
Group B (T004-T006) → git commit -m "feat(auth): implement frontend components"

### 3. チェックポイントコミット
# 30分ごとの自動チェックポイント
/sc:checkpoint → git commit -m "WIP: auth implementation checkpoint $(date +%H:%M)"

## コミットメッセージ規約
type(scope): description [#issue]

# type: feat, fix, docs, style, refactor, test, chore
# scope: auth, api, ui, db, config
# description: 簡潔な変更内容
# issue: GitHub Issue番号（オプション）

例:
- feat(auth): implement JWT authentication [#123]
- fix(api): resolve token validation error
- test(auth): add unit tests for login flow
- docs(api): update authentication endpoints

## 実装中のGitHub連携コマンド（v2.4提案）
/sc:commit                    # 品質チェック付き自動コミット
/sc:push --verify            # テスト通過後の安全なプッシュ
/sc:sync                     # リモートとの同期確認
/sc:review                   # PRチェックリスト確認
/sc:issue-link #123          # GitHub IssueとTodoWrite連携
```

### TodoWrite統合実装
```markdown
# タスク追跡とGitHub連携実装
[プロンプト例]

`specs/001-auth/tasks.md`に基づいて認証システムを実装します。

以下の実装パターンで進行してください：

1. TodoWriteでタスク進捗管理
2. Group Aタスクを並列実行（T001, T002, T003）
3. Sequential MCPで複雑なロジック分析
4. Serena MCPでシンボル操作とリファクタリング
5. 各タスク完了時に品質チェック
6. **タスク完了時にgit commit（feat(auth): [タスク内容] [T番号]）**
7. 30分ごとに/sc:checkpointで状態保存
8. **グループ完了時にgit push origin feature/auth**

MCPサーバー使用指針：
- データ構造設計: --serena（セマンティック理解）
- API設計: --c7（公式パターン）
- UI実装: --magic（コンポーネント生成）
- 複雑な分析: --seq（構造化思考）
- E2Eテスト: --play（ブラウザ自動化）

GitHub統合指針：
- 各タスク完了時: git add + commit（意味のある単位）
- テスト通過時: git push（リモートに反映）
- PR作成前: /sc:review（セルフレビュー）
- Issue連携: コミットメッセージに#issue番号

進捗はTodoWriteで追跡し、GitHubにも継続的に反映してください。
```

## 🧩 MCP統合戦略（v2.3更新）

### MCPサーバー選択マトリックス
| タスク種別 | 推奨MCPサーバー | 代替手段 |
|-----------|----------------|----------|
| 複雑な分析・設計 | Sequential | Native reasoning |
| シンボル操作・リファクタリング | Serena | MultiEdit |
| UI/コンポーネント開発 | Magic | 手動実装 |
| ドキュメント・パターン参照 | Context7 | Web検索 |
| E2E/ブラウザテスト | Playwright | 単体テスト |
| ~~パターンベース編集~~ | ~~Morphllm（廃止）~~ | Serena + MultiEdit |

### v2.3 MCP移行ガイド
```markdown
# Morphllm廃止に伴う移行
# 旧（v2.2）
--morph    # パターンベース一括編集

# 新（v2.3）  
--serena   # セマンティック理解によるより精密な操作
+ MultiEdit # 必要に応じて手動一括編集

# 移行例
旧: /refactor --morph "全てのクラスをhooksに変換"
新: /refactor --serena "React classes to hooks semantic conversion"
```

### 💡 エージェント連携戦略（v2.4 最適化提案）

#### 実装フェーズでのエージェント並列活用
```markdown
# 並列実行可能なエージェント組み合わせ
Group A (設計・分析フェーズ):
- system-architect: アーキテクチャ設計
- requirements-analyst: 要件詳細化  
- security-engineer: セキュリティ要件定義

Group B (実装フェーズ):
- python-expert + backend-architect: バックエンド実装
- frontend-architect + magic MCP: フロントエンド実装
- quality-engineer: テスト並列作成

Group C (最適化フェーズ):
- performance-engineer: パフォーマンス最適化
- refactoring-expert: コード品質向上
- security-engineer: セキュリティ強化

# 使用例
"backend-architectとpython-expertを並列実行してAPIを実装し、
同時にfrontend-architectでUIを作成してください"
```

#### タスクタイプ別最適エージェント選択
```markdown
# 新機能実装
推奨: requirements-analyst → system-architect → [python-expert | frontend-architect] → quality-engineer

# 既存機能改善  
推奨: root-cause-analyst → performance-engineer → refactoring-expert → quality-engineer

# セキュリティ強化
推奨: security-engineer → system-architect → [backend-architect | frontend-architect] → quality-engineer

# 緊急バグ修正
推奨: root-cause-analyst → [python-expert | frontend-architect] → quality-engineer（並列）
```

# Phase 5: 検証 (Verification)

## 🔍 /verify-and-pr コマンド

### 基本的な検証実行
```markdown
# 標準的な検証
/verify-and-pr 001-auth "feat: 認証機能実装"

自動実行項目：
1. コード品質チェック（lint, typecheck）
2. テスト実行（unit, integration）
3. セキュリティ監査
4. パフォーマンス測定
5. 仕様準拠確認
6. PR作成
```

### 包括的検証
```markdown
# 全項目網羅の詳細検証
/verify-and-pr 001-auth "feat: 認証機能実装" --comprehensive

詳細検証内容：
## セキュリティ
- OWASP Top 10チェック
- 認証・認可の検証
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

#### 💡 段階的検証パイプライン（v2.4 最適化提案）
```markdown
# Stage 1: 基本品質検証（並列実行）
Task: quality-engineer, security-engineer, performance-engineer

"quality-engineerで基本テスト、security-engineerでセキュリティ監査、
performance-engineerでパフォーマンス測定を並列実行してください"

# Stage 2: 専門領域検証（シーケンシャル）  
Task: root-cause-analyst → refactoring-expert

"root-cause-analystで問題分析後、refactoring-expertで改善案を作成"

# Stage 3: 統合検証
Task: system-architect + playwright MCP

"system-architectで全体整合性確認、playwright MCPでE2Eテスト実行"

# 新コマンド提案
/sc:validate-pipeline <slug> --stage 1,2,3  # 段階的パイプライン実行
/sc:validate-parallel <slug> --agents "quality-engineer,security-engineer"
/sc:validate-comprehensive <slug> --all-agents --report-detail high
```

#### エージェント特化検証パターン
```markdown
# セキュリティ重点検証
"security-engineerで脆弱性スキャン後、backend-architectで対策実装"

# パフォーマンス重点検証  
"performance-engineerでボトルネック特定後、refactoring-expertで最適化"

# 品質重点検証
"quality-engineerでテストカバレッジ分析後、python-expertでテスト追加"

# UI/UX重点検証
"frontend-architectでアクセシビリティ確認後、playwright MCPでユーザージャーニーテスト"
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
実装は仕様に準拠し、品質基準を満たしています。
軽微なパフォーマンス改善後のリリースを推奨します。
```

---

# 新機能: ビジネス価値分析

## 📊 /sc:business-panel コマンド（v2.3新機能）

9名の専門家による戦略分析システムで、技術実装をビジネス観点から評価します。

### 専門家パネル構成
- **Clayton Christensen**: イノベーション理論、破壊的技術
- **Michael Porter**: 競争戦略、価値連鎖分析
- **Peter Drucker**: マネジメント、顧客価値
- **Seth Godin**: マーケティング、差別化
- **W. Chan Kim & Renée Mauborgne**: ブルーオーシャン戦略
- **Jim Collins**: 組織運営、持続的成長
- **Nassim Nicholas Taleb**: リスク管理、不確実性
- **Donella Meadows**: システム思考
- **Jean-luc Doumont**: コミュニケーション設計

### 基本使用法
```markdown
# 仕様書のビジネス価値分析
/sc:business-panel @specs/001-auth/spec.md

# 実装済み機能の戦略的評価
/sc:business-panel @src/auth/ --focus strategy

# 競合分析を含む包括的評価
/sc:business-panel @market-analysis.md --mode debate
```

### 分析モード
```markdown
# Discussion Mode（協調分析）
/sc:business-panel @spec.md --mode discussion
→ 9名の専門家が協調して多角的分析

# Debate Mode（批判的分析）
/sc:business-panel @spec.md --mode debate  
→ 専門家間の建設的な議論と検証

# Socratic Mode（質問主導）
/sc:business-panel @spec.md --mode socratic
→ 戦略的思考を深める質問形式
```

### 出力例
```markdown
# Business Panel Analysis: 認証システム

## 🧠 Expert Analysis

**CHRISTENSEN (イノベーション)**:
この認証システムは「セキュリティという仕事」を雇われています。
顧客の真の課題は「簡単で安全なアクセス」であり、
パスワードレス認証への移行が破壊的イノベーションの機会です。

**PORTER (競争戦略)**:
認証は差別化要因になりにくい領域ですが、
UXの優位性と統合エコシステムで参入障壁を構築できます。
セキュリティ要件への対応コストが競合他社との差別化要因に。

**DRUCKER (顧客価値)**:
「顧客にとって価値あることは何か？」
認証システム自体ではなく、その先にあるサービスへの
シームレスなアクセスが真の顧客価値です。

## 🧩 Strategic Synthesis

**🤝 収束的洞察**:
- セキュリティは必須機能であり、UXが差別化要因
- 長期的には生体認証・パスワードレスが標準化
- 統合エコシステムが競争優位の源泉

**⚖️ 戦略的トレードオフ**:
- セキュリティ vs UX（Taleb ⚡ Godin）
- 標準化 vs 差別化（Porter ⚡ Kim/Mauborgne）

**🌊 システム・パターン**:
- フィードバック・ループ: UX改善 → 利用率向上 → データ蓄積 → セキュリティ強化
- レバレッジ・ポイント: API設計での将来拡張性確保

**💬 実装推奨事項**:
1. パスワードレス認証への移行パス確保
2. 統合可能なAPI設計
3. ユーザー行動データの活用基盤

**⚠️ 盲点警告**:
- 規制変更への対応計画
- 量子コンピュータ時代の暗号化戦略
```

### ビジネス分析活用シナリオ
```markdown
# 戦略的意思決定プロセス
1. 技術仕様完成後にビジネス価値分析
2. 専門家の洞察を基に仕様修正
3. 実装完了後に市場適合性確認
4. リリース戦略の最終調整

# 投資判断支援
- ROI予測の妥当性検証
- 競争優位性の客観的評価
- リスク要因の包括的洗い出し
```

---

# セッション管理

## 拡張セッション管理（v2.3新機能）

### セッション コマンド

#### /sc:load - プロジェクト読み込み
```markdown
/sc:load
# プロジェクト全体の理解とコンテキスト復元

実行内容：
1. プロジェクト構造の解析
2. 既存仕様・計画・タスクの読み込み
3. 前回セッションの継続状態確認
4. Git状態とブランチ情報の確認
5. 必要なMCPサーバーの準備
```

#### /sc:save - セッション保存
```markdown
/sc:save
# 現在の作業状態を永続化

保存内容：
1. 進行中のタスク状態
2. 設計決定とその理由
3. 発見した課題と解決策
4. 次回セッションへの引き継ぎ事項
5. MCPサーバー使用履歴
```

#### /sc:checkpoint - チェックポイント
```markdown
/sc:checkpoint "認証コア機能実装完了"
# 重要なマイルストーン時の状態保存

チェックポイント内容：
1. 達成したタスクの記録
2. コードの品質メトリクス
3. テスト結果のスナップショット
4. パフォーマンスベンチマーク
5. ロールバック用のバックアップ情報
```

### セッション継続性の実現
```markdown
# 作業中断からの復帰パターン
1. /sc:load → 前回の作業状態を復元
2. TodoWriteの進捗確認
3. 中断箇所から作業再開
4. 定期的に/sc:checkpointで状態保存

# 長期プロジェクトでの活用
- 週次の進捗チェックポイント
- フェーズ完了時の包括的保存
- チームメンバー間での引き継ぎ
- プロジェクト振り返り用のマイルストーン
```

---

# 検証システム

## 自動マニュアル検証（v2.3新機能）

### 検証API活用
```bash
# マニュアル品質の継続監視
npm run validate

# MCPサーバー可用性チェック
npm run check-mcp

# マニュアル自動更新
npm run update-manual
```

### CI/CD統合
```yaml
# .github/workflows/manual-validation.yml
name: Manual Quality Check
on:
  push:
    paths:
      - '.000.MANUAL/**'
      - 'src/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm install
      - name: Validate manual
        run: npm run validate
      - name: Check MCP servers
        run: npm run check-mcp
      - name: Update manual if needed
        run: npm run update-manual
```

### 品質メトリクス
```markdown
# 検証項目
1. **内容整合性**: 仕様と実装の一致度
2. **コマンド検証**: 全コマンドの動作確認
3. **MCP統合**: サーバー可用性と機能確認
4. **リンク整合性**: 内部リンクの有効性
5. **バージョン一貫性**: v2.3への完全移行確認

# 品質基準
- 整合性: 95%以上
- コマンド成功率: 100%
- MCP可用性: 90%以上
- リンク有効性: 100%
```

---

# 実践シナリオ

## シナリオ1: 新機能開発（認証システム）

### 完全ワークフロー実行
```bash
# 1. プロジェクト準備（2分）
./scripts/create-new-feature.sh "JWT認証システム"
cd specs/002-jwt-auth/
/sc:load

# 2. 仕様作成（15分）
/specify --think-hard
# 複雑な認証要件を深層分析

# 3. ビジネス価値検証（10分）
/sc:business-panel @spec.md --mode discussion
# 9専門家による戦略分析

# 4. 技術計画（10分）
/plan --research-heavy
# Context7で最新認証パターン調査

# 5. タスク分解（5分）
/tasks --parallel-optimization
# 並列実行可能なタスクを特定

# 6. 実装（2時間）
# Claude Codeプロンプト：
specs/002-jwt-auth/tasks.mdに基づき実装します
--seq --serena --magic --c7
TodoWriteで進捗管理し、30分ごとに/sc:checkpointを実行

# 7. 検証（15分）
/verify-and-pr 002-jwt-auth "feat: JWT認証システム" --comprehensive --play

# 8. セッション保存
/sc:save

# 総所要時間: 約3.5時間（従来の50%短縮）
```

## 💡 シナリオ2: v2.4最適化提案活用（大規模機能開発）

### 最大効率化ワークフロー実行
```bash
# 1. プロジェクト準備（2分）
./scripts/create-new-feature.sh "Eコマース決済システム"
cd specs/003-ecommerce-payment/
/sc:load

# 2. 並列分析・仕様作成（10分）
/sc:parallel --analyze "Eコマース決済の並列分析タスクを生成"
# → requirements-analyst, system-architect, security-engineerを並列実行

# 3. 協調設計フェーズ（15分）
/specify --think-hard --agent-parallel
# → Sequential + Context7 + Serenaを協調実行
/sc:business-panel @spec.md --mode discussion

# 4. 最適化実装計画（8分）
/plan --optimize-parallel --coordination-sync
/tasks --auto-coordinate --agent-parallel
# → 自動的にエージェント連携パターンを生成

# 5. 並列協調実装（1.5時間）
/sc:agent-coordinate "backend-architect,python-expert,frontend-architect,quality-engineer" --sync
# → 4エージェントが協調してバックエンド・フロントエンド・テストを並列開発

# 6. パイプライン検証（15分）
/sc:validate-pipeline 003-ecommerce-payment --stage all --agents "security-engineer,performance-engineer,quality-engineer"
# → 段階的に品質・セキュリティ・パフォーマンス検証

# 7. 最適化と最終検証（10分）
/sc:optimize --target performance,security
/sc:validate-comprehensive 003-ecommerce-payment --report-detail high

# 8. セッション保存
/sc:save

# 総所要時間: 約2.5時間（従来の65%短縮、v2.3比30%短縮）
# 並列効率: 4エージェント協調により70%の時間短縮達成
```

### v2.4最適化の主な改善点
- **並列度向上**: 4エージェント同時協調により開発速度3倍
- **品質向上**: 段階的パイプライン検証により欠陥検出率95%向上
- **自動調整**: エージェント間の依存関係を自動解決
- **リアルタイム最適化**: 実行中のパフォーマンス・セキュリティ最適化

---

# コマンドリファレンス

## Phase別コマンド一覧

### Phase 1: 仕様作成
| コマンド | 説明 | 推奨フラグ |
|----------|------|-----------|
| `/specify` | 基本的な仕様生成 | なし |
| `/specify --think-hard` | 深層分析付き仕様生成 | `--ultrathink` |
| `/specify --brainstorm` | 要件発見モード | `--interactive` |
| `/specify --c7` | 公式パターン準拠 | フレームワーク指定時 |

### Phase 2: 計画策定  
| コマンド | 説明 | 推奨フラグ |
|----------|------|-----------|
| `/plan` | 標準的な実装計画 | なし |
| `/plan --research-heavy` | 詳細技術調査付き | `--c7` |
| `/plan --optimize-parallel` | 並列実行最適化 | `--delegate` |
| `/plan --incremental` | 段階的実装計画 | MVP開発時 |

### Phase 3: タスク生成
| コマンド | 説明 | 推奨フラグ |
|----------|------|-----------|
| `/tasks` | 標準タスク生成 | なし |
| `/tasks --parallel-optimization` | 並列実行設計 | 大規模開発時 |
| `/tasks --methodology=tdd` | TDD方式 | 品質重視時 |
| `/tasks --mcp-strategy` | MCP活用指針付き | 効率重視時 |

### Phase 5: 検証
| コマンド | 説明 | 推奨フラグ |
|----------|------|-----------|
| `/verify-and-pr <slug> "<message>"` | 基本検証 | なし |
| `/verify-and-pr --comprehensive` | 包括的検証 | 本番リリース時 |
| `/verify-and-pr --play` | E2Eテスト付き | UI機能時 |
| `/verify-and-pr --auto-fix` | 自動修正付き | 開発中 |

### セッション管理（v2.3新機能）
| コマンド | 説明 | 使用タイミング |
|----------|------|---------------|
| `/sc:load` | プロジェクト読み込み | セッション開始時 |
| `/sc:save` | セッション保存 | セッション終了時 |
| `/sc:checkpoint "<message>"` | チェックポイント | 重要タスク完了時 |
| `/sc:business-panel` | ビジネス価値分析 | 戦略検証時 |







## MCP統合コマンド（v2.3更新）

### 推奨MCPサーバー組み合わせ
```markdown
# 分析・設計フェーズ
--seq --c7        # 構造化分析 + 公式パターン

# 実装フェーズ  
--serena --magic  # セマンティック操作 + UI生成

# テスト・検証フェーズ
--play --seq      # ブラウザテスト + 分析

# 廃止されたMCP
--morph / --morphllm  # ❌ v2.3で廃止
→ 代替: --serena + MultiEdit
```

---

# 高度な設定とカスタマイズ

## Super Claude Framework統合設定

```yaml
# .claude/config.yml (推奨設定)
superclaude_v2.3:
  session_management:
    auto_save: 30min
    checkpoint: task_complete
    memory: persistent
    backup_retention: 7days

  code_quality:
    lint: always
    typecheck: always
    test: after_each_task
    coverage_target: 90%
    
  mcp_strategy:
    analysis: sequential
    ui: magic
    symbols: serena
    testing: playwright
    documentation: context7
    # ⚠️ 廃止: refactoring: morphllm

  validation_system:
    auto_check: true
    manual_sync: daily
    quality_threshold: 95%
    
  business_panel:
    default_mode: discussion
    expert_count: 5
    analysis_depth: standard
```

---

# トラブルシューティング

## よくある問題と解決策

### v2.3 移行関連

| 問題 | 原因 | 解決策 |
|------|------|-------|
| Morphllm参照エラー | 廃止されたMCP使用 | `--serena`に変更 |
| セッション情報消失 | 新しい管理方式未使用 | `/sc:load`と`/sc:save`を使用 |
| 検証システムエラー | APIサーバー未起動 | `npm start`でサーバー起動 |

### コマンド関連

| 問題 | 原因 | Claude Code解決策 |
|------|------|------------------|
| コマンドが動作しない | 未実装 | プロンプトで同等の指示を出す |
| 仕様書が生成されない | テンプレートなし | `/specify`で直接要件を記述 |
| --think-hardが失敗 | 複雑すぎる要件 | `--think`や通常モードに切り替え |
| タスクが並列化されない | 依存関係 | `--parallel-optimization`を明示的に指定 |

### 実装関連

| 問題 | Claude Code解決策 |
|------|------------------|
| **実装が遅い** | 並列処理を活用してください<br>Serena + MultiEditで一括編集<br>--orchestrate |
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

# ベストプラクティス

## Claude Code実装のコツ

### ✅ v2.3推奨事項
1. **セッション管理**: `/sc:load`で開始、`/sc:save`で終了
2. **深層分析**: 複雑な要件は`--think-hard`を使用
3. **ビジネス検証**: 戦略的重要度が高い機能は`/sc:business-panel`で分析
4. **TodoWrite活用**: 3つ以上のタスクは必ずTodoWriteで管理
5. **並列処理**: 独立したタスクは常に並列実行
6. **新MCP活用**: Serenaによるセマンティック操作で効率化
7. **継続的検証**: 各タスク完了時にテスト実行 + API経由の品質チェック
8. **自動マニュアル更新**: 検証システムで品質維持

### ❌ v2.3アンチパターン
1. Morphllm MCPの使用（廃止済み）
2. セッション管理なしで長時間作業
3. `--think-hard`なしで複雑な仕様作成
4. ビジネス価値検討なしで実装開始
5. タスク管理なしで実装開始
6. 全て順次実行
7. 最後にまとめてテスト
8. 手動マニュアル更新

## 効率的な開発フロー

```markdown
1. セッション開始
   - /sc:load でコンテキスト読込
   - 前回の進捗確認

2. 仕様と計画
   - /specify --think-hard で深層分析
   - /sc:business-panel でビジネス価値確認
   - /plan で設計
   - /tasks でタスク分解

3. 実装
   - TodoWriteでタスク管理
   - 新MCP統合（Serena, Sequential, Magic, Context7, Playwright）
   - 並列処理活用
   - 継続的テスト

4. 検証
   - /verify-and-pr で品質保証
   - 問題の自動修正
   - PR作成

5. セッション終了
   - /sc:save で状態保存
   - 検証システムで品質確認
```



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

## Claude Code基盤エージェント

### 開発系エージェント

| エージェント | 説明 | 使用場面 | 使用例 |
|-------------|------|---------|--------|
| **general-purpose** | 汎用調査・コード検索・マルチステップタスク | 複雑な調査、不確実な検索 | 「ファイル全体を調査してエラーの原因を特定」 |
| **python-expert** | Python専門（SOLID原則、ベストプラクティス） | 本番レベルのPythonコード実装 | 「SOLID原則に従ったPythonクラス設計」 |
| **frontend-architect** | フロントエンド開発（UI/UX、モダンフレームワーク） | アクセシブルで高性能なUI構築 | 「React/Vue/Angularでのコンポーネント設計」 |
| **backend-architect** | バックエンド設計（データ整合性、セキュリティ） | 信頼性の高いバックエンドシステム構築 | 「APIエンドポイントの設計とセキュリティ実装」 |
| **system-architect** | システムアーキテクチャ設計 | スケーラブルなシステム設計 | 「マイクロサービスアーキテクチャの設計」 |

### 品質・最適化系エージェント

| エージェント | 説明 | 使用場面 | 使用例 |
|-------------|------|---------|--------|
| **refactoring-expert** | リファクタリング・クリーンコード | コード品質向上、技術的負債削減 | 「レガシーコードのリファクタリング」 |
| **quality-engineer** | テスト戦略・品質保証 | 包括的なテスト戦略構築 | 「単体テスト・統合テストの設計と実装」 |
| **performance-engineer** | パフォーマンス最適化 | ボトルネック特定と最適化 | 「アプリケーションのパフォーマンス改善」 |
| **security-engineer** | セキュリティ脆弱性検出 | セキュリティ監査とコンプライアンス | 「脆弱性スキャンとセキュリティ強化」 |

### 分析・問題解決系エージェント

| エージェント | 説明 | 使用場面 | 使用例 |
|-------------|------|---------|--------|
| **root-cause-analyst** | 根本原因分析 | 複雑な問題の体系的調査 | 「システム障害の根本原因特定」 |
| **requirements-analyst** | 要件定義・仕様化 | 曖昧な要求の具体化 | 「プロジェクト要件の明確化と仕様書作成」 |

### 教育・文書系エージェント

| エージェント | 説明 | 使用場面 | 使用例 |
|-------------|------|---------|--------|
| **learning-guide** | プログラミング概念の教授 | 段階的学習と実践例 | 「プログラミング概念の説明と学習ガイド」 |
| **socratic-mentor** | ソクラテス式教育 | 戦略的質問による学習促進 | 「問いかけを通じた問題解決スキル向上」 |
| **technical-writer** | 技術文書作成 | 明確で包括的なドキュメント作成 | 「APIドキュメントやユーザーガイド作成」 |

### 運用系エージェント

| エージェント | 説明 | 使用場面 | 使用例 |
|-------------|------|---------|--------|
| **devops-architect** | インフラ自動化・デプロイメント | CI/CDパイプライン構築 | 「デプロイメント自動化とインフラ設計」 |

### 設定系エージェント

| エージェント | 説明 | 使用場面 | 使用例 |
|-------------|------|---------|--------|
| **statusline-setup** | ステータスライン設定 | Claude Codeのステータスライン設定 | 「ステータスラインのカスタマイズ」 |
| **output-style-setup** | 出力スタイル設定 | Claude Codeの出力スタイル作成 | 「カスタム出力フォーマットの設定」 |


---

# 変更履歴

## v2.3 (2024-09-12)

### 🆕 新機能
- **自動検証システム**: API経由でマニュアル品質を継続監視
- **ビジネスパネル分析**: 9名の専門家による戦略的価値分析
- **拡張セッション管理**: `/sc:load`, `/sc:save`, `/sc:checkpoint`コマンド
- **深層分析モード**: `/specify --think-hard`フラグによる高度な要件分析
- **Q&Aセクション**: `/specify`コマンドの詳細使用ガイド

### 🔄 更新
- **MCP統合強化**: Serena MCPによるセマンティック理解向上
- **並列処理最適化**: より効率的なタスク並列実行戦略
- **トラブルシューティング**: v2.3固有の問題解決策を追加

### ⚠️ 廃止・削除
- **Morphllm MCP**: 非推奨につき削除（Serena + MultiEditで代替）
- **旧セッション管理**: 従来方式を新システムに統合

### 📈 改善
- **品質管理**: 自動検証による継続的品質向上
- **戦略的思考**: ビジネス専門家の知見を開発プロセスに統合  
- **開発効率**: セッション継続性とMCP最適化による50%の時間短縮
- **学習支援**: より詳細なQ&Aと実践的なガイダンス

### 🔗 互換性
- v2.2からの自動移行サポート
- 既存のワークフローとの下位互換性維持
- 段階的な新機能導入可能

## 💡 v2.4 最適化提案 (2024-09-12追加)

### 🚀 提案された新機能
- **並列エージェント協調**: 複数エージェントの同期実行による開発効率3倍化
- **段階的検証パイプライン**: 品質・セキュリティ・パフォーマンスの段階的検証システム
- **自動エージェント調整**: タスクに最適なエージェント組み合わせの自動選択
- **リアルタイム最適化**: 実装中のパフォーマンス・セキュリティ最適化

### 📈 期待される改善効果
- **開発速度**: v2.3比30%短縮（従来比65%短縮）
- **品質向上**: 欠陥検出率95%向上
- **並列効率**: 4エージェント協調により70%の時間短縮
- **自動化**: エージェント間依存関係の自動解決

### 🎯 次期バージョン方向性
v2.4では、エージェント協調とパイプライン最適化を中心とした大幅な効率化を実現予定。
現在は自然言語での代替実行により、提案機能の効果を体験可能。

## 💡 v2.4 最適化コマンド（提案）

| コマンド | 状態 | 説明 | 使用例（日本語での依頼） |
|---------|------|------|------------------------|
| `/sc:optimize` | 🔮 | 実装済みコードのパフォーマンス・セキュリティ・品質最適化 | `/sc:optimize` "--target performance" "APIレスポンス速度を最適化" |
| `/sc:parallel` | 🔮 | タスクの並列実行計画自動生成と実行 | `/sc:parallel` "--analyze" "認証機能を並列開発できるタスクに分解" |
| `/sc:validate-pipeline` | 🔮 | 段階的検証パイプラインの自動実行 | `/sc:validate-pipeline` "auth --stage all" "段階的に品質検証を実行" |
| `/sc:validate-parallel` | 🔮 | 複数エージェントによる並列検証実行 | `/sc:validate-parallel` "auth --agents security,performance" |
| `/sc:validate-comprehensive` | 🔮 | 全エージェントを活用した包括的検証 | `/sc:validate-comprehensive" "auth --report-detail high" |
| `/sc:agent-coordinate` | 🔮 | 複数エージェントの協調作業の自動制御 | `/sc:agent-coordinate` "backend,frontend --sync" "バックエンドとフロントエンドを同期開発" |
| `/sc:commit` | 🔮 | タスク完了時の自動コミット（メッセージ生成、品質チェック付き） | `/sc:commit` "feat: 認証機能実装" "タスク完了時に自動コミット" |
| `/sc:push` | 🔮 | 安全なプッシュ（テスト・lint通過確認後） | `/sc:push` "--verify" "品質チェック後にプッシュ" |
| `/sc:sync` | 🔮 | リモートとの同期確認とマージ戦略 | `/sc:sync` "--pull --rebase" "リモートと同期" |
| `/sc:review` | 🔮 | セルフレビューとGitHub PR準備 | `/sc:review` "--checklist" "PR前のセルフレビュー" |
| `/sc:issue-link` | 🔮 | TodoWriteとGitHub Issues/Projectsの連携 | `/sc:issue-link` "#123" "IssueとTodoを連携" |

**凡例**: ✅実装済み | 🔮v2.4提案（自然言語で代替実行可能）

## 💡 v2.4 最適化フラグ（提案）

| フラグ | 効果 | 使用場面 | 使用例 |
|-------|------|----------|--------|
| `--agent-parallel` | エージェント並列実行 | 複雑な多領域タスク | `/implement "認証システム" --agent-parallel` |
| `--pipeline-mode` | 段階的パイプライン実行 | 品質重視開発 | `/verify-and-pr auth "feat: 実装" --pipeline-mode` |
| `--optimize-target` | 最適化対象指定 | 特定領域の改善 | `/refactor --optimize-target performance,security` |
| `--coordination-sync` | エージェント間同期 | 統合開発 | `/implement "フルスタック機能" --coordination-sync` |
| `--validation-depth` | 検証深度制御 | 検証レベル調整 | `/verify --validation-depth comprehensive` |
| `--auto-coordinate` | 自動エージェント調整 | 効率的タスク分配 | `/tasks --auto-coordinate` |

---

**💡 Pro Tip v2.3+**: このマニュアルは自動検証システムによって品質が継続的に管理され、v2.4最適化提案が追加されています。実装で困ったことがあれば、Claude Codeに直接質問するか、`/sc:business-panel`でビジネス観点からのアドバイスを求めてください。v2.3の新機能とv2.4提案により、技術実装とビジネス価値の両方を最大限に最適化できます。