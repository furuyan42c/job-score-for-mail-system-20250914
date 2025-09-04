# 基本Git統合機能 詳細設計書
設計日時: 2025-08-25 13:00:00

## 🎯 **Git状態監視システム詳細設計**

### **監視対象ファイル分類**
```yaml
File_Classification:
  critical_files:
    patterns: ["src/**", ".claude/agents/**", "database/**"]
    priority: "CRITICAL"
    action: "即座コミット提案"

  important_files:
    patterns: ["package.json", "tsconfig.json", "*.config.js", "specs/**"]
    priority: "HIGH"
    action: "30分以内コミット推奨"

  configuration_files:
    patterns: [".env.example", "README.md", "docs/**"]
    priority: "MEDIUM"
    action: "日次コミット推奨"

  temporary_files:
    patterns: ["logs/**", "node_modules/**", ".DS_Store", "*.tmp"]
    priority: "IGNORE"
    action: "監視対象外"
```

### **Git状態評価アルゴリズム**
```python
def assess_git_urgency(git_status):
    """Git状態の緊急度評価アルゴリズム"""
    urgency_score = 0

    # 未追跡ファイルの評価
    for file in git_status.untracked_files:
        if matches_pattern(file, CRITICAL_PATTERNS):
            urgency_score += 10
        elif matches_pattern(file, IMPORTANT_PATTERNS):
            urgency_score += 5

    # 変更ファイルの評価
    for file in git_status.modified_files:
        if matches_pattern(file, CRITICAL_PATTERNS):
            urgency_score += 8
        elif matches_pattern(file, IMPORTANT_PATTERNS):
            urgency_score += 3

    # 時間経過の評価
    time_since_last_commit = get_time_since_last_commit()
    if time_since_last_commit > 60:  # 60分
        urgency_score += 15
    elif time_since_last_commit > 30:  # 30分
        urgency_score += 5

    # 緊急度判定
    if urgency_score >= 20:
        return 'CRITICAL'
    elif urgency_score >= 10:
        return 'HIGH'
    elif urgency_score >= 5:
        return 'MEDIUM'
    else:
        return 'LOW'
```

## 🔧 **自動コミットメッセージ生成システム**

### **メッセージ生成ルール**
```yaml
Commit_Message_Templates:
  task_completion:
    format: "feat: Task {task_id} 完了 - {task_summary}"
    example: "feat: Task 3.4 完了 - バッチマッチング基盤実装"

  phase_milestone:
    format: "feat: Phase {phase_num} {status} - {description}"
    example: "feat: Phase 3 完了 - マッチングシステム実装"

  performance_improvement:
    format: "perf: {improvement_area} - {metrics_improvement}"
    example: "perf: バッチ処理最適化 - 処理時間30%短縮"

  bug_fix:
    format: "fix: {bug_description} - {solution_summary}"
    example: "fix: データ品質検証エラー - null値処理改善"

  emergency_save:
    format: "wip: セッション保存 - {progress_description}"
    example: "wip: セッション保存 - Task 3.1-3.3実装中"

  critical_fix:
    format: "fix(critical): {critical_issue} 緊急修正"
    example: "fix(critical): メモリリーク緊急修正"
```

### **コミット対象ファイル自動選定**
```python
def select_commit_files(trigger_type, all_changed_files):
    """コミット対象ファイルの自動選定"""

    if trigger_type == 'TASK_COMPLETION':
        # タスク関連ファイルのみ
        return filter_task_related_files(all_changed_files)

    elif trigger_type == 'PHASE_MILESTONE':
        # フェーズ関連の全変更
        return filter_phase_related_files(all_changed_files)

    elif trigger_type == 'SESSION_PRESERVATION':
        # 全ての重要な変更
        return filter_important_files(all_changed_files)

    elif trigger_type == 'CRITICAL_FIX':
        # 修正関連ファイルのみ
        return filter_fix_related_files(all_changed_files)

def filter_important_files(files):
    """重要ファイルのフィルタリング"""
    important_files = []

    for file in files:
        # 除外パターンチェック
        if matches_any_pattern(file, EXCLUDE_PATTERNS):
            continue

        # 重要パターンチェック
        if matches_any_pattern(file, CRITICAL_PATTERNS + IMPORTANT_PATTERNS):
            important_files.append(file)

    return important_files
```

## 🚨 **エラー検知・ロールバックシステム**

### **性能監視指標の定義**
```yaml
Performance_Metrics:
  batch_processing_time:
    measurement: "10K users処理時間"
    baseline: "45-75分"
    warning_threshold: "90分"
    critical_threshold: "120分"
    measurement_interval: "リアルタイム"

  memory_usage:
    measurement: "システム全体メモリ使用量"
    baseline: "2-4GB"
    warning_threshold: "5GB"
    critical_threshold: "7GB"
    measurement_interval: "5分毎"

  error_rate:
    measurement: "処理エラー発生率"
    baseline: "0.1%未満"
    warning_threshold: "1%"
    critical_threshold: "5%"
    measurement_interval: "リアルタイム"

  matching_accuracy:
    measurement: "求人マッチング精度"
    baseline: "97-99%"
    warning_threshold: "95%未満"
    critical_threshold: "90%未満"
    measurement_interval: "バッチ完了時"
```

