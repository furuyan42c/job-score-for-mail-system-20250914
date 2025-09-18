# TDD駆動タスクリスト: バイト求人マッチングシステム

**作成日**: 2025-09-18
**方法論**: TDD (Test-Driven Development) - RED→GREEN→REFACTOR
**並列戦略**: 各フェーズ内で並列実行可能
**原則**: テストなしにコードを書かない、最小実装から始める、継続的にリファクタリング

## 🎯 TDD基本原則

### 各タスクの3フェーズ構造
```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  1. RED     │ --> │  2. GREEN   │ --> │ 3. REFACTOR  │
│ テスト作成   │     │  最小実装    │     │   改善       │
│ (必ず失敗)  │     │ (テストパス) │     │ (品質向上)   │
└─────────────┘     └─────────────┘     └──────────────┘
```

### 厳格なルール
1. **テストなしにプロダクションコードを書かない**
2. **失敗するテストを1つずつ書く**
3. **テストをパスする最小限のコードのみ書く**
4. **テストがパスしたらリファクタリング**
5. **常にテストがグリーンの状態を保つ**

---

## 📊 進捗ダッシュボード

```yaml
総タスク数: 195 (65タスク × 3フェーズ)
完了: 0%
RED Phase: 0/65
GREEN Phase: 0/65
REFACTOR Phase: 0/65
```

---

## Phase 1: インフラストラクチャ（データベース・環境設定）

### T001: データベース接続 [TDD-3段階]

#### T001.1 - RED: 接続テスト作成
```python
# tests/test_database_connection.py
import pytest
from app.core.database import get_db_connection

@pytest.mark.asyncio
async def test_database_connection():
    """データベース接続が成功することを確認"""
    conn = await get_db_connection()
    assert conn is not None
    assert conn.is_connected() is True
    await conn.close()

@pytest.mark.asyncio
async def test_database_connection_failure():
    """不正な接続情報で失敗することを確認"""
    with pytest.raises(ConnectionError):
        await get_db_connection("invalid_url")
```
**期待結果**: ❌ FAILED (モジュール未定義)

#### T001.2 - GREEN: 最小実装
```python
# app/core/database.py
async def get_db_connection(url=None):
    # ハードコーディングで最小実装
    return MockConnection(is_connected=True)

class MockConnection:
    def __init__(self, is_connected):
        self._connected = is_connected

    def is_connected(self):
        return self._connected

    async def close(self):
        pass
```
**期待結果**: ✅ PASSED

#### T001.3 - REFACTOR: 実際の接続実装
```python
# app/core/database.py
import asyncpg
from app.core.config import settings

async def get_db_connection(url=None):
    """本番用PostgreSQL接続"""
    db_url = url or settings.DATABASE_URL
    try:
        conn = await asyncpg.connect(db_url)
        return conn
    except Exception as e:
        raise ConnectionError(f"Database connection failed: {e}")
```
**期待結果**: ✅ PASSED（実際のDBで動作）

---

### T002: スキーママイグレーション [TDD-3段階]

#### T002.1 - RED: マイグレーションテスト作成
```python
# tests/test_migrations.py
@pytest.mark.asyncio
async def test_initial_migration():
    """初期マイグレーションでテーブルが作成される"""
    await run_migration("001_initial_schema.sql")

    tables = await get_table_list()
    assert "jobs" in tables
    assert "users" in tables
    assert "user_job_mapping" in tables
    assert len(tables) >= 13  # 最低13テーブル
```
**期待結果**: ❌ FAILED (run_migration未定義)

#### T002.2 - GREEN: 最小マイグレーション実装
```python
# app/core/migrations.py
async def run_migration(filename):
    # 最小実装：ダミーテーブルリストを返す
    return ["jobs", "users", "user_job_mapping"] + ["table" + str(i) for i in range(10)]
```
**期待結果**: ✅ PASSED

#### T002.3 - REFACTOR: 実際のマイグレーション
```python
# app/core/migrations.py
async def run_migration(filename):
    """SQLファイルを実行してマイグレーション"""
    conn = await get_db_connection()
    try:
        sql_path = f"migrations/{filename}"
        with open(sql_path, 'r') as f:
            await conn.execute(f.read())
    finally:
        await conn.close()
```

---

## Phase 2: モデル層（データモデル定義）

### T003: Jobモデル [TDD-3段階]

#### T003.1 - RED: モデルバリデーションテスト
```python
# tests/test_job_model.py
from app.models.job import Job

def test_job_model_validation():
    """Jobモデルのバリデーション"""
    # 必須フィールドなしで失敗
    with pytest.raises(ValidationError):
        job = Job()

    # 有効なデータで成功
    job = Job(
        job_id=1,
        endcl_cd="COMP_001",
        fee=1000,
        title="テスト求人"
    )
    assert job.job_id == 1
    assert job.fee > 500  # fee制約

def test_job_fee_constraint():
    """fee > 500 制約のテスト"""
    with pytest.raises(ValidationError):
        job = Job(job_id=1, fee=500)  # 500以下は無効
```
**期待結果**: ❌ FAILED (Jobクラス未定義)

