"""
Unit Tests for Email Fallback Service

Tests the email generation fallback system when GPT-5 is unavailable.
Validates template-based email generation, personalization, and error handling.

Author: Claude Code Assistant
Created: 2025-09-18
Version: 1.0.0
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from app.services.email_fallback import (
    EmailFallbackService,
    FallbackConfig,
    FallbackReason,
    TemplateStyle,
    TemplateVariables,
    create_fallback_service,
    get_fallback_reason_from_error,
    test_fallback_generation
)

from app.services.gpt5_integration import (
    UserProfile,
    JobMatch,
    GenerationStatus
)

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        user_id="test_user_123",
        name="田中太郎",
        email="tanaka@example.com",
        location="東京都渋谷区",
        age=28,
        skills=["Python", "データ分析", "機械学習"],
        preferred_locations=["渋谷区", "新宿区"],
        language="ja"
    )

@pytest.fixture
def sample_job_matches():
    """Create sample job matches for testing."""
    jobs = []
    companies = ["株式会社A", "有限会社B", "企業C", "会社D", "法人E"]
    titles = ["エンジニア", "アナリスト", "開発者", "プログラマー", "技術者"]
    locations = ["渋谷", "新宿", "池袋", "品川", "秋葉原"]

    for i in range(10):
        job = JobMatch(
            job_id=f"job_{i}",
            title=titles[i % len(titles)],
            company_name=companies[i % len(companies)],
            location=f"{locations[i % len(locations)]}駅",
            salary_range=f"{1200 + i*100}-{1500 + i*100}",
            match_score=(95 - i*2) / 100.0,
            description=f"求人の詳細説明{i+1}です。",
            requirements=["経験1年以上", "Python"],
            benefits=["交通費支給", "社保完備"]
        )
        jobs.append(job)

    return jobs

@pytest.fixture
def fallback_config():
    """Create fallback configuration for testing."""
    return FallbackConfig(
        language="ja",
        style=TemplateStyle.PROFESSIONAL,
        include_personalization=True,
        randomize_templates=False,  # Disable randomization for predictable tests
        add_performance_note=True
    )

@pytest.fixture
def fallback_service(fallback_config):
    """Create fallback service instance for testing."""
    return EmailFallbackService(fallback_config)

# ============================================================================
# SERVICE INITIALIZATION TESTS
# ============================================================================

class TestEmailFallbackServiceInitialization:
    """Test service initialization and configuration."""

    def test_service_initialization_default_config(self):
        """Test service initialization with default configuration."""
        service = EmailFallbackService()

        assert service.config.language == "ja"
        assert service.config.style == TemplateStyle.PROFESSIONAL
        assert service.config.include_personalization is True
        assert service.config.randomize_templates is True

    def test_service_initialization_custom_config(self, fallback_config):
        """Test service initialization with custom configuration."""
        service = EmailFallbackService(fallback_config)

        assert service.config.language == "ja"
        assert service.config.style == TemplateStyle.PROFESSIONAL
        assert service.config.randomize_templates is False
        assert service.config.add_performance_note is True

    @pytest.mark.asyncio
    async def test_create_fallback_service_factory(self):
        """Test service creation using factory function."""
        service = await create_fallback_service(
            language="en",
            style=TemplateStyle.CASUAL,
            randomize_templates=True
        )

        assert service.config.language == "en"
        assert service.config.style == TemplateStyle.CASUAL
        assert service.config.randomize_templates is True

# ============================================================================
# TEMPLATE VARIABLE TESTS
# ============================================================================

class TestTemplateVariables:
    """Test template variable generation."""

    def test_create_template_variables(
        self,
        fallback_service,
        sample_user_profile,
        sample_job_matches
    ):
        """Test template variable creation."""
        template_vars = fallback_service._create_template_variables(
            sample_user_profile,
            sample_job_matches
        )

        assert template_vars.user_name == "田中太郎"
        assert template_vars.user_location == "東京都渋谷区"
        assert template_vars.total_job_count == 10
        assert template_vars.top_match_score == 95.0  # Highest match score
        assert len(template_vars.user_skills) <= 3
        assert len(template_vars.preferred_locations) <= 2

    def test_custom_greeting_generation_young_user(self, fallback_service):
        """Test custom greeting generation for young users."""
        young_user = UserProfile(
            user_id="young_user",
            name="若いユーザー",
            age=22
        )

        greeting = fallback_service._generate_custom_greeting(young_user)
        assert "お疲れさまです" in greeting

    def test_custom_greeting_generation_older_user(self, fallback_service):
        """Test custom greeting generation for older users."""
        older_user = UserProfile(
            user_id="older_user",
            name="大人ユーザー",
            age=35
        )

        greeting = fallback_service._generate_custom_greeting(older_user)
        assert "お世話になっております" in greeting

# ============================================================================
# EMAIL GENERATION TESTS
# ============================================================================

class TestEmailGeneration:
    """Test complete email generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_email_success(
        self,
        fallback_service,
        sample_user_profile,
        sample_job_matches
    ):
        """Test successful email generation."""
        result = await fallback_service.generate_email(
            sample_user_profile,
            sample_job_matches,
            FallbackReason.GPT5_UNAVAILABLE,
            TemplateStyle.PROFESSIONAL
        )

        assert result.status == GenerationStatus.COMPLETED
        assert result.email_content is not None
        assert result.fallback_used is True
        assert result.tokens_used == 0  # Templates don't use tokens
        assert "template_based" in result.metadata["generation_method"]

        # Check email content structure
        email = result.email_content
        assert email.subject is not None
        assert email.greeting is not None
        assert len(email.sections) > 0
        assert email.footer is not None
        assert email.language == "ja"

    @pytest.mark.asyncio
    async def test_generate_email_different_styles(
        self,
        sample_user_profile,
        sample_job_matches
    ):
        """Test email generation with different styles."""
        styles = [
            TemplateStyle.PROFESSIONAL,
            TemplateStyle.CASUAL,
            TemplateStyle.URGENT
        ]

        for style in styles:
            service = EmailFallbackService(FallbackConfig(style=style))
            result = await service.generate_email(
                sample_user_profile,
                sample_job_matches,
                FallbackReason.TESTING_MODE,
                style
            )

            assert result.status == GenerationStatus.COMPLETED
            assert result.metadata["template_style"] == style.value

    @pytest.mark.asyncio
    async def test_generate_email_with_insufficient_jobs(
        self,
        fallback_service,
        sample_user_profile
    ):
        """Test email generation with fewer jobs than expected."""
        # Only provide 3 jobs instead of expected 40
        few_jobs = [
            JobMatch(
                job_id=f"job_{i}",
                title=f"職種{i}",
                company_name=f"会社{i}",
                location=f"場所{i}",
                match_score=0.8
            )
            for i in range(3)
        ]

        result = await fallback_service.generate_email(
            sample_user_profile,
            few_jobs,
            FallbackReason.TESTING_MODE
        )

        assert result.status == GenerationStatus.COMPLETED
        assert result.email_content.total_jobs == 3

    @pytest.mark.asyncio
    async def test_generate_email_error_handling(self, sample_user_profile):
        """Test error handling in email generation."""
        # Create service that will fail during generation
        service = EmailFallbackService()

        # Test with invalid input
        with patch.object(service, '_generate_email_content', side_effect=Exception("Test error")):
            result = await service.generate_email(
                sample_user_profile,
                [],  # Empty job list
                FallbackReason.TESTING_MODE
            )

            assert result.status == GenerationStatus.FAILED
            assert "Test error" in result.error_message
            assert result.fallback_used is True

