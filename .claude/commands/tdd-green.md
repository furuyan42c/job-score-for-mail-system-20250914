# TDD: GREEN Phase Command
> Minimal implementation to make tests pass

## Usage
```bash
/tdd:green <task-id> [--minimal] [--verify]
```

## Description
GREENフェーズ: 最小限の実装でテストをパスさせます。ハードコーディングも許容し、まずは動作することを優先します。

## Process
1. REDフェーズの確認
2. 最小限の実装を作成
3. テストを実行してパス確認
4. 全テストがパスすることを確認
5. コミットメッセージを生成

## Options
- `--minimal`: 最小実装を強制（ハードコード推奨）
- `--verify`: 実装後に全テストを実行

## Implementation Steps

### 1. Verify RED Phase Complete
```python
def verify_red_phase(task_id):
    """Ensure RED phase was completed"""
    test_exists = check_test_exists(task_id)
    test_failing = verify_test_failing(task_id)

    if not test_exists:
        raise TDDViolation(f"No test found for {task_id}. Run /tdd:red first")
    if not test_failing:
        raise TDDViolation(f"Test already passing for {task_id}")
```

### 2. Create Minimal Implementation
```python
# Example for T014: User Registration (Minimal)
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    name: str

@router.post("/register", status_code=201)
async def register_user(user: UserRegisterRequest) -> Dict[str, Any]:
    """最小実装: ハードコードでテストをパス"""
    return {
        "user_id": 1,  # ハードコード
        "email": user.email,
        "name": user.name,
        "created_at": "2025-09-18T00:00:00Z"  # ハードコード
    }
```

### 3. Run Tests to Verify Pass
```bash
# Run specific test
pytest tests/test_${module}.py::test_${function} -v

# Expected output:
# PASSED tests/test_users.py::test_user_registration
```

### 4. Verify All Tests Still Pass
```bash
# Run all tests to ensure no regression
pytest tests/ -v --tb=short

# Check coverage (optional)
pytest tests/ --cov=app --cov-report=term-missing
```

### 5. Commit with GREEN Phase Tag
```bash
git add app/
git commit -m "feat(${scope}): minimal implementation for ${description} [${task_id}-GREEN]"
```

## Example Output
```markdown
✅ GREEN Phase Complete for T014

📝 Implementation Created:
- File: app/routers/users.py
- Function: register_user
- Type: Minimal (with hardcoding)

✅ Test Status: PASSING
- test_user_registration: PASSED
- All regression tests: PASSED (42/42)

⚠️ Technical Debt Added:
- Hardcoded user_id: 1
- Hardcoded timestamp
- No database interaction
- No validation logic

📋 Next Step:
Run `/tdd:refactor T014` to improve implementation

💾 Committed:
"feat(users): minimal implementation for user registration [T014-GREEN]"
```

## Minimal Implementation Patterns

### Pattern 1: Hardcode Return Values
```python
def calculate_score():
    return 85.5  # Just return expected value
```

### Pattern 2: Return Input Echo
```python
def process_data(input_data):
    return {"processed": input_data}  # Echo input
```

### Pattern 3: Static Responses
```python
def get_recommendations():
    return [{"id": 1}, {"id": 2}, {"id": 3}]  # Static list
```

## Validation Rules
- ✅ テストがパス → 成功
- ✅ ハードコード使用 → 許容（GREENフェーズ）
- ⚠️ 過剰な実装 → 警告（最小実装を推奨）
- ❌ テストが失敗 → 実装を修正

## Anti-patterns to Avoid
1. **完璧な実装を目指す**: REFACTORフェーズで行う
2. **他のテストを壊す**: リグレッションチェック必須
3. **テストなしで実装**: TDD違反
4. **複雑なロジック追加**: 最小実装の原則違反

## Technical Debt Tracking
```yaml
debt_items:
  - hardcoded_values: ["user_id", "timestamp"]
  - missing_validation: true
  - missing_db_interaction: true
  - missing_error_handling: true

refactor_priority: high
estimated_effort: 2h
```

## Integration with TodoWrite
GREENフェーズ完了時、自動的にTodoWriteで技術負債を追跡: