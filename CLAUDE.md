# 🚀 Claude Code 統合開発コマンドセンター v2.4
> **最終更新**: 2025-09-18 | **Super Claude Framework**: v2.4対応 | **TDD**: 完全準拠

## 📊 現在のプロジェクト状況
<!-- このセクションは自動更新されます -->
- **Git Branch**: 003-implementation-start
- **作業ディレクトリ**: /Users/furuyanaoki/Project/new.mail.score/backend
- **セッション状態**: アクティブ
- **TDD実装状態**: Phase 2 (GREEN) 完了 / Phase 3 (REFACTOR) 進行中
- **利用可能MCP**: Sequential ✅ Context7 ✅ Serena ✅ Magic ✅ Playwright ✅

## 🎯 Claude Codeの拡張役割

### 基本役割
- 仕様書の作成（Spec-Kit使用）
- 実装後の品質検査
- コードレビューとフィードバック
- マニュアル検証と最適化

### v2.4 強化役割
- **TDD完全準拠**: RED→GREEN→REFACTORサイクルの厳密な実行
- **深層分析**: `--think-hard`による複雑な要件の多角的分析
- **ビジネス価値評価**: 9名の専門家パネルによる戦略的分析
- **並列処理最適化**: タスクの自動並列化と効率化
- **セッション継続性**: 作業状態の保存と復元
- **自動品質管理**: 継続的な検証とメトリクス監視

## 📋 利用可能なコマンド群

### 🔧 Spec-Kit基本コマンド
```markdown
/specify [--think-hard] [--brainstorm]    # 仕様書生成（深層分析・要件発見）
/plan [--optimize-parallel] [--research-heavy]  # 実装計画（並列最適化・詳細調査）
/tasks [--parallel-optimization] [--mcp-strategy]  # タスク分解（並列設計・MCP活用）
/verify-and-pr <slug> "message" [--comprehensive] [--play]  # 検証とPR作成
```

### 🎮 Super Claude拡張コマンド
```markdown
# セッション管理
/sc:load                           # プロジェクトコンテキスト読込
/sc:save                           # セッション状態保存
/sc:checkpoint "milestone"         # チェックポイント作成

# ビジネス分析
/sc:business-panel @spec.md [--mode discussion|debate|socratic]  # 専門家パネル分析

# 開発支援
/sc:analyze [--focus security|performance|architecture]  # 包括的分析
/sc:implement "feature" [--agent-parallel]  # 並列実装
/sc:optimize --target performance|security  # 最適化実行
```

### 🔍 マニュアル検証コマンド
```markdown
/validate-manual [--version 2.4] [--scope full|commands|mcp]  # マニュアル検証
/check-mcp-servers [--servers sequential,context7,...]  # MCP可用性チェック
/update-manual --validation-id <UUID> --target-version 2.4  # マニュアル最適化
```

### 🧪 TDD開発支援コマンド（v2.4新機能）
```markdown
# TDDサイクル管理
/tdd:red <task-id>                # REDフェーズ：失敗するテストを作成
/tdd:green <task-id>              # GREENフェーズ：最小実装でテストをパス
/tdd:refactor <task-id>           # REFACTORフェーズ：コード品質改善

# TDD検証
/tdd:verify [--phase red|green|refactor]  # 現在のフェーズ検証
/tdd:status                       # 全タスクのTDD状態確認
/tdd:report                       # TDD準拠レポート生成

# TDD自動化
/tdd:cycle <task-id> [--auto]     # 完全なTDDサイクル実行
/tdd:batch <task-ids> [--parallel]  # 複数タスクの並列TDD実行
```

## 🏗️ 現在の技術スタック
<!-- plan.mdから自動更新 -->
```yaml
language: TypeScript/Python
framework: Next.js/FastAPI
database: PostgreSQL
testing: Jest/pytest
mcp_servers:
  analysis: Sequential
  ui: Magic
  symbols: Serena
  testing: Playwright
  documentation: Context7
  # ⚠️ 廃止: refactoring: Morphllm → Serena + MultiEditで代替
```

