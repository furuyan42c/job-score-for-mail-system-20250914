"""
PyTest設定とフィクスチャ

テスト全体で使用される共通設定とフィクスチャを定義
"""

import pytest
import asyncio
import hashlib
import random
from typing import AsyncGenerator, Generator, List, Dict, Any
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock

from app.main import app
from app.core.database import get_db, Base
from app.core.config import TestSettings
from app.models.common import SalaryType, ActionType, EmploymentType
from app.models.jobs import JobFeatures, JobSalary, JobWorkConditions, JobCategory, JobSEO, Job
from app.models.users import UserPreferences, UserBehaviorStats, User, UserAction


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """イベントループフィクスチャ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """テストデータベースエンジン"""
    settings = TestSettings()
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True
    )

    # テストテーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # テストテーブル削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """テストデータベースセッション"""
    TestSession = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(test_db: AsyncSession):
    """データベース依存性注入のオーバーライド"""
    async def _override_get_db():
        yield test_db

    return _override_get_db


@pytest.fixture
def test_client(override_get_db) -> TestClient:
    """テストクライアント"""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """非同期テストクライアント"""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """サンプルユーザーデータ"""
    return {
        "email": "test@example.com",
        "age_group": "20代前半",
        "gender": "male",
        "estimated_pref_cd": "13",
        "estimated_city_cd": "13101"
    }


@pytest.fixture
def sample_job_data():
    """サンプル求人データ"""
    return {
        "endcl_cd": "TEST001",
        "company_name": "テスト株式会社",
        "application_name": "テスト求人",
        "location": {
            "prefecture_code": "13",
            "city_code": "13101",
            "address": "東京都千代田区丸の内1-1-1"
        },
        "salary": {
            "salary_type": "hourly",
            "min_salary": 1200,
            "max_salary": 1500,
            "fee": 1000
        },
        "work_conditions": {
            "hours": "9:00-18:00",
            "work_days": "月-金",
            "employment_type_cd": 1
        },
        "category": {
            "occupation_cd1": 100,
            "occupation_cd2": 101
        },
        "features": {
            "feature_codes": ["D01", "N01"],
            "has_daily_payment": True,
            "has_no_experience": True
        },
        "seo": {
            "description": "未経験歓迎のテスト求人です",
            "search_keywords": ["テスト", "未経験", "日払い"]
        }
    }


@pytest.fixture
def auth_headers():
    """認証ヘッダー"""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


# ===== 追加のフィクスチャ =====

@pytest.fixture
def mock_email_hash():
    """モックメールハッシュ生成"""
    def _generate_hash(email: str) -> str:
        return hashlib.sha256(email.encode()).hexdigest()[:16]
    return _generate_hash


@pytest.fixture
def sample_user_create_data():
    """ユーザー作成用サンプルデータ"""
    return {
        "email": "test@example.com",
        "age_group": "20代前半",
        "gender": "male",
        "estimated_pref_cd": "13",
        "estimated_city_cd": "13101",
        "preferences": {
            "preferred_work_styles": ["part_time", "flexible"],
            "preferred_categories": [100, 200],
            "preferred_salary_min": 1200,
            "location_preference_radius": 10,
            "preferred_areas": ["13101", "13102"]
        }
    }


@pytest.fixture
def sample_multiple_users(mock_email_hash):
    """複数ユーザーのサンプルデータ"""
    users = []
    prefectures = ["13", "27", "40"]
    age_groups = ["20代前半", "20代後半", "30代前半"]
    genders = ["male", "female", "other"]

    for i in range(10):
        email = f"user{i}@example.com"
        users.append({
            "email": email,
            "email_hash": mock_email_hash(email),
            "age_group": random.choice(age_groups),
            "gender": random.choice(genders),
            "estimated_pref_cd": random.choice(prefectures),
            "estimated_city_cd": f"{random.choice(prefectures)}101",
            "registration_date": date.today() - timedelta(days=random.randint(1, 365)),
            "is_active": random.choice([True, True, True, False]),  # 75% active
        })
    return users


@pytest.fixture
def sample_job_features():
    """求人特徴サンプルデータ"""
    return {
        "feature_codes": ["D01", "N01", "T01"],
        "has_daily_payment": True,
        "has_weekly_payment": False,
        "has_no_experience": True,
        "has_student_welcome": False,
        "has_remote_work": False,
        "has_transportation": True,
        "has_high_income": False
    }


@pytest.fixture
def sample_job_salary():
    """求人給与サンプルデータ"""
    return {
        "salary_type": "hourly",
        "min_salary": 1200,
        "max_salary": 1500,
        "fee": 1000
    }


@pytest.fixture
def sample_multiple_jobs():
    """複数求人のサンプルデータ"""
    jobs = []
    companies = ["株式会社テスト", "サンプル商事", "テスト工業", "デモ株式会社"]
    prefectures = ["13", "27", "40"]
    salary_types = ["hourly", "daily", "monthly"]

    for i in range(20):
        jobs.append({
            "endcl_cd": f"TEST{i:03d}",
            "company_name": random.choice(companies),
            "application_name": f"テスト求人{i+1}",
            "location": {
                "prefecture_code": random.choice(prefectures),
                "city_code": f"{random.choice(prefectures)}101",
                "address": f"テスト市テスト区{i+1}-1-1"
            },
            "salary": {
                "salary_type": random.choice(salary_types),
                "min_salary": random.randint(1000, 2000),
                "max_salary": random.randint(2000, 3000),
                "fee": random.randint(500, 2000)
            },
            "work_conditions": {
                "hours": "9:00-18:00",
                "work_days": "月-金",
                "employment_type_cd": random.randint(1, 4)
            },
            "category": {
                "occupation_cd1": random.randint(100, 900),
                "occupation_cd2": random.randint(101, 999)
            },
            "features": {
                "feature_codes": random.sample(["D01", "W01", "N01", "S01", "R01", "T01"], k=random.randint(1, 3)),
                "has_daily_payment": random.choice([True, False]),
                "has_no_experience": random.choice([True, False])
            },
            "seo": {
                "description": f"テスト求人{i+1}の説明文",
                "search_keywords": [f"keyword{i}", "テスト", "求人"]
            },
            "posting_date": datetime.now() - timedelta(days=random.randint(0, 30)),
            "is_active": random.choice([True, True, True, False])  # 75% active
        })
    return jobs


@pytest.fixture
def sample_user_actions():
    """ユーザー行動履歴サンプルデータ"""
    actions = []
    action_types = [ActionType.VIEW, ActionType.CLICK, ActionType.APPLY, ActionType.EMAIL_OPEN]
    sources = ["web", "mobile", "email"]

    for i in range(50):
        actions.append({
            "user_id": random.randint(1, 10),
            "job_id": random.randint(1, 20) if random.random() > 0.1 else None,
            "action_type": random.choice(action_types),
            "action_timestamp": datetime.now() - timedelta(
                hours=random.randint(0, 24*7)  # Last week
            ),
            "source": random.choice(sources),
            "session_id": f"session_{random.randint(1000, 9999)}",
            "device_type": random.choice(["desktop", "mobile", "tablet"]),
            "action_metadata": {
                "page": random.choice(["home", "search", "detail"]),
                "position": random.randint(1, 20)
            }
        })
    return actions


@pytest.fixture
def sample_scoring_data():
    """スコアリングデータサンプル"""
    return {
        "job_id": 1,
        "user_id": 1,
        "basic_score": 75.5,
        "seo_score": 82.3,
        "personalized_score_base": 68.7,
        "composite_score": 78.1,
        "location_score": 90.0,
        "salary_score": 85.0,
        "category_match_score": 70.0,
        "feature_match_score": 60.0
    }


@pytest.fixture
def mock_database_session():
    """モックデータベースセッション"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client():
    """モックRedisクライアント"""
    redis_mock = Mock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.expire = AsyncMock(return_value=True)
    return redis_mock


