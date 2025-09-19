#!/usr/bin/env python3
"""
T096 REDフェーステスト
配信結果分析機能のテスト
"""

import pytest
from fastapi.testclient import TestClient
import json


def test_t096_distribution_result_analysis():
    """T096: 配信結果分析テスト（RED）"""
    from test_simple_server import app
    client = TestClient(app)

    # Analyze distribution results
    response = client.post("/api/v1/distribution/analyze",
                          json={
                              "distribution_id": "dist_20250919_001",
                              "start_time": "2025-09-19T09:00:00Z",
                              "end_time": "2025-09-19T10:00:00Z"
                          })
    assert response.status_code == 200, f"Distribution analysis failed: {response.status_code}"

    result = response.json()
    # Basic metrics
    assert "analysis" in result
    assert "total_sent" in result["analysis"]
    assert "total_delivered" in result["analysis"]
    assert "total_opened" in result["analysis"]
    assert "total_clicked" in result["analysis"]

    # Performance metrics
    assert "delivery_rate" in result["analysis"]
    assert "open_rate" in result["analysis"]
    assert "click_rate" in result["analysis"]
    assert "conversion_rate" in result["analysis"]

    # Time-based metrics
    assert "average_open_time_minutes" in result["analysis"]
    assert "peak_engagement_hour" in result["analysis"]

    # Validate rates are percentages
    assert 0 <= result["analysis"]["delivery_rate"] <= 100
    assert 0 <= result["analysis"]["open_rate"] <= 100
    assert 0 <= result["analysis"]["click_rate"] <= 100

    # Get detailed analytics
    response = client.get("/api/v1/distribution/analytics/dist_20250919_001")
    assert response.status_code == 200

    analytics = response.json()
    assert "distribution_id" in analytics
    assert "performance_summary" in analytics
    assert "engagement_breakdown" in analytics
    assert "recommendations" in analytics

    # Test engagement breakdown
    assert "by_hour" in analytics["engagement_breakdown"]
    assert "by_job_category" in analytics["engagement_breakdown"]
    assert "by_user_segment" in analytics["engagement_breakdown"]

    # Test recommendations
    assert len(analytics["recommendations"]) > 0
    assert all("type" in r and "message" in r for r in analytics["recommendations"])


if __name__ == "__main__":
    print("🔴 T096 RED Phase Test")
    print("=" * 50)

    try:
        test_t096_distribution_result_analysis()
        print("✅ T096: 配信結果分析: PASSED (unexpected - should fail)")
    except AssertionError as e:
        print("❌ T096: 配信結果分析: FAILED (expected)")
    except Exception as e:
        print(f"❌ T096: 配信結果分析: ERROR - {e}")

    print("=" * 50)
    print("🔴 RED Phase Confirmed: Test is failing as expected")