#### T003.2 - GREEN: 最小モデル実装
```python
# app/models/job.py
class Job:
    def __init__(self, job_id=None, endcl_cd=None, fee=None, title=None):
        if job_id is None:
            raise ValidationError("job_id required")
        if fee and fee <= 500:
            raise ValidationError("fee must be > 500")
        self.job_id = job_id
        self.fee = fee
        self.endcl_cd = endcl_cd
        self.title = title

class ValidationError(Exception):
    pass
```
**期待結果**: ✅ PASSED

#### T003.3 - REFACTOR: Pydanticモデルに改善
```python
# app/models/job.py
from pydantic import BaseModel, Field, validator

class Job(BaseModel):
    job_id: int
    endcl_cd: str
    company_name: str
    title: str
    fee: int = Field(..., gt=500)
    # その他フィールド...

    @validator('fee')
    def validate_fee(cls, v):
        if v <= 500:
            raise ValueError('fee must be greater than 500')
        return v
```

---

## Phase 3: サービス層（ビジネスロジック）

### T004: 基本スコアリング [TDD-3段階]

#### T004.1 - RED: スコアリングテスト作成
```python
# tests/test_basic_scoring.py
@pytest.mark.asyncio
async def test_basic_scoring_calculation():
    """基本スコア計算のテスト"""
    job = create_test_job(fee=1000, min_salary=1200)
    user = create_test_user(pref_cd="13")

    score = await calculate_basic_score(job, user)

    assert 0 <= score <= 100
    assert score > 50  # fee > 500なので中程度以上のスコア

@pytest.mark.asyncio
async def test_fee_threshold():
    """fee <= 500の求人はスコア0"""
    job = create_test_job(fee=500)
    score = await calculate_basic_score(job, None)
    assert score == 0.0
```
**期待結果**: ❌ FAILED (calculate_basic_score未定義)

#### T004.2 - GREEN: 最小スコアリング実装
```python
# app/services/scoring.py
async def calculate_basic_score(job, user):
    """最小実装：feeベースの単純スコア"""
    if job.fee <= 500:
        return 0.0
    return 60.0  # 固定スコア
```
**期待結果**: ✅ PASSED

#### T004.3 - REFACTOR: 実際のスコアリングロジック
```python
# app/services/scoring.py
async def calculate_basic_score(job, user, area_stats=None):
    """実際のスコアリング実装"""
    if job.fee <= 500:
        return 0.0

    # 時給のZ-score正規化
    wage_score = calculate_wage_zscore(job, area_stats)

    # 企業人気度（360日）
    popularity = await get_company_popularity_360d(job.endcl_cd)

    # 重み付け合計
    score = (
        wage_score * 0.4 +
        normalize_fee(job.fee) * 0.3 +
        popularity * 0.3
    )

    return min(100.0, max(0.0, score))
```

---

## Phase 4: API層（エンドポイント）

### T005: バッチトリガーAPI [TDD-3段階]

#### T005.1 - RED: 契約テスト作成
```python
# tests/contract/test_batch_trigger.py
def test_batch_trigger_endpoint(client):
    """POST /batch/trigger の契約テスト"""
    response = client.post(
        "/api/v1/batch/trigger",
        json={"batch_type": "daily_matching"}
    )

    assert response.status_code == 202
    assert "batch_id" in response.json()
    assert response.json()["status"] in ["pending", "running"]
```
**期待結果**: ❌ FAILED (404 Not Found)

#### T005.2 - GREEN: 最小エンドポイント実装
```python
# app/routers/batch.py
@router.post("/trigger", status_code=202)
async def trigger_batch(batch_type: str):
    """最小実装：固定レスポンス"""
    return {
        "batch_id": 1,
        "job_type": batch_type,
        "status": "pending"
    }
```
**期待結果**: ✅ PASSED

#### T005.3 - REFACTOR: 実際のバッチ処理
```python
# app/routers/batch.py
@router.post("/trigger", status_code=202)
async def trigger_batch(
    request: BatchTriggerRequest,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """実際のバッチ処理実装"""
    batch_service = BatchService(db)
    batch_job = await batch_service.create_batch_job(
        batch_type=request.batch_type,
        initiated_by=request.user_id
    )

    # バックグラウンドで実行
    background_tasks.add_task(
        batch_service.execute_batch,
        batch_job.batch_id
    )

    return BatchJobResponse.from_orm(batch_job)
```

---

## Phase 5: 統合テスト

### T006: データフロー統合テスト [TDD-3段階]

#### T006.1 - RED: エンドツーエンドテスト作成
```python
# tests/integration/test_data_flow.py
@pytest.mark.integration
async def test_complete_data_flow():
    """CSV→スコアリング→マッチング→メールの完全フロー"""
    # 1. CSVインポート
    job_ids = await import_jobs_from_csv("test_jobs.csv")
    assert len(job_ids) == 100

    # 2. スコアリング実行
    scores = await calculate_all_scores(user_id=1, job_ids=job_ids)
    assert all(0 <= s.score <= 100 for s in scores)

    # 3. マッチング生成
    matches = await generate_matching(user_id=1, scores=scores)
    assert len(matches) == 40  # 40件選定

    # 4. メール生成
    email = await generate_email(user_id=1, matches=matches)
    assert email.status == "generated"
    assert len(email.sections) == 6
```
**期待結果**: ❌ FAILED (関数未定義)