@pytest.fixture
def benchmark_config():
    """パフォーマンステスト設定"""
    return {
        "min_rounds": 10,
        "max_time": 5.0,
        "warmup": True,
        "warmup_iterations": 2
    }


@pytest.fixture
def sample_pagination_params():
    """ページネーションパラメータサンプル"""
    return {
        "page": 1,
        "size": 20
    }


@pytest.fixture
def sample_search_filters():
    """検索フィルターサンプル"""
    return {
        "keyword": "テスト",
        "prefecture_codes": ["13", "27"],
        "occupation_codes": [100, 200],
        "salary_range": {
            "min_salary": 1000,
            "max_salary": 2000,
            "salary_type": "hourly"
        },
        "feature_codes": ["D01", "N01"],
        "is_active": True
    }


@pytest.fixture
def sample_error_cases():
    """エラーケーステストデータ"""
    return {
        "invalid_email": "not-an-email",
        "invalid_salary": -100,
        "invalid_score": 150.0,
        "invalid_date_range": {
            "start_date": "2024-12-31",
            "end_date": "2024-01-01"
        },
        "missing_required_field": {},
        "sql_injection": "'; DROP TABLE users; --",
        "xss_payload": "<script>alert('xss')</script>"
    }


@pytest.fixture
def performance_test_data():
    """パフォーマンステスト用大量データ"""
    def _generate_data(count: int, data_type: str) -> List[Dict[str, Any]]:
        if data_type == "users":
            return [
                {
                    "email": f"perf_user_{i}@example.com",
                    "age_group": "20代前半",
                    "gender": "male"
                } for i in range(count)
            ]
        elif data_type == "jobs":
            return [
                {
                    "endcl_cd": f"PERF{i:05d}",
                    "company_name": f"Performance Test Co. {i}",
                    "application_name": f"Performance Job {i}",
                    "location": {"prefecture_code": "13"},
                    "salary": {"salary_type": "hourly", "min_salary": 1200, "fee": 1000},
                    "work_conditions": {"employment_type_cd": 1},
                    "category": {"occupation_cd1": 100}
                } for i in range(count)
            ]
        return []

    return _generate_data


@pytest.fixture(autouse=True)
async def cleanup_test_data(test_db):
    """テスト後のクリーンアップ"""
    yield
    # テスト後のクリーンアップ処理
    try:
        await test_db.rollback()
    except Exception:
        pass


# PyTest設定
def pytest_configure(config):
    """PyTest設定"""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "benchmark: mark test as benchmark test")


def pytest_collection_modifyitems(config, items):
    """テストアイテムの設定変更"""
    for item in items:
        # スローテストにマーク追加
        if "benchmark" in item.keywords:
            item.add_marker(pytest.mark.slow)

        # 統合テストディレクトリのテストにマーク追加
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)