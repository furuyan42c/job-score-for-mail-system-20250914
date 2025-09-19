#!/usr/bin/env python3
"""
T019: EmailSection Model Tests (RED Phase)

Tests for the EmailSection model including:
- Email template management
- Section types and priorities
- Content generation
- Job matching integration
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.email_section import EmailSection, SectionType, EmailTemplate
from app.models.job import Job
from app.models.user import User
from app.models.base import Base
from app.core.database import get_db


class TestEmailSectionModel:
    """Test suite for EmailSection model"""

    @pytest.fixture
    async def db_session(self):
        """Create test database session"""
        async for session in get_db():
            yield session
            await session.rollback()

    def test_email_section_model_exists(self):
        """Test that EmailSection model is defined"""
        assert EmailSection is not None
        assert hasattr(EmailSection, '__tablename__')
        assert EmailSection.__tablename__ == 'email_sections'

    def test_email_section_fields(self):
        """Test that EmailSection model has all required fields"""
        required_fields = [
            'id', 'template_id', 'section_type', 'title',
            'content', 'priority', 'job_ids', 'user_id',
            'is_active', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert hasattr(EmailSection, field), f"EmailSection model missing field: {field}"

    def test_section_types_enum(self):
        """Test SectionType enum values"""
        assert SectionType.HEADER == 'header'
        assert SectionType.JOB_HIGHLIGHT == 'job_highlight'
        assert SectionType.JOB_LIST == 'job_list'
        assert SectionType.RECOMMENDATION == 'recommendation'
        assert SectionType.FOOTER == 'footer'
        assert SectionType.CTA == 'cta'

    def test_email_template_model(self):
        """Test EmailTemplate model exists"""
        assert EmailTemplate is not None
        assert hasattr(EmailTemplate, '__tablename__')
        assert EmailTemplate.__tablename__ == 'email_templates'

    def test_email_section_relationships(self):
        """Test that EmailSection model has proper relationships"""
        assert hasattr(EmailSection, 'template')
        assert hasattr(EmailSection, 'user')
        assert hasattr(EmailSection, 'jobs')

    @pytest.mark.asyncio
    async def test_create_email_section(self, db_session: AsyncSession):
        """Test creating an email section"""
        # Create template first
        template = EmailTemplate(
            name="Weekly Digest",
            subject="Your Weekly Job Matches",
            description="Weekly email with job recommendations"
        )
        db_session.add(template)
        await db_session.commit()
        
        section = EmailSection(
            template_id=template.id,
            section_type=SectionType.HEADER,
            title="Welcome to Your Weekly Digest",
            content="<h1>Top Job Matches This Week</h1>",
            priority=1
        )
        
        db_session.add(section)
        await db_session.commit()
        await db_session.refresh(section)
        
        assert section.id is not None
        assert section.section_type == SectionType.HEADER
        assert section.priority == 1
        assert section.is_active is True

    @pytest.mark.asyncio
    async def test_job_highlight_section(self, db_session: AsyncSession):
        """Test creating a job highlight section"""
        # Create template and jobs
        template = EmailTemplate(name="Job Alert", subject="New Job Match")
        job1 = Job(job_id="HIGH001", company_name="Top Company")
        job2 = Job(job_id="HIGH002", company_name="Great Corp")
        
        db_session.add(template)
        db_session.add(job1)
        db_session.add(job2)
        await db_session.commit()
        
        section = EmailSection(
            template_id=template.id,
            section_type=SectionType.JOB_HIGHLIGHT,
            title="Featured Opportunities",
            content="Top matches based on your profile",
            job_ids=[job1.id, job2.id],
            priority=2
        )
        
        db_session.add(section)
        await db_session.commit()
        
        assert len(section.job_ids) == 2
        assert job1.id in section.job_ids

    @pytest.mark.asyncio
    async def test_user_specific_section(self, db_session: AsyncSession):
        """Test creating user-specific email sections"""
        template = EmailTemplate(name="Personal", subject="For You")
        user = User(user_id="EMAIL001", email="user@example.com", name="Email User")
        
        db_session.add(template)
        db_session.add(user)
        await db_session.commit()
        
        section = EmailSection(
            template_id=template.id,
            section_type=SectionType.RECOMMENDATION,
            title=f"Recommendations for {user.name}",
            content="Based on your recent searches",
            user_id=user.id,
            priority=3
        )
        
        db_session.add(section)
        await db_session.commit()
        
        assert section.user_id == user.id
        assert user.name in section.title

    @pytest.mark.asyncio
    async def test_section_priority_ordering(self, db_session: AsyncSession):
        """Test section ordering by priority"""
        template = EmailTemplate(name="Ordered", subject="Test")
        db_session.add(template)
        await db_session.commit()
        
        # Create sections with different priorities
        sections = [
            EmailSection(template_id=template.id, section_type=SectionType.FOOTER, priority=10),
            EmailSection(template_id=template.id, section_type=SectionType.HEADER, priority=1),
            EmailSection(template_id=template.id, section_type=SectionType.JOB_LIST, priority=5),
        ]
        
        for section in sections:
            db_session.add(section)
        await db_session.commit()
        
        # Query sections ordered by priority
        result = await db_session.execute(
            select(EmailSection)
            .where(EmailSection.template_id == template.id)
            .order_by(EmailSection.priority)
        )
        ordered_sections = result.scalars().all()
        
        assert ordered_sections[0].section_type == SectionType.HEADER
        assert ordered_sections[1].section_type == SectionType.JOB_LIST
        assert ordered_sections[2].section_type == SectionType.FOOTER

    @pytest.mark.asyncio
    async def test_section_activation(self, db_session: AsyncSession):
        """Test section activation/deactivation"""
        template = EmailTemplate(name="Active Test", subject="Test")
        db_session.add(template)
        await db_session.commit()
        
        section = EmailSection(
            template_id=template.id,
            section_type=SectionType.CTA,
            title="Apply Now",
            content="<button>Apply</button>",
            is_active=True
        )
        
        db_session.add(section)
        await db_session.commit()
        
        # Deactivate section
        section.deactivate()
        await db_session.commit()
        
        assert section.is_active is False
        
        # Reactivate section
        section.activate()
        await db_session.commit()
        
        assert section.is_active is True

    @pytest.mark.asyncio
    async def test_template_sections_relationship(self, db_session: AsyncSession):
        """Test relationship between template and sections"""
        template = EmailTemplate(name="Full Template", subject="Complete Email")
        db_session.add(template)
        await db_session.commit()
        
        # Create multiple sections for template
        section_types = [
            SectionType.HEADER,
            SectionType.JOB_LIST,
            SectionType.CTA,
            SectionType.FOOTER
        ]
        
        for i, section_type in enumerate(section_types, 1):
            section = EmailSection(
                template_id=template.id,
                section_type=section_type,
                title=f"{section_type.value} Section",
                priority=i
            )
            db_session.add(section)
        
        await db_session.commit()
        await db_session.refresh(template)
        
        # Get all sections for template
        sections = await template.get_active_sections(db_session)
        
        assert len(sections) == 4
        assert all(s.template_id == template.id for s in sections)

    @pytest.mark.asyncio
    async def test_section_content_generation(self, db_session: AsyncSession):
        """Test dynamic content generation for sections"""
        template = EmailTemplate(name="Dynamic", subject="Test")
        user = User(user_id="DYN001", email="dyn@example.com", name="Dynamic User")
        job = Job(job_id="DYN001", company_name="Dynamic Corp", job_contents="Developer")
        
        db_session.add(template)
        db_session.add(user)
        db_session.add(job)
        await db_session.commit()
        
        section = EmailSection(
            template_id=template.id,
            section_type=SectionType.JOB_HIGHLIGHT,
            title="Perfect Match",
            content="{job_title} at {company_name}",
            job_ids=[job.id],
            user_id=user.id
        )
        
        # Generate personalized content
        personalized = section.generate_content(
            user=user,
            jobs=[job]
        )
        
        assert "Developer" in personalized
        assert "Dynamic Corp" in personalized

    @pytest.mark.asyncio
    async def test_section_validation(self, db_session: AsyncSession):
        """Test section validation rules"""
        template = EmailTemplate(name="Validate", subject="Test")
        db_session.add(template)
        await db_session.commit()
        
        # Test invalid priority
        with pytest.raises(ValueError, match="Priority must be positive"):
            section = EmailSection(
                template_id=template.id,
                section_type=SectionType.HEADER,
                priority=-1  # Invalid
            )
            section.validate_priority()

        # Test missing content
        with pytest.raises(ValueError, match="Section must have title or content"):
            section = EmailSection(
                template_id=template.id,
                section_type=SectionType.JOB_LIST,
                title="",
                content="",
                priority=1
            )
            section.validate_content()

    def test_section_serialization(self):
        """Test section serialization to dict"""
        section = EmailSection(
            template_id=1,
            section_type=SectionType.JOB_HIGHLIGHT,
            title="Top Jobs",
            content="<div>Jobs here</div>",
            priority=2,
            job_ids=[1, 2, 3],
            is_active=True
        )
        
        section_dict = section.to_dict()
        
        assert section_dict['template_id'] == 1
        assert section_dict['section_type'] == 'job_highlight'
        assert section_dict['priority'] == 2
        assert len(section_dict['job_ids']) == 3
        assert section_dict['is_active'] is True
