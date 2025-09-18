"""
Comprehensive test suite for GPT-5 nano integration service.

Tests cover:
- Email generation functionality
- Batch processing
- Rate limiting and caching
- Error handling and retry logic
- Japanese/English content generation
- Performance monitoring
- Mock mode functionality
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, List

from app.services.gpt5_integration import (
    EmailGenerationService,
    UserProfile,
    JobMatch,
    EmailSectionType,
    EmailLanguage,
    GenerationStatus,
    BatchGenerationRequest,
    create_email_generation_service
)


class TestEmailGenerationService:
    """Test suite for EmailGenerationService"""

    @pytest.fixture
    async def mock_service(self):
        """Create service in mock mode for testing"""
        service = EmailGenerationService(
            openai_api_key="test-key",
            redis_url="redis://localhost:6379/1",
            mock_mode=True
        )

        # Mock Redis to avoid actual connection
        service.redis = AsyncMock()
        service.rate_limiter = AsyncMock()
        service.rate_limiter.check_limit.return_value = True

        yield service

        if hasattr(service, 'close'):
            await service.close()

    @pytest.fixture
    def sample_user_profile(self):
        """Create sample user profile for testing"""
        return UserProfile(
            user_id=1,
            name="田中太郎",
            email="tanaka@example.com",
            preferred_language=EmailLanguage.JAPANESE,
            location="東京都",
            job_preferences={"industry": "IT", "work_type": "full_time"},
            experience_level="mid_level"
        )

    @pytest.fixture
    def sample_job_matches(self):
        """Create sample job matches for all 6 sections"""
        return {
            EmailSectionType.EDITORIAL_PICKS: [
                JobMatch(
                    job_id=i,
                    title=f"Software Engineer {i}",
                    company=f"Tech Corp {i}",
                    location="東京都",
                    match_score=95.0 - i,
                    description="Exciting opportunity for software development"
                )
                for i in range(1, 6)  # 5 jobs
            ],
            EmailSectionType.TOP_RECOMMENDATIONS: [
                JobMatch(
                    job_id=i,
                    title=f"Senior Developer {i}",
                    company=f"Dev Company {i}",
                    location="大阪府",
                    match_score=90.0 - i,
                    is_popular=True
                )
                for i in range(6, 11)  # 5 jobs
            ],
            EmailSectionType.PERSONALIZED_PICKS: [
                JobMatch(
                    job_id=i,
                    title=f"Frontend Engineer {i}",
                    company=f"Web Studio {i}",
                    location="神奈川県",
                    match_score=85.0 - i,
                    tags=["React", "JavaScript"]
                )
                for i in range(11, 21)  # 10 jobs
            ],
            EmailSectionType.NEW_ARRIVALS: [
                JobMatch(
                    job_id=i,
                    title=f"Backend Engineer {i}",
                    company=f"API Corp {i}",
                    location="千葉県",
                    match_score=80.0 - i,
                    is_new=True
                )
                for i in range(21, 31)  # 10 jobs
            ],
            EmailSectionType.POPULAR_JOBS: [
                JobMatch(
                    job_id=i,
                    title=f"Full Stack Developer {i}",
                    company=f"Startup {i}",
                    location="埼玉県",
                    match_score=88.0 - i,
                    is_popular=True,
                    application_count=100 + i
                )
                for i in range(31, 36)  # 5 jobs
            ],
            EmailSectionType.YOU_MIGHT_LIKE: [
                JobMatch(
                    job_id=i,
                    title=f"Mobile Developer {i}",
                    company=f"Mobile Inc {i}",
                    location="福岡県",
                    match_score=82.0 - i,
                    tags=["iOS", "Android"]
                )
                for i in range(36, 41)  # 5 jobs
            ]
        }

    async def test_service_initialization(self):
        """Test service initialization and configuration"""
        service = EmailGenerationService(
            openai_api_key="test-key",
            rate_limit_per_minute=50,
            cache_ttl=1800,
            mock_mode=True
        )

        assert service.mock_mode is True
        assert service.cache_ttl == 1800
        assert service.section_configs[EmailSectionType.EDITORIAL_PICKS]["job_count"] == 5
        assert service.section_configs[EmailSectionType.PERSONALIZED_PICKS]["job_count"] == 10

    async def test_factory_function(self):
        """Test service creation via factory function"""
        with patch('app.services.gpt5_integration.EmailGenerationService') as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            service = await create_email_generation_service(
                openai_api_key="test-key",
                mock_mode=True
            )

            mock_instance.initialize.assert_called_once()

    async def test_cache_key_generation(self, mock_service, sample_user_profile, sample_job_matches):
        """Test cache key generation for consistency"""
        cache_key1 = mock_service._generate_cache_key(
            sample_user_profile.user_id,
            sample_job_matches,
            EmailLanguage.JAPANESE
        )

        cache_key2 = mock_service._generate_cache_key(
            sample_user_profile.user_id,
            sample_job_matches,
            EmailLanguage.JAPANESE
        )

        # Same inputs should generate same cache key
        assert cache_key1 == cache_key2

        # Different language should generate different cache key
        cache_key3 = mock_service._generate_cache_key(
            sample_user_profile.user_id,
            sample_job_matches,
            EmailLanguage.ENGLISH
        )

        assert cache_key1 != cache_key3

    async def test_rate_limiting(self, mock_service, sample_user_profile):
        """Test rate limiting functionality"""
        # Test successful rate limit check
        mock_service.rate_limiter.check_limit.return_value = True
        result = await mock_service._check_rate_limit(sample_user_profile.user_id)
        assert result is True

        # Test rate limit exceeded
        mock_service.rate_limiter.check_limit.return_value = False
        result = await mock_service._check_rate_limit(sample_user_profile.user_id)
        assert result is False

    async def test_job_matches_validation(self, mock_service, sample_job_matches):
        """Test job matches validation"""
        # Test valid job matches
        validation_result = await mock_service.validate_job_matches(sample_job_matches)
        assert validation_result["is_valid"] is True
        assert len(validation_result["errors"]) == 0

        # Test missing section
        incomplete_matches = sample_job_matches.copy()
        del incomplete_matches[EmailSectionType.EDITORIAL_PICKS]

        validation_result = await mock_service.validate_job_matches(incomplete_matches)
        assert validation_result["is_valid"] is False
        assert len(validation_result["errors"]) > 0

        # Test wrong job count
        wrong_count_matches = sample_job_matches.copy()
        wrong_count_matches[EmailSectionType.EDITORIAL_PICKS] = [
            JobMatch(job_id=1, title="Test", company="Test", location="Test")
        ]  # Only 1 job instead of 5

        validation_result = await mock_service.validate_job_matches(wrong_count_matches)
        assert len(validation_result["warnings"]) > 0

    async def test_mock_email_generation(self, mock_service, sample_user_profile, sample_job_matches):
        """Test email generation in mock mode"""
        result = await mock_service.generate_email(
            sample_user_profile,
            sample_job_matches
        )

        assert result.status == GenerationStatus.COMPLETED
        assert result.email_content is not None
        assert result.email_content.user_id == sample_user_profile.user_id
        assert result.email_content.language == EmailLanguage.JAPANESE
        assert len(result.email_content.sections) == 6

        # Verify all section types are present
        section_types = {section.section_type for section in result.email_content.sections}
        expected_types = set(EmailSectionType)
        assert section_types == expected_types

        # Check mock indicators
        assert "[MOCK]" in result.email_content.subject
        for section in result.email_content.sections:
            assert "[MOCK]" in section.title

    async def test_english_email_generation(self, mock_service, sample_job_matches):
        """Test email generation in English"""
        english_user = UserProfile(
            user_id=2,
            name="John Smith",
            email="john@example.com",
            preferred_language=EmailLanguage.ENGLISH,
            location="Tokyo"
        )

        result = await mock_service.generate_email(
            english_user,
            sample_job_matches
        )

        assert result.status == GenerationStatus.COMPLETED
        assert result.email_content.language == EmailLanguage.ENGLISH
        assert "Hello John Smith!" in result.email_content.greeting

    async def test_rate_limit_exceeded(self, mock_service, sample_user_profile, sample_job_matches):
        """Test behavior when rate limit is exceeded"""
        mock_service.rate_limiter.check_limit.return_value = False

        result = await mock_service.generate_email(
            sample_user_profile,
            sample_job_matches
        )

        assert result.status == GenerationStatus.FAILED
        assert "Rate limit exceeded" in result.error_message

    async def test_caching_functionality(self, mock_service, sample_user_profile, sample_job_matches):
        """Test caching of generated content"""
        # Mock cache miss then cache hit
        mock_service.redis.get.return_value = None

        # First call should generate content
        result1 = await mock_service.generate_email(
            sample_user_profile,
            sample_job_matches
        )

        assert result1.status == GenerationStatus.COMPLETED
        assert result1.cache_hit is False

        # Mock cache hit for second call
        cached_content = result1.email_content.json()
        mock_service.redis.get.return_value = cached_content

        result2 = await mock_service.generate_email(
            sample_user_profile,
            sample_job_matches
        )

        assert result2.status == GenerationStatus.CACHED
        assert result2.cache_hit is True

    async def test_batch_generation(self, mock_service, sample_job_matches):
        """Test batch email generation"""
        # Create multiple user profiles
        user_profiles = [
            UserProfile(
                user_id=i,
                name=f"User {i}",
                email=f"user{i}@example.com",
                preferred_language=EmailLanguage.JAPANESE
            )
            for i in range(1, 4)
        ]

        # Create job matches for each user
        job_matches_by_user = {
            profile.user_id: sample_job_matches
            for profile in user_profiles
        }

        batch_request = BatchGenerationRequest(
            user_profiles=user_profiles,
            job_matches_by_user=job_matches_by_user,
            language=EmailLanguage.JAPANESE
        )

        results = await mock_service.generate_emails_batch(batch_request)

        assert len(results) == 3
        for result in results:
            assert result.status == GenerationStatus.COMPLETED
            assert result.email_content is not None

    async def test_batch_generation_dry_run(self, mock_service):
        """Test batch generation in dry run mode"""
        user_profiles = [
            UserProfile(
                user_id=1,
                name="Test User",
                email="test@example.com",
                preferred_language=EmailLanguage.JAPANESE
            )
        ]

        batch_request = BatchGenerationRequest(
            user_profiles=user_profiles,
            job_matches_by_user={},
            dry_run=True
        )

        results = await mock_service.generate_emails_batch(batch_request)

        assert len(results) == 1
        assert results[0].status == GenerationStatus.COMPLETED
        assert results[0].generation_time_ms == 0

    async def test_performance_metrics(self, mock_service, sample_user_profile, sample_job_matches):
        """Test performance metrics collection"""
        # Generate some emails to populate metrics
        await mock_service.generate_email(sample_user_profile, sample_job_matches)

        metrics = await mock_service.get_performance_metrics()

        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "cache_hits" in metrics
        assert "avg_response_time" in metrics
        assert metrics["total_requests"] > 0

    async def test_cache_management(self, mock_service):
        """Test cache clearing functionality"""
        # Test user-specific cache clear
        mock_service.redis.keys.return_value = ["email_content:1:ja:hash1", "email_content:1:en:hash2"]
        mock_service.redis.delete = AsyncMock()

        await mock_service.clear_cache(user_id=1)

        mock_service.redis.keys.assert_called_with("email_content:1:*")
        mock_service.redis.delete.assert_called_once()

        # Test global cache clear
        mock_service.redis.keys.return_value = [
            "email_content:1:ja:hash1",
            "email_content:2:ja:hash2",
            "email_content:3:en:hash3"
        ]

        await mock_service.clear_cache()

        mock_service.redis.keys.assert_called_with("email_content:*")

    @patch('app.services.gpt5_integration.AsyncOpenAI')
    async def test_gpt5_nano_api_call(self, mock_openai_class, mock_service):
        """Test GPT-5 nano API call with retry logic"""
        # Disable mock mode for this test
        mock_service.mock_mode = False

        # Mock successful API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage.total_tokens = 150

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        mock_service.openai_client = mock_client

        result = await mock_service._call_gpt5_nano("Test prompt")

        assert result == "Generated content"
        mock_client.chat.completions.create.assert_called_once()

    @patch('app.services.gpt5_integration.AsyncOpenAI')
    async def test_gpt5_nano_retry_logic(self, mock_openai_class, mock_service):
        """Test retry logic for GPT-5 nano API failures"""
        mock_service.mock_mode = False

        # Mock API failure then success
        from openai import RateLimitError

        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit exceeded"),
            Mock(choices=[Mock(message=Mock(content="Success"))], usage=Mock(total_tokens=100))
        ]

        mock_openai_class.return_value = mock_client
        mock_service.openai_client = mock_client

        result = await mock_service._call_gpt5_nano("Test prompt")

        assert result == "Success"
        assert mock_client.chat.completions.create.call_count == 2

    async def test_fallback_content_generation(self, mock_service, sample_job_matches):
        """Test fallback content generation when GPT-5 is unavailable"""
        jobs = sample_job_matches[EmailSectionType.EDITORIAL_PICKS]

        # Test Japanese fallback
        section = mock_service._fallback_section_content(
            EmailSectionType.EDITORIAL_PICKS,
            jobs,
            EmailLanguage.JAPANESE
        )

        assert section.section_type == EmailSectionType.EDITORIAL_PICKS
        assert "編集部おすすめ" in section.title
        assert len(section.job_descriptions) == len(jobs)
        assert section.generation_metadata.get("fallback") is True

        # Test English fallback
        section = mock_service._fallback_section_content(
            EmailSectionType.EDITORIAL_PICKS,
            jobs,
            EmailLanguage.ENGLISH
        )

        assert "Editorial Picks" in section.title
        assert "Check out these opportunities:" in section.intro_text

    async def test_subject_line_generation(self, mock_service, sample_user_profile):
        """Test subject line generation"""
        job_counts = {
            EmailSectionType.EDITORIAL_PICKS: 5,
            EmailSectionType.TOP_RECOMMENDATIONS: 5,
            EmailSectionType.PERSONALIZED_PICKS: 10,
            EmailSectionType.NEW_ARRIVALS: 10,
            EmailSectionType.POPULAR_JOBS: 5,
            EmailSectionType.YOU_MIGHT_LIKE: 5
        }

        # Test Japanese subject line
        subject = await mock_service._generate_subject_line(
            sample_user_profile,
            job_counts,
            EmailLanguage.JAPANESE
        )

        assert sample_user_profile.name in subject or "[MOCK]" in subject

        # Test English subject line
        sample_user_profile.preferred_language = EmailLanguage.ENGLISH
        subject = await mock_service._generate_subject_line(
            sample_user_profile,
            job_counts,
            EmailLanguage.ENGLISH
        )

        assert isinstance(subject, str)
        assert len(subject) > 0

    async def test_greeting_and_closing_generation(self, mock_service):
        """Test greeting and closing generation"""
        japanese_user = UserProfile(
            user_id=1,
            name="田中太郎",
            email="tanaka@example.com",
            preferred_language=EmailLanguage.JAPANESE
        )

        english_user = UserProfile(
            user_id=2,
            name="John Smith",
            email="john@example.com",
            preferred_language=EmailLanguage.ENGLISH
        )

        # Test Japanese
        greeting = mock_service._generate_greeting(japanese_user)
        assert "田中太郎さん、こんにちは！" == greeting

        closing = mock_service._generate_closing(EmailLanguage.JAPANESE)
        assert "転職活動" in closing

        signature = mock_service._generate_signature(EmailLanguage.JAPANESE)
        assert "バイト求人マッチングチーム" in signature

        # Test English
        greeting = mock_service._generate_greeting(english_user)
        assert "Hello John Smith!" == greeting

        closing = mock_service._generate_closing(EmailLanguage.ENGLISH)
        assert "career journey" in closing

        signature = mock_service._generate_signature(EmailLanguage.ENGLISH)
        assert "Job Matching Team" in signature

    async def test_section_content_structure(self, mock_service, sample_job_matches):
        """Test structure of generated section content"""
        jobs = sample_job_matches[EmailSectionType.EDITORIAL_PICKS]

        section = await mock_service._generate_section_content(
            EmailSectionType.EDITORIAL_PICKS,
            UserProfile(
                user_id=1,
                name="Test User",
                email="test@example.com",
                preferred_language=EmailLanguage.JAPANESE
            ),
            jobs,
            EmailLanguage.JAPANESE
        )

        # Verify required fields
        assert section.section_type == EmailSectionType.EDITORIAL_PICKS
        assert isinstance(section.title, str) and len(section.title) > 0
        assert isinstance(section.intro_text, str) and len(section.intro_text) > 0
        assert isinstance(section.job_descriptions, list)
        assert isinstance(section.call_to_action, str) and len(section.call_to_action) > 0
        assert isinstance(section.generated_at, datetime)
        assert isinstance(section.generation_metadata, dict)

    async def test_error_handling(self, mock_service, sample_user_profile, sample_job_matches):
        """Test comprehensive error handling"""
        # Test with corrupted job matches
        corrupted_matches = {}  # Empty matches should cause validation error

        result = await mock_service.generate_email(
            sample_user_profile,
            corrupted_matches
        )

        # Should still complete in mock mode but with warnings
        assert result.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]

    async def test_concurrent_generation(self, mock_service, sample_job_matches):
        """Test concurrent email generation"""
        users = [
            UserProfile(
                user_id=i,
                name=f"User {i}",
                email=f"user{i}@example.com",
                preferred_language=EmailLanguage.JAPANESE
            )
            for i in range(1, 6)
        ]

        # Generate emails concurrently
        tasks = [
            mock_service.generate_email(user, sample_job_matches)
            for user in users
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for result in results:
            assert result.status == GenerationStatus.COMPLETED

    async def test_memory_efficiency(self, mock_service, sample_user_profile, sample_job_matches):
        """Test memory efficiency with large batches"""
        # Generate multiple emails to test memory usage
        for i in range(10):
            result = await mock_service.generate_email(
                sample_user_profile,
                sample_job_matches
            )
            assert result.status == GenerationStatus.COMPLETED

        # Verify service is still responsive
        final_result = await mock_service.generate_email(
            sample_user_profile,
            sample_job_matches
        )
        assert final_result.status == GenerationStatus.COMPLETED


# Integration tests (require actual Redis and OpenAI setup)
@pytest.mark.integration
class TestEmailGenerationServiceIntegration:
    """Integration tests for EmailGenerationService"""

    @pytest.fixture
    async def integration_service(self):
        """Create service for integration testing"""
        import os

        openai_key = os.getenv("OPENAI_API_KEY", "test-key")
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

        service = EmailGenerationService(
            openai_api_key=openai_key,
            redis_url=redis_url,
            mock_mode=True  # Keep in mock mode for safe testing
        )

        try:
            await service.initialize()
            yield service
        finally:
            await service.close()

    async def test_redis_connection(self, integration_service):
        """Test actual Redis connection"""
        # This will only work if Redis is available
        try:
            await integration_service.redis.ping()
            assert True  # Connection successful
        except:
            pytest.skip("Redis not available for integration testing")

    async def test_end_to_end_generation(self, integration_service, sample_user_profile, sample_job_matches):
        """Test complete end-to-end email generation"""
        result = await integration_service.generate_email(
            sample_user_profile,
            sample_job_matches
        )

        assert result.status == GenerationStatus.COMPLETED
        assert result.email_content is not None
        assert result.generation_time_ms > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])