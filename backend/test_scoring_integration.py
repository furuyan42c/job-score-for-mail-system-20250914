#!/usr/bin/env python3
"""
Test script to verify T021-T023 scoring components integration
Direct testing without pytest framework dependencies
"""

import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add the project root to Python path
sys.path.append(os.path.dirname(__file__))

# Mock the database dependency
class MockAsyncSession:
    def __init__(self):
        pass

    async def execute(self, query, params=None):
        # Mock database responses
        result = MagicMock()
        result.fetchone.return_value = MagicMock(
            avg_salary=1300,
            std_salary=200,
            job_count=100,
            views_360d=1000,
            applications_360d=50,
            applications_7d=2
        )
        return result

# Create mock job and user objects
def create_mock_job():
    job = MagicMock()
    job.job_id = "TEST_JOB_001"
    job.endcl_cd = "COMPANY_001"
    job.employment_type_cd = 1  # アルバイト
    job.fee = 1000
    job.title = "コンビニ バイト 短期"
    job.company_name = "セブンイレブン"
    job.catch_copy = "駅チカ！日払いOK！"
    job.station_name = "新宿駅"

    # Salary info
    job.salary = MagicMock()
    job.salary.min_salary = 1200
    job.salary.max_salary = 1500
    job.salary.salary_type = "hourly"

    # Location info
    job.location = MagicMock()
    job.location.prefecture_code = "13"  # Tokyo
    job.location.city_code = "101"  # Chiyoda
    job.location.station_name = "新宿駅"

    # Category info
    job.category = MagicMock()
    job.category.occupation_cd1 = 1

    # Features
    job.features = MagicMock()
    job.features.has_daily_payment = True
    job.features.has_no_experience = True
    job.features.has_student_welcome = True

    # Work conditions
    job.work_conditions = MagicMock()
    job.work_conditions.work_hours = "9:00-17:00"

    return job

def create_mock_user():
    user = MagicMock()
    user.user_id = 456
    user.age_group = "20代前半"
    user.estimated_pref_cd = "13"
    user.estimated_city_cd = "101"
    return user

def create_mock_user_profile():
    profile = MagicMock()
    profile.user_id = 456
    profile.application_history = [
        {'category': 1, 'salary_range': {'min': 1000, 'max': 1500}},
        {'category': 1, 'salary_range': {'min': 1100, 'max': 1400}}
    ]
    profile.click_history = [
        {'category': 1}, {'category': 1}, {'category': 2}
    ]
    profile.latent_factors = [0.5] * 50  # 50-dimensional latent factors
    return profile

async def test_basic_scoring():
    """Test T021: Basic scoring implementation"""
    print("Testing T021: Basic Scoring...")

    try:
        from app.services.basic_scoring import BasicScoringEngine

        db = MockAsyncSession()
        engine = BasicScoringEngine(db)
        job = create_mock_job()

        # Test basic score calculation
        score = await engine.calculate_basic_score(job)

        print(f"Basic score: {score}")
        assert 0 <= score <= 100, f"Score {score} is out of range"
        assert score > 0, "Score should be positive for valid job"

        # Test fee threshold
        job_low_fee = create_mock_job()
        job_low_fee.fee = 500  # At threshold
        score_low = await engine.calculate_basic_score(job_low_fee)
        print(f"Low fee score: {score_low}")
        assert score_low == 0.0, "Fee at threshold should return 0"

        print("✅ T021 Basic Scoring tests passed!")
        return True

    except Exception as e:
        print(f"❌ T021 Basic Scoring test failed: {e}")
        return False

async def test_seo_scoring():
    """Test T022: SEO scoring implementation"""
    print("\nTesting T022: SEO Scoring...")

    try:
        from app.services.seo_scoring import SEOScoringEngine
        import pandas as pd

        db = MockAsyncSession()
        engine = SEOScoringEngine(db)
        job = create_mock_job()

        # Create mock SEMRUSH data
        semrush_data = pd.DataFrame([
            {'id': 1, 'keyword': 'コンビニ バイト', 'volume': 10000, 'intent': 'Commercial', 'keyword_difficulty': 45},
            {'id': 2, 'keyword': '短期 バイト', 'volume': 8000, 'intent': 'Transactional', 'keyword_difficulty': 40},
            {'id': 3, 'keyword': '日払い バイト', 'volume': 5000, 'intent': 'Commercial', 'keyword_difficulty': 35},
            {'id': 4, 'keyword': '新宿 バイト', 'volume': 3000, 'intent': 'Navigational', 'keyword_difficulty': 30},
            {'id': 5, 'keyword': 'セブンイレブン', 'volume': 1000, 'intent': 'Informational', 'keyword_difficulty': 25},
        ])

        # Test keyword preprocessing
        processed_df = await engine.preprocess_semrush_keywords(semrush_data)
        print(f"Processed keywords: {len(processed_df)} rows")
        assert len(processed_df) >= len(semrush_data), "Should generate keyword variations"

        # Test SEO score calculation
        score, matched_keywords = await engine.calculate_seo_score(job, processed_df)

        print(f"SEO score: {score}")
        print(f"Matched keywords: {len(matched_keywords)}")

        assert 0 <= score <= 100, f"SEO score {score} is out of range"
        assert len(matched_keywords) <= 7, "Should match max 7 keywords"

        print("✅ T022 SEO Scoring tests passed!")
        return True

    except Exception as e:
        print(f"❌ T022 SEO Scoring test failed: {e}")
        return False

