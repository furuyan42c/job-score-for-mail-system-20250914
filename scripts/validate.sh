#!/bin/bash

# Super Claudeマニュアル検証スクリプト
# 使用方法: ./scripts/validate.sh [version] [scope]

VERSION=${1:-"2.2"}
SCOPE=${2:-"full"}

echo "==============================================="
echo "Super Claudeマニュアル検証システム"
echo "==============================================="
echo "検証対象バージョン: v$VERSION"
echo "検証範囲: $SCOPE"
echo ""

# 前提条件チェック
echo "📋 前提条件をチェック中..."

# Node.jsの確認
if ! command -v node &> /dev/null; then
    echo "❌ Node.jsがインストールされていません"
    exit 1
fi

# MCPサーバー設定の確認
if [ ! -d "$HOME/.config/claude/mcp" ]; then
    echo "⚠️ MCPサーバー設定が見つかりません"
fi

# コマンド実装の確認
if [ ! -d ".claude/commands" ]; then
    echo "❌ Spec-Kitコマンドディレクトリが見つかりません"
    exit 1
fi

# マニュアルファイルの確認
MANUAL_FILE=".000.MANUAL/super_claude_integrated_manual_v${VERSION}.md"
if [ ! -f "$MANUAL_FILE" ]; then
    echo "❌ マニュアルファイル $MANUAL_FILE が見つかりません"
    exit 1
fi

echo "✅ 前提条件チェック完了"
echo ""

# 検証実行
echo "🔍 検証を開始します..."

# Step 1: MCPサーバーチェック
echo "Step 1: MCPサーバーの利用可能性をチェック"
if [ -f "src/cli/check-mcp-servers.js" ]; then
    node src/cli/check-mcp-servers.js
else
    echo "⚠️ MCPチェッカーが未実装です"
fi

# Step 2: コマンド実装チェック
echo ""
echo "Step 2: Spec-Kitコマンドの実装状態を確認"
for cmd in specify plan tasks verify-and-pr; do
    if [ -f ".claude/commands/$cmd.md" ]; then
        echo "✅ /$cmd - 実装済み ($(wc -c < .claude/commands/$cmd.md) bytes)"
    else
        echo "❌ /$cmd - 未実装"
    fi
done

# Step 3: マニュアル検証
echo ""
echo "Step 3: マニュアル全体の検証"
if [ -f "src/cli/validate-manual.js" ]; then
    node src/cli/validate-manual.js --version "$VERSION" --scope "$SCOPE"
else
    echo "⚠️ マニュアル検証ツールが未実装です"
    echo "マニュアルファイルのサイズ: $(wc -l < $MANUAL_FILE) 行"
fi

# 結果サマリー
echo ""
echo "==============================================="
echo "検証完了"
echo "==============================================="
echo "詳細な結果は specs/001-think-hard-manual/validation-results/ を確認してください"

# 検証結果ディレクトリを作成
mkdir -p specs/001-think-hard-manual/validation-results

# タイムスタンプ付きで結果を保存
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="specs/001-think-hard-manual/validation-results/result-${TIMESTAMP}.json"

# 簡易的な結果JSONを生成
cat > "$RESULT_FILE" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "$VERSION",
  "scope": "$SCOPE",
  "status": "PENDING",
  "message": "検証ツール実装待ち"
}
EOF

echo "結果を保存しました: $RESULT_FILE"