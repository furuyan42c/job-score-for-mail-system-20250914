# ドキュメント管理ベストプラクティス

## 📚 概要

このガイドは、Claude Codeとの効果的な協働のためのドキュメント管理ベストプラクティスをまとめたものです。
あらゆるプロジェクトで再利用可能な汎用的なガイドラインとして設計されています。

---

## 🎯 ドキュメント管理の原則

### 1. **Single Source of Truth (SSOT)**
- 各情報には1つの正式な記録場所を定める
- 重複を避け、矛盾を防ぐ
- 更新箇所を明確にする

### 2. **Progressive Disclosure**
- 概要 → 詳細 の階層構造
- 読者が必要な深さまで読めるように構成
- 目次とナビゲーションを充実させる

### 3. **Living Documentation**
- コードと同期してドキュメントも更新
- 定期的なレビューと更新
- 古い情報は明示的にアーカイブ

### 4. **Machine Readable**
- Claude Codeが解析しやすい構造
- 明確な命名規則とパス構造
- 構造化されたマークダウン

---

## 📁 推奨ディレクトリ構造

```
project-root/
│
├── README.md                 # プロジェクト概要と入口
├── CLAUDE.md                 # Claude Code専用作業指示書
├── .claudeignore            # Claude Codeが無視するファイル
│
├── docs/                    # ドキュメントルート
│   ├── README.md           # ドキュメント索引
│   ├── architecture/       # アーキテクチャ設計
│   │   ├── overview.md    # システム全体像
│   │   ├── database.md    # DB設計
│   │   └── api.md         # API設計
│   │
│   ├── guides/            # 開発ガイド
│   │   ├── setup.md      # セットアップガイド
│   │   ├── development.md # 開発ガイド
│   │   └── deployment.md  # デプロイガイド
│   │
│   ├── api/               # API仕様書
│   │   ├── rest/         # REST API
│   │   └── graphql/      # GraphQL スキーマ
│   │
│   └── decisions/         # アーキテクチャ決定記録 (ADR)
│       ├── adr-001.md    # 決定記録テンプレート
│       └── template.md    # ADRテンプレート
│
├── specs/                  # 仕様書
│   ├── README.md          # 仕様書索引
│   ├── business/          # ビジネス要件
│   ├── functional/        # 機能仕様
│   └── technical/         # 技術仕様
│
└── scripts/               # 自動化スクリプト
    └── docs/             # ドキュメント生成スクリプト
```

---

## 📝 各ドキュメントファイルの役割と内容

### 1. **README.md（ルート）**

```markdown
# プロジェクト名

## 概要
- プロジェクトの目的と価値提案
- 主要機能の箇条書き（3-5項目）

## クイックスタート
\`\`\`bash
# インストール
npm install

# 開発サーバー起動
npm run dev
\`\`\`

## ドキュメント
- [アーキテクチャ設計](docs/architecture/overview.md)
- [セットアップガイド](docs/guides/setup.md)
- [API仕様](docs/api/)

## 技術スタック
- 主要な技術とバージョン

## ライセンス
```

### 2. **CLAUDE.md**

```markdown
# Claude Code 作業ガイド

## プロジェクト固有の規約

### コーディング規約
- TypeScript: strict mode有効
- インデント: スペース2つ
- 行末セミコロン: なし

### 命名規則
- ファイル名: kebab-case
- コンポーネント: PascalCase
- 変数・関数: camelCase

## よく使うコマンド

### 開発
\`\`\`bash
npm run dev        # 開発サーバー起動
npm run build      # ビルド
npm run test       # テスト実行
npm run lint       # Lint実行
npm run typecheck  # 型チェック
\`\`\`

### データベース
\`\`\`bash
npm run db:migrate   # マイグレーション実行
npm run db:seed      # シードデータ投入
npm run db:reset     # DBリセット
\`\`\`

## ファイル構造の規約
- 新規機能は features/ ディレクトリに追加
- 共通コンポーネントは components/common/ に配置
- ユーティリティは utils/ に配置

## 作業フロー
1. 仕様確認: specs/ を参照
2. 実装前にテストファイルを作成
3. 実装後は必ずlintとtypecheckを実行
4. PRにはテスト結果を含める

## 注意事項
- .envファイルは絶対にコミットしない
- 大容量ファイルは.claudeignoreに追加
- APIキーはすべて環境変数で管理
```

### 3. **.claudeignore**

```
# Dependencies
node_modules/
vendor/
.pnpm-store/

# Build outputs
dist/
build/
out/
.next/
*.pyc
__pycache__/

# Large files
*.mp4
*.zip
*.tar.gz
data/*.csv
datasets/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment
.env
.env.local
.env.*.local

# Test coverage
coverage/
.nyc_output/
```

### 4. **docs/README.md**

```markdown
# ドキュメント索引

## 📚 カテゴリ別ドキュメント

### アーキテクチャ
- [システム全体像](./architecture/overview.md) - 最終更新: 2024-01-15
- [データベース設計](./architecture/database.md) - 最終更新: 2024-01-10
- [API設計](./architecture/api.md) - 最終更新: 2024-01-12

### 開発ガイド
- [セットアップガイド](./guides/setup.md) - 環境構築手順
- [開発ガイド](./guides/development.md) - 開発フロー
- [デプロイガイド](./guides/deployment.md) - 本番環境へのデプロイ

### API仕様
- [REST API](./api/rest/) - RESTful API仕様
- [GraphQL](./api/graphql/) - GraphQLスキーマ

### 決定記録
- [ADR一覧](./decisions/) - アーキテクチャ決定記録

## 📝 ドキュメント作成ルール
1. マークダウン形式で記述
2. 相対パスでリンク
3. 更新日時を記載
4. 図表はMermaidを使用
```

