# プロジェクト固有ドキュメント整備ガイド

## 📋 このプロジェクトで必要なドキュメント一覧

### 優先度: 🔴 高（即座に作成）

#### 1. **README.md（ルートディレクトリ）**
```markdown
# バイト求人マッチングシステム

## 🎯 概要
1万人のユーザーに対して、10万件の求人データから毎日40件を自動選定し、
パーソナライズされたメールを配信するマッチングシステム。

## 🚀 クイックスタート

### 前提条件
- Docker Desktop
- Node.js 18+
- PostgreSQL 15+

### セットアップ
\`\`\`bash
# リポジトリのクローン
git clone [repository-url]
cd new-mail-score-20250904

# 環境変数の設定
cp .env.example .env
# .envファイルを編集して必要な値を設定

# Dockerコンテナの起動
docker-compose up -d

# フロントエンドの起動
cd front
npm install
npm run dev
\`\`\`

## 📚 ドキュメント
- [システム仕様](specs/system_specification_v2.md)
- [ビジネス仕様](specs/business_specification.md)
- [ER図](specs/ER/20250904_ER_new_modified.mmd)
- [フロントエンド仕様](specs/frontend_er_viewer_spec.md)

## 🛠 技術スタック
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL 15+ (Supabase)
- **Email**: SendGrid / Amazon SES
- **AI/ML**: OpenAI GPT-4, Claude API

## 📁 プロジェクト構造
\`\`\`
new-mail-score-20250904/
├── front/              # Next.jsフロントエンド
├── backend/            # Python バックエンド（未実装）
├── data/              # サンプルデータ・CSV
├── specs/             # 仕様書
├── docs/              # ドキュメント
└── docker-compose.yml # Docker設定
\`\`\`

## 🔧 主要コマンド
- `npm run dev` - 開発サーバー起動
- `npm run build` - ビルド
- `npm run test` - テスト実行
- `docker-compose up` - Docker環境起動

## 📞 お問い合わせ
[プロジェクト管理者の連絡先]
```

#### 2. **CLAUDE.md（ルートディレクトリ）**
```markdown
# Claude Code 作業ガイド

## プロジェクト概要
バイト求人マッチングシステムの開発プロジェクト。
1万人×10万件のマッチングを毎日実行する大規模システム。

## 重要な仕様書
- 最新仕様: specs/system_specification_v2.md
- ビジネス要件: specs/business_specification.md
- DB設計: specs/ER/20250904_ER_new_modified.mmd

## コーディング規約

### TypeScript/JavaScript
- strict mode有効
- インデント: スペース2つ
- セミコロン: なし
- 命名規則:
  - ファイル: kebab-case
  - コンポーネント: PascalCase
  - 変数/関数: camelCase

### Python
- PEP 8準拠
- 型ヒント必須
- docstring必須

## よく使うコマンド

### 開発環境
\`\`\`bash
# Docker環境起動
docker-compose up -d

# フロントエンド開発
cd front
npm run dev

# Supabaseローカル起動
supabase start

# PostgreSQL接続
psql -h localhost -U postgres -d mailscore
\`\`\`

### テスト・品質チェック
\`\`\`bash
npm run test          # テスト実行
npm run test:coverage # カバレッジ確認
npm run lint          # ESLint実行
npm run typecheck     # TypeScript型チェック
\`\`\`

### データベース操作
\`\`\`bash
# マイグレーション実行（Prisma使用時）
npx prisma migrate dev

# シードデータ投入
npm run db:seed

# DBリセット
npm run db:reset
\`\`\`

## ディレクトリ構造の規約

### フロントエンド (front/)
\`\`\`
front/
├── app/              # Next.js App Router
├── components/       # 再利用可能コンポーネント
│   ├── common/      # 共通コンポーネント
│   ├── features/    # 機能別コンポーネント
│   └── layouts/     # レイアウト
├── lib/             # ユーティリティ関数
├── hooks/           # カスタムフック
└── types/           # TypeScript型定義
\`\`\`

### バックエンド (backend/) - 未実装
\`\`\`
backend/
├── api/             # APIエンドポイント
├── models/          # データモデル
├── services/        # ビジネスロジック
├── utils/           # ユーティリティ
└── tests/           # テスト
\`\`\`

## 実装時の注意事項

### セキュリティ
- APIキーは必ず環境変数で管理
- .envファイルは絶対にコミットしない
- SQLインジェクション対策を徹底

### パフォーマンス
- 1万人×10万件の処理を考慮
- バッチ処理は非同期で実装
- DB接続はコネクションプーリング使用

### エラーハンドリング
- すべてのAPIエンドポイントでエラー処理
- ユーザーフレンドリーなエラーメッセージ
- エラーログの適切な記録

## TODOリスト管理
- 実装前に必ずTODOリストを作成
- 各タスクは具体的で測定可能に
- 完了したらすぐにステータス更新

## デバッグ用コマンド
\`\`\`bash
# Dockerログ確認
docker-compose logs -f

# PostgreSQL直接接続
docker exec -it postgres_container psql -U postgres

# Redisモニタリング
redis-cli monitor
\`\`\`
```

