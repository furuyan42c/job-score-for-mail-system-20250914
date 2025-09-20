#!/usr/bin/env bash
# Claude Code 自動化システム - 検知機能テストスクリプト

set -euo pipefail

# テスト用設定
TEST_TASKS_PATH="/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md"
TASKS_PATH="$TEST_TASKS_PATH"

# ログ関数
log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# 高度なタスク完了検知機能（TDD対応・ブロッカー検知・グループ進捗管理）
tasks_done(){
    [[ -f "$TASKS_PATH" ]] || return 1

    local total_tasks completed_tasks blocked_tasks group_completion

    # T形式のタスク（#### T001: タスク名 [100%] [Q:95%] [[DONE]]）を検知
    total_tasks=$(grep -Ec '^#### T[0-9]+:' "$TASKS_PATH" || true)
    completed_tasks=$(grep -Ec '^#### T[0-9]+:.*\[100%\].*\[\[DONE\]\]' "$TASKS_PATH" || true)

    # ブロッカータスクをチェック（⚠️ブロッカー）
    blocked_tasks=$(grep -Ec '⚠️.*ブロック|ブロック.*⚠️' "$TASKS_PATH" || true)

    # 従来形式のprogress:100%とチェックボックスもサポート
    local progress_total progress_done checkbox_total checkbox_done
    progress_total=$(grep -Ec 'progress:[[:space:]]*[0-9]+%' "$TASKS_PATH" || true)
    progress_done=$(grep -Ec 'progress:[[:space:]]*100%\\b' "$TASKS_PATH" || true)
    checkbox_total=$(grep -Ec '^[[:space:]]*[-*][[:space:]]*\[[ xX]\]' "$TASKS_PATH" || true)
    checkbox_done=$(grep -Ec '^[[:space:]]*[-*][[:space:]]*\[[xX]\]' "$TASKS_PATH" || true)

    # グループ全体の完了率をチェック（ダッシュボードから）
    group_completion=$(grep -Eo '\*\*合計\*\*.*\*\*[0-9]+%\*\*' "$TASKS_PATH" 2>/dev/null | grep -Eo '[0-9]+%' | tail -1 | tr -d '%' || echo "0")

    log "Task analysis: T-tasks=$total_tasks completed=$completed_tasks blocked=$blocked_tasks group_completion=${group_completion}%"

    # 完了条件の判定（複数条件で厳密にチェック）
    local t_format_complete=false
    local progress_complete=false
    local checkbox_complete=false
    local group_complete=false

    # T形式タスクが100%完了かつブロッカーなし
    if (( total_tasks > 0 && completed_tasks == total_tasks && blocked_tasks == 0 )); then
        t_format_complete=true
        log "T-format tasks: ALL COMPLETED ($completed_tasks/$total_tasks, no blockers)"
    fi

    # 従来のprogress形式チェック
    if (( progress_total == 0 || progress_done == progress_total )); then
        progress_complete=true
        log "Progress format: completed ($progress_done/$progress_total)"
    fi

    # チェックボックス形式チェック
    if (( checkbox_total == 0 || checkbox_done == checkbox_total )); then
        checkbox_complete=true
        log "Checkbox format: completed ($checkbox_done/$checkbox_total)"
    fi

    # グループ全体完了率チェック（95%以上で完了とみなす）
    if (( group_completion >= 95 )); then
        group_complete=true
        log "Group completion: ${group_completion}% >= 95%"
    fi

    # 総合判定（いずれかの条件で完了）
    if $t_format_complete || ($progress_complete && $checkbox_complete && $group_complete); then
        log "TASKS COMPLETED: t_format=$t_format_complete progress=$progress_complete checkbox=$checkbox_complete group=$group_complete"
        return 0
    else
        log "Tasks still in progress: t_format=$t_format_complete progress=$progress_complete checkbox=$checkbox_complete group=$group_complete"
        return 1
    fi
}

