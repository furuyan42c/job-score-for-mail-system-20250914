#!/usr/bin/env python3
"""
T021: Optimized Basic Scoring Service (REFACTOR Phase)

高速化された基礎スコア計算サービス
- NumPyベクトル演算による高速化
- バッチ処理最適化
- メモリ効率改善
"""

import logging
from typing import List, Dict, Optional, Union
import numpy as np
from dataclasses import dataclass

from app.models.job import Job

logger = logging.getLogger(__name__)


@dataclass
class BatchScoringResult:
    """バッチスコアリング結果"""
    job_id: str
    fee_score: float
    wage_score: float
    popularity_score: float
    combined_score: float


class OptimizedBasicScoringService:
    """最適化された基礎スコア計算サービス"""

    # 定数の事前計算
    FEE_THRESHOLD = 500
    FEE_MAX = 5000
    FEE_SCALE = 100.0 / (FEE_MAX - FEE_THRESHOLD)

    WAGE_THRESHOLD = 1000
    WAGE_MAX = 3000
    WAGE_SCALE = 100.0 / (WAGE_MAX - WAGE_THRESHOLD)

    # 重み付け設定
    WAGE_WEIGHT = 0.4
    FEE_WEIGHT = 0.3
    POPULARITY_WEIGHT = 0.3

    def __init__(self):
        """サービス初期化"""
        logger.info("OptimizedBasicScoringService initialized")

    async def calculate_fee_score(self, job: Job) -> float:
        """単体ジョブのfeeスコア計算（互換性維持）"""
        fee = getattr(job, "fee", 0)
        if fee <= self.FEE_THRESHOLD:
            return 0.0
        return min((fee - self.FEE_THRESHOLD) * self.FEE_SCALE, 100.0)

    async def calculate_hourly_wage_score(self, job: Job) -> float:
        """単体ジョブの時給スコア計算（互換性維持）"""
        hourly_wage = getattr(job, "hourly_wage", 0)
        if hourly_wage <= self.WAGE_THRESHOLD:
            return 0.0
        return min((hourly_wage - self.WAGE_THRESHOLD) * self.WAGE_SCALE, 100.0)

    async def calculate_company_popularity_score(
        self, job: Job, mean_applications: float, std_applications: float
    ) -> float:
        """単体ジョブの人気度スコア計算（互換性維持）"""
        application_clicks = getattr(job, "application_clicks", 0)
        if application_clicks <= 0 or std_applications == 0:
            return 50.0 if std_applications == 0 else 0.0

        z_score = (application_clicks - mean_applications) / std_applications
        normalized_score = ((z_score + 3) / 6) * 100
        return max(0.0, min(100.0, normalized_score))

    async def calculate_combined_score(
        self, job: Job, mean_applications: float = 100, std_applications: float = 50
    ) -> float:
        """単体ジョブの総合スコア計算（互換性維持）"""
        fee_score = await self.calculate_fee_score(job)
        wage_score = await self.calculate_hourly_wage_score(job)
        popularity_score = await self.calculate_company_popularity_score(
            job, mean_applications, std_applications
        )

        combined = (
            wage_score * self.WAGE_WEIGHT +
            fee_score * self.FEE_WEIGHT +
            popularity_score * self.POPULARITY_WEIGHT
        )
        return min(combined, 100.0)

    @classmethod
    def _calculate_fee_scores_vectorized(cls, fees: np.ndarray) -> np.ndarray:
        """ベクトル化されたfeeスコア計算"""
        scores = np.zeros_like(fees, dtype=np.float32)
        valid = fees > cls.FEE_THRESHOLD
        scores[valid] = np.minimum(
            (fees[valid] - cls.FEE_THRESHOLD) * cls.FEE_SCALE,
            100.0
        )
        return scores

    @classmethod
    def _calculate_wage_scores_vectorized(cls, wages: np.ndarray) -> np.ndarray:
        """ベクトル化された時給スコア計算"""
        scores = np.zeros_like(wages, dtype=np.float32)
        valid = wages > cls.WAGE_THRESHOLD
        scores[valid] = np.minimum(
            (wages[valid] - cls.WAGE_THRESHOLD) * cls.WAGE_SCALE,
            100.0
        )
        return scores

    @classmethod
    def _calculate_popularity_scores_vectorized(
        cls, clicks: np.ndarray, mean: float, std: float
    ) -> np.ndarray:
        """ベクトル化された人気度スコア計算"""
        if std == 0:
            return np.full_like(clicks, 50.0, dtype=np.float32)

        z_scores = (clicks - mean) / std
        scores = ((z_scores + 3) / 6) * 100
        return np.clip(scores, 0, 100).astype(np.float32)

    async def batch_calculate_scores(
        self,
        jobs: List[Job],
        batch_size: int = 10000
    ) -> List[BatchScoringResult]:
        """
        バッチ処理での高速スコア計算

        Args:
            jobs: ジョブオブジェクトのリスト
            batch_size: バッチサイズ（メモリ使用量調整）

        Returns:
            スコア計算結果のリスト
        """
        if not jobs:
            return []

        results = []
        total = len(jobs)

        # NumPy配列に変換
        fees = np.array([getattr(j, "fee", 0) for j in jobs], dtype=np.float32)
        wages = np.array([getattr(j, "hourly_wage", 0) for j in jobs], dtype=np.float32)
        clicks = np.array([getattr(j, "application_clicks", 0) for j in jobs], dtype=np.float32)

        # 統計値の事前計算
        clicks_mean = np.mean(clicks)
        clicks_std = np.std(clicks)

        logger.info(f"Starting batch scoring for {total} jobs (batch_size={batch_size})")

        # バッチごとに処理
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            batch_slice = slice(i, end_idx)

            # ベクトル化計算
            fee_scores = self._calculate_fee_scores_vectorized(fees[batch_slice])
            wage_scores = self._calculate_wage_scores_vectorized(wages[batch_slice])
            popularity_scores = self._calculate_popularity_scores_vectorized(
                clicks[batch_slice], clicks_mean, clicks_std
            )

            # 重み付け合計
            combined_scores = (
                wage_scores * self.WAGE_WEIGHT +
                fee_scores * self.FEE_WEIGHT +
                popularity_scores * self.POPULARITY_WEIGHT
            )

            # 結果を構造体に格納
            for j, idx in enumerate(range(i, end_idx)):
                result = BatchScoringResult(
                    job_id=getattr(jobs[idx], "job_id", f"unknown_{idx}"),
                    fee_score=float(fee_scores[j]),
                    wage_score=float(wage_scores[j]),
                    popularity_score=float(popularity_scores[j]),
                    combined_score=float(combined_scores[j])
                )
                results.append(result)

            # 進捗ログ
            if (i + batch_size) % 50000 == 0:
                logger.info(f"Processed {min(i + batch_size, total)}/{total} jobs")

        logger.info(f"Batch scoring completed for {total} jobs")
        return results

    async def get_statistics(self, jobs: List[Job]) -> Dict[str, float]:
        """ジョブリストの統計情報を取得"""
        if not jobs:
            return {"mean": 0, "std": 0, "min": 0, "max": 0}

        clicks = [getattr(j, "application_clicks", 0) for j in jobs]
        return {
            "mean": float(np.mean(clicks)),
            "std": float(np.std(clicks)),
            "min": float(np.min(clicks)),
            "max": float(np.max(clicks)),
            "count": len(jobs)
        }