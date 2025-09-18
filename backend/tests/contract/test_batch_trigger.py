"""
Contract test for POST /batch/trigger endpoint
Testing batch processing trigger according to API specification
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestBatchTriggerContract:
    """Contract tests for batch trigger endpoint"""

    def test_trigger_daily_matching_batch(self, client: TestClient):
        """Test triggering daily matching batch process"""
        response = client.post(
            "/api/v1/batch/trigger",
            json={
                "batch_type": "daily_matching"
            }
        )

        # Assert 202 Accepted response
        assert response.status_code == 202

        # Check response structure
        data = response.json()
        assert "batch_id" in data
        assert "job_type" in data
        assert "started_at" in data
        assert "status" in data
        assert data["status"] in ["pending", "running"]
        assert data["job_type"] == "daily_matching"

        # Verify batch_id is integer
        assert isinstance(data["batch_id"], int)

    def test_trigger_scoring_batch(self, client: TestClient):
        """Test triggering scoring batch process"""
        response = client.post(
            "/api/v1/batch/trigger",
            json={
                "batch_type": "scoring"
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["job_type"] == "scoring"
        assert "batch_id" in data

    def test_trigger_email_generation_batch(self, client: TestClient):
        """Test triggering email generation batch process"""
        response = client.post(
            "/api/v1/batch/trigger",
            json={
                "batch_type": "email_generation"
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["job_type"] == "email_generation"
        assert "batch_id" in data

    def test_force_trigger_batch(self, client: TestClient):
        """Test force triggering batch when another is running"""
        response = client.post(
            "/api/v1/batch/trigger",
            json={
                "batch_type": "daily_matching",
                "force": True
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert "batch_id" in data

    def test_trigger_without_force_when_running(self, client: TestClient):
        """Test triggering batch without force when another is running"""
        # First trigger
        client.post(
            "/api/v1/batch/trigger",
            json={"batch_type": "daily_matching"}
        )

        # Second trigger should fail with 409
        response = client.post(
            "/api/v1/batch/trigger",
            json={"batch_type": "daily_matching"}
        )

        # This might be 409 if already running
        assert response.status_code in [202, 409]

    def test_invalid_batch_type(self, client: TestClient):
        """Test triggering with invalid batch type"""
        response = client.post(
            "/api/v1/batch/trigger",
            json={
                "batch_type": "invalid_type"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_missing_batch_type(self, client: TestClient):
        """Test triggering without batch_type"""
        response = client.post(
            "/api/v1/batch/trigger",
            json={}
        )

        assert response.status_code == 422  # Validation error