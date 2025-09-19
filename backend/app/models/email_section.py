#!/usr/bin/env python3
"""
T019: EmailSection Model (GREEN Phase)

Minimal implementation to pass tests
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class SectionType(str, enum.Enum):
    """Email section type enumeration"""
    HEADER = 'header'
    JOB_HIGHLIGHT = 'job_highlight'
    JOB_LIST = 'job_list'
    RECOMMENDATION = 'recommendation'
    FOOTER = 'footer'
    CTA = 'cta'


class EmailTemplate(Base):
    """Email template model"""
    
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    subject = Column(String)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sections = relationship("EmailSection", back_populates="template")
    
    async def get_active_sections(self, db_session):
        """Get active sections for this template"""
        from sqlalchemy import select
        
        result = await db_session.execute(
            select(EmailSection)
            .where(EmailSection.template_id == self.id)
            .where(EmailSection.is_active == True)
            .order_by(EmailSection.priority)
        )
        
        return result.scalars().all()


class EmailSection(Base):
    """Email section model"""
    
    __tablename__ = "email_sections"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    template_id = Column(Integer, ForeignKey('email_templates.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
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
    
    def generate_content(self, user=None, jobs=None):
        """Generate personalized content"""
        content = self.content or ""
        
        # Simple template replacement
        if jobs and len(jobs) > 0:
            job = jobs[0]
            content = content.replace("{job_title}", job.job_contents or "")
            content = content.replace("{company_name}", job.company_name or "")
        
        if user:
            content = content.replace("{user_name}", user.name or "")
            content = content.replace("{user_email}", user.email or "")
        
        return content
    
    def validate_priority(self):
        """Validate priority is positive"""
        if self.priority is not None and self.priority < 1:
            raise ValueError("Priority must be positive")
    
    def validate_content(self):
        """Validate section has content"""
        if not self.title and not self.content:
            raise ValueError("Section must have title or content")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'user_id': self.user_id,
            'section_type': self.section_type.value if self.section_type else None,
            'title': self.title,
            'content': self.content,
            'priority': self.priority,
            'job_ids': self.job_ids,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
