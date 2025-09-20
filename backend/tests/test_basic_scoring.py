#!/usr/bin/env python3
"""
T021: Basic Scoring Tests (RED Phase)
Tests for fee, hourly_wage, and company_popularity scoring
"""

import pytest
from datetime import datetime, timedelta
from app.services.basic_scoring import BasicScoringService
from app.models.job import Job
from app.models.user import User


class TestBasicScoring:
    """Test suite for basic scoring service"""

    @pytest.fixture
    def scoring_service(self):
        """Create scoring service instance"""
        return BasicScoringService()

    @pytest.fixture
    def sample_job(self):
        """Create sample job for testing"""
        return Job(
            job_id="test_job_001",
            title="Software Engineer",
            company="Test Company",
            fee=600,
            hourly_wage=2500,
            prefecture_cd=13,  # Tokyo
            created_at=datetime.now()
        )

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing"""
        return User(
            user_id="test_user_001",
            email="test@example.com",
            name="Test User",
            preferences={"preferred_prefecture": 13}
        )

    @pytest.mark.asyncio
    async def test_fee_scoring_above_threshold(self, scoring_service, sample_job):
        """Test fee scoring when fee > 500"""
        score = await scoring_service.calculate_fee_score(sample_job)

        assert score > 0
        assert score <= 100
        # Fee of 600 should give high score
        assert score >= 80

    @pytest.mark.asyncio
    async def test_fee_scoring_below_threshold(self, scoring_service):
        """Test fee scoring when fee <= 500"""
        job = Job(
            job_id="test_job_002",
            fee=400,
            hourly_wage=2000
        )

        score = await scoring_service.calculate_fee_score(job)

        assert score == 0  # Should be 0 when fee <= 500

    @pytest.mark.asyncio
    async def test_hourly_wage_z_score_normalization(self, scoring_service, sample_job):
        """Test hourly wage scoring with Z-score normalization"""
        # Mock area statistics
        area_stats = {
            "mean": 2000,
            "std_dev": 500,
            "prefecture_cd": 13
        }

        score = await scoring_service.calculate_hourly_wage_score(
            sample_job,
            area_stats
        )

        assert score >= 0
        assert score <= 100
        # 2500 wage with mean 2000 should give good score
        assert score >= 60

    @pytest.mark.asyncio
    async def test_company_popularity_360_days(self, scoring_service):
        """Test company popularity calculation over 360 days"""
        company_data = {
            "company_name": "Popular Company",
            "application_count_360d": 1000,
            "view_count_360d": 5000
        }

        score = await scoring_service.calculate_company_popularity_score(
            company_data
        )

        assert score >= 0
        assert score <= 100
        # High application and view counts should give high score
        assert score >= 70

    @pytest.mark.asyncio
    async def test_combined_basic_score(self, scoring_service, sample_job):
        """Test combined basic scoring calculation"""
        area_stats = {
            "mean": 2000,
            "std_dev": 500,
            "prefecture_cd": 13
        }

        company_data = {
            "company_name": sample_job.company,
            "application_count_360d": 500,
            "view_count_360d": 2000
        }

        result = await scoring_service.calculate_basic_score(
            sample_job,
            area_stats,
            company_data
        )

        assert "fee_score" in result
        assert "hourly_wage_score" in result
        assert "company_popularity_score" in result
        assert "total_basic_score" in result

        # Total should be weighted average
        assert result["total_basic_score"] >= 0
        assert result["total_basic_score"] <= 100

    @pytest.mark.asyncio
    async def test_scoring_with_missing_data(self, scoring_service):
        """Test scoring with missing or invalid data"""
        job = Job(
            job_id="test_job_003",
            fee=None,  # Missing fee
            hourly_wage=None  # Missing wage
        )

        result = await scoring_service.calculate_basic_score(
            job,
            area_stats=None,
            company_data=None
        )

        # Should handle missing data gracefully
        assert result["fee_score"] == 0
        assert result["hourly_wage_score"] == 0
        assert result["company_popularity_score"] == 0

    @pytest.mark.asyncio
    async def test_z_score_edge_cases(self, scoring_service):
        """Test Z-score calculation edge cases"""
        job = Job(hourly_wage=2000)

        # Test with zero standard deviation
        area_stats = {"mean": 2000, "std_dev": 0, "prefecture_cd": 13}
        score = await scoring_service.calculate_hourly_wage_score(job, area_stats)
        assert score == 50  # Should return median score

        # Test with extreme values
        job.hourly_wage = 10000
        area_stats = {"mean": 2000, "std_dev": 500, "prefecture_cd": 13}
        score = await scoring_service.calculate_hourly_wage_score(job, area_stats)
        assert score <= 100  # Should be capped at 100

    @pytest.mark.asyncio
    async def test_company_popularity_weighting(self, scoring_service):
        """Test company popularity weighting between applications and views"""
        # High applications, low views
        data1 = {
            "company_name": "Company1",
            "application_count_360d": 1000,
            "view_count_360d": 100
        }

        # Low applications, high views
        data2 = {
            "company_name": "Company2",
            "application_count_360d": 100,
            "view_count_360d": 10000
        }

        score1 = await scoring_service.calculate_company_popularity_score(data1)
        score2 = await scoring_service.calculate_company_popularity_score(data2)

        # Applications should be weighted more heavily
        assert score1 > score2