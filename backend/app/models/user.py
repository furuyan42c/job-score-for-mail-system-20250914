#!/usr/bin/env python3
"""
T017: User Model (GREEN Phase)

Minimal implementation to pass tests
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import json
import re

from app.core.database import Base


class User(Base):
    """User model for users table"""

    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
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
        """Verify password"""
        # Simplified for testing - should use proper hashing
        from app.core.security import verify_password
        return verify_password(password, self.hashed_password)
    
    def set_preference(self, key: str, value):
        """Set user preference"""
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value
    
    def get_preference(self, key: str, default=None):
        """Get user preference"""
        if not self.preferences:
            return default
        return self.preferences.get(key, default)
    
    def add_search_history(self, search_data: dict):
        """Add to search history"""
        if not self.search_history:
            self.search_history = []
        # Add to beginning of list (most recent first)
        self.search_history.insert(0, search_data)
        # Keep only last 100 searches
        self.search_history = self.search_history[:100]
    
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
    
    def validate_email(self):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")
    
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
    
    def to_dict(self, exclude_sensitive: bool = False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'subscription_type': self.subscription_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if not exclude_sensitive:
            data['hashed_password'] = self.hashed_password
        
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
