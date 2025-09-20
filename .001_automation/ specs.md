仕様書（常駐＋自動リフレッシュ、/exitベース、リフレッシュ前に必ず/sc-save）
1) ゴール
Claude Code を 常駐させつつ、自動的に安定リフレッシュして品質を維持する。
停止やエラー、文脈肥大に 自律対応。
再起動前は必ず /sc-save → 再起動後に /sc-load LAST で即時復元。

2) 構成
ターミナルA（本体）: tmux cc:1.0 に Claude Code を起動（例：codex /run agent）。
ターミナルB（監視）: 下のスクリプトを常駐実行し、TARGET=cc:1.0 へコマンド注入。
3) 管理ファイル / ログ

進捗: tasks.md（progress: 100% / - [x]）
ログ: ~/cc_logs/
Claude出力 → claude_<SESSION>_YYYYMMDD.log（tmux pipe-pane、時刻付き・ANSI除去）
監視行動 → monitor_<SESSION>.log
直近チェックポイント名 → <SESSION>-LAST（中に ckpt-YYYYMMDD-hhmmss）

4) 自動動作（常駐＋自動リフレッシュ）

アイドル検知: 出力変化なし IDLE_SECS(推奨600) → /continue（COOLDOWN_SECSで連打抑制）
定期セーブ: AUTO_SAVE_MINS(推奨15)ごとに /sc-save ckpt-...
コンテキスト肥大:
ログに%が出るなら context ≥ CONTEXT_THRESHOLD(推奨70) で判定
%が出ない環境は プローブ（監視が /note で CTX:<n>% を1行で報告させる）
どちらも超過時は必ず /sc-save → /exit → 再起動 → /sc-load LAST
時間ボックス: MAX_SESSION_MIN(推奨45) 経過で 必ず /sc-save → /exit 再起動 → /sc-load
エラー多発（ERR_WINDOW_SECS=300 中 ERR_THRESHOLD=3 回以上）:
400/403/404 → skip（/noteで原因と再現手順を tasks.md に残す）
401 → 安全再起動（= /sc-save → /exit → 再起動 → /sc-load）
429/5xx/ネットワーク → retry（/retry＋クールダウン）
safe-restart 指定時は 安全再起動
完了: tasks.md 全完 → 最終 /sc-save → /exit → 監視終了

5) 受入基準（要点）

すべての再起動前に /sc-save が実行される（ログに痕跡）。
再起動後に 直前の LAST を /sc-load して即復元。
アイドル・エラー・コンテキスト・時間ボックスの各条件で自動行動。
monitor_*.log に判定理由と送信コマンドが全て残る。
tasks.md 全完で自動終了。

6) 主要パラメータ（既定値）

IDLE_SECS=600, COOLDOWN_SECS=45
AUTO_SAVE_MINS=15
CONTEXT_THRESHOLD=70（0で無効）
PROBE_CTX_MINS=10, PROBE_TIMEOUT_SEC=12
MAX_SESSION_MIN=45, RESTART_MIN_GAP=2
ERR_WINDOW_SECS=300, ERR_THRESHOLD=3
エラー動作: ON_ERR_400=skip, ON_ERR_401=reset(=再起動), ON_ERR_403=skip, ON_ERR_404=skip, ON_ERR_429=retry, ON_ERR_5XX=retry

実行手順（Runbook）

ターミナルA（本体）

tmux new -s cc -n claude
codex /run agent   # ←あなたの起動コマンド


ターミナルB（監視）

# 下のスクリプトを保存して実行権限付与
chmod +x ~/cc_automation/monitor_refresh.sh

# 監視起動（必要に応じてSTART_CMD/TASKS_PATH等を上書き）
TARGET="cc:1.0" START_CMD='codex /run agent' TASKS_PATH="$HOME/work/tasks.md" \
~/cc_automation/monitor_refresh.sh


停止: ターミナルBで Ctrl+C（本体は継続）
完全終了: tasks.md 全完で自動 /exit、またはターミナルAで手動 /exit

完成スクリプト（リフレッシュ前に必ず /sc-save を実行）

~/cc_automation/monitor_refresh.sh

#!/usr/bin/env bash
set -euo pipefail

# ===== 基本設定（環境変数で上書き可）=====
SESSION="${SESSION:-cc}"
TARGET="${TARGET:-cc:1.0}"                # Claude Code の tmux pane
START_CMD="${START_CMD:-codex /run agent}"# 初回起動
RESTART_CMD="${RESTART_CMD:-$START_CMD}"   # 再起動コマンド
TASKS_PATH="${TASKS_PATH:-$HOME/work/tasks.md}"

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
log(){ echo "[$(ts)] $*" | tee -a "$MONITOR_LOG" >/dev/null; }
now(){ date +%s; }

send(){ tmux send-keys -t "$TARGET" "$1" C-m; log "send: $1 -> $TARGET"; }

