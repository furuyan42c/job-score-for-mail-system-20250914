# 理想的なエージェント仕様書フォーマット

## 概要

このドキュメントは、Claude Code用エージェントファイルの統一フォーマットを定義します。
全エージェントは一貫性を保ち、相互運用性と保守性を確保するため、この仕様に従って記述する必要があります。

## 標準フォーマット

### YAML Front Matter

```yaml
---
name: エージェント名 (kebab-case)
description: エージェントの簡潔な説明（1行）
model: sonnet
color: エージェント色 (blue|red|yellow|green|purple)
category: エージェント分類 (orchestrator|specialist|utility)
version: 1.0.0
created_date: YYYY-MM-DD
dependencies: [依存エージェント名の配列]
tags: [タグ配列]
---
```

### Markdown構造

```markdown
# エージェント名

## 🎯 **コア責務**

- 主要責務1: 詳細説明
- 主要責務2: 詳細説明
- ...

## 📋 **Agent-Orchestratorとの連携**

### エージェント間通信インターフェース

```typescript
interface AgentRequest {
  task_id: string;
  request_type: string;
  parameters: Record<string, any>;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  timeout_seconds?: number;
}

interface AgentResponse {
  success: boolean;
  result: Record<string, any>;
  error_message?: string;
  execution_time?: number;
  next_actions?: string[];
}
```

## 🔧 **実装機能**

### 機能1
実装詳細...

### 機能2
実装詳細...

## 📊 **ログ・監視**

### 専用ログシステム
ログ実装詳細...

### 監視指標
監視項目詳細...

## ⚙️ **設定・制約事項**

- 設定項目1
- 設定項目2
- ...

## 🔗 **関連エージェント**

- エージェント1: 連携内容
- エージェント2: 連携内容
```

## フォーマット規則

### 1. ファイル命名規則
- ファイル名: `{agent-name}.md` (kebab-case)
- 例: `github-integration.md`, `quality-assurance.md`

### 2. YAML Front Matter必須項目
- `name`: エージェント識別名
- `description`: 1行での簡潔な説明
- `model`: 使用モデル（基本的には`sonnet`）
- `color`: エージェント色分け
- `category`: エージェント分類

### 3. セクション構成規則
- 🎯 コア責務: エージェントの主要な責任範囲
- 📋 Agent-Orchestratorとの連携: 他エージェントとのインターフェース
- 🔧 実装機能: 具体的な機能実装
- 📊 ログ・監視: ログシステムと監視項目
- ⚙️ 設定・制約事項: 設定可能項目と制約
- 🔗 関連エージェント: 依存・連携エージェント

### 4. コードブロック規則
- TypeScript/Python: インターフェース定義
- 実装例: 実際のコード例
- 設定例: 設定ファイル例

## エージェント分類

### orchestrator
- 目的: 他エージェントの調整・管理
- 例: `agent-orchestrator`

### specialist
- 目的: 特定領域の専門業務
- 例: `github-integration`, `quality-assurance`, `cicd-management`

### utility
- 目的: 汎用的なサポート機能
- 例: `thorough-todo-executor`

## 品質ガイドライン

### 1. 一貫性
- 全エージェントで同じフォーマット構造を維持
- 同じセクション名・絵文字を使用
- インターフェース定義の統一

### 2. 明確性
- 責務範囲を明確に定義
- 他エージェントとの境界を明示
- 実装詳細を具体的に記述

### 3. 保守性
- バージョン管理の実施
- 依存関係の明記
- 変更履歴の記録

### 4. 相互運用性
- 標準インターフェースの遵守
- 共通データ構造の使用
- エラーハンドリングの統一

## テンプレート例

```yaml
---
name: example-agent
description: エージェントの説明を1行で記述
model: sonnet
color: blue
category: specialist
version: 1.0.0
created_date: 2025-08-25
dependencies: ["agent-orchestrator"]
tags: ["example", "template"]
---

# Example Agent

## 🎯 **コア責務**

- 責務1: 詳細説明
- 責務2: 詳細説明

## 📋 **Agent-Orchestratorとの連携**

### エージェント間通信インターフェース

```typescript
interface ExampleRequest {
  // インターフェース定義
}

interface ExampleResponse {
  // インターフェース定義
}
```

## 🔧 **実装機能**

### 機能1
実装詳細...

## 📊 **ログ・監視**

### 専用ログシステム
ログ実装詳細...

## ⚙️ **設定・制約事項**

- 設定項目

## 🔗 **関連エージェント**

- agent-orchestrator: 調整・委譲
```

このフォーマットに従うことで、全エージェントの一貫性と品質を保つことができます。
