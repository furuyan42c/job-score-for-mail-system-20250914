"""
T048: データベーストランザクション統合テスト
トランザクション管理とエラー時のロールバック検証

This integration test validates database transaction management:
1. Transaction Rollback: Error scenarios trigger proper rollback
2. Concurrent Access: Multiple simultaneous database operations
3. Data Consistency: ACID properties maintained under load
4. Deadlock Handling: Proper deadlock detection and recovery
5. Connection Pool: Database connection pool behavior under stress

Dependencies: Database layer, SQLAlchemy ORM, Connection pooling
Standards: ACID compliance, proper error handling, concurrent safety
"""

import pytest
import asyncio
import uuid
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, OperationalError, DatabaseError
from sqlalchemy import text, select, update, delete
from sqlalchemy.pool import StaticPool

from app.core.database import get_async_session, get_db, Base, ConnectionPoolStats
from app.core.config import TestSettings
from app.models.users import User, UserProfile, UserPreferences
from app.models.jobs import Job, JobSalary, JobLocation, JobCategory
from app.models.matching import MatchingScore
from app.models.common import ActionType
from app.services.users import UserService
from app.services.jobs import JobService
from app.services.matching import MatchingService

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# Transaction test targets
TRANSACTION_TEST_TARGETS = {
    'rollback_success_rate': 100,        # Must rollback 100% on errors
    'concurrent_operations_max': 50,     # 50 concurrent database operations
    'deadlock_resolution_time': 5000,    # 5 seconds max deadlock resolution
    'connection_pool_efficiency': 90,    # 90% pool efficiency under load
    'transaction_isolation_compliance': 100,  # 100% isolation compliance
    'data_consistency_verification': 100,     # 100% data consistency
}

