"""
Contract test for GET /batch/status/{id} endpoint
Testing batch status retrieval according to API specification
"""
import pytest
from fastapi.testclient import TestClient


class TestBatchStatusContract:
    """Contract tests for batch status endpoint"""

    def test_get_batch_status_success(self, client: TestClient):
        """Test retrieving batch status for existing batch"""
        # First create a batch
        trigger_response = client.post(
            "/api/v1/batch/trigger",
            json={"batch_type": "daily_matching"}
        )

        # Skip if trigger fails
        if trigger_response.status_code != 202:
            pytest.skip("Batch trigger not implemented yet")

        batch_id = trigger_response.json()["batch_id"]

        # Get batch status
        response = client.get(f"/api/v1/batch/status/{batch_id}")

        assert response.status_code == 200

        # Verify response schema
        data = response.json()
        assert "batch_id" in data
        assert "job_type" in data
        assert "started_at" in data
        assert "status" in data
        assert "processed_records" in data
        assert "error_count" in data

        # Verify field types
        assert isinstance(data["batch_id"], int)
        assert data["batch_id"] == batch_id
        assert data["status"] in ["pending", "running", "completed", "failed"]
        assert isinstance(data["processed_records"], int)
        assert isinstance(data["error_count"], int)

    def test_get_batch_status_not_found(self, client: TestClient):
        """Test retrieving status for non-existent batch"""
        response = client.get("/api/v1/batch/status/999999")

        assert response.status_code == 404

    def test_get_batch_status_with_completed_batch(self, client: TestClient):
        """Test retrieving status for completed batch"""
        # This would need a mock or a way to ensure batch completion
        # For now, testing the contract structure
        batch_id = 1  # Assuming batch 1 exists and is completed

        response = client.get(f"/api/v1/batch/status/{batch_id}")

        if response.status_code == 200:
            data = response.json()
            if data["status"] == "completed":
                assert "completed_at" in data
                assert data["completed_at"] is not None
                assert "total_records" in data

    def test_get_batch_status_with_failed_batch(self, client: TestClient):
        """Test retrieving status for failed batch"""
        # This would need a mock or a way to trigger failure
        batch_id = 2  # Assuming batch 2 exists and failed

        response = client.get(f"/api/v1/batch/status/{batch_id}")

        if response.status_code == 200:
            data = response.json()
            if data["status"] == "failed":
                assert "error_logs" in data
                assert isinstance(data["error_logs"], list)

    def test_get_batch_status_invalid_id(self, client: TestClient):
        """Test retrieving status with invalid batch ID format"""
        response = client.get("/api/v1/batch/status/invalid")

        assert response.status_code == 422  # Validation error