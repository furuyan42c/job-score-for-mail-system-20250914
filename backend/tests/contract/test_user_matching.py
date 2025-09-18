"""
Contract test for GET /matching/user/{id} endpoint
Testing user-specific matching retrieval according to API specification
"""
import pytest
from fastapi.testclient import TestClient


class TestUserMatchingContract:
    """Contract tests for user matching retrieval endpoint"""

    def test_get_user_matching_success(self, client: TestClient):
        """Test retrieving matching results for existing user"""
        user_id = 1
        response = client.get(f"/api/v1/matching/user/{user_id}")

        assert response.status_code == 200

        # Verify response structure
        data = response.json()
        assert "user_id" in data
        assert "generated_at" in data
        assert "sections" in data

        # Verify user_id matches
        assert data["user_id"] == user_id

        # Verify sections structure
        sections = data["sections"]
        expected_sections = [
            "editorial_picks",
            "top5",
            "regional",
            "nearby",
            "high_income",
            "new"
        ]

        for section in expected_sections:
            assert section in sections
            assert isinstance(sections[section], list)

    def test_get_user_matching_not_found(self, client: TestClient):
        """Test retrieving matching for non-existent user"""
        response = client.get("/api/v1/matching/user/999999")

        assert response.status_code == 404

    def test_get_user_matching_job_details(self, client: TestClient):
        """Test job details in user matching response"""
        response = client.get("/api/v1/matching/user/1")

        if response.status_code == 200:
            data = response.json()

            # Check if any section has jobs
            for section_name, jobs in data["sections"].items():
                if len(jobs) > 0:
                    job = jobs[0]

                    # Verify job structure
                    assert "job_id" in job
                    assert "endcl_cd" in job
                    assert "application_name" in job
                    assert "min_salary" in job
                    assert "max_salary" in job
                    assert "fee" in job
                    assert "pref_cd" in job
                    assert "city_cd" in job
                    assert "created_at" in job

                    # Verify types
                    assert isinstance(job["job_id"], int)
                    assert isinstance(job["application_name"], str)
                    assert isinstance(job["min_salary"], int)
                    assert isinstance(job["max_salary"], int)

                    break

    def test_get_user_matching_section_limits(self, client: TestClient):
        """Test that sections respect expected limits"""
        response = client.get("/api/v1/matching/user/1")

        if response.status_code == 200:
            data = response.json()
            sections = data["sections"]

            # Expected section limits
            section_limits = {
                "editorial_picks": 3,  # Usually 3 picks
                "top5": 5,  # Top 5 as name suggests
                "regional": 10,  # Regional recommendations
                "nearby": 10,  # Nearby jobs
                "high_income": 10,  # High income opportunities
                "new": 10  # New postings
            }

            for section_name, limit in section_limits.items():
                if section_name in sections:
                    # Should not exceed expected limits
                    assert len(sections[section_name]) <= limit

    def test_get_user_matching_total_job_count(self, client: TestClient):
        """Test total number of jobs returned"""
        response = client.get("/api/v1/matching/user/1")

        if response.status_code == 200:
            data = response.json()

            # Count total jobs across all sections
            total_jobs = 0
            for jobs in data["sections"].values():
                total_jobs += len(jobs)

            # Should not exceed 40 (default limit)
            assert total_jobs <= 40

    def test_get_user_matching_invalid_id(self, client: TestClient):
        """Test with invalid user ID format"""
        response = client.get("/api/v1/matching/user/invalid")

        assert response.status_code == 422  # Validation error

    def test_get_user_matching_zero_id(self, client: TestClient):
        """Test with user ID zero"""
        response = client.get("/api/v1/matching/user/0")

        # Could be 404 or 422 depending on validation
        assert response.status_code in [404, 422]

    def test_get_user_matching_negative_id(self, client: TestClient):
        """Test with negative user ID"""
        response = client.get("/api/v1/matching/user/-1")

        # Could be 404 or 422 depending on validation
        assert response.status_code in [404, 422]

    def test_get_user_matching_generated_timestamp(self, client: TestClient):
        """Test generated_at timestamp format"""
        response = client.get("/api/v1/matching/user/1")

        if response.status_code == 200:
            data = response.json()

            # Verify timestamp format
            assert "generated_at" in data

            # Should be ISO format datetime string
            from datetime import datetime
            try:
                datetime.fromisoformat(data["generated_at"].replace('Z', '+00:00'))
            except ValueError:
                pytest.fail("generated_at is not in valid ISO format")