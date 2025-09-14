# /verify-and-pr コマンド

## 概要
実装内容を検証し、問題がなければ自動的にプルリクエストを作成してコメントを追加する統合コマンドです。

## 使用方法
```
/verify-and-pr [機能名] "[PRタイトル]"
```

## 実行フロー

### Phase 1: 検証（Verification）

#### 1.1 仕様準拠チェック
```bash
# spec.mdとの照合
cat specs/${機能名}/spec.md
# 実装ファイルの確認
find . -name "*.js" -o -name "*.ts" -o -name "*.py" | grep -E "${機能名}"
```

#### 1.2 コード品質チェック
```bash
# Lintとフォーマット
npm run lint || python -m flake8
npm run format || black . --check

# 型チェック
npm run typecheck || python -m mypy
```

#### 1.3 テスト実行
```bash
# テストとカバレッジ
npm test -- --coverage || python -m pytest --cov
```

#### 1.4 セキュリティスキャン
```bash
# 依存関係の脆弱性チェック
npm audit || pip-audit
```

### Phase 2: 検証結果の評価

```markdown
## 検証結果サマリー
- 🟢 仕様準拠: [%]
- 🟢 コード品質: [A/B/C]
- 🟢 セキュリティ: [Pass/Fail]
- 🟢 テストカバレッジ: [%]

## 判定
✅ すべての項目が基準を満たしています → PR作成へ進む
❌ 改善が必要な項目があります → 修正を促す
```

### Phase 3: プルリクエスト作成（検証合格の場合のみ）

#### 3.1 事前準備
```bash
# ブランチとコミット状態の確認
git branch --show-current
git status
git log --oneline -5
```

#### 3.2 PR作成
```bash
gh pr create \
  --title "[PRタイトル]" \
  --body "$(cat <<EOF
## 📋 概要
[機能名]の実装が完了しました。

## ✅ 検証結果
### 合格項目
- 仕様準拠: ${仕様準拠率}%
- コード品質: ${品質グレード}
- セキュリティ: Pass
- テストカバレッジ: ${カバレッジ}%

### 仕様書リンク
- 📝 [仕様書](specs/${機能名}/spec.md)
- 📋 [実装計画](specs/${機能名}/plan.md)
- ✅ [タスクリスト](specs/${機能名}/tasks.md)

## 🧪 テスト結果
\`\`\`
${テスト結果}
\`\`\`

## 📸 スクリーンショット
[UIの変更がある場合]

## ✔️ チェックリスト
- [x] 仕様書の要件をすべて満たしている
- [x] テストが通っている
- [x] Lintエラーがない
- [x] 型チェックが通っている
- [x] セキュリティスキャンをパスしている
- [x] レビュー準備完了

## 💬 レビュアーへのメモ
自動検証により品質基準を満たしていることを確認済みです。
詳細な検証レポートはコメントに添付します。

🤖 Generated with Claude Code
EOF
)" \
  --base main \
  --assignee @me
```

#### 3.3 検証レポートをコメントとして追加
```bash
# 詳細な検証レポートを作成
cat > /tmp/verification-report.md <<EOF
# 🔍 詳細検証レポート

## 仕様準拠の詳細
### 実装された機能要件
${実装済み機能リスト}

### 非機能要件の達成状況
${NFR達成状況}

## コード品質の詳細
### メトリクス
- 循環的複雑度: ${複雑度}
- 重複コード: ${重複率}%
- 技術的負債: ${負債時間}

### 改善提案（任意）
${改善提案リスト}

## セキュリティ分析
### チェック項目
- ✅ 入力検証
- ✅ 認証・認可
- ✅ SQLインジェクション対策
- ✅ XSS対策
- ✅ 機密情報の取り扱い

## パフォーマンス評価
- 平均レスポンス時間: ${レスポンス時間}ms
- メモリ使用量: ${メモリ}MB
- DB クエリ数: ${クエリ数}

## 今後の改善点
${今後の改善点}

---
⏰ 検証実行時刻: $(date)
🤖 自動生成レポート by Claude Code
EOF

# コメントとして投稿
gh pr comment --body-file /tmp/verification-report.md
```

