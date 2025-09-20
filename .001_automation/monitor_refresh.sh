#!/usr/bin/env bash
set -euo pipefail

# ===== 基本設定（環境変数で上書き可）=====
SESSION="${SESSION:-cc}"
TARGET="${TARGET:-cc:1.0}"                # Claude Code の tmux pane
START_CMD="${START_CMD:-codex /run agent}"# 初回起動
RESTART_CMD="${RESTART_CMD:-$START_CMD}"   # 再起動コマンド
TASKS_PATH="${TASKS_PATH:-$HOME/work/tasks.md}"
CONTINUE_PROMPT_FILE="${CONTINUE_PROMPT_FILE:-$(dirname "$0")/continue_prompt.txt}"

# 挙動パラメータ
IDLE_SECS="${IDLE_SECS:-600}"             # 無出力連続で /continue
COOLDOWN_SECS="${COOLDOWN_SECS:-45}"      # /continue 後のクールダウン
AUTO_SAVE_MINS="${AUTO_SAVE_MINS:-15}"    # 定期 /sc-save (0=無効)
CONTEXT_THRESHOLD="${CONTEXT_THRESHOLD:-70}" # 0=無効（ログに%が出ない環境はプローブ併用）
MAX_SESSION_MIN="${MAX_SESSION_MIN:-45}"  # 時間ボックスで再起動
RESTART_MIN_GAP="${RESTART_MIN_GAP:-2}"   # 連続再起動の最短間隔(分)

# コンテキスト・プローブ（%が出ない環境もカバー）
PROBE_CTX_MINS="${PROBE_CTX_MINS:-10}"    # 0=無効
PROBE_TIMEOUT_SEC="${PROBE_TIMEOUT_SEC:-12}"
CTX_PROMPT='/note 現在のコンテキスト使用率を整数%のみで「CTX:<数値>%」と1行だけ出力してください。他の文やコードは出さないでください。'

# エラー検知
ERR_WINDOW_SECS="${ERR_WINDOW_SECS:-300}"
ERR_THRESHOLD="${ERR_THRESHOLD:-3}"
ERR_PAT='(400|401|403|404|429|5[0-9]{2}|ECONNRESET|ETIMEDOUT|ETIMEOUT|ENOTFOUND)'
ON_ERR_400_ACTION="${ON_ERR_400_ACTION:-skip}"
ON_ERR_401_ACTION="${ON_ERR_401_ACTION:-reset}"   # reset=安全再起動
ON_ERR_403_ACTION="${ON_ERR_403_ACTION:-skip}"
ON_ERR_404_ACTION="${ON_ERR_404_ACTION:-skip}"
ON_ERR_429_ACTION="${ON_ERR_429_ACTION:-retry}"
ON_ERR_5XX_ACTION="${ON_ERR_5XX_ACTION:-retry}"
RETRY_CMD="${RETRY_CMD:-/retry}"

# ログ
LOG_DIR="${LOG_DIR:-$HOME/cc_logs}"
PANE_LOG="${PANE_LOG:-$LOG_DIR/claude_${SESSION}_$(date +%Y%m%d).log}"
MONITOR_LOG="${MONITOR_LOG:-$LOG_DIR/monitor_${SESSION}.log}"
mkdir -p "$LOG_DIR"

# ===== ユーティリティ =====
ts(){ date '+%Y-%m-%d %H:%M:%S'; }
log(){ echo "[$(ts)] $*" | tee -a "$MONITOR_LOG"; }
now(){ date +%s; }

send(){
    tmux send-keys -t "$TARGET" "$1" C-m
    log "send: $1 -> $TARGET"
}

send_multiline(){
    local content="$1"
    # 複数行のコンテンツをtmuxに送信
    echo "$content" | while IFS= read -r line; do
        tmux send-keys -t "$TARGET" "$line" C-m
        sleep 0.1
    done
}

cap_tail(){
    tmux capture-pane -p -t "$TARGET" -S -400 2>/dev/null \
    | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' | tail -n 400
}

cap_hash(){ cap_tail | shasum | awk '{print $1}'; }

# tasks 完了（progress:100% / 全[x]）
tasks_done(){
    [[ -f "$TASKS_PATH" ]] || return 1
    local tp dp tc dc
    tp=$(grep -Ec 'progress:[[:space:]]*[0-9]+%' "$TASKS_PATH" || true)
    dp=$(grep -Ec 'progress:[[:space:]]*100%\\b' "$TASKS_PATH" || true)
    tc=$(grep -Ec '^[[:space:]]*[-*][[:space:]]*\[[ xX]\]' "$TASKS_PATH" || true)
    dc=$(grep -Ec '^[[:space:]]*[-*][[:space:]]*\[[xX]\]' "$TASKS_PATH" || true)
    (( (tp==0 || dp==tp) && (tc==0 || dc==tc) ))
}