### **ロールバック戦略決定アルゴリズム**
```python
def determine_rollback_strategy(error_diagnosis):
    """エラー診断に基づくロールバック戦略決定"""

    severity = error_diagnosis.severity
    affected_components = error_diagnosis.affected_components
    time_since_last_good_state = error_diagnosis.time_since_last_good_state

    if severity == 'CRITICAL' and 'system_stability' in affected_components:
        # システム全体に影響する重大問題
        return {
            'strategy': 'EMERGENCY_FULL_ROLLBACK',
            'target': get_last_stable_checkpoint(),
            'auto_execute': True,
            'notify_human': True
        }

    elif severity == 'CRITICAL' and time_since_last_good_state < 30:
        # 最近の変更による重大問題
        return {
            'strategy': 'SELECTIVE_COMMIT_ROLLBACK',
            'target': identify_problem_commits(error_diagnosis),
            'auto_execute': False,  # 人間承認要求
            'notify_human': True
        }

    elif severity == 'HIGH':
        # 重要だが即座対応不要
        return {
            'strategy': 'ASSISTED_ROLLBACK',
            'target': generate_rollback_options(error_diagnosis),
            'auto_execute': False,
            'notify_human': True
        }

    else:
        # 監視継続
        return {
            'strategy': 'MONITOR_AND_ALERT',
            'auto_execute': False,
            'notify_human': True
        }
```

## 📊 **進捗報告強化システム**

### **Git統合進捗レポート形式**
```yaml
Enhanced_Progress_Report_Format:
  header:
    timestamp: "2025-08-25T13:00:00.000Z"
    session_duration: "45分"
    overall_progress: "Phase 3: 25% 完了"

  git_status_section:
    branch: "develop"
    last_commit: "feat: Task 3.2 完了 - スコアリング最適化"
    uncommitted_files:
      critical: 3
      important: 1
      total: 7
    recommended_action: "Task 3.3完了後のコミット推奨"
    urgency: "MEDIUM"

  automated_actions_section:
    recent_commits:
      - "13:00 - feat: Task 3.2 完了 (auto)"
      - "12:30 - wip: セッション保存 (auto)"
    error_detections:
      - "12:45 - 性能軽度劣化検知 - 監視継続中"
    pending_approvals:
      - "フェーズ3マイルストーン・コミット承認待ち"

  github_integration_section:
    sync_status: "最終同期: 13:00"
    open_issues: 2
    pending_prs: 0
    milestone_progress: "Phase 3: 25%"
```

## 🛡️ **安全性機構の詳細設計**

### **コミット前検証システム**
```python
def validate_commit_safety(files_to_commit):
    """コミット前安全性検証"""

    validation_results = []

    for file_path in files_to_commit:
        # 1. ファイル存在確認
        if not os.path.exists(file_path):
            validation_results.append({
                'file': file_path,
                'status': 'ERROR',
                'message': 'ファイルが存在しません'
            })
            continue

        # 2. ファイルサイズ確認
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            validation_results.append({
                'file': file_path,
                'status': 'WARNING',
                'message': 'ファイルサイズが大きいです (10MB超過)'
            })

        # 3. 秘匿情報スキャン
        if contains_sensitive_data(file_path):
            validation_results.append({
                'file': file_path,
                'status': 'ERROR',
                'message': '秘匿情報が含まれている可能性があります'
            })

        # 4. 構文チェック（TypeScript/JSONファイル）
        if file_path.endswith(('.ts', '.js', '.json')):
            syntax_result = check_syntax(file_path)
            if not syntax_result.valid:
                validation_results.append({
                    'file': file_path,
                    'status': 'ERROR',
                    'message': f'構文エラー: {syntax_result.error}'
                })

    return validation_results

def contains_sensitive_data(file_path):
    """秘匿情報検出"""
    sensitive_patterns = [
        r'(?i)api[_-]?key[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}',
        r'(?i)password[\'"\s]*[:=][\'"\s]*[^\s\'"]{8,}',
        r'(?i)secret[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{16,}',
        r'(?i)token[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}'
    ]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for pattern in sensitive_patterns:
            if re.search(pattern, content):
                return True

    except Exception:
        return False

    return False
```

### **ロールバック安全機構**
```python
def execute_safe_rollback(rollback_option):
    """安全なロールバック実行"""

    try:
        # 1. 事前スナップショット作成
        snapshot_id = create_emergency_snapshot()
        log_action(f"ロールバック前スナップショット作成: {snapshot_id}")

        # 2. 他エージェント通知・停止
        notify_all_agents("ROLLBACK_IN_PROGRESS")
        stop_all_agents()

        # 3. ロールバック実行
        if rollback_option.type == 'FILE_SELECTIVE':
            result = execute_file_rollback(rollback_option)
        elif rollback_option.type == 'COMMIT_ROLLBACK':
            result = execute_commit_rollback(rollback_option)
        else:
            result = execute_full_rollback(rollback_option)

        # 4. 整合性確認
        integrity_check = verify_system_integrity()
        if not integrity_check.passed:
            # ロールバック失敗時の緊急復旧
            restore_from_snapshot(snapshot_id)
            raise RollbackException("整合性確認失敗")

        # 5. エージェント再起動
        restart_agents_safely()

        # 6. 成功ログ記録
        log_action(f"ロールバック成功: {rollback_option.description}")

        return {
            'status': 'SUCCESS',
            'snapshot_id': snapshot_id,
            'restored_state': result.restored_state
        }

    except Exception as e:
        log_error(f"ロールバック失敗: {str(e)}")
        # 緊急復旧手順
        emergency_recovery_procedure()
        raise
```

この詳細設計に基づいて、次にagent-orchestrator.mdに実装を追加します。