#### 3.4 ラベルとステータス設定
```bash
# 適切なラベルを追加
gh pr edit --add-label "ready-for-review"
gh pr edit --add-label "${機能カテゴリ}"
gh pr edit --add-label "verified"

# レビュアーへの通知
echo "✅ PR #${PR番号} を作成し、検証レポートを添付しました"
```

## エラーハンドリング

### 検証失敗時の処理
```markdown
## ❌ 検証失敗

以下の項目で問題が検出されました：

### 要修正項目
1. **[問題1]**
   - 詳細: [説明]
   - 修正方法: [提案]
   - 参考: [リンク]

2. **[問題2]**
   - 詳細: [説明]
   - 修正方法: [提案]

### 次のステップ
1. 上記の問題を修正してください
2. 修正後、再度 `/verify-and-pr` を実行してください

💡 ヒント: 個別に検証したい場合は `/verify` コマンドを使用できます
```

### Git状態の問題
```bash
# コミットされていない変更がある場合
if [[ -n $(git status -s) ]]; then
  echo "⚠️ コミットされていない変更があります"
  echo "以下のコマンドで変更をコミットしてください："
  echo "  git add ."
  echo "  git commit -m \"feat: ${機能名}の実装\""
  exit 1
fi
```

## 使用例

### 基本的な使用
```bash
# 認証機能の検証とPR作成
/verify-and-pr auth "feat: JWT認証システムの実装"
```

### 詳細オプション付き
```bash
# セキュリティ重視の検証とPR作成
/verify-and-pr payment "feat: 決済システムの追加" --security-focus

# 緊急修正のPR（簡易検証）
/verify-and-pr hotfix "fix: ログイン時のクラッシュを修正" --quick
```

## オプション

- `--quick`: 簡易検証モード（CI/CD用）
- `--comprehensive`: 包括的検証モード
- `--security-focus`: セキュリティ重視の検証
- `--performance-focus`: パフォーマンス重視の検証
- `--draft`: ドラフトPRとして作成
- `--reviewers [names]`: レビュアーを指定
- `--auto-merge`: 承認後の自動マージを有効化

## ワークフロー統合

```yaml
# .github/workflows/verify-and-pr.yml
name: Verify and Create PR

on:
  push:
    branches:
      - 'feature/*'

jobs:
  verify-and-pr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run verification and create PR
        run: |
          /verify-and-pr ${FEATURE_NAME} "${PR_TITLE}"
```

## 成功基準

検証がPASSしてPRが作成されるための基準：

| 項目 | 最小要件 | 推奨値 |
|------|---------|--------|
| 仕様準拠率 | 90% | 95%以上 |
| テストカバレッジ | 70% | 80%以上 |
| Lintエラー | 0 | 0 |
| セキュリティ警告 | Critical: 0 | すべて0 |
| パフォーマンス | 基準値以内 | 基準値の80%以下 |

## 注意事項

1. **前提条件**
   - feature/ブランチで作業していること
   - すべての変更がコミットされていること
   - package.jsonまたはrequirements.txtが正しく設定されていること

2. **推奨事項**
   - 大きな機能は複数の小さなPRに分割する
   - PRタイトルは[Conventional Commits](https://www.conventionalcommits.org/)形式を使用
   - 検証に失敗した場合は、修正してから再実行

3. **セキュリティ**
   - 機密情報をコミットしていないことを確認
   - APIキーや認証情報は環境変数を使用
   - セキュリティ関連の変更は必ずセキュリティレビューを依頼

## トラブルシューティング

### よくある問題と解決方法

| 問題 | 原因 | 解決方法 |
|------|------|----------|
| PR作成失敗 | 権限不足 | `gh auth login` でGitHub認証 |
| テスト失敗 | 環境設定 | `.env.test` ファイルを確認 |
| Lint エラー | 設定不一致 | `npm run lint:fix` で自動修正 |
| カバレッジ不足 | テスト不足 | 追加テストを作成 |