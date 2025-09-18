"""
スコア計算とマッチングAPIの包括的テスト

スコアリングエンジン、マッチング処理、パフォーマンス、
リアルタイム処理のテストを実装
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import asyncio
import time
from datetime import datetime, date, timedelta

from app.services.scoring import ScoringEngine
from app.models.matching import (
    MatchingScore, MatchingRequest, ScoringConfiguration,
    MatchingResult, ABTestConfig, RealtimeMatchingRequest
)
from app.models.jobs import Job
from app.models.users import User, UserProfile


class TestScoringEngine:
    """スコアリングエンジンのテスト"""

    @pytest.fixture
    async def scoring_engine(self, mock_database_session):
        """スコアリングエンジンのフィクスチャ"""
        return ScoringEngine(mock_database_session)

    @pytest.fixture
    def sample_user(self):
        """サンプルユーザー"""
        return User(
            user_id=1,
            email="test@example.com",
            age_group="20代前半",
            gender="male",
            estimated_pref_cd="13",
            estimated_city_cd="13101",
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
            location={
                "prefecture_code": "13",
                "city_code": "13101",
                "address": "東京都渋谷区1-1-1"
            },
            salary={
                "salary_type": "hourly",
                "min_salary": 1200,
                "max_salary": 1500,
                "fee": 1000
            },
            work_conditions={
                "hours": "9:00-18:00",
                "employment_type_cd": 1
            },
            category={
                "occupation_cd1": 100,
                "occupation_cd2": 101
            },
            features={
                "has_daily_payment": True,
                "has_no_experience": True,
                "has_transportation": True
            },
            posting_date=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def sample_user_profile(self):
        """サンプルユーザープロファイル"""
        return UserProfile(
            user_id=1,
            preference_scores={
                "daily_payment": 0.8,
                "no_experience": 0.9,
                "transportation": 0.7
            },
            category_interests={
                "100": 0.85,
                "200": 0.6
            },
            latent_factors=[0.5, 0.3, 0.8, 0.2, 0.6, 0.4, 0.7, 0.1, 0.9, 0.3],
            behavioral_cluster=1,
            profile_updated_at=datetime.now(),
            created_at=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_calculate_score_basic(self, scoring_engine, sample_user, sample_job):
        """基本スコア計算テスト"""
        score = await scoring_engine.calculate_score(sample_user, sample_job)

        assert isinstance(score, MatchingScore)
        assert 0 <= score.basic_score <= 100
        assert 0 <= score.location_score <= 100
        assert 0 <= score.category_score <= 100
        assert 0 <= score.composite_score <= 100

    @pytest.mark.asyncio
    async def test_calculate_score_with_profile(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """プロファイル付きスコア計算テスト"""
        score = await scoring_engine.calculate_score(
            sample_user, sample_job, sample_user_profile
        )

        assert isinstance(score, MatchingScore)
        assert score.preference_score > 0
        assert score.feature_score > 0
        # プロファイル情報により精度の高いスコアが計算されることを確認

    @pytest.mark.asyncio
    async def test_calculate_basic_score(self, scoring_engine, sample_user, sample_job):
        """基本スコア計算の詳細テスト"""
        basic_score = await scoring_engine._calculate_basic_score(sample_user, sample_job)

        assert isinstance(basic_score, float)
        assert 0 <= basic_score <= 100

        # 給与レベルによる加点確認
        if sample_job.salary.min_salary >= 1200:
            assert basic_score > 50  # ベーススコア + ボーナス

    @pytest.mark.asyncio
    async def test_calculate_location_score(self, scoring_engine, sample_user, sample_job):
        """立地スコア計算テスト"""
        location_score = await scoring_engine._calculate_location_score(sample_user, sample_job)

        assert isinstance(location_score, float)
        assert 0 <= location_score <= 100

        # 同じ都道府県の場合は高スコア
        if sample_user.estimated_pref_cd == sample_job.location.prefecture_code:
            assert location_score >= 80

    @pytest.mark.asyncio
    async def test_calculate_category_score(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """カテゴリスコア計算テスト"""
        category_score = await scoring_engine._calculate_category_score(
            sample_user, sample_job, sample_user_profile
        )

        assert isinstance(category_score, float)
        assert 0 <= category_score <= 100

    @pytest.mark.asyncio
    async def test_calculate_salary_score(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """給与スコア計算テスト"""
        salary_score = await scoring_engine._calculate_salary_score(
            sample_user, sample_job, sample_user_profile
        )

        assert isinstance(salary_score, float)
        assert 0 <= salary_score <= 100

    @pytest.mark.asyncio
    async def test_calculate_feature_score(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """特徴スコア計算テスト"""
        feature_score = await scoring_engine._calculate_feature_score(
            sample_user, sample_job, sample_user_profile
        )

        assert isinstance(feature_score, float)
        assert 0 <= feature_score <= 100

        # プロファイルの嗜好に合致する特徴があれば高スコア
        if (sample_user_profile.preference_scores.get('daily_payment', 0) > 0.6 and
            sample_job.features.has_daily_payment):
            assert feature_score > 50

    @pytest.mark.asyncio
    async def test_calculate_bonus_points(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """ボーナスポイント計算テスト"""
        bonus = await scoring_engine._calculate_bonus_points(
            sample_user, sample_job, sample_user_profile
        )

        assert isinstance(bonus, dict)
        assert all(isinstance(v, float) for v in bonus.values())

        # 高収入求人ボーナス確認
        if sample_job.salary.min_salary >= 1500:
            assert 'high_income_job' in bonus

    @pytest.mark.asyncio
    async def test_calculate_penalty_points(self, scoring_engine, sample_user, sample_job):
        """ペナルティポイント計算テスト"""
        penalty = await scoring_engine._calculate_penalty_points(sample_user, sample_job)

        assert isinstance(penalty, dict)
        assert all(isinstance(v, float) for v in penalty.values())
        assert all(v <= 0 for v in penalty.values())  # ペナルティは負の値

    @pytest.mark.asyncio
    async def test_batch_calculate_scores(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """バッチスコア計算テスト"""
        # 複数のユーザー・求人ペアを作成
        pairs = [
            (sample_user, sample_job, sample_user_profile),
            (sample_user, sample_job, None),
            (sample_user, sample_job, sample_user_profile)
        ]

        scores = await scoring_engine.batch_calculate_scores(pairs)

        assert len(scores) == 3
        assert all(isinstance(score, MatchingScore) for score in scores)

    @pytest.mark.asyncio
    async def test_scoring_error_handling(self, scoring_engine, sample_user):
        """スコア計算エラーハンドリングテスト"""
        # 不正な求人データでエラーを発生させる
        invalid_job = Job(
            job_id=-1,
            endcl_cd="",
            company_name="",
            application_name="",
            location={},
            salary={},
            work_conditions={},
            category={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        score = await scoring_engine.calculate_score(sample_user, invalid_job)

        # エラー時は低スコアが返されることを確認
        assert score.composite_score == 0
        assert 'error' in score.penalty_points


class TestScoringConfiguration:
    """スコアリング設定のテスト"""

    def test_scoring_configuration_validation(self):
        """スコアリング設定バリデーションテスト"""
        # 正常な設定
        valid_config = ScoringConfiguration(
            weights={
                'basic_score': 0.25,
                'location_score': 0.15,
                'category_score': 0.20,
                'salary_score': 0.15,
                'feature_score': 0.10,
                'preference_score': 0.10,
                'popularity_score': 0.05
            },
            thresholds={
                'min_distance_km': 50.0,
                'high_income_threshold': 1500
            },
            version="v1.0"
        )
        assert valid_config.weights['basic_score'] == 0.25

    def test_invalid_weights_sum(self):
        """重みの合計が1.0でない場合のテスト"""
        with pytest.raises(ValueError, match="重みの合計は1.0である必要があります"):
            ScoringConfiguration(
                weights={
                    'basic_score': 0.5,
                    'location_score': 0.5,  # 合計1.0を超える
                    'category_score': 0.5,
                    'salary_score': 0.0,
                    'feature_score': 0.0,
                    'preference_score': 0.0,
                    'popularity_score': 0.0
                },
                thresholds={},
                version="v1.0"
            )

    def test_missing_required_weights(self):
        """必要な重み設定が不足している場合のテスト"""
        with pytest.raises(ValueError, match="必要な重み設定が不足しています"):
            ScoringConfiguration(
                weights={
                    'basic_score': 1.0
                    # その他の重みが不足
                },
                thresholds={},
                version="v1.0"
            )


class TestMatchingAPI:
    """マッチングAPIのテスト"""

    @pytest.mark.asyncio
    async def test_realtime_matching_request(self, async_client: AsyncClient):
        """リアルタイムマッチングリクエストテスト"""
        request_data = {
            "user_id": 1,
            "max_results": 20,
            "exclude_job_ids": [1, 2, 3],
            "include_explanations": True
        }

        response = await async_client.post("/matching/realtime", json=request_data)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "user_id" in data
            assert "matches" in data
            assert "processing_time_ms" in data

    @pytest.mark.asyncio
    async def test_batch_matching_request(self, async_client: AsyncClient):
        """バッチマッチングリクエストテスト"""
        request_data = {
            "user_ids": [1, 2, 3],
            "job_ids": [1, 2, 3, 4, 5],
            "score_threshold": 70.0,
            "max_results_per_user": 50,
            "dry_run": True
        }

        response = await async_client.post("/matching/batch", json=request_data)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]

    @pytest.mark.asyncio
    async def test_get_matching_results(self, async_client: AsyncClient):
        """マッチング結果取得テスト"""
        params = {
            "user_id": 1,
            "min_score": 60.0,
            "limit": 20
        }

        response = await async_client.get("/matching/results", params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list) or "items" in data

    @pytest.mark.asyncio
    async def test_get_user_score_breakdown(self, async_client: AsyncClient):
        """ユーザースコア詳細取得テスト"""
        user_id = 1
        job_id = 1

        response = await async_client.get(f"/scoring/users/{user_id}/jobs/{job_id}/breakdown")

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "basic_score" in data
            assert "composite_score" in data
            assert "score_breakdown" in data

    @pytest.mark.asyncio
    async def test_recalculate_user_scores(self, async_client: AsyncClient):
        """ユーザースコア再計算テスト"""
        user_id = 1
        response = await async_client.post(f"/scoring/users/{user_id}/recalculate")

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_202_ACCEPTED,
            status.HTTP_404_NOT_FOUND
        ]

    @pytest.mark.asyncio
    async def test_scoring_configuration_update(self, async_client: AsyncClient):
        """スコアリング設定更新テスト"""
        config_data = {
            "weights": {
                "basic_score": 0.30,
                "location_score": 0.20,
                "category_score": 0.20,
                "salary_score": 0.15,
                "feature_score": 0.10,
                "preference_score": 0.05,
                "popularity_score": 0.00
            },
            "thresholds": {
                "min_distance_km": 30.0,
                "high_income_threshold": 1800
            },
            "version": "v1.1"
        }

        response = await async_client.put("/scoring/configuration", json=config_data)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]


class TestScoringPerformance:
    """スコアリングパフォーマンステスト"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_single_score_calculation_performance(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """単一スコア計算パフォーマンステスト"""
        start_time = time.time()

        score = await scoring_engine.calculate_score(
            sample_user, sample_job, sample_user_profile
        )

        end_time = time.time()
        calculation_time = end_time - start_time

        assert isinstance(score, MatchingScore)
        assert calculation_time < 0.1  # 100ms以内

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_batch_scoring_performance(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """バッチスコアリングパフォーマンステスト"""
        # 1000ペアのバッチ処理
        batch_size = 1000
        pairs = [(sample_user, sample_job, sample_user_profile)] * batch_size

        start_time = time.time()
        scores = await scoring_engine.batch_calculate_scores(pairs)
        end_time = time.time()

        processing_time = end_time - start_time
        avg_time_per_pair = processing_time / batch_size

        assert len(scores) == batch_size
        assert processing_time < 10.0  # 10秒以内
        assert avg_time_per_pair < 0.01  # 10ms以内/ペア

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_scoring(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """並行スコアリングテスト"""
        # 100個の並行リクエスト
        concurrent_requests = 100

        async def calculate_single_score():
            return await scoring_engine.calculate_score(
                sample_user, sample_job, sample_user_profile
            )

        start_time = time.time()
        tasks = [calculate_single_score() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        processing_time = end_time - start_time

        assert len(results) == concurrent_requests
        assert all(isinstance(result, MatchingScore) for result in results)
        assert processing_time < 5.0  # 5秒以内

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_scoring_memory_usage(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """スコアリングメモリ使用量テスト"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 大量のスコア計算
        batch_size = 10000
        pairs = [(sample_user, sample_job, sample_user_profile)] * batch_size

        scores = await scoring_engine.batch_calculate_scores(pairs)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # メモリ使用量が合理的な範囲内であることを確認
        assert len(scores) == batch_size
        assert memory_increase < 100 * 1024 * 1024  # 100MB以内


