#!/usr/bin/env python3
"""
T080: 基本APIエンドポイントテスト - シンプル版
TDD RED Phase - 失敗するテストを作成
"""

from fastapi.testclient import TestClient
from test_simple_server import app


def test_health_check_endpoint():
    """ヘルスチェックエンドポイントのテスト"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    print("✅ Health check test passed")


def test_jobs_list_endpoint():
    """求人一覧取得エンドポイントのテスト"""
    client = TestClient(app)
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)
    print("✅ Jobs list test passed")


def test_jobs_get_by_id_endpoint():
    """求人詳細取得エンドポイントのテスト"""
    client = TestClient(app)
    job_id = 1
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == job_id
    print("✅ Job detail test passed")


def test_users_register_endpoint():
    """ユーザー登録エンドポイントのテスト"""
    client = TestClient(app)
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
    print("✅ User register test passed")


def run_all_tests():
    """全テストを実行（REDフェーズを確認）"""
    print("🔴 T080 RED Phase: Running failing tests...")
    print("-" * 50)

    failed_tests = []

    # Health check test (should pass)
    try:
        test_health_check_endpoint()
    except AssertionError as e:
        failed_tests.append(("Health Check", str(e)))
    except Exception as e:
        failed_tests.append(("Health Check", f"Error: {e}"))

    # Jobs list test (should fail)
    try:
        test_jobs_list_endpoint()
    except AssertionError as e:
        failed_tests.append(("Jobs List", str(e)))
        print(f"❌ Jobs list test failed (expected): {e}")
    except Exception as e:
        failed_tests.append(("Jobs List", f"Error: {e}"))
        print(f"❌ Jobs list test error: {e}")

    # Job detail test (should fail)
    try:
        test_jobs_get_by_id_endpoint()
    except AssertionError as e:
        failed_tests.append(("Job Detail", str(e)))
        print(f"❌ Job detail test failed (expected): {e}")
    except Exception as e:
        failed_tests.append(("Job Detail", f"Error: {e}"))
        print(f"❌ Job detail test error: {e}")

    # User register test (should fail)
    try:
        test_users_register_endpoint()
    except AssertionError as e:
        failed_tests.append(("User Register", str(e)))
        print(f"❌ User register test failed (expected): {e}")
    except Exception as e:
        failed_tests.append(("User Register", f"Error: {e}"))
        print(f"❌ User register test error: {e}")

    print("-" * 50)
    print(f"📊 Results: {len(failed_tests)} tests failed (expected in RED phase)")
    print("🔴 RED Phase Confirmed: Tests are failing as expected")

    return len(failed_tests) > 0


if __name__ == "__main__":
    # RED フェーズ確認
    run_all_tests()