## 📈 品質メトリクス（自動更新）
<!-- 最終更新: 2025-09-18 -->
| メトリクス | 現在値 | 目標値 | ステータス |
|-----------|--------|--------|-----------|
| テストカバレッジ | 70% | >90% | 🚧 |
| TDD準拠率 | 30% | 100% | 🚧 |
| コード複雑度 | - | <8 | ⏳ |
| セキュリティスコア | - | A | ⏳ |
| パフォーマンススコア | - | >8.5 | ⏳ |
| 技術負債インデックス | 0.35 | <0.15 | ⚠️ |

## 🔴 TDD実装状況
| フェーズ | 完了タスク | 総タスク | 達成率 |
|---------|-----------|----------|--------|
| RED (テスト作成) | 13 | 65 | 20% |
| GREEN (最小実装) | 13 | 65 | 20% |
| REFACTOR (改善) | 0 | 65 | 0% |

## 🚀 並列実行とMCP統合戦略

### 並列実行可能タスクグループ
```markdown
# Group A: 設計・分析フェーズ（並列実行可能）
- データモデル定義 → --serena
- API仕様策定 → --c7
- UIコンポーネント設計 → --magic

# Group B: 実装フェーズ（Group A完了後）
- バックエンド実装 → --seq --serena
- フロントエンド実装 → --magic --c7
- テスト作成 → --play

# Group C: 最適化フェーズ（統合後）
- パフォーマンス最適化 → --seq
- セキュリティ強化 → --serena
- E2Eテスト → --play
```

### MCP活用マトリックス
| タスク種別 | 推奨MCP | 代替手段 | 並列可能 |
|-----------|---------|----------|----------|
| 深層分析 | Sequential | Native推論 | ❌ |
| UI生成 | Magic | 手動実装 | ✅ |
| シンボル操作 | Serena | MultiEdit | ✅ |
| ドキュメント参照 | Context7 | Web検索 | ✅ |
| E2Eテスト | Playwright | 単体テスト | ✅ |

## 🔧 エラーハンドリングガイド

### よくあるエラーと対処法
```markdown
# Import Error
原因: 依存関係の未インストール
対処: npm ci または pip install -r requirements.txt
検証: /verify-and-pr <slug> --comprehensive

# Test Failure  
原因: 実装とテストの不整合
対処: テストを先に修正（TDD）→ 実装を調整
検証: TodoWriteで失敗テストをタスク化

# Lint Error
原因: コードスタイル違反  
対処: npm run lint:fix または black .
予防: /sc:checkpoint前に自動実行

# MCP Connection Error
原因: MCPサーバー未起動
対処: 自動フォールバック → 代替手段を使用
監視: /check-mcp-servers --auto-switch
```

## 📊 タスク進捗状況
<!-- tasks_tdd.mdから自動更新 -->
```markdown
総タスク数: 195 (65タスク × 3フェーズ)
✅ RED完了: 13 (20%）
✅ GREEN完了: 13 (20%）
⏳ REFACTOR待機: 13
🚧 進行中: 0
⏳ 未着手: 169

次の優先タスク（TDDサイクル）:
1. T005-T013のREFACTORフェーズ（ハードコード除去）
2. T014-T016のREDフェーズ（ユーザー管理テスト作成）
3. T046-T049のREDフェーズ（統合テスト作成）
```

## 🧪 TDDワークフロー（v2.4必須）

### TDD実装フロー
```bash
# 1. REDフェーズ（テストファースト）
/tdd:red T014
→ テスト作成（必ず失敗することを確認）
→ git commit -m "test(users): add failing test for user registration [T014-RED]"

# 2. GREENフェーズ（最小実装）
/tdd:green T014
→ 最小限のコードでテストをパス
→ git commit -m "feat(users): minimal implementation for user registration [T014-GREEN]"

# 3. REFACTORフェーズ（品質改善）
/tdd:refactor T014
→ コード品質改善（テストは常にパス）
→ git commit -m "refactor(users): improve user registration implementation [T014-REFACTOR]"
```

