#!/usr/bin/env python3
"""
T016: Job Model (GREEN Phase)

Minimal implementation to pass tests
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

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
    email_sections = relationship("EmailSection", secondary="email_section_jobs", back_populates="jobs")
    
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
    
    def calculate_base_score(self):
        """Calculate base score for the job"""
        # Simple implementation for testing
        score = 50.0  # Base score
        
        if self.min_salary and self.max_salary:
            avg_salary = (self.min_salary + self.max_salary) / 2
            if avg_salary > 400000:
                score += 10
            if avg_salary > 600000:
                score += 10
        
        return min(100.0, max(0.0, score))
    
    def calculate_location_score(self):
        """Calculate location score"""
        # Tokyo gets high score
        if self.pref_cd == 13:
            return 85.0
        elif self.pref_cd in [27, 14, 23]:  # Osaka, Kanagawa, Aichi
            return 75.0
        else:
            return 50.0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'company_name': self.company_name,
            'job_contents': self.job_contents,
            'min_salary': self.min_salary,
            'max_salary': self.max_salary,
            'area': self.area,
            'pref_cd': self.pref_cd,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Association table for many-to-many relationship
from sqlalchemy import Table, ForeignKey

email_section_jobs = Table(
    'email_section_jobs',
    Base.metadata,
    Column('email_section_id', Integer, ForeignKey('email_sections.id')),
    Column('job_id', Integer, ForeignKey('jobs.id'))
)


class UserJobMatch(Base):
    """User-Job match relationship (placeholder)"""
    __tablename__ = "user_job_matches"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    job_id = Column(Integer)
    match_score = Column(Float)
    
    job = relationship("Job", back_populates="user_matches")
