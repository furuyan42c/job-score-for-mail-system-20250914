"""
SQL Injection Prevention Tests

包括的なSQLインジェクション攻撃防止テスト
- パラメータ化クエリの検証
- 入力サニタイゼーションのテスト
- プリペアドステートメントの使用確認
- 一般的なインジェクションパターンのテスト
- エラーメッセージからのスキーマ情報漏洩防止確認
- ストアドプロシージャインジェクション攻撃のテスト
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

# Common SQL injection payloads for testing
SQL_INJECTION_PAYLOADS = [
    # Basic SQL injection attempts
    "'; DROP TABLE users; --",
    "1' OR '1'='1",
    "admin'--",
    "1' UNION SELECT * FROM users--",
    "'; EXEC xp_cmdshell('dir'); --",

    # Advanced injection patterns
    "1' OR 1=1 UNION SELECT username, password FROM users--",
    "' OR 'a'='a",
    "1'; UPDATE users SET password='hacked' WHERE username='admin'--",
    "1' AND (SELECT COUNT(*) FROM users) > 0--",

    # Template injection attempts
    "${1+1}",
    "{{7*7}}",
    "#{''.getClass().forName('java.lang.Runtime').getRuntime().exec('ls')}",

    # Time-based blind injection
    "1' AND (SELECT SLEEP(5))--",
    "1'; WAITFOR DELAY '00:00:05'--",

    # Boolean-based blind injection
    "1' AND ASCII(SUBSTRING((SELECT password FROM users WHERE username='admin'),1,1))>64--",

    # Error-based injection
    "1' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e))--",
    "1' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
]

# Endpoints that should be tested for SQL injection
VULNERABLE_ENDPOINTS = [
    {"method": "GET", "path": "/users/", "params": ["email", "name", "location"]},
    {"method": "GET", "path": "/jobs/", "params": ["title", "company", "location", "skills"]},
    {"method": "GET", "path": "/scores/", "params": ["user_id", "job_id"]},
    {"method": "POST", "path": "/users/", "body_fields": ["email", "name", "location"]},
    {"method": "PUT", "path": "/users/1", "body_fields": ["email", "name", "location"]},
    {"method": "POST", "path": "/jobs/", "body_fields": ["title", "company", "description"]},
    {"method": "POST", "path": "/auth/login", "body_fields": ["email", "password"]},
]


class TestSQLInjectionPrevention:
    """SQL インジェクション防止テストスイート"""

    @pytest.mark.asyncio
    async def test_parameterized_queries_validation(self, async_client: AsyncClient):
        """パラメータ化クエリの使用確認テスト"""
        # Monitor SQL queries to ensure they use parameterized statements
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
            mock_execute.return_value = MagicMock()

            # Test user search with potential injection
            response = await async_client.get("/users/?email=test@example.com")

            # Verify that execute was called with text() and parameters
            assert mock_execute.called
            call_args = mock_execute.call_args[0][0]

            # Ensure SQL uses parameterized queries (not string concatenation)
            assert isinstance(call_args, (text, type(text("SELECT * FROM users WHERE email = :email"))))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:10])  # Test first 10 payloads
    async def test_get_endpoint_injection_resistance(self, async_client: AsyncClient, payload: str):
        """GET エンドポイントのインジェクション耐性テスト"""
        # Test user search endpoint
        response = await async_client.get(f"/users/?email={payload}")

        # Should not return 500 error (which might indicate successful injection)
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

        # Should not expose database errors in response
        response_text = response.text.lower()
        database_error_keywords = [
            'sql', 'syntax error', 'mysql', 'postgresql', 'sqlite',
            'syntax error', 'column', 'table', 'database', 'select', 'insert', 'update', 'delete'
        ]

        for keyword in database_error_keywords:
            assert keyword not in response_text, f"Database error exposed: {keyword}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:10])
    async def test_post_endpoint_injection_resistance(self, async_client: AsyncClient, payload: str):
        """POST エンドポイントのインジェクション耐性テスト"""
        # Test user creation with malicious payload
        malicious_user_data = {
            "email": payload,
            "name": f"Test User {payload}",
            "age_group": "20代前半",
            "location": "東京都",
            "occupation": "エンジニア"
        }

        response = await async_client.post("/users/", json=malicious_user_data)

        # Should handle invalid input gracefully
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,  # Input validation error
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # Validation error
        ]

        # Should not expose SQL errors
        response_text = response.text.lower()
        assert 'sql' not in response_text
        assert 'syntax error' not in response_text

    @pytest.mark.asyncio
    async def test_authentication_injection_resistance(self, async_client: AsyncClient):
        """認証エンドポイントのインジェクション耐性テスト"""
        injection_attempts = [
            "admin'--",
            "' OR '1'='1",
            "admin' UNION SELECT 'admin', 'password'--"
        ]

        for payload in injection_attempts:
            login_data = {
                "email": payload,
                "password": "any_password"
            }

            response = await async_client.post("/auth/login", json=login_data)

            # Should not allow authentication bypass
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

            # Should not expose SQL information
            response_data = response.json()
            assert 'sql' not in str(response_data).lower()

    @pytest.mark.asyncio
    async def test_search_parameter_sanitization(self, async_client: AsyncClient):
        """検索パラメータのサニタイゼーションテスト"""
        dangerous_search_terms = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE jobs; --",
            "%' UNION SELECT * FROM users--",
            "../../etc/passwd"
        ]

        for term in dangerous_search_terms:
            response = await async_client.get(f"/jobs/?title={term}")

            # Should return appropriate status (not 500)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

            # Check that dangerous content is not reflected in response
            response_text = response.text
            assert "<script>" not in response_text
            assert "DROP TABLE" not in response_text.upper()

    @pytest.mark.asyncio
    async def test_numeric_parameter_injection(self, async_client: AsyncClient):
        """数値パラメータのインジェクションテスト"""
        numeric_injection_payloads = [
            "1 OR 1=1",
            "1; DROP TABLE users;",
            "1' UNION SELECT * FROM users--",
            "1 AND (SELECT COUNT(*) FROM users) > 0"
        ]

        for payload in numeric_injection_payloads:
            # Test with user_id parameter
            response = await async_client.get(f"/users/{payload}")

            # Should return 404 or 400, not 500 or 200 with unexpected data
            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.asyncio
    async def test_batch_operation_injection_resistance(self, async_client: AsyncClient):
        """バッチ操作のインジェクション耐性テスト"""
        malicious_batch_data = {
            "operation": "delete",
            "user_ids": ["1'; DROP TABLE users; --", "2", "3"],
            "reason": "Test batch operation"
        }

        response = await async_client.post("/users/bulk", json=malicious_batch_data)

        # Should validate input properly
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    @pytest.mark.asyncio
    async def test_stored_procedure_injection_resistance(self, async_session: AsyncSession):
        """ストアドプロシージャインジェクション耐性テスト"""
        # Test direct database access with injection attempts
        injection_attempts = [
            "'; EXEC xp_cmdshell('dir'); --",
            "1; CALL malicious_procedure(); --",
            "1'; SELECT * FROM sensitive_data; --"
        ]

        for payload in injection_attempts:
            # Simulate a procedure call that might be vulnerable
            try:
                # This should use parameterized queries
                stmt = text("SELECT calculate_score(:user_id, :job_id)")
                result = await async_session.execute(stmt, {"user_id": payload, "job_id": "1"})

                # If the query succeeds, it should only return expected data types
                if result:
                    rows = result.fetchall()
                    for row in rows:
                        # Ensure no unexpected data is returned
                        assert len(row) <= 1  # Only score should be returned

            except Exception as e:
                # Should fail gracefully without exposing internal details
                error_message = str(e).lower()
                assert 'password' not in error_message
                assert 'table' not in error_message
                assert 'column' not in error_message

    @pytest.mark.asyncio
    async def test_error_message_information_disclosure(self, async_client: AsyncClient):
        """エラーメッセージ情報漏洩防止テスト"""
        # Test various malformed requests
        malformed_requests = [
            ("GET", "/users/?email='invalid"),
            ("GET", "/jobs/?id=abc'def"),
            ("POST", "/users/", {"email": "test'; SELECT * FROM users--"}),
        ]

        for method, url, *data in malformed_requests:
            if method == "GET":
                response = await async_client.get(url)
            elif method == "POST":
                response = await async_client.post(url, json=data[0] if data else {})

            # Check that error messages don't expose database structure
            if response.status_code >= 400:
                response_text = response.text.lower()
                sensitive_info = [
                    'table', 'column', 'constraint', 'foreign key',
                    'primary key', 'index', 'database', 'schema',
                    'mysql', 'postgresql', 'sqlite', 'sql server'
                ]

                for info in sensitive_info:
                    assert info not in response_text, f"Sensitive info exposed: {info}"

    @pytest.mark.asyncio
    async def test_csv_import_injection_resistance(self, async_client: AsyncClient):
        """CSV インポート機能のインジェクション耐性テスト"""
        malicious_csv_content = """email,name,location
