#!/usr/bin/env python3
"""
T017: User Model Tests (RED Phase)

Tests for the User model including:
- Model structure and fields
- Authentication and authorization
- User preferences
- CRUD operations
- Relationships
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.base import Base
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password


class TestUserModel:
    """Test suite for User model"""

    @pytest.fixture
    async def db_session(self):
        """Create test database session"""
        async for session in get_db():
            yield session
            await session.rollback()

    def test_user_model_exists(self):
        """Test that User model is defined"""
        assert User is not None
        assert hasattr(User, '__tablename__')
        assert User.__tablename__ == 'users'

    def test_user_model_fields(self):
        """Test that User model has all required fields"""
        required_fields = [
            'id', 'user_id', 'email', 'name', 'hashed_password',
            'is_active', 'is_verified', 'created_at', 'updated_at',
            'last_login_at', 'preferences', 'search_history',
            'notification_settings', 'subscription_type',
            'subscription_expires_at'
        ]
        
        for field in required_fields:
            assert hasattr(User, field), f"User model missing field: {field}"

    def test_user_model_relationships(self):
        """Test that User model has proper relationships"""
        assert hasattr(User, 'job_matches')
        assert hasattr(User, 'saved_jobs')
        assert hasattr(User, 'email_preferences')
        assert hasattr(User, 'search_alerts')

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user"""
        user = User(
            user_id="USER001",
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("password123")
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_verified is False

    @pytest.mark.asyncio
    async def test_user_authentication(self, db_session: AsyncSession):
        """Test user authentication"""
        password = "secure_password_123"
        user = User(
            user_id="AUTH001",
            email="auth@example.com",
            name="Auth User",
            hashed_password=get_password_hash(password)
        )
        
        db_session.add(user)
        await db_session.commit()
        
        # Test password verification
        assert user.verify_password(password) is True
        assert user.verify_password("wrong_password") is False

    @pytest.mark.asyncio
    async def test_user_preferences(self, db_session: AsyncSession):
        """Test user preferences management"""
        user = User(
            user_id="PREF001",
            email="pref@example.com",
            name="Pref User"
        )
        
        # Set preferences
        user.set_preference('job_type', ['full_time', 'contract'])
        user.set_preference('location', 'Tokyo')
        user.set_preference('min_salary', 400000)
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Get preferences
        assert user.get_preference('job_type') == ['full_time', 'contract']
        assert user.get_preference('location') == 'Tokyo'
        assert user.get_preference('min_salary') == 400000
        assert user.get_preference('non_existent') is None

    @pytest.mark.asyncio
    async def test_user_search_history(self, db_session: AsyncSession):
        """Test user search history tracking"""
        user = User(
            user_id="SEARCH001",
            email="search@example.com",
            name="Search User"
        )
        
        # Add search history
        user.add_search_history({
            'query': 'Python developer',
            'filters': {'location': 'Tokyo', 'salary_min': 400000},
            'timestamp': datetime.utcnow()
        })
        
        user.add_search_history({
            'query': 'Data scientist',
            'filters': {'location': 'Osaka'},
            'timestamp': datetime.utcnow()
        })
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Check search history
        history = user.get_search_history(limit=10)
        assert len(history) == 2
        assert history[0]['query'] == 'Data scientist'  # Most recent first

    @pytest.mark.asyncio
    async def test_user_notification_settings(self, db_session: AsyncSession):
        """Test user notification settings"""
        user = User(
            user_id="NOTIF001",
            email="notif@example.com",
            name="Notif User"
        )
        
        # Set notification settings
        user.update_notification_settings({
            'email_daily_digest': True,
            'email_job_alerts': True,
            'email_marketing': False,
            'push_notifications': True
        })
        
        db_session.add(user)
        await db_session.commit()
        
        assert user.notification_settings['email_daily_digest'] is True
        assert user.notification_settings['email_marketing'] is False

    @pytest.mark.asyncio
    async def test_user_subscription(self, db_session: AsyncSession):
        """Test user subscription management"""
        user = User(
            user_id="SUB001",
            email="sub@example.com",
            name="Sub User",
            subscription_type="premium"
        )
        
        # Set subscription expiry
        from datetime import timedelta
        user.extend_subscription(days=30)
        
        db_session.add(user)
        await db_session.commit()
        
        assert user.subscription_type == "premium"
        assert user.is_premium() is True
        assert user.subscription_expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_user_email_validation(self, db_session: AsyncSession):
        """Test email validation"""
        # Test invalid email
        with pytest.raises(ValueError, match="Invalid email format"):
            user = User(
                user_id="EMAIL001",
                email="invalid-email",
                name="Invalid User"
            )
            user.validate_email()

        # Test duplicate email
        user1 = User(
            user_id="EMAIL002",
            email="duplicate@example.com",
            name="User 1"
        )
        db_session.add(user1)
        await db_session.commit()
        
        with pytest.raises(ValueError, match="Email already registered"):
            user2 = User(
                user_id="EMAIL003",
                email="duplicate@example.com",
                name="User 2"
            )
            await user2.check_email_unique(db_session)

    @pytest.mark.asyncio
    async def test_user_update_last_login(self, db_session: AsyncSession):
        """Test updating last login timestamp"""
        user = User(
            user_id="LOGIN001",
            email="login@example.com",
            name="Login User"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        # Update last login
        old_login = user.last_login_at
        user.update_last_login()
        await db_session.commit()
        
        assert user.last_login_at is not None
        assert user.last_login_at > old_login if old_login else True

    def test_user_serialization(self):
        """Test user serialization to dict"""
        user = User(
            user_id="SERIAL001",
            email="serial@example.com",
            name="Serial User",
            subscription_type="free"
        )
        
        user_dict = user.to_dict(exclude_sensitive=True)
        
        assert user_dict['user_id'] == "SERIAL001"
        assert user_dict['email'] == "serial@example.com"
        assert 'hashed_password' not in user_dict  # Sensitive data excluded
        assert 'created_at' in user_dict
