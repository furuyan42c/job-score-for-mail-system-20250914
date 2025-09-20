#!/usr/bin/env python3
"""
T015: User Authentication Tests (RED Phase)

Comprehensive tests for user authentication including:
- Login/logout
- Token validation
- Session management
- Password reset
"""

import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user import User
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import json


class TestUserAuthentication:
    """Test suite for user authentication"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def test_user(self, client: AsyncClient):
        """Create a test user for authentication tests"""
        user_data = {
            "email": "auth_test@example.com",
            "password": "TestPass123!",
            "name": "Auth Test User"
        }
        response = await client.post("/auth/register", json=user_data)
        if response.status_code == 201:
            return {**user_data, **response.json()}
        return user_data

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login"""
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }

        response = await client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user["email"]

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with non-existent email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePass123!"
        }

        response = await client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "incorrect" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password"""
        login_data = {
            "email": test_user["email"],
            "password": "WrongPass123!"
        }

        response = await client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_case_insensitive_email(self, client: AsyncClient, test_user):
        """Test login with different case email"""
        login_data = {
            "email": test_user["email"].upper(),
            "password": test_user["password"]
        }

        response = await client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(self, client: AsyncClient, test_user):
        """Test accessing protected endpoint with valid token"""
        # Login to get token
        login_response = await client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        token = login_response.json()["access_token"]

        # Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["name"] == test_user["name"]
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token"""
        response = await client.get("/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_protected_endpoint_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_token_expiry(self, client: AsyncClient, test_user):
        """Test token expiration"""
        # Create expired token
        expired_token = create_access_token(
            data={"sub": test_user["email"]},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, test_user):
        """Test user logout"""
        # Login first
        login_response = await client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        token = login_response.json()["access_token"]

        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

        # Token should be blacklisted (attempting to use it should fail)
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user):
        """Test token refresh functionality"""
        # Login to get initial token
        login_response = await client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        initial_data = login_response.json()
        refresh_token = initial_data.get("refresh_token")

        # Use refresh token to get new access token
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != initial_data["access_token"]  # Should be different

    @pytest.mark.asyncio
    async def test_password_reset_request(self, client: AsyncClient, test_user):
        """Test password reset request"""
        response = await client.post("/auth/reset-password", json={
            "email": test_user["email"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reset" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_password_reset_with_token(self, client: AsyncClient, test_user):
        """Test password reset with valid token"""
        # Request reset
        reset_response = await client.post("/auth/reset-password", json={
            "email": test_user["email"]
        })
        assert reset_response.status_code == 200

        # Mock reset token (in real app would be sent via email)
        reset_token = "mock_reset_token"

        # Reset password
        new_password = "NewSecurePass456!"
        response = await client.post("/auth/reset-password/confirm", json={
            "token": reset_token,
            "new_password": new_password
        })

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Try login with new password
        login_response = await client.post("/auth/login", json={
            "email": test_user["email"],
            "password": new_password
        })
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limiting_login(self, client: AsyncClient):
        """Test rate limiting on login attempts"""
        login_data = {
            "email": "ratelimit@example.com",
            "password": "WrongPass!"
        }

        # Multiple failed login attempts
        responses = []
        for _ in range(10):
            response = await client.post("/auth/login", json=login_data)
            responses.append(response.status_code)

        # Should be rate limited after several attempts
        assert any(status == 429 for status in responses[5:])

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, client: AsyncClient, test_user):
        """Test multiple concurrent sessions"""
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }

        # Create multiple sessions
        tokens = []
        for _ in range(3):
            response = await client.post("/auth/login", json=login_data)
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])

        # All tokens should be valid
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/auth/me", headers=headers)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_password(self, client: AsyncClient, test_user):
        """Test password update for authenticated user"""
        # Login
        login_response = await client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        token = login_response.json()["access_token"]

        # Update password
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.put("/auth/update-password", json={
            "current_password": test_user["password"],
            "new_password": "UpdatedPass789!"
        }, headers=headers)

        assert response.status_code == 200

        # Login with new password
        new_login = await client.post("/auth/login", json={
            "email": test_user["email"],
            "password": "UpdatedPass789!"
        })
        assert new_login.status_code == 200