### 5. **specs/README.md**

```markdown
# 仕様書管理

## 📋 仕様書一覧

| ドキュメント | 説明 | バージョン | 最終更新 | ステータス |
|------------|------|-----------|---------|-----------|
| [ビジネス仕様](./business/) | ビジネス要件と目標 | v2.0 | 2024-01-15 | ✅ 確定 |
| [機能仕様](./functional/) | 機能要件定義 | v1.5 | 2024-01-10 | 🔄 更新中 |
| [技術仕様](./technical/) | 技術実装詳細 | v1.0 | 2024-01-05 | 📝 ドラフト |

## バージョン管理ルール
- Major: 破壊的変更
- Minor: 機能追加
- Patch: バグ修正

## ステータス定義
- ✅ 確定: 実装可能な状態
- 🔄 更新中: レビュー・修正中
- 📝 ドラフト: 初期案
- 🗄️ アーカイブ: 過去バージョン
```

---

## 🤖 Claude Code 自走ルール

### ドキュメント更新の自動判断基準

Claude Codeは以下の条件で自動的にドキュメント更新を提案・実行します：

#### 1. **必須更新トリガー**
- 新機能の実装完了時
- APIエンドポイントの追加・変更時
- データベーススキーマの変更時
- 破壊的変更の実装時
- 依存関係の大幅な更新時

#### 2. **更新対象の自動識別**
```yaml
コード変更タイプ → 更新すべきドキュメント:
  - 新規ファイル作成:
    - README.mdのプロジェクト構造
    - CLAUDE.mdのファイル規約
  
  - API変更:
    - docs/api/の該当仕様書
    - specs/technical/の技術仕様
  
  - DB変更:
    - docs/architecture/database.md
    - specs/technical/のスキーマ定義
  
  - 環境変数追加:
    - .env.example
    - docs/guides/setup.md
  
  - コマンド追加:
    - CLAUDE.mdのコマンド一覧
    - package.jsonのscripts
```

#### 3. **ドキュメント生成テンプレート**

新規機能追加時のドキュメントテンプレート：

```markdown
## 機能名

### 概要
[1-2文で機能の目的を説明]

### 使用方法
\`\`\`typescript
// コード例
\`\`\`

### API
| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | /api/resource | リスト取得 |

### 設定
| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| CONFIG_VAR | 設定の説明 | default |

### 関連ドキュメント
- [リンク](path/to/doc.md)
```

### 自動化スクリプト

```bash
#!/bin/bash
# docs/scripts/update-docs.sh

# ドキュメント索引の自動更新
find docs -name "*.md" -exec sh -c 'echo "- [$(basename {} .md)]({})"' \;

# 最終更新日の自動挿入
for file in docs/**/*.md; do
  sed -i "1s/^/<!-- Last Updated: $(date +%Y-%m-%d) -->\n/" "$file"
done
```

---

## 📊 ドキュメント品質メトリクス

### 必須要素チェックリスト

各ドキュメントが満たすべき基準：

- [ ] **タイトルと概要**が明確
- [ ] **目次**（3階層以上の場合）
- [ ] **更新日時**の記載
- [ ] **著者/責任者**の明記
- [ ] **関連リンク**の設置
- [ ] **コード例**（技術文書の場合）
- [ ] **図表**（複雑な概念の場合）

### ドキュメント健全性スコア

```javascript
// ドキュメント健全性チェック
function calculateDocHealth(doc) {
  const score = {
    hasTitle: 10,
    hasTableOfContents: 10,
    hasUpdateDate: 15,
    hasCodeExamples: 20,
    hasLinks: 10,
    isUnder2000Lines: 15,
    usesProperFormatting: 20
  };
  
  // 30日以上更新されていない場合は警告
  if (daysSinceUpdate > 30) {
    console.warn(`⚠️ ${doc.path} needs update`);
  }
  
  return totalScore;
}
```

---

## 🔄 継続的改善プロセス

### 月次レビュー項目
1. 古いドキュメントの識別とアーカイブ
2. リンク切れのチェック
3. 新機能のドキュメント化状況
4. ユーザーフィードバックの反映

### 四半期レビュー項目
1. ドキュメント構造の見直し
2. 命名規則の一貫性確認
3. 図表の更新
4. サンプルコードの動作確認

---

## 🎯 成功指標 (KPI)

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| ドキュメントカバレッジ | 90%以上 | 機能数 / ドキュメント化済み機能数 |
| 更新頻度 | 30日以内 | 最終更新からの経過日数 |
| リンク有効性 | 100% | 有効リンク数 / 全リンク数 |
| コード例の動作率 | 100% | 動作するサンプル / 全サンプル |

---

## 📚 参考資料

- [Diátaxis Framework](https://diataxis.fr/) - ドキュメント構造の指針
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [The Documentation System](https://documentation.divio.com/)
- [Write the Docs](https://www.writethedocs.org/)

---

*最終更新: 2024-01-15*