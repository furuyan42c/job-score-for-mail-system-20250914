# TDD: Verify Command
> Validate TDD compliance for current implementation

## Usage
```bash
/tdd:verify [--phase <red|green|refactor>] [--task <task-id>] [--strict]
```

## Description
現在の実装がTDD原則に準拠しているか検証します。違反を検出し、修正方法を提案します。

## Process
1. 実装とテストの時系列を分析
2. TDD違反パターンを検出
3. フェーズ別の要件を検証
4. 違反レポートを生成
5. 修正提案を提供

## Options
- `--phase`: 特定フェーズの検証
- `--task`: 特定タスクの検証
- `--strict`: 厳密モード（警告もエラー扱い）

## Verification Rules

### RED Phase Verification
```python
def verify_red_phase(task_id):
    """REDフェーズの検証"""
    violations = []

    # 1. テストが存在するか
    test_file = find_test_file(task_id)
    if not test_file:
        violations.append({
            "type": "MISSING_TEST",
            "severity": "ERROR",
            "message": "No test file found"
        })

    # 2. テストが失敗するか
    test_result = run_test(test_file)
    if test_result.passed:
        violations.append({
            "type": "TEST_NOT_FAILING",
            "severity": "ERROR",
            "message": "Test should fail in RED phase"
        })

    # 3. 実装が存在しないか
    impl_file = find_implementation(task_id)
    if impl_file and has_real_implementation(impl_file):
        violations.append({
            "type": "PREMATURE_IMPLEMENTATION",
            "severity": "ERROR",
            "message": "Implementation exists before test"
        })

    return violations
```

### GREEN Phase Verification
```python
def verify_green_phase(task_id):
    """GREENフェーズの検証"""
    violations = []

    # 1. REDフェーズが完了しているか
    if not has_red_commit(task_id):
        violations.append({
            "type": "SKIPPED_RED_PHASE",
            "severity": "ERROR",
            "message": "RED phase was not completed"
        })

    # 2. テストがパスするか
    test_result = run_test(task_id)
    if not test_result.passed:
        violations.append({
            "type": "TEST_FAILING",
            "severity": "ERROR",
            "message": "Test must pass in GREEN phase"
        })

    # 3. 実装が最小限か
    complexity = measure_complexity(task_id)
    if complexity > MINIMAL_THRESHOLD:
        violations.append({
            "type": "OVER_ENGINEERING",
            "severity": "WARNING",
            "message": "Implementation is too complex for GREEN phase"
        })

    return violations
```

### REFACTOR Phase Verification
```python
def verify_refactor_phase(task_id):
    """REFACTORフェーズの検証"""
    violations = []

    # 1. GREENフェーズが完了しているか
    if not has_green_commit(task_id):
        violations.append({
            "type": "SKIPPED_GREEN_PHASE",
            "severity": "ERROR",
            "message": "GREEN phase was not completed"
        })

    # 2. テストが継続的にパスするか
    test_result = run_test(task_id)
    if not test_result.passed:
        violations.append({
            "type": "BROKEN_TESTS",
            "severity": "ERROR",
            "message": "Tests broken during refactoring"
        })

    # 3. 技術負債が改善されているか
    debt_before = get_debt_at_commit(f"{task_id}-GREEN")
    debt_after = get_current_debt(task_id)
    if debt_after >= debt_before:
        violations.append({
            "type": "DEBT_NOT_REDUCED",
            "severity": "WARNING",
            "message": "Technical debt not improved"
        })

    return violations
```

## Violation Detection Patterns

### Pattern 1: Test After Implementation
```python
# Git log analysis
commits = get_commits()
for commit in commits:
    if "feat(" in commit.message and not has_prior_test(commit):
        report_violation("TEST_AFTER_IMPLEMENTATION", commit)
```

### Pattern 2: Skipped Tests
```python
# Test file analysis
skipped = grep_pattern(r"@pytest\.mark\.skip|\.skip\(|skipTest")
if skipped:
    report_violation("SKIPPED_TESTS", skipped)
```

### Pattern 3: Disabled Assertions
```python
# Commented assertions
disabled = grep_pattern(r"#\s*assert|//\s*assert|/\*.*assert.*\*/")
if disabled:
    report_violation("DISABLED_ASSERTIONS", disabled)
```

## Example Output

### Success Case
```markdown
✅ TDD Verification Passed

## Summary
- Tasks Verified: 13
- Violations: 0
- Warnings: 2
- Compliance: 100%

## Phase Verification
- RED: ✅ All tests created first
- GREEN: ✅ Minimal implementations
- REFACTOR: ⚠️ 2 tasks pending refactor

## Recommendations
1. Complete refactor for T005-T006
2. Continue with T014 RED phase
```

### Violation Case
```markdown
❌ TDD Violations Detected

## Summary
- Tasks Verified: 5
- Violations: 3 (ERROR: 2, WARNING: 1)
- Compliance: 40%

## Violations Found

### 🔴 ERROR: Test After Implementation
- Task: T020
- File: app/routers/analytics.py
- Evidence: Implementation commit before test commit
- Fix: Cannot fix retroactively, mark as technical debt

### 🔴 ERROR: Skipped Tests
- Task: T025
- File: tests/test_scoring.py:45
- Evidence: @pytest.mark.skip("TODO: implement")
- Fix: Remove skip decorator and implement test

### ⚠️ WARNING: Over-Engineering in GREEN
- Task: T030
- File: app/services/matching.py
- Evidence: Complex algorithm in GREEN phase
- Fix: Simplify to hardcoded values first

## Correction Plan
1. Run `/tdd:red T020` to add missing tests
2. Enable skipped tests and fix failures
3. Simplify T030 to minimal implementation
```

## Automated Fixes

### Auto-fix Options
```python
def auto_fix_violations(violations):
    """違反の自動修正"""
    fixes_applied = []

    for violation in violations:
        if violation["type"] == "SKIPPED_TESTS":
            remove_skip_decorators(violation["file"])
            fixes_applied.append("Enabled skipped tests")

        elif violation["type"] == "DISABLED_ASSERTIONS":
            uncomment_assertions(violation["file"])
            fixes_applied.append("Re-enabled assertions")

        elif violation["type"] == "OVER_ENGINEERING":
            suggest_minimal_implementation(violation["task"])
            fixes_applied.append("Generated minimal version")

    return fixes_applied
```

## Compliance Metrics
```yaml
compliance_levels:
  strict:  # --strict mode
    red_phase_required: true
    test_first_enforced: true
    minimal_implementation: true
    zero_skip_tests: true
    max_complexity: 5

  standard:  # default
    red_phase_required: true
    test_first_enforced: false
    minimal_implementation: false
    zero_skip_tests: false
    max_complexity: 10

  lenient:  # migration mode
    red_phase_required: false
    test_first_enforced: false
    minimal_implementation: false
    zero_skip_tests: false
    max_complexity: 20
```

## Integration with CI/CD
```yaml
# .github/workflows/tdd-verify.yml
name: TDD Compliance Check
on: [push, pull_request]

jobs:
  tdd-verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Verify TDD Compliance
        run: |
          claude-code /tdd:verify --strict
          if [ $? -ne 0 ]; then
            echo "TDD violations detected"
            exit 1
          fi
```