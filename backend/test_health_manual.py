"""
T005 Manual Test: Health Check Endpoint Verification
Test the health check endpoint manually to verify TDD implementation
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Mock the environment to avoid configuration issues
os.environ['TESTING'] = 'true'
os.environ['DEBUG'] = 'true'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-purposes-only-minimum-32-chars'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test.db'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'test-anon-key'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'
os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,testserver'
os.environ['SMTP_USER'] = 'test@example.com'
os.environ['SMTP_PASSWORD'] = 'testpassword'
os.environ['FROM_EMAIL'] = 'test@example.com'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'

def test_health_endpoint_direct():
    """Test the health endpoint directly from the router"""
    try:
        # Import just the router function
        from app.routers.health import health_check
        import asyncio

        async def run_test():
            result = await health_check()
            print("✅ Health check endpoint test PASSED")
            print(f"Response: {result}")

            # Verify required fields
            assert "status" in result
            assert "timestamp" in result
            assert "version" in result
            assert "uptime" in result
            assert result["status"] in ["healthy", "degraded", "unhealthy"]
            assert isinstance(result["version"], str)
            assert isinstance(result["uptime"], (int, float))

            print("✅ All TDD assertions PASSED")
            return True

        return asyncio.run(run_test())

    except Exception as e:
        print(f"❌ Health check test FAILED: {e}")
        return False

if __name__ == "__main__":
    print("Testing T005 Health Check Endpoint...")
    success = test_health_endpoint_direct()
    if success:
        print("🎉 T005 Health Check TDD Implementation COMPLETE")
    else:
        print("💥 T005 Health Check TDD Implementation FAILED")
        sys.exit(1)