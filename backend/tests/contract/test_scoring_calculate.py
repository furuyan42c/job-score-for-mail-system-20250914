"""
Contract test for POST /scoring/calculate endpoint
Testing scoring calculation according to API specification
"""
import pytest
from fastapi.testclient import TestClient


class TestScoringCalculateContract:
    """Contract tests for scoring calculation endpoint"""

    def test_calculate_all_users_all_scores(self, client: TestClient):
        """Test calculating scores for all users and all score types"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={}  # Empty body = all users, all scores
        )

        assert response.status_code == 202  # Accepted

        # Check response structure
        data = response.json()
        assert "task_id" in data
        assert "estimated_time" in data

        # Verify field types
        assert isinstance(data["task_id"], str)
        assert isinstance(data["estimated_time"], int)
        assert data["estimated_time"] >= 0

    def test_calculate_specific_users(self, client: TestClient):
        """Test calculating scores for specific users"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "user_ids": [1, 2, 3, 4, 5]
            }
        )

        assert response.status_code == 202

        data = response.json()
        assert "task_id" in data
        assert "estimated_time" in data

    def test_calculate_specific_score_types(self, client: TestClient):
        """Test calculating specific types of scores"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "score_types": ["basic", "seo"]
            }
        )

        assert response.status_code == 202

        data = response.json()
        assert "task_id" in data

    def test_calculate_all_score_types(self, client: TestClient):
        """Test calculating all available score types"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "score_types": ["basic", "seo", "personalized"]
            }
        )

        assert response.status_code == 202

        data = response.json()
        assert "task_id" in data

    def test_calculate_single_user_single_score(self, client: TestClient):
        """Test calculating single score type for single user"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "user_ids": [1],
                "score_types": ["basic"]
            }
        )

        assert response.status_code == 202

        data = response.json()
        assert "task_id" in data
        # Single user should have shorter estimated time
        assert data["estimated_time"] >= 0

    def test_calculate_invalid_score_type(self, client: TestClient):
        """Test with invalid score type"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "score_types": ["invalid_type"]
            }
        )

        assert response.status_code == 422  # Validation error

    def test_calculate_invalid_user_ids(self, client: TestClient):
        """Test with invalid user IDs"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "user_ids": ["not_a_number"]
            }
        )

        assert response.status_code == 422  # Validation error

    def test_calculate_empty_user_list(self, client: TestClient):
        """Test with empty user list"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "user_ids": []
            }
        )

        # Empty list might be interpreted as "all users"
        assert response.status_code == 202

    def test_calculate_large_user_batch(self, client: TestClient):
        """Test calculating scores for large batch of users"""
        response = client.post(
            "/api/v1/scoring/calculate",
            json={
                "user_ids": list(range(1, 1001))  # 1000 users
            }
        )

        assert response.status_code == 202

        data = response.json()
        assert "task_id" in data
        assert "estimated_time" in data
        # Large batch should have longer estimated time
        assert data["estimated_time"] > 0