async def test_personalized_scoring():
    """Test T023: Personalized scoring implementation"""
    print("\nTesting T023: Personalized Scoring...")

    try:
        from app.services.personalized_scoring import PersonalizedScoringEngine

        db = MockAsyncSession()
        engine = PersonalizedScoringEngine(db)
        user = create_mock_user()
        job = create_mock_job()
        user_profile = create_mock_user_profile()

        # Initialize ALS model (will use fallback if implicit not available)
        await engine.initialize_als_model()

        # Test personalized score calculation
        score = await engine.calculate_personalized_score(user, job, user_profile)

        print(f"Personalized score: {score}")
        assert 0 <= score <= 100, f"Personalized score {score} is out of range"

        # Test application history analysis
        history_score = await engine._analyze_application_history(
            user_profile.application_history, job
        )
        print(f"Application history score: {history_score}")
        assert history_score >= 0, "History score should be non-negative"

        # Test click pattern analysis
        click_score = await engine._analyze_click_patterns(
            user_profile.click_history, job
        )
        print(f"Click pattern score: {click_score}")
        assert click_score >= 0, "Click score should be non-negative"

        # Test latent factor scoring
        latent_score = engine._calculate_latent_factor_score(
            user_profile.latent_factors, job
        )
        print(f"Latent factor score: {latent_score}")
        assert 0 <= latent_score <= 100, "Latent score should be in range"

        print("✅ T023 Personalized Scoring tests passed!")
        return True

    except Exception as e:
        print(f"❌ T023 Personalized Scoring test failed: {e}")
        return False

async def test_integrated_scoring():
    """Test integrated scoring engine"""
    print("\nTesting Integrated Scoring Engine...")

    try:
        from app.services.scoring import ScoringEngine
        from app.models.matching import ScoringConfiguration

        db = MockAsyncSession()
        config = ScoringConfiguration(
            weights={
                'basic_score': 0.25,
                'location_score': 0.15,
                'category_score': 0.20,
                'salary_score': 0.15,
                'feature_score': 0.10,
                'preference_score': 0.10,
                'popularity_score': 0.05
            },
            thresholds={},
            bonus_rules=[],
            penalty_rules=[],
            version="test"
        )

        engine = ScoringEngine(db, config)
        user = create_mock_user()
        job = create_mock_job()
        user_profile = create_mock_user_profile()

        # Test integrated score calculation
        score_result = await engine.calculate_score(user, job, user_profile)

        print(f"Composite score: {score_result.composite_score}")
        print(f"Basic score: {score_result.basic_score}")
        print(f"SEO score: {score_result.seo_score}")
        print(f"Personalized score: {score_result.personalized_score}")

        assert 0 <= score_result.composite_score <= 100, "Composite score out of range"
        assert hasattr(score_result, 'seo_score'), "Should have SEO score"
        assert hasattr(score_result, 'personalized_score'), "Should have personalized score"

        print("✅ Integrated Scoring Engine tests passed!")
        return True

    except Exception as e:
        print(f"❌ Integrated Scoring Engine test failed: {e}")
        return False

async def main():
    """Run all scoring component tests"""
    print("🔄 Starting T021-T023 Scoring Components Integration Test")
    print("=" * 60)

    # Test all components
    results = []

    # T021 Basic Scoring
    results.append(await test_basic_scoring())

    # T022 SEO Scoring
    results.append(await test_seo_scoring())

    # T023 Personalized Scoring
    results.append(await test_personalized_scoring())

    # Integrated Scoring
    results.append(await test_integrated_scoring())

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 All scoring components are working correctly!")
        print("T021-T023 implementation is ready for production.")
    else:
        print("\n⚠️  Some components need attention.")

    return all(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)