### TDDアンチパターン検出
```yaml
violations:
  - テストなしで実装開始 → 自動検出・警告
  - テストを後から追加 → TDD違反として記録
  - テストをスキップ → ビルド失敗
  - ハードコードのまま放置 → 技術負債として追跡
```

## 🔄 GitHub統合とコミット戦略

### TDD準拠コミット戦略
```bash
# TDDフェーズ別コミット（必須）
REDフェーズ → git commit -m "test(<scope>): <description> [<task-id>-RED]"
GREENフェーズ → git commit -m "feat(<scope>): <description> [<task-id>-GREEN]"
REFACTORフェーズ → git commit -m "refactor(<scope>): <description> [<task-id>-REFACTOR]"

# 従来のコミット（非推奨）
タスク完了 → git commit -m "feat(<scope>): <description> [<task-id>]"  # ⚠️ TDD違反

# チェックポイントコミット（30分ごと）
/sc:checkpoint → git commit -m "WIP: checkpoint $(date +%H:%M)"
```

### PR作成フロー
```markdown
1. /verify-and-pr <slug> "feat: description" --comprehensive
2. 自動品質チェック実行
3. テスト・Lint・セキュリティ検証
4. PR自動作成（検証結果付き）
5. /sc:business-panel でビジネス価値確認
```

## 📁 出力先ディレクトリ
```
specs/<slug>/              # 仕様書群
├── spec.md               # 機能仕様
├── plan.md               # 実装計画
├── tasks.md              # タスクリスト
├── research.md           # 技術調査
└── validation-results/   # 検証結果

reports/                   # レポート群
├── <slug>-review.md      # コードレビュー
├── metrics-weekly.md     # 週次メトリクス
└── business-analysis.md  # ビジネス分析

.000.MANUAL/              # マニュアル群
├── super_claude_integrated_manual_v*.md
└── validation-logs/      # 検証ログ
```

## 🎯 Quick Actions（よく使うコマンド組み合わせ）

### TDD開発の標準フロー（v2.4推奨）
```bash
# 1. セッション開始とTDD準備
/sc:load
/tdd:status  # 現在のTDD実装状態確認

# 2. タスクのTDDサイクル実行
/tdd:red T014  # 失敗するテストを作成
pytest tests/test_users.py::test_user_registration -v  # 失敗確認
git commit -m "test(users): add failing test for user registration [T014-RED]"

/tdd:green T014  # 最小実装
pytest tests/test_users.py::test_user_registration -v  # パス確認
git commit -m "feat(users): minimal implementation [T014-GREEN]"

/tdd:refactor T014  # リファクタリング
pytest tests/ -v  # 全テストパス確認
git commit -m "refactor(users): improve implementation [T014-REFACTOR]"

# 3. 並列TDD実行（独立タスク）
/tdd:batch T015,T016,T017 --parallel

# 4. 検証とPR
/tdd:report  # TDD準拠レポート生成
/verify-and-pr <slug> "feat: TDD implementation" --tdd-compliant
```

### 従来の開発フロー（非推奨）
```bash
# ⚠️ TDD違反：実装ファーストアプローチ
# 1. セッション開始
/sc:load

# 2. 仕様から実装まで一気通貫
/specify --think-hard
/plan --optimize-parallel
/tasks --parallel-optimization --mcp-strategy

# 3. 実装（TodoWrite自動管理）
specs/<slug>/tasks.mdに基づいて実装を開始
--seq --serena --magic --c7 --play

# 4. 検証とPR
/verify-and-pr <slug> "feat: description" --comprehensive --play
/sc:business-panel @specs/<slug>/spec.md

# 5. セッション保存
/sc:save
```

