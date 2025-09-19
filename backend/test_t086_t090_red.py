#!/usr/bin/env python3
"""
T086-T090 REDフェーステスト
データ投入、検証、スコア計算のテスト
"""

import pytest
from fastapi.testclient import TestClient
import json


def test_t086_master_data_loading():
    """T086: マスタデータ投入テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Prefecture master data
    response = client.post("/api/v1/data/master/prefectures",
                          json={"prefectures": [
                              {"code": "01", "name": "北海道"},
                              {"code": "13", "name": "東京都"}
                          ]})
    assert response.status_code == 201, f"Prefecture master data loading failed: {response.status_code}"
    assert response.json()["loaded"] == 2

    # Job categories master data
    response = client.post("/api/v1/data/master/categories",
                          json={"categories": [
                              {"code": "01", "name": "飲食"},
                              {"code": "02", "name": "小売"}
                          ]})
    assert response.status_code == 201, f"Category master data loading failed: {response.status_code}"
    assert response.json()["loaded"] == 2


def test_t087_seo_keyword_data_loading():
    """T087: SEOキーワードデータ投入テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # SEO keywords data
    response = client.post("/api/v1/data/seo/keywords",
                          json={"keywords": [
                              {"keyword": "高収入 バイト", "volume": 10000, "competition": 0.8},
                              {"keyword": "短期 求人", "volume": 5000, "competition": 0.6}
                          ]})
    assert response.status_code == 201, f"SEO keyword loading failed: {response.status_code}"
    assert response.json()["loaded"] == 2

    # Get SEO data for analysis
    response = client.get("/api/v1/data/seo/keywords")
    assert response.status_code == 200
    assert len(response.json()["keywords"]) >= 2


def test_t088_job_data_import():
    """T088: 求人データインポートテスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Import jobs batch
    jobs_data = [
        {
            "title": "ホールスタッフ",
            "company": "レストランA",
            "location": "東京都渋谷区",
            "salary_min": 1200,
            "salary_max": 1500,
            "category": "飲食"
        },
        {
            "title": "キッチンスタッフ",
            "company": "カフェB",
            "location": "東京都新宿区",
            "salary_min": 1100,
            "salary_max": 1400,
            "category": "飲食"
        }
    ]

    response = client.post("/api/v1/data/jobs/import", json={"jobs": jobs_data})
    assert response.status_code == 201, f"Job import failed: {response.status_code}"
    assert response.json()["imported"] == 2

    # Verify imported data
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    jobs = response.json()["jobs"]
    assert len(jobs) >= 2


def test_t089_data_integrity_validation():
    """T089: データ整合性検証テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Run data integrity checks
    response = client.post("/api/v1/data/validate/integrity")
    assert response.status_code == 200, f"Integrity validation failed: {response.status_code}"

    result = response.json()
    assert "validation_results" in result
    assert result["validation_results"]["master_data"]["status"] == "valid"
    assert result["validation_results"]["job_data"]["status"] == "valid"
    assert result["validation_results"]["referential_integrity"]["status"] == "valid"

    # Check for orphaned records
    response = client.get("/api/v1/data/validate/orphans")
    assert response.status_code == 200
    assert response.json()["orphaned_records"] == 0


def test_t090_basic_score_calculation():
    """T090: 基礎スコア計算テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Calculate basic matching score
    response = client.post("/api/v1/scoring/calculate/basic",
                          json={
                              "user_id": 1,
                              "job_id": 1,
                              "user_profile": {
                                  "location": "東京都渋谷区",
                                  "preferred_salary": 1300,
                                  "skills": ["接客", "コミュニケーション"]
                              },
                              "job_profile": {
                                  "location": "東京都渋谷区",
                                  "salary": 1200,
                                  "required_skills": ["接客"]
                              }
                          })
    assert response.status_code == 200, f"Score calculation failed: {response.status_code}"

    result = response.json()
    assert "score" in result
    assert 0 <= result["score"] <= 100
    assert "components" in result
    assert "location_score" in result["components"]
    assert "salary_score" in result["components"]
    assert "skill_score" in result["components"]

    # Batch score calculation
    response = client.post("/api/v1/scoring/calculate/batch",
                          json={"user_ids": [1, 2, 3], "job_ids": [1, 2, 3]})
    assert response.status_code == 200
    assert len(response.json()["scores"]) == 9  # 3x3 combinations


if __name__ == "__main__":
    print("🔴 T086-T090 RED Phase Tests")
    print("=" * 50)

    failures = []

    # Run each test and catch failures
    tests = [
        ("T086: マスタデータ投入", test_t086_master_data_loading),
        ("T087: SEOキーワードデータ投入", test_t087_seo_keyword_data_loading),
        ("T088: 求人データインポート", test_t088_job_data_import),
        ("T089: データ整合性検証", test_t089_data_integrity_validation),
        ("T090: 基礎スコア計算", test_t090_basic_score_calculation)
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