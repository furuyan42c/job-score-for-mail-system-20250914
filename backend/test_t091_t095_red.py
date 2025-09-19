#!/usr/bin/env python3
"""
T091-T095 REDフェーステスト
SEOスコア計算、マッチング、メール配信機能のテスト
"""

import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime


def test_t091_seo_score_calculation():
    """T091: SEOスコア計算テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Calculate SEO score for a job
    response = client.post("/api/v1/scoring/calculate/seo",
                          json={
                              "job_id": 1,
                              "job_data": {
                                  "title": "高収入 バイト 渋谷",
                                  "description": "時給1500円以上の高収入バイト",
                                  "location": "渋谷"
                              },
                              "seo_keywords": [
                                  {"keyword": "高収入 バイト", "volume": 10000, "competition": 0.8},
                                  {"keyword": "渋谷 バイト", "volume": 5000, "competition": 0.7}
                              ]
                          })
    assert response.status_code == 200, f"SEO score calculation failed: {response.status_code}"

    result = response.json()
    assert "seo_score" in result
    assert 0 <= result["seo_score"] <= 100
    assert "keyword_matches" in result
    assert len(result["keyword_matches"]) > 0
    assert "search_volume_score" in result
    assert "competition_score" in result


def test_t092_user_job_matching():
    """T092: ユーザー×求人マッチングテスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Generate user-job matches
    response = client.post("/api/v1/matching/generate/comprehensive",
                          json={
                              "user_ids": [1, 2, 3],
                              "job_ids": [1, 2, 3, 4, 5],
                              "scoring_factors": {
                                  "location": 0.3,
                                  "salary": 0.3,
                                  "skills": 0.2,
                                  "seo": 0.2
                              }
                          })
    assert response.status_code == 200, f"Matching generation failed: {response.status_code}"

    result = response.json()
    assert "matches" in result
    assert len(result["matches"]) == 15  # 3 users x 5 jobs
    assert all("user_id" in m and "job_id" in m and "total_score" in m for m in result["matches"])

    # Get top matches for a user
    response = client.get("/api/v1/matching/user/1/top?limit=3")
    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) <= 3
    assert matches[0]["total_score"] >= matches[-1]["total_score"]  # Sorted by score


def test_t093_email_generation():
    """T093: メール生成テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Generate email for a user with job recommendations
    response = client.post("/api/v1/email/generate",
                          json={
                              "user_id": 1,
                              "user_data": {
                                  "name": "田中太郎",
                                  "email": "tanaka@example.com"
                              },
                              "job_recommendations": [
                                  {
                                      "job_id": 1,
                                      "title": "カフェスタッフ",
                                      "company": "スターバックス",
                                      "location": "渋谷",
                                      "salary": "時給1200円",
                                      "match_score": 85
                                  },
                                  {
                                      "job_id": 2,
                                      "title": "販売スタッフ",
                                      "company": "ユニクロ",
                                      "location": "新宿",
                                      "salary": "時給1100円",
                                      "match_score": 78
                                  }
                              ]
                          })
    assert response.status_code == 200, f"Email generation failed: {response.status_code}"

    result = response.json()
    assert "email" in result
    assert "subject" in result["email"]
    assert "body_html" in result["email"]
    assert "body_text" in result["email"]
    assert "田中太郎" in result["email"]["body_text"]
    assert len(result["email"]["body_html"]) > 100  # Has substantial content


def test_t094_distribution_list_generation():
    """T094: 配信リスト生成テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Generate distribution list
    response = client.post("/api/v1/distribution/generate-list",
                          json={
                              "schedule": "daily",
                              "filters": {
                                  "active_users_only": True,
                                  "min_match_score": 70,
                                  "max_recipients": 100
                              }
                          })
    assert response.status_code == 200, f"Distribution list generation failed: {response.status_code}"

    result = response.json()
    assert "distribution_list" in result
    assert "total_recipients" in result
    assert result["total_recipients"] > 0
    assert len(result["distribution_list"]) <= 100

    # Each recipient should have necessary data
    if result["distribution_list"]:
        recipient = result["distribution_list"][0]
        assert "user_id" in recipient
        assert "email" in recipient
        assert "job_recommendations" in recipient
        assert len(recipient["job_recommendations"]) > 0


def test_t095_batch_distribution_simulation():
    """T095: バッチ配信シミュレーションテスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Simulate batch email distribution
    response = client.post("/api/v1/distribution/simulate",
                          json={
                              "distribution_list_id": "test_list_001",
                              "send_rate": 10,  # emails per second
                              "total_recipients": 100,
                              "test_mode": True
                          })
    assert response.status_code == 200, f"Distribution simulation failed: {response.status_code}"

    result = response.json()
    assert "simulation_results" in result
    assert "estimated_time_seconds" in result["simulation_results"]
    assert "success_count" in result["simulation_results"]
    assert "failure_count" in result["simulation_results"]
    assert "queue_status" in result["simulation_results"]

    # Check simulation metrics
    assert result["simulation_results"]["success_count"] >= 0
    assert result["simulation_results"]["estimated_time_seconds"] == 10  # 100 emails / 10 per second

    # Get distribution status
    response = client.get("/api/v1/distribution/status/test_list_001")
    assert response.status_code == 200
    status = response.json()
    assert "status" in status
    assert status["status"] in ["pending", "in_progress", "completed", "failed"]


if __name__ == "__main__":
    print("🔴 T091-T095 RED Phase Tests")
    print("=" * 50)

    failures = []

    # Run each test and catch failures
    tests = [
        ("T091: SEOスコア計算", test_t091_seo_score_calculation),
        ("T092: ユーザー×求人マッチング", test_t092_user_job_matching),
        ("T093: メール生成", test_t093_email_generation),
        ("T094: 配信リスト生成", test_t094_distribution_list_generation),
        ("T095: バッチ配信シミュレーション", test_t095_batch_distribution_simulation)
    ]

    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name}: PASSED (unexpected - should fail)")
        except AssertionError as e:
            print(f"❌ {name}: FAILED (expected)")
            failures.append(name)
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            failures.append(name)

    print("=" * 50)
    print(f"📊 Total failures: {len(failures)}/{len(tests)}")
    if len(failures) == len(tests):
        print("🔴 RED Phase Confirmed: All tests are failing as expected")
    else:
        print("⚠️  Some tests passed unexpectedly")