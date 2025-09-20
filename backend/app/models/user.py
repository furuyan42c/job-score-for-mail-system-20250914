#!/usr/bin/env python3
"""
T017: User Model (REFACTORED)

User model with authentication, preferences, and subscription management.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base

logger = logging.getLogger(__name__)


class User(Base):
    """User model for users table"""

    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_active", "is_active"),
        {"extend_existing": True},
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Required fields from tests
    user_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)

    # Status fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))

    # JSON fields
    preferences = Column(JSON, default={})
    search_history = Column(JSON, default=[])
    notification_settings = Column(JSON, default={})

    # Subscription
    subscription_type = Column(String, default="free")
    subscription_expires_at = Column(DateTime(timezone=True))

    # Relationships
    job_matches = relationship("UserJobMatch", back_populates="user")
    saved_jobs = relationship("SavedJob", back_populates="user")
    email_preferences = relationship("EmailPreference", back_populates="user")
    search_alerts = relationship("SearchAlert", back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        if not self.hashed_password:
            return False
        try:
            from app.core.security import verify_password

            return verify_password(password, self.hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    def set_preference(self, key: str, value: Any) -> None:
        """Set user preference.

        Args:
            key: Preference key
            value: Preference value
        """
        if self.preferences is None:
            self.preferences = {}
        self.preferences = {**self.preferences, key: value}  # Ensure SQLAlchemy detects change

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference.

        Args:
            key: Preference key
            default: Default value if key not found

        Returns:
            Preference value or default
        """
        if not self.preferences:
            return default
        return self.preferences.get(key, default)

    # Configuration constants
    MAX_SEARCH_HISTORY = 100
    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    def add_search_history(self, search_data: dict) -> None:
        """Add to search history, maintaining max history limit.

        Args:
            search_data: Search information to store
        """
        if self.search_history is None:
            self.search_history = []

        # Create new list to ensure SQLAlchemy detects change
        new_history = [search_data] + (self.search_history or [])
        self.search_history = new_history[: self.MAX_SEARCH_HISTORY]

    def get_search_history(self, limit: int = 10):
        """Get search history"""
        if not self.search_history:
            return []
        return self.search_history[:limit]

    def update_notification_settings(self, settings: dict):
        """Update notification settings"""
        if not self.notification_settings:
            self.notification_settings = {}
        self.notification_settings.update(settings)

    def extend_subscription(self, days: int):
        """Extend subscription"""
        if not self.subscription_expires_at or self.subscription_expires_at < datetime.utcnow():
            self.subscription_expires_at = datetime.utcnow() + timedelta(days=days)
        else:
            self.subscription_expires_at = self.subscription_expires_at + timedelta(days=days)

    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        if self.subscription_type != "premium":
            return False
        if not self.subscription_expires_at:
            return False
        return self.subscription_expires_at > datetime.utcnow()

    @validates("email")
    def validate_email(self, key: str, email: str) -> str:
        """Validate email format on assignment.

        Args:
            key: Field name (email)
            email: Email value to validate

        Returns:
            Validated email

        Raises:
            ValueError: If email format is invalid
        """
        if not email or not re.match(self.EMAIL_REGEX, email):
            raise ValueError(f"Invalid email format: {email}")
        return email.lower()  # Normalize to lowercase

    async def check_email_unique(self, db_session):
        """Check if email is unique"""
        from sqlalchemy import select

        result = await db_session.execute(
            select(User).where(User.email == self.email).where(User.id != self.id)
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()

    def to_dict(
        self, exclude_sensitive: bool = True, include_preferences: bool = False
    ) -> Dict[str, Any]:
        """Convert user to dictionary representation.

        Args:
            exclude_sensitive: Whether to exclude sensitive data
            include_preferences: Whether to include user preferences

        Returns:
            Dictionary representation of user
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "subscription_type": self.subscription_type,
            "is_premium": self.is_premium(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

        if include_preferences and self.preferences:
            data["preferences"] = self.preferences

        if not exclude_sensitive:
            data["hashed_password"] = self.hashed_password
            data["search_history_count"] = len(self.search_history) if self.search_history else 0

        return data


# UserJobMatch is defined in app/models/job.py


class SavedJob(Base):
    """Saved jobs"""

    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    job_id = Column(Integer)

    user = relationship("User", back_populates="saved_jobs")


class EmailPreference(Base):
    """Email preferences"""

    __tablename__ = "email_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)

    user = relationship("User", back_populates="email_preferences")


class SearchAlert(Base):
    """Search alerts"""

    __tablename__ = "search_alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)

    user = relationship("User", back_populates="search_alerts")
