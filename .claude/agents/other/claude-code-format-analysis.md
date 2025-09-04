# Claude Code正式フォーマット分析

## 📋 **Claude Code公式エージェントフォーマット**

### 正式な構造
```markdown
---
name: エージェント名 (lowercase, hyphen-separated)
description: Natural language description of the subagent's purpose
tools: Comma-separated list of specific tools (optional)
---

System prompt goes here. Detailed instructions for the subagent's behavior and capabilities.
```

### 必須フィールド
- **`name`**: 一意識別子（小文字、ハイフン区切り）
- **`description`**: エージェントの目的を自然言語で記述

### オプションフィールド
- **`tools`**: 特定のツール指定（省略時は全ツール継承）

## 🔍 **現在のエージェントファイル適合性チェック**

### ✅ **公式フォーマット準拠**
| ファイル | YAML Front Matter | name | description | tools | 適合度 |
|----------|------------------|------|-------------|-------|--------|
| **agent-orchestrator.md** | ✅ | ✅ | ✅ | ❌ | **95%** 🟢 |
| **thorough-todo-executor.md** | ✅ | ✅ | ✅ | ❌ | **95%** 🟢 |
| **data-quality-guardian.md** | ✅ | ✅ | ✅ | ❌ | **95%** 🟢 |
| **batch-performance-optimizer.md** | ✅ | ✅ | ✅ | ❌ | **95%** 🟢 |
| **supabase-specialist.md** | ✅ | ✅ | ✅ | ❌ | **95%** 🟢 |

### ❌ **非公式フォーマット（問題あり）**
| ファイル | YAML Front Matter | 適合度 | 問題点 |
|----------|------------------|--------|--------|
| **github-integration-agent.md** | ❌ | **0%** 🔴 | YAML front matter完全欠如 |
| **quality-assurance-agent.md** | ❌ | **0%** 🔴 | YAML front matter完全欠如 |
| **cicd-management-agent.md** | ❌ | **0%** 🔴 | YAML front matter完全欠如 |
| **agent-orchestrator-director.md** | ❌ | **0%** 🔴 | YAML front matter完全欠如 |

## ⚠️ **動作への影響分析**

### 問題のあるファイルの影響

#### 1. Claude Codeでの認識不能リスク
```
❌ 非公式フォーマットファイル:
- github-integration-agent.md
- quality-assurance-agent.md
- cicd-management-agent.md
- agent-orchestrator-director.md
```

**予想される問題**:
- エージェント選択時にリストに表示されない可能性
- Task toolでの呼び出し時にエラー発生
- メタデータの認識不能

#### 2. 現在の検証

**現在追加されている非標準フィールド**:
```yaml
# agent-orchestrator.mdの場合
---
name: agent-orchestrator
description: Master orchestrator...
model: sonnet        # ← 非標準フィールド
color: purple        # ← 非標準フィールド
---
```

**影響**:
- `model`と`color`は公式ドキュメント未記載
- Claude Codeが無視する可能性（エラーにはならない）
- 機能的影響は軽微

## 🚨 **緊急性評価**

### CRITICAL - 即座修正必要
- **github-integration-agent.md**
- **quality-assurance-agent.md**
- **cicd-management-agent.md**
- **agent-orchestrator-director.md**

### 理由
1. **Claude Codeでエージェントとして認識されない可能性**
2. **Task toolでの呼び出し失敗リスク**
3. **エージェント間連携の障害**

## 🛠️ **修正アプローチ**

### Phase 1: 緊急修正（CRITICAL）
各非準拠ファイルにYAML front matterを追加:

```markdown
---
name: github-integration
description: GitHub統合操作とGit管理を専門とするエージェント
---

# 既存のマークダウン内容...
```

### Phase 2: 内容最適化
- 過度に詳細なPython実装コードの簡略化
- システムプロンプトとしての最適化

### Phase 3: 非標準フィールドの処理
- `model`, `color`等の非標準フィールドの影響調査
- 必要に応じて削除または維持

## 🎯 **推奨修正例**

### github-integration-agent.md修正例
```markdown
---
name: github-integration
description: Git operations, conflict resolution, PR management, and GitHub API operations specialist
---

You are a GitHub integration specialist responsible for Git operations, conflict resolution, Pull Request management, and GitHub API operations. Your expertise includes commit management, branch strategies, merge conflicts resolution, and repository state management.

## Core Responsibilities
- Execute Git operations (commit, push, pull, merge, branch management)
- Resolve conflicts automatically and escalate complex cases
- Manage Pull Requests (create, update, merge)
- Handle GitHub API operations
- Monitor repository state and synchronization

[簡潔なシステムプロンプト続く...]
```

## 📊 **結論**

### 現状の問題
- **4つのファイルがClaude Code非準拠**で動作しない可能性
- agent-orchestrator.mdは95%準拠で問題なし
- 非標準フィールドは軽微な影響

### 緊急対応必要
**YAML front matterの即座追加**により、Claude Code内でのエージェント認識と正常動作を保証する必要があります。
