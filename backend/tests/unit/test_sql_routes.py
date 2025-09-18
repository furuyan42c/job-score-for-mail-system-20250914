"""
Unit Tests for SQL Routes

Tests the SQL execution API endpoint with comprehensive security testing.
This test file validates:
- SQL injection protection
- Authentication and authorization
- Rate limiting
- Read-only enforcement
- Audit logging
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy import text
from datetime import datetime, timedelta

from app.main import app
from app.routers.sql_routes import (
    validate_sql_security,
    check_rate_limit,
    generate_query_hash,
    verify_sql_access_token,
    ALLOWED_TABLES,
    DANGEROUS_SQL_PATTERNS,
    RATE_LIMIT_REQUESTS
)

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def valid_auth_headers():
    """Create valid authentication headers"""
    return {"Authorization": "Bearer sql_test_user_12345"}

@pytest.fixture
def invalid_auth_headers():
    """Create invalid authentication headers"""
    return {"Authorization": "Bearer invalid_token"}

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.incr.return_value = 1
    redis_mock.expire.return_value = True
    redis_mock.hgetall.return_value = {"total_queries": "5", "successful_queries": "4"}
    redis_mock.hincrby.return_value = 1
    redis_mock.pipeline.return_value = redis_mock
    redis_mock.execute.return_value = [1, True]
    return redis_mock

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session_mock = AsyncMock()

    # Mock query result
    result_mock = Mock()
    result_mock.fetchall.return_value = [
        ("job_1", "エンジニア", "株式会社A", "東京", 1500),
        ("job_2", "デザイナー", "株式会社B", "大阪", 1200)
    ]
    result_mock.keys.return_value = ["job_id", "title", "company", "location", "salary"]

    session_mock.execute.return_value = result_mock
    return session_mock

# ============================================================================
# SECURITY VALIDATION TESTS
# ============================================================================

class TestSQLSecurityValidation:
    """Test SQL security validation functions"""

    def test_validate_sql_security_allowed_queries(self):
        """Test that allowed queries pass validation"""
        valid_queries = [
            "SELECT * FROM jobs WHERE is_active = TRUE",
            "SELECT job_id, title, company_name FROM jobs LIMIT 10",
            "SHOW TABLES",
            "DESCRIBE jobs",
            "EXPLAIN SELECT * FROM users",
            "WITH active_jobs AS (SELECT * FROM jobs WHERE is_active = TRUE) SELECT * FROM active_jobs"
        ]

        for query in valid_queries:
            is_safe, violations = validate_sql_security(query)
            assert is_safe, f"Query should be safe: {query}, violations: {violations}"
            assert len(violations) == 0

    def test_validate_sql_security_dangerous_queries(self):
        """Test that dangerous queries are blocked"""
        dangerous_queries = [
            "DROP TABLE jobs",
            "DELETE FROM users WHERE id = 1",
            "UPDATE jobs SET salary = 0",
            "INSERT INTO jobs VALUES (...)",
            "ALTER TABLE jobs ADD COLUMN malicious TEXT",
            "SELECT * FROM jobs; DROP TABLE users;",
            "SELECT * FROM jobs UNION SELECT * FROM admin_users",
            "SELECT * FROM jobs WHERE id = 1 AND SLEEP(10)",
            "SELECT LOAD_FILE('/etc/passwd')",
            "SELECT * FROM jobs WHERE title = 'test' OR '1'='1' --",
            "SELECT * FROM jobs /* comment */ WHERE id = 1"
        ]

        for query in dangerous_queries:
            is_safe, violations = validate_sql_security(query)
            assert not is_safe, f"Query should be blocked: {query}"
            assert len(violations) > 0

    def test_validate_sql_security_table_restrictions(self):
        """Test table access restrictions"""
        # Test allowed tables
        for table in ALLOWED_TABLES:
            query = f"SELECT * FROM {table}"
            is_safe, violations = validate_sql_security(query)
            assert is_safe, f"Allowed table should pass: {table}"

        # Test disallowed tables
        disallowed_tables = ["admin_users", "secrets", "config", "non_existent_table"]
        for table in disallowed_tables:
            query = f"SELECT * FROM {table}"
            is_safe, violations = validate_sql_security(query)
            assert not is_safe, f"Disallowed table should be blocked: {table}"

    def test_validate_sql_security_join_restrictions(self):
        """Test JOIN statement restrictions"""
        # Allowed JOIN
        query = "SELECT j.title, u.email FROM jobs j JOIN users u ON j.user_id = u.id"
        is_safe, violations = validate_sql_security(query)
        assert is_safe

        # Disallowed JOIN
        query = "SELECT * FROM jobs j JOIN admin_secrets s ON j.id = s.job_id"
        is_safe, violations = validate_sql_security(query)
        assert not is_safe

    def test_validate_sql_security_subquery_depth(self):
        """Test subquery depth limitations"""
        # Acceptable depth
        query = "SELECT * FROM jobs WHERE id IN (SELECT job_id FROM user_actions WHERE action = 'view')"
        is_safe, violations = validate_sql_security(query)
        assert is_safe

        # Excessive depth
        deep_query = "SELECT * FROM jobs WHERE id IN (" + \
                    "SELECT job_id FROM user_actions WHERE user_id IN (" + \
                    "SELECT user_id FROM users WHERE age IN (" + \
                    "SELECT DISTINCT age FROM user_profiles WHERE score IN (" + \
                    "SELECT score FROM scores))))"
        is_safe, violations = validate_sql_security(deep_query)
        assert not is_safe

# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self, mock_redis):
        """Test rate limiting when under the limit"""
        mock_redis.get.return_value = "5"  # Current count

        is_allowed, current_count, remaining = await check_rate_limit(
            mock_redis, "test_user", 1800, 30
        )

        assert is_allowed is True
        assert current_count == 6  # Should increment
        assert remaining == 24

    @pytest.mark.asyncio
    async def test_check_rate_limit_over_limit(self, mock_redis):
        """Test rate limiting when over the limit"""
        mock_redis.get.return_value = "30"  # At limit

        is_allowed, current_count, remaining = await check_rate_limit(
            mock_redis, "test_user", 1800, 30
        )

        assert is_allowed is False
        assert current_count == 30
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_failure(self):
        """Test rate limiting behavior when Redis fails"""
        failing_redis = AsyncMock()
        failing_redis.get.side_effect = Exception("Redis connection failed")

        is_allowed, current_count, remaining = await check_rate_limit(
            failing_redis, "test_user", 1800, 30
        )

        # Should allow requests when Redis fails (graceful degradation)
        assert is_allowed is True

# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthentication:
    """Test authentication and authorization"""

    @pytest.mark.asyncio
    async def test_verify_sql_access_token_valid(self):
        """Test valid token verification"""
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="sql_test_user_12345"
        )

        user_id = await verify_sql_access_token(credentials)
        assert user_id == "test_user_12345"

    @pytest.mark.asyncio
    async def test_verify_sql_access_token_invalid(self):
        """Test invalid token rejection"""
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        # Test short token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="short"
        )

        with pytest.raises(HTTPException) as exc_info:
            await verify_sql_access_token(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

        # Test non-SQL token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="regular_token_12345678"
        )

        with pytest.raises(HTTPException) as exc_info:
            await verify_sql_access_token(credentials)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions"""

    def test_generate_query_hash(self):
        """Test query hash generation"""
        query = "SELECT * FROM jobs"
        user_id = "test_user"

        hash1 = generate_query_hash(query, user_id)
        hash2 = generate_query_hash(query, user_id)
        hash3 = generate_query_hash("SELECT * FROM users", user_id)

        assert hash1 == hash2  # Same input should produce same hash
        assert hash1 != hash3  # Different input should produce different hash
        assert len(hash1) == 16  # Should be 16 characters

# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestSQLExecuteEndpoint:
    """Test SQL execution endpoint"""

    @patch('app.routers.sql_routes.get_redis')
    @patch('app.routers.sql_routes.get_db_read_only')
    @patch('app.routers.sql_routes.verify_sql_access_token')
    def test_execute_sql_success(self, mock_auth, mock_db, mock_redis, client):
        """Test successful SQL execution"""
        # Setup mocks
        mock_auth.return_value = "test_user"
        mock_db.return_value = mock_db_session()
        mock_redis.return_value = mock_redis()

        request_data = {
            "query": "SELECT job_id, title, company_name FROM jobs LIMIT 5",
            "limit": 5
        }

        response = client.post(
            "/api/v1/sql/execute",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "columns" in data
        assert "rows" in data
        assert data["row_count"] >= 0

    def test_execute_sql_unauthorized(self, client):
        """Test SQL execution without authentication"""
        request_data = {
            "query": "SELECT * FROM jobs LIMIT 5"
        }

        response = client.post("/api/v1/sql/execute", json=request_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('app.routers.sql_routes.verify_sql_access_token')
    def test_execute_sql_dangerous_query(self, mock_auth, client):
        """Test execution of dangerous query"""
        mock_auth.return_value = "test_user"

        request_data = {
            "query": "DROP TABLE jobs"
        }

        response = client.post(
            "/api/v1/sql/execute",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "violations" in data["detail"]

    @patch('app.routers.sql_routes.verify_sql_access_token')
    @patch('app.routers.sql_routes.check_rate_limit')
    def test_execute_sql_rate_limit_exceeded(self, mock_rate_limit, mock_auth, client):
        """Test SQL execution when rate limit is exceeded"""
        mock_auth.return_value = "test_user"
        mock_rate_limit.return_value = (False, 30, 0)  # Over limit

        request_data = {
            "query": "SELECT * FROM jobs LIMIT 5"
        }

        response = client.post(
            "/api/v1/sql/execute",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_execute_sql_invalid_query_format(self, client):
        """Test execution with invalid query format"""
        request_data = {
            "query": "",  # Empty query
            "limit": 5
        }

        response = client.post(
            "/api/v1/sql/execute",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.routers.sql_routes.verify_sql_access_token')
    def test_execute_sql_query_too_long(self, mock_auth, client):
        """Test execution with excessively long query"""
        mock_auth.return_value = "test_user"

        # Create a very long query (over 5000 characters)
        long_query = "SELECT * FROM jobs WHERE " + " OR ".join([f"id = {i}" for i in range(1000)])

        request_data = {
            "query": long_query
        }

        response = client.post(
            "/api/v1/sql/execute",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# ============================================================================
# UTILITY ENDPOINT TESTS
# ============================================================================

class TestUtilityEndpoints:
    """Test utility endpoints"""

    @patch('app.routers.sql_routes.verify_sql_access_token')
    def test_get_allowed_tables(self, mock_auth, client):
        """Test allowed tables endpoint"""
        mock_auth.return_value = "test_user"

        response = client.get(
            "/api/v1/sql/allowed-tables",
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "allowed_tables" in data
        assert len(data["allowed_tables"]) > 0
        assert "jobs" in data["allowed_tables"]

    @patch('app.routers.sql_routes.verify_sql_access_token')
    @patch('app.routers.sql_routes.get_redis')
    def test_get_usage_stats(self, mock_redis, mock_auth, client):
        """Test usage statistics endpoint"""
        mock_auth.return_value = "test_user"

        redis_mock = AsyncMock()
        redis_mock.hgetall.return_value = {"total_queries": "10", "successful_queries": "8"}
        redis_mock.get.return_value = "5"
        mock_redis.return_value = redis_mock

        response = client.get(
            "/api/v1/sql/usage-stats",
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "today_stats" in data
        assert "rate_limit" in data
        assert "limits" in data

    @patch('app.routers.sql_routes.verify_sql_access_token')
    def test_validate_sql_query(self, mock_auth, client):
        """Test SQL query validation endpoint"""
        mock_auth.return_value = "test_user"

        # Test safe query
        request_data = {
            "query": "SELECT * FROM jobs WHERE is_active = TRUE"
        }

        response = client.post(
            "/api/v1/sql/validate",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_safe"] is True
        assert len(data["violations"]) == 0

        # Test dangerous query
        request_data = {
            "query": "DROP TABLE jobs"
        }

        response = client.post(
            "/api/v1/sql/validate",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_safe"] is False
        assert len(data["violations"]) > 0

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSQLRoutesIntegration:
    """Test integration scenarios"""

    @patch('app.routers.sql_routes.get_redis')
    @patch('app.routers.sql_routes.get_db_read_only')
    @patch('app.routers.sql_routes.verify_sql_access_token')
    def test_full_sql_execution_flow(self, mock_auth, mock_db, mock_redis, client):
        """Test complete SQL execution flow"""
        # Setup mocks
        mock_auth.return_value = "test_user"

        # Mock database session
        session_mock = AsyncMock()
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            ("job_1", "エンジニア", "株式会社A"),
            ("job_2", "デザイナー", "株式会社B")
        ]
        result_mock.keys.return_value = ["job_id", "title", "company_name"]
        session_mock.execute.return_value = result_mock
        mock_db.return_value = session_mock

        # Mock Redis
        redis_mock = AsyncMock()
        redis_mock.get.return_value = "5"  # Rate limit count
        redis_mock.pipeline.return_value = redis_mock
        redis_mock.execute.return_value = [6, True]
        redis_mock.hincrby.return_value = 1
        redis_mock.setex.return_value = True
        mock_redis.return_value = redis_mock

        # Execute SQL
        request_data = {
            "query": "SELECT job_id, title, company_name FROM jobs WHERE is_active = TRUE LIMIT 10",
            "limit": 10,
            "cache_ttl": 300
        }

        response = client.post(
            "/api/v1/sql/execute",
            json=request_data,
            headers={"Authorization": "Bearer sql_test_user_12345"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert data["query"] == request_data["query"]
        assert len(data["columns"]) == 3
        assert len(data["rows"]) == 2
        assert data["row_count"] == 2
        assert data["execution_time_ms"] > 0
        assert "metadata" in data

    @patch('app.routers.sql_routes.verify_sql_access_token')
    def test_security_violation_logging(self, mock_auth, client):
        """Test that security violations are properly logged"""
        mock_auth.return_value = "test_user"

        with patch('app.routers.sql_routes.logger') as mock_logger:
            request_data = {
                "query": "SELECT * FROM jobs; DROP TABLE users;"
            }

            response = client.post(
                "/api/v1/sql/execute",
                json=request_data,
                headers={"Authorization": "Bearer sql_test_user_12345"}
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            # Verify that security violation was logged
            mock_logger.warning.assert_called()

if __name__ == "__main__":
    # Run specific test when script is executed directly
    pytest.main([__file__, "-v"])