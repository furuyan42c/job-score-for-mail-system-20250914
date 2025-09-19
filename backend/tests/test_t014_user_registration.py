"""
T014: User Registration - TDD RED Phase Test
Expected to FAIL as endpoint is not implemented yet
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid


class TestUserRegistration:
    """Test cases for user registration endpoint - RED phase"""

    def test_register_new_user_success(self, client: TestClient):
        """Test successful user registration with valid data"""
        # Arrange
        user_data = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "name": "Test User",
            "pref_cd": "13",  # Tokyo
            "birth_year": 1990,
            "gender": "M"
        }

        # Act
        response = client.post("/api/v1/users/register", json=user_data)

        # Assert - These will fail initially (RED phase)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        data = response.json()
        assert "user_id" in data, "Response should contain user_id"
        assert isinstance(data["user_id"], int), "user_id should be integer"
        assert data["email"] == user_data["email"], "Email should match"
        assert data["name"] == user_data["name"], "Name should match"
        assert "password" not in data, "Password should not be in response"
        assert "created_at" in data, "Should have created_at timestamp"

    def test_register_duplicate_email_fails(self, client: TestClient):
        """Test that duplicate email registration fails"""
        # Arrange
        email = f"duplicate_{uuid.uuid4()}@example.com"
        user_data = {
            "email": email,
            "password": "SecurePass123!",
            "name": "First User",
            "pref_cd": "13"
        }

        # First registration
        response1 = client.post("/api/v1/users/register", json=user_data)

        # Second registration with same email
        user_data["name"] = "Second User"
        response2 = client.post("/api/v1/users/register", json=user_data)

        # Assert - Expect 409 Conflict for duplicate
        assert response2.status_code == 409, f"Expected 409 for duplicate, got {response2.status_code}"
        error = response2.json()
        assert "detail" in error
        assert "already registered" in error["detail"].lower()

    def test_register_invalid_email_format(self, client: TestClient):
        """Test registration with invalid email format"""
        # Arrange
        user_data = {
            "email": "invalid-email",  # Missing @ and domain
            "password": "SecurePass123!",
            "name": "Test User",
            "pref_cd": "13"
        }

        # Act
        response = client.post("/api/v1/users/register", json=user_data)

        # Assert
        assert response.status_code == 422, "Should return 422 for invalid email"
        error = response.json()
        assert "detail" in error
        assert any("email" in str(err).lower() for err in error["detail"])

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        # Arrange
        user_data = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "weak",  # Too short, no special chars
            "name": "Test User",
            "pref_cd": "13"
        }

        # Act
        response = client.post("/api/v1/users/register", json=user_data)

        # Assert
        assert response.status_code == 422, "Should return 422 for weak password"
        error = response.json()
        assert "detail" in error
        # Password must be at least 8 characters with special chars

    def test_register_missing_required_fields(self, client: TestClient):
        """Test registration with missing required fields"""
        # Arrange - Missing password
        user_data = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "name": "Test User"
        }

        # Act
        response = client.post("/api/v1/users/register", json=user_data)

        # Assert
        assert response.status_code == 422, "Should return 422 for missing fields"
        error = response.json()
        assert "detail" in error

    def test_register_invalid_pref_code(self, client: TestClient):
        """Test registration with invalid prefecture code"""
        # Arrange
        user_data = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "name": "Test User",
            "pref_cd": "99"  # Invalid code (valid: 01-47)
        }

        # Act
        response = client.post("/api/v1/users/register", json=user_data)

        # Assert
        assert response.status_code == 422, "Should return 422 for invalid pref_cd"
        error = response.json()
        assert "detail" in error

    def test_register_with_optional_fields(self, client: TestClient):
        """Test registration with all optional fields provided"""
        # Arrange
        user_data = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "name": "Test User",
            "pref_cd": "13",
            "birth_year": 1990,
            "gender": "F",
            "phone": "090-1234-5678",
            "job_search_status": "active",
            "preferred_industries": ["IT", "Finance"],
            "skills": ["Python", "SQL", "Docker"]
        }

        # Act
        response = client.post("/api/v1/users/register", json=user_data)

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert data["birth_year"] == 1990
        assert data["gender"] == "F"
        assert "phone" in data