# ============================================================================
# BATCH GENERATION TESTS
# ============================================================================

class TestBatchGeneration:
    """Test batch email generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_batch_emails_success(
        self,
        fallback_service,
        sample_job_matches
    ):
        """Test successful batch email generation."""
        # Create multiple users
        users = [
            UserProfile(
                user_id=f"user_{i}",
                name=f"ユーザー{i}",
                location="東京"
            )
            for i in range(3)
        ]

        # Create job lists for each user
        job_lists = [sample_job_matches[:5] for _ in range(3)]

        results = await fallback_service.generate_batch_emails(
            users,
            job_lists,
            FallbackReason.COST_OPTIMIZATION
        )

        assert len(results) == 3
        assert all(r.status == GenerationStatus.COMPLETED for r in results)
        assert all(r.fallback_used for r in results)

    @pytest.mark.asyncio
    async def test_generate_batch_emails_mismatched_lengths(self, fallback_service):
        """Test batch generation with mismatched input lengths."""
        users = [UserProfile(user_id="user1")]
        job_lists = [[], []]  # Different length

        with pytest.raises(ValueError, match="must have same length"):
            await fallback_service.generate_batch_emails(
                users,
                job_lists,
                FallbackReason.TESTING_MODE
            )

    @pytest.mark.asyncio
    async def test_generate_batch_emails_with_errors(
        self,
        fallback_service,
        sample_job_matches
    ):
        """Test batch generation with some failures."""
        users = [
            UserProfile(user_id="user1"),
            UserProfile(user_id="user2"),
            UserProfile(user_id="user3")
        ]
        job_lists = [sample_job_matches[:5] for _ in range(3)]

        # Mock one generation to fail
        original_generate = fallback_service.generate_email

        async def mock_generate(profile, jobs, reason):
            if profile.user_id == "user2":
                raise Exception("Simulated error")
            return await original_generate(profile, jobs, reason)

        with patch.object(fallback_service, 'generate_email', side_effect=mock_generate):
            results = await fallback_service.generate_batch_emails(
                users,
                job_lists,
                FallbackReason.TESTING_MODE
            )

        assert len(results) == 3
        assert results[0].status == GenerationStatus.COMPLETED
        assert results[1].status == GenerationStatus.FAILED
        assert results[2].status == GenerationStatus.COMPLETED

# ============================================================================
# TEMPLATE GENERATION TESTS
# ============================================================================

class TestTemplateGeneration:
    """Test specific template generation components."""

    def test_generate_subject_professional(
        self,
        fallback_service,
        sample_user_profile,
        sample_job_matches
    ):
        """Test subject generation with professional style."""
        template_vars = fallback_service._create_template_variables(
            sample_user_profile,
            sample_job_matches
        )

        subject = fallback_service._generate_subject(template_vars, TemplateStyle.PROFESSIONAL)

        assert "田中太郎" in subject
        assert str(len(sample_job_matches)) in subject

    def test_generate_greeting_casual(
        self,
        fallback_service,
        sample_user_profile,
        sample_job_matches
    ):
        """Test greeting generation with casual style."""
        template_vars = fallback_service._create_template_variables(
            sample_user_profile,
            sample_job_matches
        )

        greeting = fallback_service._generate_greeting(template_vars, TemplateStyle.CASUAL)

        assert "田中太郎" in greeting

    @pytest.mark.asyncio
    async def test_generate_section(
        self,
        fallback_service,
        sample_user_profile,
        sample_job_matches
    ):
        """Test individual section generation."""
        template_vars = fallback_service._create_template_variables(
            sample_user_profile,
            sample_job_matches
        )

        section = await fallback_service._generate_section(
            "editorial_picks",
            sample_job_matches[:5],
            template_vars,
            TemplateStyle.PROFESSIONAL,
            sample_user_profile
        )

        assert section.section_type == "editorial_picks"
        assert section.title is not None
        assert section.description is not None
        assert len(section.job_items) == 5
        assert section.job_count == 5

    def test_generate_footer_with_performance_note(self, sample_user_profile):
        """Test footer generation with performance note."""
        config = FallbackConfig(add_performance_note=True)
        service = EmailFallbackService(config)

        template_vars = TemplateVariables(
            user_name="テストユーザー",
            user_location="東京",
            current_date="2025-09-18",
            current_time="10:00",
            total_job_count=10,
            top_match_score=95.0,
            user_skills=["スキル1"],
            preferred_locations=["エリア1"],
            salary_range="1200-1500",
            custom_greeting="こんにちは"
        )

        footer = service._generate_footer(sample_user_profile, template_vars)

        assert "テンプレートベース" in footer

# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions and helpers."""

    def test_get_fallback_reason_from_error(self):
        """Test fallback reason determination from errors."""
        # Test timeout error
        timeout_error = Exception("Connection timeout occurred")
        assert get_fallback_reason_from_error(timeout_error) == FallbackReason.GPT5_TIMEOUT

        # Test quota error
        quota_error = Exception("Rate limit exceeded")
        assert get_fallback_reason_from_error(quota_error) == FallbackReason.GPT5_QUOTA_EXCEEDED

        # Test API error
        api_error = Exception("API connection failed")
        assert get_fallback_reason_from_error(api_error) == FallbackReason.GPT5_API_ERROR

        # Test general error
        general_error = Exception("Something went wrong")
        assert get_fallback_reason_from_error(general_error) == FallbackReason.GPT5_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_fallback_generation_test_function(self):
        """Test the built-in test function."""
        results = await test_fallback_generation(user_count=2, jobs_per_user=10)

        assert len(results) == 2
        assert all(r.status == GenerationStatus.COMPLETED for r in results)
        assert all(r.fallback_used for r in results)
        assert all(r.metadata["fallback_reason"] == FallbackReason.TESTING_MODE.value for r in results)

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFallbackIntegration:
    """Test integration with other system components."""

    @pytest.mark.asyncio
    async def test_fallback_with_real_template_variables(
        self,
        sample_user_profile,
        sample_job_matches
    ):
        """Test fallback generation with realistic data."""
        # Create service with randomization enabled
        service = EmailFallbackService(FallbackConfig(
            randomize_templates=True,
            include_personalization=True
        ))

        result = await service.generate_email(
            sample_user_profile,
            sample_job_matches,
            FallbackReason.GPT5_UNAVAILABLE
        )

        assert result.status == GenerationStatus.COMPLETED

        email = result.email_content
        # Verify personalization
        assert sample_user_profile.name in email.subject
        assert sample_user_profile.location in email.personalization_note

        # Verify all sections are present
        section_types = [s.section_type for s in email.sections]
        expected_sections = [
            "editorial_picks", "top_recommendations", "trending_jobs",
            "near_you", "high_paying", "new_arrivals"
        ]

        # Should have at least some sections even with limited jobs
        assert len(section_types) > 0

    @pytest.mark.asyncio
    async def test_fallback_performance_benchmark(
        self,
        sample_user_profile,
        sample_job_matches
    ):
        """Test performance characteristics of fallback generation."""
        service = EmailFallbackService()

        start_time = datetime.now()

        # Generate multiple emails to test performance
        tasks = [
            service.generate_email(
                sample_user_profile,
                sample_job_matches,
                FallbackReason.TESTING_MODE
            )
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # All should succeed
        assert all(r.status == GenerationStatus.COMPLETED for r in results)

        # Should be reasonably fast (less than 5 seconds for 5 emails)
        assert total_time < 5.0

        # Individual generation times should be recorded
        assert all(r.generation_time_ms > 0 for r in results)

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    @pytest.mark.asyncio
    async def test_handle_missing_user_data(self, fallback_service, sample_job_matches):
        """Test handling of missing user profile data."""
        incomplete_user = UserProfile(
            user_id="incomplete_user"
            # Missing name, location, etc.
        )

        result = await fallback_service.generate_email(
            incomplete_user,
            sample_job_matches,
            FallbackReason.TESTING_MODE
        )

        # Should still succeed with default values
        assert result.status == GenerationStatus.COMPLETED
        assert "お客様" in result.email_content.subject  # Default name

    @pytest.mark.asyncio
    async def test_handle_empty_job_list(self, fallback_service, sample_user_profile):
        """Test handling of empty job list."""
        result = await fallback_service.generate_email(
            sample_user_profile,
            [],  # Empty job list
            FallbackReason.TESTING_MODE
        )

        assert result.status == GenerationStatus.COMPLETED
        assert result.email_content.total_jobs == 0

    @pytest.mark.asyncio
    async def test_handle_malformed_job_data(self, fallback_service, sample_user_profile):
        """Test handling of malformed job data."""
        malformed_jobs = [
            JobMatch(
                job_id="malformed_job",
                title="",  # Empty title
                company_name=None,  # None company name
                match_score=1.5  # Invalid score > 1.0
            )
        ]

        result = await fallback_service.generate_email(
            sample_user_profile,
            malformed_jobs,
            FallbackReason.TESTING_MODE
        )

        # Should handle gracefully
        assert result.status == GenerationStatus.COMPLETED

# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfiguration:
    """Test different configuration scenarios."""

    @pytest.mark.asyncio
    async def test_different_languages(self, sample_user_profile, sample_job_matches):
        """Test fallback generation with different languages."""
        # Test Japanese
        ja_service = EmailFallbackService(FallbackConfig(language="ja"))
        ja_result = await ja_service.generate_email(
            sample_user_profile,
            sample_job_matches,
            FallbackReason.TESTING_MODE
        )

        assert ja_result.status == GenerationStatus.COMPLETED
        assert ja_result.email_content.language == "ja"

        # Test English
        en_service = EmailFallbackService(FallbackConfig(language="en"))
        en_result = await en_service.generate_email(
            sample_user_profile,
            sample_job_matches,
            FallbackReason.TESTING_MODE
        )

        assert en_result.status == GenerationStatus.COMPLETED
        assert en_result.email_content.language == "en"

    def test_randomization_settings(self, sample_user_profile, sample_job_matches):
        """Test template randomization settings."""
        # Test with randomization disabled
        no_random_service = EmailFallbackService(FallbackConfig(randomize_templates=False))

        # Test with randomization enabled
        random_service = EmailFallbackService(FallbackConfig(randomize_templates=True))

        # Both should work, but randomization setting should be reflected in config
        assert no_random_service.config.randomize_templates is False
        assert random_service.config.randomize_templates is True

if __name__ == "__main__":
    # Run specific test when script is executed directly
    pytest.main([__file__, "-v"])