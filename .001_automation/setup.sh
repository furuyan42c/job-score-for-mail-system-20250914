#!/usr/bin/env bash
set -euo pipefail

# Claude Code 自動化システム セットアップスクリプト
# Usage: ./setup.sh [OPTIONS]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_INSTALL_DIR="$HOME/cc_automation"
DEFAULT_LOG_DIR="$HOME/cc_logs"
DEFAULT_SESSION="cc"

show_help() {
    cat << 'EOF'
Claude Code 自動化システム セットアップ

USAGE:
    ./setup.sh [OPTIONS]

OPTIONS:
    -d, --install-dir DIR    インストールディレクトリ (default: ~/cc_automation)
    -l, --log-dir DIR        ログディレクトリ (default: ~/cc_logs)
    -s, --session NAME       tmuxセッション名 (default: cc)
    -h, --help               このヘルプを表示

EXAMPLES:
    # デフォルト設定でセットアップ
    ./setup.sh

    # カスタムディレクトリでセットアップ
    ./setup.sh -d /opt/claude-automation -l /var/log/claude

    # 本プロジェクト用設定
    ./setup.sh -s mail-score -d ~/mail-score-automation
EOF
}

# パラメータ解析
INSTALL_DIR="$DEFAULT_INSTALL_DIR"
LOG_DIR="$DEFAULT_LOG_DIR"
SESSION="$DEFAULT_SESSION"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -l|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -s|--session)
            SESSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_help >&2
            exit 1
            ;;
    esac
done

echo "=== Claude Code 自動化システム セットアップ ==="
echo "インストールディレクトリ: $INSTALL_DIR"
echo "ログディレクトリ: $LOG_DIR"
echo "tmuxセッション名: $SESSION"
echo

# 前提条件チェック
check_prerequisites() {
    echo "前提条件をチェック中..."

    # tmux チェック
    if ! command -v tmux &> /dev/null; then
        echo "ERROR: tmux が見つかりません"
        echo "インストール方法:"
        echo "  macOS: brew install tmux"
        echo "  Ubuntu: sudo apt install tmux"
        echo "  CentOS: sudo yum install tmux"
        exit 1
    fi

    # shasum チェック
    if ! command -v shasum &> /dev/null; then
        echo "ERROR: shasum が見つかりません"
        exit 1
    fi

    # awk チェック
    if ! command -v awk &> /dev/null; then
        echo "ERROR: awk が見つかりません"
        exit 1
    fi

    echo "✓ 前提条件チェック完了"
}

# ディレクトリ作成
setup_directories() {
    echo "ディレクトリを作成中..."

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"

    echo "✓ ディレクトリ作成完了"
    echo "  - インストール: $INSTALL_DIR"
    echo "  - ログ: $LOG_DIR"
}

# ファイルコピー
install_files() {
    echo "ファイルをインストール中..."

    # メインスクリプト
    cp "$SCRIPT_DIR/monitor_refresh.sh" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/monitor_refresh.sh"

    # 設定ファイル
    if [[ -f "$SCRIPT_DIR/continue_prompt.txt" ]]; then
        cp "$SCRIPT_DIR/continue_prompt.txt" "$INSTALL_DIR/"
    fi

    # 設定例ファイル
    if [[ -f "$SCRIPT_DIR/config.env.example" ]]; then
        cp "$SCRIPT_DIR/config.env.example" "$INSTALL_DIR/"
    fi

    echo "✓ ファイルインストール完了"
}

# 実行スクリプト作成
create_runner_script() {
    echo "実行スクリプトを作成中..."

    cat > "$INSTALL_DIR/run_monitor.sh" << EOF
#!/usr/bin/env bash
# Claude Code 監視スクリプト実行用

# 設定ファイルがあれば読み込み
if [[ -f "\$(dirname "\$0")/config.env" ]]; then
    source "\$(dirname "\$0")/config.env"
fi

# デフォルト設定
export SESSION="\${SESSION:-$SESSION}"
export TARGET="\${TARGET:-\${SESSION}:1.0}"
export START_CMD="\${START_CMD:-codex /run agent}"
export LOG_DIR="\${LOG_DIR:-$LOG_DIR}"
export TASKS_PATH="\${TASKS_PATH:-\$HOME/work/tasks.md}"

# 監視スクリプト実行
exec "\$(dirname "\$0")/monitor_refresh.sh" "\$@"
EOF

    chmod +x "$INSTALL_DIR/run_monitor.sh"

    echo "✓ 実行スクリプト作成完了: $INSTALL_DIR/run_monitor.sh"
}

