# Claude Code 自動化システム

Claude Codeを常駐させつつ、自動的に安定リフレッシュして品質を維持する監視システムです。

## 🎯 概要

このシステムは以下の機能を提供します：

- **自動セッション管理**: コンテキスト肥大、エラー、タイムアウト時の自動再起動
- **継続的監視**: アイドル状態の検知と自動継続実行
- **品質保証**: 定期的なチェックポイント保存と復元
- **エラーハンドリング**: APIエラーの自動検知と適切な対応
- **完了検知**: tasks.md の進捗監視と自動終了

## 📋 必要条件

- **tmux**: セッション管理
- **Claude Code**: codex コマンド
- **bash**: 4.0以上推奨
- **標準ツール**: awk, grep, shasum

### インストール

```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# CentOS/RHEL
sudo yum install tmux
```

## 🚀 クイックスタート

### 1. セットアップ

```bash
# セットアップスクリプトを実行
chmod +x setup.sh
./setup.sh

# カスタム設定でセットアップ
./setup.sh -d ~/my-automation -l ~/my-logs -s my-session
```

### 2. Claude Code 起動

```bash
# 自動起動（推奨）
~/cc_automation/start_claude.sh

# または手動起動
tmux new -s cc -n claude
# セッション内で
codex /run agent
```

### 3. 監視開始

```bash
# 別ターミナルで監視開始
~/cc_automation/run_monitor.sh

# または環境変数で設定を上書き
TASKS_PATH="$PWD/specs/*/tasks.md" ~/cc_automation/run_monitor.sh
```

### 4. 停止

```bash
# 監視のみ停止（Claude Codeは継続）
Ctrl+C

# Claude Code も終了
# Claude Code 内で /exit
```

## 📁 ファイル構成

セットアップ後のディレクトリ構造：

```
~/cc_automation/
├── monitor_refresh.sh      # メイン監視スクリプト
├── run_monitor.sh          # 実行用ラッパー
├── start_claude.sh         # Claude Code起動ヘルパー
├── continue_prompt.txt     # カスタム continue プロンプト
├── config.env              # 設定ファイル
└── config.env.example      # 設定例

~/cc_logs/
├── claude_cc_YYYYMMDD.log  # Claude Code出力ログ
├── monitor_cc.log          # 監視動作ログ
└── cc-LAST                 # 最新チェックポイント名
```

## ⚙️ 設定

### 主要パラメータ

`config.env` で設定をカスタマイズできます：

```bash
# === 基本設定 ===
SESSION="cc"                    # tmuxセッション名
TARGET="${SESSION}:1.0"         # 監視対象ペイン
START_CMD="codex /run agent"    # 起動コマンド
TASKS_PATH="$HOME/work/tasks.md" # タスクファイルパス

# === 監視動作 ===
IDLE_SECS=600                   # アイドル検知時間（秒）
COOLDOWN_SECS=45                # continue後のクールダウン
AUTO_SAVE_MINS=15               # 自動保存間隔（分）
CONTEXT_THRESHOLD=70            # コンテキスト閾値（%）
MAX_SESSION_MIN=45              # セッション最大時間（分）

# === エラーハンドリング ===
ERR_THRESHOLD=3                 # エラー閾値
ON_ERR_400_ACTION="skip"        # 400エラー時の動作
ON_ERR_401_ACTION="reset"       # 401エラー時の動作
ON_ERR_429_ACTION="retry"       # 429エラー時の動作
```

### 環境変数での上書き

```bash
# 一時的な設定変更
TARGET="mail-score:1.0" TASKS_PATH="$PWD/tasks.md" ~/cc_automation/run_monitor.sh

# プロジェクト固有の設定
export SESSION="mail-score"
export TASKS_PATH="$PWD/specs/002-think-hard-ultrathink/tasks.md"
~/cc_automation/run_monitor.sh
```

## 🔄 自動動作

### アイドル検知

出力変化がない状態が `IDLE_SECS`（デフォルト600秒）続くと、自動的に continue プロンプトを送信します。

```bash
# デフォルトの /continue の代わりに
# continue_prompt.txt の内容を送信
```

### 定期保存

`AUTO_SAVE_MINS`（デフォルト15分）ごとに `/sc-save ckpt-YYYYMMDD-HHMMSS` を実行します。

### コンテキスト監視

- ログから `context N%` を自動検知
- `CONTEXT_THRESHOLD`（デフォルト70%）を超えると自動再起動
- ログに%が出ない環境では定期的にプローブを送信

### 時間ボックス

`MAX_SESSION_MIN`（デフォルト45分）経過すると自動再起動します。

### エラー対応

5分間で3回以上のエラーを検知すると：

- **400/403/404**: タスクをスキップ
- **401**: 安全再起動
- **429/5xx**: リトライ

### 完了検知

`tasks.md` ファイルを監視し：

- `progress: 100%` または
- 全チェックボックスが `[x]` 状態

