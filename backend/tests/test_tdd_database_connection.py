"""
T001.1 - RED Phase: Database Connection Tests
TDD Principle: Create failing tests first

These tests MUST fail initially to follow TDD methodology
"""

import pytest
import asyncio
from app.core.tdd_database import get_tdd_db_connection, TDDConnectionPool, TDDConnectionError


@pytest.mark.asyncio
async def test_tdd_database_connection():
    """
    T001.1 - RED: Basic database connection test

    This test MUST fail initially because get_tdd_db_connection doesn't exist yet
    """
    conn = await get_tdd_db_connection()
    assert conn is not None
    assert conn.is_connected() is True
    await conn.close()


@pytest.mark.asyncio
async def test_tdd_database_connection_with_config():
    """
    T001.1 - RED: Database connection with custom config

    This test MUST fail initially
    """
    config = {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "user": "test_user",
        "password": "test_pass"
    }

    conn = await get_tdd_db_connection(config)
    assert conn is not None
    assert hasattr(conn, 'config')
    assert conn.config == config
    await conn.close()


@pytest.mark.asyncio
async def test_tdd_database_connection_failure():
    """
    T001.1 - RED: Test connection failure handling

    This test MUST fail initially
    """
    invalid_config = {
        "host": "invalid_host",
        "port": 9999,
        "database": "nonexistent",
        "user": "fake_user",
        "password": "wrong_pass"
    }

    with pytest.raises(TDDConnectionError):
        await get_tdd_db_connection(invalid_config)


@pytest.mark.asyncio
async def test_tdd_connection_ping():
    """
    T001.1 - RED: Test connection health check

    This test MUST fail initially
    """
    conn = await get_tdd_db_connection()

    # Test ping functionality
    ping_result = await conn.ping()
    assert ping_result is True

    await conn.close()

    # After closing, ping should fail
    ping_result = await conn.ping()
    assert ping_result is False


@pytest.mark.asyncio
async def test_tdd_connection_execute_query():
    """
    T001.1 - RED: Test basic query execution

    This test MUST fail initially
    """
    conn = await get_tdd_db_connection()

    # Simple SELECT query
    result = await conn.execute("SELECT 1 as test_value")
    assert result is not None
    assert len(result) == 1
    assert result[0]['test_value'] == 1

    await conn.close()


class TestTDDConnectionLifecycle:
    """
    T001.1 - RED: Connection lifecycle tests

    These tests MUST fail initially
    """

    @pytest.mark.asyncio
    async def test_connection_context_manager(self):
        """Test connection as async context manager"""
        async with get_tdd_db_connection() as conn:
            assert conn.is_connected() is True

        # Connection should be automatically closed
        assert conn.is_connected() is False

    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """Test connection can be reused"""
        conn = await get_tdd_db_connection()

        # First query
        result1 = await conn.execute("SELECT 'test1' as msg")
        assert result1[0]['msg'] == 'test1'

        # Second query on same connection
        result2 = await conn.execute("SELECT 'test2' as msg")
        assert result2[0]['msg'] == 'test2'

        await conn.close()

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test connection timeout handling"""
        # This should timeout quickly
        config = {
            "host": "localhost",
            "port": 5432,
            "timeout": 0.1  # Very short timeout
        }

        with pytest.raises(TDDConnectionError, match="timeout"):
            await get_tdd_db_connection(config)


@pytest.mark.asyncio
async def test_tdd_multiple_connections():
    """
    T001.1 - RED: Test multiple simultaneous connections

    This test MUST fail initially
    """
    connections = []

    # Create multiple connections
    for i in range(3):
        conn = await get_tdd_db_connection()
        connections.append(conn)
        assert conn.is_connected() is True

    # All connections should be independent
    for i, conn in enumerate(connections):
        result = await conn.execute(f"SELECT {i} as conn_id")
        assert result[0]['conn_id'] == i

    # Close all connections
    for conn in connections:
        await conn.close()
        assert conn.is_connected() is False