#### 3. **.claudeignore（ルートディレクトリ）**
```
# Dependencies
node_modules/
.pnpm-store/
vendor/

# Build outputs
.next/
dist/
build/
out/
*.pyc
__pycache__/

# Large data files
data/*.csv
data/*.json
datasets/
*.sqlite
*.db

# IDE and OS
.idea/
.vscode/
.DS_Store
Thumbs.db
*.swp
*.swo

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment
.env
.env.local
.env.*.local

# Test
coverage/
.nyc_output/
*.test.js.snap

# Temporary files
tmp/
temp/
*.tmp

# Docker
docker-compose.override.yml
```

### 優先度: 🟡 中（段階的に作成）

#### 4. **docs/README.md**
```markdown
# ドキュメント索引

## 📚 プロジェクトドキュメント

### 開発ガイド
- [ドキュメント管理ベストプラクティス](./documentation-best-practices.md)
- [Claude Code自走ルール](./claude-code-automation-rules.md)
- [プロジェクト固有設定](./project-documentation-setup.md)

### アーキテクチャ
- [システムアーキテクチャ](./architecture/system-overview.md) - 作成予定
- [データベース設計](./architecture/database-design.md) - 作成予定
- [API設計](./architecture/api-design.md) - 作成予定

### 開発手順
- [環境構築ガイド](./guides/setup.md) - 作成予定
- [開発フロー](./guides/development.md) - 作成予定
- [デプロイメント](./guides/deployment.md) - 作成予定

## 🔗 仕様書リンク
- [システム仕様 v2.0](../specs/system_specification_v2.md)
- [ビジネス仕様](../specs/business_specification.md)
- [ER図](../specs/ER/20250904_ER_new_modified.mmd)

## 📝 ドキュメント作成ルール
1. すべてマークダウン形式
2. 日本語で記述
3. 図表はMermaidを使用
4. 更新日時を必ず記載

最終更新: 2024-01-15
```

#### 5. **specs/README.md**
```markdown
# 仕様書管理

## 📋 仕様書一覧

| ドキュメント | 説明 | バージョン | 最終更新 | ステータス |
|------------|------|-----------|---------|-----------|
| [system_specification_v2.md](./system_specification_v2.md) | システム総合仕様書 | v2.0 | 2024-09-04 | ✅ 最新 |
| [business_specification.md](./business_specification.md) | ビジネス仕様書 | v1.0 | 2024-09-05 | ✅ 確定 |
| [20250901_specification.md](./20250901_specification.md) | 初期仕様 | v0.1 | 2024-09-01 | 🗄️ アーカイブ |
| [frontend_er_viewer_spec.md](./frontend_er_viewer_spec.md) | ERビューアー仕様 | v1.0 | 2024-09-04 | 📝 ドラフト |

## 📊 ER図

| ファイル | 説明 | 最終更新 |
|---------|------|---------|
| [20250904_ER_new_modified.mmd](./ER/20250904_ER_new_modified.mmd) | 最新ER図 | 2024-09-04 |
| [ER_new_modified.mmd](./ER/ER_new_modified.mmd) | 旧ER図 | 2024-08-31 |

## 🔄 更新履歴

### 2024-09-04
- system_specification_v2.md: LLM実装詳細を追加
- ER図を更新（20250904_ER_new_modified.mmd）

### 2024-09-01
- 初期仕様書作成

## 📌 注意事項
- 最新の仕様は `system_specification_v2.md` を参照
- DB設計は `ER/20250904_ER_new_modified.mmd` が最新
- 実装時は必ず最新版を確認すること
```

