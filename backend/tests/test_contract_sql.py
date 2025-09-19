#!/usr/bin/env python3
"""
T012: Contract Test for POST /sql/execute (RED Phase)

Tests API contract for SQL execution endpoint including:
- Request validation
- Response schema
- Security controls
- Error handling
"""

import pytest
from httpx import AsyncClient
from app.main import app
import json


class TestSqlExecuteContract:
    """Contract tests for POST /sql/execute endpoint"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_execute_sql_success(self, client: AsyncClient):
        """Test successful SQL query execution"""
        request_data = {
            "query": "SELECT job_id, score FROM scores WHERE score > 80 LIMIT 10",
            "params": {},
            "timeout": 5000
        }

        response = await client.post("/sql/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response schema
        assert "results" in data
        assert "columns" in data
        assert "row_count" in data
        assert "execution_time" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["columns"], list)

    @pytest.mark.asyncio
    async def test_execute_sql_with_params(self, client: AsyncClient):
        """Test SQL execution with parameters"""
        request_data = {
            "query": "SELECT * FROM jobs WHERE area = :area AND salary >= :min_salary",
            "params": {
                "area": "Tokyo",
                "min_salary": 300000
            }
        }

        response = await client.post("/sql/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["params_used"]) == 2 if "params_used" in data else True

    @pytest.mark.asyncio
    async def test_execute_sql_read_only(self, client: AsyncClient):
        """Test that only SELECT queries are allowed"""
        # Test INSERT - should be rejected
        request_data = {
            "query": "INSERT INTO jobs (job_contents) VALUES ('test')"
        }

        response = await client.post("/sql/execute", json=request_data)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "read-only" in data["detail"].lower() or "select" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_sql_update_rejected(self, client: AsyncClient):
        """Test UPDATE queries are rejected"""
        request_data = {
            "query": "UPDATE jobs SET is_active = false WHERE job_id = 1"
        }

        response = await client.post("/sql/execute", json=request_data)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_execute_sql_delete_rejected(self, client: AsyncClient):
        """Test DELETE queries are rejected"""
        request_data = {
            "query": "DELETE FROM jobs WHERE job_id = 1"
        }

        response = await client.post("/sql/execute", json=request_data)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_execute_sql_sql_injection_protection(self, client: AsyncClient):
        """Test SQL injection prevention"""
        request_data = {
            "query": "SELECT * FROM jobs WHERE job_id = 1; DROP TABLE users;--"
        }

        response = await client.post("/sql/execute", json=request_data)

        # Should either reject or sanitize
        assert response.status_code in [400, 403]
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_execute_sql_timeout(self, client: AsyncClient):
        """Test query timeout"""
        request_data = {
            "query": "SELECT * FROM jobs CROSS JOIN scores",  # Potentially slow query
            "timeout": 1  # 1ms timeout
        }

        response = await client.post("/sql/execute", json=request_data)

        # Should timeout
        assert response.status_code in [408, 504]
        data = response.json()
        assert "detail" in data
        assert "timeout" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_sql_invalid_query(self, client: AsyncClient):
        """Test invalid SQL syntax"""
        request_data = {
            "query": "SELEKT * FORM jobs"  # Invalid SQL
        }

        response = await client.post("/sql/execute", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "syntax" in data["detail"].lower() or "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_sql_empty_query(self, client: AsyncClient):
        """Test empty query validation"""
        request_data = {
            "query": ""
        }

        response = await client.post("/sql/execute", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_execute_sql_auth_required(self, client: AsyncClient):
        """Test authentication requirement"""
        request_data = {
            "query": "SELECT * FROM jobs LIMIT 1"
        }

        # Without auth header
        response = await client.post("/sql/execute", json=request_data)

        # Should require authentication for SQL execution
        assert response.status_code in [401, 403]

        # With auth header
        headers = {"Authorization": "Bearer test_admin_token"}
        response = await client.post("/sql/execute", json=request_data, headers=headers)

        # Should allow with valid auth (admin only)
        assert response.status_code in [200, 403]  # 403 if not admin

    @pytest.mark.asyncio
    async def test_execute_sql_result_limit(self, client: AsyncClient):
        """Test result row limit"""
        request_data = {
            "query": "SELECT * FROM jobs",  # No LIMIT clause
            "max_rows": 100
        }

        response = await client.post("/sql/execute", json=request_data)

        if response.status_code == 200:
            data = response.json()
            assert len(data["results"]) <= 100
            assert "truncated" in data or "row_limit_reached" in data

    @pytest.mark.asyncio
    async def test_execute_sql_response_time(self, client: AsyncClient):
        """Test response time SLA"""
        import time

        request_data = {
            "query": "SELECT job_id, job_contents FROM jobs LIMIT 10"
        }

        start = time.time()
        response = await client.post("/sql/execute", json=request_data)
        duration = time.time() - start

        assert response.status_code in [200, 401, 403]  # May require auth
        assert duration < 5.0  # Response should be under 5 seconds