になると自動的に `/sc-save` → `/exit` して終了します。

## 🔧 カスタマイズ

### カスタム continue プロンプト

`continue_prompt.txt` を編集して、アイドル時に送信するコマンドをカスタマイズできます：

```bash
# デフォルトの自律実行プロンプトを
# プロジェクト固有の指示に変更
cat > ~/cc_automation/continue_prompt.txt << 'EOF'
/sc:load
次のタスクを実行してください: T076-T080
--think-hard --parallel
EOF
```

### セッション毎の設定

```bash
# プロジェクト固有のセットアップ
./setup.sh -s mail-score -d ~/mail-score-automation

# 専用設定ファイル
cat > ~/mail-score-automation/config.env << 'EOF'
SESSION="mail-score"
TASKS_PATH="$HOME/Project/new.mail.score/specs/*/tasks.md"
CONTEXT_THRESHOLD=75
AUTO_SAVE_MINS=10
EOF
```

## 📊 監視とログ

### ログファイル

```bash
# Claude Code の出力（時刻付き、ANSI除去済み）
tail -f ~/cc_logs/claude_cc_YYYYMMDD.log

# 監視システムの動作ログ
tail -f ~/cc_logs/monitor_cc.log

# リアルタイム監視
watch -n 5 'tail -10 ~/cc_logs/monitor_cc.log'
```

### 状態確認

```bash
# tmuxセッション確認
tmux list-sessions
tmux list-panes -t cc:1.0

# 現在のチェックポイント
cat ~/cc_logs/cc-LAST

# プロセス確認
ps aux | grep monitor_refresh
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. "target pane not found"

```bash
# セッション・ペインの確認
tmux list-sessions
tmux list-panes -a

# 正しいターゲットを指定
export TARGET="correct-session:1.0"
```

#### 2. "tasks file not found"

```bash
# ファイルパスの確認
ls -la "$TASKS_PATH"

# 正しいパスを指定
export TASKS_PATH="/full/path/to/tasks.md"
```

#### 3. continue プロンプトが効かない

```bash
# プロンプトファイルの確認
cat ~/cc_automation/continue_prompt.txt

# 手動テスト
tmux send-keys -t cc:1.0 "$(cat ~/cc_automation/continue_prompt.txt)" C-m
```

#### 4. 自動再起動しない

```bash
# ログで原因確認
grep "safe-restart\|context\|timebox" ~/cc_logs/monitor_cc.log

# 設定値確認
grep -E "(CONTEXT_THRESHOLD|MAX_SESSION)" ~/cc_automation/config.env
```

### デバッグモード

```bash
# 詳細ログ出力
DEBUG=1 ~/cc_automation/run_monitor.sh

# 手動でプローブ実行
echo '/note 現在のコンテキスト使用率を整数%のみで「CTX:<数値>%」と1行だけ出力してください。' | \
  tmux send-keys -t cc:1.0
```

## 🔄 手動操作

### チェックポイント操作

```bash
# 手動保存
tmux send-keys -t cc:1.0 "/sc-save manual-$(date +%Y%m%d-%H%M%S)" C-m

# 特定ポイントから復元
tmux send-keys -t cc:1.0 "/sc-load ckpt-20241001-143000" C-m

# 最新から復元
tmux send-keys -t cc:1.0 "/sc-load $(cat ~/cc_logs/cc-LAST)" C-m
```

### 監視制御

```bash
# 一時停止（監視プロセスにSIGTERM）
killall -TERM monitor_refresh.sh

# 強制終了
killall -KILL monitor_refresh.sh

# 再開
~/cc_automation/run_monitor.sh
```

## 📈 ベストプラクティス

### 運用指針

1. **事前準備**
   - tasks.md の存在確認
   - tmuxセッションの事前作成
   - 設定ファイルのカスタマイズ

2. **監視開始前**
   - Claude Code の正常起動確認
   - 初期チェックポイントの作成
   - ログディレクトリの容量確認

3. **長期実行時**
   - 定期的なログファイルのローテーション
   - ディスク容量の監視
   - チェックポイントファイルの管理

4. **トラブル対応**
   - ログファイルでの原因調査
   - 手動でのチェックポイント復元
   - 設定値の調整

### 推奨設定

```bash
# 開発環境（短時間作業）
AUTO_SAVE_MINS=5
MAX_SESSION_MIN=30
CONTEXT_THRESHOLD=80

# 本番環境（長時間作業）
AUTO_SAVE_MINS=15
MAX_SESSION_MIN=45
CONTEXT_THRESHOLD=70

# 高負荷環境（大量タスク）
IDLE_SECS=300
ERR_THRESHOLD=5
CONTEXT_THRESHOLD=60
```

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

バグ報告や機能提案は Issue でお知らせください。
プルリクエストも歓迎します。

---

**作成者**: Claude Code 自動化プロジェクト
**更新日**: 2024年9月
**バージョン**: 1.0.0