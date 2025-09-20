#!/usr/bin/env python3
"""
T021: パフォーマンステスト - 基礎スコア計算
目標: 10万件を5分以内で処理
"""

import asyncio
import time
from typing import List
import numpy as np
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobData:
    """軽量なジョブデータクラス"""
    job_id: str
    fee: int
    hourly_wage: int
    application_clicks: int

class OptimizedBasicScoring:
    """最適化された基礎スコア計算"""

    # 定数を事前計算
    FEE_THRESHOLD = 500
    FEE_MAX = 5000
    FEE_SCALE = 100.0 / (FEE_MAX - FEE_THRESHOLD)

    WAGE_THRESHOLD = 1000
    WAGE_MAX = 3000
    WAGE_SCALE = 100.0 / (WAGE_MAX - WAGE_THRESHOLD)

    @classmethod
    def calculate_fee_score_vectorized(cls, fees: np.ndarray) -> np.ndarray:
        """ベクトル化されたfeeスコア計算"""
        # NumPy配列での一括処理
        scores = np.zeros_like(fees, dtype=np.float32)
        valid = fees > cls.FEE_THRESHOLD
        scores[valid] = np.minimum(
            (fees[valid] - cls.FEE_THRESHOLD) * cls.FEE_SCALE,
            100.0
        )
        return scores

    @classmethod
    def calculate_wage_score_vectorized(cls, wages: np.ndarray) -> np.ndarray:
        """ベクトル化された時給スコア計算"""
        scores = np.zeros_like(wages, dtype=np.float32)
        valid = wages > cls.WAGE_THRESHOLD
        scores[valid] = np.minimum(
            (wages[valid] - cls.WAGE_THRESHOLD) * cls.WAGE_SCALE,
            100.0
        )
        return scores

    @classmethod
    def calculate_popularity_score_vectorized(
        cls,
        clicks: np.ndarray,
        mean: float,
        std: float
    ) -> np.ndarray:
        """ベクトル化された人気度スコア計算"""
        if std == 0:
            return np.full_like(clicks, 50.0, dtype=np.float32)

        # Z-scoreの一括計算
        z_scores = (clicks - mean) / std
        # -3 to 3を0 to 100にマップ
        scores = ((z_scores + 3) / 6) * 100
        return np.clip(scores, 0, 100).astype(np.float32)

    @classmethod
    def batch_calculate_scores(cls, jobs: List[JobData], batch_size: int = 10000) -> dict:
        """バッチ処理での高速スコア計算"""
        results = {}
        total = len(jobs)

        # NumPy配列に変換
        fees = np.array([j.fee for j in jobs], dtype=np.float32)
        wages = np.array([j.hourly_wage for j in jobs], dtype=np.float32)
        clicks = np.array([j.application_clicks for j in jobs], dtype=np.float32)

        # 統計値の事前計算
        clicks_mean = np.mean(clicks)
        clicks_std = np.std(clicks)

        # バッチごとに処理
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            batch_slice = slice(i, end_idx)

            # ベクトル化計算
            fee_scores = cls.calculate_fee_score_vectorized(fees[batch_slice])
            wage_scores = cls.calculate_wage_score_vectorized(wages[batch_slice])
            popularity_scores = cls.calculate_popularity_score_vectorized(
                clicks[batch_slice], clicks_mean, clicks_std
            )

            # 重み付け合計（ベクトル演算）
            # 時給40%, fee30%, 人気度30%
            combined_scores = (
                wage_scores * 0.4 +
                fee_scores * 0.3 +
                popularity_scores * 0.3
            )

            # 結果を辞書に格納
            for j, idx in enumerate(range(i, end_idx)):
                results[jobs[idx].job_id] = {
                    'fee_score': float(fee_scores[j]),
                    'wage_score': float(wage_scores[j]),
                    'popularity_score': float(popularity_scores[j]),
                    'combined_score': float(combined_scores[j])
                }

        return results


def generate_test_data(n: int) -> List[JobData]:
    """テスト用ダミーデータ生成"""
    np.random.seed(42)
    jobs = []
    for i in range(n):
        job = JobData(
            job_id=f"JOB_{i:06d}",
            fee=np.random.randint(0, 10000),
            hourly_wage=np.random.randint(800, 3000),
            application_clicks=np.random.poisson(100)  # ポアソン分布で現実的なクリック数
        )
        jobs.append(job)
    return jobs


def run_performance_test():
    """パフォーマンステスト実行"""
    print("=" * 60)
    print("T021: 基礎スコア計算パフォーマンステスト")
    print("=" * 60)

    # テストケース
    test_cases = [
        (1000, "Small dataset"),
        (10000, "Medium dataset"),
        (100000, "Target dataset (100K)"),
    ]

    for n_jobs, description in test_cases:
        print(f"\n📊 {description}: {n_jobs:,} jobs")
        print("-" * 40)

        # データ生成
        jobs = generate_test_data(n_jobs)

        # 最適化版の測定
        start_time = time.time()
        results = OptimizedBasicScoring.batch_calculate_scores(jobs)
        elapsed = time.time() - start_time

        # 結果表示
        throughput = n_jobs / elapsed if elapsed > 0 else 0
        print(f"✅ 処理時間: {elapsed:.2f}秒")
        print(f"✅ スループット: {throughput:,.0f} jobs/sec")

        # 目標達成チェック
        if n_jobs == 100000:
            target_seconds = 300  # 5分 = 300秒
            if elapsed <= target_seconds:
                print(f"🎉 目標達成! ({elapsed:.2f}秒 < {target_seconds}秒)")
            else:
                print(f"⚠️ 目標未達成 ({elapsed:.2f}秒 > {target_seconds}秒)")

        # サンプル結果表示
        sample_ids = list(results.keys())[:3]
        print(f"\n📈 サンプル結果:")
        for job_id in sample_ids:
            scores = results[job_id]
            print(f"  {job_id}: Combined={scores['combined_score']:.1f}, "
                  f"Fee={scores['fee_score']:.1f}, "
                  f"Wage={scores['wage_score']:.1f}, "
                  f"Popularity={scores['popularity_score']:.1f}")

    print("\n" + "=" * 60)
    print("テスト完了")


if __name__ == "__main__":
    run_performance_test()