"""
T016: User Profile Management - TDD RED Phase Test
Expected to FAIL as profile management endpoints are not implemented yet
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid


class TestUserProfileManagement:
    """Test cases for user profile management endpoints - RED phase"""

    @pytest.fixture
    def authenticated_client(self, client: TestClient):
        """Helper to get authenticated client with valid token"""
        # Register and login a test user
        email = f"profile_test_{uuid.uuid4()}@example.com"
        password = "SecurePass123!"

        register_data = {
            "email": email,
            "password": password,
            "name": "Profile Test User",
            "pref_cd": "13"
        }

        # Register
        client.post("/api/v1/users/register", json=register_data)

        # Login
        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })

        # Get token (might fail in RED phase)
        token = login_response.json().get("access_token", "dummy_token")
        user_id = login_response.json().get("user", {}).get("user_id", 1)

        # Return client with auth headers
        client.headers = {"Authorization": f"Bearer {token}"}
        return client, user_id, email

    def test_get_user_profile(self, client: TestClient):
        """Test retrieving user's own profile"""
        # Arrange - Get authenticated client
        auth_client, user_id, email = self.authenticated_client(client)

        # Act
        response = auth_client.get("/api/v1/users/me")

        # Assert - These will fail initially (RED phase)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "user_id" in data, "Response should contain user_id"
        assert "email" in data, "Response should contain email"
        assert "name" in data, "Response should contain name"
        assert "pref_cd" in data, "Response should contain pref_cd"
        assert data["email"] == email, "Email should match"
        assert "password" not in data, "Password should not be exposed"
        assert "created_at" in data, "Should have created_at timestamp"
        assert "updated_at" in data, "Should have updated_at timestamp"

    def test_update_user_profile(self, client: TestClient):
        """Test updating user profile information"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        update_data = {
            "name": "Updated Name",
            "pref_cd": "27",  # Change to Osaka
            "birth_year": 1985,
            "gender": "M",
            "phone": "080-9999-8888",
            "job_search_status": "passive",
            "preferred_industries": ["Tech", "Consulting", "Finance"],
            "skills": ["Python", "JavaScript", "AWS", "Docker"]
        }

        # Act
        response = auth_client.put("/api/v1/users/me", json=update_data)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["name"] == "Updated Name", "Name should be updated"
        assert data["pref_cd"] == "27", "Prefecture should be updated"
        assert data["birth_year"] == 1985, "Birth year should be updated"
        assert data["gender"] == "M", "Gender should be updated"
        assert data["phone"] == "080-9999-8888", "Phone should be updated"
        assert data["job_search_status"] == "passive", "Job search status should be updated"
        assert set(data["preferred_industries"]) == {"Tech", "Consulting", "Finance"}
        assert set(data["skills"]) == {"Python", "JavaScript", "AWS", "Docker"}

    def test_partial_profile_update(self, client: TestClient):
        """Test partial update of user profile (PATCH)"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        # Only update specific fields
        patch_data = {
            "job_search_status": "active",
            "skills": ["Go", "Kubernetes"]
        }

        # Act
        response = auth_client.patch("/api/v1/users/me", json=patch_data)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["job_search_status"] == "active", "Job search status should be updated"
        assert set(data["skills"]) == {"Go", "Kubernetes"}, "Skills should be updated"
        # Other fields should remain unchanged
        assert data["email"] == email, "Email should not change"

    def test_update_email_requires_verification(self, client: TestClient):
        """Test that updating email requires verification"""
        # Arrange
        auth_client, user_id, old_email = self.authenticated_client(client)

        new_email = f"new_email_{uuid.uuid4()}@example.com"
        update_data = {
            "email": new_email
        }

        # Act
        response = auth_client.put("/api/v1/users/me", json=update_data)

        # Assert - Should not directly update email
        assert response.status_code == 202, f"Expected 202 (Accepted), got {response.status_code}"

        data = response.json()
        assert "message" in data
        assert "verification" in data["message"].lower()
        assert "verification_sent" in data
        assert data["verification_sent"] == True

    def test_change_password(self, client: TestClient):
        """Test password change endpoint"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        password_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!",
            "confirm_password": "NewSecurePass456!"
        }

        # Act
        response = auth_client.post("/api/v1/users/me/change-password", json=password_data)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower() or "changed" in data["message"].lower()

        # Verify can login with new password
        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "NewSecurePass456!"
        })
        assert login_response.status_code == 200, "Should be able to login with new password"

    def test_change_password_wrong_current(self, client: TestClient):
        """Test password change with incorrect current password"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewSecurePass456!",
            "confirm_password": "NewSecurePass456!"
        }

        # Act
        response = auth_client.post("/api/v1/users/me/change-password", json=password_data)

        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        error = response.json()
        assert "detail" in error
        assert "incorrect" in error["detail"].lower() or "wrong" in error["detail"].lower()

    def test_change_password_mismatch(self, client: TestClient):
        """Test password change with mismatched new passwords"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        password_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!",
            "confirm_password": "DifferentPass789!"  # Mismatch
        }

        # Act
        response = auth_client.post("/api/v1/users/me/change-password", json=password_data)

        # Assert
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        error = response.json()
        assert "detail" in error
        assert "match" in str(error["detail"]).lower()

    def test_delete_user_account(self, client: TestClient):
        """Test user account deletion (soft delete)"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        delete_data = {
            "password": "SecurePass123!",  # Require password confirmation
            "confirm": "DELETE MY ACCOUNT"  # Safety confirmation
        }

        # Act
        response = auth_client.delete("/api/v1/users/me", json=delete_data)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower() or "deactivated" in data["message"].lower()

        # Verify cannot login after deletion
        login_response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "SecurePass123!"
        })
        assert login_response.status_code == 401, "Should not be able to login after deletion"

    def test_get_user_preferences(self, client: TestClient):
        """Test retrieving user preferences/settings"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        # Act
        response = auth_client.get("/api/v1/users/me/preferences")

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "email_notifications" in data
        assert "job_alert_frequency" in data
        assert "preferred_job_types" in data
        assert "salary_range" in data
        assert "commute_time_max" in data

    def test_update_user_preferences(self, client: TestClient):
        """Test updating user preferences/settings"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        preferences = {
            "email_notifications": {
                "job_alerts": True,
                "newsletter": False,
                "system_updates": True
            },
            "job_alert_frequency": "weekly",
            "preferred_job_types": ["full_time", "remote"],
            "salary_range": {
                "min": 5000000,  # 500万円
                "max": 8000000   # 800万円
            },
            "commute_time_max": 60  # minutes
        }

        # Act
        response = auth_client.put("/api/v1/users/me/preferences", json=preferences)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["job_alert_frequency"] == "weekly"
        assert data["email_notifications"]["job_alerts"] == True
        assert data["email_notifications"]["newsletter"] == False
        assert data["salary_range"]["min"] == 5000000
        assert data["commute_time_max"] == 60

    def test_upload_profile_image(self, client: TestClient):
        """Test uploading user profile image"""
        # Arrange
        auth_client, user_id, email = self.authenticated_client(client)

        # Create a mock image file
        image_content = b"fake_image_content"
        files = {"file": ("profile.jpg", image_content, "image/jpeg")}

        # Act
        response = auth_client.post("/api/v1/users/me/profile-image", files=files)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "profile_image_url" in data
        assert data["profile_image_url"].startswith("http")
        assert "thumbnail_url" in data