# GitHub統合機能 テスト・検証プラン
テスト計画策定日時: 2025-08-25 13:20:00

## 🎯 **テスト目的・範囲**

agent-orchestratorに実装したGitHub統合機能（Phase 1）の動作検証と安全性確認を行う。

## 📋 **テスト項目一覧**

### **A. Git状態監視機能テスト**

#### **A-1. 基本監視機能**
```yaml
Test_A1_Basic_Monitoring:
  test_cases:
    monitor_untracked_files:
      setup: "新規ファイル作成（src/test.ts, .claude/agents/test.md）"
      action: "monitor_git_status()実行"
      expected: "critical_files配列に2ファイル検出、urgency='HIGH'"

    monitor_modified_files:
      setup: "既存ファイル変更（package.json, database/schema.sql）"
      action: "monitor_git_status()実行"
      expected: "important_files配列に検出、urgency='MEDIUM'"

    no_changes_detected:
      setup: "Git作業ディレクトリクリーン状態"
      action: "monitor_git_status()実行"
      expected: "urgency='LOW', recommended_action='現在のペースで作業継続'"
```

#### **A-2. ファイル分類精度**
```yaml
Test_A2_File_Classification:
  critical_files_detection:
    test_files: ["src/core/matching.ts", ".claude/agents/orchestrator.md", "database/migrations/001.sql"]
    expected_classification: "CRITICAL"

  important_files_detection:
    test_files: ["package.json", "tsconfig.json", "specs/tasks.md"]
    expected_classification: "IMPORTANT"

  ignored_files_exclusion:
    test_files: ["logs/debug.log", "node_modules/package.json", ".DS_Store"]
    expected_classification: "IGNORE"
```

### **B. 自動コミット機能テスト**

#### **B-1. タスク完了時自動コミット**
```yaml
Test_B1_Task_Completion_Commit:
  low_urgency_auto_commit:
    setup: "Task 3.1完了、1ファイル変更（src/utils/helper.ts）"
    action: "handle_task_completion('3.1', 'ヘルパー関数実装')"
    expected: "自動コミット実行、メッセージ='feat: Task 3.1 完了 - ヘルパー関数実装'"

  high_urgency_approval_required:
    setup: "Task 3.4完了、10ファイル変更（重要システム変更）"
    action: "handle_task_completion('3.4', 'バッチマッチング実装')"
    expected: "人間承認要求、自動実行なし"

  safety_check_failure:
    setup: "構文エラーファイル含む変更"
    action: "handle_task_completion('3.2', 'テスト実装')"
    expected: "safety_check失敗、コミット中止、エラーログ出力"
```

#### **B-2. セッション保存機能**
```yaml
Test_B2_Session_Preservation:
  emergency_save_trigger:
    setup: "セッション80分経過、重要ファイル3個変更"
    action: "handle_session_preservation()"
    expected: "緊急コミット実行、プッシュ実行、handover情報作成"

  no_important_changes:
    setup: "セッション80分経過、変更なしまたは無関係ファイルのみ"
    action: "handle_session_preservation()"
    expected: "コミット不要、handover情報のみ作成"
```

### **C. エラー検知・ロールバック機能テスト**

#### **C-1. 性能劣化検知**
```yaml
Test_C1_Performance_Detection:
  critical_performance_issue:
    setup: "バッチ処理時間150分に設定"
    action: "detect_performance_regression(mock_metrics)"
    expected: "CRITICAL severity issue検出、自動ロールバック判定"

  warning_level_issue:
    setup: "バッチ処理時間95分、メモリ5.5GB使用"
    action: "detect_performance_regression(mock_metrics)"
    expected: "HIGH severity issue検出、人間承認要求"

  normal_operation:
    setup: "バッチ処理時間65分、メモリ3.2GB使用"
    action: "detect_performance_regression(mock_metrics)"
    expected: "issues=[]、正常判定"
```

#### **C-2. 自動ロールバック実行**
```yaml
Test_C2_Automatic_Rollback:
  file_selective_rollback:
    setup: "特定ファイル問題、safe_commit特定済み"
    action: "execute_automatic_rollback(FILE_SELECTIVE_option)"
    expected: "問題ファイルのみロールバック、整合性チェック通過"

  commit_revert_rollback:
    setup: "問題コミット2個特定済み"
    action: "execute_automatic_rollback(COMMIT_REVERT_option)"
    expected: "git revert実行、システム健全性復旧"

  rollback_failure_recovery:
    setup: "ロールバック実行中にエラー発生"
    action: "execute_automatic_rollback(mock_failing_option)"
    expected: "emergency_snapshot復元、人間介入要求"
```

