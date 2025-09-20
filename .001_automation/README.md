# Claude Code 自動化システム - コピペ実行ガイド

## 🚀 1分で開始（コピペ実行）

### ステップ1: セットアップ（コピペ実行）
```bash
# ディレクトリ移動
cd /Users/furuyanaoki/Project/new.mail.score/.001_automation

# 実行権限付与
chmod +x setup.sh monitor_refresh.sh

# セットアップ実行
./setup.sh
```

### ステップ2: Claude Code起動（コピペ実行）
```bash
# tmuxセッション作成
tmux new -s cc -n claude

# Claude Code起動（tmuxセッション内で実行）
claude --dangerously-skip-permissions
```

### ステップ3: 監視開始（新しいターミナルでコピペ実行）
```bash
# 監視開始
~/cc_automation/run_monitor.sh
```

#### 初回のみ: 設定ファイルが存在しない場合
```bash
# 初回のみ実行（設定ファイル作成）
cat > ~/cc_automation/config.env << 'EOF'
SESSION="cc"
TARGET="${SESSION}:0.0"
START_CMD="claude --dangerously-skip-permissions"
LOG_DIR="/Users/furuyanaoki/cc_logs"
TASKS_PATH="/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md"
IDLE_SECS=600
AUTO_SAVE_MINS=15
CONTEXT_THRESHOLD=70
EOF

# 監視開始
~/cc_automation/run_monitor.sh
```

### ステップ4: 停止（コピペ実行）
```bash
# 監視停止（監視ターミナルで）
Ctrl+C

# Claude Code終了（Claude Codeターミナルで）
/exit
```

---

## 📋 詳細設定・機能説明

### 🎯 システム概要

Claude Codeを常駐させつつ、自動的に安定リフレッシュして品質を維持する監視システムです。

**主要機能**:
- 自動セッション管理（コンテキスト肥大・エラー・タイムアウト対応）
- 継続的監視（アイドル検知と自動継続実行）
- 品質保証（定期チェックポイント保存・復元）
- エラーハンドリング（APIエラー自動検知・対応）
- 完了検知（tasks.md進捗監視・自動終了）

### 📋 必要条件

- **tmux**: セッション管理
- **Claude Code**: `claude --dangerously-skip-permissions`
- **bash**: 4.0以上推奨
- **標準ツール**: awk, grep, shasum

### tmuxインストール（必要に応じてコピペ実行）
```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# CentOS/RHEL
sudo yum install tmux
```

### カスタム設定（必要に応じてコピペ実行）
```bash
# カスタムディレクトリでセットアップ
./setup.sh -d ~/my-automation -l ~/my-logs -s my-session

# プロジェクト固有設定で監視開始
TASKS_PATH="$PWD/specs/*/tasks.md" ~/cc_automation/run_monitor.sh
```

## 🔧 ログ確認（コピペ実行）

### リアルタイム監視
```bash
# 監視ログの確認
tail -f ~/cc_logs/monitor_cc.log

# Claude Codeの出力確認
tail -f ~/cc_logs/claude_cc_$(date +%Y%m%d).log
```

### 状態確認
```bash
# tmuxセッション確認
tmux list-sessions

# チェックポイント確認
cat ~/cc_logs/cc-LAST

# プロセス確認
ps aux | grep monitor_refresh
```

## 🚨 トラブル対応（コピペ実行）

### エラー: "target pane not found"
```bash
# 設定ファイルを正しく再作成
cat > ~/cc_automation/config.env << 'EOF'
SESSION="cc"
TARGET="${SESSION}:0.0"
START_CMD="claude --dangerously-skip-permissions"
LOG_DIR="/Users/furuyanaoki/cc_logs"
TASKS_PATH="/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md"
IDLE_SECS=600
AUTO_SAVE_MINS=15
CONTEXT_THRESHOLD=70
EOF

# 監視再開
~/cc_automation/run_monitor.sh
```

### エラー: "tasks file not found"
```bash
# ファイル確認
ls -la /Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md

# パス修正
export TASKS_PATH="/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md"
~/cc_automation/run_monitor.sh
```

