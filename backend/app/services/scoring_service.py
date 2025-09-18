"""
スコアリングサービス
API層とスコアリングエンジンのブリッジ層

T021統合版 - BasicScoringEngineと既存ScoringEngineを統合
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.services.scoring import ScoringEngine
from app.models.jobs import Job
from app.models.users import User, UserProfile
from app.models.matching import MatchingScore
from app.core.config import settings
from app.core.cache import cache_manager

logger = logging.getLogger(__name__)


class ScoringService:
    """
    スコアリングサービス

    APIエンドポイントから呼び出される高レベルのサービス層
    T021準拠のBasicScoringEngineを内部的に使用
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.scoring_engine = ScoringEngine(db)
        self._batch_cache = {}

    async def calculate_single_score(
        self,
        user_id: int,
        job_id: int,
        include_explanation: bool = False,
        score_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        単一ペアのスコア計算

        Args:
            user_id: ユーザーID
            job_id: 求人ID
            include_explanation: 説明を含めるか
            score_version: スコアリングバージョン（T021など）

        Returns:
            スコア計算結果
        """
        try:
            # ユーザーと求人データの取得
            user = await self._get_user(user_id)
            job = await self._get_job(job_id)

            if not user or not job:
                return None

            # ユーザープロファイルの取得（オプション）
            user_profile = await self._get_user_profile(user_id)

            # スコア計算（T021統合版を使用）
            matching_score = await self.scoring_engine.calculate_score(
                user=user,
                job=job,
                user_profile=user_profile
            )

            # レスポンス形式に変換
            response = {
                "user_id": user_id,
                "job_id": job_id,
                "composite_score": matching_score.composite_score,
                "component_scores": {
                    "basic": matching_score.basic_score,
                    "location": matching_score.location_score,
                    "category": matching_score.category_score,
                    "salary": matching_score.salary_score,
                    "feature": matching_score.feature_score,
                    "preference": matching_score.preference_score,
                    "popularity": matching_score.popularity_score
                },
                "calculated_at": datetime.now().isoformat()
            }

            # 説明を含める場合
            if include_explanation:
                response["explanation"] = self._generate_explanation(matching_score)

            # スコアリングログの記録
            await self._log_scoring_execution(
                user_id, job_id, matching_score, score_version or "T021"
            )

            return response

        except Exception as e:
            logger.error(f"Error calculating score for user {user_id}, job {job_id}: {e}")
            raise

    async def calculate_batch_scores(
        self,
        user_ids: List[int],
        job_ids: List[int],
        include_explanation: bool = False,
        score_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        バッチスコア計算（同期処理）

        Args:
            user_ids: ユーザーIDリスト
            job_ids: 求人IDリスト
            include_explanation: 説明を含めるか
            score_version: スコアリングバージョン

        Returns:
            バッチスコア計算結果
        """
        import time
        start_time = time.time()

        try:
            # ユーザーと求人データの一括取得
            users = await self._get_users_batch(user_ids)
            jobs = await self._get_jobs_batch(job_ids)
            user_profiles = await self._get_user_profiles_batch(user_ids)

            # ペアの組み合わせを作成
            pairs = []
            for user in users:
                for job in jobs:
                    profile = user_profiles.get(user.user_id)
                    pairs.append((user, job, profile))

            # バッチスコア計算（T021対応）
            scores = await self.scoring_engine.batch_calculate_scores(pairs)

            # レスポンス形式に変換
            score_responses = []
            for (user, job, _), score in zip(pairs, scores):
                response = {
                    "user_id": user.user_id,
                    "job_id": job.job_id,
                    "composite_score": score.composite_score,
                    "component_scores": {
                        "basic": score.basic_score,
                        "location": score.location_score,
                        "category": score.category_score,
                        "salary": score.salary_score,
                        "feature": score.feature_score,
                        "preference": score.preference_score,
                        "popularity": score.popularity_score
                    },
                    "calculated_at": datetime.now().isoformat()
                }

                if include_explanation:
                    response["explanation"] = self._generate_explanation(score)

                score_responses.append(response)

            processing_time = time.time() - start_time

            return {
                "batch_id": None,  # 同期処理のためなし
                "total_combinations": len(user_ids) * len(job_ids),
                "completed_count": len(score_responses),
                "scores": score_responses,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Error in batch score calculation: {e}")
            raise

    async def start_batch_calculation(
        self,
        user_ids: List[int],
        job_ids: List[int],
        include_explanation: bool = False,
        score_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        非同期バッチ計算の開始

        Args:
            user_ids: ユーザーIDリスト
            job_ids: 求人IDリスト
            include_explanation: 説明を含めるか
            score_version: スコアリングバージョン

        Returns:
            バッチ情報
        """
        batch_id = str(uuid.uuid4())
        total_combinations = len(user_ids) * len(job_ids)

        # バッチ情報をキャッシュに保存
        batch_info = {
            "batch_id": batch_id,
            "total_combinations": total_combinations,
            "completed_count": 0,
            "status": "processing",
            "created_at": datetime.now().isoformat()
        }

        self._batch_cache[batch_id] = batch_info

        return {
            "batch_id": batch_id,
            "total_combinations": total_combinations,
            "completed_count": 0,
            "scores": [],
            "processing_time": 0
        }

    async def process_batch_async(self, batch_id: str):
        """
        バックグラウンドでバッチ処理を実行

        Args:
            batch_id: バッチID
        """
        # 実際のバッチ処理実装
        # ここでは簡略化のため、実装を省略
        logger.info(f"Processing batch {batch_id} in background")
        await asyncio.sleep(1)  # シミュレーション

    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        バッチ処理状況の取得

        Args:
            batch_id: バッチID

        Returns:
            バッチ状況
        """
        return self._batch_cache.get(batch_id)

    async def get_batch_results(
        self,
        batch_id: str,
        page: int = 1,
        size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        バッチ処理結果の取得

        Args:
            batch_id: バッチID
            page: ページ番号
            size: ページサイズ

        Returns:
            バッチ結果
        """
        batch_info = self._batch_cache.get(batch_id)
        if not batch_info:
            return None

        # 実際の結果取得実装
        # ここでは簡略化のため、ダミーデータを返す
        return {
            "batch_id": batch_id,
            "total_combinations": batch_info["total_combinations"],
            "completed_count": batch_info["completed_count"],
            "scores": [],
            "processing_time": 0
        }

    async def get_user_scores(
        self,
        user_id: int,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ユーザーのスコア一覧取得

        Args:
            user_id: ユーザーID
            limit: 取得件数
            filters: フィルター条件

        Returns:
            ユーザースコア情報
        """
        # 実装簡略化のため、基本的な実装のみ
        return {
            "user_id": user_id,
            "total_scores": 0,
            "top_scores": [],
            "average_score": 0,
            "updated_at": datetime.now().isoformat()
        }

    async def get_score_rankings(
        self,
        ranking_type: str = "composite",
        period: str = "daily",
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        スコアランキングの取得

        Args:
            ranking_type: ランキング種別
            period: 期間
            limit: 取得件数
            filters: フィルター条件

        Returns:
            ランキング情報
        """
        # 実装簡略化のため、基本的な実装のみ
        return {
            "rankings": [],
            "total_count": 0,
            "generated_at": datetime.now().isoformat()
        }

    async def recalculate_user_scores(self, user_id: int, force: bool = False):
        """
        ユーザースコアの再計算

        Args:
            user_id: ユーザーID
            force: 強制再計算フラグ
        """
        logger.info(f"Recalculating scores for user {user_id} (force={force})")
        # 実際の再計算処理をここに実装

    async def get_scoring_statistics(
        self,
        period_days: int = 30,
        breakdown_by: str = "category"
    ) -> Dict[str, Any]:
        """
        スコアリング統計情報の取得

        Args:
            period_days: 統計期間（日）
            breakdown_by: 分析軸

        Returns:
            統計情報
        """
        # 実装簡略化のため、基本的な統計のみ
        return {
            "period_days": period_days,
            "breakdown_by": breakdown_by,
            "total_scores_calculated": 0,
            "average_score": 0,
            "breakdown": {}
        }

    async def clear_score_cache(
        self,
        cache_type: str = "all",
        user_ids: Optional[List[int]] = None
    ):
        """
        スコアキャッシュのクリア

        Args:
            cache_type: キャッシュ種別
            user_ids: 対象ユーザーID
        """
        logger.info(f"Clearing score cache (type={cache_type}, users={user_ids})")
        # キャッシュクリア処理をここに実装
        if cache_type == "all":
            self._batch_cache.clear()

    # プライベートメソッド

    async def _get_user(self, user_id: int) -> Optional[User]:
        """ユーザー取得"""
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_job(self, job_id: int) -> Optional[Job]:
        """求人取得"""
        result = await self.db.execute(
            select(Job).where(Job.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def _get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """ユーザープロファイル取得"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_users_batch(self, user_ids: List[int]) -> List[User]:
        """ユーザー一括取得"""
        result = await self.db.execute(
            select(User).where(User.user_id.in_(user_ids))
        )
        return result.scalars().all()

    async def _get_jobs_batch(self, job_ids: List[int]) -> List[Job]:
        """求人一括取得"""
        result = await self.db.execute(
            select(Job).where(Job.job_id.in_(job_ids))
        )
        return result.scalars().all()

    async def _get_user_profiles_batch(self, user_ids: List[int]) -> Dict[int, UserProfile]:
        """ユーザープロファイル一括取得"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id.in_(user_ids))
        )
        profiles = result.scalars().all()
        return {p.user_id: p for p in profiles}

    def _generate_explanation(self, score: MatchingScore) -> str:
        """
        スコアの説明文生成

        Args:
            score: マッチングスコア

        Returns:
            説明文
        """
        explanation = f"総合スコア: {score.composite_score:.1f}/100\n\n"

        # 各コンポーネントの説明
        if score.basic_score >= 80:
            explanation += "✅ 基本評価: 非常に魅力的な求人です\n"
        elif score.basic_score >= 60:
            explanation += "👍 基本評価: 良好な条件の求人です\n"
        else:
            explanation += "📝 基本評価: 標準的な求人です\n"

        if score.location_score >= 80:
            explanation += "✅ 立地: 通勤に非常に便利です\n"
        elif score.location_score >= 60:
            explanation += "👍 立地: アクセス良好です\n"
        else:
            explanation += "📝 立地: 通勤に時間がかかる可能性があります\n"

        if score.category_score >= 80:
            explanation += "✅ 職種: 希望に完全一致しています\n"
        elif score.category_score >= 60:
            explanation += "👍 職種: 関連性の高い仕事です\n"
        else:
            explanation += "📝 職種: 新しい分野にチャレンジできます\n"

        return explanation

    async def _log_scoring_execution(
        self,
        user_id: int,
        job_id: int,
        score: MatchingScore,
        version: str
    ):
        """
        スコアリング実行ログの記録

        Args:
            user_id: ユーザーID
            job_id: 求人ID
            score: マッチングスコア
            version: スコアリングバージョン
        """
        # SQLAlchemyを使用したログ記録
        # 実装簡略化のため、詳細は省略
        logger.info(
            f"Score calculated: user={user_id}, job={job_id}, "
            f"score={score.composite_score:.1f}, version={version}"
        )