# Test data volumes for stress testing
STRESS_TEST_VOLUMES = {
    'concurrent_users': 25,
    'concurrent_jobs': 50,
    'transactions_per_user': 10,
    'max_test_duration': 30,  # seconds
}

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
async def transaction_test_engine():
    """Dedicated test engine for transaction testing"""
    settings = TestSettings()

    # Create engine with specific transaction settings
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True,
        pool_size=20,  # Larger pool for concurrent testing
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=3600,
        # Transaction-specific settings
        isolation_level="READ_COMMITTED",
        connect_args={
            "statement_timeout": 30000,  # 30 second timeout
            "lock_timeout": 10000,       # 10 second lock timeout
        }
    )

    # Initialize test schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def transaction_test_session(transaction_test_engine):
    """Test session for transaction testing"""
    TestSession = sessionmaker(
        transaction_test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with TestSession() as session:
        yield session

@pytest.fixture
def sample_transaction_data():
    """Sample data for transaction testing"""
    return {
        "users": [
            {
                "email": f"tx_user_{i}_{uuid.uuid4().hex[:8]}@example.com",
                "age_group": "20代前半",
                "gender": "male",
                "estimated_pref_cd": "13",
                "estimated_city_cd": "13101"
            } for i in range(20)
        ],
        "jobs": [
            {
                "endcl_cd": f"TX_JOB_{i}_{uuid.uuid4().hex[:8]}",
                "company_name": f"Transaction Test Co {i}",
                "application_name": f"Transaction Job {i}",
                "location": {"prefecture_code": "13", "city_code": "13101"},
                "salary": {"salary_type": "hourly", "min_salary": 1200, "fee": 1000},
                "work_conditions": {"employment_type_cd": 1},
                "category": {"occupation_cd1": 100 + i}
            } for i in range(30)
        ]
    }

# ============================================================================
# TRANSACTION ROLLBACK TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_rollback_on_error(transaction_test_session: AsyncSession):
    """
    T048-RED: エラー時トランザクションロールバックテスト（失敗するテスト）

    This test MUST FAIL initially to follow TDD RED phase.
    Tests: Database operations rollback properly when errors occur
    """

    # Step 1: Start transaction and create valid data
    async with transaction_test_session.begin():

        # Create a user (THIS WILL FAIL - User model not properly configured for transactions)
        user_data = {
            "email": f"rollback_test_{uuid.uuid4().hex[:8]}@example.com",
            "age_group": "20代前半",
            "gender": "male",
            "estimated_pref_cd": "13",
            "estimated_city_cd": "13101",
            "registration_date": datetime.now().date()
        }

        user = User(**user_data)
        transaction_test_session.add(user)
        await transaction_test_session.flush()  # Get user ID

        # EXPECTED TO FAIL: User creation not properly implemented for transactions
        assert user.id is not None, "User should be created and have an ID"

        # Step 2: Create related data that will cause constraint violation
        # Attempt to create duplicate user with same email (should fail)
        duplicate_user = User(**user_data)  # Same email - constraint violation
        transaction_test_session.add(duplicate_user)

        # THIS SHOULD FAIL and trigger rollback
        with pytest.raises(IntegrityError):
            await transaction_test_session.commit()

    # Step 3: Verify rollback occurred (THIS WILL FAIL)
    # Check that original user was also rolled back
    async with transaction_test_session.begin():
        result = await transaction_test_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        found_user = result.scalar_one_or_none()

        # EXPECTED TO FAIL: Rollback mechanism not properly implemented
        assert found_user is None, "User should be rolled back after transaction failure"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nested_transaction_rollback(transaction_test_session: AsyncSession):
    """
    T048-RED: ネストトランザクションロールバックテスト（失敗するテスト）

    This test MUST FAIL initially - nested transaction handling not implemented
    Tests: Nested transactions and savepoint rollback
    """

    user_email = f"nested_tx_test_{uuid.uuid4().hex[:8]}@example.com"

    try:
        async with transaction_test_session.begin():
            # Outer transaction: Create user
            user = User(
                email=user_email,
                age_group="20代前半",
                gender="male",
                estimated_pref_cd="13",
                estimated_city_cd="13101",
                registration_date=datetime.now().date()
            )
            transaction_test_session.add(user)
            await transaction_test_session.flush()

            # EXPECTED TO FAIL: User creation not implemented
            assert user.id is not None

            try:
                # Inner transaction (savepoint): Create job
                async with transaction_test_session.begin_nested():
                    job = Job(
                        endcl_cd=f"NESTED_JOB_{uuid.uuid4().hex[:8]}",
                        company_name="Nested Test Company",
                        application_name="Nested Test Job",
                        posting_date=datetime.now(),
                        is_active=True
                    )
                    transaction_test_session.add(job)
                    await transaction_test_session.flush()

                    # Force error in nested transaction
                    # Create invalid job with constraint violation
                    invalid_job = Job(
                        endcl_cd=job.endcl_cd,  # Duplicate endcl_cd
                        company_name="Invalid Job",
                        application_name="Should Fail",
                        posting_date=datetime.now(),
                        is_active=True
                    )
                    transaction_test_session.add(invalid_job)

                    # THIS SHOULD FAIL and rollback nested transaction only
                    await transaction_test_session.commit()

            except IntegrityError:
                # Expected: nested transaction should be rolled back
                pass

            # Outer transaction should still be valid
            await transaction_test_session.commit()

    except Exception as e:
        await transaction_test_session.rollback()
        pytest.fail(f"Outer transaction failed unexpectedly: {e}")

    # Verify user exists but job doesn't (THIS WILL FAIL)
    async with transaction_test_session.begin():
        # EXPECTED TO FAIL: Nested transaction handling not implemented
        user_result = await transaction_test_session.execute(
            select(User).where(User.email == user_email)
        )
        found_user = user_result.scalar_one_or_none()
        assert found_user is not None, "User should exist after nested rollback"

        job_result = await transaction_test_session.execute(
            select(Job).where(Job.endcl_cd.like("NESTED_JOB_%"))
        )
        found_job = job_result.scalar_one_or_none()
        assert found_job is None, "Job should not exist after nested rollback"


# ============================================================================
# CONCURRENT ACCESS TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_database_operations(transaction_test_engine):
    """
    T048-RED: 並行データベース操作テスト（失敗するテスト）

    This test MUST FAIL initially - concurrent access handling not implemented
    Tests: Multiple simultaneous database operations maintain consistency
    """

    async def concurrent_user_creation(engine, user_index: int) -> Tuple[bool, str]:
        """Create user concurrently and return success status"""
        TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        try:
            async with TestSession() as session:
                async with session.begin():
                    user = User(
                        email=f"concurrent_user_{user_index}_{uuid.uuid4().hex[:8]}@example.com",
                        age_group="20代前半",
                        gender="male" if user_index % 2 == 0 else "female",
                        estimated_pref_cd="13",
                        estimated_city_cd="13101",
                        registration_date=datetime.now().date()
                    )
                    session.add(user)
                    await session.commit()

                    # EXPECTED TO FAIL: Concurrent user creation not properly handled
                    return True, f"User {user_index} created successfully"

        except Exception as e:
            return False, f"User {user_index} creation failed: {str(e)}"

    # Execute concurrent operations (THIS WILL FAIL)
    concurrent_tasks = [
        concurrent_user_creation(transaction_test_engine, i)
        for i in range(STRESS_TEST_VOLUMES['concurrent_users'])
    ]

    # EXPECTED TO FAIL: Concurrent handling not implemented
    results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

    successful_operations = sum(1 for success, _ in results if success)
    failure_rate = (len(results) - successful_operations) / len(results) * 100

    # Allow some failures due to concurrent conflicts, but not all
    assert failure_rate < 20, f"Too many concurrent failures: {failure_rate}%"
    assert successful_operations > 0, "At least some concurrent operations should succeed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_deadlock_detection_and_recovery(transaction_test_engine):
    """
    T048-RED: デッドロック検出と回復テスト（失敗するテスト）

    This test MUST FAIL initially - deadlock handling not implemented
    Tests: Database properly detects and resolves deadlocks
    """

    TestSession = sessionmaker(transaction_test_engine, class_=AsyncSession, expire_on_commit=False)

    # Create test users for deadlock scenario
    async with TestSession() as setup_session:
        async with setup_session.begin():
            user1 = User(
                email=f"deadlock_user1_{uuid.uuid4().hex[:8]}@example.com",
                age_group="20代前半",
                gender="male",
                estimated_pref_cd="13",
                estimated_city_cd="13101",
                registration_date=datetime.now().date()
            )
            user2 = User(
                email=f"deadlock_user2_{uuid.uuid4().hex[:8]}@example.com",
                age_group="20代前半",
                gender="female",
                estimated_pref_cd="13",
                estimated_city_cd="13101",
                registration_date=datetime.now().date()
            )
            setup_session.add_all([user1, user2])
            await setup_session.commit()

            user1_id = user1.id
            user2_id = user2.id

    async def deadlock_transaction_1():
        """Transaction that will cause deadlock scenario"""
        async with TestSession() as session:
            async with session.begin():
                # Lock user1 first
                await session.execute(
                    select(User).where(User.id == user1_id).with_for_update()
                )

                # Simulate processing time
                await asyncio.sleep(0.1)

                # Try to lock user2 (potential deadlock)
                await session.execute(
                    select(User).where(User.id == user2_id).with_for_update()
                )

                # Update both users
                await session.execute(
                    update(User).where(User.id == user1_id).values(age_group="30代前半")
                )
                await session.execute(
                    update(User).where(User.id == user2_id).values(age_group="30代前半")
                )

                await session.commit()
                return "Transaction 1 completed"

    async def deadlock_transaction_2():
        """Transaction that will cause deadlock scenario"""
        async with TestSession() as session:
            async with session.begin():
                # Lock user2 first (opposite order from transaction 1)
                await session.execute(
                    select(User).where(User.id == user2_id).with_for_update()
                )

                # Simulate processing time
                await asyncio.sleep(0.1)

                # Try to lock user1 (potential deadlock)
                await session.execute(
                    select(User).where(User.id == user1_id).with_for_update()
                )

                # Update both users
                await session.execute(
                    update(User).where(User.id == user2_id).values(age_group="30代後半")
                )
                await session.execute(
                    update(User).where(User.id == user1_id).values(age_group="30代後半")
                )

                await session.commit()
                return "Transaction 2 completed"

    # Execute potentially deadlocking transactions (THIS WILL FAIL)
    start_time = time.time()

    try:
        # EXPECTED TO FAIL: Deadlock handling not implemented properly
        results = await asyncio.gather(
            deadlock_transaction_1(),
            deadlock_transaction_2(),
            return_exceptions=True
        )

        deadlock_resolution_time = (time.time() - start_time) * 1000

        # At least one transaction should complete successfully
        successful_transactions = [r for r in results if isinstance(r, str)]
        failed_transactions = [r for r in results if isinstance(r, Exception)]

        # EXPECTED TO FAIL: Proper deadlock resolution not implemented
        assert len(successful_transactions) >= 1, "At least one transaction should succeed"
        assert deadlock_resolution_time < TRANSACTION_TEST_TARGETS['deadlock_resolution_time'], \
            f"Deadlock resolution took {deadlock_resolution_time}ms, expected < {TRANSACTION_TEST_TARGETS['deadlock_resolution_time']}ms"

    except Exception as e:
        pytest.fail(f"Deadlock test failed unexpectedly: {e}")


# ============================================================================
# DATA CONSISTENCY TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_acid_compliance(transaction_test_session: AsyncSession):
    """
    T048-RED: ACID準拠テスト（失敗するテスト）

    This test MUST FAIL initially - ACID properties not properly implemented
    Tests: Atomicity, Consistency, Isolation, Durability
    """

    # Test Atomicity: All or nothing (THIS WILL FAIL)
    user_email = f"acid_test_{uuid.uuid4().hex[:8]}@example.com"

    try:
        async with transaction_test_session.begin():
            # Create user
            user = User(
                email=user_email,
                age_group="20代前半",
                gender="male",
                estimated_pref_cd="13",
                estimated_city_cd="13101",
                registration_date=datetime.now().date()
            )
            transaction_test_session.add(user)
            await transaction_test_session.flush()

            # Create related profile
            profile = UserProfile(
                user_id=user.id,
                display_name="ACID Test User",
                bio="Testing ACID compliance"
            )
            transaction_test_session.add(profile)

            # Create preferences
            preferences = UserPreferences(
                user_id=user.id,
                preferred_work_styles=["part_time"],
                preferred_categories=[100, 200],
                preferred_salary_min=1500
            )
            transaction_test_session.add(preferences)

            # Force error to test atomicity
            # Create duplicate user (should fail and rollback everything)
            duplicate_user = User(
                email=user_email,  # Duplicate email
                age_group="20代後半",
                gender="female",
                estimated_pref_cd="27",
                estimated_city_cd="27001",
                registration_date=datetime.now().date()
            )
            transaction_test_session.add(duplicate_user)

            # THIS SHOULD FAIL and rollback all operations
            await transaction_test_session.commit()

    except IntegrityError:
        # Expected: transaction should fail due to duplicate email
        pass

    # Test Atomicity verification (THIS WILL FAIL)
    async with transaction_test_session.begin():
        # EXPECTED TO FAIL: Atomicity not properly implemented
        user_result = await transaction_test_session.execute(
            select(User).where(User.email == user_email)
        )
        found_user = user_result.scalar_one_or_none()
        assert found_user is None, "User should not exist due to atomicity (all-or-nothing)"

        profile_result = await transaction_test_session.execute(
            select(UserProfile).join(User).where(User.email == user_email)
        )
        found_profile = profile_result.scalar_one_or_none()
        assert found_profile is None, "Profile should not exist due to atomicity"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_isolation_levels(transaction_test_engine):
    """
    T048-RED: トランザクション分離レベルテスト（失敗するテスト）

    This test MUST FAIL initially - isolation levels not properly configured
    Tests: Different isolation levels behave correctly
    """

    TestSession = sessionmaker(transaction_test_engine, class_=AsyncSession, expire_on_commit=False)

    # Create test user
    test_email = f"isolation_test_{uuid.uuid4().hex[:8]}@example.com"

    async with TestSession() as setup_session:
        async with setup_session.begin():
            user = User(
                email=test_email,
                age_group="20代前半",
                gender="male",
                estimated_pref_cd="13",
                estimated_city_cd="13101",
                registration_date=datetime.now().date()
            )
            setup_session.add(user)
            await setup_session.commit()
            user_id = user.id

    # Test READ COMMITTED isolation (THIS WILL FAIL)
    async def transaction_1():
        """Transaction that updates user data"""
        async with TestSession() as session:
            async with session.begin():
                # Update user age group
                await session.execute(
                    update(User).where(User.id == user_id).values(age_group="30代前半")
                )

                # Hold transaction open for a moment
                await asyncio.sleep(0.5)

                await session.commit()
                return "Transaction 1 committed"

    async def transaction_2():
        """Transaction that reads user data"""
        # Wait a bit to let transaction 1 start
        await asyncio.sleep(0.1)

        async with TestSession() as session:
            async with session.begin():
                # This should see old data until transaction 1 commits (READ COMMITTED)
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one()

                age_group_before_commit = user.age_group

                # Wait for transaction 1 to commit
                await asyncio.sleep(0.6)

                # Re-read after transaction 1 commits
                await session.refresh(user)
                age_group_after_commit = user.age_group

                return age_group_before_commit, age_group_after_commit

    # Execute isolation test (THIS WILL FAIL)
    results = await asyncio.gather(transaction_1(), transaction_2())

    # EXPECTED TO FAIL: Isolation levels not properly implemented
    commit_result = results[0]
    age_before, age_after = results[1]

    assert commit_result == "Transaction 1 committed"
    assert age_before == "20代前半", "Should see old data before commit"
    assert age_after == "30代前半", "Should see new data after commit"


# ============================================================================
# CONNECTION POOL TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_pool_under_stress(transaction_test_engine):
    """
    T048-RED: コネクションプールストレステスト（失敗するテスト）

    This test MUST FAIL initially - connection pool not properly configured
    Tests: Connection pool behavior under high concurrent load
    """

    TestSession = sessionmaker(transaction_test_engine, class_=AsyncSession, expire_on_commit=False)

    async def database_operation(operation_id: int):
        """Single database operation for stress testing"""
        try:
            async with TestSession() as session:
                async with session.begin():
                    # Create user
                    user = User(
                        email=f"pool_test_{operation_id}_{uuid.uuid4().hex[:8]}@example.com",
                        age_group="20代前半",
                        gender="male",
                        estimated_pref_cd="13",
                        estimated_city_cd="13101",
                        registration_date=datetime.now().date()
                    )
                    session.add(user)
                    await session.flush()

                    # Simulate some work
                    await asyncio.sleep(random.uniform(0.1, 0.5))

                    # Query user
                    result = await session.execute(
                        select(User).where(User.id == user.id)
                    )
                    found_user = result.scalar_one()

                    await session.commit()

                    return True, f"Operation {operation_id} succeeded"

        except Exception as e:
            return False, f"Operation {operation_id} failed: {str(e)}"

    # Execute stress test (THIS WILL FAIL)
    stress_operations = [
        database_operation(i)
        for i in range(STRESS_TEST_VOLUMES['concurrent_operations'])
    ]

    start_time = time.time()

    # EXPECTED TO FAIL: Connection pool not properly configured for stress
    results = await asyncio.gather(*stress_operations)

    test_duration = time.time() - start_time

    # Analyze results
    successful_ops = sum(1 for success, _ in results if success)
    failure_rate = (len(results) - successful_ops) / len(results) * 100
    operations_per_second = len(results) / test_duration

    # Get pool statistics
    pool_stats = ConnectionPoolStats.get_pool_stats()

    # EXPECTED TO FAIL: Pool efficiency not meeting targets
    assert failure_rate < 10, f"Too many pool-related failures: {failure_rate}%"
    assert pool_stats["utilization"] > TRANSACTION_TEST_TARGETS["connection_pool_efficiency"], \
        f"Pool efficiency {pool_stats['utilization']}% below target {TRANSACTION_TEST_TARGETS['connection_pool_efficiency']}%"
    assert test_duration < STRESS_TEST_VOLUMES['max_test_duration'], \
        f"Stress test took {test_duration}s, expected < {STRESS_TEST_VOLUMES['max_test_duration']}s"


# ============================================================================
# TRANSACTION TIMEOUT TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_timeout_handling(transaction_test_session: AsyncSession):
    """
    T048-RED: トランザクションタイムアウト処理テスト（失敗するテスト）

    This test MUST FAIL initially - timeout handling not implemented
    Tests: Long-running transactions are properly timed out
    """

    # Test long-running transaction timeout (THIS WILL FAIL)
    user_email = f"timeout_test_{uuid.uuid4().hex[:8]}@example.com"

    try:
        async with transaction_test_session.begin():
            # Create user
            user = User(
                email=user_email,
                age_group="20代前半",
                gender="male",
                estimated_pref_cd="13",
                estimated_city_cd="13101",
                registration_date=datetime.now().date()
            )
            transaction_test_session.add(user)
            await transaction_test_session.flush()

            # Simulate long-running operation that should timeout
            # This should trigger statement timeout
            await asyncio.sleep(35)  # Longer than statement_timeout (30s)

            # THIS SHOULD FAIL due to timeout
            await transaction_test_session.commit()
            pytest.fail("Transaction should have timed out")

    except (OperationalError, DatabaseError) as e:
        # EXPECTED TO FAIL: Timeout handling not properly implemented
        assert "timeout" in str(e).lower() or "cancel" in str(e).lower(), \
            f"Expected timeout error, got: {str(e)}"

    # Verify transaction was rolled back (THIS WILL FAIL)
    async with transaction_test_session.begin():
        result = await transaction_test_session.execute(
            select(User).where(User.email == user_email)
        )
        found_user = result.scalar_one_or_none()

        # EXPECTED TO FAIL: Timeout rollback not properly implemented
        assert found_user is None, "User should not exist after timeout rollback"


# ============================================================================
# BULK OPERATIONS TRANSACTION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_operations_transaction_consistency(transaction_test_session: AsyncSession, sample_transaction_data: Dict):
    """
    T048-RED: バルク操作トランザクション一貫性テスト（失敗するテスト）

    This test MUST FAIL initially - bulk operations not properly transactional
    Tests: Bulk operations maintain transactional consistency
    """

    users_data = sample_transaction_data["users"][:10]  # Use 10 users for bulk test

    # Test bulk insert with partial failure (THIS WILL FAIL)
    try:
        async with transaction_test_session.begin():
            # Create valid users
            valid_users = []
            for i, user_data in enumerate(users_data[:8]):  # First 8 are valid
                user = User(**user_data, registration_date=datetime.now().date())
                valid_users.append(user)

            # Add invalid users that will cause constraint violations
            invalid_users = [
                User(
                    email=users_data[0]["email"],  # Duplicate email
                    age_group="invalid_age_group",  # Invalid value
                    gender="invalid_gender",        # Invalid value
                    estimated_pref_cd="99",
                    estimated_city_cd="99999",
                    registration_date=datetime.now().date()
                ),
                User(
                    email=users_data[1]["email"],  # Another duplicate
                    age_group="20代前半",
                    gender="male",
                    estimated_pref_cd="13",
                    estimated_city_cd="13101",
                    registration_date=datetime.now().date()
                )
            ]

            # Add all users (valid and invalid)
            all_users = valid_users + invalid_users
            transaction_test_session.add_all(all_users)

            # THIS SHOULD FAIL and rollback all inserts
            await transaction_test_session.commit()
            pytest.fail("Bulk insert should have failed due to constraint violations")

    except (IntegrityError, DatabaseError):
        # Expected: bulk operation should fail
        pass

    # Verify complete rollback (THIS WILL FAIL)
    async with transaction_test_session.begin():
        # EXPECTED TO FAIL: Bulk rollback not properly implemented
        result = await transaction_test_session.execute(
            select(User).where(User.email.in_([u["email"] for u in users_data]))
        )
        found_users = result.scalars().all()

        assert len(found_users) == 0, "No users should exist after bulk rollback"


# ============================================================================
# COMPLEX TRANSACTION SCENARIOS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complex_multi_table_transaction(transaction_test_session: AsyncSession):
    """
    T048-RED: 複雑な複数テーブルトランザクションテスト（失敗するテスト）

    This test MUST FAIL initially - multi-table transactions not implemented
    Tests: Complex transactions spanning multiple tables maintain consistency
    """

    user_email = f"complex_tx_{uuid.uuid4().hex[:8]}@example.com"
    job_code = f"COMPLEX_JOB_{uuid.uuid4().hex[:8]}"

    try:
        async with transaction_test_session.begin():
            # Step 1: Create user
            user = User(
                email=user_email,
                age_group="20代前半",
                gender="male",
                estimated_pref_cd="13",
                estimated_city_cd="13101",
                registration_date=datetime.now().date()
            )
            transaction_test_session.add(user)
            await transaction_test_session.flush()

            # Step 2: Create job
            job = Job(
                endcl_cd=job_code,
                company_name="Complex Transaction Company",
                application_name="Complex Transaction Job",
                posting_date=datetime.now(),
                is_active=True
            )
            transaction_test_session.add(job)
            await transaction_test_session.flush()

            # Step 3: Create matching score
            matching_score = MatchingScore(
                user_id=user.id,
                job_id=job.id,
                basic_score=85.5,
                composite_score=82.3,
                created_at=datetime.now()
            )
            transaction_test_session.add(matching_score)

            # Step 4: Create user preferences
            preferences = UserPreferences(
                user_id=user.id,
                preferred_work_styles=["full_time"],
                preferred_categories=[100, 200],
                preferred_salary_min=2000
            )
            transaction_test_session.add(preferences)

            # Step 5: Force error to test multi-table rollback
            # Create duplicate matching score (should fail)
            duplicate_score = MatchingScore(
                user_id=user.id,
                job_id=job.id,  # Same user_id, job_id pair
                basic_score=75.0,
                composite_score=78.0,
                created_at=datetime.now()
            )
            transaction_test_session.add(duplicate_score)

            # THIS SHOULD FAIL and rollback all tables
            await transaction_test_session.commit()
            pytest.fail("Complex transaction should have failed")

    except IntegrityError:
        # Expected: transaction should fail due to duplicate constraint
        pass

    # Verify complete multi-table rollback (THIS WILL FAIL)
    async with transaction_test_session.begin():
        # EXPECTED TO FAIL: Multi-table rollback not properly implemented

        # Check user
        user_result = await transaction_test_session.execute(
            select(User).where(User.email == user_email)
        )
        found_user = user_result.scalar_one_or_none()
        assert found_user is None, "User should be rolled back"

        # Check job
        job_result = await transaction_test_session.execute(
            select(Job).where(Job.endcl_cd == job_code)
        )
        found_job = job_result.scalar_one_or_none()
        assert found_job is None, "Job should be rolled back"

        # Check matching scores
        score_result = await transaction_test_session.execute(
            select(MatchingScore).join(User).where(User.email == user_email)
        )
        found_scores = score_result.scalars().all()
        assert len(found_scores) == 0, "Matching scores should be rolled back"

        # Check preferences
        pref_result = await transaction_test_session.execute(
            select(UserPreferences).join(User).where(User.email == user_email)
        )
        found_prefs = pref_result.scalars().all()
        assert len(found_prefs) == 0, "Preferences should be rolled back"