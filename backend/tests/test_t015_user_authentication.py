"""
T015: User Authentication - TDD RED Phase Test
Expected to FAIL as authentication endpoints are not implemented yet
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import uuid
import jwt


class TestUserAuthentication:
    """Test cases for user authentication endpoints - RED phase"""

    def test_login_with_valid_credentials(self, client: TestClient):
        """Test successful login with valid email and password"""
        # Arrange - First register a user
        email = f"auth_test_{uuid.uuid4()}@example.com"
        password = "SecurePass123!"
        register_data = {
            "email": email,
            "password": password,
            "name": "Auth Test User",
            "pref_cd": "13"
        }

        # Register user first (this might also fail in RED phase)
        client.post("/api/v1/users/register", json=register_data)

        # Act - Attempt login
        login_data = {
            "email": email,
            "password": password
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert - These will fail initially (RED phase)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "refresh_token" in data, "Response should contain refresh_token"
        assert "token_type" in data, "Response should contain token_type"
        assert data["token_type"] == "bearer", "Token type should be bearer"
        assert "expires_in" in data, "Response should contain expiration time"
        assert "user" in data, "Response should contain user info"
        assert data["user"]["email"] == email, "User email should match"

    def test_login_with_invalid_password(self, client: TestClient):
        """Test login failure with incorrect password"""
        # Arrange
        email = f"auth_test_{uuid.uuid4()}@example.com"
        correct_password = "SecurePass123!"
        wrong_password = "WrongPassword123!"

        # Register user
        register_data = {
            "email": email,
            "password": correct_password,
            "name": "Auth Test User",
            "pref_cd": "13"
        }
        client.post("/api/v1/users/register", json=register_data)

        # Act - Attempt login with wrong password
        login_data = {
            "email": email,
            "password": wrong_password
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        error = response.json()
        assert "detail" in error
        assert "invalid" in error["detail"].lower() or "incorrect" in error["detail"].lower()

    def test_login_with_nonexistent_user(self, client: TestClient):
        """Test login failure with non-existent email"""
        # Arrange
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        error = response.json()
        assert "detail" in error

    def test_refresh_token_endpoint(self, client: TestClient):
        """Test token refresh with valid refresh token"""
        # Arrange - First login to get refresh token
        email = f"refresh_test_{uuid.uuid4()}@example.com"
        password = "SecurePass123!"

        # Register and login
        register_data = {
            "email": email,
            "password": password,
            "name": "Refresh Test User",
            "pref_cd": "13"
        }
        client.post("/api/v1/users/register", json=register_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })

        # Get refresh token (might fail in RED phase)
        refresh_token = login_response.json().get("refresh_token", "dummy_token")

        # Act - Use refresh token to get new access token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "access_token" in data, "Should return new access token"
        assert "expires_in" in data, "Should include expiration time"

    def test_logout_endpoint(self, client: TestClient):
        """Test logout endpoint"""
        # Arrange - First login to get token
        email = f"logout_test_{uuid.uuid4()}@example.com"
        password = "SecurePass123!"

        # Register and login
        register_data = {
            "email": email,
            "password": password,
            "name": "Logout Test User",
            "pref_cd": "13"
        }
        client.post("/api/v1/users/register", json=register_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })

        # Get access token (might fail in RED phase)
        access_token = login_response.json().get("access_token", "dummy_token")

        # Act - Logout with token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower() or "logged out" in data["message"].lower()

    def test_protected_endpoint_with_valid_token(self, client: TestClient):
        """Test accessing protected endpoint with valid token"""
        # Arrange - Get valid token
        email = f"protected_test_{uuid.uuid4()}@example.com"
        password = "SecurePass123!"

        register_data = {
            "email": email,
            "password": password,
            "name": "Protected Test User",
            "pref_cd": "13"
        }
        client.post("/api/v1/users/register", json=register_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })

        access_token = login_response.json().get("access_token", "dummy_token")

        # Act - Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["email"] == email

    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token"""
        # Act
        response = client.get("/api/v1/users/me")

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        error = response.json()
        assert "detail" in error
        assert "not authenticated" in error["detail"].lower() or "unauthorized" in error["detail"].lower()

    def test_protected_endpoint_with_expired_token(self, client: TestClient):
        """Test accessing protected endpoint with expired token"""
        # Arrange - Create an expired token (mock)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.4Adcj3UFYzPUVaVF43FmMab6RlaQD8A9V8wFzzht-KQ"

        # Act
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        error = response.json()
        assert "detail" in error
        assert "expired" in error["detail"].lower() or "invalid" in error["detail"].lower()

    def test_rate_limiting_on_login(self, client: TestClient):
        """Test rate limiting on failed login attempts"""
        # Arrange
        email = "ratelimit@example.com"
        wrong_password = "WrongPassword!"

        # Act - Multiple failed login attempts
        for i in range(6):  # Assume limit is 5 attempts
            response = client.post("/api/v1/auth/login", json={
                "email": email,
                "password": wrong_password
            })

            if i < 5:
                assert response.status_code == 401, f"Attempt {i+1}: Expected 401"
            else:
                # After 5 attempts, should be rate limited
                assert response.status_code == 429, f"Attempt {i+1}: Expected 429 (Too Many Requests)"
                error = response.json()
                assert "detail" in error
                assert "rate limit" in error["detail"].lower() or "too many" in error["detail"].lower()