# TDD: Status Command
> Monitor TDD implementation progress across the project

## Usage
```bash
/tdd:status [--task <task-id>] [--phase <red|green|refactor>] [--verbose]
```

## Description
プロジェクト全体またはタスク別のTDD実装状況を確認します。各フェーズの進捗、技術負債、品質メトリクスを可視化します。

## Process
1. tasks_tdd.mdから状態を読み込み
2. 実装ファイルとテストファイルを検証
3. 各タスクのフェーズを判定
4. メトリクスを計算
5. レポートを生成

## Options
- `--task`: 特定タスクの詳細状態
- `--phase`: 特定フェーズのタスク一覧
- `--verbose`: 詳細情報を表示

## Status Detection Logic

### 1. Phase Detection
```python
def detect_task_phase(task_id):
    """タスクの現在フェーズを検出"""

    # Check git history for phase commits
    red_commit = find_commit(f"[{task_id}-RED]")
    green_commit = find_commit(f"[{task_id}-GREEN]")
    refactor_commit = find_commit(f"[{task_id}-REFACTOR]")

    # Determine current phase
    if refactor_commit:
        return "COMPLETED"
    elif green_commit:
        return "REFACTOR_PENDING"
    elif red_commit:
        return "GREEN_PENDING"
    else:
        return "NOT_STARTED"
```

### 2. Test Coverage Analysis
```python
def analyze_test_coverage():
    """テストカバレッジを分析"""
    result = run_command("pytest --cov=app --cov-report=json")
    coverage_data = json.loads(result)

    return {
        "total_coverage": coverage_data["totals"]["percent_covered"],
        "files": coverage_data["files"],
        "uncovered_lines": extract_uncovered_lines(coverage_data)
    }
```

### 3. Technical Debt Assessment
```python
def assess_technical_debt():
    """技術負債を評価"""
    debt_indicators = {
        "hardcoded_values": grep_pattern(r"(return\s+\d+|=\s*[\"\']\d+[\"\'])"),
        "todo_comments": grep_pattern(r"(TODO|FIXME|HACK|XXX)"),
        "skipped_tests": grep_pattern(r"@pytest\.mark\.skip"),
        "long_methods": find_long_methods(threshold=50),
        "duplicate_code": detect_duplication()
    }

    return calculate_debt_score(debt_indicators)
```

## Example Output

### Project Overview
```markdown
# 🧪 TDD Status Report
Generated: 2025-09-18 10:30:00

## 📊 Overall Progress
Total Tasks: 65
├── ✅ Completed (all phases): 0 (0%)
├── 🔄 In Refactor: 13 (20%)
├── 🟢 In Green: 0 (0%)
├── 🔴 In Red: 0 (0%)
└── ⏳ Not Started: 52 (80%)

## 📈 Phase Distribution
```
RED     ████████████████░░░░ 20% (13/65)
GREEN   ████████████████░░░░ 20% (13/65)
REFACTOR ░░░░░░░░░░░░░░░░░░░░  0% (0/65)
```

## 🎯 TDD Compliance
- Compliance Rate: 30%
- Violations Found: 35
- Tests First Rate: 20%
- Test Coverage: 70%

## ⚠️ Technical Debt
- Debt Index: 0.35 (Target: <0.15)
- Hardcoded Values: 127 instances
- TODO Comments: 43
- Skipped Tests: 8

## 🚧 Current Focus
### Tasks in REFACTOR Phase (Priority)
- T005: Batch trigger endpoint
- T006: Batch status endpoint
- T007: Job import endpoint
- T008: Scoring calculation
- T009: Matching generation
- T010: User matching retrieval
- T011: Email generation
- T012: SQL execution
- T013: Monitoring metrics

### Next RED Phase Tasks
- T014: User registration
- T015: User login
- T016: User profile
```

### Task-Specific Status
```markdown
# Task T014 Status

## 📋 Basic Info
- Description: User registration endpoint
- Current Phase: NOT_STARTED
- Assigned: backend/app/routers/users.py

## 🧪 Test Status
- Test File: Not created
- Test Cases: 0
- Coverage: 0%

## 📝 Implementation Status
- Endpoint: Not implemented
- Database Model: Exists
- Schema: Defined

## ⏭️ Next Actions
1. Run `/tdd:red T014` to create failing tests
2. Define test cases for:
   - Valid registration
   - Duplicate email
   - Invalid password
   - Missing fields

## 🔗 Dependencies
- Database: ✅ Ready
- Schema: ✅ Defined
- Security: ⚠️ Needs implementation
```

## Metrics Calculation

### TDD Compliance Score
```python
def calculate_tdd_compliance():
    """TDD準拠スコアを計算"""
    factors = {
        "test_first_rate": 0.4,      # テストファースト率
        "coverage": 0.3,              # カバレッジ
        "phase_completion": 0.2,      # フェーズ完了率
        "debt_index": 0.1             # 技術負債指数
    }

    score = sum(
        get_metric(name) * weight
        for name, weight in factors.items()
    )

    return min(100, max(0, score))
```

### Phase Progress Tracking
```yaml
phases:
  RED:
    completed: [T005, T006, T007, T008, T009, T010, T011, T012, T013]
    in_progress: []
    pending: [T014, T015, T016, ...]

  GREEN:
    completed: [T005, T006, T007, T008, T009, T010, T011, T012, T013]
    in_progress: []
    pending: [T014, T015, T016, ...]

  REFACTOR:
    completed: []
    in_progress: []
    pending: [T005, T006, T007, T008, T009, T010, T011, T012, T013, ...]
```

## Visualization
```python
def generate_progress_chart():
    """進捗チャートを生成"""
    chart = """
    Task Progress by Phase:

    RED     [████████████████    ] 80% (52/65)
    GREEN   [████                ] 20% (13/65)
    REFACTOR[                    ]  0% (0/65)

    Daily Progress:
    Day 1: ████ 4 tasks
    Day 2: ████████ 8 tasks
    Day 3: ██ 2 tasks
    """
    return chart
```

## Integration Points
- `tasks_tdd.md`: タスク定義の読み込み
- `TDD_IMPLEMENTATION_STATUS.md`: 実装状況の更新
- Git history: フェーズコミットの検出
- pytest coverage: カバレッジ分析