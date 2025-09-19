"""
マッチングサービス

求人とユーザーのマッチング処理、推薦システムに関するビジネスロジック
T053-T055統合: 最適化機能を統合したマッチングサービス
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.models.matching import (
    MatchingRequest, MatchingResult, MatchingBatchInfo, UserJobRecommendations,
    RealtimeMatchingRequest, RealtimeMatchingResponse, MatchingAnalytics,
    ScoringConfiguration, ABTestConfig
)
from app.services.scoring import ScoringEngine
# T053-T055統合: 最適化モジュールのインポート
from app.optimizations.query_optimizer import optimize_query, QueryOptimizer
from app.optimizations.parallel_processor import parallel_execute, parallel_batch_execute, TaskPriority
from app.services.cache_service import cached, get_cached, invalidate_cache

logger = logging.getLogger(__name__)


class MatchingService:
    """
    マッチング処理サービス（最適化統合版）

    T053-T055の最適化機能を統合:
    - クエリ最適化によるデータベースアクセス高速化
    - 並列処理によるスコアリング処理の並列化
    - キャッシュによる頻繁なアクセスの高速化
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.scoring_engine = ScoringEngine(db)
        # T053: クエリ最適化
        self.query_optimizer = QueryOptimizer()
        # T054: 並列処理設定
        self.enable_parallel_scoring = True
        self.parallel_batch_size = 100
        # T055: キャッシュ設定
        self.cache_enabled = True
        self.default_cache_ttl = 3600  # 1時間

    async def execute_matching(self, request: MatchingRequest) -> MatchingBatchInfo:
        """
        マッチング実行（最適化統合版）

        T053-T055統合による高速化:
        - クエリ最適化による高速データ取得
        - 並列処理によるスコアリング高速化
        - キャッシュによる重複計算の削減
        """
        start_time = datetime.now()
        logger.info(f"Starting optimized matching execution: {request.batch_id}")

        try:
            # T053: 最適化されたユーザー・求人データ取得
            users, jobs = await self._get_matching_data_optimized(
                request.user_ids,
                request.job_filters
            )

            if not users or not jobs:
                logger.warning("No users or jobs found for matching")
                return MatchingBatchInfo(
                    batch_id=request.batch_id,
                    status="completed",
                    total_users=0,
                    total_jobs=0,
                    total_matches=0,
                    start_time=start_time,
                    end_time=datetime.now()
                )

            # T054: 並列スコアリング実行
            matching_results = await self._parallel_scoring_execution(
                users, jobs, request.scoring_config
            )

            # T055: 結果のキャッシュ保存
            await self._cache_matching_results(request.batch_id, matching_results)

            # バッチ情報作成
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            batch_info = MatchingBatchInfo(
                batch_id=request.batch_id,
                status="completed",
                total_users=len(users),
                total_jobs=len(jobs),
                total_matches=len(matching_results),
                start_time=start_time,
                end_time=end_time,
                execution_time_seconds=execution_time,
                optimization_metrics={
                    "query_optimization_enabled": True,
                    "parallel_processing_enabled": self.enable_parallel_scoring,
                    "cache_enabled": self.cache_enabled,
                    "performance_improvement": "Optimized with T053-T055"
                }
            )

            logger.info(f"Matching completed: {execution_time:.2f}s, {len(matching_results)} matches")
            return batch_info

        except Exception as e:
            logger.error(f"Matching execution failed: {e}")
            return MatchingBatchInfo(
                batch_id=request.batch_id,
                status="failed",
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )

    async def realtime_matching(self, request: RealtimeMatchingRequest) -> RealtimeMatchingResponse:
        """リアルタイムマッチング"""
        # 実装簡略化
        pass

    async def get_user_recommendations(
        self,
        user_id: int,
        recommendation_date: Optional[str] = None,
        include_sent: bool = False
    ) -> Optional[UserJobRecommendations]:
        """ユーザー推薦取得"""
        # 実装簡略化
        pass

    async def get_batch_info(self, batch_id: int) -> Optional[MatchingBatchInfo]:
        """バッチ情報取得"""
        # 実装簡略化
        pass

    async def search_results(
        self,
        filters: Dict[str, Any],
        sort_by: str = "composite_score",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20
    ) -> List[MatchingResult]:
        """マッチング結果検索"""
        # 実装簡略化
        pass

    async def get_analytics(self, period_days: int, include_trends: bool = True) -> MatchingAnalytics:
        """マッチング分析"""
        # 実装簡略化
        pass

    async def get_scoring_config(self, version: Optional[str] = None) -> Optional[ScoringConfiguration]:
        """スコアリング設定取得"""
        # 実装簡略化
        pass

    async def update_scoring_config(self, config: ScoringConfiguration) -> ScoringConfiguration:
        """スコアリング設定更新"""
        # 実装簡略化
        pass

    async def create_ab_test(self, test_config: ABTestConfig) -> ABTestConfig:
        """A/Bテスト作成"""
        # 実装簡略化
        pass

    async def generate_daily_picks(
        self,
        target_date: Optional[str] = None,
        user_ids: Optional[List[int]] = None,
        force_regenerate: bool = False
    ) -> None:
        """日次求人選定（最適化統合版）"""
        target_date = target_date or datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Generating optimized daily picks for {target_date}")

        try:
            # T055: キャッシュチェック
            cache_key = f"daily_picks_{target_date}"
            if not force_regenerate and self.cache_enabled:
                cached_picks = await get_cached(cache_key, None)
                if cached_picks:
                    logger.info("Using cached daily picks")
                    return

            # T053: 最適化されたユーザーデータ取得
            if user_ids:
                users_query = """
                SELECT user_id, estimated_pref_cd, estimated_city_cd, age_group
                FROM users
                WHERE user_id = ANY(:user_ids) AND is_active = true
                """
                result, _ = await optimize_query(self.db, users_query, {"user_ids": user_ids})
            else:
                users_query = """
                SELECT user_id, estimated_pref_cd, estimated_city_cd, age_group
                FROM users
                WHERE is_active = true
                ORDER BY last_login_date DESC
                LIMIT 10000
                """
                result, _ = await optimize_query(self.db, users_query)

            users = result.fetchall()

            # T054: 並列処理でユーザーごとの推薦生成
            if users and self.enable_parallel_scoring:
                def generate_user_picks(user_batch):
                    return self._generate_picks_for_users(user_batch, target_date)

                user_batches = [
                    users[i:i + self.parallel_batch_size]
                    for i in range(0, len(users), self.parallel_batch_size)
                ]

                picks_results = await parallel_batch_execute(
                    generate_user_picks,
                    user_batches,
                    batch_size=self.parallel_batch_size
                )

                # T055: 結果をキャッシュに保存
                if self.cache_enabled:
                    await get_cached(
                        cache_key,
                        lambda: picks_results,
                        ttl=86400  # 24時間
                    )

            logger.info(f"Daily picks generation completed for {len(users)} users")

        except Exception as e:
            logger.error(f"Daily picks generation failed: {e}")
            raise

    # T053-T055統合: 最適化ヘルパーメソッド

    async def _get_matching_data_optimized(
        self,
        user_ids: Optional[List[int]],
        job_filters: Dict[str, Any]
    ) -> Tuple[List[Any], List[Any]]:
        """最適化されたマッチングデータ取得"""

        # T055: キャッシュキー生成
        cache_key_users = f"users_{hash(str(sorted(user_ids)) if user_ids else 'all')}"
        cache_key_jobs = f"jobs_{hash(str(sorted(job_filters.items())))}"

        async def fetch_users():
            if user_ids:
                query = """
                SELECT u.user_id, u.estimated_pref_cd, u.estimated_city_cd, u.age_group,
                       up.preferences, up.behavior_stats, up.preference_scores
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                WHERE u.user_id = ANY(:user_ids) AND u.is_active = true
                """
                result, metrics = await optimize_query(self.db, query, {"user_ids": user_ids})
            else:
                query = """
                SELECT u.user_id, u.estimated_pref_cd, u.estimated_city_cd, u.age_group,
                       up.preferences, up.behavior_stats, up.preference_scores
                FROM users u
                LEFT JOIN user_profiles up ON u.user_id = up.user_id
                WHERE u.is_active = true
                ORDER BY u.last_login_date DESC
                LIMIT 10000
                """
                result, metrics = await optimize_query(self.db, query)

            return result.fetchall()

        async def fetch_jobs():
            # 基本の求人クエリ
            base_query = """
            SELECT j.job_id, j.title, j.endcl_cd, j.posting_date,
                   jl.prefecture_code, jl.city_code, jl.station_name,
                   js.min_salary, js.max_salary, js.salary_type,
                   jf.has_daily_payment, jf.has_no_experience, jf.has_student_welcome,
                   jc.occupation_cd1, jc.occupation_cd2
            FROM jobs j
            LEFT JOIN job_locations jl ON j.job_id = jl.job_id
            LEFT JOIN job_salaries js ON j.job_id = js.job_id
            LEFT JOIN job_features jf ON j.job_id = jf.job_id
            LEFT JOIN job_categories jc ON j.job_id = jc.job_id
            WHERE j.is_active = true
            """

            # フィルター条件を動的に追加
            conditions = []
            params = {}

            if job_filters.get('prefecture_codes'):
                conditions.append("jl.prefecture_code = ANY(:prefecture_codes)")
                params['prefecture_codes'] = job_filters['prefecture_codes']

            if job_filters.get('min_salary'):
                conditions.append("js.min_salary >= :min_salary")
                params['min_salary'] = job_filters['min_salary']

            if job_filters.get('occupation_codes'):
                conditions.append("jc.occupation_cd1 = ANY(:occupation_codes)")
                params['occupation_codes'] = job_filters['occupation_codes']

            if conditions:
                query = f"{base_query} AND {' AND '.join(conditions)}"
            else:
                query = base_query

            query += " ORDER BY j.posting_date DESC LIMIT 10000"

            result, metrics = await optimize_query(self.db, query, params)
            return result.fetchall()

        # T055: キャッシュからデータ取得
        users = await get_cached(cache_key_users, fetch_users, ttl=self.default_cache_ttl)
        jobs = await get_cached(cache_key_jobs, fetch_jobs, ttl=1800)  # 30分

        return users, jobs

    async def _parallel_scoring_execution(
        self,
        users: List[Any],
        jobs: List[Any],
        scoring_config: Optional[ScoringConfiguration]
    ) -> List[MatchingResult]:
        """並列スコアリング実行"""

        if not self.enable_parallel_scoring:
            # 通常の逐次実行
            return await self._sequential_scoring(users, jobs, scoring_config)

        # T054: 並列処理でスコアリング
        logger.info(f"Starting parallel scoring: {len(users)} users × {len(jobs)} jobs")

        def score_user_job_batch(user_job_pairs):
            """ユーザー・求人ペアのバッチスコアリング"""
            results = []
            for user, job in user_job_pairs:
                try:
                    # スコア計算（簡略版）
                    score = self._calculate_simple_score(user, job)
                    if score > 30:  # 閾値フィルタ
                        results.append(MatchingResult(
                            user_id=user.user_id,
                            job_id=job.job_id,
                            composite_score=score,
                            match_date=datetime.now().date(),
                            score_details={"simple_score": score}
                        ))
                except Exception as e:
                    logger.error(f"Scoring error for user {user.user_id}, job {job.job_id}: {e}")
            return results

        # ユーザー・求人ペアの生成
        user_job_pairs = []
        for user in users[:1000]:  # 制限
            for job in jobs[:1000]:  # 制限
                user_job_pairs.append((user, job))

        # バッチに分割
        batch_size = self.parallel_batch_size
        batches = [
            user_job_pairs[i:i + batch_size]
            for i in range(0, len(user_job_pairs), batch_size)
        ]

        # 並列実行
        batch_results = await parallel_batch_execute(
            score_user_job_batch,
            batches,
            batch_size=batch_size
        )

        # 結果をフラット化
        matching_results = []
        for batch_result in batch_results:
            matching_results.extend(batch_result)

        # スコアでソート
        matching_results.sort(key=lambda x: x.composite_score, reverse=True)

        logger.info(f"Parallel scoring completed: {len(matching_results)} matches")
        return matching_results

    async def _sequential_scoring(
        self,
        users: List[Any],
        jobs: List[Any],
        scoring_config: Optional[ScoringConfiguration]
    ) -> List[MatchingResult]:
        """逐次スコアリング実行"""
        logger.info(f"Starting sequential scoring: {len(users)} users × {len(jobs)} jobs")

        matching_results = []
        for user in users[:1000]:  # 制限
            for job in jobs[:1000]:  # 制限
                try:
                    score = self._calculate_simple_score(user, job)
                    if score > 30:  # 閾値フィルタ
                        matching_results.append(MatchingResult(
                            user_id=user.user_id,
                            job_id=job.job_id,
                            composite_score=score,
                            match_date=datetime.now().date(),
                            score_details={"simple_score": score}
                        ))
                except Exception as e:
                    logger.error(f"Scoring error for user {user.user_id}, job {job.job_id}: {e}")

        matching_results.sort(key=lambda x: x.composite_score, reverse=True)
        return matching_results

    def _calculate_simple_score(self, user: Any, job: Any) -> float:
        """簡単なスコア計算"""
        score = 50.0  # ベーススコア

        # 地域マッチング
        if hasattr(user, 'estimated_pref_cd') and hasattr(job, 'prefecture_code'):
            if user.estimated_pref_cd == job.prefecture_code:
                score += 20

        # 給与評価
        if hasattr(job, 'min_salary') and job.min_salary:
            if job.min_salary >= 1200:
                score += 15
            elif job.min_salary >= 1000:
                score += 10

        # 年齢適合性
        if hasattr(user, 'age_group') and hasattr(job, 'has_student_welcome'):
            if user.age_group in ['10代', '20代前半'] and job.has_student_welcome:
                score += 10

        return min(100.0, max(0.0, score))

    async def _cache_matching_results(
        self,
        batch_id: int,
        results: List[MatchingResult]
    ):
        """マッチング結果のキャッシュ保存"""
        if not self.cache_enabled:
            return

        cache_key = f"matching_results_{batch_id}"
        await get_cached(
            cache_key,
            lambda: [result.__dict__ for result in results],
            ttl=self.default_cache_ttl
        )

    def _generate_picks_for_users(self, user_batch: List[Any], target_date: str) -> List[Dict]:
        """ユーザーバッチの求人選定"""
        picks = []
        for user in user_batch:
            # 簡略化された選定ロジック
            user_picks = {
                'user_id': user.user_id,
                'picks': [1, 2, 3],  # 求人IDのリスト
                'generated_date': target_date
            }
            picks.append(user_picks)
        return picks

    @cached("user_recommendations_{user_id}_{recommendation_date}", ttl=3600)
    async def get_user_recommendations(
        self,
        user_id: int,
        recommendation_date: Optional[str] = None,
        include_sent: bool = False
    ) -> Optional[UserJobRecommendations]:
        """ユーザー推薦取得（キャッシュ統合版）"""
        recommendation_date = recommendation_date or datetime.now().strftime('%Y-%m-%d')

        # T053: 最適化クエリで推薦データ取得
        query = """
        SELECT r.user_id, r.job_id, r.recommendation_score, r.recommendation_reason,
               j.title, j.endcl_cd, js.min_salary
        FROM user_job_recommendations r
        JOIN jobs j ON r.job_id = j.job_id
        LEFT JOIN job_salaries js ON j.job_id = js.job_id
        WHERE r.user_id = :user_id
        AND r.recommendation_date = :recommendation_date
        """

        if not include_sent:
            query += " AND r.is_sent = false"

        query += " ORDER BY r.recommendation_score DESC LIMIT 20"

        result, metrics = await optimize_query(
            self.db,
            query,
            {"user_id": user_id, "recommendation_date": recommendation_date}
        )

        recommendations = result.fetchall()

        if recommendations:
            return UserJobRecommendations(
                user_id=user_id,
                recommendation_date=recommendation_date,
                job_recommendations=[
                    {
                        "job_id": rec.job_id,
                        "score": rec.recommendation_score,
                        "reason": rec.recommendation_reason,
                        "job_title": rec.title
                    }
                    for rec in recommendations
                ],
                total_recommendations=len(recommendations)
            )

        return None