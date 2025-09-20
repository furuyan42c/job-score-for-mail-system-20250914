#!/usr/bin/env python3
"""
T014: User Registration Tests (RED Phase)

Comprehensive tests for user registration functionality including:
- User creation
- Input validation
- Duplicate prevention
- Email verification
"""

import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user import User
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json


class TestUserRegistration:
    """Test suite for user registration"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def db_session(self):
        """Get database session for tests"""
        async for session in get_db():
            yield session
            await session.rollback()

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "Test User",
            "preferences": {
                "location": "Tokyo",
                "job_type": "full_time"
            }
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == user_data["email"]
        assert "name" in data
        assert data["name"] == user_data["name"]
        assert "created_at" in data
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email"""
        user_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "name": "First User"
        }

        # First registration
        response1 = await client.post("/auth/register", json=user_data)
        assert response1.status_code == 201

        # Duplicate registration
        user_data["name"] = "Second User"
        response2 = await client.post("/auth/register", json=user_data)

        assert response2.status_code == 409
        data = response2.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format"""
        user_data = {
            "email": "not_an_email",
            "password": "SecurePass123!",
            "name": "Test User"
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("email" in str(error).lower() for error in data["detail"])

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password"""
        test_cases = [
            "123",  # Too short
            "password",  # No numbers
            "12345678",  # No letters
            "Pass123",  # No special characters
        ]

        for weak_password in test_cases:
            user_data = {
                "email": f"user_{weak_password}@example.com",
                "password": weak_password,
                "name": "Test User"
            }

            response = await client.post("/auth/register", json=user_data)

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_register_missing_required_fields(self, client: AsyncClient):
        """Test registration with missing required fields"""
        # Missing email
        response = await client.post("/auth/register", json={
            "password": "SecurePass123!",
            "name": "Test User"
        })
        assert response.status_code == 422

        # Missing password
        response = await client.post("/auth/register", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        assert response.status_code == 422

        # Missing name
        response = await client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_with_profile_data(self, client: AsyncClient):
        """Test registration with complete profile data"""
        user_data = {
            "email": "complete@example.com",
            "password": "SecurePass123!",
            "name": "Complete User",
            "preferences": {
                "location": "Tokyo",
                "job_type": "full_time",
                "salary_min": 300000,
                "salary_max": 600000,
                "industries": ["IT", "Finance"]
            },
            "profile": {
                "bio": "Experienced developer",
                "skills": ["Python", "JavaScript", "SQL"],
                "experience_years": 5
            }
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_register_email_normalization(self, client: AsyncClient):
        """Test email normalization during registration"""
        user_data = {
            "email": "  TEST@EXAMPLE.COM  ",
            "password": "SecurePass123!",
            "name": "Test User"
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"  # Should be normalized

    @pytest.mark.asyncio
    async def test_register_password_not_in_response(self, client: AsyncClient):
        """Test that password is never returned in response"""
        user_data = {
            "email": "secure@example.com",
            "password": "SecurePass123!",
            "name": "Secure User"
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()

        # Password should never be in response
        assert "password" not in data
        assert "hashed_password" not in data

        # But should return access token
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_register_creates_database_record(self, client: AsyncClient, db_session: AsyncSession):
        """Test that registration creates user in database"""
        user_data = {
            "email": "database@example.com",
            "password": "SecurePass123!",
            "name": "Database User"
        }

        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 201

        # Verify user exists in database
        result = await db_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.email == user_data["email"]
        assert user.name == user_data["name"]
        assert user.hashed_password is not None
        assert user.hashed_password != user_data["password"]  # Should be hashed

    @pytest.mark.asyncio
    async def test_register_rate_limiting(self, client: AsyncClient):
        """Test rate limiting on registration endpoint"""
        # Attempt multiple registrations rapidly
        responses = []
        for i in range(10):
            user_data = {
                "email": f"ratelimit{i}@example.com",
                "password": "SecurePass123!",
                "name": f"User {i}"
            }
            response = await client.post("/auth/register", json=user_data)
            responses.append(response.status_code)

        # Some should be rate limited (429)
        assert any(status == 429 for status in responses[5:])  # Later requests should be limited