# tmuxセッション作成ヘルパー
create_tmux_helper() {
    echo "tmuxヘルパースクリプトを作成中..."

    cat > "$INSTALL_DIR/start_claude.sh" << EOF
#!/usr/bin/env bash
# Claude Code tmuxセッション作成・起動ヘルパー

SESSION_NAME="\${1:-$SESSION}"
START_CMD="\${2:-codex /run agent}"

echo "=== Claude Code セッション起動 ==="
echo "セッション名: \$SESSION_NAME"
echo "起動コマンド: \$START_CMD"

# 既存セッションがあるかチェック
if tmux has-session -t "\$SESSION_NAME" 2>/dev/null; then
    echo "既存セッション '\$SESSION_NAME' が見つかりました"
    echo "アタッチしますか？ [y/N]"
    read -r response
    if [[ "\$response" =~ ^[Yy] ]]; then
        tmux attach-session -t "\$SESSION_NAME"
        exit 0
    else
        echo "新しいウィンドウを作成します"
        tmux new-window -t "\$SESSION_NAME" -n claude
        tmux send-keys -t "\$SESSION_NAME:claude" "\$START_CMD" C-m
        echo "ウィンドウ '\$SESSION_NAME:claude' でClaude Codeを起動しました"
        exit 0
    fi
fi

# 新規セッション作成
echo "新しいtmuxセッション '\$SESSION_NAME' を作成中..."
tmux new-session -d -s "\$SESSION_NAME" -n claude
tmux send-keys -t "\$SESSION_NAME:claude" "\$START_CMD" C-m

echo "✓ セッション作成完了"
echo "アタッチするには: tmux attach-session -t \$SESSION_NAME"
echo "監視を開始するには: $INSTALL_DIR/run_monitor.sh"
EOF

    chmod +x "$INSTALL_DIR/start_claude.sh"

    echo "✓ tmuxヘルパー作成完了: $INSTALL_DIR/start_claude.sh"
}

# 設定ファイル作成
create_config() {
    echo "設定ファイルを作成中..."

    cat > "$INSTALL_DIR/config.env" << EOF
# Claude Code 自動化システム設定ファイル
# このファイルを編集して設定をカスタマイズしてください

# === 基本設定 ===
SESSION="$SESSION"
TARGET="\${SESSION}:1.0"
START_CMD="codex /run agent"
LOG_DIR="$LOG_DIR"
TASKS_PATH="\$HOME/work/tasks.md"

# === 監視パラメータ ===
IDLE_SECS=600              # アイドル検知時間（秒）
COOLDOWN_SECS=45           # /continue後のクールダウン（秒）
AUTO_SAVE_MINS=15          # 自動保存間隔（分、0で無効）
CONTEXT_THRESHOLD=70       # コンテキスト閾値（%、0で無効）
MAX_SESSION_MIN=45         # セッション最大時間（分）
RESTART_MIN_GAP=2          # 再起動最小間隔（分）

# === コンテキストプローブ ===
PROBE_CTX_MINS=10          # プローブ間隔（分、0で無効）
PROBE_TIMEOUT_SEC=12       # プローブタイムアウト（秒）

# === エラーハンドリング ===
ERR_WINDOW_SECS=300        # エラー検知ウィンドウ（秒）
ERR_THRESHOLD=3            # エラー閾値（回数）
ON_ERR_400_ACTION="skip"   # 400エラー時の動作
ON_ERR_401_ACTION="reset"  # 401エラー時の動作
ON_ERR_403_ACTION="skip"   # 403エラー時の動作
ON_ERR_404_ACTION="skip"   # 404エラー時の動作
ON_ERR_429_ACTION="retry"  # 429エラー時の動作
ON_ERR_5XX_ACTION="retry"  # 5xxエラー時の動作
RETRY_CMD="/retry"         # リトライコマンド
EOF

    echo "✓ 設定ファイル作成完了: $INSTALL_DIR/config.env"
}

# 使用方法の表示
show_usage() {
    echo
    echo "=== セットアップ完了 ==="
    echo
    echo "次の手順で使用してください:"
    echo
    echo "1. Claude Code起動:"
    echo "   $INSTALL_DIR/start_claude.sh"
    echo
    echo "2. 監視開始（別ターミナルで）:"
    echo "   $INSTALL_DIR/run_monitor.sh"
    echo
    echo "設定ファイル: $INSTALL_DIR/config.env"
    echo "ログディレクトリ: $LOG_DIR"
    echo
    echo "手動でtmuxセッションを作成する場合:"
    echo "   tmux new -s $SESSION -n claude"
    echo "   # セッション内で: codex /run agent"
    echo
    echo "監視の詳細な使用方法は README.md を参照してください"
}

# メイン実行
main() {
    check_prerequisites
    setup_directories
    install_files
    create_runner_script
    create_tmux_helper
    create_config
    show_usage
}

main "$@"