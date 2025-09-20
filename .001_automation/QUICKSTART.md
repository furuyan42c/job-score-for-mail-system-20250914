# 🚀 Claude Code 自動化システム - クイックスタート

## 📋 現在の状況に応じた実行方法

### あなたの現在のペイン番号を確認（コピペ実行）
```bash
tmux list-panes -t cc -a
```

**結果が `cc:0.0` の場合** ← **これが一般的**
```bash
# 監視開始
~/cc_automation/run_monitor.sh
```

**結果が `cc:1.0` の場合**
```bash
# TARGET指定で監視開始
TARGET="cc:1.0" ~/cc_automation/run_monitor.sh
```

## 🔧 完全な手順（最初からの場合）

### 1. セットアップ
```bash
cd /Users/furuyanaoki/Project/new.mail.score/.001_automation
chmod +x setup.sh monitor_refresh.sh
./setup.sh
```

### 2. Claude Code起動
```bash
tmux new -s cc -n claude
claude --dangerously-skip-permissions
```

### 3. ペイン番号確認（新しいターミナル）
```bash
tmux list-panes -t cc -a
```

### 4. 監視開始（確認結果に応じて）
```bash
# cc:0.0 の場合（最も一般的）
~/cc_automation/run_monitor.sh

# cc:1.0 の場合
TARGET="cc:1.0" ~/cc_automation/run_monitor.sh
```

## 🚨 よくあるエラー対応

### "target pane not found"
```bash
# ペイン確認
tmux list-panes -t cc -a

# 結果に応じて実行
TARGET="cc:0.0" ~/cc_automation/run_monitor.sh  # cc:0.0 の場合
TARGET="cc:1.0" ~/cc_automation/run_monitor.sh  # cc:1.0 の場合
```

### "tasks file not found"
```bash
# ファイル存在確認
ls -la /Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md

# 存在する場合はTASKS_PATH指定で実行
TASKS_PATH="/Users/furuyanaoki/Project/new.mail.score/specs/002-think-hard-ultrathink/tasks.md" ~/cc_automation/run_monitor.sh
```

## 📊 監視状況確認

### ログ確認
```bash
# 監視ログ
tail -f ~/cc_logs/monitor_cc.log

# Claude Code出力
tail -f ~/cc_logs/claude_cc_$(date +%Y%m%d).log
```

### 停止方法
```bash
# 監視停止（監視ターミナルで）
Ctrl+C

# Claude Code終了（Claude Codeターミナルで）
/exit
```

---

**重要**: ペイン番号（cc:0.0 vs cc:1.0）の確認が成功の鍵です。
必ず `tmux list-panes -t cc -a` で確認してから実行してください。