### **D. 進捗報告強化機能テスト**

#### **D-1. Git統合進捗報告**
```yaml
Test_D1_Enhanced_Progress_Report:
  comprehensive_report_generation:
    setup: "タスク進捗50%、Git未コミット5ファイル、GitHub同期済み"
    action: "generate_enhanced_progress_report()"
    expected: |
      - 基本進捗情報正常
      - git_integration セクション正常
      - automated_actions セクション正常
      - github_integration セクション正常

  git_urgency_recommendations:
    setup: "CRITICAL urgency状態"
    action: "get_recommended_git_action('CRITICAL')"
    expected: "'即座にコミット・プッシュが必要です'"

  action_history_tracking:
    setup: "自動コミット3回、エラー検知1回実行後"
    action: "get_recent_auto_commits(), get_recent_error_detections()"
    expected: "正確な履歴情報取得、タイムスタンプ正常"
```

### **E. GitHub API連携機能テスト**

#### **E-1. Issue管理機能**
```yaml
Test_E1_GitHub_Issues:
  completed_task_issue_close:
    setup: "Task 3.1完了、関連Issue #15存在"
    action: "sync_with_github_issues()"
    expected: "Issue #15自動クローズ、完了コメント追加"

  new_problem_issue_creation:
    setup: "新規システム問題検出"
    action: "create_github_issue(problem_info)"
    expected: "新Issue作成、適切なラベル・説明文設定"

  api_failure_graceful_handling:
    setup: "GitHub API接続不可状態"
    action: "sync_with_github_issues()"
    expected: "エラーログ出力、ローカル操作継続、接続回復時再試行"
```

#### **E-2. Pull Request作成支援**
```yaml
Test_E2_Pull_Request:
  phase_completion_pr_suggestion:
    setup: "Phase 3完了"
    action: "suggest_pull_request_creation(3, 'マッチングシステム実装')"
    expected: "PR提案生成、人間承認待ち状態、詳細説明文生成"

  pr_description_generation:
    setup: "Phase 3の10タスク完了、性能改善2件"
    action: "generate_pr_description(3, 'マッチングシステム実装')"
    expected: "構造化された説明文、タスクリスト、改善項目、チェックリスト含む"
```

## 🧪 **テスト実行手順**

### **Phase 1: 単体機能テスト（1日目）**

#### **環境準備**
```bash
# テスト環境の初期化
git checkout -b test/github-integration
echo "# Test file for GitHub integration" > src/test-integration.ts
echo "# Test agent file" > .claude/agents/test-agent.md

# テスト用設定の適用
export GITHUB_INTEGRATION_TEST_MODE=true
export GIT_INTEGRATION_LOG_LEVEL=DEBUG
```

#### **Git状態監視テスト実行**
```python
# Test A-1: 基本監視機能
def test_basic_git_monitoring():
    # 1. クリーン状態の確認
    result = monitor_git_status()
    assert result['urgency'] == 'LOW'

    # 2. 重要ファイル追加
    create_test_file('src/critical-test.ts')
    result = monitor_git_status()
    assert result['urgency'] in ['HIGH', 'CRITICAL']
    assert 'src/critical-test.ts' in result['critical_files']

    # 3. 推奨アクション確認
    action = get_recommended_git_action(result['urgency'])
    assert 'コミット' in action

    print("✅ Git監視機能テスト通過")

# Test A-2: ファイル分類テスト
def test_file_classification():
    test_files = [
        ('src/core/test.ts', 'CRITICAL'),
        ('package.json', 'IMPORTANT'),
        ('logs/test.log', 'IGNORE')
    ]

    for file_path, expected_class in test_files:
        create_test_file(file_path)
        classification = classify_file_importance(file_path)
        assert classification == expected_class

    print("✅ ファイル分類テスト通過")
```

#### **自動コミット機能テスト実行**
```python
# Test B-1: タスク完了コミットテスト
def test_task_completion_commit():
    # 1. 低緊急度自動コミット
    create_test_file('src/simple-change.ts')
    result = handle_task_completion('TEST-1', 'テスト実装')
    assert result['auto_committed'] == True
    assert 'feat: Task TEST-1 完了' in result['commit_message']

    # 2. 高緊急度承認要求
    create_multiple_test_files(10)  # 多数ファイル変更
    result = handle_task_completion('TEST-2', '大規模変更')
    assert result['auto_committed'] == False
    assert result['requires_approval'] == True

    print("✅ タスク完了コミットテスト通過")
```

