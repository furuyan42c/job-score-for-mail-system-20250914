"""
T005 RED Phase: Simple Health Check Test
- Verify that current endpoint fails
- Minimal test to confirm RED phase
"""
import os
os.environ["ENV_FILE"] = ".env.test"
os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient

# Import after setting environment
from app.main import app

client = TestClient(app)

def test_health_check_endpoint_404():
    """RED: Test that /api/v1/health/check does not exist yet (should return 404)"""
    response = client.get("/api/v1/health/check")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    # This should fail with 404 since endpoint doesn't exist yet
    assert response.status_code == 404  # RED: Should fail as endpoint doesn't exist

if __name__ == "__main__":
    test_health_check_endpoint_404()
    print("RED phase confirmed: endpoint does not exist")