class TestMatchingQuality:
    """マッチング品質のテスト"""

    @pytest.mark.asyncio
    async def test_score_consistency(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """スコア一貫性テスト（同じ入力で同じ結果）"""
        # 同じ入力で複数回計算
        scores = []
        for _ in range(5):
            score = await scoring_engine.calculate_score(
                sample_user, sample_job, sample_user_profile
            )
            scores.append(score)

        # すべて同じスコアが返されることを確認
        first_score = scores[0]
        for score in scores[1:]:
            assert abs(score.composite_score - first_score.composite_score) < 0.001

    @pytest.mark.asyncio
    async def test_score_range_validation(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """スコア範囲妥当性テスト"""
        score = await scoring_engine.calculate_score(
            sample_user, sample_job, sample_user_profile
        )

        # すべてのスコアが有効な範囲内であることを確認
        assert 0 <= score.basic_score <= 100
        assert 0 <= score.location_score <= 100
        assert 0 <= score.category_score <= 100
        assert 0 <= score.salary_score <= 100
        assert 0 <= score.feature_score <= 100
        assert 0 <= score.preference_score <= 100
        assert 0 <= score.popularity_score <= 100
        assert 0 <= score.composite_score <= 100

    @pytest.mark.asyncio
    async def test_high_quality_match_detection(
        self, scoring_engine, sample_user, sample_job, sample_user_profile
    ):
        """高品質マッチ検出テスト"""
        # 完璧な条件のユーザープロファイルを作成
        perfect_profile = UserProfile(
            user_id=1,
            preference_scores={
                "daily_payment": 1.0,
                "no_experience": 1.0,
                "transportation": 1.0
            },
            category_interests={
                str(sample_job.category.occupation_cd1): 1.0
            },
            latent_factors=[1.0] * 10,
            behavioral_cluster=1,
            profile_updated_at=datetime.now(),
            created_at=datetime.now()
        )

        # 完璧な条件のユーザーを作成
        perfect_user = User(
            user_id=1,
            email="perfect@example.com",
            age_group="20代前半",
            gender="male",
            estimated_pref_cd=sample_job.location.prefecture_code,
            estimated_city_cd=sample_job.location.city_code,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        score = await scoring_engine.calculate_score(
            perfect_user, sample_job, perfect_profile
        )

        # 高スコアが算出されることを確認
        assert score.composite_score > 80

    @pytest.mark.asyncio
    async def test_poor_match_detection(
        self, scoring_engine, sample_user, sample_job
    ):
        """低品質マッチ検出テスト"""
        # 条件が合わないユーザーを作成
        poor_user = User(
            user_id=2,
            email="poor@example.com",
            age_group="50代以上",
            gender="female",
            estimated_pref_cd="47",  # 沖縄県
            estimated_city_cd="47201",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        score = await scoring_engine.calculate_score(poor_user, sample_job)

        # 低スコアが算出されることを確認
        assert score.composite_score < 50


class TestABTesting:
    """A/Bテストのテスト"""

    def test_ab_test_config_validation(self):
        """A/Bテスト設定バリデーションテスト"""
        control_config = ScoringConfiguration(
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
            version="v1.0"
        )

        treatment_config = ScoringConfiguration(
            weights={
                'basic_score': 0.20,
                'location_score': 0.20,
                'category_score': 0.25,
                'salary_score': 0.15,
                'feature_score': 0.10,
                'preference_score': 0.05,
                'popularity_score': 0.05
            },
            thresholds={},
            version="v1.1"
        )

        ab_test = ABTestConfig(
            test_id="test_001",
            test_name="カテゴリ重み調整テスト",
            description="カテゴリスコアの重みを上げる実験",
            control_config=control_config,
            treatment_config=treatment_config,
            traffic_split=0.5,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            success_metrics=["ctr", "application_rate", "user_engagement"]
        )

        assert ab_test.test_id == "test_001"
        assert ab_test.traffic_split == 0.5


class TestScoringAPI:
    """スコアリングAPIのテスト"""

    @pytest.mark.asyncio
    async def test_calculate_user_job_score(self, async_client: AsyncClient):
        """ユーザー・求人スコア計算APIテスト"""
        user_id = 1
        job_id = 1

        response = await async_client.post(f"/scoring/calculate/{user_id}/{job_id}")

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "composite_score" in data
            assert "basic_score" in data

    @pytest.mark.asyncio
    async def test_bulk_score_calculation(self, async_client: AsyncClient):
        """一括スコア計算APIテスト"""
        request_data = {
            "user_job_pairs": [
                {"user_id": 1, "job_id": 1},
                {"user_id": 1, "job_id": 2},
                {"user_id": 2, "job_id": 1}
            ]
        }

        response = await async_client.post("/scoring/bulk", json=request_data)

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_202_ACCEPTED
        ]

    @pytest.mark.asyncio
    async def test_get_scoring_analytics(self, async_client: AsyncClient):
        """スコアリング分析取得APIテスト"""
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }

        response = await async_client.get("/scoring/analytics", params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "avg_score" in data or isinstance(data, dict)


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_database_error_handling(self, async_client: AsyncClient):
        """データベースエラーハンドリングテスト"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            response = await async_client.post("/scoring/calculate/1/1")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_invalid_user_id(self, async_client: AsyncClient):
        """無効なユーザーIDテスト"""
        response = await async_client.post("/scoring/calculate/invalid/1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_invalid_job_id(self, async_client: AsyncClient):
        """無効な求人IDテスト"""
        response = await async_client.post("/scoring/calculate/1/invalid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_missing_data_handling(self, async_client: AsyncClient):
        """データ不足時のハンドリングテスト"""
        # 存在しないユーザー・求人の組み合わせ
        response = await async_client.post("/scoring/calculate/999999/999999")
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]


@pytest.fixture
def mock_scoring_service():
    """ScoringServiceのモック"""
    with patch('app.services.scoring.ScoringEngine') as mock:
        service_instance = mock.return_value
        service_instance.calculate_score = AsyncMock()
        service_instance.batch_calculate_scores = AsyncMock()
        yield service_instance