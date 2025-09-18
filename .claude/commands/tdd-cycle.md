# TDD: Cycle Command
> Execute complete TDD cycle for a task

## Usage
```bash
/tdd:cycle <task-id> [--auto] [--parallel] [--validate]
```

## Description
タスクの完全なTDDサイクル（RED→GREEN→REFACTOR）を実行します。各フェーズで必要な検証を行い、自動的に次のフェーズへ進みます。

## Process
1. REDフェーズ: テスト作成と失敗確認
2. GREENフェーズ: 最小実装とパス確認
3. REFACTORフェーズ: コード品質改善
4. 最終検証とレポート生成
5. 次タスクへの移行準備

## Options
- `--auto`: 各フェーズを自動実行（確認なし）
- `--parallel`: 独立タスクを並列実行
- `--validate`: 各フェーズ後に詳細検証

## Full Cycle Implementation

### 1. Initialize Cycle
```python
def initialize_tdd_cycle(task_id):
    """TDDサイクルを初期化"""
    task = load_task(task_id)

    # Validate prerequisites
    check_dependencies(task)
    ensure_clean_state()

    # Create cycle context
    context = {
        "task": task,
        "start_time": datetime.now(),
        "phases": ["RED", "GREEN", "REFACTOR"],
        "current_phase": None,
        "artifacts": []
    }

    return context
```

### 2. Execute RED Phase
```python
async def execute_red_phase(context):
    """REDフェーズを実行"""
    task = context["task"]

    # Create test structure
    test_file = create_test_file(task)

    # Write failing tests
    tests = [
        write_happy_path_test(task),
        write_edge_case_tests(task),
        write_error_case_tests(task)
    ]

    # Verify tests fail
    result = await run_tests(test_file)
    if result.passed:
        raise TDDViolation("Tests must fail in RED phase")

    # Commit
    await git_commit(f"test({task.scope}): add failing tests [{task.id}-RED]")

    context["phases_completed"].append("RED")
    return context
```

### 3. Execute GREEN Phase
```python
async def execute_green_phase(context):
    """GREENフェーズを実行"""
    task = context["task"]

    # Create minimal implementation
    impl_file = create_implementation_file(task)

    # Write minimal code
    if task.complexity == "simple":
        write_hardcoded_implementation(impl_file, task)
    else:
        write_minimal_logic_implementation(impl_file, task)

    # Verify tests pass
    result = await run_tests()
    if not result.passed:
        raise TDDViolation("Tests must pass in GREEN phase")

    # Commit
    await git_commit(f"feat({task.scope}): minimal implementation [{task.id}-GREEN]")

    context["phases_completed"].append("GREEN")
    context["tech_debt"].append(analyze_tech_debt(impl_file))
    return context
```

### 4. Execute REFACTOR Phase
```python
async def execute_refactor_phase(context):
    """REFACTORフェーズを実行"""
    task = context["task"]
    debt_items = context["tech_debt"]

    # Refactor implementation
    for debt in debt_items:
        if debt.type == "hardcoded":
            replace_with_dynamic_values(debt)
        elif debt.type == "duplication":
            extract_common_code(debt)
        elif debt.type == "complexity":
            simplify_logic(debt)

    # Add missing components
    add_validation(task)
    add_error_handling(task)
    add_logging(task)

    # Verify tests still pass
    result = await run_tests()
    if not result.passed:
        raise TDDViolation("Tests broken during refactoring")

    # Measure improvements
    metrics = measure_quality_metrics()

    # Commit
    await git_commit(f"refactor({task.scope}): improve implementation [{task.id}-REFACTOR]")

    context["phases_completed"].append("REFACTOR")
    context["final_metrics"] = metrics
    return context
```

### 5. Finalize Cycle
```python
def finalize_cycle(context):
    """サイクルを完了"""
    # Generate summary
    summary = {
        "task_id": context["task"]["id"],
        "duration": datetime.now() - context["start_time"],
        "phases_completed": context["phases_completed"],
        "metrics": context["final_metrics"],
        "next_task": suggest_next_task()
    }

    # Update tracking
    update_tdd_status(summary)

    # Generate report
    generate_cycle_report(summary)

    return summary
```

## Example Execution