### **Phase 2: 統合機能テスト（2日目）**

#### **エラー検知・ロールバックテスト**
```python
# Test C-1: 性能劣化検知テスト
def test_performance_regression_detection():
    # 1. 正常状態
    normal_metrics = create_normal_metrics()
    issues = detect_performance_regression(normal_metrics)
    assert len(issues) == 0

    # 2. CRITICAL問題
    critical_metrics = create_critical_metrics(processing_time=150)
    issues = detect_performance_regression(critical_metrics)
    assert len(issues) > 0
    assert issues[0]['severity'] == 'CRITICAL'

    print("✅ 性能劣化検知テスト通過")

# Test C-2: ロールバック実行テスト
def test_rollback_execution():
    # 安全な環境でのロールバックテスト
    snapshot_id = create_test_snapshot()

    # 問題状態作成
    create_problematic_commit()

    # ロールバック実行
    rollback_option = create_test_rollback_option()
    result = execute_automatic_rollback(rollback_option, snapshot_id)

    assert result['status'] == 'SUCCESS'
    assert verify_system_integrity()['passed'] == True

    print("✅ ロールバック実行テスト通過")
```

### **Phase 3: 完全統合テスト（3日目）**

#### **実環境シミュレーションテスト**
```bash
# 完全なワークフローテスト
echo "=== GitHub統合機能 完全統合テスト ==="

# 1. タスク実行→自動コミット→進捗報告のフロー
python test_full_workflow.py

# 2. エラー発生→検知→ロールバック→復旧のフロー
python test_error_recovery_workflow.py

# 3. セッション保存→プッシュ→次セッション復旧のフロー
python test_session_continuity.py

echo "=== 統合テスト完了 ==="
```

## ✅ **成功基準・合格条件**

### **機能要件合格基準**
```yaml
Functional_Success_Criteria:
  git_monitoring:
    file_detection_accuracy: "95%以上"
    urgency_assessment_accuracy: "90%以上"
    response_time: "5秒以内"

  auto_commit:
    safety_check_effectiveness: "100%（危険コミット0件）"
    message_generation_quality: "手動レビュー90%満足"
    success_rate: "95%以上"

  error_detection:
    performance_issue_detection: "90%以上"
    false_positive_rate: "5%未満"
    response_time: "30秒以内"

  rollback_system:
    rollback_success_rate: "90%以上"
    data_loss_incidents: "0件"
    integrity_verification: "100%実行"
```

### **非機能要件合格基準**
```yaml
Non_Functional_Success_Criteria:
  reliability:
    system_availability: "99%以上"
    error_recovery_rate: "95%以上"

  performance:
    monitoring_overhead: "5%未満"
    git_operation_time: "平均10秒以内"

  safety:
    unauthorized_commits: "0件"
    system_corruption: "0件"
    rollback_failures: "5%未満"
```

## 📊 **テスト結果記録テンプレート**

### **テスト実行記録**
```yaml
Test_Execution_Record:
  date: "2025-08-25"
  tester: "Claude Code"
  environment: "Development"

  test_results:
    git_monitoring_tests:
      total_cases: 12
      passed: 12
      failed: 0
      success_rate: "100%"

    auto_commit_tests:
      total_cases: 8
      passed: 7
      failed: 1
      issues: ["高負荷時のタイムアウト発生"]

    error_detection_tests:
      total_cases: 6
      passed: 6
      failed: 0
      success_rate: "100%"

  overall_assessment: "合格"
  deployment_recommendation: "本番環境デプロイ承認"
```

## 🚨 **トラブルシューティング・ガイド**

### **よくある問題と対処法**
```yaml
Common_Issues:
  git_command_timeout:
    symptom: "Git操作が30秒以上応答しない"
    cause: "リポジトリサイズ大、ネットワーク遅延"
    solution: "タイムアウト値調整、操作分割"

  commit_safety_check_failure:
    symptom: "安全性チェックで構文エラー検出"
    cause: "TypeScriptコンパイルエラー"
    solution: "該当ファイル修正、再テスト実行"

  rollback_integrity_failure:
    symptom: "ロールバック後の整合性チェック失敗"
    cause: "依存ファイル不整合、DB状態不一致"
    solution: "完全スナップショット復元、手動修正"

  github_api_rate_limit:
    symptom: "GitHub API呼び出し制限に到達"
    cause: "短時間での大量API呼び出し"
    solution: "API呼び出し間隔調整、キャッシュ活用"
```

この包括的なテスト計画により、GitHub統合機能の安全性と信頼性を確保できます。
