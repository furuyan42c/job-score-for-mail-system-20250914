#!/usr/bin/env python3
"""
T021: 品質保証テスト - 基礎スコア計算
正確性と一貫性を検証
"""

import asyncio
import numpy as np
from typing import List, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.basic_scoring_optimized import OptimizedBasicScoringService, BatchScoringResult


class QualityTestJob:
    """品質テスト用ジョブクラス"""
    def __init__(self, job_id: str, fee: int, hourly_wage: int, application_clicks: int):
        self.job_id = job_id
        self.fee = fee
        self.hourly_wage = hourly_wage
        self.application_clicks = application_clicks


def validate_score_range(score: float) -> bool:
    """スコアが有効範囲内か確認"""
    return 0.0 <= score <= 100.0


def validate_consistency(results: List[BatchScoringResult]) -> Tuple[bool, str]:
    """結果の一貫性を検証"""
    errors = []

    for result in results:
        # 各スコアの範囲チェック
        if not validate_score_range(result.fee_score):
            errors.append(f"{result.job_id}: fee_score out of range: {result.fee_score}")
        if not validate_score_range(result.wage_score):
            errors.append(f"{result.job_id}: wage_score out of range: {result.wage_score}")
        if not validate_score_range(result.popularity_score):
            errors.append(f"{result.job_id}: popularity_score out of range: {result.popularity_score}")
        if not validate_score_range(result.combined_score):
            errors.append(f"{result.job_id}: combined_score out of range: {result.combined_score}")

        # 重み付け計算の検証
        expected_combined = (
            result.wage_score * 0.4 +
            result.fee_score * 0.3 +
            result.popularity_score * 0.3
        )
        if abs(result.combined_score - expected_combined) > 0.01:
            errors.append(
                f"{result.job_id}: combined score mismatch: "
                f"expected {expected_combined:.2f}, got {result.combined_score:.2f}"
            )

    return len(errors) == 0, "\n".join(errors)


async def test_edge_cases():
    """エッジケースのテスト"""
    print("📋 エッジケーステスト:")
    print("-" * 40)

    service = OptimizedBasicScoringService()

    # エッジケースのテストデータ
    edge_cases = [
        # (job_id, fee, hourly_wage, clicks, description)
        ("ZERO_VALUES", 0, 0, 0, "全ゼロ値"),
        ("MIN_THRESHOLD", 500, 1000, 0, "閾値境界"),
        ("JUST_ABOVE", 501, 1001, 1, "閾値直上"),
        ("MAX_VALUES", 10000, 5000, 10000, "最大値"),
        ("NEGATIVE_FEE", -100, 1500, 100, "負のfee"),
        ("HUGE_VALUES", 999999, 999999, 999999, "巨大値"),
    ]

    jobs = [QualityTestJob(ec[0], ec[1], ec[2], ec[3]) for ec in edge_cases]
    results = await service.batch_calculate_scores(jobs)

    print("結果:")
    for i, result in enumerate(results):
        desc = edge_cases[i][4]
        print(f"  {result.job_id} ({desc}):")
        print(f"    Fee: {result.fee_score:.1f}, Wage: {result.wage_score:.1f}, "
              f"Pop: {result.popularity_score:.1f}, Combined: {result.combined_score:.1f}")

        # 負の値チェック
        assert result.fee_score >= 0, f"Negative fee score: {result.fee_score}"
        assert result.wage_score >= 0, f"Negative wage score: {result.wage_score}"
        assert result.popularity_score >= 0, f"Negative popularity score: {result.popularity_score}"
        assert result.combined_score >= 0, f"Negative combined score: {result.combined_score}"

    print("✅ エッジケーステスト合格")
    return True


