# バイト求人マッチングシステム

## 🎯 概要
1万人のユーザーに対して、10万件の求人データから毎日40件を自動選定し、パーソナライズされたメールを配信するマッチングシステム。

## 🚀 クイックスタート

### 前提条件
- Docker Desktop
- Node.js 18+
- PostgreSQL 15+ (Supabase)

### セットアップ
```bash
# 1. リポジトリのクローン
git clone [repository-url]
cd new.mail.score

# 2. 環境変数の設定
cp .env.example .env
# .envファイルを編集して必要な値を設定

# 3. Dockerコンテナの起動
docker-compose up -d

# 4. フロントエンドの起動
cd front
npm install
npm run dev
```

アプリケーション: http://localhost:3000

## 📚 主要ドキュメント

| ドキュメント | 説明 |
|------------|------|
| [CLAUDE.md](CLAUDE.md) | Claude Code用の作業ガイド |
| [システム仕様](specs/20250905_system_spec_v2.0.md) | 詳細なシステム仕様書 |
| [ビジネス仕様](specs/20250905_business_spec_v1.0.md) | ビジネス要件 |
| [ER図](specs/ER/20250904_er_complete_v2.0.mmd) | データベース設計 |

## 🛠 技術スタック

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: Python 3.11+ (予定)
- **Database**: PostgreSQL 15+ (Supabase)
- **Email**: SendGrid / Amazon SES
- **AI/ML**: OpenAI GPT-4, Claude API

## 📁 プロジェクト構造

```
new.mail.score/
├── front/              # Next.jsフロントエンド
├── data/              # サンプルデータ・CSV
├── specs/             # 仕様書
│   ├── ER/           # ER図（Mermaid）
│   └── *.md          # 各種仕様書
├── docs/              # 開発ドキュメント
├── docker-compose.yml # Docker設定
└── .env.example       # 環境変数テンプレート
```

## 🔧 主要コマンド

```bash
# 開発
npm run dev          # 開発サーバー起動
npm run build        # ビルド
npm run test         # テスト実行
npm run lint         # Lint実行
npm run typecheck    # TypeScript型チェック

# Docker
docker-compose up    # サービス起動
docker-compose down  # サービス停止
docker-compose logs  # ログ確認
```

## 📝 開発の始め方

1. **仕様確認**: `specs/system_specification_v2.md`を読む
2. **環境構築**: 上記クイックスタートを実行
3. **開発**: `front/`ディレクトリで作業
4. **テスト**: `npm run test`でテスト実行

## 🚨 注意事項

- `.env`ファイルは絶対にコミットしない
- APIキーは環境変数で管理
- 大きな変更前は仕様書を確認

## 📞 お問い合わせ

[プロジェクト管理者の連絡先]

---

最終更新: 2025-01-05