cap_tail(){ tmux capture-pane -p -t "$TARGET" -S -400 2>/dev/null \
  | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' | tail -n 400; }
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
save_ckpt(){ local n="ckpt-$(date +%Y%m%d-%H%M%S)"; echo "$n" > "$LAST_CKPT_FILE"; send "/sc-save $n"; }
load_last(){ [[ -f "$LAST_CKPT_FILE" ]] && send "/sc-load $(cat "$LAST_CKPT_FILE")"; }

# Claude出力ログを時刻付きで保存（ANSI除去）
tmux pipe-pane -t "$TARGET" || true
tmux pipe-pane -o -t "$TARGET" \
  "awk '{ cmd=\"date +[%Y-%m-%d %H:%M:%S]\"; cmd | getline d; close(cmd); gsub(/\x1b\\[[0-9;]*[a-zA-Z]/,\"\"); print d, \$0; fflush() }' >> $PANE_LOG"

# エラー/文脈
recent_errs(){ cap_tail | grep -Eoi "$ERR_PAT" | wc -l | awk '{print $1}'; }
has_code(){ local code="$1"; cap_tail | grep -Eiq "(^|[^0-9])${code}([^0-9]|$)"; }
read_ctx_from_log(){ cap_tail | grep -Eio 'context[^0-9%]*([0-9]{1,3})%' | tail -n1 | grep -Eo '([0-9]{1,3})' || true; }

parse_ctx_from_tail(){ cap_tail | grep -Eo 'CTX:[[:space:]]*([0-9]{1,3})%' | tail -n1 | grep -Eo '([0-9]{1,3})' || true; }
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

# 安全再起動（必ず /sc-save を先行）
safe_restart(){
  local t0=$(now)
  save_ckpt
  send "/exit"
  sleep 2
  tmux send-keys -t "$TARGET" "$RESTART_CMD" C-m
  sleep 2
  load_last
  SESSION_START_TS=$(now)
  LAST_RESTART_TS=$SESSION_START_TS
  LAST_HASH="$(cap_hash)"
  LAST_CHANGE=$SESSION_START_TS
  log "safe-restart done in $(( $(now)-t0 ))s"
}

# ===== 初期化 =====
log "monitor start target=$TARGET tasks=$TASKS_PATH"
SESSION_START_TS=$(now)
LAST_RESTART_TS=$(( $(now) - RESTART_MIN_GAP*60 ))
LAST_AUTOSAVE_TS=$(now)
LAST_CTX_PROBE_TS=$(now)
LAST_HASH="$(cap_hash)"
LAST_CHANGE=$(now)

# ===== メインループ =====
while :; do
  sleep 5

  # 1) 完了 → 最終保存 & 終了
  if tasks_done; then
    log "tasks done -> final /sc-save & /exit"
    save_ckpt
    send "/exit"
    sleep 2
    log "bye"
    exit 0
  fi

  # 2) 定期オートセーブ
  if (( AUTO_SAVE_MINS>0 && $(now)-LAST_AUTOSAVE_TS >= AUTO_SAVE_MINS*60 )); then
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
    log "errors: ${n} hits -> action=$a"
    case "$a" in
      skip)  send "/note 自動判定: APIエラー多発。該当タスクはスキップして次へ。原因と再現手順をtasks.mdに追記";;
      retry) send "$RETRY_CMD"; sleep 10;;
      reset|safe-restart) safe_restart;;
    esac
  fi

  # 4) コンテキストしきい（ログ% or プローブ）
  ctx="$(read_ctx_from_log || true)"
  if [[ -z "${ctx:-}" && $PROBE_CTX_MINS -gt 0 && $(now)-LAST_CTX_PROBE_TS -ge $PROBE_CTX_MINS*60 ]]; then
    ctx="$(probe_ctx || true)"
    LAST_CTX_PROBE_TS=$(now)
    [[ -n "${ctx:-}" ]] && log "ctx-probe: ${ctx}%"
  fi
  if (( CONTEXT_THRESHOLD>0 )) && [[ -n "${ctx:-}" ]] && (( ctx >= CONTEXT_THRESHOLD )); then
    log "context ${ctx}% >= ${CONTEXT_THRESHOLD}% -> safe-restart"
    safe_restart
    continue
  fi

  # 5) 時間ボックス
  elapsed_min=$(( ( $(now) - SESSION_START_TS ) / 60 ))
  since_restart_min=$(( ( $(now) - LAST_RESTART_TS ) / 60 ))
  if (( elapsed_min >= MAX_SESSION_MIN && since_restart_min >= RESTART_MIN_GAP )); then
    log "timebox ${elapsed_min}min -> safe-restart"
    safe_restart
    continue
  fi

  # 6) アイドル検知 → /continue
  H="$(cap_hash)"
  if [[ "$H" != "$LAST_HASH" ]]; then
    LAST_HASH="$H"; LAST_CHANGE=$(now); continue
  fi
  if (( $(now)-LAST_CHANGE >= IDLE_SECS )); then
    log "idle ${IDLE_SECS}s -> /continue"
    send "/continue"
    sleep "$COOLDOWN_SECS"
  fi
done

補足（確認ポイント）

リフレッシュ系の全ルート（コンテキスト超 / 時間ボックス / 401やsafe-restart指定のエラー）はすべて safe_restart() を通り、先頭で /sc-save を確実に実施します。

完了処理（tasks.md 全完）でも最後に /sc-save を実行してから /exit します。

%が出ない環境**でも**PROBE_CTX_MINSにより**監視側が数分おきに% を取得**します（CTX:<n>%`）。