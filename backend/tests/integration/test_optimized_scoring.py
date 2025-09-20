#!/usr/bin/env python3
"""
T021: 最適化版スコアリングの統合テスト
元の実装との互換性を確認
"""

import asyncio
from app.services.basic_scoring import BasicScoringService
from app.services.basic_scoring_optimized import OptimizedBasicScoringService

# モックジョブクラス
class MockJob:
    def __init__(self, job_id, fee, hourly_wage, application_clicks):
        self.job_id = job_id
        self.fee = fee
        self.hourly_wage = hourly_wage
        self.application_clicks = application_clicks


async def test_compatibility():
    """元の実装との互換性テスト"""
    print("=" * 60)
    print("T021: 最適化版との互換性テスト")
    print("=" * 60)

    # サービスインスタンス
    original_service = BasicScoringService()
    optimized_service = OptimizedBasicScoringService()

    # テストケース
    test_jobs = [
        MockJob("TEST_001", 500, 1000, 50),    # 閾値境界
        MockJob("TEST_002", 1000, 1500, 100),  # 通常値
        MockJob("TEST_003", 5000, 3000, 200),  # 高値
        MockJob("TEST_004", 10000, 5000, 500), # 最大値超え
        MockJob("TEST_005", 0, 0, 0),          # ゼロ値
    ]

    print("\n📊 単体スコア計算の互換性チェック:")
    print("-" * 40)

    for job in test_jobs:
        # 元の実装
        orig_fee = await original_service.calculate_fee_score(job)
        orig_wage = await original_service.calculate_hourly_wage_score(job)
        orig_popularity = await original_service.calculate_company_popularity_score(
            job, 100, 50
        )
        orig_combined = await original_service.calculate_combined_score(job, 100, 50)

        # 最適化版
        opt_fee = await optimized_service.calculate_fee_score(job)
        opt_wage = await optimized_service.calculate_hourly_wage_score(job)
        opt_popularity = await optimized_service.calculate_company_popularity_score(
            job, 100, 50
        )
        opt_combined = await optimized_service.calculate_combined_score(job, 100, 50)

        # 比較
        fee_match = abs(orig_fee - opt_fee) < 0.01
        wage_match = abs(orig_wage - opt_wage) < 0.01
        popularity_match = abs(orig_popularity - opt_popularity) < 0.01
        combined_match = abs(orig_combined - opt_combined) < 0.01

        status = "✅" if all([fee_match, wage_match, popularity_match, combined_match]) else "❌"

        print(f"{status} {job.job_id}:")
        print(f"   Fee: {orig_fee:.1f} vs {opt_fee:.1f} {'✓' if fee_match else '✗'}")
        print(f"   Wage: {orig_wage:.1f} vs {opt_wage:.1f} {'✓' if wage_match else '✗'}")
        print(f"   Popularity: {orig_popularity:.1f} vs {opt_popularity:.1f} {'✓' if popularity_match else '✗'}")
        print(f"   Combined: {orig_combined:.1f} vs {opt_combined:.1f} {'✓' if combined_match else '✗'}")

    # バッチ処理テスト
    print("\n📊 バッチ処理テスト:")
    print("-" * 40)

    batch_jobs = [
        MockJob(f"BATCH_{i:03d}", 500 + i * 100, 1000 + i * 50, 50 + i * 10)
        for i in range(100)
    ]

    # バッチ処理実行
    batch_results = await optimized_service.batch_calculate_scores(batch_jobs)

    print(f"✅ バッチ処理完了: {len(batch_results)} jobs")
    print(f"   サンプル結果:")
    for result in batch_results[:3]:
        print(f"   - {result.job_id}: Combined={result.combined_score:.1f}")

    # 統計情報テスト
    stats = await optimized_service.get_statistics(batch_jobs)
    print(f"\n📊 統計情報:")
    print(f"   Mean clicks: {stats['mean']:.1f}")
    print(f"   Std clicks: {stats['std']:.1f}")
    print(f"   Min/Max: {stats['min']:.0f} - {stats['max']:.0f}")

    print("\n" + "=" * 60)
    print("✅ 互換性テスト完了")


if __name__ == "__main__":
    asyncio.run(test_compatibility())