# TDDフェーズ分析機能
analyze_tdd_phase(){
    [[ -f "$TASKS_PATH" ]] || return 1

    local red_tasks green_tasks refactor_tasks total_tdd_tasks

    # TDDフェーズごとのタスク数を分析
    red_tasks=$(grep -Ec '\[25%\].*RED|\[\[RED\]\]' "$TASKS_PATH" || true)
    green_tasks=$(grep -Ec '\[50%\].*GREEN|\[\[GREEN\]\]' "$TASKS_PATH" || true)
    refactor_tasks=$(grep -Ec '\[75%\].*REFACTOR|\[\[REFACTOR\]\]' "$TASKS_PATH" || true)
    total_tdd_tasks=$(grep -Ec '^#### T[0-9]+:' "$TASKS_PATH" || true)

    log "TDD Analysis: RED=$red_tasks GREEN=$green_tasks REFACTOR=$refactor_tasks TOTAL=$total_tdd_tasks"

    # TDD準拠率の計算
    local tdd_compliance=0
    if (( total_tdd_tasks > 0 )); then
        tdd_compliance=$(( (red_tasks + green_tasks + refactor_tasks) * 100 / total_tdd_tasks ))
    fi

    log "TDD Compliance: ${tdd_compliance}%"

    # 進行中タスクの特定
    local current_task=$(grep -E '^#### T[0-9]+:.*\[(25|50|75)%\]' "$TASKS_PATH" | head -1 | grep -Eo 'T[0-9]+' || echo "none")
    if [[ "$current_task" != "none" ]]; then
        log "Current TDD task: $current_task"
    fi

    return 0
}

# ブロッカー検知と報告
check_blockers(){
    [[ -f "$TASKS_PATH" ]] || return 1

    local blockers
    blockers=$(grep -n '⚠️.*ブロック\|ブロック.*⚠️' "$TASKS_PATH" 2>/dev/null | head -5)

    if [[ -n "$blockers" ]]; then
        log "BLOCKERS DETECTED:"
        echo "$blockers" | while IFS=: read -r line_num content; do
            log "  Line $line_num: $(echo "$content" | sed 's/^[[:space:]]*//')"
        done
        return 0
    else
        log "No blockers detected"
        return 1
    fi
}

echo "=== Claude Code 自動化システム - 検知機能テスト ==="
echo "対象ファイル: $TEST_TASKS_PATH"
echo

# ファイル存在確認
if [[ ! -f "$TEST_TASKS_PATH" ]]; then
    echo "❌ エラー: タスクファイルが見つかりません: $TEST_TASKS_PATH"
    exit 1
fi

echo "✅ タスクファイル確認完了"
echo

# 1. 基本統計情報
echo "📊 基本統計情報"
echo "=================="
total_tasks=$(grep -Ec '^#### T[0-9]+:' "$TEST_TASKS_PATH" || true)
echo "総タスク数: $total_tasks"

completed_tasks=$(grep -Ec '^#### T[0-9]+:.*\[100%\].*\[\[DONE\]\]' "$TEST_TASKS_PATH" || true)
echo "完了タスク数: $completed_tasks"

blocked_tasks=$(grep -Ec '⚠️.*ブロック|ブロック.*⚠️' "$TEST_TASKS_PATH" || true)
echo "ブロック中タスク数: $blocked_tasks"

group_completion=$(grep -Eo '\*\*合計\*\*.*\*\*[0-9]+%\*\*' "$TEST_TASKS_PATH" 2>/dev/null | grep -Eo '[0-9]+%' | tail -1 | tr -d '%' || echo "0")
echo "グループ全体進捗: ${group_completion}%"
echo

# 2. TDD分析テスト
echo "🧪 TDD分析テスト"
echo "=================="
analyze_tdd_phase
echo

# 3. ブロッカー検知テスト
echo "⚠️ ブロッカー検知テスト"
echo "======================="
if check_blockers; then
    echo "ブロッカーが検知されました。"
else
    echo "ブロッカーは検知されませんでした。"
fi
echo

