# TDD: RED Phase Command
> Create failing tests first - the foundation of TDD

## Usage
```bash
/tdd:red <task-id> [--file <test-file>] [--describe]
```

## Description
REDフェーズ: テストファーストアプローチの実装。必ず失敗するテストを先に作成し、実装前の期待動作を定義します。

## Process
1. タスク仕様を分析
2. テストファイルを作成/更新
3. 失敗するテストを実装
4. テスト実行して失敗を確認
5. コミットメッセージを生成

## Options
- `--file`: 特定のテストファイルを指定
- `--describe`: テスト仕様の詳細説明を追加

## Implementation Steps

### 1. Analyze Task Requirements
```python
# タスクIDから要件を取得
task = get_task_by_id(task_id)
requirements = analyze_requirements(task)
```

### 2. Generate Test Structure
```python
def generate_test_structure(task_id, requirements):
    """
    Generate test structure based on requirements
    """
    test_cases = []

    # 正常系テスト
    test_cases.append(create_happy_path_test(requirements))

    # エッジケース
    test_cases.append(create_edge_case_tests(requirements))

    # エラーケース
    test_cases.append(create_error_case_tests(requirements))

    return test_cases
```

### 3. Create Failing Test
```python
# Example for T014: User Registration
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_user_registration():
    """Test user registration endpoint - RED phase"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        }

        # Act
        response = await client.post("/api/v1/users/register", json=user_data)

        # Assert - These will fail initially
        assert response.status_code == 201
        assert "user_id" in response.json()
        assert response.json()["email"] == user_data["email"]
```

### 4. Verify Test Fails
```bash
# Run test and confirm failure
pytest tests/test_${module}.py::test_${function} -v

# Expected output:
# FAILED tests/test_users.py::test_user_registration - AssertionError
```

### 5. Commit with RED Phase Tag
```bash
git add tests/
git commit -m "test(${scope}): add failing test for ${description} [${task_id}-RED]"
```

## Example Output
```markdown
✅ RED Phase Complete for T014

📝 Test Created:
- File: tests/test_users.py
- Function: test_user_registration
- Cases: 3 (happy path, edge cases, error cases)

🔴 Test Status: FAILING (as expected)
- Status Code: 404 (expected 201)
- Missing endpoint implementation

📋 Next Step:
Run `/tdd:green T014` to implement minimal code

💾 Committed:
"test(users): add failing test for user registration [T014-RED]"
```

## Validation Rules
- ❌ テストなしで実装開始 → エラー
- ❌ テストがパスしてしまう → 警告（テストが不十分）
- ✅ テストが期待通り失敗 → 次フェーズへ

## Anti-patterns to Avoid
1. **実装を先に書く**: TDD違反
2. **テストを後回し**: 根本的な誤り
3. **最初からパスするテスト**: 無意味なテスト
4. **テスト内容が曖昧**: 仕様が不明確

## Integration with Tasks
このコマンドは`tasks_tdd.md`の各タスクのREDフェーズに対応します。