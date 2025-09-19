"""
T005 RED Phase: Health Check Endpoint TDD Tests
- Test failing health check endpoint implementation
- Following strict TDD RED-GREEN-REFACTOR cycle
"""
import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthCheckEndpointTDD:
    """T005: Health Check Endpoint TDD Tests"""

    def test_health_check_endpoint_exists(self):
        """RED: Test that health check endpoint exists and returns 200"""
        response = client.get("/api/v1/health/check")
        assert response.status_code == 200

    def test_health_check_response_structure(self):
        """RED: Test health check response has required structure"""
        response = client.get("/api/v1/health/check")
        data = response.json()

        # Required fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data

        # Status should be 'healthy' or 'unhealthy'
        assert data["status"] in ["healthy", "unhealthy"]
        assert isinstance(data["version"], str)
        assert isinstance(data["uptime"], (int, float))

    def test_health_check_content_type(self):
        """RED: Test health check returns JSON content type"""
        response = client.get("/api/v1/health/check")
        assert response.headers["content-type"] == "application/json"

    def test_health_check_response_time(self):
        """RED: Test health check responds within acceptable time"""
        import time
        start_time = time.time()
        response = client.get("/api/v1/health/check")
        end_time = time.time()

        assert response.status_code == 200
        # Health check should respond within 1 second
        assert (end_time - start_time) < 1.0

    def test_health_check_idempotent(self):
        """RED: Test health check is idempotent"""
        response1 = client.get("/api/v1/health/check")
        response2 = client.get("/api/v1/health/check")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should have same status
        assert response1.json()["status"] == response2.json()["status"]

    def test_health_check_no_authentication_required(self):
        """RED: Test health check works without authentication"""
        # Should work without any auth headers
        response = client.get("/api/v1/health/check")
        assert response.status_code == 200
        assert "status" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])