async def test_statistical_distribution():
    """統計的分布のテスト"""
    print("\n📊 統計的分布テスト:")
    print("-" * 40)

    service = OptimizedBasicScoringService()

    # 正規分布に従うテストデータ生成
    np.random.seed(42)
    n_samples = 10000

    # 現実的な分布のシミュレーション
    fees = np.random.gamma(2, 1000, n_samples).clip(0, 10000)
    wages = np.random.normal(1500, 500, n_samples).clip(800, 3000)
    clicks = np.random.poisson(100, n_samples)

    jobs = [
        QualityTestJob(f"STAT_{i:05d}", int(fees[i]), int(wages[i]), int(clicks[i]))
        for i in range(n_samples)
    ]

    # バッチ処理実行
    results = await service.batch_calculate_scores(jobs)

    # 統計情報収集
    combined_scores = [r.combined_score for r in results]
    mean_score = np.mean(combined_scores)
    std_score = np.std(combined_scores)
    min_score = np.min(combined_scores)
    max_score = np.max(combined_scores)

    print(f"総合スコア統計:")
    print(f"  平均: {mean_score:.2f}")
    print(f"  標準偏差: {std_score:.2f}")
    print(f"  最小値: {min_score:.2f}")
    print(f"  最大値: {max_score:.2f}")

    # 分布の妥当性チェック
    assert 20 <= mean_score <= 80, f"Mean score out of expected range: {mean_score}"
    assert 5 <= std_score <= 30, f"Std deviation out of expected range: {std_score}"
    assert min_score >= 0, f"Minimum score negative: {min_score}"
    assert max_score <= 100, f"Maximum score exceeds 100: {max_score}"

    # パーセンタイル分析
    percentiles = [0, 25, 50, 75, 100]
    pct_values = np.percentile(combined_scores, percentiles)
    print(f"\nパーセンタイル:")
    for p, v in zip(percentiles, pct_values):
        print(f"  {p}%: {v:.2f}")

    print("✅ 統計的分布テスト合格")
    return True


async def test_deterministic_behavior():
    """決定論的動作のテスト（同じ入力→同じ出力）"""
    print("\n🔒 決定論的動作テスト:")
    print("-" * 40)

    service = OptimizedBasicScoringService()

    # テストデータ
    test_jobs = [
        QualityTestJob("DET_001", 1000, 1500, 100),
        QualityTestJob("DET_002", 2000, 2000, 200),
        QualityTestJob("DET_003", 3000, 2500, 150),
    ]

    # 10回実行して結果が同じか確認
    all_results = []
    for run in range(10):
        results = await service.batch_calculate_scores(test_jobs)
        all_results.append(results)

    # 結果の一貫性確認
    for i in range(1, 10):
        for j, job in enumerate(test_jobs):
            r1 = all_results[0][j]
            r2 = all_results[i][j]

            assert r1.fee_score == r2.fee_score, f"Fee score mismatch in run {i}"
            assert r1.wage_score == r2.wage_score, f"Wage score mismatch in run {i}"
            assert r1.popularity_score == r2.popularity_score, f"Popularity score mismatch in run {i}"
            assert r1.combined_score == r2.combined_score, f"Combined score mismatch in run {i}"

    print(f"✅ 10回実行で完全一致を確認")
    return True


async def test_boundary_conditions():
    """境界値テスト"""
    print("\n🔍 境界値テスト:")
    print("-" * 40)

    service = OptimizedBasicScoringService()

    # 境界値のテストケース
    boundary_cases = [
        # fee境界（500が閾値）
        (499, 1500, 100, "Fee境界下"),
        (500, 1500, 100, "Fee境界"),
        (501, 1500, 100, "Fee境界上"),
        # wage境界（1000が閾値）
        (1000, 999, 100, "Wage境界下"),
        (1000, 1000, 100, "Wage境界"),
        (1000, 1001, 100, "Wage境界上"),
        # 最大値テスト
        (5000, 3000, 1000, "Fee/Wage最大値"),
        (10000, 5000, 2000, "超最大値"),
    ]

    for fee, wage, clicks, desc in boundary_cases:
        job = QualityTestJob(f"BOUNDARY_{desc}", fee, wage, clicks)
        results = await service.batch_calculate_scores([job])
        result = results[0]

        print(f"{desc}:")
        print(f"  入力: fee={fee}, wage={wage}, clicks={clicks}")
        print(f"  出力: fee_score={result.fee_score:.1f}, "
              f"wage_score={result.wage_score:.1f}, "
              f"combined={result.combined_score:.1f}")

        # 境界値での正しい動作確認
        if fee <= 500:
            assert result.fee_score == 0.0, f"Fee score should be 0 for fee={fee}"
        if wage <= 1000:
            assert result.wage_score == 0.0, f"Wage score should be 0 for wage={wage}"

    print("✅ 境界値テスト合格")
    return True


async def run_quality_tests():
    """全品質テスト実行"""
    print("=" * 60)
    print("T021: 基礎スコア計算 - 品質保証テスト")
    print("=" * 60)

    tests = [
        ("エッジケース", test_edge_cases),
        ("統計的分布", test_statistical_distribution),
        ("決定論的動作", test_deterministic_behavior),
        ("境界値条件", test_boundary_conditions),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {name}テスト失敗: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 テスト結果: {passed}/{len(tests)} 合格")

    if failed == 0:
        print("🎉 全品質テスト合格！")
        return True
    else:
        print(f"⚠️ {failed}個のテストが失敗しました")
        return False


if __name__ == "__main__":
    result = asyncio.run(run_quality_tests())
    sys.exit(0 if result else 1)