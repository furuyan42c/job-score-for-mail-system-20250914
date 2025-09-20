#!/usr/bin/env python3
"""
User Job Match Model - Minimal GREEN Phase Implementation
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from app.core.database import Base


class UserJobMatch(Base):
    """Model for storing user-job matching results"""

    __tablename__ = "user_job_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    components = Column(JSON, nullable=True)  # Store score components
    match_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(String(1), default="Y")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserJobMatch(user_id={self.user_id}, job_id={self.job_id}, score={self.score})>"
