"""
T021: 基礎スコア計算の統合テスト
仕様書準拠の検証テストスイート
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import numpy as np

from app.services.basic_scoring import BasicScoringEngine, MIN_FEE_THRESHOLD
from app.models.jobs import Job, JobSalary, JobLocation, JobCategory, JobFeatures
from app.models.users import User


@pytest.fixture
def mock_db_session():
    """モックDBセッション"""
    session = AsyncMock()
    return session


@pytest.fixture
def scoring_engine(mock_db_session):
    """スコアリングエンジンインスタンス"""
    return BasicScoringEngine(mock_db_session)


@pytest.fixture
def sample_job():
    """サンプル求人データ"""
    job = MagicMock(spec=Job)
    job.job_id = "TEST_JOB_001"
    job.endcl_cd = "COMPANY_001"
    job.employment_type_cd = 1  # アルバイト
    job.fee = 1000  # 正常なfee

    # 給与情報
    job.salary = MagicMock(spec=JobSalary)
    job.salary.min_salary = 1200
    job.salary.max_salary = 1500
    job.salary.salary_type = "hourly"

    # 位置情報
    job.location = MagicMock(spec=JobLocation)
    job.location.prefecture_code = "13"  # 東京
    job.location.city_code = "101"  # 千代田区

    # カテゴリ情報
    job.category = MagicMock(spec=JobCategory)
    job.category.occupation_cd1 = 1

    return job


@pytest.fixture
def area_stats():
    """エリア統計データ"""
    return {
        'avg_salary': 1300,  # 平均時給
        'std_salary': 200,   # 標準偏差
        'job_count': 1000
    }


class TestFeeValidation:
    """Fee > 500 チェックのテスト"""

    @pytest.mark.asyncio
    async def test_fee_below_threshold_returns_zero(self, scoring_engine, sample_job):
        """fee <= 500の場合、スコアが0になることを確認"""
        # fee = 500 (閾値)
        sample_job.fee = 500
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score == 0.0, f"Fee=500 should return 0, got {score}"

        # fee = 499 (閾値未満)
        sample_job.fee = 499
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score == 0.0, f"Fee=499 should return 0, got {score}"

        # fee = 1 (極小値)
        sample_job.fee = 1
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score == 0.0, f"Fee=1 should return 0, got {score}"

    @pytest.mark.asyncio
    async def test_fee_above_threshold_returns_positive(self, scoring_engine, sample_job):
        """fee > 500の場合、正のスコアが返ることを確認"""
        # fee = 501 (閾値+1)
        sample_job.fee = 501
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score > 0.0, f"Fee=501 should return positive score, got {score}"

        # fee = 1000 (通常値)
        sample_job.fee = 1000
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score > 0.0, f"Fee=1000 should return positive score, got {score}"

    @pytest.mark.asyncio
    async def test_fee_normalization(self, scoring_engine, sample_job):
        """Fee正規化の計算が正しいことを確認"""
        # fee = 500: 0点
        assert scoring_engine._calculate_fee_score(
            MagicMock(fee=500)
        ) == 0.0

        # fee = 2750: 50点 (中間値)
        expected = (2750 - 500) / (5000 - 500) * 100
        assert abs(scoring_engine._calculate_fee_score(
            MagicMock(fee=2750)
        ) - expected) < 0.01

        # fee = 5000: 100点
        assert scoring_engine._calculate_fee_score(
            MagicMock(fee=5000)
        ) == 100.0

        # fee > 5000: 100点（上限）
        assert scoring_engine._calculate_fee_score(
            MagicMock(fee=10000)
        ) == 100.0


class TestHourlyWageNormalization:
    """時給正規化（z-score）のテスト"""

    @pytest.mark.asyncio
    async def test_zscore_normalization(self, scoring_engine, sample_job, area_stats):
        """z-score正規化が正しく計算されることを確認"""
        # 平均値の場合: z=0 → 50点
        sample_job.salary.min_salary = 1300
        sample_job.salary.max_salary = 1300
        score = await scoring_engine._calculate_hourly_wage_score(sample_job, area_stats)
        assert abs(score - 50.0) < 0.01, f"Average wage should give 50 points, got {score}"

        # +1σの場合: z=1 → 75点
        sample_job.salary.min_salary = 1500
        sample_job.salary.max_salary = 1500
        score = await scoring_engine._calculate_hourly_wage_score(sample_job, area_stats)
        assert abs(score - 75.0) < 0.01, f"+1σ wage should give 75 points, got {score}"

        # -1σの場合: z=-1 → 25点
        sample_job.salary.min_salary = 1100
        sample_job.salary.max_salary = 1100
        score = await scoring_engine._calculate_hourly_wage_score(sample_job, area_stats)
        assert abs(score - 25.0) < 0.01, f"-1σ wage should give 25 points, got {score}"

        # +2σ以上の場合: z>=2 → 100点
        sample_job.salary.min_salary = 1700
        sample_job.salary.max_salary = 1700
        score = await scoring_engine._calculate_hourly_wage_score(sample_job, area_stats)
        assert score == 100.0, f"+2σ wage should give 100 points, got {score}"

        # -2σ以下の場合: z<=-2 → 0点
        sample_job.salary.min_salary = 900
        sample_job.salary.max_salary = 900
        score = await scoring_engine._calculate_hourly_wage_score(sample_job, area_stats)
        assert score == 0.0, f"-2σ wage should give 0 points, got {score}"

    @pytest.mark.asyncio
    async def test_daily_wage_conversion(self, scoring_engine, sample_job, area_stats):
        """日給から時給への変換が正しいことを確認"""
        # 日給10,400円 = 時給1,300円（8時間労働）
        sample_job.salary.salary_type = "daily"
        sample_job.salary.min_salary = 10400
        sample_job.salary.max_salary = 10400
        score = await scoring_engine._calculate_hourly_wage_score(sample_job, area_stats)
        assert abs(score - 50.0) < 1.0, f"Daily wage 10400 should give ~50 points, got {score}"

    @pytest.mark.asyncio
    async def test_monthly_wage_conversion(self, scoring_engine, sample_job, area_stats):
        """月給から時給への変換が正しいことを確認"""
        # 月給208,000円 = 時給1,300円（160時間労働）
        sample_job.salary.salary_type = "monthly"
        sample_job.salary.min_salary = 208000
        sample_job.salary.max_salary = 208000
        score = await scoring_engine._calculate_hourly_wage_score(sample_job, area_stats)
        assert abs(score - 50.0) < 1.0, f"Monthly wage 208000 should give ~50 points, got {score}"


class TestCompanyPopularity:
    """企業人気度計算（360日データ）のテスト"""

    @pytest.mark.asyncio
    async def test_popularity_360d_calculation(self, scoring_engine, sample_job, mock_db_session):
        """360日データを使用した人気度計算を確認"""
        # モックデータ設定
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            views_360d=1000,
            applications_360d=150,  # 15%応募率
            applications_7d=10
        )
        mock_db_session.execute.return_value = mock_result

        score = await scoring_engine._calculate_company_popularity_score(sample_job)
        assert score == 100.0, f"15% application rate should give 100 points, got {score}"

        # 10%応募率
        mock_result.fetchone.return_value = MagicMock(
            views_360d=1000,
            applications_360d=100,
            applications_7d=5
        )
        scoring_engine._company_popularity_cache.clear()
        score = await scoring_engine._calculate_company_popularity_score(sample_job)
        assert score == 80.0, f"10% application rate should give 80 points, got {score}"

        # 5%応募率
        mock_result.fetchone.return_value = MagicMock(
            views_360d=1000,
            applications_360d=50,
            applications_7d=2
        )
        scoring_engine._company_popularity_cache.clear()
        score = await scoring_engine._calculate_company_popularity_score(sample_job)
        assert score == 60.0, f"5% application rate should give 60 points, got {score}"

        # 2%応募率
        mock_result.fetchone.return_value = MagicMock(
            views_360d=1000,
            applications_360d=20,
            applications_7d=1
        )
        scoring_engine._company_popularity_cache.clear()
        score = await scoring_engine._calculate_company_popularity_score(sample_job)
        assert score == 40.0, f"2% application rate should give 40 points, got {score}"

        # 2%未満
        mock_result.fetchone.return_value = MagicMock(
            views_360d=1000,
            applications_360d=10,
            applications_7d=0
        )
        scoring_engine._company_popularity_cache.clear()
        score = await scoring_engine._calculate_company_popularity_score(sample_job)
        assert score == 20.0, f"<2% application rate should give 20 points, got {score}"


class TestBasicScoreIntegration:
    """基礎スコア総合計算のテスト"""

    @pytest.mark.asyncio
    async def test_score_weights(self, scoring_engine, sample_job, mock_db_session):
        """スコアの重み付けが仕様通りであることを確認"""
        # モックデータ設定
        area_stats = {
            'avg_salary': 1350,  # 平均より少し低い
            'std_salary': 200,
            'job_count': 100
        }

        mock_result = MagicMock()
        # エリア統計クエリ結果
        mock_result.fetchone.return_value = MagicMock(
            avg_salary=1350,
            std_salary=200,
            job_count=100
        )

        # 企業人気度クエリ結果（5%応募率）
        popularity_result = MagicMock()
        popularity_result.fetchone.return_value = MagicMock(
            views_360d=1000,
            applications_360d=50,
            applications_7d=2
        )

        # クエリ結果を順番に返す
        mock_db_session.execute.side_effect = [mock_result, popularity_result]

        # テストデータ設定
        sample_job.salary.min_salary = 1350  # 平均値 → 50点
        sample_job.salary.max_salary = 1350
        sample_job.fee = 2750  # 中間値 → 50点

        score = await scoring_engine.calculate_basic_score(sample_job)

        # 期待値計算
        # 時給スコア: 50点 × 0.40 = 20点
        # feeスコア: 50点 × 0.30 = 15点
        # 人気度スコア: 60点 × 0.30 = 18点
        # 合計: 53点
        expected_score = 50 * 0.40 + 50 * 0.30 + 60 * 0.30
        assert abs(score - expected_score) < 1.0, \
            f"Expected score ~{expected_score}, got {score}"

    @pytest.mark.asyncio
    async def test_employment_type_filter(self, scoring_engine, sample_job):
        """無効なemployment_type_cdの場合スコア0を確認"""
        # 正社員（フィルタ対象外）
        sample_job.employment_type_cd = 2
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score == 0.0, f"Invalid employment type should return 0, got {score}"

        # 契約社員（フィルタ対象外）
        sample_job.employment_type_cd = 4
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score == 0.0, f"Invalid employment type should return 0, got {score}"

    @pytest.mark.asyncio
    async def test_edge_cases(self, scoring_engine, sample_job, mock_db_session):
        """エッジケースのテスト"""
        # 給与情報なし
        sample_job.salary = None
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            avg_salary=1200, std_salary=200, job_count=100,
            views_360d=100, applications_360d=5, applications_7d=0
        )
        mock_db_session.execute.return_value = mock_result

        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score >= 0.0, "Should handle missing salary gracefully"

        # fee情報なし
        delattr(sample_job, 'fee')
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score >= 0.0, "Should handle missing fee gracefully"

        # 企業コードなし
        sample_job.endcl_cd = None
        score = await scoring_engine.calculate_basic_score(sample_job)
        assert score >= 0.0, "Should handle missing company code gracefully"


class TestEditorialPopularityScore:
    """編集部おすすめスコアのテスト"""

    @pytest.mark.asyncio
    async def test_editorial_score_with_location(self, scoring_engine, sample_job):
        """地域重み付けを含む編集部スコア計算"""
        sample_job.fee = 2750  # 50点
        sample_job.recent_applications = 25  # 50点

        # 同じ市区町村（重み1.0）
        user_location = {'city_code': '101', 'pref_code': '13'}
        score = await scoring_engine.calculate_editorial_popularity_score(
            sample_job, user_location
        )
        assert abs(score - 50.0) < 1.0, f"Same city should give ~50 points, got {score}"

        # 同じ都道府県（重み0.5）
        user_location = {'city_code': '102', 'pref_code': '13'}
        score = await scoring_engine.calculate_editorial_popularity_score(
            sample_job, user_location
        )
        assert abs(score - 25.0) < 1.0, f"Same prefecture should give ~25 points, got {score}"

        # 異なる都道府県（重み0.3）
        user_location = {'city_code': '201', 'pref_code': '14'}
        score = await scoring_engine.calculate_editorial_popularity_score(
            sample_job, user_location
        )
        assert abs(score - 15.0) < 1.0, f"Different prefecture should give ~15 points, got {score}"


class TestCachingMechanism:
    """キャッシュ機構のテスト"""

    @pytest.mark.asyncio
    async def test_area_stats_caching(self, scoring_engine, sample_job, mock_db_session):
        """エリア統計のキャッシュが機能することを確認"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            avg_salary=1300, std_salary=200, job_count=100
        )
        mock_db_session.execute.return_value = mock_result

        # 1回目の呼び出し
        stats1 = await scoring_engine._get_area_statistics(sample_job)
        # 2回目の呼び出し（キャッシュから）
        stats2 = await scoring_engine._get_area_statistics(sample_job)

        # DBへのクエリは1回のみ
        assert mock_db_session.execute.call_count == 1
        assert stats1 == stats2

    @pytest.mark.asyncio
    async def test_company_popularity_caching(self, scoring_engine, sample_job, mock_db_session):
        """企業人気度のキャッシュが機能することを確認"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            views_360d=1000, applications_360d=50, applications_7d=2
        )
        mock_db_session.execute.return_value = mock_result

        # 1回目の呼び出し
        score1 = await scoring_engine._calculate_company_popularity_score(sample_job)
        # 2回目の呼び出し（キャッシュから）
        score2 = await scoring_engine._calculate_company_popularity_score(sample_job)

        # DBへのクエリは1回のみ
        assert mock_db_session.execute.call_count == 1
        assert score1 == score2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])