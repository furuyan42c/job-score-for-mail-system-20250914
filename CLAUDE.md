# Claude Code 作業ガイド

## 🎯 このプロジェクトについて
**バイト求人マッチングシステム** - 1万人のユーザーに10万件の求人から毎日40件を自動配信

## 📋 重要ファイル
- **最新仕様**: `specs/20250905_system_spec_v2.0.md` 
- **DB設計**: `specs/ER/20250904_er_complete_v2.0.mmd`
- **ビジネス要件**: `specs/20250905_business_spec_v1.0.md`

## 💻 よく使うコマンド

### 開発
```bash
cd front
npm run dev      # 開発サーバー (http://localhost:3000)
npm run build    # ビルド
npm run test     # テスト
npm run lint     # ESLint
npm run typecheck # TypeScript型チェック
```

### Docker
```bash
docker-compose up -d    # バックグラウンドで起動
docker-compose logs -f  # ログ監視
docker-compose down     # 停止
```

## 📁 ディレクトリ構造
```
front/
├── app/          # Next.js App Router
├── components/   # コンポーネント
├── lib/         # ユーティリティ
└── types/       # 型定義
```

## ✅ 作業時のルール

1. **実装前に必ず仕様書を確認** - `specs/`ディレクトリ
2. **DB変更時はER図を更新** - Mermaid形式で記述
3. **テストとLintを実行** - コミット前に確認
4. **環境変数は.envで管理** - 絶対にコミットしない

## 📝 ファイル命名規則

### 新規ファイル作成時
- **日付付き**: `20250905_[内容]_v1.0.md` （仕様書・ER図）
- **バージョン付き**: `[内容]_v1.0.md` （継続更新）
- **禁止**: `untitled.md`, `temp.md`, `test.md`, 日本語名

### 重要
- **既存ファイルの編集を優先** - 新規作成は最小限に
- **archive/に古いファイルを移動** - 新バージョン作成時や明らかに不要な場合のみ
- **詳細**: `docs/20250105_file_naming_rules_v1.0.md`参照

## ⚠️ 注意事項

- **セキュリティ**: APIキーは環境変数で管理
- **パフォーマンス**: 1万人×10万件の処理を考慮
- **エラー処理**: ユーザーフレンドリーなメッセージ

## 🔍 デバッグ

```bash
# PostgreSQL接続
docker exec -it [container_name] psql -U postgres

# Next.jsデバッグ
NODE_OPTIONS='--inspect' npm run dev
```

## 📝 TODOリスト使用推奨

複雑なタスクは`TodoWrite`ツールで管理：
- 3つ以上のステップがある作業
- 複数ファイルにまたがる変更
- バグ修正で調査が必要な場合

## 🚀 クイック対応

| やりたいこと | コマンド/ファイル |
|------------|------------------|
| UI変更 | `front/app/` |
| API追加 | 未実装（Python予定） |
| DB確認 | `specs/ER/*.mmd` |
| 仕様確認 | `specs/*.md` |

---
*シンプルに、確実に、効率的に作業しましょう*