### 優先度: 🟢 低（必要に応じて作成）

#### 6. **docs/architecture/system-overview.md**
```markdown
# システムアーキテクチャ概要

## システム構成図

\`\`\`mermaid
graph TB
    subgraph "データ収集層"
        A[外部求人API] --> B[データ収集バッチ]
        C[CSVインポート] --> B
    end
    
    subgraph "データ処理層"
        B --> D[PostgreSQL]
        E[SEMRush API] --> F[スコアリングバッチ]
        D --> F
        F --> G[job_enrichment]
    end
    
    subgraph "マッチング層"
        G --> H[マッチングバッチ]
        H --> I[user_job_mapping]
    end
    
    subgraph "配信層"
        I --> J[メール生成バッチ]
        J --> K[daily_email_queue]
        K --> L[SendGrid/SES]
        L --> M[ユーザー]
    end
\`\`\`

## 主要コンポーネント

### 1. データ収集バッチ
- 実行頻度: 日次（深夜2:00）
- 処理内容: 10万件の求人データ取得
- 処理時間目標: 30分以内

### 2. スコアリングバッチ
- 実行頻度: 日次（深夜3:00）
- 処理内容: SEMRushキーワードマッチング
- 処理時間目標: 45分以内

### 3. マッチングバッチ
- 実行頻度: 日次（深夜4:00）
- 処理内容: 1万人×40件のマッチング
- 処理時間目標: 60分以内

### 4. メール配信バッチ
- 実行頻度: 日次（朝6:00）
- 処理内容: 1万通のメール送信
- 処理時間目標: 30分以内

## スケーラビリティ設計

### 水平スケーリング
- バッチ処理の並列実行
- DB読み取りレプリカの活用
- Redis/Memcachedでのキャッシング

### 垂直スケーリング
- PostgreSQLのチューニング
- インデックス最適化
- パーティショニング

最終更新: 2024-01-15
```

---

## 🚀 実装手順

### ステップ1: 基本ドキュメントの作成（優先度:高）
```bash
# 1. README.mdを作成
# 2. CLAUDE.mdを作成
# 3. .claudeignoreを作成
```

### ステップ2: ドキュメントインデックスの整備（優先度:中）
```bash
# 4. docs/README.mdを作成
# 5. specs/README.mdを作成
```

### ステップ3: 詳細ドキュメントの追加（優先度:低）
```bash
# 6. アーキテクチャドキュメント作成
# 7. 開発ガイド作成
# 8. API仕様書作成
```

---

## 📝 メンテナンスチェックリスト

### 日次チェック
- [ ] 新規作成ファイルのドキュメント化
- [ ] 変更されたAPIの仕様更新
- [ ] テストカバレッジの確認

### 週次チェック
- [ ] 古いドキュメントの更新（30日以上）
- [ ] リンク切れの確認
- [ ] TODOコメントの整理

### 月次チェック
- [ ] ドキュメント構造の見直し
- [ ] 不要ファイルの削除
- [ ] パフォーマンスメトリクスの更新

---

## 🎯 品質目標

| 項目 | 目標値 |
|-----|--------|
| ドキュメントカバレッジ | 90%以上 |
| 更新頻度 | 30日以内 |
| リンク有効性 | 100% |
| コード例の動作率 | 100% |

---

*このガイドに従って、プロジェクトのドキュメントを整備してください。*

*最終更新: 2024-01-15*