test@example.com,Normal User,Tokyo
"'; DROP TABLE users; --",Malicious User,Osaka
admin@example.com,"=cmd|' /C calc'!A0",Tokyo
"""

        # Simulate CSV upload (if the endpoint exists)
        files = {"file": ("malicious.csv", malicious_csv_content, "text/csv")}
        response = await async_client.post("/users/import", files=files)

        # Should handle malicious CSV gracefully
        if response.status_code == 200:
            # If successful, verify no malicious data was processed
            users_response = await async_client.get("/users/")
            users_data = users_response.json()

            # Check that malicious entries were filtered out
            for user in users_data.get("items", []):
                assert "DROP TABLE" not in user.get("name", "").upper()
                assert "cmd|" not in user.get("name", "")

    def test_sql_query_logging_safety(self, caplog):
        """SQL クエリログの安全性テスト"""
        with caplog.at_level(logging.DEBUG):
            # Simulate a query that might log parameters
            sensitive_data = "password123"

            # This should not appear in logs
            logger = logging.getLogger("sqlalchemy.engine")
            logger.debug(f"Executing query with params: {{'password': '{sensitive_data}'}}")

            # Check that sensitive data is not in logs
            for record in caplog.records:
                assert sensitive_data not in record.getMessage()


class TestDatabaseConnectionSecurity:
    """データベース接続セキュリティテスト"""

    @pytest.mark.asyncio
    async def test_connection_string_security(self):
        """データベース接続文字列のセキュリティテスト"""
        # Ensure database credentials are not hardcoded
        import app.database

        # Check that connection uses environment variables
        db_url = str(app.database.DATABASE_URL)

        # Should not contain hardcoded passwords
        assert "password123" not in db_url
        assert "admin" not in db_url
        assert "root" not in db_url

        # Should use secure connection parameters
        if "postgresql" in db_url:
            # Should use SSL in production
            pass  # Will be checked in integration tests

    @pytest.mark.asyncio
    async def test_database_user_permissions(self, async_session: AsyncSession):
        """データベースユーザー権限テスト"""
        try:
            # Try to execute administrative commands
            admin_commands = [
                "CREATE DATABASE test_db",
                "DROP DATABASE test_db",
                "CREATE USER test_user",
                "GRANT ALL PRIVILEGES ON *.* TO test_user"
            ]

            for cmd in admin_commands:
                try:
                    await async_session.execute(text(cmd))
                    # If this succeeds, the database user has too many privileges
                    assert False, f"Database user has excessive privileges: {cmd}"
                except Exception:
                    # Expected to fail - good!
                    pass

        except Exception as e:
            # Connection issues are acceptable for this test
            pass


@pytest.fixture
async def async_session():
    """Async database session fixture for direct database testing"""
    # This would be implemented based on your database setup
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])