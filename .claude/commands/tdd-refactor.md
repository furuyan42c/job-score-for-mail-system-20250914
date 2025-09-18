# TDD: REFACTOR Phase Command
> Improve code quality while keeping tests green

## Usage
```bash
/tdd:refactor <task-id> [--focus <aspect>] [--validate]
```

## Description
REFACTORフェーズ: テストを常にパスさせながら、コード品質を改善します。ハードコードを除去し、実際のビジネスロジックを実装します。

## Process
1. GREENフェーズの確認
2. 技術負債の特定
3. リファクタリング実施
4. テストが継続的にパスすることを確認
5. パフォーマンス・品質メトリクス測定
6. コミットメッセージを生成

## Options
- `--focus`: 特定の側面に焦点（performance|security|maintainability|all）
- `--validate`: リファクタリング後の品質検証

## Refactoring Steps

### 1. Identify Technical Debt
```python
def analyze_technical_debt(task_id):
    """Identify areas for improvement"""
    debt_items = {
        "hardcoded_values": find_hardcoded_values(),
        "code_duplication": detect_duplication(),
        "complex_methods": find_high_complexity(),
        "missing_validation": check_validation_gaps(),
        "performance_issues": analyze_performance()
    }
    return prioritize_debt_items(debt_items)
```

### 2. Refactor Implementation
```python
# Example for T014: User Registration (Refactored)
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import hash_password
from app.models.users import User
from app.schemas.users import UserRegisterRequest, UserResponse
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/register", status_code=201, response_model=UserResponse)
async def register_user(
    user_data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """本番実装: 実際のビジネスロジック"""

    # 1. バリデーション
    existing_user = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # 2. パスワードハッシュ化
    hashed_password = await hash_password(user_data.password)

    # 3. ユーザー作成
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password,
        created_at=datetime.utcnow(),
        is_active=True
    )

    # 4. データベース保存
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 5. レスポンス返却
    return UserResponse.from_orm(new_user)
```

### 3. Extract Reusable Components
```python
# Extract validation logic
class UserValidator:
    @staticmethod
    async def validate_unique_email(email: str, db: AsyncSession):
        """Email重複チェックを再利用可能に"""
        existing = await UserRepository.find_by_email(email, db)
        if existing:
            raise EmailAlreadyExistsError(email)

# Extract repository pattern
class UserRepository:
    @staticmethod
    async def create(user_data: dict, db: AsyncSession) -> User:
        """ユーザー作成ロジックを分離"""
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
```

### 4. Continuous Test Verification
```bash
# Run tests after each refactoring step
pytest tests/test_users.py -v --tb=short

# Run with watch mode for continuous feedback
pytest-watch tests/ -- -v
```

### 5. Quality Metrics
```python
def measure_quality_improvements():
    """品質向上を測定"""
    metrics = {
        "cyclomatic_complexity": calculate_complexity(),
        "code_coverage": get_test_coverage(),
        "duplication_ratio": calculate_duplication(),
        "maintainability_index": calculate_maintainability(),
        "performance_score": benchmark_performance()
    }
    return metrics
```

### 6. Commit with REFACTOR Phase Tag
```bash
git add app/
git commit -m "refactor(${scope}): improve ${description} implementation [${task_id}-REFACTOR]"
```

## Example Output
```markdown
✅ REFACTOR Phase Complete for T014

📝 Improvements Made:
- Removed hardcoded values (3 instances)
- Added input validation
- Implemented database persistence
- Added error handling
- Extracted reusable components

📊 Quality Metrics:
- Code Coverage: 85% → 92% (+7%)
- Complexity: 8 → 4 (-50%)
- Duplication: 15% → 3% (-12%)
- Performance: 120ms → 45ms (-62%)

✅ Test Status: ALL PASSING
- Unit tests: 15/15 ✅
- Integration tests: 8/8 ✅
- No regression detected

🏗️ Architecture Improvements:
- Repository pattern implemented
- Validation layer added
- Service layer separation
- Dependency injection utilized

💾 Committed:
"refactor(users): improve user registration implementation [T014-REFACTOR]"
```

## Refactoring Patterns

### Pattern 1: Remove Hardcoding
```python
# Before
return {"id": 1, "name": "test"}

# After
return {"id": generate_uuid(), "name": user.name}
```

### Pattern 2: Extract Method
```python
# Before
def process(data):
    # 20 lines of validation
    # 30 lines of processing
    # 15 lines of formatting

# After
def process(data):
    validated = self._validate(data)
    processed = self._transform(validated)
    return self._format(processed)
```

### Pattern 3: Dependency Injection
```python
# Before
def save_user():
    db = create_database_connection()  # Direct dependency

# After
def save_user(db: AsyncSession = Depends(get_db)):  # Injected
```

## Validation Checklist
- [ ] All tests still pass
- [ ] No new test failures
- [ ] Code coverage maintained/improved
- [ ] Performance not degraded
- [ ] No security vulnerabilities introduced
- [ ] Code complexity reduced
- [ ] Documentation updated

## Anti-patterns to Avoid
1. **テストを変更する**: テストは仕様、変更禁止
2. **機能追加**: リファクタリングは改善のみ
3. **一度に全部変更**: 段階的に改善
4. **テスト実行を怠る**: 継続的検証必須

## Performance Benchmarks
```yaml
before_refactor:
  response_time: 120ms
  memory_usage: 45MB
  cpu_usage: 15%

after_refactor:
  response_time: 45ms  # -62.5%
  memory_usage: 32MB   # -28.8%
  cpu_usage: 8%        # -46.6%
```

## Next Steps
REFACTORフェーズ完了後:
1. 品質メトリクスを記録
2. 次のタスクのREDフェーズへ
3. または統合テストの実行