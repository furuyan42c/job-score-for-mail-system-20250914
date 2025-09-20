#!/usr/bin/env python3
"""
T022: SEO Scoring Tests (RED Phase)
Tests for keyword matching with semrush_keywords
"""

import pytest
from app.services.seo_scoring import SEOScoringService
from app.models.job import Job


class TestSEOScoring:
    """Test suite for SEO scoring service"""

    @pytest.fixture
    def scoring_service(self):
        """Create SEO scoring service instance"""
        return SEOScoringService()

    @pytest.fixture
    def sample_job(self):
        """Sample job with SEO-relevant content"""
        return Job(
            job_id="seo_test_001",
            title="Python Developer",
            description="Backend development with Django and FastAPI",
            company="Tech Company",
            application_name="Senior Python Engineer"
        )

    @pytest.fixture
    def semrush_keywords(self):
        """Sample SEMrush keyword data"""
        return [
            {"keyword": "python developer", "search_volume": 10000, "difficulty": 75},
            {"keyword": "django", "search_volume": 5000, "difficulty": 60},
            {"keyword": "fastapi", "search_volume": 3000, "difficulty": 50},
            {"keyword": "backend engineer", "search_volume": 8000, "difficulty": 70}
        ]

    @pytest.mark.asyncio
    async def test_keyword_preprocessing(self, scoring_service):
        """Test keyword preprocessing and normalization"""
        keywords = ["Python Developer", "python-developer", "PYTHON_DEVELOPER"]

        normalized = await scoring_service.normalize_keywords(keywords)

        assert len(normalized) == 3
        assert all(k.islower() for k in normalized)
        assert "python developer" in normalized

    @pytest.mark.asyncio
    async def test_field_weighting(self, scoring_service, sample_job, semrush_keywords):
        """Test different weights for different fields"""
        # application_name should have weight 1.5
        score_with_app_name = await scoring_service.calculate_seo_score(
            sample_job, semrush_keywords
        )

        # Remove application_name and test again
        sample_job.application_name = None
        score_without_app_name = await scoring_service.calculate_seo_score(
            sample_job, semrush_keywords
        )

        assert score_with_app_name > score_without_app_name

    @pytest.mark.asyncio
    async def test_search_volume_scoring(self, scoring_service, sample_job):
        """Test scoring based on search volume"""
        high_volume_keywords = [
            {"keyword": "python", "search_volume": 50000, "difficulty": 80}
        ]
        low_volume_keywords = [
            {"keyword": "python", "search_volume": 100, "difficulty": 30}
        ]

        high_score = await scoring_service.calculate_seo_score(
            sample_job, high_volume_keywords
        )
        low_score = await scoring_service.calculate_seo_score(
            sample_job, low_volume_keywords
        )

        assert high_score > low_score

    @pytest.mark.asyncio
    async def test_keyword_variations(self, scoring_service):
        """Test generation of keyword variations"""
        base_keyword = "python developer"

        variations = await scoring_service.generate_variations(base_keyword)

        assert "python developer" in variations
        assert "python-developer" in variations
        assert "python_developer" in variations
        assert "pythondeveloper" in variations