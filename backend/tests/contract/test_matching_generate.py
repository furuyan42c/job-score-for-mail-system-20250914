"""
Contract test for POST /matching/generate endpoint
Testing matching generation according to API specification
"""
import pytest
from fastapi.testclient import TestClient


class TestMatchingGenerateContract:
    """Contract tests for matching generation endpoint"""

    def test_generate_matching_for_users(self, client: TestClient):
        """Test generating matching for specific users"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": [1, 2, 3]
            }
        )

        assert response.status_code == 200

        # Check response is array
        data = response.json()
        assert isinstance(data, list)

        # Verify each user matching structure
        for user_matching in data:
            assert "user_id" in user_matching
            assert "generated_at" in user_matching
            assert "sections" in user_matching

            # Verify sections structure
            sections = user_matching["sections"]
            assert "editorial_picks" in sections
            assert "top5" in sections
            assert "regional" in sections
            assert "nearby" in sections
            assert "high_income" in sections
            assert "new" in sections

            # Each section should be a list
            for section_name, section_data in sections.items():
                assert isinstance(section_data, list)

    def test_generate_matching_with_custom_limit(self, client: TestClient):
        """Test generating matching with custom job limit"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": [1],
                "limit": 20  # Custom limit instead of default 40
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            # Count total jobs across all sections
            user_matching = data[0]
            total_jobs = 0
            for section_data in user_matching["sections"].values():
                total_jobs += len(section_data)

            # Should not exceed the limit
            assert total_jobs <= 20

    def test_generate_matching_default_limit(self, client: TestClient):
        """Test generating matching with default limit of 40 jobs"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": [1]
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            # Count total jobs across all sections
            user_matching = data[0]
            total_jobs = 0
            for section_data in user_matching["sections"].values():
                total_jobs += len(section_data)

            # Should not exceed default limit of 40
            assert total_jobs <= 40

    def test_generate_matching_job_structure(self, client: TestClient):
        """Test job structure in matching results"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": [1]
            }
        )

        assert response.status_code == 200

        data = response.json()
        if len(data) > 0 and len(data[0]["sections"]["top5"]) > 0:
            job = data[0]["sections"]["top5"][0]

            # Verify job structure
            assert "job_id" in job
            assert "endcl_cd" in job
            assert "application_name" in job
            assert "min_salary" in job
            assert "max_salary" in job
            assert "fee" in job
            assert "pref_cd" in job
            assert "city_cd" in job

            # Verify field types
            assert isinstance(job["job_id"], int)
            assert isinstance(job["endcl_cd"], str)
            assert isinstance(job["application_name"], str)
            assert isinstance(job["min_salary"], int)
            assert isinstance(job["max_salary"], int)
            assert isinstance(job["fee"], int)
            assert isinstance(job["pref_cd"], int)
            assert isinstance(job["city_cd"], int)

    def test_generate_matching_empty_user_list(self, client: TestClient):
        """Test generating matching with empty user list"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": []
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_generate_matching_without_user_ids(self, client: TestClient):
        """Test generating matching without user_ids field"""
        response = client.post(
            "/api/v1/matching/generate",
            json={}
        )

        # May return empty or error depending on implementation
        assert response.status_code in [200, 422]

    def test_generate_matching_invalid_user_ids(self, client: TestClient):
        """Test with invalid user ID format"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": ["not_a_number"]
            }
        )

        assert response.status_code == 422  # Validation error

    def test_generate_matching_invalid_limit(self, client: TestClient):
        """Test with invalid limit value"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": [1],
                "limit": -1
            }
        )

        assert response.status_code == 422  # Validation error

    def test_generate_matching_large_user_batch(self, client: TestClient):
        """Test generating matching for large batch of users"""
        response = client.post(
            "/api/v1/matching/generate",
            json={
                "user_ids": list(range(1, 101))  # 100 users
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Should return matching for each requested user
        assert len(data) <= 100