#### T006.2 - GREEN: モック統合実装
```python
# tests/integration/mock_integration.py
async def import_jobs_from_csv(filename):
    return list(range(100))

async def calculate_all_scores(user_id, job_ids):
    return [MockScore(job_id=id, score=50.0) for id in job_ids]

async def generate_matching(user_id, scores):
    return scores[:40]

async def generate_email(user_id, matches):
    return MockEmail(status="generated", sections=[{} for _ in range(6)])
```
**期待結果**: ✅ PASSED

#### T006.3 - REFACTOR: 実際の統合実装
```python
# app/services/integration.py
async def complete_matching_pipeline(csv_file, user_ids):
    """本番用統合パイプライン"""
    async with get_db() as db:
        # トランザクション管理
        async with db.begin():
            # 実際のサービスを呼び出し
            job_service = JobService(db)
            scoring_service = ScoringService(db)
            matching_service = MatchingService(db)
            email_service = EmailService(db)

            jobs = await job_service.import_csv(csv_file)

            for user_id in user_ids:
                scores = await scoring_service.calculate_batch(user_id, jobs)
                matches = await matching_service.generate(user_id, scores)
                email = await email_service.create(user_id, matches)

            return {"processed": len(user_ids)}
```

---

## 📋 TDDチェックリスト

### 各タスク実行前の確認事項
- [ ] テストファイルを最初に作成したか？
- [ ] テストが失敗することを確認したか？（RED）
- [ ] 最小限のコードでテストをパスさせたか？（GREEN）
- [ ] リファクタリング後もテストがパスするか？（REFACTOR）
- [ ] コミットメッセージにフェーズを明記したか？

### コミットメッセージ規約
```bash
# RED Phase
git commit -m "test(T001): Add database connection tests [RED]"

# GREEN Phase
git commit -m "feat(T001): Add minimal database connection [GREEN]"

# REFACTOR Phase
git commit -m "refactor(T001): Implement actual PostgreSQL connection [REFACTOR]"
```

---

## 📊 メトリクス追跡

### TDDサイクル時間
| タスク | RED | GREEN | REFACTOR | 合計 |
|--------|-----|-------|----------|------|
| T001 | 15分 | 10分 | 30分 | 55分 |
| T002 | 20分 | 15分 | 45分 | 80分 |
| T003 | 10分 | 10分 | 20分 | 40分 |

### テストカバレッジ目標
- RED Phase完了時: 0% （テストのみ存在）
- GREEN Phase完了時: 60%（最小実装）
- REFACTOR Phase完了時: 90%（完全実装）

---

## 🚫 アンチパターン警告

### やってはいけないこと
1. **テストなしでコードを書く**
   ```python
   # ❌ BAD: テストなしで実装
   def calculate_score(job):
       return job.fee * 0.1 + job.salary * 0.5
   ```

2. **複数のテストを一度に書く**
   ```python
   # ❌ BAD: 一度に多くのテスト
   def test_everything():
       test_connection()
       test_migration()
       test_model()
   ```

3. **テストをパスする以上の実装**
   ```python
   # ❌ BAD: GREEN phaseで完全実装
   def get_user(id):
       # 最小実装で良いのに...
       user = db.query(User).filter_by(id=id).first()
       user.calculate_preferences()
       user.update_last_access()
       return user
   ```

### 正しいアプローチ
1. **1つずつテストを書く**
2. **テストが失敗することを確認**
3. **最小限のコードで緑にする**
4. **リファクタリングで改善**

---

## 🎯 成功基準

### Phase完了条件

#### RED Phase ✅
- テストファイルが存在する
- テストが実行できる
- テストが失敗する（期待通り）
- 失敗理由が明確

#### GREEN Phase ✅
- すべてのテストがパスする
- コードは最小限
- ハードコーディングOK
- 重複OK

#### REFACTOR Phase ✅
- テストが引き続きパスする
- コードが整理されている
- 重複が除去されている
- パフォーマンスが改善されている

---

## 📅 実行スケジュール

### Week 1: インフラ＋モデル（T001-T020）
- Day 1-2: RED Phase（全テスト作成）
- Day 3-4: GREEN Phase（最小実装）
- Day 5: REFACTOR Phase（改善）

### Week 2: サービス＋API（T021-T040）
- Day 1-2: RED Phase
- Day 3-4: GREEN Phase
- Day 5: REFACTOR Phase

### Week 3: 統合＋E2E（T041-T065）
- Day 1-2: RED Phase
- Day 3-4: GREEN Phase
- Day 5: REFACTOR Phase

---

*このタスクリストは厳格なTDD原則に従います。テストなしにコードを書くことは許されません。*