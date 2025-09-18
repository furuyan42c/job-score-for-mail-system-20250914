"""
スコアリングエンジン

求人とユーザーのマッチングスコアを計算する高性能エンジン
- 基本スコア計算
- 立地スコア計算
- カテゴリスコア計算
- パーソナライゼーションスコア
- 総合スコア算出
"""

import asyncio
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.matching import MatchingScore, ScoringConfiguration
from app.models.jobs import Job
from app.models.users import User, UserProfile
from app.core.config import settings
from app.services.basic_scoring import BasicScoringEngine  # T021統合
from app.services.seo_scoring import SEOScoringEngine  # T022統合
from app.services.personalized_scoring import PersonalizedScoringEngine  # T023統合
import logging

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    スコアリングエンジン

    求人とユーザーの適合度を多次元で評価し、
    10万件×1万人のスケールに対応した高速計算を実現
    """

    def __init__(self, db: AsyncSession, config: Optional[ScoringConfiguration] = None):
        self.db = db
        self.config = config or self._get_default_config()

        # T021統合: BasicScoringEngineの初期化
        self._basic_engine = BasicScoringEngine(db)
        self._use_t021_scoring = getattr(config, 'use_t021_basic_scoring', True) if config else True
        self._t021_fallback_enabled = getattr(config, 't021_fallback_enabled', True) if config else True

        # T022統合: SEOScoringEngineの初期化
        self._seo_engine = SEOScoringEngine(db)

        # T023統合: PersonalizedScoringEngineの初期化
        self._personalized_engine = PersonalizedScoringEngine(db)
        # ALSモデルの初期化
        asyncio.create_task(self._init_personalized_model())

        # キャッシュ用辞書（T021エンジンと共有）
        self._prefecture_cache = {}
        self._city_cache = {}
        self._occupation_cache = {}
        self._company_popularity_cache = {}

    async def _init_personalized_model(self):
        """パーソナライズモデルの非同期初期化"""
        try:
            await self._personalized_engine.initialize_als_model()
            await self._personalized_engine.train_model()
        except Exception as e:
            logger.warning(f"Failed to initialize personalized model: {e}")

    def _get_default_config(self) -> ScoringConfiguration:
        """デフォルトスコアリング設定"""
        return ScoringConfiguration(
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
                'high_income_threshold': 1500,
                'category_match_bonus': 10.0,
                'feature_match_bonus': 5.0
            },
            bonus_rules=[
                {'condition': 'perfect_category_match', 'bonus': 15.0},
                {'condition': 'high_income_job', 'bonus': 10.0},
                {'condition': 'daily_payment_user', 'bonus': 8.0},
                {'condition': 'student_friendly', 'bonus': 5.0}
            ],
            penalty_rules=[
                {'condition': 'recent_application', 'penalty': -20.0},
                {'condition': 'far_location', 'penalty': -15.0},
                {'condition': 'category_mismatch', 'penalty': -10.0}
            ],
            version="v1.0"
        )

    async def calculate_score(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile] = None
    ) -> MatchingScore:
        """
        求人とユーザーの総合マッチングスコア計算

        Args:
            user: ユーザー情報
            job: 求人情報
            user_profile: ユーザープロファイル（省略可）

        Returns:
            MatchingScore: 詳細なスコア情報
        """
        try:
            # 並列でスコア計算（T022, T023追加）
            tasks = [
                self._calculate_basic_score(user, job),
                self._calculate_location_score(user, job),
                self._calculate_category_score(user, job, user_profile),
                self._calculate_salary_score(user, job, user_profile),
                self._calculate_feature_score(user, job, user_profile),
                self._calculate_preference_score(user, job, user_profile),
                self._calculate_popularity_score(user, job),
                self._calculate_seo_score(job),  # T022
                self._calculate_personalized_score(user, job, user_profile)  # T023
            ]

            scores = await asyncio.gather(*tasks)

            basic_score, location_score, category_score, salary_score, \
            feature_score, preference_score, popularity_score, seo_score, \
            personalized_score = scores

            # ボーナス・ペナルティ計算
            bonus_points = await self._calculate_bonus_points(user, job, user_profile)
            penalty_points = await self._calculate_penalty_points(user, job)

            # 重み付け総合スコア計算
            weighted_scores = {
                'basic': basic_score * self.config.weights['basic_score'],
                'location': location_score * self.config.weights['location_score'],
                'category': category_score * self.config.weights['category_score'],
                'salary': salary_score * self.config.weights['salary_score'],
                'feature': feature_score * self.config.weights['feature_score'],
                'preference': preference_score * self.config.weights['preference_score'],
                'popularity': popularity_score * self.config.weights['popularity_score']
            }

            base_composite = sum(weighted_scores.values())
            total_bonus = sum(bonus_points.values())
            total_penalty = sum(penalty_points.values())

            composite_score = max(0, min(100, base_composite + total_bonus + total_penalty))

            return MatchingScore(
                basic_score=basic_score,
                location_score=location_score,
                category_score=category_score,
                salary_score=salary_score,
                feature_score=feature_score,
                preference_score=preference_score,
                popularity_score=popularity_score,
                seo_score=seo_score,  # T022
                personalized_score=personalized_score,  # T023
                composite_score=composite_score,
                score_breakdown=weighted_scores,
                bonus_points=bonus_points,
                penalty_points=penalty_points,
                matched_keywords=getattr(self, '_last_matched_keywords', None),  # T022 keywords
                als_prediction=None  # T023 ALS prediction (if available)
            )

        except Exception as e:
            logger.error(f"スコア計算エラー (user_id: {user.user_id}, job_id: {job.job_id}): {e}")
            # エラー時は低スコアを返す
            return MatchingScore(
                basic_score=0,
                location_score=0,
                category_score=0,
                salary_score=0,
                feature_score=0,
                preference_score=0,
                popularity_score=0,
                composite_score=0,
                score_breakdown={},
                bonus_points={},
                penalty_points={'error': -100}
            )

    async def _calculate_basic_score(self, user: User, job: Job) -> float:
        """
        基本スコア計算（T021統合版）

        T021仕様準拠の基礎スコア計算を使用し、
        フォールバック機構により安定性を確保
        """
        if self._use_t021_scoring:
            try:
                # T021実装を使用
                user_location = None
                if user.estimated_pref_cd:
                    user_location = {
                        'pref_code': user.estimated_pref_cd,
                        'city_code': user.estimated_city_cd
                    }

                return await self._basic_engine.calculate_basic_score(
                    job=job,
                    user_location=user_location
                )
            except Exception as e:
                logger.warning(f"T021 basic scoring failed for job {job.job_id}: {e}")

                if self._t021_fallback_enabled:
                    # レガシー実装にフォールバック
                    return await self._calculate_basic_score_legacy(user, job)
                else:
                    raise
        else:
            # レガシー実装を使用
            return await self._calculate_basic_score_legacy(user, job)

    async def _calculate_basic_score_legacy(self, user: User, job: Job) -> float:
        """レガシー基本スコア計算（フォールバック用）"""
        score = 50.0  # ベーススコア

        # 給与レベル評価
        if job.salary and job.salary.min_salary:
            if job.salary.salary_type == "hourly":
                if job.salary.min_salary >= 1500:
                    score += 20
                elif job.salary.min_salary >= 1200:
                    score += 15
                elif job.salary.min_salary >= 1000:
                    score += 10
            elif job.salary.salary_type == "daily":
                if job.salary.min_salary >= 12000:
                    score += 20
                elif job.salary.min_salary >= 10000:
                    score += 15
                elif job.salary.min_salary >= 8000:
                    score += 10

        # 特徴ボーナス
        if job.features:
            feature_bonus = 0
            if job.features.has_daily_payment:
                feature_bonus += 8
            if job.features.has_no_experience:
                feature_bonus += 6
            if job.features.has_student_welcome:
                feature_bonus += 5
            if job.features.has_transportation:
                feature_bonus += 4

            score += min(feature_bonus, 15)  # 最大15点

        # 求人の新しさ
        if job.posting_date:
            days_old = (datetime.now() - job.posting_date).days
            if days_old <= 3:
                score += 5
            elif days_old <= 7:
                score += 3
            elif days_old <= 14:
                score += 1

        return min(100.0, max(0.0, score))

    async def _calculate_location_score(self, user: User, job: Job) -> float:
        """立地スコア計算（通勤の便利さ）"""
        # ユーザーの居住地情報が不明な場合
        if not user.estimated_pref_cd or not job.location.prefecture_code:
            return 30.0  # 中間値

        # 同じ都道府県なら高スコア
        if user.estimated_pref_cd == job.location.prefecture_code:
            score = 80.0

            # 同じ市区町村ならさらに高スコア
            if (user.estimated_city_cd and
                job.location.city_code and
                user.estimated_city_cd == job.location.city_code):
                score = 95.0
        else:
            # 隣接県判定（簡易版）
            adjacent_prefs = await self._get_adjacent_prefectures(user.estimated_pref_cd)
            if job.location.prefecture_code in adjacent_prefs:
                score = 60.0
            else:
                score = 20.0

        # 駅情報がある場合のボーナス
        if job.location.station_name:
            score += 5

        return min(100.0, max(0.0, score))

    async def _calculate_category_score(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile]
    ) -> float:
        """カテゴリスコア計算（職種の適合度）"""
        if not user_profile or not user_profile.preferences.preferred_categories:
            return 40.0  # デフォルト値

        job_category = job.category.occupation_cd1  # 大分類
        if not job_category:
            return 30.0

        score = 0.0

        # 希望カテゴリとの一致度
        if job_category in user_profile.preferences.preferred_categories:
            score = 90.0

            # 中分類も一致する場合のボーナス
            job_minor_category = job.category.occupation_cd2
            if job_minor_category:
                # ここでは簡易実装（実際はより詳細な判定が必要）
                score = 95.0
        else:
            # 関連カテゴリの判定
            related_score = await self._get_category_similarity(
                job_category,
                user_profile.preferences.preferred_categories
            )
            score = related_score

        # カテゴリ関心度による重み付け
        if user_profile.category_interests:
            interest_weight = user_profile.category_interests.get(str(job_category), 0.5)
            score *= (0.5 + interest_weight * 0.5)  # 0.5〜1.0の範囲で重み付け

        return min(100.0, max(0.0, score))

    async def _calculate_salary_score(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile]
    ) -> float:
        """給与スコア計算（給与の魅力度）"""
        if not job.salary or not job.salary.min_salary:
            return 30.0

        # ユーザーの希望給与
        if user_profile and user_profile.behavior_stats.avg_salary_preference:
            preferred_salary = user_profile.behavior_stats.avg_salary_preference
        elif user.preferences and user.preferences.preferred_salary_min:
            preferred_salary = user.preferences.preferred_salary_min
        else:
            # デフォルト希望給与（職種別・年齢別の統計値を使用）
            preferred_salary = await self._get_default_salary_expectation(user)

        job_salary = job.salary.min_salary

        # 給与比較スコア計算
        if job_salary >= preferred_salary * 1.3:
            score = 100.0
        elif job_salary >= preferred_salary * 1.1:
            score = 85.0
        elif job_salary >= preferred_salary:
            score = 70.0
        elif job_salary >= preferred_salary * 0.9:
            score = 55.0
        elif job_salary >= preferred_salary * 0.8:
            score = 40.0
        else:
            score = 20.0

        # 給与タイプボーナス（時給の場合は少し低めに評価）
        if job.salary.salary_type == "daily":
            score += 5
        elif job.salary.salary_type == "monthly":
            score += 3

        return min(100.0, max(0.0, score))

    async def _calculate_feature_score(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile]
    ) -> float:
        """特徴スコア計算（求人特徴の魅力度）"""
        if not job.features:
            return 30.0

        score = 40.0  # ベーススコア

        # ユーザーの嗜好スコアを使用
        if user_profile and user_profile.preference_scores:
            feature_preferences = user_profile.preference_scores

            # 各特徴とユーザー嗜好の照合
            if job.features.has_daily_payment and feature_preferences.get('daily_payment', 0) > 0.6:
                score += 15
            if job.features.has_weekly_payment and feature_preferences.get('weekly_payment', 0) > 0.6:
                score += 10
            if job.features.has_no_experience and feature_preferences.get('no_experience', 0) > 0.6:
                score += 12
            if job.features.has_student_welcome and feature_preferences.get('student_welcome', 0) > 0.6:
                score += 8
            if job.features.has_remote_work and feature_preferences.get('remote_work', 0) > 0.6:
                score += 10
            if job.features.has_transportation and feature_preferences.get('transportation', 0) > 0.6:
                score += 6
        else:
            # デフォルト評価（一般的に魅力的な特徴）
            if job.features.has_daily_payment:
                score += 12
            if job.features.has_no_experience:
                score += 10
            if job.features.has_student_welcome:
                score += 8
            if job.features.has_transportation:
                score += 6
            if job.features.has_remote_work:
                score += 8

        return min(100.0, max(0.0, score))

    async def _calculate_preference_score(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile]
    ) -> float:
        """嗜好スコア計算（個人の好みとの適合度）"""
        if not user_profile:
            return 40.0

        score = 50.0

        # 希望勤務スタイルとの照合
        if user_profile.preferences.preferred_work_styles:
            style_match = 0
            for style in user_profile.preferences.preferred_work_styles:
                if style == "flexible" and job.work_conditions.shift_flexibility:
                    style_match += 15
                elif style == "part_time" and job.work_conditions.employment_type_cd == 1:
                    style_match += 10
                elif style == "short_term" and "短期" in (job.work_conditions.work_days or ""):
                    style_match += 12

            score += min(style_match, 25)

        # 過去の応募傾向との類似度
        if user_profile.latent_factors and len(user_profile.latent_factors) >= 10:
            # 協調フィルタリングベースのスコア
            # （実装簡略化：ランダムな例として）
            similarity_score = min(30, sum(user_profile.latent_factors[:10]) / 10 * 30)
            score += similarity_score

        # 行動パターンによる調整
        if user_profile.behavior_stats:
            # アクティブユーザーほど高スコア
            if user_profile.behavior_stats.application_count > 10:
                score += 5
            elif user_profile.behavior_stats.application_count > 5:
                score += 3

        return min(100.0, max(0.0, score))

    async def _calculate_popularity_score(self, user: User, job: Job) -> float:
        """人気度スコア計算（求人・企業の人気度）"""
        # 企業人気度の取得
        company_popularity = await self._get_company_popularity(job.endcl_cd)

        if not company_popularity:
            return 30.0

        # 人気度スコアの正規化（0-100）
        # 応募率が高いほど高スコア
        application_rate = company_popularity.get('application_rate', 0)
        if application_rate >= 0.1:  # 10%以上
            score = 90.0
        elif application_rate >= 0.05:  # 5%以上
            score = 70.0
        elif application_rate >= 0.02:  # 2%以上
            score = 50.0
        else:
            score = 30.0

        # 最近の応募数による調整
        recent_applications = company_popularity.get('applications_7d', 0)
        if recent_applications > 100:
            score += 10
        elif recent_applications > 50:
            score += 5

        return min(100.0, max(0.0, score))

    async def _calculate_seo_score(self, job: Job) -> float:
        """
        T022: SEOスコア計算（semrush_keywordsとのマッチング）

        Args:
            job: 求人情報

        Returns:
            SEOスコア (0-100)
        """
        try:
            seo_score, matched_keywords = await self._seo_engine.calculate_seo_score(job)

            # マッチしたキーワードを保存（MatchingScore用）
            self._last_matched_keywords = matched_keywords

            # マッチしたキーワードをDBに保存（非同期で実行）
            if matched_keywords and hasattr(job, 'job_id'):
                asyncio.create_task(
                    self._seo_engine.save_keyword_scoring(job.job_id, matched_keywords)
                )

            return seo_score
        except Exception as e:
            logger.warning(f"SEO scoring failed for job {job.job_id}: {e}")
            self._last_matched_keywords = None
            return 30.0  # デフォルト値

    async def _calculate_personalized_score(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile]
    ) -> float:
        """
        T023: パーソナライズスコア計算（implicit ALSによる協調フィルタリング）

        Args:
            user: ユーザー情報
            job: 求人情報
            user_profile: ユーザープロファイル

        Returns:
            パーソナライズスコア (0-100)
        """
        try:
            return await self._personalized_engine.calculate_personalized_score(
                user, job, user_profile
            )
        except Exception as e:
            logger.warning(f"Personalized scoring failed for user {user.user_id}, job {job.job_id}: {e}")
            return 40.0  # デフォルト値

    async def _calculate_bonus_points(
        self,
        user: User,
        job: Job,
        user_profile: Optional[UserProfile]
    ) -> Dict[str, float]:
        """ボーナスポイント計算"""
        bonus = {}

        # 完全カテゴリマッチ
        if (user_profile and
            user_profile.preferences.preferred_categories and
            job.category.occupation_cd1 in user_profile.preferences.preferred_categories and
            job.category.occupation_cd2):
            bonus['perfect_category_match'] = 15.0

        # 高収入求人
        if (job.salary and job.salary.min_salary and
            ((job.salary.salary_type == "hourly" and job.salary.min_salary >= 1500) or
             (job.salary.salary_type == "daily" and job.salary.min_salary >= 12000))):
            bonus['high_income_job'] = 10.0

        # 日払い希望ユーザー
        if (user_profile and
            user_profile.preference_scores.get('daily_payment', 0) > 0.7 and
            job.features and job.features.has_daily_payment):
            bonus['daily_payment_user'] = 8.0

        # 学生歓迎
        if (user.age_group in ['10代', '20代前半'] and
            job.features and job.features.has_student_welcome):
            bonus['student_friendly'] = 5.0

        return bonus

    async def _calculate_penalty_points(self, user: User, job: Job) -> Dict[str, float]:
        """ペナルティポイント計算"""
        penalty = {}

        # 最近の応募企業
        recent_application = await self._check_recent_application(user.user_id, job.endcl_cd)
        if recent_application:
            penalty['recent_application'] = -20.0

        # 距離が遠い場合（座標情報がある場合）
        if (user.estimated_pref_cd and job.location.prefecture_code and
            user.estimated_pref_cd != job.location.prefecture_code):
            # 隣接県でもない場合
            adjacent_prefs = await self._get_adjacent_prefectures(user.estimated_pref_cd)
            if job.location.prefecture_code not in adjacent_prefs:
                penalty['far_location'] = -15.0

        return penalty

    async def batch_calculate_scores(
        self,
        user_job_pairs: List[Tuple[User, Job, Optional[UserProfile]]]
    ) -> List[MatchingScore]:
        """
        バッチスコア計算

        大量のユーザー・求人ペアを効率的に処理
        """
        batch_size = settings.SCORING_BATCH_SIZE
        results = []

        for i in range(0, len(user_job_pairs), batch_size):
            batch = user_job_pairs[i:i + batch_size]

            # 並列処理でスコア計算
            tasks = [
                self.calculate_score(user, job, profile)
                for user, job, profile in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # エラーハンドリング
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"バッチスコア計算エラー (バッチ {i//batch_size}, 項目 {j}): {result}")
                    # エラー時のデフォルトスコア
                    user, job, _ = batch[j]
                    result = MatchingScore(
                        basic_score=0, location_score=0, category_score=0,
                        salary_score=0, feature_score=0, preference_score=0,
                        popularity_score=0, composite_score=0,
                        score_breakdown={}, bonus_points={},
                        penalty_points={'error': -100}
                    )

                results.append(result)

        return results

    # ヘルパーメソッド

    async def _get_adjacent_prefectures(self, pref_code: str) -> List[str]:
        """隣接都道府県の取得"""
        # キャッシュチェック
        if pref_code in self._prefecture_cache:
            return self._prefecture_cache[pref_code]

        try:
            result = await self.db.execute(text("""
                SELECT adjacent_prefectures
                FROM prefecture_adjacency
                WHERE pref_code = :pref_code
            """), {"pref_code": pref_code})

            row = result.fetchone()
            adjacent = row.adjacent_prefectures if row else []

            self._prefecture_cache[pref_code] = adjacent
            return adjacent

        except Exception as e:
            logger.warning(f"隣接都道府県取得エラー: {e}")
            return []

    async def _get_category_similarity(
        self,
        job_category: int,
        user_categories: List[int]
    ) -> float:
        """カテゴリ類似度計算"""
        try:
            # 職種階層による類似度計算
            result = await self.db.execute(text("""
                SELECT
                    CASE
                        WHEN :job_category = ANY(:user_categories::integer[]) THEN 90
                        WHEN EXISTS (
                            SELECT 1 FROM occupation_master o1, occupation_master o2
                            WHERE o1.code = :job_category
                            AND o2.code = ANY(:user_categories::integer[])
                            AND o1.major_category_code = o2.major_category_code
                        ) THEN 60
                        ELSE 20
                    END as similarity_score
            """), {
                "job_category": job_category,
                "user_categories": user_categories
            })

            row = result.fetchone()
            return float(row.similarity_score) if row else 20.0

        except Exception as e:
            logger.warning(f"カテゴリ類似度計算エラー: {e}")
            return 20.0

    async def _get_default_salary_expectation(self, user: User) -> int:
        """デフォルト希望給与の推定"""
        base_salary = 1000  # 基準時給

        # 年齢による調整
        if user.age_group:
            if user.age_group in ['10代']:
                base_salary = 900
            elif user.age_group in ['20代前半']:
                base_salary = 1000
            elif user.age_group in ['20代後半']:
                base_salary = 1200
            elif user.age_group in ['30代前半', '30代後半']:
                base_salary = 1400
            else:
                base_salary = 1300

        return base_salary

    async def _get_company_popularity(self, endcl_cd: str) -> Optional[Dict[str, Any]]:
        """企業人気度の取得"""
        if endcl_cd in self._company_popularity_cache:
            return self._company_popularity_cache[endcl_cd]

        try:
            result = await self.db.execute(text("""
                SELECT
                    application_rate,
                    applications_7d,
                    popularity_score
                FROM company_popularity
                WHERE endcl_cd = :endcl_cd
            """), {"endcl_cd": endcl_cd})

            row = result.fetchone()
            if row:
                popularity = {
                    'application_rate': float(row.application_rate),
                    'applications_7d': int(row.applications_7d),
                    'popularity_score': float(row.popularity_score)
                }
                self._company_popularity_cache[endcl_cd] = popularity
                return popularity

            return None

        except Exception as e:
            logger.warning(f"企業人気度取得エラー: {e}")
            return None

    async def _check_recent_application(self, user_id: int, endcl_cd: str) -> bool:
        """最近の応募チェック"""
        try:
            result = await self.db.execute(text("""
                SELECT 1
                FROM user_actions
                WHERE user_id = :user_id
                AND endcl_cd = :endcl_cd
                AND action_type IN ('apply', 'application')
                AND action_timestamp > CURRENT_DATE - INTERVAL '14 days'
                LIMIT 1
            """), {"user_id": user_id, "endcl_cd": endcl_cd})

            return result.fetchone() is not None

        except Exception as e:
            logger.warning(f"最近の応募チェックエラー: {e}")
            return False