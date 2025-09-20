#!/usr/bin/env bash
# TodoWrite強制機能テストスクリプト

set -euo pipefail

echo "=== TodoWrite強制機能テスト ==="
echo

# テスト用の仮想関数を定義
send_multiline() {
    echo "📤 [SENDING MULTILINE]:"
    echo "$1"
    echo "📤 [END MULTILINE]"
    echo
}

send() {
    echo "📤 [SENDING]: $1"
    echo
}

log() {
    echo "📝 [LOG]: $*"
}

# 強制機能を定義（テスト用）
enforce_todowrite(){
    log "Enforcing TodoWrite usage (anti-procrastination measure)"

    local todo_enforcement="
/note TodoWrite更新が必要です。以下を必ず実行してください：

1. 【必須】TodoWrite更新:
   - 現在の作業状況をTodoWriteで記録
   - 完了したタスクをcompletedに変更
   - 次のタスクをin_progressに設定
   - 新しく発見したタスクを追加

2. 【必須】進捗の可視化:
   - TodoWriteでタスクの依存関係を明確化
   - ブロッカーをTodoWriteで明記
   - 並列実行可能なタスクをTodoWriteで特定

3. 【厳守】TodoWrite使用ルール:
   - 作業開始時: TodoWrite必須
   - 30分毎: TodoWrite更新必須
   - タスク完了時: TodoWrite完了マーク必須
   - 新タスク発見時: TodoWrite追加必須

TodoWriteを使わない作業は禁止です。即座にTodoWriteを更新してから作業を継続してください。"

    send_multiline "$todo_enforcement"
    log "TodoWrite enforcement command sent"
}

check_todowrite_compliance(){
    log "Checking TodoWrite compliance before save/load operation"

    local todowrite_reminder="
/note 🚨 チェックポイント操作前のTodoWrite確認 🚨

【必須確認事項】
✅ 現在のTodoWriteは最新状態ですか？
✅ 完了したタスクをcompletedにマークしましたか？
✅ 進行中タスクをin_progressに設定しましたか？
✅ 新しく発見したタスクを追加しましたか？
✅ ブロッカーを明記しましたか？

【重要】チェックポイント保存/復元の前後で必ずTodoWriteを更新してください。
作業の継続性を保つため、TodoWrite管理は最優先事項です。"

    send_multiline "$todowrite_reminder"
    log "TodoWrite compliance check sent"
}

echo "🧪 テスト1: enforce_todowrite() 関数"
echo "=================================="
enforce_todowrite
echo

echo "🧪 テスト2: check_todowrite_compliance() 関数"
echo "=============================================="
check_todowrite_compliance
echo

echo "🧪 テスト3: save/load時のTodoWrite強制メッセージ確認"
echo "=================================================="

# save_ckpt関数の一部をテスト
echo "💾 save_ckpt() のTodoWrite強制部分:"
echo "-----------------------------------"
send "/note 【保存前確認】現在の作業状況をTodoWriteで記録してから/sc-saveを実行します"
check_todowrite_compliance
send "/note 【保存完了】チェックポイント test-001 を保存しました。復元時のためにTodoWriteの状態も記録しておいてください。"
echo

# load_last関数の一部をテスト
echo "📁 load_last() のTodoWrite強制部分:"
echo "-----------------------------------"
send "/note 【復元前確認】チェックポイント test-001 から復元します。作業再開時は必ずTodoWriteを更新してください。"
check_todowrite_compliance
send "/note 【復元完了】作業を再開する前に、必ずTodoWriteで現在の状況を確認・更新してください。"
enforce_todowrite
echo

echo "🧪 テスト4: continue_prompt.txtのTodoWrite強調確認"
echo "================================================"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/continue_prompt.txt" ]]; then
    echo "📄 continue_prompt.txt の TodoWrite 関連箇所:"
    echo "--------------------------------------------"
    grep -A 10 -B 2 "TodoWrite" "$SCRIPT_DIR/continue_prompt.txt" | head -20
else
    echo "❌ continue_prompt.txt が見つかりません"
fi
echo

echo "🧪 テスト5: 定期リマインダーメッセージ"
echo "=================================="
echo "📅 10分毎の定期リマインダー:"
send "/note 【定期リマインダー】TodoWriteの更新はお済みですか？作業の進捗を正確に記録するため、定期的なTodoWrite更新をお願いします。"
echo

echo "📊 テスト結果サマリー"
echo "==================="
echo "✅ enforce_todowrite(): 詳細なTodoWrite使用指示を送信"
echo "✅ check_todowrite_compliance(): チェックポイント操作時の確認"
echo "✅ save/load 強化: 保存・復元時の強制リマインダー"
echo "✅ continue_prompt: TodoWrite必須化の明記"
echo "✅ 定期リマインダー: 10分毎の自動送信"
echo

echo "🎯 強制機能の効果"
echo "================"
echo "1. アイドル時（600秒毎）: TodoWrite強制 + 継続プロンプト"
echo "2. チェックポイント時: 保存・復元前後でTodoWrite確認"
echo "3. 定期リマインダー（10分毎）: サボり防止のリマインダー"
echo "4. 継続プロンプト: TodoWriteなしの作業禁止を明記"
echo "5. エラー回復時: TodoWrite確認を含む復元処理"
echo

echo "🚨 重要ポイント"
echo "=============="
echo "• Claude Codeのサボり癖を多層防御で阻止"
echo "• /sc-save と /sc-load の前後で必ず TodoWrite 確認"
echo "• 作業継続時の TodoWrite 使用を絶対必須化"
echo "• 定期的な自動リマインダーで継続的な圧力"
echo

echo "=== TodoWrite強制機能テスト完了 ==="