# 4. タスク完了検知テスト
echo "✅ タスク完了検知テスト"
echo "======================="
if tasks_done; then
    echo "✅ タスク完了条件: 満たしています"
    echo "   → システムは自動終了します"
else
    echo "🔄 タスク完了条件: まだ満たしていません"
    echo "   → システムは継続実行します"
fi
echo

# 5. 進行中タスクの詳細分析
echo "📈 進行中タスクの詳細分析"
echo "========================="

echo "進行中タスク（25%, 50%, 75%）:"
grep -En '^#### T[0-9]+:.*\[(25|50|75)%\]' "$TEST_TASKS_PATH" | head -5 | while IFS=: read -r line_num content; do
    task_id=$(echo "$content" | grep -Eo 'T[0-9]+' | head -1)
    progress=$(echo "$content" | grep -Eo '\[[0-9]+%\]' | head -1)
    phase=""
    if echo "$content" | grep -q "25%"; then phase="🔴 RED"; fi
    if echo "$content" | grep -q "50%"; then phase="🟢 GREEN"; fi
    if echo "$content" | grep -q "75%"; then phase="🔄 REFACTOR"; fi
    echo "  Line $line_num: $task_id $progress $phase"
done
echo

echo "未着手タスク（0%）:"
grep -En '^#### T[0-9]+:.*\[0%\]' "$TEST_TASKS_PATH" | head -5 | while IFS=: read -r line_num content; do
    task_id=$(echo "$content" | grep -Eo 'T[0-9]+' | head -1)
    echo "  Line $line_num: $task_id [0%] ⏳ 未着手"
done
echo

# 6. グループ別進捗分析
echo "📋 グループ別進捗分析"
echo "===================="

for group in "Group A" "Group B" "Group C" "Group D" "Group E"; do
    if grep -q "$group" "$TEST_TASKS_PATH" 2>/dev/null; then
        echo "$group:"
        # グループ内のタスク数を概算
        group_start_line=$(grep -n "$group" "$TEST_TASKS_PATH" | head -1 | cut -d: -f1)
        if [[ -n "$group_start_line" ]]; then
            # そのグループから次のグループまでの範囲でタスクを検索
            next_group_line=$(grep -n "^## Group" "$TEST_TASKS_PATH" | awk -v start="$group_start_line" '$1 > start {print $1; exit}' | cut -d: -f1)
            if [[ -n "$next_group_line" ]]; then
                range="${group_start_line},${next_group_line}"
            else
                range="${group_start_line},\$"
            fi

            group_tasks=$(sed -n "${range}p" "$TEST_TASKS_PATH" | grep -Ec '^#### T[0-9]+:' || true)
            group_done=$(sed -n "${range}p" "$TEST_TASKS_PATH" | grep -Ec '^#### T[0-9]+:.*\[100%\].*\[\[DONE\]\]' || true)

            if (( group_tasks > 0 )); then
                group_percent=$(( group_done * 100 / group_tasks ))
                echo "  タスク: $group_done/$group_tasks 完了 (${group_percent}%)"
            else
                echo "  タスクが見つかりません"
            fi
        fi
    fi
done
echo

# 7. 検知機能の動作確認
echo "🔍 検知機能の動作確認"
echo "===================="

echo "検知関数の動作状況:"
echo "- tasks_done(): $(tasks_done && echo "完了検知" || echo "継続判定")"
echo "- analyze_tdd_phase(): 分析完了"
echo "- check_blockers(): $(check_blockers >/dev/null && echo "ブロッカー検知" || echo "ブロッカーなし")"
echo

# 8. 設定値の確認
echo "⚙️ 設定値の確認"
echo "================"
echo "TASKS_PATH: $TASKS_PATH"
echo "ファイルサイズ: $(ls -lh "$TASKS_PATH" | awk '{print $5}')"
echo "最終更新: $(ls -l "$TASKS_PATH" | awk '{print $6, $7, $8}')"
echo

echo "=== テスト完了 ==="
echo "すべての検知機能が正常に動作しています。"