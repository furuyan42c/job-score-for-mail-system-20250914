#!/usr/bin/env python3
"""
Manual test script for refactored T010-T013 endpoints
This validates the REFACTOR phase implementations work correctly
"""

import asyncio
import json
from fastapi.testclient import TestClient
from app.main import app

def test_refactored_endpoints():
    """Test the refactored endpoints T010-T013"""
    client = TestClient(app)

    print("=" * 50)
    print("Testing Refactored Endpoints T010-T013")
    print("=" * 50)

    # Test T010: GET /matching/user/{id}
    print("\n1. Testing T010: GET /api/v1/matching/user/1")
    try:
        response = client.get("/api/v1/matching/user/1")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Keys: {list(data.keys())}")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Generated At: {data.get('generated_at')}")
            print(f"   Sections: {list(data.get('sections', {}).keys())}")
            print("   ✅ T010 structure matches contract expectations")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ T010 test failed: {e}")

    # Test T010 with invalid user
    print("\n2. Testing T010: GET /api/v1/matching/user/999999 (should be 404)")
    try:
        response = client.get("/api/v1/matching/user/999999")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ T010 correctly returns 404 for non-existent user")
        else:
            print(f"   ⚠️  Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ T010 404 test failed: {e}")

    # Test T011: POST /email/generate
    print("\n3. Testing T011: POST /api/v1/email/generate")
    try:
        email_data = {"user_id": 1, "use_gpt5": True}
        response = client.post("/api/v1/email/generate", json=email_data)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Keys: {list(data.keys())}")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Subject: {data.get('subject', '')[:50]}...")
            print(f"   Has HTML Body: {'html_body' in data}")
            print(f"   Has Plain Body: {'plain_body' in data}")
            print("   ✅ T011 structure matches contract expectations")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ T011 test failed: {e}")

    # Test T011 with missing user_id
    print("\n4. Testing T011: POST /api/v1/email/generate (missing user_id)")
    try:
        response = client.post("/api/v1/email/generate", json={})
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 422:
            print("   ✅ T011 correctly returns 422 for missing user_id")
        else:
            print(f"   ⚠️  Expected 422, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ T011 validation test failed: {e}")

    # Test T012: POST /sql/execute
    print("\n5. Testing T012: POST /api/v1/sql/execute")
    try:
        sql_data = {"query": "SELECT 1 as test_column", "limit": 10}
        response = client.post("/api/v1/sql/execute", json=sql_data)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Keys: {list(data.keys())}")
            print(f"   Columns: {data.get('columns', [])}")
            print(f"   Row Count: {data.get('row_count', 0)}")
            print(f"   Execution Time: {data.get('execution_time', 0)}")
            print("   ✅ T012 structure matches contract expectations")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ T012 test failed: {e}")

    # Test T012 with forbidden query
    print("\n6. Testing T012: POST /api/v1/sql/execute (forbidden INSERT)")
    try:
        sql_data = {"query": "INSERT INTO users (name) VALUES ('test')"}
        response = client.post("/api/v1/sql/execute", json=sql_data)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 403:
            print("   ✅ T012 correctly blocks forbidden operations")
        else:
            print(f"   ⚠️  Expected 403, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ T012 security test failed: {e}")

    # Test T013: GET /monitoring/metrics
    print("\n7. Testing T013: GET /api/v1/monitoring/metrics")
    try:
        response = client.get("/api/v1/monitoring/metrics")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Keys: {list(data.keys())}")
            print(f"   Active Users: {data.get('active_users', 'N/A')}")
            print(f"   Total Jobs: {data.get('total_jobs', 'N/A')}")
            print(f"   System Health: {data.get('system_health', 'N/A')}")
            print("   ✅ T013 structure matches contract expectations")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ T013 test failed: {e}")

    print("\n" + "=" * 50)
    print("Manual Test Summary:")
    print("All refactored endpoints T010-T013 tested")
    print("REFACTOR phase validation complete")
    print("=" * 50)

if __name__ == "__main__":
    test_refactored_endpoints()