### Interactive Mode (Default)
```bash
$ /tdd:cycle T014

🔄 Starting TDD Cycle for T014: User Registration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1/3: RED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Creating test file: tests/test_users.py
✅ Test structure created
✅ 3 test cases written

🧪 Running tests...
❌ All tests failing (expected)

Continue to GREEN phase? [Y/n]: Y

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2/3: GREEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Creating implementation: app/routers/users.py
✅ Minimal implementation created
⚠️ Technical debt: 3 hardcoded values

🧪 Running tests...
✅ All tests passing

Continue to REFACTOR phase? [Y/n]: Y

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3/3: REFACTOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔨 Refactoring implementation...
✅ Removed hardcoded values
✅ Added input validation
✅ Implemented error handling
✅ Added database persistence

🧪 Running tests...
✅ All tests still passing

📊 Quality Metrics:
- Coverage: 92% (+15%)
- Complexity: 4 (-4)
- Performance: 45ms (-75ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ TDD Cycle Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Duration: 2h 15min
Commits: 3
Quality: A

Next suggested task: T015
```

### Auto Mode
```bash
$ /tdd:cycle T014 --auto

🤖 Auto-executing TDD Cycle for T014

[RED] Creating tests... ✅ (5 min)
[RED] Verifying failure... ✅
[RED] Committing... ✅

[GREEN] Implementing... ✅ (8 min)
[GREEN] Verifying pass... ✅
[GREEN] Committing... ✅

[REFACTOR] Improving... ✅ (12 min)
[REFACTOR] Verifying... ✅
[REFACTOR] Committing... ✅

✅ Cycle completed in 25 minutes
View report: reports/tdd/T014-cycle.md
```

## Parallel Execution

### Parallel Task Processing
```python
async def execute_parallel_cycles(task_ids):
    """複数タスクを並列実行"""
    # Group independent tasks
    groups = group_by_dependencies(task_ids)

    results = []
    for group in groups:
        # Execute group in parallel
        tasks = [execute_cycle(task_id) for task_id in group]
        group_results = await asyncio.gather(*tasks)
        results.extend(group_results)

    return results
```

### Example Parallel Execution
```bash
$ /tdd:cycle T014,T015,T016 --parallel

🔄 Executing 3 tasks in parallel

T014: [RED····] [GREEN····] [REFACTOR····] ✅
T015: [RED····] [GREEN····] [REFACTOR····] ✅
T016: [RED····] [GREEN····] [REFACTOR····] ✅

All cycles completed in 45 minutes (3x speedup)
```

## Cycle Report Generation

```markdown
# TDD Cycle Report: T014

## Summary
- Task: User Registration Endpoint
- Duration: 2h 15min
- Result: ✅ Success

## Phase Details

### RED Phase (30 min)
- Tests created: 3
- Test file: tests/test_users.py
- Verification: All tests failing ✅

### GREEN Phase (45 min)
- Implementation: app/routers/users.py
- Type: Minimal with hardcoding
- Verification: All tests passing ✅

### REFACTOR Phase (60 min)
- Improvements:
  - Removed 3 hardcoded values
  - Added input validation
  - Implemented error handling
  - Added database layer

## Quality Metrics
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Coverage | 77% | 92% | +15% |
| Complexity | 8 | 4 | -50% |
| Performance | 120ms | 45ms | -62% |
| Tech Debt | 0.4 | 0.1 | -75% |

## Artifacts
- Test file: `tests/test_users.py`
- Implementation: `app/routers/users.py`
- Schema: `app/schemas/users.py`
- Repository: `app/repositories/users.py`

## Commits
1. `test(users): add failing tests [T014-RED]`
2. `feat(users): minimal implementation [T014-GREEN]`
3. `refactor(users): improve implementation [T014-REFACTOR]`

## Next Steps
- Continue with T015: User Login
- Add integration tests
- Performance benchmark
```

## Error Recovery

### Phase Failure Handling
```python
async def handle_phase_failure(context, error):
    """フェーズ失敗時の処理"""
    phase = context["current_phase"]

    if phase == "RED":
        # Provide test writing assistance
        suggest_test_structure(context["task"])

    elif phase == "GREEN":
        # Debug why tests aren't passing
        debug_test_failures()

    elif phase == "REFACTOR":
        # Rollback changes and retry
        await git_rollback()
        retry_refactor(context)
```

## Integration with CI/CD
```yaml
# Automated TDD cycle in CI
steps:
  - name: Execute TDD Cycle
    run: |
      claude-code /tdd:cycle $TASK_ID --auto --validate
      claude-code /tdd:verify --strict
```