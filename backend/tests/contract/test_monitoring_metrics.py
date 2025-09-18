"""
Contract test for GET /monitoring/metrics endpoint
Testing system metrics retrieval according to API specification
"""
import pytest
from fastapi.testclient import TestClient


class TestMonitoringMetricsContract:
    """Contract tests for monitoring metrics endpoint"""

    def test_get_system_metrics(self, client: TestClient):
        """Test retrieving system metrics"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        # Verify response structure
        data = response.json()
        assert "active_users" in data
        assert "total_jobs" in data
        assert "daily_emails_sent" in data
        assert "avg_processing_time" in data
        assert "last_batch_status" in data
        assert "system_health" in data

        # Verify field types
        assert isinstance(data["active_users"], int)
        assert isinstance(data["total_jobs"], int)
        assert isinstance(data["daily_emails_sent"], int)
        assert isinstance(data["avg_processing_time"], (int, float))
        assert isinstance(data["last_batch_status"], str)
        assert isinstance(data["system_health"], str)

    def test_get_metrics_value_ranges(self, client: TestClient):
        """Test that metric values are in reasonable ranges"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()

        # Check non-negative values
        assert data["active_users"] >= 0
        assert data["total_jobs"] >= 0
        assert data["daily_emails_sent"] >= 0
        assert data["avg_processing_time"] >= 0

        # Check system health enum values
        assert data["system_health"] in ["healthy", "degraded", "critical"]

    def test_get_metrics_system_health_status(self, client: TestClient):
        """Test system health status values"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()
        health_status = data["system_health"]

        # Verify health status is one of expected values
        valid_statuses = ["healthy", "degraded", "critical"]
        assert health_status in valid_statuses

    def test_get_metrics_batch_status_format(self, client: TestClient):
        """Test last batch status format"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()
        batch_status = data["last_batch_status"]

        # Batch status could be various formats
        # Could be "completed", "failed", "running", etc.
        # Or could be a timestamp or "N/A"
        assert isinstance(batch_status, str)
        assert len(batch_status) > 0

    def test_get_metrics_processing_time_unit(self, client: TestClient):
        """Test average processing time is in minutes as specified"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()
        avg_time = data["avg_processing_time"]

        # Processing time should be reasonable (in minutes)
        # Assuming batch processing takes between 0 and 60 minutes on average
        assert avg_time >= 0
        assert avg_time <= 1440  # Max 24 hours in minutes

    def test_get_metrics_job_count_range(self, client: TestClient):
        """Test total jobs count is in expected range"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()
        total_jobs = data["total_jobs"]

        # Based on requirements: ~100,000 jobs
        # But in test environment might be less
        assert total_jobs >= 0
        assert total_jobs <= 1000000  # Max 1 million for safety

    def test_get_metrics_user_count_range(self, client: TestClient):
        """Test active users count is in expected range"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()
        active_users = data["active_users"]

        # Based on requirements: ~10,000 users
        # But in test environment might be less
        assert active_users >= 0
        assert active_users <= 100000  # Max 100k for safety

    def test_get_metrics_daily_emails_range(self, client: TestClient):
        """Test daily emails sent is reasonable"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()
        daily_emails = data["daily_emails_sent"]

        # Should not exceed number of users (10,000)
        # Each user gets at most one email per day
        assert daily_emails >= 0
        assert daily_emails <= 20000  # Max 20k for safety

    def test_get_metrics_no_parameters(self, client: TestClient):
        """Test that endpoint requires no parameters"""
        # Should work without any query parameters
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

    def test_get_metrics_with_invalid_parameter(self, client: TestClient):
        """Test that unknown parameters are ignored"""
        response = client.get("/api/v1/monitoring/metrics?unknown=param")

        # Should still work, ignoring unknown parameter
        assert response.status_code == 200

        data = response.json()
        # Should return standard metrics
        assert "active_users" in data
        assert "total_jobs" in data

    def test_get_metrics_response_completeness(self, client: TestClient):
        """Test that all required metrics are present"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200

        data = response.json()

        # All required fields must be present
        required_fields = [
            "active_users",
            "total_jobs",
            "daily_emails_sent",
            "avg_processing_time",
            "last_batch_status",
            "system_health"
        ]

        for field in required_fields:
            assert field in data
            # No field should be None (all should have default values)
            assert data[field] is not None