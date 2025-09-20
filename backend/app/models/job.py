#!/usr/bin/env python3
"""
T016: Job Model (REFACTORED)

SQLAlchemy ORM model for job postings with comprehensive scoring and relationships.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Job(Base):
    """Job model for jobs table"""

    __tablename__ = "jobs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Required fields from tests
    job_id = Column(String, unique=True, index=True)
    company_id = Column(String)
    company_name = Column(String)
    job_contents = Column(Text)
    job_contents_detail = Column(Text)
    salary = Column(String)
    min_salary = Column(Integer)
    max_salary = Column(Integer)
    area = Column(String)
    area_address = Column(String)
    pref_cd = Column(Integer)
    city_cd = Column(Integer)
    station = Column(String)
    hours = Column(String)
    employment_type = Column(String)
    employment_type_cd = Column(Integer)
    welfare = Column(Text)
    requirement = Column(Text)
    appeal_point = Column(Text)
    image_url = Column(String)
    occupation_cd1 = Column(Integer)
    occupation_cd2 = Column(Integer)
    occupation_cd3 = Column(Integer)
    min_age = Column(Integer)
    max_age = Column(Integer)
    start_at = Column(String)
    end_at = Column(String)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scores = relationship("Score", back_populates="job", cascade="all, delete-orphan")
    user_matches = relationship("UserJobMatch", back_populates="job")
    email_sections = relationship(
        "EmailSection", secondary="email_section_jobs", back_populates="jobs"
    )

    def validate_salary_range(self):
        """Validate salary range"""
        if self.min_salary and self.max_salary:
            if self.min_salary > self.max_salary:
                raise ValueError("min_salary cannot be greater than max_salary")

    def validate_age_range(self):
        """Validate age range"""
        if self.min_age and self.max_age:
            if self.min_age > self.max_age:
                raise ValueError("min_age cannot be greater than max_age")

    def calculate_base_score(self, market_avg_salary: float = 400000) -> float:
        """Calculate base score for the job based on various factors.

        Args:
            market_avg_salary: Average market salary for comparison

        Returns:
            Base score between 0 and 100
        """
        score = 50.0  # Default base score

        # Salary component (0-30 points)
        if self.min_salary and self.max_salary:
            avg_salary = (self.min_salary + self.max_salary) / 2
            salary_ratio = avg_salary / market_avg_salary if market_avg_salary > 0 else 1.0
            salary_score = min(30, salary_ratio * 15)  # Scale to max 30 points
            score += salary_score

        # Completeness bonus (0-20 points)
        completeness_score = self._calculate_completeness_score()
        score += completeness_score * 0.2

        return round(min(100.0, max(0.0, score)), 2)

    # Prefecture scores based on job market demand
    PREFECTURE_SCORES = {
        13: 100,  # Tokyo
        27: 90,  # Osaka
        14: 85,  # Kanagawa
        23: 85,  # Aichi
        40: 80,  # Fukuoka
        11: 75,  # Saitama
        12: 75,  # Chiba
        28: 70,  # Hyogo
        1: 65,  # Hokkaido
        26: 65,  # Kyoto
    }

    DEFAULT_PREFECTURE_SCORE = 50

    def calculate_location_score(self) -> float:
        """Calculate location score based on prefecture popularity.

        Returns:
            Location score between 0 and 100
        """
        return float(self.PREFECTURE_SCORES.get(self.pref_cd, self.DEFAULT_PREFECTURE_SCORE))

    def _calculate_completeness_score(self) -> float:
        """Calculate data completeness score.

        Returns:
            Completeness score between 0 and 100
        """
        fields = [
            self.company_name,
            self.job_contents,
            self.job_contents_detail,
            self.salary,
            self.min_salary,
            self.max_salary,
            self.area,
            self.area_address,
            self.hours,
            self.employment_type,
            self.welfare,
            self.requirement,
        ]
        filled_count = sum(1 for field in fields if field)
        return round((filled_count / len(fields)) * 100, 2)

    def to_dict(self, include_scores: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary representation.

        Args:
            include_scores: Whether to include calculated scores

        Returns:
            Dictionary representation of the job
        """
        data = {
            "id": self.id,
            "job_id": self.job_id,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "job_contents": self.job_contents,
            "job_contents_detail": self.job_contents_detail,
            "salary": self.salary,
            "min_salary": self.min_salary,
            "max_salary": self.max_salary,
            "area": self.area,
            "area_address": self.area_address,
            "pref_cd": self.pref_cd,
            "city_cd": self.city_cd,
            "employment_type": self.employment_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_scores:
            data.update(
                {
                    "base_score": self.calculate_base_score(),
                    "location_score": self.calculate_location_score(),
                    "completeness_score": self._calculate_completeness_score(),
                }
            )

        return data


# Association table for many-to-many relationship between EmailSection and Job
email_section_jobs = Table(
    "email_section_jobs",
    Base.metadata,
    Column("email_section_id", Integer, ForeignKey("email_sections.id"), primary_key=True),
    Column("job_id", Integer, ForeignKey("jobs.id"), primary_key=True),
    Index("idx_email_section_jobs", "email_section_id", "job_id"),
)


class UserJobMatch(Base):
    """User-Job match relationship for tracking match scores between users and jobs."""

    __tablename__ = "user_job_matches"
    __table_args__ = (
        Index("idx_user_job_match", "user_id", "job_id"),
        Index("idx_match_score", "match_score"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    match_score = Column(Float, nullable=False, default=0.0)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="user_matches")
    user = relationship("User", back_populates="job_matches")
