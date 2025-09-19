"""
T080: Basic API Endpoint Tests [RED PHASE]

This test is intentionally designed to fail (TDD RED phase).
Documents that the following API endpoints are not yet implemented,
making the need for implementation clear.

Test targets:
- Health Check: GET /health
- Jobs API: GET /api/v1/jobs
- Users API: POST /api/v1/users/register

Run command: pytest tests/integration/test_basic_api_endpoints.py -v
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any


# Test target API base URL
API_BASE_URL = "http://localhost:8001"

# Request timeout setting
REQUEST_TIMEOUT = 10.0


class TestBasicAPIEndpoints:
    """Basic API endpoint tests"""

    @pytest.fixture(scope="class")
    def client(self):
        """HTTP client setup"""
        return httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=REQUEST_TIMEOUT
        )

    @pytest.mark.asyncio
    async def test_health_check_endpoint_exists(self, client):
        """
        Health check endpoint existence verification

        Expected behavior:
        - GET /health returns 200
        - Response contains status field
        - status is "ok" or "healthy"

        Current state: Not implemented -> This test will fail
        """
        response = await client.get("/health")

        # Status code verification
        assert response.status_code == 200, f"Health check failed with status {response.status_code}"

        # Response format verification
        data = response.json()
        assert isinstance(data, dict), "Health check response should be JSON object"
        assert "status" in data, "Health check response should contain 'status' field"
        assert data["status"] in ["ok", "healthy"], f"Invalid health status: {data['status']}"

    @pytest.mark.asyncio
    async def test_jobs_api_endpoint_exists(self, client):
        """
        Jobs API endpoint existence verification

        Expected behavior:
        - GET /api/v1/jobs returns 200
        - Response is list format
        - Each job data contains required fields

        Current state: Not implemented -> This test will fail
        """
        response = await client.get("/api/v1/jobs")

        # Status code verification
        assert response.status_code == 200, f"Jobs API failed with status {response.status_code}"

        # Response format verification
        data = response.json()
        assert isinstance(data, list), "Jobs API response should be a list"

        # Job data structure verification if not empty
        if data:
            job = data[0]
            required_fields = ["id", "title", "company", "location", "description"]
            for field in required_fields:
                assert field in job, f"Job data should contain '{field}' field"

    @pytest.mark.asyncio
    async def test_user_registration_endpoint_exists(self, client):
        """
        User registration API endpoint existence verification

        Expected behavior:
        - POST /api/v1/users/register returns 201 for valid request
        - Response contains user_id or user information
        - Password not included in response (security)

        Current state: Not implemented -> This test will fail
        """
        test_user_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test User"
        }

        response = await client.post(
            "/api/v1/users/register",
            json=test_user_data,
            headers={"Content-Type": "application/json"}
        )

        # Status code verification
        assert response.status_code == 201, f"User registration failed with status {response.status_code}"

        # Response format verification
        data = response.json()
        assert isinstance(data, dict), "Registration response should be JSON object"

        # Required fields verification
        expected_fields = ["id", "email", "name", "created_at"]
        for field in expected_fields:
            assert field in data, f"Registration response should contain '{field}' field"

        # Security verification: password should not be in response
        assert "password" not in data, "Password should not be included in registration response"
        assert data["email"] == test_user_data["email"], "Returned email should match input"


if __name__ == "__main__":
    # Display notes when running tests
    print("🔴 TDD RED PHASE: Basic API Endpoint Tests")
    print("=" * 50)
    print("These tests are intentionally designed to fail.")
    print("Failure content:")
    print("1. /health endpoint not implemented")
    print("2. /api/v1/jobs endpoint not implemented")
    print("3. /api/v1/users/register endpoint not implemented")
    print("")
    print("Next step (GREEN PHASE):")
    print("- Implement these endpoints with FastAPI router")
    print("- Make tests pass with minimal functionality")
    print("- Then improve quality in REFACTOR PHASE")
    print("=" * 50)
