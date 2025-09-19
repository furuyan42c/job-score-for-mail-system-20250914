"""
T084: ユーザージャーニーテスト
TDD RED Phase - 失敗するテストを作成
"""

import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any, List


class TestUserJourney:
    """ユーザージャーニーテスト - 実際のユーザー操作シナリオ"""

    @pytest.fixture
    def client(self):
        """テストクライアントのセットアップ"""
        from test_simple_server import app
        return TestClient(app)

    def test_new_user_complete_journey(self, client):
        """新規ユーザーの完全なジャーニー"""
        # 1. トップページアクセス
        home_response = client.get("/")
        assert home_response.status_code == 200

        # 2. ユーザー登録
        register_data = {
            "email": "journey.user@example.com",
            "password": "Journey123!",
            "name": "Journey User",
            "preferences": {
                "location": "Tokyo",
                "job_type": "full-time",
                "salary_min": 400000
            }
        }
        register_response = client.post("/api/v1/users/register", json=register_data)
        assert register_response.status_code == 201
        user = register_response.json()
        user_id = user["id"]

        # 3. プロファイル設定
        profile_data = {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience_years": 5,
            "desired_positions": ["Backend Developer", "Full Stack Developer"]
        }
        # ログイン
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        login_response = client.post("/api/v1/users/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        profile_response = client.patch("/api/v1/users/profile",
                                       json=profile_data,
                                       headers=headers)
        assert profile_response.status_code == 200

        # 4. 求人検索
        search_response = client.get("/api/v1/jobs/search?q=Python&location=Tokyo",
                                    headers=headers)
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert "jobs" in search_results

        # 5. マッチング結果取得
        matching_response = client.get(f"/api/v1/matching/user/{user_id}/recommendations",
                                      headers=headers)
        assert matching_response.status_code == 200
        recommendations = matching_response.json()
        assert "recommendations" in recommendations

        # 6. メール配信設定
        email_settings = {
            "frequency": "daily",
            "categories": ["editorial_picks", "top5"],
            "enabled": True
        }
        email_response = client.post("/api/v1/users/email-settings",
                                    json=email_settings,
                                    headers=headers)
        assert email_response.status_code == 200

        # 7. アクション記録（閲覧）
        if recommendations.get("recommendations"):
            job_id = recommendations["recommendations"][0]["job_id"]
            action_response = client.post("/api/v1/actions/view",
                                         json={"job_id": job_id},
                                         headers=headers)
            assert action_response.status_code == 201

    def test_returning_user_journey(self, client):
        """リピーターユーザーのジャーニー"""
        # 1. ログイン
        login_data = {
            "email": "existing.user@example.com",
            "password": "Existing123!"
        }
        login_response = client.post("/api/v1/users/login", json=login_data)
        assert login_response.status_code in [200, 401]  # 既存ユーザーがいない場合は401

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. 新着求人確認
            new_jobs_response = client.get("/api/v1/jobs/new",
                                          headers=headers)
            assert new_jobs_response.status_code == 200

            # 3. 保存済み求人確認
            saved_jobs_response = client.get("/api/v1/users/saved-jobs",
                                            headers=headers)
            assert saved_jobs_response.status_code == 200

            # 4. 応募履歴確認
            applications_response = client.get("/api/v1/users/applications",
                                              headers=headers)
            assert applications_response.status_code == 200

    def test_guest_user_limited_journey(self, client):
        """ゲストユーザーの制限付きジャーニー"""
        # 1. 求人一覧閲覧（認証なし）
        jobs_response = client.get("/api/v1/jobs")
        assert jobs_response.status_code == 200

        # 2. 求人詳細閲覧（認証なし）
        job_detail_response = client.get("/api/v1/jobs/1")
        assert job_detail_response.status_code in [200, 404]

        # 3. マッチング取得試行（認証なし - 失敗すべき）
        matching_response = client.get("/api/v1/matching/user/1/recommendations")
        assert matching_response.status_code == 401  # 未認証エラー

        # 4. 登録画面への誘導確認
        register_prompt_response = client.get("/api/v1/auth/register-prompt")
        assert register_prompt_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])