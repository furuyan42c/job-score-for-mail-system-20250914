"""
T080: 基本APIエンドポイントテスト
TDD RED Phase - 失敗するテストを作成
"""

import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any


class TestBasicAPIEndpoints:
    """基本APIエンドポイントのテスト"""

    @pytest.fixture
    def client(self):
        """テストクライアントのセットアップ"""
        # シンプルなテストサーバーを使用
        from test_simple_server import app
        return TestClient(app)

    def test_health_check_endpoint(self, client):
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_jobs_list_endpoint(self, client):
        """求人一覧取得エンドポイントのテスト"""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    def test_jobs_get_by_id_endpoint(self, client):
        """求人詳細取得エンドポイントのテスト"""
        job_id = 1
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == job_id

    def test_users_register_endpoint(self, client):
        """ユーザー登録エンドポイントのテスト"""
        user_data = {
            "email": "test@example.com",
            "password": "Test123!",
            "name": "Test User"
        }
        response = client.post("/api/v1/users/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert data["email"] == user_data["email"]

    def test_users_login_endpoint(self, client):
        """ユーザーログインエンドポイントのテスト"""
        login_data = {
            "email": "test@example.com",
            "password": "Test123!"
        }
        response = client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"


if __name__ == "__main__":
    # テストを実行してREDフェーズを確認
    pytest.main([__file__, "-v"])