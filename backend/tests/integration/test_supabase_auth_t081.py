"""
T081: Supabase Auth統合テスト
TDD RED Phase - 失敗するテストを作成
"""

import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any


class TestSupabaseAuthIntegration:
    """Supabase認証機能の統合テスト"""

    @pytest.fixture
    def client(self):
        """テストクライアントのセットアップ"""
        from test_simple_server import app
        return TestClient(app)

    def test_supabase_signup_endpoint(self, client):
        """Supabaseサインアップのテスト"""
        signup_data = {
            "email": "supabase.test@example.com",
            "password": "SecurePass123!",
            "metadata": {
                "name": "Supabase User",
                "role": "user"
            }
        }
        response = client.post("/api/v1/auth/supabase/signup", json=signup_data)
        assert response.status_code == 201
        data = response.json()
        assert "session" in data
        assert "user" in data
        assert data["user"]["email"] == signup_data["email"]

    def test_supabase_login_endpoint(self, client):
        """Supabaseログインのテスト"""
        login_data = {
            "email": "supabase.test@example.com",
            "password": "SecurePass123!"
        }
        response = client.post("/api/v1/auth/supabase/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "access_token" in data["session"]
        assert "refresh_token" in data["session"]

    def test_supabase_logout_endpoint(self, client):
        """Supabaseログアウトのテスト"""
        # ヘッダーにトークンを設定
        headers = {
            "Authorization": "Bearer fake_supabase_token_123"
        }
        response = client.post("/api/v1/auth/supabase/logout", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "logged_out"

    def test_supabase_refresh_token_endpoint(self, client):
        """リフレッシュトークンのテスト"""
        refresh_data = {
            "refresh_token": "fake_refresh_token_456"
        }
        response = client.post("/api/v1/auth/supabase/refresh", json=refresh_data)
        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "access_token" in data["session"]

    def test_supabase_user_profile_endpoint(self, client):
        """ユーザープロファイル取得のテスト"""
        headers = {
            "Authorization": "Bearer fake_supabase_token_123"
        }
        response = client.get("/api/v1/auth/supabase/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "email" in data["user"]
        assert "metadata" in data["user"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])