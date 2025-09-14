# 🚀 Claude Code 統合開発コマンドセンター v2.3
> **最終更新**: 2025-09-12 | **Super Claude Framework**: v2.3対応 | **自動検証**: 有効

## 📊 現在のプロジェクト状況
<!-- このセクションは自動更新されます -->
- **Git Branch**: 001-think-hard-manual
- **作業ディレクトリ**: /Users/naoki/000_PROJECT/作業用
- **セッション状態**: アクティブ
- **利用可能MCP**: Sequential ✅ Context7 ✅ Serena ✅ Magic ✅ Playwright ✅ IDE ✅

## 🎯 Claude Codeの拡張役割

### 基本役割
- 仕様書の作成（Spec-Kit使用）
- 実装後の品質検査
- コードレビューとフィードバック
- マニュアル検証と最適化

### v2.3 強化役割
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
/validate-manual [--version 2.3] [--scope full|commands|mcp]  # マニュアル検証
/check-mcp-servers [--servers sequential,context7,...]  # MCP可用性チェック
/update-manual --validation-id <UUID> --target-version 2.3  # マニュアル最適化
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
<!-- 最終更新: 2025-09-12 14:00 -->
| メトリクス | 現在値 | 目標値 | ステータス |
|-----------|--------|--------|-----------|
| テストカバレッジ | - | >90% | ⏳ |
| コード複雑度 | - | <8 | ⏳ |
| セキュリティスコア | - | A | ⏳ |
| パフォーマンススコア | - | >8.5 | ⏳ |
| 技術負債インデックス | - | <0.15 | ⏳ |

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
<!-- tasks.mdから自動更新 -->
```markdown
総タスク数: -
✅ 完了: - (-%）
🚧 進行中: -
🚫 ブロック: -
⏳ 未着手: -

次の優先タスク:
1. [タスク読込中...]
2. [タスク読込中...]
3. [タスク読込中...]
```

## 🔄 GitHub統合とコミット戦略

### コミット戦略
```bash
# タスクレベルコミット（推奨）
T001完了 → git commit -m "feat(auth): implement JWT token [T001]"

# グループレベルコミット  
Group A完了 → git commit -m "feat(auth): complete backend implementation"

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

### 新機能開発の最速パス
```bash
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

### ✅ 推奨事項
1. **セッション管理**: 必ず`/sc:load`で開始、`/sc:save`で終了
2. **深層分析**: 複雑な要件は`--think-hard`を使用
3. **並列処理**: 独立タスクは常に並列実行
4. **継続的検証**: 各タスク完了時にテスト実行
5. **ビジネス価値**: 重要機能は`/sc:business-panel`で分析

### ❌ アンチパターン
1. Morphllm MCPの使用（v2.3で廃止）
2. セッション管理なしでの長時間作業
3. 順次実行のみでの実装
4. テストを最後にまとめて実行
5. ビジネス価値の検討なしでの実装

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

### v2.3→v2.4 移行準備
- エージェント並列協調の準備
- 段階的検証パイプラインの設計
- GitHub統合の強化
- リアルタイム最適化の実装

---
*このファイルは自動検証システムにより品質管理されています*
*問題や提案がある場合は https://github.com/anthropics/claude-code/issues へ*