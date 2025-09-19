"""
T002.1 - RED Phase: Connection Pooling Tests
TDD Principle: Create failing tests first

These tests MUST fail initially to follow TDD methodology
"""

import pytest
import asyncio
from app.core.tdd_database import TDDConnectionPool, TDDConnectionError, get_tdd_db_connection


@pytest.mark.asyncio
async def test_tdd_connection_pool_creation():
    """
    T002.1 - RED: Basic connection pool creation test

    This test MUST fail initially because TDDConnectionPool isn't implemented yet
    """
    pool_config = {
        "min_connections": 2,
        "max_connections": 10,
        "host": "localhost",
        "port": 5432,
        "database": "test_db"
    }

    pool = await TDDConnectionPool.create(pool_config)
    assert pool is not None
    assert pool.is_active() is True
    assert pool.get_pool_size() >= 2
    assert pool.get_pool_size() <= 10

    await pool.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_acquire_release():
    """
    T002.1 - RED: Test connection acquisition and release

    This test MUST fail initially
    """
    pool = await TDDConnectionPool.create({
        "min_connections": 1,
        "max_connections": 5
    })

    # Acquire connection from pool
    conn = await pool.acquire()
    assert conn is not None
    assert conn.is_connected() is True

    # Release connection back to pool
    await pool.release(conn)

    # Pool should still be active
    assert pool.is_active() is True

    await pool.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_max_connections():
    """
    T002.1 - RED: Test maximum connection limit

    This test MUST fail initially
    """
    pool = await TDDConnectionPool.create({
        "min_connections": 1,
        "max_connections": 2
    })

    # Acquire maximum connections
    conn1 = await pool.acquire()
    conn2 = await pool.acquire()

    # Third acquisition should timeout or raise error
    with pytest.raises((TDDConnectionError, asyncio.TimeoutError)):
        conn3 = await asyncio.wait_for(pool.acquire(), timeout=0.5)

    # Release one connection
    await pool.release(conn1)

    # Now we should be able to acquire again
    conn3 = await pool.acquire()
    assert conn3 is not None

    await pool.release(conn2)
    await pool.release(conn3)
    await pool.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_health_check():
    """
    T002.1 - RED: Test pool health monitoring

    This test MUST fail initially
    """
    pool = await TDDConnectionPool.create({
        "min_connections": 2,
        "max_connections": 5
    })

    # Check pool health
    health = await pool.check_health()
    assert health['status'] == 'healthy'
    assert health['active_connections'] >= 0
    assert health['idle_connections'] >= 0

    await pool.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_with_context_manager():
    """
    T002.1 - RED: Test pool as async context manager

    This test MUST fail initially
    """
    pool_config = {
        "min_connections": 1,
        "max_connections": 3
    }

    async with TDDConnectionPool.create(pool_config) as pool:
        assert pool.is_active() is True

        # Use connection from pool
        async with pool.acquire_connection() as conn:
            result = await conn.execute("SELECT 1 as test")
            assert result[0]['test'] == 1

    # Pool should be automatically closed
    # Note: We can't test this directly since pool is out of scope


@pytest.mark.asyncio
async def test_tdd_connection_pool_statistics():
    """
    T002.1 - RED: Test pool statistics and monitoring

    This test MUST fail initially
    """
    pool = await TDDConnectionPool.create({
        "min_connections": 2,
        "max_connections": 8
    })

    stats = pool.get_statistics()
    assert 'total_connections' in stats
    assert 'active_connections' in stats
    assert 'idle_connections' in stats
    assert 'connection_attempts' in stats

    # Initial state
    assert stats['total_connections'] >= 2
    assert stats['active_connections'] >= 0
    assert stats['idle_connections'] >= 0

    await pool.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_connection_timeout():
    """
    T002.1 - RED: Test connection timeout in pool

    This test MUST fail initially
    """
    pool = await TDDConnectionPool.create({
        "min_connections": 1,
        "max_connections": 1,
        "acquire_timeout": 0.1  # Very short timeout
    })

    # Acquire the only connection
    conn = await pool.acquire()

    # Second acquisition should timeout
    with pytest.raises(asyncio.TimeoutError):
        await pool.acquire()

    await pool.release(conn)
    await pool.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_retry_logic():
    """
    T002.1 - RED: Test connection retry and recovery

    This test MUST fail initially
    """
    pool = await TDDConnectionPool.create({
        "min_connections": 1,
        "max_connections": 3,
        "retry_attempts": 3
    })

    # Simulate connection failure and recovery
    await pool.simulate_connection_failure()

    # Pool should attempt to recover
    recovery_success = await pool.attempt_recovery()
    assert recovery_success is True

    # Should be able to acquire connection after recovery
    conn = await pool.acquire()
    assert conn.is_connected() is True

    await pool.release(conn)
    await pool.close()