# チェックポイント
LAST_CKPT_FILE="$LOG_DIR/${SESSION}-LAST"
save_ckpt(){
    local n="ckpt-$(date +%Y%m%d-%H%M%S)"
    echo "$n" > "$LAST_CKPT_FILE"
    send "/sc-save $n"
    log "checkpoint saved: $n"
}

load_last(){
    if [[ -f "$LAST_CKPT_FILE" ]]; then
        local ckpt=$(cat "$LAST_CKPT_FILE")
        send "/sc-load $ckpt"
        log "checkpoint loaded: $ckpt"
    else
        log "no previous checkpoint found"
    fi
}

# Claude出力ログを時刻付きで保存（ANSI除去）
setup_logging(){
    tmux pipe-pane -t "$TARGET" || true
    tmux pipe-pane -o -t "$TARGET" \
        "awk '{ cmd=\"date +[%Y-%m-%d %H:%M:%S]\"; cmd | getline d; close(cmd); gsub(/\x1b\\[[0-9;]*[a-zA-Z]/,\"\"); print d, \$0; fflush() }' >> $PANE_LOG"
    log "logging setup: $PANE_LOG"
}

# エラー/文脈
recent_errs(){ cap_tail | grep -Eoi "$ERR_PAT" | wc -l | awk '{print $1}'; }
has_code(){ local code="$1"; cap_tail | grep -Eiq "(^|[^0-9])${code}([^0-9]|$)"; }
read_ctx_from_log(){
    cap_tail | grep -Eio 'context[^0-9%]*([0-9]{1,3})%' | tail -n1 | grep -Eo '([0-9]{1,3})' || true
}

parse_ctx_from_tail(){
    cap_tail | grep -Eo 'CTX:[[:space:]]*([0-9]{1,3})%' | tail -n1 | grep -Eo '([0-9]{1,3})' || true
}

probe_ctx(){
    local start=$(now)
    send "$CTX_PROMPT"
    while (( $(now) - start < PROBE_TIMEOUT_SEC )); do
        sleep 1
        local v; v=$(parse_ctx_from_tail)
        if [[ -n "${v:-}" ]]; then echo "$v"; return 0; fi
    done
    echo ""; return 1
}

# カスタム /continue コマンド送信
send_continue(){
    if [[ -f "$CONTINUE_PROMPT_FILE" ]]; then
        log "sending custom continue prompt from: $CONTINUE_PROMPT_FILE"
        local content=$(cat "$CONTINUE_PROMPT_FILE")
        send_multiline "$content"
    else
        log "sending default /continue"
        send "/continue"
    fi
}

# 安全再起動（必ず /sc-save を先行）
safe_restart(){
    local t0=$(now)
    log "initiating safe restart..."

    # 1. 現在の状態を保存
    save_ckpt
    sleep 2

    # 2. Claude Codeを終了
    send "/exit"
    sleep 3

    # 3. tmuxペインが終了するのを待つ
    local wait_count=0
    while tmux list-panes -t "$TARGET" &>/dev/null && (( wait_count < 10 )); do
        sleep 1
        ((wait_count++))
    done

    # 4. Claude Codeを再起動
    log "restarting Claude Code..."
    tmux send-keys -t "$TARGET" "$RESTART_CMD" C-m
    sleep 5

    # 5. チェックポイントを復元
    load_last

    # 6. タイムスタンプをリセット
    SESSION_START_TS=$(now)
    LAST_RESTART_TS=$SESSION_START_TS
    LAST_HASH="$(cap_hash)"
    LAST_CHANGE=$SESSION_START_TS

    log "safe-restart completed in $(( $(now)-t0 ))s"
}

# 起動前チェック
pre_flight_check(){
    log "=== Pre-flight Check ==="

    # tmuxセッション確認
    if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
        log "ERROR: tmux session '$SESSION' not found"
        log "Please create it with: tmux new -s $SESSION -n claude"
        exit 1
    fi

    # ターゲットペイン確認
    if ! tmux list-panes -t "$TARGET" &>/dev/null; then
        log "ERROR: target pane '$TARGET' not found"
        exit 1
    fi

    # tasks.mdファイル確認
    if [[ ! -f "$TASKS_PATH" ]]; then
        log "WARNING: tasks file not found: $TASKS_PATH"
        log "Monitoring will continue but task completion detection disabled"
    fi

    # continue_promptファイル確認
    if [[ -f "$CONTINUE_PROMPT_FILE" ]]; then
        log "Custom continue prompt found: $CONTINUE_PROMPT_FILE"
    else
        log "Using default /continue command"
    fi

    log "Pre-flight check passed"
    log "=== Configuration ==="
    log "SESSION: $SESSION"
    log "TARGET: $TARGET"
    log "TASKS_PATH: $TASKS_PATH"
    log "LOG_DIR: $LOG_DIR"
    log "IDLE_SECS: $IDLE_SECS"
    log "AUTO_SAVE_MINS: $AUTO_SAVE_MINS"
    log "CONTEXT_THRESHOLD: $CONTEXT_THRESHOLD"
    log "MAX_SESSION_MIN: $MAX_SESSION_MIN"
    log "===================="
}

