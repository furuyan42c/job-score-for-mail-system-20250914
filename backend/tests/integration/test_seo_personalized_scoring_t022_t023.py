"""
T022 & T023: SEOスコアリングとパーソナライズスコアリングの統合テスト
仕様書準拠の検証テストスイート
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.seo_scoring import SEOScoringEngine, FIELD_WEIGHT_CONFIG
from app.services.personalized_scoring import PersonalizedScoringEngine
from app.models.jobs import Job
from app.models.users import User, UserProfile


@pytest.fixture
def mock_db_session():
    """モックDBセッション"""
    session = AsyncMock()
    return session


@pytest.fixture
def seo_engine(mock_db_session):
    """SEOスコアリングエンジンインスタンス"""
    return SEOScoringEngine(mock_db_session)


@pytest.fixture
def personalized_engine(mock_db_session):
    """パーソナライズスコアリングエンジンインスタンス"""
    return PersonalizedScoringEngine(mock_db_session)


@pytest.fixture
def sample_job():
    """サンプル求人データ"""
    job = MagicMock(spec=Job)
    job.job_id = 123
    job.endcl_cd = "COMPANY_001"
    job.title = "コンビニ バイト 短期"
    job.company_name = "セブンイレブン"
    job.catch_copy = "駅チカ！日払いOK！"
    job.salary_text = "時給1200円〜1500円"
    job.work_hours = "9:00-17:00"
    job.features_text = "日払い 未経験OK 学生歓迎"
    job.station_name = "新宿駅"

    # ネストされたオブジェクト
    job.location = MagicMock()
    job.location.station_name = "新宿駅"

    job.salary = MagicMock()
    job.salary.min_salary = 1200
    job.salary.max_salary = 1500

    job.features = MagicMock()
    job.features.has_daily_payment = True
    job.features.has_no_experience = True
    job.features.has_student_welcome = True

    job.work_conditions = MagicMock()
    job.work_conditions.work_hours = "9:00-17:00"

    return job


@pytest.fixture
def sample_user():
    """サンプルユーザーデータ"""
    user = MagicMock(spec=User)
    user.user_id = 456
    user.age_group = "20代前半"
    user.estimated_pref_cd = "13"
    user.estimated_city_cd = "101"
    return user


@pytest.fixture
def sample_user_profile():
    """サンプルユーザープロファイル"""
    profile = MagicMock(spec=UserProfile)
    profile.user_id = 456
    profile.application_history = [
        {'category': 1, 'salary_range': {'min': 1000, 'max': 1500}},
        {'category': 1, 'salary_range': {'min': 1100, 'max': 1400}}
    ]
    profile.click_history = [
        {'category': 1}, {'category': 1}, {'category': 2}
    ]
    profile.latent_factors = [0.5] * 50  # 50次元の潜在因子
    return profile


@pytest.fixture
def semrush_keywords():
    """SEMRUSHキーワードのサンプルデータ"""
    return pd.DataFrame([
        {'keyword': 'コンビニ バイト', 'volume': 10000, 'intent': 'Commercial', 'keyword_difficulty': 45},
        {'keyword': '短期 バイト', 'volume': 8000, 'intent': 'Transactional', 'keyword_difficulty': 40},
        {'keyword': '日払い バイト', 'volume': 5000, 'intent': 'Commercial', 'keyword_difficulty': 35},
        {'keyword': '新宿 バイト', 'volume': 3000, 'intent': 'Navigational', 'keyword_difficulty': 30},
        {'keyword': 'セブンイレブン', 'volume': 1000, 'intent': 'Informational', 'keyword_difficulty': 25},
    ])


class TestT022SEOScoring:
    """T022: SEOスコアリングのテスト"""

    @pytest.mark.asyncio
    async def test_keyword_preprocessing(self, seo_engine, semrush_keywords):
        """キーワードの前処理とバリエーション生成のテスト"""
        processed_df = await seo_engine.preprocess_semrush_keywords(semrush_keywords)

        # バリエーションが生成されることを確認
        original_count = len(semrush_keywords)
        processed_count = len(processed_df)
        assert processed_count >= original_count, "Variations should be generated"

        # "コンビニ バイト"のバリエーション確認
        konbini_variations = processed_df[
            processed_df['original'] == 'コンビニ バイト'
        ]['processed'].tolist()

        assert 'コンビニ バイト' in konbini_variations
        assert 'コンビニバイト' in konbini_variations

    @pytest.mark.asyncio
    async def test_field_weight_application(self, seo_engine, sample_job, semrush_keywords):
        """フィールドごとの重み付けが正しく適用されることを確認"""
        processed_df = await seo_engine.preprocess_semrush_keywords(semrush_keywords)

        # SEOスコア計算
        score, matched_keywords = await seo_engine.calculate_seo_score(sample_job, processed_df)

        # スコアが0-100の範囲内であることを確認
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"

        # マッチしたキーワードがあることを確認
        assert len(matched_keywords) > 0, "Should have matched keywords"

        # company_nameフィールドの高い重み（1.5）が適用されているか確認
        company_match = [m for m in matched_keywords if m['matched_field'] == 'company_name']
        if company_match:
            # セブンイレブンがマッチした場合、重みが適用されているはず
            assert company_match[0]['score'] > 0

    @pytest.mark.asyncio
    async def test_volume_based_scoring(self, seo_engine):
        """検索ボリュームに基づくスコアリングのテスト"""
        test_cases = [
            (10001, 15),  # >= 10000: 15点
            (5001, 10),   # >= 5000: 10点
            (1001, 7),    # >= 1000: 7点
            (501, 5),     # >= 500: 5点
            (100, 3),     # < 500: 3点
        ]

        for volume, expected_base_score in test_cases:
            keyword_row = pd.Series({
                'volume': volume,
                'intent': 'Informational',
                'processed': 'test'
            })

            score = seo_engine._calculate_keyword_field_score(
                keyword_row, 'catch_copy'  # 標準重み1.0のフィールド
            )

            assert score == expected_base_score, \
                f"Volume {volume} should give base score {expected_base_score}, got {score}"

    @pytest.mark.asyncio
    async def test_intent_multiplier(self, seo_engine):
        """検索意図による倍率のテスト"""
        intents = {
            'Commercial': 1.5,
            'Transactional': 1.3,
            'Informational': 1.0,
            'Navigational': 0.8
        }

        base_volume = 1000  # 基本スコア7点

        for intent, multiplier in intents.items():
            keyword_row = pd.Series({
                'volume': base_volume,
                'intent': intent,
                'processed': 'test'
            })

            score = seo_engine._calculate_keyword_field_score(
                keyword_row, 'catch_copy'  # 標準重み1.0
            )

            expected = 7 * multiplier  # 基本スコア × 意図倍率
            assert abs(score - expected) < 0.01, \
                f"Intent {intent} should give score {expected}, got {score}"

    @pytest.mark.asyncio
    async def test_max_keyword_limit(self, seo_engine, sample_job):
        """最大7個のキーワードまでしかマッチしないことを確認"""
        # 多数のキーワードを生成
        many_keywords = pd.DataFrame([
            {'original': f'keyword{i}', 'processed': f'バイト{i}',
             'volume': 1000, 'intent': 'Informational'}
            for i in range(20)
        ])

        # 全てのキーワードがマッチするように求人を設定
        sample_job.features_text = ' '.join([f'バイト{i}' for i in range(20)])

        score, matched_keywords = await seo_engine.calculate_seo_score(sample_job, many_keywords)

        # 最大7個までしかマッチしていないことを確認
        assert len(matched_keywords) <= 7, f"Should match max 7 keywords, got {len(matched_keywords)}"


class TestT023PersonalizedScoring:
    """T023: パーソナライズスコアリングのテスト"""

    @pytest.mark.asyncio
    async def test_als_model_initialization(self, personalized_engine):
        """ALSモデルの初期化テスト"""
        await personalized_engine.initialize_als_model(
            factors=50,
            regularization=0.01,
            iterations=15
        )

        # implicitライブラリが利用可能な場合のみテスト
        if hasattr(personalized_engine, '_als_model') and personalized_engine._als_model:
            assert personalized_engine._als_model.factors == 50
            assert personalized_engine._als_model.regularization == 0.01
            assert personalized_engine._als_model.iterations == 15

    @pytest.mark.asyncio
    async def test_fallback_scoring(self, personalized_engine, sample_user, sample_job, sample_user_profile):
        """ALSモデルが利用できない場合のフォールバックスコアリング"""
        # ALSモデルを無効化
        personalized_engine._model_trained = False

        score = await personalized_engine.calculate_personalized_score(
            sample_user, sample_job, sample_user_profile
        )

        # スコアが範囲内であることを確認
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"

        # プロファイルベースのスコアが返されることを確認
        assert score > 0, "Should return profile-based score"

    @pytest.mark.asyncio
    async def test_application_history_analysis(self, personalized_engine, sample_job, sample_user_profile):
        """応募履歴分析のテスト"""
        # カテゴリが一致する求人
        sample_job.category = MagicMock()
        sample_job.category.occupation_cd1 = 1

        score = await personalized_engine._analyze_application_history(
            sample_user_profile.application_history, sample_job
        )

        # カテゴリが一致するので正のスコアが返るはず
        assert score > 0, "Should return positive score for matching category"

    @pytest.mark.asyncio
    async def test_click_pattern_analysis(self, personalized_engine, sample_job, sample_user_profile):
        """クリックパターン分析のテスト"""
        sample_job.category = MagicMock()
        sample_job.category.occupation_cd1 = 1

        score = await personalized_engine._analyze_click_patterns(
            sample_user_profile.click_history, sample_job
        )

        # カテゴリ1が2/3のクリックなので高スコアのはず
        assert score > 50, f"Should return high score for matching clicks, got {score}"

    @pytest.mark.asyncio
    async def test_latent_factor_calculation(self, personalized_engine, sample_job, sample_user_profile):
        """潜在因子を使用したスコア計算のテスト"""
        sample_job.category = MagicMock()
        sample_job.category.occupation_cd1 = 5
        sample_job.salary = MagicMock()
        sample_job.salary.min_salary = 1200
        sample_job.features = MagicMock()
        sample_job.features.has_daily_payment = True
        sample_job.features.has_no_experience = True
        sample_job.features.has_student_welcome = True

        score = personalized_engine._calculate_latent_factor_score(
            sample_user_profile.latent_factors, sample_job
        )

        # スコアが範囲内であることを確認
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"

    @pytest.mark.asyncio
    async def test_user_item_matrix_building(self, personalized_engine, mock_db_session):
        """ユーザー・アイテム行列構築のテスト"""
        # モックデータを返すように設定
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(user_id=1, job_id=100, interaction_count=3, interaction_weight=5),
            MagicMock(user_id=1, job_id=101, interaction_count=1, interaction_weight=2),
            MagicMock(user_id=2, job_id=100, interaction_count=2, interaction_weight=1),
        ]
        mock_db_session.execute.return_value = mock_result

        await personalized_engine._build_user_item_matrix()

        # マトリックスが構築されていることを確認
        assert personalized_engine._user_item_matrix is not None
        assert len(personalized_engine._user_id_to_index) == 2  # 2ユーザー
        assert len(personalized_engine._job_id_to_index) == 2   # 2求人


class TestIntegration:
    """T022とT023の統合テスト"""

    @pytest.mark.asyncio
    async def test_combined_scoring(self, seo_engine, personalized_engine,
                                   sample_user, sample_job, sample_user_profile,
                                   semrush_keywords):
        """SEOスコアとパーソナライズスコアの統合計算"""
        # SEOスコア計算
        processed_keywords = await seo_engine.preprocess_semrush_keywords(semrush_keywords)
        seo_score, _ = await seo_engine.calculate_seo_score(sample_job, processed_keywords)

        # パーソナライズスコア計算
        personalized_score = await personalized_engine.calculate_personalized_score(
            sample_user, sample_job, sample_user_profile
        )

        # 両方のスコアが正しい範囲内であることを確認
        assert 0 <= seo_score <= 100, f"SEO score should be 0-100, got {seo_score}"
        assert 0 <= personalized_score <= 100, f"Personalized score should be 0-100, got {personalized_score}"

        # 統合スコア計算の例（重み付け）
        combined_score = seo_score * 0.3 + personalized_score * 0.7
        assert 0 <= combined_score <= 100, f"Combined score should be 0-100, got {combined_score}"


class TestCaching:
    """キャッシング機構のテスト"""

    @pytest.mark.asyncio
    async def test_keyword_caching(self, seo_engine, semrush_keywords):
        """キーワードのキャッシュが機能することを確認"""
        # 1回目の呼び出し
        processed1 = await seo_engine.preprocess_semrush_keywords(semrush_keywords)

        # 2回目の呼び出し（キャッシュから）
        processed2 = await seo_engine.preprocess_semrush_keywords()

        # 同じ結果が返ることを確認
        assert len(processed1) == len(processed2)
        assert processed1.equals(processed2)

    @pytest.mark.asyncio
    async def test_batch_seo_scoring(self, seo_engine, sample_job):
        """バッチSEOスコアリングのテスト"""
        jobs = [sample_job] * 5  # 5つの求人

        results = await seo_engine.batch_calculate_seo_scores(jobs)

        assert len(results) == 5
        for job_id, (score, keywords) in results.items():
            assert 0 <= score <= 100
            assert isinstance(keywords, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])