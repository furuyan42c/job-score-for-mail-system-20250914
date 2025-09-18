"""
スコアリングエンジンの単体テスト
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.scoring import ScoringEngine
from app.models.jobs import Job, JobSalary, JobFeatures, JobCategory, JobLocation
from app.models.users import User, UserProfile, UserPreferences, UserBehaviorStats
from app.models.matching import ScoringConfiguration


class TestScoringEngine:
    """スコアリングエンジンテストクラス"""

    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return AsyncMock()

    @pytest.fixture
    def scoring_engine(self, mock_db):
        """スコアリングエンジンインスタンス"""
        return ScoringEngine(mock_db)

    @pytest.fixture
    def sample_user(self):
        """サンプルユーザー"""
        return User(
            user_id=1,
            email="test@example.com",
            email_hash="hash123",
            age_group="20代前半",
            gender="male",
            estimated_pref_cd="13",
            estimated_city_cd="13101",
            registration_date=datetime.now().date(),
            is_active=True,
            email_subscription=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def sample_job(self):
        """サンプル求人"""
        return Job(
            job_id=1,
            endcl_cd="TEST001",
            company_name="テスト株式会社",
            application_name="テスト求人",
            location=JobLocation(
                prefecture_code="13",
                city_code="13101",
                address="東京都千代田区"
            ),
            salary=JobSalary(
                salary_type="hourly",
                min_salary=1200,
                max_salary=1500,
                fee=1000
            ),
            category=JobCategory(
                occupation_cd1=100,
                occupation_cd2=101
            ),
            features=JobFeatures(
                feature_codes=["D01", "N01"],
                has_daily_payment=True,
                has_no_experience=True
            ),
            posting_date=datetime.now(),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def sample_user_profile(self):
        """サンプルユーザープロファイル"""
        return UserProfile(
            user_id=1,
            preferences=UserPreferences(
                preferred_categories=[100, 200],
                preferred_salary_min=1000,
                location_preference_radius=20
            ),
            behavior_stats=UserBehaviorStats(
                application_count=5,
                click_count=20,
                view_count=50,
                avg_salary_preference=1200
            ),
            preference_scores={
                "daily_payment": 0.8,
                "no_experience": 0.9,
                "student_welcome": 0.6
            },
            category_interests={"100": 0.9, "200": 0.3},
            profile_updated_at=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_calculate_basic_score(self, scoring_engine, sample_user, sample_job):
        """基本スコア計算テスト"""
        score = await scoring_engine._calculate_basic_score(sample_user, sample_job)

        assert 0 <= score <= 100
        assert isinstance(score, float)

    @pytest.mark.asyncio
    async def test_calculate_location_score_same_prefecture(self, scoring_engine, sample_user, sample_job):
        """立地スコア計算テスト（同じ都道府県）"""
        score = await scoring_engine._calculate_location_score(sample_user, sample_job)

        # 同じ都道府県・市区町村なので高スコアが期待される
        assert score >= 80
        assert score <= 100

    @pytest.mark.asyncio
    async def test_calculate_location_score_different_prefecture(self, scoring_engine, sample_user, sample_job):
        """立地スコア計算テスト（異なる都道府県）"""
        # 求人の都道府県を変更
        sample_job.location.prefecture_code = "27"  # 大阪府
        sample_job.location.city_code = "27100"

        with patch.object(scoring_engine, '_get_adjacent_prefectures', return_value=[]):
            score = await scoring_engine._calculate_location_score(sample_user, sample_job)

        # 遠い地域なので低スコアが期待される
        assert score <= 30

    @pytest.mark.asyncio
    async def test_calculate_category_score_perfect_match(self, scoring_engine, sample_user, sample_job, sample_user_profile):
        """カテゴリスコア計算テスト（完全一致）"""
        score = await scoring_engine._calculate_category_score(sample_user, sample_job, sample_user_profile)

        # 完全一致なので高スコアが期待される
        assert score >= 85

    @pytest.mark.asyncio
    async def test_calculate_salary_score_high_salary(self, scoring_engine, sample_user, sample_job, sample_user_profile):
        """給与スコア計算テスト（高給与）"""
        # 高給与に設定
        sample_job.salary.min_salary = 2000

        score = await scoring_engine._calculate_salary_score(sample_user, sample_job, sample_user_profile)

        # 希望給与を上回るので高スコアが期待される
        assert score >= 80

    @pytest.mark.asyncio
    async def test_calculate_feature_score_matching_preferences(self, scoring_engine, sample_user, sample_job, sample_user_profile):
        """特徴スコア計算テスト（嗜好一致）"""
        score = await scoring_engine._calculate_feature_score(sample_user, sample_job, sample_user_profile)

        # 日払い・未経験歓迎の嗜好が高いので高スコアが期待される
        assert score >= 60

    @pytest.mark.asyncio
    async def test_calculate_composite_score(self, scoring_engine, sample_user, sample_job, sample_user_profile):
        """総合スコア計算テスト"""
        with patch.object(scoring_engine, '_get_adjacent_prefectures', return_value=[]), \
             patch.object(scoring_engine, '_get_company_popularity', return_value={'application_rate': 0.05, 'applications_7d': 20}), \
             patch.object(scoring_engine, '_check_recent_application', return_value=False):

            score = await scoring_engine.calculate_score(sample_user, sample_job, sample_user_profile)

        assert isinstance(score.composite_score, float)
        assert 0 <= score.composite_score <= 100
        assert all(0 <= s <= 100 for s in [
            score.basic_score, score.location_score, score.category_score,
            score.salary_score, score.feature_score, score.preference_score,
            score.popularity_score
        ])

    @pytest.mark.asyncio
    async def test_bonus_points_perfect_category_match(self, scoring_engine, sample_user, sample_job, sample_user_profile):
        """ボーナスポイント計算テスト（完全カテゴリ一致）"""
        bonus = await scoring_engine._calculate_bonus_points(sample_user, sample_job, sample_user_profile)

        assert 'perfect_category_match' in bonus
        assert bonus['perfect_category_match'] == 15.0

    @pytest.mark.asyncio
    async def test_penalty_points_recent_application(self, scoring_engine, sample_user, sample_job):
        """ペナルティポイント計算テスト（最近の応募）"""
        with patch.object(scoring_engine, '_check_recent_application', return_value=True), \
             patch.object(scoring_engine, '_get_adjacent_prefectures', return_value=[]):

            penalty = await scoring_engine._calculate_penalty_points(sample_user, sample_job)

        assert 'recent_application' in penalty
        assert penalty['recent_application'] == -20.0

    @pytest.mark.asyncio
    async def test_batch_calculate_scores(self, scoring_engine, sample_user, sample_job, sample_user_profile):
        """バッチスコア計算テスト"""
        user_job_pairs = [
            (sample_user, sample_job, sample_user_profile),
            (sample_user, sample_job, sample_user_profile)
        ]

        with patch.object(scoring_engine, 'calculate_score') as mock_calculate:
            mock_calculate.return_value = AsyncMock()

            results = await scoring_engine.batch_calculate_scores(user_job_pairs)

        assert len(results) == 2
        assert mock_calculate.call_count == 2

    def test_scoring_configuration_validation(self):
        """スコアリング設定バリデーションテスト"""
        # 正常な設定
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
            thresholds={'min_distance_km': 50.0},
            version="test"
        )

        # 重みの合計が1.0になることを確認
        assert abs(sum(config.weights.values()) - 1.0) < 0.01

    def test_scoring_configuration_invalid_weights(self):
        """スコアリング設定バリデーションテスト（無効な重み）"""
        with pytest.raises(ValueError):
            ScoringConfiguration(
                weights={
                    'basic_score': 0.5,
                    'location_score': 0.5,
                    'category_score': 0.5  # 合計が1.0を超える
                },
                thresholds={},
                version="test"
            )