### 監視再起動
```bash
# 監視停止
killall monitor_refresh.sh

# 監視再開
~/cc_automation/run_monitor.sh
```

## ⚙️ カスタム設定（コピペ実行）

### プロジェクト固有設定（完全版）
```bash
# 設定ファイル作成（このプロジェクト用最適化）
cat > ~/cc_automation/config.env << 'EOF'
# Claude Code 自動化システム設定ファイル
SESSION="cc"
TARGET="${SESSION}:0.0"
START_CMD="claude --dangerously-skip-permissions"
LOG_DIR="/Users/furuyanaoki/cc_logs"
TASKS_PATH="/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md"

# 監視パラメータ
IDLE_SECS=600
COOLDOWN_SECS=45
AUTO_SAVE_MINS=15
CONTEXT_THRESHOLD=70
MAX_SESSION_MIN=45
RESTART_MIN_GAP=2

# コンテキストプローブ
PROBE_CTX_MINS=10
PROBE_TIMEOUT_SEC=12

# エラーハンドリング
ERR_WINDOW_SECS=300
ERR_THRESHOLD=3
ON_ERR_400_ACTION="skip"
ON_ERR_401_ACTION="reset"
ON_ERR_403_ACTION="skip"
ON_ERR_404_ACTION="skip"
ON_ERR_429_ACTION="retry"
ON_ERR_5XX_ACTION="retry"
RETRY_CMD="/retry"
EOF

# 設定反映で監視開始
~/cc_automation/run_monitor.sh
```

### 別プロジェクト用セットアップ
```bash
# カスタムディレクトリセットアップ
./setup.sh -s my-project -d ~/my-project-automation -l ~/my-project-logs

# 専用設定で監視
SESSION="my-project" TASKS_PATH="$PWD/my-tasks.md" ~/my-project-automation/run_monitor.sh
```

## 🔄 手動操作（コピペ実行）

### チェックポイント操作
```bash
# 手動保存
tmux send-keys -t cc:0.0 "/sc-save manual-$(date +%Y%m%d-%H%M%S)" C-m

# 最新復元
tmux send-keys -t cc:0.0 "/sc-load $(cat ~/cc_logs/cc-LAST)" C-m

# 特定チェックポイントから復元
tmux send-keys -t cc:0.0 "/sc-load ckpt-20250920-154500" C-m
```

### デバッグ実行
```bash
# デバッグモードで監視開始
DEBUG=1 ~/cc_automation/run_monitor.sh
```

---

## 📋 システム詳細

**主要機能**:
- 自動セッション管理（コンテキスト肥大・エラー・タイムアウト対応）
- 継続的監視（アイドル検知と自動継続実行）
- 品質保証（定期チェックポイント保存・復元）
- エラーハンドリング（APIエラー自動検知・対応）
- 完了検知（tasks.md進捗監視・自動終了）

**ファイル構成**:
```
~/cc_automation/          # セットアップ後の実行ディレクトリ
├── monitor_refresh.sh     # メイン監視スクリプト
├── run_monitor.sh         # 実行用ラッパー
├── start_claude.sh        # Claude Code起動ヘルパー
├── continue_prompt.txt    # カスタム継続プロンプト
└── config.env             # 設定ファイル

~/cc_logs/                 # ログディレクトリ
├── claude_cc_YYYYMMDD.log # Claude Code出力ログ
├── monitor_cc.log         # 監視動作ログ
└── cc-LAST                # 最新チェックポイント名
```

**自動動作**:
- **アイドル検知**: 600秒無出力で自動継続プロンプト送信
- **定期保存**: 15分毎にチェックポイント保存
- **コンテキスト監視**: 70%超過で自動再起動（/sc-save → /exit → 復元）
- **エラーハンドリング**: APIエラー自動検知・適切な対応
- **完了検知**: tasks.md分析で自動終了（134タスク監視対応）
- **TodoWrite促進**: 30分毎の軽いリマインダー送信

---

**更新**: 2025-09-20 | **バージョン**: 1.0.0