class TestTDDConnectionPoolLifecycle:
    """
    T002.1 - RED: Connection pool lifecycle tests

    These tests MUST fail initially
    """

    @pytest.mark.asyncio
    async def test_pool_graceful_shutdown(self):
        """Test graceful pool shutdown"""
        pool = await TDDConnectionPool.create({
            "min_connections": 2,
            "max_connections": 5
        })

        # Acquire some connections
        conn1 = await pool.acquire()
        conn2 = await pool.acquire()

        # Start graceful shutdown
        shutdown_task = asyncio.create_task(pool.graceful_shutdown(timeout=1.0))

        # Release connections
        await pool.release(conn1)
        await pool.release(conn2)

        # Wait for shutdown to complete
        await shutdown_task

        assert pool.is_active() is False

    @pytest.mark.asyncio
    async def test_pool_force_close(self):
        """Test force close of pool"""
        pool = await TDDConnectionPool.create({
            "min_connections": 1,
            "max_connections": 3
        })

        conn = await pool.acquire()

        # Force close should work even with active connections
        await pool.force_close()

        assert pool.is_active() is False

    @pytest.mark.asyncio
    async def test_pool_connection_recycling(self):
        """Test connection recycling and cleanup"""
        pool = await TDDConnectionPool.create({
            "min_connections": 1,
            "max_connections": 2,
            "max_connection_age": 0.1  # Very short max age
        })

        # Get a connection
        conn1 = await pool.acquire()
        conn1_id = id(conn1)

        await pool.release(conn1)

        # Wait for connection to age out
        await asyncio.sleep(0.2)

        # Get connection again - should be a new one due to aging
        conn2 = await pool.acquire()
        conn2_id = id(conn2)

        # Should be different connection objects
        assert conn1_id != conn2_id

        await pool.release(conn2)
        await pool.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_integration_with_get_connection():
    """
    T002.1 - RED: Test integration between pool and get_tdd_db_connection

    This test MUST fail initially
    """
    # Create a pooled connection factory
    pool_factory = await TDDConnectionPool.create_factory({
        "min_connections": 2,
        "max_connections": 10
    })

    # Get connection through the factory (should use pooling)
    conn = await get_tdd_db_connection(use_pool=True, pool_factory=pool_factory)

    assert conn is not None
    assert conn.is_connected() is True

    # Connection should be managed by pool
    assert hasattr(conn, '_from_pool')
    assert conn._from_pool is True

    await conn.close()  # Should return to pool, not actually close
    await pool_factory.close()


@pytest.mark.asyncio
async def test_tdd_connection_pool_concurrent_access():
    """
    T002.1 - RED: Test concurrent access to connection pool

    This test MUST fail initially
    """
    pool = await TDDConnectionPool.create({
        "min_connections": 1,
        "max_connections": 5
    })

    async def worker(worker_id: int):
        """Worker function to test concurrent access"""
        conn = await pool.acquire()

        # Simulate some work
        result = await conn.execute(f"SELECT {worker_id} as worker_id")
        assert result[0]['worker_id'] == worker_id

        # Hold connection for a bit
        await asyncio.sleep(0.1)

        await pool.release(conn)
        return worker_id

    # Run multiple workers concurrently
    tasks = [worker(i) for i in range(3)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    assert sorted(results) == [0, 1, 2]

    await pool.close()