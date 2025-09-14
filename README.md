# 🚀 Super Claude + Spec-Kit Base Development Environment

## 概要
Super ClaudeフレームワークとSpec-Kitを統合したチーム開発のベース環境です。

## 📁 ディレクトリ構造

```
.
├── .000.MANUAL/          # Super Claudeマニュアルディレクトリ
│   ├── SEO/
│   ├── develop/
│   └── marketing/
├── .claude/commands/     # Spec-Kitコマンド定義
│   ├── specify.md
│   ├── plan.md
│   ├── tasks.md
│   └── verify-and-pr.md
├── .devcontainer/        # VS Code開発コンテナ設定
├── memory/               # セッション永続化
├── scripts/              # 開発支援スクリプト
│   └── create-new-feature.sh
├── specs/                # プロジェクト仕様書（新規作成用）
├── templates/            # プロジェクトテンプレート
├── .eslintrc.json        # ESLint設定
├── .gitignore            # Git除外設定
├── .prettierrc.json      # Prettier設定
├── AGENT.md              # Claude Codeエージェント説明
├── CLAUDE.md             # Claude Code運用ガイド
├── mcp-config.json       # MCPサーバー設定
└── tsconfig.json         # TypeScript設定
```

## 🚀 Quick Start

### 新プロジェクトの開始

```bash
# 1. 新機能のブランチと仕様ディレクトリを作成
./scripts/create-new-feature.sh "機能名"

# 2. Claude Codeで仕様作成
/specify

# 3. 実装計画作成
/plan

# 4. タスク分解
/tasks

# 5. 実装開始
# Claude Codeが自動的にTodoWriteでタスク管理
```

## 📚 利用可能なコマンド

### Spec-Kit コマンド（✅ 実装済み）
- `/specify` - 仕様書生成
- `/plan` - 実装計画作成
- `/tasks` - タスク分解
- `/verify-and-pr` - 検証とPR作成

### Super Claude コマンド（✅ 実装済み）
- `/sc:load` - プロジェクトコンテキスト読み込み
- `/sc:save` - セッション保存
- `/sc:checkpoint` - チェックポイント作成
- `/sc:business-panel` - ビジネス価値分析

詳細は CLAUDE.md ファイルを参照

## 🛠️ 開発環境設定

### 必要なツール
- Node.js 18+
- Git
- VS Code（推奨）

### 初期セットアップ

```bash
# 依存関係のインストール（プロジェクトごと）
npm install

# ESLint/Prettier設定の確認
npm run lint
npm run format
```

## 📖 ドキュメント

- [Super Claude Framework設定](CLAUDE.md)
- [Claude Code 運用ガイド](CLAUDE.md)
- [エージェント説明](AGENT.md)

## 🎯 特徴

- **仕様駆動開発**: Spec-Kitによる要件定義から実装まで
- **セッション管理**: 作業状態の永続化と再開
- **MCP統合**: 高度な分析とコード生成
- **品質保証**: 自動検証とPR作成
- **並列処理**: タスクの自動並列化

## 📋 プロジェクトテンプレート

`templates/` ディレクトリに各種プロジェクトテンプレートが用意されています。

## 🤝 チーム開発

1. このベース環境をクローン
2. プロジェクト固有の設定を追加
3. `specs/` にプロジェクト仕様を作成
4. Spec-Kitワークフローに従って開発

---

**Version**: 1.0.0  
**Last Updated**: 2025-09-13