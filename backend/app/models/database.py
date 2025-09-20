"""
Enhanced database models for authentication and user management
Includes password hashing, roles, and extended user functionality
"""

from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserRole(str, Enum):
    """User role enumeration"""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class User(Base):
    """Enhanced user model with authentication fields"""

    __tablename__ = "users"

    # Primary Key
    user_id = Column(Integer, primary_key=True, autoincrement=True)

    # Authentication fields
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)

    # Basic user information
    name = Column(String(100), nullable=False)
    email_hash = Column(String(256), nullable=True, index=True)

    # Optional profile fields
    pref_cd = Column(String(2), nullable=True)  # Prefecture code
    birth_year = Column(Integer, nullable=True)
    gender = Column(String(1), nullable=True)  # M/F
    phone = Column(String(20), nullable=True)

    # Job search related fields
    job_search_status = Column(String(20), nullable=True)  # active, passive, not_searching
    preferred_industries = Column(ARRAY(String), nullable=True)
    skills = Column(ARRAY(String), nullable=True)

    # Location information (legacy fields)
    estimated_pref_cd = Column(String(2), nullable=True)
    estimated_city_cd = Column(String(5), nullable=True)

    # Status information
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    registration_date = Column(Date, nullable=False, default=func.current_date())
    last_login_date = Column(DateTime(timezone=True), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # Subscription settings
    email_subscription = Column(Boolean, default=True, nullable=False)

    # System timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    profile = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    matching_scores = relationship(
        "MatchingScore", back_populates="user", cascade="all, delete-orphan"
    )
    match_history = relationship(
        "MatchHistory", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email='{self.email}', role='{self.role}', active={self.is_active})>"


class UserProfile(Base):
    """Enhanced user profile model"""

    __tablename__ = "user_profiles"

    # Primary Key
    profile_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)

    # Profile information
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Preferences data (JSON)
    preference_scores = Column(JSONB, nullable=True, default={})
    category_interests = Column(JSONB, nullable=True, default={})

    # Location preferences
    location_preference_radius = Column(Integer, default=10)
    preferred_areas = Column(ARRAY(String), nullable=True, default=[])

    # Statistics
    avg_salary_preference = Column(Integer, nullable=True)
    application_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Machine learning features
    latent_factors = Column(ARRAY(Float), nullable=True, default=[])
    behavioral_cluster = Column(Integer, nullable=True)

    # Email engagement
    email_open_rate = Column(Numeric(5, 4), nullable=True)  # Decimal 0.0000 to 1.0000
    last_application_date = Column(Date, nullable=True)

    # System timestamps
    profile_updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, display_name='{self.display_name}')>"


class UserPreferences(Base):
    """Enhanced user preferences model"""

    __tablename__ = "user_preferences"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)

    # Work style preferences
    preferred_work_styles = Column(ARRAY(String), nullable=True, default=[])
    preferred_categories = Column(ARRAY(Integer), nullable=True, default=[])
    preferred_areas = Column(ARRAY(String), nullable=True, default=[])

    # Salary preferences
    preferred_salary_min = Column(Integer, nullable=True)
    preferred_salary_max = Column(Integer, nullable=True)

    # Location preferences
    location_preference_radius = Column(Integer, default=10)

    # Notification preferences
    email_notifications = Column(
        JSONB,
        nullable=True,
        default={"job_alerts": True, "newsletter": False, "system_updates": True},
    )
    job_alert_frequency = Column(String(20), default="weekly")  # daily, weekly, monthly

    # Job type preferences
    preferred_job_types = Column(ARRAY(String), nullable=True, default=[])
    commute_time_max = Column(Integer, default=60)  # minutes

    # System timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, salary_min={self.preferred_salary_min})>"


class MatchingScore(Base):
    """Enhanced matching score model"""

    __tablename__ = "matching_scores"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    job_id = Column(Integer, nullable=False, index=True)  # Reference to job_data table

    # Algorithm version and type
    algorithm_version = Column(String(50), nullable=False, default="v1.0")
    score_type = Column(String(50), nullable=False, default="basic")  # basic, weighted, advanced

    # Score data
    basic_score = Column(Integer, nullable=True)
    weighted_score = Column(Integer, nullable=True)
    personalized_score = Column(Integer, nullable=True)
    composite_score = Column(Integer, nullable=True)

    # Component scores (for detailed analysis)
    skill_match_score = Column(Integer, nullable=True)
    location_score = Column(Integer, nullable=True)
    salary_score = Column(Integer, nullable=True)
    category_match_score = Column(Integer, nullable=True)
    experience_match_score = Column(Integer, nullable=True)

    # Weighting factors used
    weights = Column(JSONB, nullable=True, default={})

    # System timestamps
    calculated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.current_timestamp()
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="matching_scores")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", "job_id", "algorithm_version", name="unique_user_job_algorithm_score"
        ),
    )

    def __repr__(self):
        return f"<MatchingScore(user_id={self.user_id}, job_id={self.job_id}, score={self.composite_score})>"


class MatchHistory(Base):
    """Match history and interaction tracking"""

    __tablename__ = "match_history"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    job_id = Column(Integer, nullable=False, index=True)

    # Match details
    match_score = Column(Integer, nullable=False)
    algorithm_used = Column(String(50), nullable=False)
    match_rank = Column(Integer, nullable=True)  # Rank in user's match list

    # User interactions
    viewed = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    applied = Column(Boolean, default=False)
    favorited = Column(Boolean, default=False)
    hidden = Column(Boolean, default=False)

    # Interaction timestamps
    matched_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    favorited_at = Column(DateTime(timezone=True), nullable=True)

    # Feedback and engagement
    user_feedback = Column(String(20), nullable=True)  # interested, not_interested, maybe
    feedback_reason = Column(String(100), nullable=True)

    # System timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    user = relationship("User", back_populates="match_history")

    # Indexes for performance
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="unique_user_job_match"),)

    def __repr__(self):
        return f"<MatchHistory(user_id={self.user_id}, job_id={self.job_id}, score={self.match_score})>"
