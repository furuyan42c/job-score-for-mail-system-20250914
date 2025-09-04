# Claude Code カスタムコマンド集

効率的な開発を支援する高機能コマンドセットです。

## 🚀 主要コマンド

### `/kiro [機能名]` - 仕様駆動開発
Kiroスタイル仕様駆動開発の初期化を行います。

**機能:**
- `specs/requirements.md` に要件定義テンプレートを追加
- `specs/design.md` に技術設計テンプレートを追加
- `specs/tasks.md` に実装タスクテンプレートを追加

**使用例:** `/kiro ユーザー認証システム`

### `/cifix [options]` - CI/CDエラー自動修正
CI/CDパイプラインのエラーを自動検証・修正します。

**機能:**
- テスト・Lint・型チェックの自動実行
- 一般的な問題の自動修正
- 最大リトライ回数の設定
- 自動コミット機能

**使用例:** `/cifix --auto-commit --retries=3`

### `/merge [branch]` - 安全なマージ
安全性を重視したマージ処理を行います。

**機能:**
- マージ前の完全チェック
- バックアップブランチの作成
- PR状態の確認
- 自動クリーンアップ

**使用例:** `/merge feature/auth main --squash --auto-push`

### `/analyze [options]` - コードベース分析
プロジェクトの詳細分析を行います。

**機能:**
- プロジェクト構造解析
- 依存関係・脆弱性チェック
- Git履歴分析
- コード品質評価

**使用例:** `/analyze --full --report`

### `/refactor [options]` - リファクタリング支援
コードの品質向上を支援します。

**機能:**
- リファクタリング対象の自動検出
- メソッド抽出
- 自動修正
- リファクタリング計画生成

**使用例:** `/refactor --extract-method --file=src/app.js --start=10 --end=20`

### `/deploy [options]` - デプロイメント管理
複数のプラットフォームへの安全なデプロイを管理します。

**機能:**
- Vercel、Netlify、Heroku対応
- デプロイ前チェック
- ロールバック機能
- デプロイレポート生成

**使用例:** `/deploy --platform=vercel --env=production`

### `/optimize [options]` - パフォーマンス最適化
コードとアセットの最適化を行います。

**機能:**
- バンドルサイズ分析
- 画像・CSS・JS最適化
- 未使用依存関係検出
- 最適化計画生成

**使用例:** `/optimize --auto --deps --format`

## 📝 エイリアス一覧

| エイリアス | 元コマンド | 用途 |
|------------|------------|------|
| `/k`, `/init`, `/仕様` | kiro | 仕様初期化 |
| `/ci`, `/fix` | cifix | CI修正 |
| `/m` | merge | マージ |
| `/a`, `/分析` | analyze | 分析 |
| `/r`, `/リファクタ` | refactor | リファクタリング |
| `/d`, `/デプロイ` | deploy | デプロイ |
| `/o`, `/最適化`, `/perf` | optimize | 最適化 |

## 🏗️ ファイル構成

```
.claude/
├── commands.json      # コマンド定義・エイリアス
├── config.json        # プロジェクト設定
├── README.md          # このファイル
└── commands/
    ├── kiro.js        # 仕様駆動開発
    ├── cifix.js       # CI/CD修正
    ├── merge.js       # 安全マージ
    ├── analyze.js     # コード分析
    ├── refactor.js    # リファクタリング
    ├── deploy.js      # デプロイ管理
    └── optimize.js    # パフォーマンス最適化
```

## 🔄 効率的な開発フロー

```bash
# 1. 新機能の仕様作成
/kiro 新しい機能

# 2. 実装後のコード分析
/analyze --full

# 3. 品質改善
/refactor --auto --fix-whitespace
/optimize --auto --deps

# 4. CI/CD修正（必要に応じて）
/cifix --auto-commit

# 5. 安全なマージ
/merge --backup --delete-branch

# 6. デプロイ
/deploy --platform=vercel
```

## ⚙️ カスタマイズ

### 新コマンド追加
1. `commands/new-command.js` を作成
2. `commands.json` に定義を追加
3. 必要に応じてエイリアス設定

### 設定変更
- `config.json`: プロジェクト全般設定
- 各コマンドファイル: 個別カスタマイズ

## 📋 システム要件

- **Node.js**: 14以上
- **Git**: 必須
- **GitHub CLI**: 推奨 (`gh` コマンド)
- **実行権限**: `chmod +x .claude/commands/*.js`

## 🚀 高度な使い方

### バッチ処理例
```bash
# 完全な品質チェック＆修正
/analyze --full && /refactor --auto && /cifix && /optimize --auto

# 安全なリリース準備
/merge --backup && /deploy --platform=vercel --skip-checks
```

### 自動化設定
各コマンドはpackage.jsonのscriptsセクションに追加可能:
```json
{
  "scripts": {
    "qa": "node .claude/commands/analyze.js --full",
    "deploy-prod": "node .claude/commands/deploy.js --platform=vercel"
  }
}
```