# シグナルハンドラー
cleanup(){
    log "=== Monitor Shutdown ==="
    log "Saving final checkpoint..."
    save_ckpt
    log "Monitor stopped. Claude Code session remains active in tmux."
    exit 0
}

trap cleanup SIGINT SIGTERM

# ===== 初期化 =====
pre_flight_check
setup_logging

log "=== Monitor Started ==="
SESSION_START_TS=$(now)
LAST_RESTART_TS=$(( $(now) - RESTART_MIN_GAP*60 ))
LAST_AUTOSAVE_TS=$(now)
LAST_CTX_PROBE_TS=$(now)
LAST_HASH="$(cap_hash)"
LAST_CHANGE=$(now)
LAST_CONTINUE_TS=0

# 既存のチェックポイントがあれば読み込む
load_last

# ===== メインループ =====
log "Entering main monitoring loop..."
while :; do
    sleep 5

    # 1) 完了 → 最終保存 & 終了
    if tasks_done; then
        log "All tasks completed! -> final /sc-save & /exit"
        save_ckpt
        send "/exit"
        sleep 2
        log "Mission accomplished! Goodbye."
        exit 0
    fi

    # 2) 定期オートセーブ
    if (( AUTO_SAVE_MINS>0 && $(now)-LAST_AUTOSAVE_TS >= AUTO_SAVE_MINS*60 )); then
        log "auto-save triggered (every ${AUTO_SAVE_MINS} mins)"
        save_ckpt
        LAST_AUTOSAVE_TS=$(now)
    fi

    # 3) エラー多発
    n=$(recent_errs)
    if (( n >= ERR_THRESHOLD )); then
        if   has_code 400; then a="$ON_ERR_400_ACTION"
        elif has_code 401; then a="$ON_ERR_401_ACTION"
        elif has_code 403; then a="$ON_ERR_403_ACTION"
        elif has_code 404; then a="$ON_ERR_404_ACTION"
        elif has_code 429; then a="$ON_ERR_429_ACTION"
        else a="$ON_ERR_5XX_ACTION"; fi

        log "errors detected: ${n} occurrences -> action=$a"

        case "$a" in
            skip)
                send "/note 自動判定: APIエラー多発。該当タスクはスキップして次へ。原因と再現手順をtasks.mdに追記"
                ;;
            retry)
                send "$RETRY_CMD"
                sleep 10
                ;;
            reset|safe-restart)
                safe_restart
                ;;
        esac
    fi

    # 4) コンテキストしきい値チェック（ログ% or プローブ）
    ctx="$(read_ctx_from_log || true)"
    if [[ -z "${ctx:-}" && $PROBE_CTX_MINS -gt 0 && $(now)-LAST_CTX_PROBE_TS -ge $PROBE_CTX_MINS*60 ]]; then
        log "probing context usage..."
        ctx="$(probe_ctx || true)"
        LAST_CTX_PROBE_TS=$(now)
        [[ -n "${ctx:-}" ]] && log "context probe result: ${ctx}%"
    fi

    if (( CONTEXT_THRESHOLD>0 )) && [[ -n "${ctx:-}" ]] && (( ctx >= CONTEXT_THRESHOLD )); then
        log "context ${ctx}% >= threshold ${CONTEXT_THRESHOLD}% -> triggering safe-restart"
        safe_restart
        continue
    fi

    # 5) 時間ボックス
    elapsed_min=$(( ( $(now) - SESSION_START_TS ) / 60 ))
    since_restart_min=$(( ( $(now) - LAST_RESTART_TS ) / 60 ))
    if (( elapsed_min >= MAX_SESSION_MIN && since_restart_min >= RESTART_MIN_GAP )); then
        log "time-box reached: ${elapsed_min}min >= ${MAX_SESSION_MIN}min -> safe-restart"
        safe_restart
        continue
    fi

    # 6) アイドル検知 → /continue
    H="$(cap_hash)"
    if [[ "$H" != "$LAST_HASH" ]]; then
        LAST_HASH="$H"
        LAST_CHANGE=$(now)
        continue
    fi

    idle_time=$(( $(now) - LAST_CHANGE ))
    if (( idle_time >= IDLE_SECS )); then
        # クールダウンチェック
        if (( $(now) - LAST_CONTINUE_TS >= COOLDOWN_SECS )); then
            log "idle detected: ${idle_time}s >= ${IDLE_SECS}s -> sending continue"
            send_continue
            LAST_CONTINUE_TS=$(now)
            LAST_CHANGE=$(now)
            sleep "$COOLDOWN_SECS"
        fi
    fi
done