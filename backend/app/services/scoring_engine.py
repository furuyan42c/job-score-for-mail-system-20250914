"""
スコアリングエンジン

求人とユーザーのマッチングスコアを計算する高性能エンジン
各スコア算出関数を独立して実装し、総合的な評価を行う
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from functools import lru_cache
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload

from app.models.jobs import Job, JobSalary, JobFeatures, JobCategory
from app.models.users import User, UserProfile, UserPreferences
from app.models.matching import MatchingScore
from app.models.common import SalaryType
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    求人スコアリングエンジン

    基礎スコア、SEOスコア、パーソナルスコアを統合して
    総合的なマッチングスコアを算出する
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        # 計算効率化のためのキャッシュ
        self._prefecture_distance_cache = {}
        self._occupation_similarity_cache = {}
        self._user_history_cache = {}

    async def calculate_base_score(self, job: Job) -> float:
        """
        基礎スコア計算 (0-100点)

        Args:
            job: 求人情報

        Returns:
            基礎スコア (0-100)
        """
        try:
            score = 0.0

            # fee（応募促進費用）重視: 最大50点
            if job.salary and job.salary.fee:
                fee_score = min((job.salary.fee / 5000) * 50, 50)
                score += fee_score
                logger.debug(f"Fee score: {fee_score} (fee: {job.salary.fee})")

            # 給与の魅力度: 最大30点
            salary_score = await self._calculate_salary_attractiveness(job)
            score += salary_score
            logger.debug(f"Salary attractiveness: {salary_score}")

            # アクセススコア: 最大20点
            access_score = await self._calculate_access_score(job)
            score += access_score
            logger.debug(f"Access score: {access_score}")

            # 範囲チェック
            final_score = max(0.0, min(100.0, score))
            logger.info(f"Base score calculated: {final_score} for job {job.job_id}")

            return final_score

        except Exception as e:
            logger.error(f"Error calculating base score for job {job.job_id}: {e}")
            return 0.0

    async def _calculate_salary_attractiveness(self, job: Job) -> float:
        """給与の魅力度計算"""
        if not job.salary or not job.salary.min_salary:
            return 5.0  # デフォルト最低点

        min_salary = job.salary.min_salary
        salary_type = job.salary.salary_type

        if salary_type == SalaryType.HOURLY:
            if min_salary >= 1500:
                return 30.0
            elif min_salary >= 1200:
                return 20.0
            elif min_salary >= 1000:
                return 10.0
            else:
                return 5.0
        elif salary_type == SalaryType.DAILY:
            # 時給換算での評価
            hourly_equivalent = min_salary / 8  # 8時間勤務想定
            if hourly_equivalent >= 1500:
                return 30.0
            elif hourly_equivalent >= 1200:
                return 20.0
            elif hourly_equivalent >= 1000:
                return 10.0
            else:
                return 5.0
        elif salary_type == SalaryType.MONTHLY:
            # 月給を時給換算（160時間/月想定）
            hourly_equivalent = min_salary / 160
            if hourly_equivalent >= 1500:
                return 30.0
            elif hourly_equivalent >= 1200:
                return 20.0
            elif hourly_equivalent >= 1000:
                return 10.0
            else:
                return 5.0

        return 5.0

    async def _calculate_access_score(self, job: Job) -> float:
        """アクセススコア計算"""
        score = 5.0  # ベーススコア

        # 駅情報がある場合のボーナス
        if job.location and job.location.station_name:
            score += 15.0  # 駅近想定での高評価
            logger.debug(f"Station bonus applied: {job.location.station_name}")

        # 住所詳細がある場合の追加ポイント
        if job.location and job.location.address:
            score += 5.0

        return min(20.0, score)

    async def calculate_seo_score(self, job: Job, user: User) -> float:
        """
        SEOスコア計算 (0-100点)

        Args:
            job: 求人情報
            user: ユーザー情報

        Returns:
            SEOスコア (0-100)
        """
        try:
            # マッチング要素を並列計算
            location_task = self._calculate_location_match(job, user)
            category_task = self._calculate_category_match(job, user)
            condition_task = self._calculate_condition_match(job, user)

            location_match, category_match, condition_match = await asyncio.gather(
                location_task, category_task, condition_task
            )

            # 平均スコア計算
            seo_score = (location_match + category_match + condition_match) / 3

            logger.info(f"SEO score: {seo_score:.2f} (location: {location_match}, "
                       f"category: {category_match}, condition: {condition_match})")

            return max(0.0, min(100.0, seo_score))

        except Exception as e:
            logger.error(f"Error calculating SEO score for job {job.job_id}, user {user.user_id}: {e}")
            return 20.0  # エラー時のデフォルト値

    async def _calculate_location_match(self, job: Job, user: User) -> float:
        """地域マッチング計算"""
        if not job.location or not job.location.prefecture_code:
            return 20.0

        # ユーザーの居住地情報が不明な場合
        user_pref = getattr(user, 'pref_cd', None) or getattr(user, 'estimated_pref_cd', None)
        if not user_pref:
            return 20.0

        job_pref = job.location.prefecture_code

        # 同じ都道府県
        if user_pref == job_pref:
            # 同じ市区町村ならさらに高スコア
            user_city = getattr(user, 'city_cd', None) or getattr(user, 'estimated_city_cd', None)
            if (user_city and job.location.city_code and
                user_city == job.location.city_code):
                return 100.0
            return 100.0

        # 隣接都道府県チェック
        if await self._is_adjacent_prefecture(user_pref, job_pref):
            return 60.0

        return 20.0

    async def _calculate_category_match(self, job: Job, user: User) -> float:
        """カテゴリマッチング計算"""
        if not job.category or not job.category.occupation_cd1:
            return 20.0

        # ユーザーの希望カテゴリ取得
        user_categories = getattr(user, 'preferred_categories', [])
        if not user_categories:
            return 20.0

        job_category = job.category.occupation_cd1

        # 完全一致
        if job_category in user_categories:
            return 100.0

        # 大分類一致チェック
        if await self._check_major_category_match(job_category, user_categories):
            return 60.0

        return 20.0

    async def _calculate_condition_match(self, job: Job, user: User) -> float:
        """条件マッチング計算"""
        total_conditions = 0
        matched_conditions = 0

        # 給与条件チェック
        if hasattr(user, 'preferred_salary_min') and user.preferred_salary_min:
            total_conditions += 1
            if job.salary and job.salary.min_salary:
                if job.salary.min_salary >= user.preferred_salary_min:
                    matched_conditions += 1

        # 勤務スタイルチェック
        if hasattr(user, 'preferred_work_style') and user.preferred_work_style:
            total_conditions += 1
            # 簡易的なマッチング（実際はより詳細な実装が必要）
            matched_conditions += 0.5  # 部分マッチとして扱う

        # 特徴条件チェック
        if job.features:
            total_conditions += 1
            # 一般的に魅力的な特徴がある場合
            if (job.features.has_daily_payment or
                job.features.has_no_experience or
                job.features.has_student_welcome):
                matched_conditions += 1

        if total_conditions == 0:
            return 50.0  # デフォルト値

        match_ratio = matched_conditions / total_conditions
        return match_ratio * 100

    async def calculate_personal_score(self, job: Job, user_profile: UserProfile) -> float:
        """
        パーソナルスコア計算 (0-100点)

        Args:
            job: 求人情報
            user_profile: ユーザープロファイル

        Returns:
            パーソナルスコア (0-100)
        """
        try:
            if not user_profile:
                return 40.0  # デフォルト値

            # 各コンポーネントスコアを並列計算
            history_task = self._analyze_application_history(job, user_profile)
            click_task = self._analyze_click_patterns(job, user_profile)
            collaborative_task = self._collaborative_filtering(job, user_profile)

            history_score, click_score, collaborative_score = await asyncio.gather(
                history_task, click_task, collaborative_task
            )

            # 重み付け平均計算
            weights = {'history': 0.4, 'click': 0.3, 'collaborative': 0.3}
            personal_score = (
                history_score * weights['history'] +
                click_score * weights['click'] +
                collaborative_score * weights['collaborative']
            )

            logger.info(f"Personal score: {personal_score:.2f} "
                       f"(history: {history_score}, click: {click_score}, "
                       f"collaborative: {collaborative_score})")

            return max(0.0, min(100.0, personal_score))

        except Exception as e:
            logger.error(f"Error calculating personal score for job {job.job_id}: {e}")
            return 40.0

    async def _analyze_application_history(self, job: Job, user_profile: UserProfile) -> float:
        """応募履歴分析"""
        try:
            # ユーザーの過去の応募パターンを分析
            result = await self.db.execute(text("""
                SELECT
                    j.occupation_cd1,
                    j.min_salary,
                    j.prefecture_code,
                    COUNT(*) as application_count
                FROM user_actions ua
                JOIN jobs j ON ua.job_id = j.job_id
                WHERE ua.user_id = :user_id
                AND ua.action_type = 'application'
                AND ua.action_timestamp > CURRENT_DATE - INTERVAL '90 days'
                GROUP BY j.occupation_cd1, j.min_salary, j.prefecture_code
                ORDER BY application_count DESC
                LIMIT 10
            """), {"user_id": user_profile.user_id})

            history_patterns = result.fetchall()

            if not history_patterns:
                return 50.0  # 履歴なしの場合

            similarity_score = 0.0

            # 職種類似度
            for pattern in history_patterns:
                if (job.category and job.category.occupation_cd1 == pattern.occupation_cd1):
                    similarity_score += 30.0
                    break

            # 給与レベル類似度
            if job.salary and job.salary.min_salary:
                avg_salary = np.mean([p.min_salary for p in history_patterns if p.min_salary])
                if abs(job.salary.min_salary - avg_salary) / avg_salary < 0.2:  # 20%以内
                    similarity_score += 25.0

            # 地域類似度
            for pattern in history_patterns:
                if (job.location and job.location.prefecture_code == pattern.prefecture_code):
                    similarity_score += 20.0
                    break

            # ベーススコア
            similarity_score += 25.0

            return min(100.0, similarity_score)

        except Exception as e:
            logger.warning(f"Error analyzing application history: {e}")
            return 50.0

    async def _analyze_click_patterns(self, job: Job, user_profile: UserProfile) -> float:
        """クリックパターン分析"""
        try:
            # ユーザーのクリック傾向を分析
            result = await self.db.execute(text("""
                SELECT
                    j.occupation_cd1,
                    j.has_daily_payment,
                    j.has_no_experience,
                    j.has_student_welcome,
                    COUNT(*) as click_count
                FROM user_actions ua
                JOIN jobs j ON ua.job_id = j.job_id
                WHERE ua.user_id = :user_id
                AND ua.action_type = 'click'
                AND ua.action_timestamp > CURRENT_DATE - INTERVAL '30 days'
                GROUP BY j.occupation_cd1, j.has_daily_payment, j.has_no_experience, j.has_student_welcome
                ORDER BY click_count DESC
                LIMIT 20
            """), {"user_id": user_profile.user_id})

            click_patterns = result.fetchall()

            if not click_patterns:
                return 40.0

            pattern_score = 40.0  # ベース

            # 職種クリック傾向
            for pattern in click_patterns:
                if (job.category and job.category.occupation_cd1 == pattern.occupation_cd1):
                    pattern_score += 20.0
                    break

            # 特徴クリック傾向
            if job.features:
                if job.features.has_daily_payment:
                    daily_payment_clicks = sum(1 for p in click_patterns if p.has_daily_payment)
                    if daily_payment_clicks > 0:
                        pattern_score += 15.0

                if job.features.has_no_experience:
                    no_exp_clicks = sum(1 for p in click_patterns if p.has_no_experience)
                    if no_exp_clicks > 0:
                        pattern_score += 10.0

                if job.features.has_student_welcome:
                    student_clicks = sum(1 for p in click_patterns if p.has_student_welcome)
                    if student_clicks > 0:
                        pattern_score += 10.0

            return min(100.0, pattern_score)

        except Exception as e:
            logger.warning(f"Error analyzing click patterns: {e}")
            return 40.0

    async def _collaborative_filtering(self, job: Job, user_profile: UserProfile) -> float:
        """協調フィルタリング"""
        try:
            # 類似ユーザーの行動パターン分析
            if not user_profile.latent_factors or len(user_profile.latent_factors) < 10:
                return 45.0  # デフォルト値

            # 簡易的な協調フィルタリング実装
            # 実際にはより高度なアルゴリズムを使用

            user_vector = np.array(user_profile.latent_factors[:10])

            # 求人の特徴ベクトル生成（簡易版）
            job_features = []
            job_features.append(float(job.category.occupation_cd1) if job.category and job.category.occupation_cd1 else 0.0)
            job_features.append(float(job.salary.min_salary) if job.salary and job.salary.min_salary else 1000.0)
            job_features.append(1.0 if job.features and job.features.has_daily_payment else 0.0)
            job_features.append(1.0 if job.features and job.features.has_no_experience else 0.0)
            job_features.extend([0.0] * (10 - len(job_features)))  # パディング

            job_vector = np.array(job_features[:10])

            # コサイン類似度計算
            similarity = np.dot(user_vector, job_vector) / (
                np.linalg.norm(user_vector) * np.linalg.norm(job_vector) + 1e-10
            )

            # -1から1の範囲を0から100にスケール
            collaborative_score = (similarity + 1) * 50

            return max(0.0, min(100.0, collaborative_score))

        except Exception as e:
            logger.warning(f"Error in collaborative filtering: {e}")
            return 45.0

    async def calculate_total_score(
        self,
        job: Job,
        user: User,
        user_profile: Optional[UserProfile] = None
    ) -> float:
        """
        総合スコア計算

        Args:
            job: 求人情報
            user: ユーザー情報
            user_profile: ユーザープロファイル

        Returns:
            総合スコア (0-100)
        """
        try:
            # 各スコアを並列計算
            base_task = self.calculate_base_score(job)
            seo_task = self.calculate_seo_score(job, user)

            if user_profile:
                personal_task = self.calculate_personal_score(job, user_profile)
                base_score, seo_score, personal_score = await asyncio.gather(
                    base_task, seo_task, personal_task
                )
            else:
                base_score, seo_score = await asyncio.gather(base_task, seo_task)
                personal_score = 40.0  # デフォルト値

            # 重み設定
            weights = {'base': 0.4, 'seo': 0.3, 'personal': 0.3}

            # 重み付け総合スコア計算
            total_score = (
                base_score * weights['base'] +
                seo_score * weights['seo'] +
                personal_score * weights['personal']
            )

            logger.info(f"Total score calculated: {total_score:.2f} for job {job.job_id}, "
                       f"user {user.user_id} (base: {base_score:.2f}, seo: {seo_score:.2f}, "
                       f"personal: {personal_score:.2f})")

            return max(0.0, min(100.0, total_score))

        except Exception as e:
            logger.error(f"Error calculating total score for job {job.job_id}, "
                        f"user {user.user_id}: {e}")
            return 0.0

    # ヘルパーメソッド

    @lru_cache(maxsize=1000)
    async def _is_adjacent_prefecture(self, pref1: str, pref2: str) -> bool:
        """隣接都道府県判定（キャッシュ付き）"""
        cache_key = f"{pref1}-{pref2}"
        if cache_key in self._prefecture_distance_cache:
            return self._prefecture_distance_cache[cache_key]

        try:
            result = await self.db.execute(text("""
                SELECT 1 FROM prefecture_adjacency
                WHERE pref_code = :pref1 AND :pref2 = ANY(adjacent_prefectures)
                UNION
                SELECT 1 FROM prefecture_adjacency
                WHERE pref_code = :pref2 AND :pref1 = ANY(adjacent_prefectures)
                LIMIT 1
            """), {"pref1": pref1, "pref2": pref2})

            is_adjacent = result.fetchone() is not None
            self._prefecture_distance_cache[cache_key] = is_adjacent
            return is_adjacent

        except Exception as e:
            logger.warning(f"Error checking prefecture adjacency: {e}")
            return False

    async def _check_major_category_match(self, job_category: int, user_categories: List[int]) -> bool:
        """大分類マッチング判定"""
        try:
            result = await self.db.execute(text("""
                SELECT 1 FROM occupation_master o1, occupation_master o2
                WHERE o1.code = :job_category
                AND o2.code = ANY(:user_categories::integer[])
                AND o1.major_category_code = o2.major_category_code
                LIMIT 1
            """), {"job_category": job_category, "user_categories": user_categories})

            return result.fetchone() is not None

        except Exception as e:
            logger.warning(f"Error checking major category match: {e}")
            return False

    async def batch_calculate_scores(
        self,
        job_user_pairs: List[Tuple[Job, User, Optional[UserProfile]]]
    ) -> List[float]:
        """
        バッチスコア計算

        Args:
            job_user_pairs: (求人, ユーザー, プロファイル)のタプルリスト

        Returns:
            総合スコアのリスト
        """
        try:
            batch_size = getattr(settings, 'SCORING_BATCH_SIZE', 100)
            all_scores = []

            for i in range(0, len(job_user_pairs), batch_size):
                batch = job_user_pairs[i:i + batch_size]

                # バッチ内で並列処理
                tasks = [
                    self.calculate_total_score(job, user, profile)
                    for job, user, profile in batch
                ]

                batch_scores = await asyncio.gather(*tasks, return_exceptions=True)

                # エラーハンドリング
                processed_scores = []
                for j, score in enumerate(batch_scores):
                    if isinstance(score, Exception):
                        logger.error(f"Batch scoring error (batch {i//batch_size}, item {j}): {score}")
                        processed_scores.append(0.0)  # エラー時のデフォルトスコア
                    else:
                        processed_scores.append(score)

                all_scores.extend(processed_scores)

            logger.info(f"Batch scoring completed: {len(all_scores)} scores calculated")
            return all_scores

        except Exception as e:
            logger.error(f"Error in batch scoring: {e}")
            return [0.0] * len(job_user_pairs)  # エラー時は全て0スコア

    async def get_score_explanation(
        self,
        job: Job,
        user: User,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """
        スコア説明の生成

        Args:
            job: 求人情報
            user: ユーザー情報
            user_profile: ユーザープロファイル

        Returns:
            スコア説明の辞書
        """
        try:
            # 各スコア計算
            base_score = await self.calculate_base_score(job)
            seo_score = await self.calculate_seo_score(job, user)
            personal_score = await self.calculate_personal_score(job, user_profile) if user_profile else 40.0
            total_score = await self.calculate_total_score(job, user, user_profile)

            explanation = {
                "total_score": round(total_score, 2),
                "component_scores": {
                    "base_score": round(base_score, 2),
                    "seo_score": round(seo_score, 2),
                    "personal_score": round(personal_score, 2)
                },
                "score_factors": {
                    "fee_boost": job.salary.fee if job.salary and job.salary.fee else 0,
                    "salary_attractiveness": await self._calculate_salary_attractiveness(job),
                    "location_match": await self._calculate_location_match(job, user),
                    "category_match": await self._calculate_category_match(job, user)
                },
                "recommendations": []
            }

            # 改善提案
            if total_score < 70:
                if base_score < 50:
                    explanation["recommendations"].append("より魅力的な給与条件の求人を検討してください")
                if seo_score < 50:
                    explanation["recommendations"].append("希望条件を見直すことでより良いマッチングが期待できます")
                if personal_score < 50 and user_profile:
                    explanation["recommendations"].append("アクティビティを増やすことでパーソナライゼーションが向上します")

            return explanation

        except Exception as e:
            logger.error(f"Error generating score explanation: {e}")
            return {"error": "スコア説明の生成に失敗しました"}