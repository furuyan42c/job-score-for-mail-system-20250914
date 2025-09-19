"""
Integration tests for user authentication and management system
Tests the complete TDD implementation of T014-T020
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.main import app
from app.core.database import get_db
from app.models.database import User, UserProfile, MatchHistory
from app.core.security import hash_password


class TestUserAuthenticationIntegration:
    """Integration tests for user authentication system"""

    def test_complete_user_lifecycle(self, client: TestClient, db: Session):
        """Test complete user lifecycle: register -> login -> profile -> auth endpoints"""

        # 1. User Registration
        email = f"lifecycle_test_{uuid.uuid4()}@example.com"
        registration_data = {
            "email": email,
            "password": "SecurePass123!",
            "name": "Test User",
            "pref_cd": "13",
            "birth_year": 1990,
            "gender": "M",
            "skills": ["Python", "SQL", "FastAPI"]
        }

        register_response = client.post("/api/v1/users/register", json=registration_data)
        assert register_response.status_code == 201

        user_data = register_response.json()
        assert user_data["email"] == email
        assert user_data["name"] == "Test User"
        assert "password" not in user_data  # Password should not be returned

        # 2. Login with correct credentials
        login_data = {
            "email": email,
            "password": "SecurePass123!"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        login_result = login_response.json()
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        assert login_result["token_type"] == "bearer"

        access_token = login_result["access_token"]
        refresh_token = login_result["refresh_token"]

        # 3. Access protected endpoints
        headers = {"Authorization": f"Bearer {access_token}"}

        profile_response = client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == 200

        profile_data = profile_response.json()
        assert profile_data["email"] == email
        assert profile_data["skills"] == ["Python", "SQL", "FastAPI"]

        # 4. Update profile
        update_data = {
            "name": "Updated Name",
            "skills": ["Python", "SQL", "FastAPI", "Docker"]
        }

        update_response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        assert update_response.status_code == 200

        updated_profile = update_response.json()
        assert updated_profile["name"] == "Updated Name"
        assert "Docker" in updated_profile["skills"]

        # 5. Change password
        password_change_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!"
        }

        password_response = client.post("/api/v1/users/me/change-password",
                                      json=password_change_data, headers=headers)
        assert password_response.status_code == 200

        # 6. Refresh token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200

        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens

        # 7. Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 200

        # 8. Verify token is invalidated
        protected_response = client.get("/api/v1/users/me", headers=headers)
        assert protected_response.status_code == 401

    def test_authentication_security_features(self, client: TestClient):
        """Test security features like rate limiting and password validation"""

        # Test password strength validation
        weak_password_data = {
            "email": "weak_test@example.com",
            "password": "weak",
            "name": "Test User",
            "pref_cd": "13"
        }

        weak_response = client.post("/api/v1/users/register", json=weak_password_data)
        assert weak_response.status_code == 422

        # Test rate limiting on login attempts
        email = "ratelimit_test@example.com"

        # Register user first
        registration_data = {
            "email": email,
            "password": "SecurePass123!",
            "name": "Rate Limit Test",
            "pref_cd": "13"
        }
        client.post("/api/v1/users/register", json=registration_data)

        # Multiple failed login attempts
        wrong_login_data = {
            "email": email,
            "password": "WrongPassword123!"
        }

        for i in range(6):  # Exceed rate limit (5 attempts)
            response = client.post("/api/v1/auth/login", json=wrong_login_data)

            if i < 5:
                assert response.status_code == 401
            else:
                assert response.status_code == 429  # Rate limited

        # Test duplicate email registration
        duplicate_response = client.post("/api/v1/users/register", json=registration_data)
        assert duplicate_response.status_code == 409

    def test_authorization_roles(self, client: TestClient, db: Session):
        """Test role-based authorization"""

        # Create admin user directly in database
        admin_email = "admin@example.com"
        admin_user = User(
            email=admin_email,
            password_hash=hash_password("AdminPass123!"),
            name="Admin User",
            role="admin",
            pref_cd="13",
            is_active=True
        )
        db.add(admin_user)
        db.commit()

        # Login as admin
        admin_login = client.post("/api/v1/auth/login", json={
            "email": admin_email,
            "password": "AdminPass123!"
        })
        assert admin_login.status_code == 200

        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Test admin-only endpoints
        admin_response = client.get("/api/v1/auth/admin/login-attempts", headers=admin_headers)
        assert admin_response.status_code == 200

        # Test regular user cannot access admin endpoints
        regular_email = f"regular_{uuid.uuid4()}@example.com"
        regular_registration = {
            "email": regular_email,
            "password": "RegularPass123!",
            "name": "Regular User",
            "pref_cd": "13"
        }

        client.post("/api/v1/users/register", json=regular_registration)

        regular_login = client.post("/api/v1/auth/login", json={
            "email": regular_email,
            "password": "RegularPass123!"
        })

        regular_token = regular_login.json()["access_token"]
        regular_headers = {"Authorization": f"Bearer {regular_token}"}

        unauthorized_response = client.get("/api/v1/auth/admin/login-attempts", headers=regular_headers)
        assert unauthorized_response.status_code == 403


class TestMatchingSystemIntegration:
    """Integration tests for matching system"""

    def test_basic_matching_algorithm(self, client: TestClient, db: Session):
        """Test basic skills-based matching algorithm"""

        from app.algorithms.basic_matching import BasicMatchingAlgorithm, UserProfile, JobData

        algorithm = BasicMatchingAlgorithm()

        # Create test user profile
        user_profile = UserProfile(
            user_id=1,
            skills=["Python", "SQL", "FastAPI"],
            preferred_categories=["IT", "Software"],
            preferred_location="Tokyo",
            prefecture_code="13",
            salary_min=4000000,
            max_commute_distance=30,
            experience_level="mid",
            job_types=["full_time"]
        )

        # Create test job data
        job_data = JobData(
            job_id=1,
            title="Python Developer",
            required_skills=["Python", "SQL"],
            preferred_skills=["FastAPI", "Docker"],
            category="IT",
            location="Tokyo",
            prefecture_code="13",
            salary_min=3500000,
            salary_max=5500000,
            experience_required="mid",
            employment_type="full_time",
            description="Python developer position"
        )

        # Calculate match score
        score = algorithm.calculate_match_score(user_profile, job_data)

        assert score.total_score > 70  # Should be a good match
        assert score.skills_score > 70  # Good skills match
        assert score.location_score == 100  # Perfect location match
        assert score.salary_score > 70  # Good salary match
        assert score.category_score == 100  # Perfect category match

    def test_weighted_matching_algorithm(self, client: TestClient, db: Session):
        """Test advanced weighted matching algorithm"""

        from app.algorithms.weighted_matching import WeightedMatchingAlgorithm, UserBehaviorData
        from app.algorithms.basic_matching import UserProfile, JobData

        algorithm = WeightedMatchingAlgorithm()

        # Create test data
        user_profile = UserProfile(
            user_id=1,
            skills=["Python", "Machine Learning"],
            preferred_categories=["IT", "Data Science"],
            preferred_location="Tokyo",
            prefecture_code="13",
            salary_min=5000000,
            max_commute_distance=30,
            experience_level="senior",
            job_types=["full_time"]
        )

        user_behavior = UserBehaviorData(
            user_id=1,
            job_applications=[101, 102],
            job_clicks=[101, 102, 103, 104],
            job_views=[101, 102, 103, 104, 105],
            feedback_history={101: "interested", 102: "applied", 103: "not_interested"}
        )

        job_data = JobData(
            job_id=1,
            title="Senior Data Scientist",
            required_skills=["Python", "Machine Learning"],
            preferred_skills=["TensorFlow", "Pandas"],
            category="IT",
            location="Tokyo",
            prefecture_code="13",
            salary_min=5000000,
            salary_max=8000000,
            experience_required="senior",
            employment_type="full_time",
            description="Senior data scientist position"
        )

        # Calculate weighted score
        score = algorithm.calculate_weighted_score(user_profile, job_data, user_behavior)

        assert score.total_score > 75  # Should be a very good match with behavior data
        assert "weighted_matching" in score.details["algorithm"]
        assert "personalized_weights" in score.details

    def test_matching_service_integration(self, client: TestClient, db: Session):
        """Test matching service with filtering and sorting"""

        from app.services.matching_service import MatchingService, MatchFilter, SortOrder, AlgorithmType

        service = MatchingService(db)

        # Create test user
        user_email = f"matching_test_{uuid.uuid4()}@example.com"
        user = User(
            email=user_email,
            password_hash=hash_password("TestPass123!"),
            name="Matching Test User",
            pref_cd="13",
            skills=["Python", "SQL"],
            preferred_industries=["IT"],
            is_active=True
        )
        db.add(user)
        db.commit()

        # Test finding matches
        filters = MatchFilter(
            min_score=50,
            categories=["IT"],
            exclude_applied=True
        )

        matches = await service.find_matches(
            user_id=user.user_id,
            algorithm=AlgorithmType.BASIC,
            limit=10,
            filters=filters,
            sort_order=SortOrder.SCORE_DESC
        )

        assert isinstance(matches, list)
        # Even with mock data, should return some structure

        # Test match history
        history = await service.get_match_history(user.user_id, limit=50)
        assert isinstance(history, list)

        # Test recording interactions
        success = await service.record_interaction(
            user_id=user.user_id,
            job_id=1,
            interaction_type="viewed",
            feedback="interested"
        )
        assert success is True

        # Test metrics
        metrics = await service.get_recommendation_metrics(user.user_id, days=30)
        assert "total_matches" in metrics
        assert "interactions" in metrics
        assert "rates" in metrics

    def test_match_history_tracking(self, client: TestClient, db: Session):
        """Test comprehensive match history tracking"""

        # Create test user
        user_email = f"history_test_{uuid.uuid4()}@example.com"
        user = User(
            email=user_email,
            password_hash=hash_password("TestPass123!"),
            name="History Test User",
            pref_cd="13",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Create match history records
        history_records = [
            MatchHistory(
                user_id=user.user_id,
                job_id=1,
                match_score=85,
                algorithm_used="basic",
                match_rank=1,
                viewed=True,
                clicked=True,
                applied=True,
                viewed_at=datetime.utcnow(),
                clicked_at=datetime.utcnow(),
                applied_at=datetime.utcnow(),
                user_feedback="interested"
            ),
            MatchHistory(
                user_id=user.user_id,
                job_id=2,
                match_score=75,
                algorithm_used="weighted",
                match_rank=2,
                viewed=True,
                clicked=False,
                applied=False,
                viewed_at=datetime.utcnow(),
                user_feedback="maybe"
            ),
            MatchHistory(
                user_id=user.user_id,
                job_id=3,
                match_score=65,
                algorithm_used="basic",
                match_rank=3,
                viewed=True,
                clicked=True,
                applied=False,
                viewed_at=datetime.utcnow(),
                clicked_at=datetime.utcnow(),
                user_feedback="not_interested",
                feedback_reason="salary_too_low"
            )
        ]

        for record in history_records:
            db.add(record)
        db.commit()

        # Query match history
        from app.services.matching_service import MatchingService
        service = MatchingService(db)

        history = await service.get_match_history(user.user_id, limit=10, include_interactions=True)

        assert len(history) == 3

        # Verify first record (most engaged)
        first_record = next(h for h in history if h["job_id"] == 1)
        assert first_record["viewed"] is True
        assert first_record["clicked"] is True
        assert first_record["applied"] is True
        assert first_record["user_feedback"] == "interested"

        # Test metrics calculation
        metrics = await service.get_recommendation_metrics(user.user_id, days=30)

        assert metrics["total_matches"] == 3
        assert metrics["interactions"]["viewed"] == 3
        assert metrics["interactions"]["clicked"] == 2
        assert metrics["interactions"]["applied"] == 1
        assert metrics["rates"]["view_rate"] == 1.0  # All viewed
        assert metrics["rates"]["click_through_rate"] == 2/3  # 2 out of 3 clicked
        assert metrics["rates"]["application_rate"] == 1/2  # 1 out of 2 applied
        assert metrics["feedback"]["positive"] == 1
        assert metrics["feedback"]["negative"] == 1
        assert metrics["avg_match_score"] == 75.0  # (85+75+65)/3