### 問題解決フロー
```bash
# 1. 問題分析
/sc:analyze . --focus security,performance
エラーの根本原因を分析してください --seq

# 2. 修正実装
/sc:implement "修正内容" --validate
TodoWriteで修正タスクを管理

# 3. 検証
/verify-and-pr <slug> "fix: description" --auto-fix
```

## 🔄 自動更新とメンテナンス

### 自動更新スケジュール
- **30分ごと**: /sc:checkpoint（作業状態保存）
- **タスク完了時**: git commit（進捗記録）
- **日次**: /validate-manual（品質チェック）
- **週次**: /sc:business-panel（価値分析）

### 品質維持の自動化
```yaml
auto_validation:
  enabled: true
  frequency: daily
  actions:
    - check_mcp_servers
    - validate_manual
    - update_metrics
    - sync_tech_stack

quality_gates:
  test_coverage: 90%
  security_score: A
  performance: 8.5
  auto_fix: true
```

## 💡 ベストプラクティス

### ✅ v2.4推奨事項
1. **TDD厳守**: 必ずRED→GREEN→REFACTORサイクルを守る
2. **テストファースト**: 実装前に必ずテストを作成
3. **セッション管理**: 必ず`/sc:load`で開始、`/sc:save`で終了
4. **深層分析**: 複雑な要件は`--think-hard`を使用
5. **並列処理**: 独立タスクは常に並列実行
6. **継続的検証**: 各フェーズでテスト実行
7. **ビジネス価値**: 重要機能は`/sc:business-panel`で分析

### ❌ v2.4アンチパターン
1. **実装ファースト開発**（最重要違反）
2. テストを後から追加する
3. テストをスキップ・無効化する
4. ハードコードのまま放置する
5. Morphllm MCPの使用（v2.3で廃止）
6. セッション管理なしでの長時間作業
7. 順次実行のみでの実装
8. テストを最後にまとめて実行
9. ビジネス価値の検討なしでの実装

## 🆘 トラブルシューティング

### コマンドが動作しない
```bash
# 権限確認
ls -la .claude/commands/
chmod +x scripts/*.sh

# 代替実行（Claude Codeで直接指示）
"specifyコマンドと同等の仕様書を作成してください"
```

### MCPサーバーエラー
```bash
# 状態確認
/check-mcp-servers
cat ~/.config/claude/mcp/config.json

# 自動フォールバック
--no-mcp  # MCPなしで実行
```

### 検証失敗
```bash
# デバッグモード
DEBUG=* /validate-manual --version 2.3
tail -f logs/validation.log

# 手動検証
/verify-and-pr <slug> --fallback --simple
```

## 📝 補足情報

### 非推奨・削除済みコマンド
- `/verify-implementation <slug>` → `/verify-and-pr`を使用
- `/enhance-tasks-for-codex <slug>` → 削除済み
- `/handoff-to-codex` → 未実装

### v2.3→v2.4 移行ガイド
#### 主要変更点
- **TDD必須化**: すべての新規開発はTDDサイクル準拠
- **コマンド追加**: `/tdd:*` コマンド群の追加
- **メトリクス追加**: TDD準拠率の追跡開始
- **コミット規約変更**: フェーズ別コミットメッセージ必須

#### 移行手順
1. 既存コードのTDD準拠率を測定: `/tdd:status`
2. 技術負債の可視化: `/tdd:report`
3. 段階的リファクタリング計画: `/plan --tdd-migration`
4. 並列TDD実行で効率化: `/tdd:batch --parallel`

### v2.4→v2.5 ロードマップ
- TDD自動化の完全統合
- AIペアプログラミング強化
- リアルタイムコード品質分析
- 自己修復型テストシステム

---
*このファイルは自動検証システムにより品質管理されています*
*問題や提案がある場合は https://github.com/anthropics/claude-code/issues へ*