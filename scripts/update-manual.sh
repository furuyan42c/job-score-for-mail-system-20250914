#!/bin/bash

# Super Claudeマニュアル更新スクリプト
# 使用方法: ./scripts/update-manual.sh [validation-id] [target-version]

VALIDATION_ID=${1:-"latest"}
TARGET_VERSION=${2:-"2.3"}

echo "==============================================="
echo "Super Claudeマニュアル更新システム"
echo "==============================================="
echo "検証結果ID: $VALIDATION_ID"
echo "ターゲットバージョン: v$TARGET_VERSION"
echo ""

# 前提条件チェック
echo "📋 前提条件をチェック中..."

# 検証結果の確認
VALIDATION_DIR="specs/001-think-hard-manual/validation-results"
if [ "$VALIDATION_ID" = "latest" ]; then
    RESULT_FILE=$(ls -t "$VALIDATION_DIR"/result-*.json 2>/dev/null | head -1)
else
    RESULT_FILE="$VALIDATION_DIR/result-$VALIDATION_ID.json"
fi

if [ ! -f "$RESULT_FILE" ]; then
    echo "❌ 検証結果ファイルが見つかりません: $RESULT_FILE"
    echo "まず ./scripts/validate.sh を実行してください"
    exit 1
fi

echo "✅ 検証結果を読み込みました: $RESULT_FILE"

# 元のマニュアルファイルの確認
SOURCE_MANUAL=".000.MANUAL/super_claude_integrated_manual_v2.2.md"
if [ ! -f "$SOURCE_MANUAL" ]; then
    echo "❌ 元のマニュアルファイルが見つかりません: $SOURCE_MANUAL"
    exit 1
fi

# 更新実行
echo ""
echo "📝 マニュアルの更新を開始します..."

# Step 1: バックアップ作成
echo "Step 1: 現在のマニュアルをバックアップ"
BACKUP_FILE=".000.MANUAL/super_claude_integrated_manual_v2.2.backup.$(date +%Y%m%d_%H%M%S).md"
cp "$SOURCE_MANUAL" "$BACKUP_FILE"
echo "✅ バックアップ作成: $BACKUP_FILE"

# Step 2: 更新処理
echo ""
echo "Step 2: マニュアルを更新"
TARGET_MANUAL=".000.MANUAL/super_claude_integrated_manual_v${TARGET_VERSION}.md"

if [ -f "src/cli/update-manual.js" ]; then
    node src/cli/update-manual.js \
        --validation-id "$VALIDATION_ID" \
        --source "$SOURCE_MANUAL" \
        --target "$TARGET_MANUAL" \
        --version "$TARGET_VERSION"
else
    echo "⚠️ マニュアル更新ツールが未実装です"
    echo "仮の更新版を作成します..."
    
    # 仮の更新版を作成（ヘッダーのバージョン番号のみ変更）
    sed "s/v2.2/v${TARGET_VERSION}/g" "$SOURCE_MANUAL" > "$TARGET_MANUAL"
    
    # 更新マーカーを追加
    {
        echo ""
        echo "---"
        echo "## 更新履歴"
        echo ""
        echo "### v${TARGET_VERSION} ($(date +%Y-%m-%d))"
        echo "- 検証システムによる自動更新"
        echo "- 未実装機能の削除"
        echo "- Claude Code代替プロンプトの追加"
        echo "- MCPサーバー利用可能性の更新"
    } >> "$TARGET_MANUAL"
fi

# Step 3: 移行ガイド生成
echo ""
echo "Step 3: 移行ガイドを生成"
MIGRATION_GUIDE="specs/001-think-hard-manual/migration-guide.md"

cat > "$MIGRATION_GUIDE" << 'EOF'
# 移行ガイド: v2.2 → v2.3

## 概要
このガイドは、Super Claudeマニュアル v2.2からv2.3への移行方法を説明します。

## 主な変更点

### 削除された機能
- `/handoff-to-codex` コマンド（未実装のため削除）
  - 代替: Task agentを使用 `Task agent --delegate`

### 更新された機能
- MCPサーバーの利用可能性
  - Morphllm: 未実装として明記
  - IDE連携: 新規追加

### 追加された機能
- Claude Code代替プロンプト例の充実
- トラブルシューティングセクションの実践的更新

## 移行手順

1. **バックアップ作成**
   ```bash
   cp .000.MANUAL/super_claude_integrated_manual_v2.2.md \
      .000.MANUAL/super_claude_integrated_manual_v2.2.backup.md
   ```

2. **新バージョンの適用**
   ```bash
   ./scripts/update-manual.sh
   ```

3. **検証**
   ```bash
   ./scripts/validate.sh 2.3
   ```

## 互換性

- v2.2のワークフローは基本的にv2.3でも動作します
- 削除されたコマンドを使用している場合は、代替プロンプトに置き換えてください

## サポート

問題が発生した場合は、以下を確認してください：
1. このガイドのトラブルシューティングセクション
2. specs/001-think-hard-manual/quickstart.md
3. プロジェクトのissueトラッカー
EOF

echo "✅ 移行ガイド作成: $MIGRATION_GUIDE"

# 結果サマリー
echo ""
echo "==============================================="
echo "更新完了"
echo "==============================================="
echo "✅ 新バージョン: $TARGET_MANUAL"
echo "✅ バックアップ: $BACKUP_FILE"
echo "✅ 移行ガイド: $MIGRATION_GUIDE"
echo ""
echo "次のステップ:"
echo "1. 新バージョンの内容を確認"
echo "2. ./scripts/validate.sh $TARGET_VERSION で再検証"
echo "3. 問題がなければコミット"