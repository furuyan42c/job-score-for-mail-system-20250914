"""
T083: データフロー統合テスト
TDD RED Phase - 失敗するテストを作成
"""

import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any, List


class TestDataFlowIntegration:
    """データフロー統合テスト"""

    @pytest.fixture
    def client(self):
        """テストクライアントのセットアップ"""
        from test_simple_server import app
        return TestClient(app)

    def test_job_data_flow(self, client):
        """求人データのフロー（作成→取得→更新→削除）"""
        # 1. Create
        job_data = {
            "title": "Python Developer",
            "company": "Tech Corp",
            "description": "Full-stack developer position",
            "salary": 600000
        }
        create_response = client.post("/api/v1/jobs", json=job_data)
        assert create_response.status_code == 201
        created_job = create_response.json()
        job_id = created_job["id"]

        # 2. Read
        get_response = client.get(f"/api/v1/jobs/{job_id}")
        assert get_response.status_code == 200
        retrieved_job = get_response.json()
        assert retrieved_job["title"] == job_data["title"]

        # 3. Update
        update_data = {"salary": 700000}
        update_response = client.patch(f"/api/v1/jobs/{job_id}", json=update_data)
        assert update_response.status_code == 200
        updated_job = update_response.json()
        assert updated_job["salary"] == 700000

        # 4. Delete
        delete_response = client.delete(f"/api/v1/jobs/{job_id}")
        assert delete_response.status_code == 204

        # 5. Verify deletion
        verify_response = client.get(f"/api/v1/jobs/{job_id}")
        assert verify_response.status_code == 404

    def test_user_data_flow(self, client):
        """ユーザーデータのフロー（登録→ログイン→プロファイル更新）"""
        # 1. Register
        register_data = {
            "email": "dataflow.user@example.com",
            "password": "TestPass123!",
            "name": "Data Flow User"
        }
        register_response = client.post("/api/v1/users/register", json=register_data)
        assert register_response.status_code == 201
        user = register_response.json()

        # 2. Login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        login_response = client.post("/api/v1/users/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 3. Update Profile
        headers = {"Authorization": f"Bearer {token}"}
        profile_data = {"name": "Updated Name"}
        update_response = client.patch("/api/v1/users/profile",
                                     json=profile_data,
                                     headers=headers)
        assert update_response.status_code == 200
        updated_user = update_response.json()
        assert updated_user["name"] == "Updated Name"

    def test_matching_data_flow(self, client):
        """マッチングデータのフロー（スコア計算→マッチング生成→結果取得）"""
        # 1. Calculate Score
        score_request = {
            "user_id": 1,
            "job_id": 1
        }
        score_response = client.post("/api/v1/scoring/calculate", json=score_request)
        assert score_response.status_code == 200
        score = score_response.json()
        assert "score" in score
        assert 0 <= score["score"] <= 100

        # 2. Generate Matching
        matching_request = {
            "user_id": 1,
            "limit": 10
        }
        matching_response = client.post("/api/v1/matching/generate", json=matching_request)
        assert matching_response.status_code == 200
        matches = matching_response.json()
        assert "matches" in matches
        assert len(matches["matches"]) <= 10

        # 3. Get Matching Results
        user_id = 1
        results_response = client.get(f"/api/v1/matching/user/{user_id}")
        assert results_response.status_code == 200
        results = results_response.json()
        assert "matches" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])