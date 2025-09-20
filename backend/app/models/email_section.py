#!/usr/bin/env python3
"""
T019: EmailSection Model (REFACTORED)

Email template and section management for dynamic email generation.
"""

import enum
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base

logger = logging.getLogger(__name__)


class SectionType(str, enum.Enum):
    """Email section type enumeration"""

    HEADER = "header"
    JOB_HIGHLIGHT = "job_highlight"
    JOB_LIST = "job_list"
    RECOMMENDATION = "recommendation"
    FOOTER = "footer"
    CTA = "cta"


class EmailTemplate(Base):
    """Email template model"""

    __tablename__ = "email_templates"
    __table_args__ = (Index("idx_template_name", "name"), {"extend_existing": True})

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    subject = Column(String)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sections = relationship("EmailSection", back_populates="template")

    async def get_active_sections(self, db_session: AsyncSession) -> List["EmailSection"]:
        """Get active sections for this template ordered by priority.

        Args:
            db_session: Database session

        Returns:
            List of active email sections
        """
        from sqlalchemy import select

        try:
            result = await db_session.execute(
                select(EmailSection)
                .where(EmailSection.template_id == self.id)
                .where(EmailSection.is_active == True)
                .order_by(EmailSection.priority)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get active sections: {e}")
            return []


class EmailSection(Base):
    """Email section model"""

    __tablename__ = "email_sections"
    __table_args__ = (
        Index("idx_section_template", "template_id"),
        Index("idx_section_user", "user_id"),
        Index("idx_section_priority", "priority"),
        Index("idx_section_active", "is_active"),
        {"extend_existing": True},
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    template_id = Column(Integer, ForeignKey("email_templates.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Section details
    section_type = Column(SQLEnum(SectionType))
    title = Column(String)
    content = Column(Text)
    priority = Column(Integer, default=1)
    job_ids = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("EmailTemplate", back_populates="sections")
    user = relationship("User")
    jobs = relationship("Job", secondary="email_section_jobs", back_populates="email_sections")

    def activate(self):
        """Activate the section"""
        self.is_active = True

    def deactivate(self):
        """Deactivate the section"""
        self.is_active = False

    # Template variable patterns
    TEMPLATE_VARS = {
        "user": ["user_name", "user_email", "user_id"],
        "job": ["job_title", "company_name", "salary", "location"],
        "meta": ["current_date", "section_title"],
    }

    def generate_content(
        self,
        user: Optional[Any] = None,
        jobs: Optional[List[Any]] = None,
        additional_vars: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate personalized content with template variable replacement.

        Args:
            user: User object for personalization
            jobs: List of job objects
            additional_vars: Additional template variables

        Returns:
            Personalized content string
        """
        if not self.content:
            return ""

        content = str(self.content)
        replacements = {}

        # User variables
        if user:
            replacements.update(
                {
                    "{user_name}": getattr(user, "name", ""),
                    "{user_email}": getattr(user, "email", ""),
                    "{user_id}": str(getattr(user, "user_id", "")),
                }
            )

        # Job variables (using first job if available)
        if jobs and len(jobs) > 0:
            job = jobs[0]
            replacements.update(
                {
                    "{job_title}": getattr(job, "job_contents", ""),
                    "{company_name}": getattr(job, "company_name", ""),
                    "{salary}": getattr(job, "salary", ""),
                    "{location}": getattr(job, "area", ""),
                }
            )

        # Additional variables
        if additional_vars:
            for key, value in additional_vars.items():
                replacements[f"{{{key}}}"] = str(value)

        # Replace all variables
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value or "")

        return content

    @validates("priority")
    def validate_priority(self, key: str, priority: Optional[int]) -> Optional[int]:
        """Validate priority is positive.

        Args:
            key: Field name
            priority: Priority value

        Returns:
            Validated priority

        Raises:
            ValueError: If priority is not positive
        """
        if priority is not None and priority < 1:
            raise ValueError(f"Priority must be positive, got {priority}")
        return priority

    def validate_content(self) -> bool:
        """Validate section has either title or content.

        Returns:
            True if valid

        Raises:
            ValueError: If neither title nor content exists
        """
        if not self.title and not self.content:
            raise ValueError("Section must have title or content")
        return True

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "user_id": self.user_id,
            "section_type": self.section_type.value if self.section_type else None,
            "title": self.title,
            "content": self.content,
            "priority": self.priority,
            "job_ids": self.job_ids,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
