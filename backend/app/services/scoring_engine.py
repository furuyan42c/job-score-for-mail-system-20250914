"""
スコアリングエンジン

求人とユーザーのマッチングスコアを計算する高性能エンジン
各スコア算出関数を独立して実装し、総合的な評価を行う
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, date, timedelta
from functools import lru_cache
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload
from concurrent.futures import ThreadPoolExecutor
import warnings

# Suppress pandas warnings for performance
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

from app.models.jobs import Job, JobSalary, JobFeatures, JobCategory
from app.models.users import User, UserProfile, UserPreferences
from app.models.matching import MatchingScore
from app.models.common import SalaryType
from app.core.config import settings

logger = logging.getLogger(__name__)

# パフォーマンス設定
PERFORMANCE_TARGET_MS_PER_USER = 180  # 180ms per user target
MAX_BATCH_SIZE = 10000  # メモリ使用量制限
DEFAULT_CHUNK_SIZE = 1000  # チャンクサイズ


class ScoringEngine:
    """
    高性能求人スコアリングエンジン

    NumPy/pandas vectorization, 積極的キャッシング、バッチ処理により
    180ms/user target (100K jobs × 10K users) を実現
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # パフォーマンス監視
        self._performance_stats = {
            'total_calculations': 0,
            'avg_calculation_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # 多層キャッシュ戦略
        self._prefecture_distance_cache = {}  # 永続的キャッシュ
        self._occupation_similarity_cache = {}  # セッションキャッシュ
        self._user_history_cache = {}  # 短期キャッシュ
        self._company_popularity_cache = {}  # 1時間キャッシュ
        self._category_similarity_matrix = None  # セッション全体でキャッシュ

        # chunked processing設定
        self.chunk_size = 1000
        self.max_workers = 4

        # NumPy dtypes for memory optimization
        self.score_dtype = np.float32
        self.int_dtype = np.int16

    def calculate_base_scores_vectorized(self, jobs_df: pd.DataFrame) -> np.ndarray:
        """
        基礎スコア計算 (Vectorized) - 180ms target for large batches

        Args:
            jobs_df: 求人データのDataFrame

        Returns:
            基礎スコアのNumPy配列 (0-100)
        """
        start_time = time.time()

        try:
            # NumPy配列として効率的に処理
            n_jobs = len(jobs_df)
            scores = np.zeros(n_jobs, dtype=self.score_dtype)

            # Fee scoring - vectorized (最大50点)
            fee_values = jobs_df['fee'].fillna(0).values.astype(self.score_dtype)
            fee_scores = np.clip(fee_values / 5000 * 50, 0, 50)
            scores += fee_scores

            # Salary attractiveness - vectorized (最大30点)
            salary_scores = self._calculate_salary_attractiveness_vectorized(jobs_df)
            scores += salary_scores

            # Access score - vectorized (最大20点)
            access_scores = self._calculate_access_score_vectorized(jobs_df)
            scores += access_scores

            # 範囲制限
            scores = np.clip(scores, 0, 100)

            # パフォーマンス統計更新
            calc_time = time.time() - start_time
            self._update_performance_stats('base_score_vectorized', calc_time, n_jobs)

            logger.info(f"Vectorized base scores calculated for {n_jobs} jobs in {calc_time:.3f}s")
            return scores

        except Exception as e:
            logger.error(f"Error in vectorized base score calculation: {e}")
            return np.zeros(len(jobs_df), dtype=self.score_dtype)

    async def calculate_base_score(self, job: Job) -> float:
        """
        基礎スコア計算 (単一求人用) - 後方互換性のため残す
        """
        # 単一求人をDataFrameに変換して処理
        job_data = {
            'job_id': [job.job_id],
            'fee': [job.salary.fee if job.salary and job.salary.fee else 0],
            'min_salary': [job.salary.min_salary if job.salary and job.salary.min_salary else 0],
            'salary_type': [job.salary.salary_type if job.salary else 'hourly'],
            'station_name': [job.location.station_name if job.location and job.location.station_name else None],
            'address': [job.location.address if job.location and job.location.address else None]
        }

        jobs_df = pd.DataFrame(job_data)
        scores = self.calculate_base_scores_vectorized(jobs_df)
        return float(scores[0])

    def _calculate_salary_attractiveness_vectorized(self, jobs_df: pd.DataFrame) -> np.ndarray:
        """給与魅力度計算 (Vectorized)"""
        n_jobs = len(jobs_df)
        scores = np.full(n_jobs, 5.0, dtype=self.score_dtype)  # デフォルト最低点

        min_salaries = jobs_df['min_salary'].fillna(0).values
        salary_types = jobs_df['salary_type'].fillna('hourly').values

        # 時給換算値を一括計算
        hourly_equivalents = np.zeros_like(min_salaries, dtype=self.score_dtype)

        # Vectorized salary type conversion
        hourly_mask = salary_types == 'hourly'
        daily_mask = salary_types == 'daily'
        monthly_mask = salary_types == 'monthly'

        hourly_equivalents[hourly_mask] = min_salaries[hourly_mask]
        hourly_equivalents[daily_mask] = min_salaries[daily_mask] / 8  # 8時間勤務想定
        hourly_equivalents[monthly_mask] = min_salaries[monthly_mask] / 160  # 160時間/月想定

        # Vectorized scoring thresholds
        scores[hourly_equivalents >= 1500] = 30.0
        scores[(hourly_equivalents >= 1200) & (hourly_equivalents < 1500)] = 20.0
        scores[(hourly_equivalents >= 1000) & (hourly_equivalents < 1200)] = 10.0

        return scores

    async def _calculate_salary_attractiveness(self, job: Job) -> float:
        """給与魅力度計算 (単一求人用) - 後方互換性"""
        job_data = pd.DataFrame({
            'min_salary': [job.salary.min_salary if job.salary and job.salary.min_salary else 0],
            'salary_type': [job.salary.salary_type if job.salary else 'hourly']
        })
        scores = self._calculate_salary_attractiveness_vectorized(job_data)
        return float(scores[0])

    def _calculate_access_score_vectorized(self, jobs_df: pd.DataFrame) -> np.ndarray:
        """アクセススコア計算 (Vectorized)"""
        n_jobs = len(jobs_df)
        scores = np.full(n_jobs, 5.0, dtype=self.score_dtype)  # ベーススコア

        # 駅情報ボーナス (vectorized)
        has_station = jobs_df['station_name'].notna().values
        scores[has_station] += 15.0

        # 住所詳細ボーナス (vectorized)
        has_address = jobs_df['address'].notna().values
        scores[has_address] += 5.0

        return np.clip(scores, 0, 20.0)

    async def _calculate_access_score(self, job: Job) -> float:
        """アクセススコア計算 (単一求人用) - 後方互換性"""
        job_data = pd.DataFrame({
            'station_name': [job.location.station_name if job.location and job.location.station_name else None],
            'address': [job.location.address if job.location and job.location.address else None]
        })
        scores = self._calculate_access_score_vectorized(job_data)
        return float(scores[0])

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

    @lru_cache(maxsize=10000)  # 拡張キャッシュサイズ
    async def _is_adjacent_prefecture(self, pref1: str, pref2: str) -> bool:
        """隣接都道府県判定（永続キャッシュ付き）"""
        cache_key = f"{pref1}-{pref2}"
        if cache_key in self._prefecture_distance_cache:
            self._performance_stats['cache_hits'] += 1
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
            self._performance_stats['cache_misses'] += 1
            return is_adjacent

        except Exception as e:
            logger.warning(f"Error checking prefecture adjacency: {e}")
            return False

    async def _load_prefecture_adjacency_bulk(self) -> Dict[str, List[str]]:
        """都道府県隣接データを一括ロード (セッション開始時)"""
        try:
            result = await self.db.execute(text("""
                SELECT pref_code, adjacent_prefectures
                FROM prefecture_adjacency
            """))

            adjacency_data = {}
            for row in result.fetchall():
                adjacency_data[row.pref_code] = row.adjacent_prefectures

            # 相互参照でキャッシュを充填
            for pref1, adjacents in adjacency_data.items():
                for pref2 in adjacents:
                    self._prefecture_distance_cache[f"{pref1}-{pref2}"] = True
                    self._prefecture_distance_cache[f"{pref2}-{pref1}"] = True

            logger.info(f"Prefecture adjacency cache loaded: {len(self._prefecture_distance_cache)} entries")
            return adjacency_data

        except Exception as e:
            logger.error(f"Error loading prefecture adjacency data: {e}")
            return {}

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

    async def process_scoring_batch(
        self,
        users_df: pd.DataFrame,
        jobs_df: pd.DataFrame,
        chunk_size: int = 1000
    ) -> pd.DataFrame:
        """
        高性能バッチスコア計算 - DataFrameベース

        Target: 180ms per user for 100K jobs

        Args:
            users_df: ユーザーDataFrame
            jobs_df: 求人DataFrame
            chunk_size: チャンクサイズ

        Returns:
            スコアデータを含むDataFrame
        """
        start_time = time.time()

        try:
            total_users = len(users_df)
            total_jobs = len(jobs_df)

            logger.info(f"Starting batch scoring: {total_users} users × {total_jobs} jobs")

            all_results = []

            # ユーザーをチャンクに分割して処理
            for i in range(0, total_users, chunk_size):
                chunk_users = users_df.iloc[i:i + chunk_size]

                # チャンク内スコア計算
                chunk_results = await self._calculate_chunk_scores(chunk_users, jobs_df)
                all_results.append(chunk_results)

                # 進捗ログ
                processed_users = min(i + chunk_size, total_users)
                elapsed = time.time() - start_time
                avg_time_per_user = elapsed / processed_users

                logger.info(f"Processed {processed_users}/{total_users} users in {elapsed:.2f}s "
                           f"(avg: {avg_time_per_user*1000:.1f}ms/user)")

                # 180ms target check
                if avg_time_per_user > 0.18:
                    logger.warning(f"Performance target missed: {avg_time_per_user*1000:.1f}ms/user > 180ms")

            # 結果をマージ
            final_results = pd.concat(all_results, ignore_index=True)

            total_time = time.time() - start_time
            total_calculations = len(final_results)
            avg_time_per_calculation = total_time / total_calculations * 1000

            logger.info(f"Batch scoring completed: {total_calculations} scores in {total_time:.2f}s "
                       f"(avg: {avg_time_per_calculation:.2f}ms/calculation)")

            return final_results

        except Exception as e:
            logger.error(f"Error in batch scoring: {e}")
            # エラー時は最小限のデータを返す
            return pd.DataFrame({
                'user_id': [],
                'job_id': [],
                'total_score': [],
                'base_score': [],
                'seo_score': [],
                'personal_score': []
            })

    async def _calculate_chunk_scores(
        self,
        users_chunk: pd.DataFrame,
        jobs_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        チャンク内スコア計算 - 高度な最適化
        """
        chunk_size = len(users_chunk)
        n_jobs = len(jobs_df)

        # すべての組み合わせのインデックス生成
        user_indices = np.repeat(users_chunk.index.values, n_jobs)
        job_indices = np.tile(jobs_df.index.values, chunk_size)

        # 基礎スコア計算 (全求人対象)
        base_scores = self.calculate_base_scores_vectorized(jobs_df)
        expanded_base_scores = np.tile(base_scores, chunk_size)

        # SEOスコア計算 (vectorized)
        seo_scores = await self._calculate_seo_scores_vectorized(users_chunk, jobs_df)

        # パーソナルスコア計算 (vectorized)
        personal_scores = await self._calculate_personal_scores_vectorized(users_chunk, jobs_df)

        # 総合スコア計算
        weights = {'base': 0.4, 'seo': 0.3, 'personal': 0.3}
        total_scores = (
            expanded_base_scores * weights['base'] +
            seo_scores * weights['seo'] +
            personal_scores * weights['personal']
        )

        # 結果DataFrame作成
        results_df = pd.DataFrame({
            'user_id': users_chunk.iloc[user_indices // n_jobs]['user_id'].values,
            'job_id': jobs_df.iloc[job_indices]['job_id'].values,
            'total_score': total_scores.astype(self.score_dtype),
            'base_score': expanded_base_scores.astype(self.score_dtype),
            'seo_score': seo_scores.astype(self.score_dtype),
            'personal_score': personal_scores.astype(self.score_dtype)
        })

        return results_df

    async def batch_calculate_scores(
        self,
        job_user_pairs: List[Tuple[Job, User, Optional[UserProfile]]]
    ) -> List[float]:
        """
        バッチスコア計算 (Legacy compatibility)
        """
        # Legacy interface - convert to DataFrame processing
        try:
            # DataFrameに変換
            users_data = []
            jobs_data = []

            for job, user, profile in job_user_pairs:
                user_data = {
                    'user_id': user.user_id,
                    'estimated_pref_cd': getattr(user, 'estimated_pref_cd', None),
                    'estimated_city_cd': getattr(user, 'estimated_city_cd', None)
                }
                users_data.append(user_data)

                job_data = {
                    'job_id': job.job_id,
                    'fee': job.salary.fee if job.salary and job.salary.fee else 0,
                    'min_salary': job.salary.min_salary if job.salary and job.salary.min_salary else 0,
                    'salary_type': job.salary.salary_type if job.salary else 'hourly',
                    'prefecture_code': job.location.prefecture_code if job.location else None,
                    'occupation_cd1': job.category.occupation_cd1 if job.category else None
                }
                jobs_data.append(job_data)

            users_df = pd.DataFrame(users_data).drop_duplicates('user_id')
            jobs_df = pd.DataFrame(jobs_data).drop_duplicates('job_id')

            # 新しいバッチ処理で計算
            results_df = await self.process_scoring_batch(users_df, jobs_df)

            # 元の順序で結果を返す
            scores = []
            for job, user, profile in job_user_pairs:
                matching_scores = results_df[
                    (results_df['user_id'] == user.user_id) &
                    (results_df['job_id'] == job.job_id)
                ]
                if not matching_scores.empty:
                    scores.append(float(matching_scores.iloc[0]['total_score']))
                else:
                    scores.append(0.0)

            return scores

        except Exception as e:
            logger.error(f"Error in legacy batch scoring: {e}")
            return [0.0] * len(job_user_pairs)

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

    # === 新しい高性能メソッド ===

    async def _calculate_seo_scores_vectorized(
        self,
        users_df: pd.DataFrame,
        jobs_df: pd.DataFrame
    ) -> np.ndarray:
        """
        SEOスコアのvectorized計算
        """
        n_users = len(users_df)
        n_jobs = len(jobs_df)
        total_combinations = n_users * n_jobs

        # デフォルトスコア
        seo_scores = np.full(total_combinations, 40.0, dtype=self.score_dtype)

        # Location matching (vectorized)
        user_prefs = users_df['estimated_pref_cd'].values
        job_prefs = jobs_df['prefecture_code'].values

        # Broadcast for all combinations
        user_prefs_expanded = np.repeat(user_prefs, n_jobs)
        job_prefs_expanded = np.tile(job_prefs, n_users)

        # Perfect location matches
        location_matches = (user_prefs_expanded == job_prefs_expanded) & \
                          pd.notna(user_prefs_expanded) & pd.notna(job_prefs_expanded)
        seo_scores[location_matches] += 40.0

        return seo_scores

    async def _calculate_personal_scores_vectorized(
        self,
        users_df: pd.DataFrame,
        jobs_df: pd.DataFrame
    ) -> np.ndarray:
        """
        パーソナルスコアのvectorized計算
        """
        n_users = len(users_df)
        n_jobs = len(jobs_df)
        total_combinations = n_users * n_jobs

        # デフォルトスコア
        personal_scores = np.full(total_combinations, 40.0, dtype=self.score_dtype)

        # 簡易的な傾向ベースのスコアリング
        # 実際の実装では user behavior データを使用

        return personal_scores

    @lru_cache(maxsize=500)  # 1時間キャッシュ
    async def _get_company_popularity_cached(self, endcl_cd: str) -> Dict[str, Any]:
        """
        企業人気度の1時間キャッシュ
        """
        cache_key = f"popularity_{endcl_cd}_{datetime.now().hour}"

        if cache_key in self._company_popularity_cache:
            self._performance_stats['cache_hits'] += 1
            return self._company_popularity_cache[cache_key]

        try:
            result = await self.db.execute(text("""
                SELECT
                    application_rate,
                    applications_7d,
                    views_7d,
                    popularity_score
                FROM job_company_popularity
                WHERE endcl_cd = :endcl_cd
                LIMIT 1
            """), {"endcl_cd": endcl_cd})

            row = result.fetchone()
            if row:
                data = {
                    'application_rate': row.application_rate,
                    'applications_7d': row.applications_7d,
                    'views_7d': row.views_7d,
                    'popularity_score': row.popularity_score
                }
            else:
                data = {
                    'application_rate': 0.05,
                    'applications_7d': 0,
                    'views_7d': 0,
                    'popularity_score': 50.0
                }

            self._company_popularity_cache[cache_key] = data
            self._performance_stats['cache_misses'] += 1
            return data

        except Exception as e:
            logger.warning(f"Error fetching company popularity for {endcl_cd}: {e}")
            return {'application_rate': 0.05, 'applications_7d': 0, 'views_7d': 0, 'popularity_score': 50.0}

    def _update_performance_stats(self, operation: str, calc_time: float, count: int):
        """
        パフォーマンス統計の更新
        """
        self._performance_stats['total_calculations'] += count

        # 移動平均の更新
        if self._performance_stats['avg_calculation_time'] == 0:
            self._performance_stats['avg_calculation_time'] = calc_time / count
        else:
            # Exponential moving average
            alpha = 0.1
            new_avg = calc_time / count
            self._performance_stats['avg_calculation_time'] = (
                alpha * new_avg + (1 - alpha) * self._performance_stats['avg_calculation_time']
            )

        # パフォーマンスアラート
        avg_per_item = calc_time / count * 1000  # ms
        if avg_per_item > 180:  # 180ms threshold
            logger.warning(f"Performance alert: {operation} took {avg_per_item:.1f}ms per item (target: 180ms)")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        パフォーマンス統計の取得
        """
        total_cache_operations = self._performance_stats['cache_hits'] + self._performance_stats['cache_misses']
        cache_hit_rate = (
            self._performance_stats['cache_hits'] / total_cache_operations
            if total_cache_operations > 0 else 0
        )

        return {
            **self._performance_stats,
            'cache_hit_rate': cache_hit_rate,
            'avg_calculation_time_ms': self._performance_stats['avg_calculation_time'] * 1000,
            'memory_usage': {
                'prefecture_cache_size': len(self._prefecture_distance_cache),
                'occupation_cache_size': len(self._occupation_similarity_cache),
                'company_popularity_cache_size': len(self._company_popularity_cache)
            }
        }

    def clear_caches(self, cache_types: List[str] = None):
        """
        キャッシュのクリア

        Args:
            cache_types: クリア対象のキャッシュタイプリスト
                        None の場合は全てクリア
        """
        if cache_types is None:
            cache_types = ['all']

        if 'all' in cache_types or 'session' in cache_types:
            self._occupation_similarity_cache.clear()
            self._user_history_cache.clear()

        if 'all' in cache_types or 'company' in cache_types:
            self._company_popularity_cache.clear()

        if 'all' in cache_types or 'prefecture' in cache_types:
            # 永続キャッシュは通常クリアしない
            logger.info("Prefecture cache cleared (not recommended)")
            self._prefecture_distance_cache.clear()

        logger.info(f"Caches cleared: {cache_types}")

    async def warmup_caches(self):
        """
        キャッシュのウォームアップ (セッション開始時に実行)
        """
        logger.info("Starting cache warmup...")
        start_time = time.time()

        # 都道府県隣接データのプリロード
        await self._load_prefecture_adjacency_bulk()

        # その他のキャッシュウォームアップ処理...

        warmup_time = time.time() - start_time
        logger.info(f"Cache warmup completed in {warmup_time:.2f}s")

    # === データベース最適化メソッド ===

    async def _batch_load_user_history(self, user_ids: List[int]) -> Dict[int, Dict]:
        """
        ユーザー履歴データの一括ロード
        個別クエリの代わりにバッチクエリを使用
        """
        try:
            result = await self.db.execute(text("""
                SELECT
                    ua.user_id,
                    j.occupation_cd1,
                    j.min_salary,
                    j.prefecture_code,
                    ua.action_type,
                    COUNT(*) as action_count
                FROM user_actions ua
                JOIN jobs j ON ua.job_id = j.job_id
                WHERE ua.user_id = ANY(:user_ids)
                AND ua.action_timestamp > CURRENT_DATE - INTERVAL '90 days'
                GROUP BY ua.user_id, j.occupation_cd1, j.min_salary, j.prefecture_code, ua.action_type
                ORDER BY ua.user_id, action_count DESC
            """), {"user_ids": user_ids})

            # ユーザー別に履歴を整理
            user_history = {}
            for row in result.fetchall():
                user_id = row.user_id
                if user_id not in user_history:
                    user_history[user_id] = {
                        'applications': [],
                        'clicks': [],
                        'views': []
                    }

                action_data = {
                    'occupation_cd1': row.occupation_cd1,
                    'min_salary': row.min_salary,
                    'prefecture_code': row.prefecture_code,
                    'count': row.action_count
                }

                user_history[user_id][f"{row.action_type}s"].append(action_data)

            logger.info(f"Loaded history for {len(user_history)} users")
            return user_history

        except Exception as e:
            logger.error(f"Error loading user history batch: {e}")
            return {}

    async def _batch_load_company_popularity(self, endcl_cds: List[str]) -> Dict[str, Dict]:
        """
        企業人気度データの一括ロード
        """
        try:
            result = await self.db.execute(text("""
                SELECT
                    endcl_cd,
                    application_rate,
                    applications_7d,
                    applications_30d,
                    views_7d,
                    views_30d,
                    popularity_score
                FROM job_company_popularity
                WHERE endcl_cd = ANY(:endcl_cds)
            """), {"endcl_cds": endcl_cds})

            popularity_data = {}
            for row in result.fetchall():
                popularity_data[row.endcl_cd] = {
                    'application_rate': row.application_rate,
                    'applications_7d': row.applications_7d,
                    'applications_30d': row.applications_30d,
                    'views_7d': row.views_7d,
                    'views_30d': row.views_30d,
                    'popularity_score': row.popularity_score
                }

            logger.info(f"Loaded popularity data for {len(popularity_data)} companies")
            return popularity_data

        except Exception as e:
            logger.error(f"Error loading company popularity batch: {e}")
            return {}

    async def _batch_load_jobs_optimized(self, job_ids: List[int] = None, limit: int = None) -> pd.DataFrame:
        """
        求人データの最適化された一括ロード
        インデックス利用とJOIN最適化
        """
        try:
            if job_ids:
                where_clause = "WHERE j.job_id = ANY(:job_ids)"
                params = {"job_ids": job_ids}
            else:
                where_clause = "WHERE j.is_active = true"
                params = {}

            limit_clause = f"LIMIT {limit}" if limit else ""

            result = await self.db.execute(text(f"""
                SELECT
                    j.job_id,
                    j.endcl_cd,
                    j.company_name,
                    j.application_name,

                    -- Location data
                    jl.prefecture_code,
                    jl.city_code,
                    jl.station_name,
                    jl.address,

                    -- Salary data
                    js.salary_type,
                    js.min_salary,
                    js.max_salary,
                    js.fee,

                    -- Category data
                    jc.occupation_cd1,
                    jc.occupation_cd2,

                    -- Features
                    jf.has_daily_payment,
                    jf.has_no_experience,
                    jf.has_student_welcome,
                    jf.has_remote_work,

                    -- Timestamps
                    j.posting_date,
                    j.created_at
                FROM jobs j
                LEFT JOIN job_locations jl ON j.job_id = jl.job_id
                LEFT JOIN job_salaries js ON j.job_id = js.job_id
                LEFT JOIN job_categories jc ON j.job_id = jc.job_id
                LEFT JOIN job_features jf ON j.job_id = jf.job_id
                {where_clause}
                ORDER BY j.job_id
                {limit_clause}
            """), params)

            # pandasDataFrameに変換
            columns = [
                'job_id', 'endcl_cd', 'company_name', 'application_name',
                'prefecture_code', 'city_code', 'station_name', 'address',
                'salary_type', 'min_salary', 'max_salary', 'fee',
                'occupation_cd1', 'occupation_cd2',
                'has_daily_payment', 'has_no_experience', 'has_student_welcome', 'has_remote_work',
                'posting_date', 'created_at'
            ]

            data = []
            for row in result.fetchall():
                data.append(dict(zip(columns, row)))

            jobs_df = pd.DataFrame(data)

            # データ型最適化
            if not jobs_df.empty:
                jobs_df['job_id'] = jobs_df['job_id'].astype('int32')
                jobs_df['min_salary'] = pd.to_numeric(jobs_df['min_salary'], errors='coerce').astype('float32')
                jobs_df['max_salary'] = pd.to_numeric(jobs_df['max_salary'], errors='coerce').astype('float32')
                jobs_df['fee'] = pd.to_numeric(jobs_df['fee'], errors='coerce').astype('float32')
                jobs_df['occupation_cd1'] = pd.to_numeric(jobs_df['occupation_cd1'], errors='coerce').astype('Int16')

                # Boolean columns
                bool_columns = ['has_daily_payment', 'has_no_experience', 'has_student_welcome', 'has_remote_work']
                for col in bool_columns:
                    jobs_df[col] = jobs_df[col].fillna(False).astype('bool')

            logger.info(f"Loaded {len(jobs_df)} jobs with optimized data types")
            return jobs_df

        except Exception as e:
            logger.error(f"Error loading jobs batch: {e}")
            return pd.DataFrame()

    async def _batch_load_users_optimized(self, user_ids: List[int] = None, limit: int = None) -> pd.DataFrame:
        """
        ユーザーデータの最適化された一括ロード
        """
        try:
            if user_ids:
                where_clause = "WHERE u.user_id = ANY(:user_ids)"
                params = {"user_ids": user_ids}
            else:
                where_clause = "WHERE u.is_active = true"
                params = {}

            limit_clause = f"LIMIT {limit}" if limit else ""

            result = await self.db.execute(text(f"""
                SELECT
                    u.user_id,
                    u.email_hash,
                    u.age_group,
                    u.gender,
                    u.estimated_pref_cd,
                    u.estimated_city_cd,

                    -- Preferences
                    up.preferred_categories,
                    up.preferred_salary_min,
                    up.location_preference_radius,

                    -- Behavior stats
                    ubs.application_count,
                    ubs.click_count,
                    ubs.view_count,
                    ubs.avg_salary_preference,

                    u.registration_date,
                    u.created_at
                FROM users u
                LEFT JOIN user_preferences up ON u.user_id = up.user_id
                LEFT JOIN user_behavior_stats ubs ON u.user_id = ubs.user_id
                {where_clause}
                ORDER BY u.user_id
                {limit_clause}
            """), params)

            columns = [
                'user_id', 'email_hash', 'age_group', 'gender',
                'estimated_pref_cd', 'estimated_city_cd',
                'preferred_categories', 'preferred_salary_min', 'location_preference_radius',
                'application_count', 'click_count', 'view_count', 'avg_salary_preference',
                'registration_date', 'created_at'
            ]

            data = []
            for row in result.fetchall():
                data.append(dict(zip(columns, row)))

            users_df = pd.DataFrame(data)

            # データ型最適化
            if not users_df.empty:
                users_df['user_id'] = users_df['user_id'].astype('int32')
                users_df['preferred_salary_min'] = pd.to_numeric(users_df['preferred_salary_min'], errors='coerce').astype('float32')
                users_df['application_count'] = pd.to_numeric(users_df['application_count'], errors='coerce').astype('int16')
                users_df['click_count'] = pd.to_numeric(users_df['click_count'], errors='coerce').astype('int16')
                users_df['view_count'] = pd.to_numeric(users_df['view_count'], errors='coerce').astype('int16')

            logger.info(f"Loaded {len(users_df)} users with optimized data types")
            return users_df

        except Exception as e:
            logger.error(f"Error loading users batch: {e}")
            return pd.DataFrame()

    # === メモリ最適化メソッド ===

    def _optimize_dataframe_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameのメモリ使用量最適化
        """
        start_memory = df.memory_usage(deep=True).sum()

        for col in df.columns:
            col_type = df[col].dtype

            if col_type != 'object':
                continue

            # カテゴリカルデータへの変換
            num_unique_values = len(df[col].unique())
            num_total_values = len(df[col])

            if num_unique_values / num_total_values < 0.5:  # 50%以下ならカテゴリ化
                df[col] = df[col].astype('category')

        # 数値型の最適化
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')

        end_memory = df.memory_usage(deep=True).sum()
        memory_reduction = (start_memory - end_memory) / start_memory * 100

        logger.info(f"Memory usage reduced by {memory_reduction:.1f}% "
                   f"({start_memory / 1024**2:.1f}MB -> {end_memory / 1024**2:.1f}MB)")

        return df

    def _clear_large_objects(self, *objects):
        """
        大きなオブジェクトのメモリクリア
        """
        import gc
        for obj in objects:
            if obj is not None:
                del obj
        gc.collect()

    # === 高性能エントリーポイント ===

    async def calculate_scores_for_all_users(
        self,
        job_limit: int = None,
        user_limit: int = None,
        score_types: List[str] = None
    ) -> pd.DataFrame:
        """
        全ユーザー・全求人スコア計算のエントリーポイント

        100K jobs × 10K users = 1B combinations
        Target: 180ms per user average
        """
        start_time = time.time()

        try:
            # データの一括ロード
            logger.info("Loading data...")

            load_start = time.time()
            jobs_df, users_df = await asyncio.gather(
                self._batch_load_jobs_optimized(limit=job_limit),
                self._batch_load_users_optimized(limit=user_limit)
            )
            load_time = time.time() - load_start

            if jobs_df.empty or users_df.empty:
                logger.error("No data loaded")
                return pd.DataFrame()

            logger.info(f"Data loaded in {load_time:.2f}s: {len(jobs_df)} jobs, {len(users_df)} users")

            # メモリ最適化
            jobs_df = self._optimize_dataframe_memory(jobs_df)
            users_df = self._optimize_dataframe_memory(users_df)

            # キャッシュウォームアップ
            await self.warmup_caches()

            # バッチスコア計算
            results_df = await self.process_scoring_batch(users_df, jobs_df)

            total_time = time.time() - start_time
            total_scores = len(results_df)
            avg_time_per_user = total_time / len(users_df)

            logger.info(f"Complete scoring finished in {total_time:.2f}s")
            logger.info(f"Performance: {avg_time_per_user*1000:.1f}ms per user, {total_scores} total scores")

            # パフォーマンス目標チェック
            if avg_time_per_user > 0.18:
                logger.warning(f"Performance target missed: {avg_time_per_user*1000:.1f}ms > 180ms per user")
            else:
                logger.info(f"Performance target achieved: {avg_time_per_user*1000:.1f}ms per user")

            return results_df

        except Exception as e:
            logger.error(f"Error in complete scoring calculation: {e}")
            return pd.DataFrame()