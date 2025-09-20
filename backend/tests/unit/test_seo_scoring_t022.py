#!/usr/bin/env python3
"""
T022: SEOスコア計算のテスト (RED Phase)
semrush_keywordsとのマッチングによるスコアリング
"""

import pytest
from typing import List, Dict
import asyncio


class TestSEOScoring:
    """SEOスコア計算のテストスイート"""

    @pytest.fixture
    def sample_job_data(self):
        """サンプルジョブデータ"""
        return {
            "job_id": "TEST_001",
            "title": "軽作業スタッフ募集 未経験OK 高時給",
            "description": "倉庫での仕分け作業、梱包作業のお仕事です。未経験者歓迎、研修制度あり。",
            "catch_copy": "カンタン作業で高収入！",
            "semrush_keywords": ["軽作業", "未経験", "高時給", "倉庫", "仕分け"]
        }

    @pytest.fixture
    def keyword_variations(self):
        """キーワードバリエーション辞書"""
        return {
            "軽作業": ["軽作業", "かんたん作業", "カンタン作業", "簡単作業"],
            "未経験": ["未経験", "未経験者", "経験不問", "初心者"],
            "高時給": ["高時給", "高収入", "時給高め"],
            "倉庫": ["倉庫", "物流", "配送センター"],
            "仕分け": ["仕分け", "仕分", "ピッキング"]
        }

    def test_exact_keyword_match(self, sample_job_data):
        """完全一致キーワードのスコア計算テスト"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        # タイトルに「軽作業」「未経験」「高時給」が含まれる
        score = asyncio.run(service.calculate_title_match_score(
            sample_job_data["title"],
            sample_job_data["semrush_keywords"]
        ))

        # 3/5キーワードがマッチ = 60点期待
        assert score >= 60.0
        assert score <= 100.0

    def test_keyword_variations(self, sample_job_data, keyword_variations):
        """キーワードバリエーションの認識テスト"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        # 「カンタン作業」は「軽作業」のバリエーション
        test_title = "カンタン作業で稼げる！初心者歓迎"

        score = asyncio.run(service.calculate_with_variations(
            test_title,
            ["軽作業", "未経験"],
            keyword_variations
        ))

        # バリエーションも含めてマッチするはず
        assert score > 0

    def test_description_keyword_density(self, sample_job_data):
        """説明文のキーワード密度テスト"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        density = asyncio.run(service.calculate_keyword_density(
            sample_job_data["description"],
            sample_job_data["semrush_keywords"]
        ))

        # 適切な密度範囲（2-5%）
        assert 0.0 <= density <= 10.0

    def test_title_weight_higher_than_description(self):
        """タイトルの重みが説明文より高いことの確認"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        # タイトルのみにキーワード
        title_only = asyncio.run(service.calculate_combined_seo_score(
            title="軽作業スタッフ募集",
            description="お仕事の詳細です",
            keywords=["軽作業"]
        ))

        # 説明文のみにキーワード
        desc_only = asyncio.run(service.calculate_combined_seo_score(
            title="スタッフ募集",
            description="軽作業のお仕事です",
            keywords=["軽作業"]
        ))

        # タイトルマッチの方が高スコア
        assert title_only > desc_only

    def test_multiple_keyword_occurrence_bonus(self):
        """複数キーワード出現時のボーナステスト"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        # 1キーワードのみ
        single = asyncio.run(service.calculate_combined_seo_score(
            title="軽作業スタッフ",
            description="",
            keywords=["軽作業", "未経験", "高時給"]
        ))

        # 3キーワード全て
        multiple = asyncio.run(service.calculate_combined_seo_score(
            title="軽作業 未経験OK 高時給",
            description="",
            keywords=["軽作業", "未経験", "高時給"]
        ))

        # 複数マッチの方が高スコア
        assert multiple > single * 3

    def test_catch_copy_contribution(self, sample_job_data):
        """キャッチコピーのスコア寄与テスト"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        # キャッチコピーありなし比較
        with_catch = asyncio.run(service.calculate_with_catch_copy(
            title=sample_job_data["title"],
            description=sample_job_data["description"],
            catch_copy=sample_job_data["catch_copy"],
            keywords=sample_job_data["semrush_keywords"]
        ))

        without_catch = asyncio.run(service.calculate_combined_seo_score(
            title=sample_job_data["title"],
            description=sample_job_data["description"],
            keywords=sample_job_data["semrush_keywords"]
        ))

        # キャッチコピーがあると少し高い
        assert with_catch >= without_catch

    def test_empty_keywords_handling(self):
        """空キーワードリストのハンドリング"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        score = asyncio.run(service.calculate_combined_seo_score(
            title="求人タイトル",
            description="求人説明",
            keywords=[]
        ))

        # 空の場合はデフォルトスコア
        assert score == 50.0  # 中間スコア

    def test_normalization_and_preprocessing(self):
        """テキスト正規化と前処理のテスト"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        # 全角半角、大文字小文字の統一
        score1 = asyncio.run(service.calculate_title_match_score(
            "カンタン作業",
            ["かんたん作業"]
        ))

        score2 = asyncio.run(service.calculate_title_match_score(
            "ｶﾝﾀﾝ作業",
            ["カンタン作業"]
        ))

        # 正規化により同じスコアになるはず
        assert abs(score1 - score2) < 0.01

    def test_seo_score_range(self):
        """SEOスコアが0-100の範囲内であることの確認"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        test_cases = [
            ("", "", []),  # 空データ
            ("test", "test", ["test"]),  # 完全一致
            ("abc", "def", ["xyz"]),  # 完全不一致
        ]

        for title, desc, keywords in test_cases:
            score = asyncio.run(service.calculate_combined_seo_score(
                title=title,
                description=desc,
                keywords=keywords
            ))
            assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_batch_processing_capability(self):
        """バッチ処理能力のテスト"""
        from app.services.seo_scoring import SEOScoringService

        service = SEOScoringService()

        # 100件のジョブデータ
        jobs = [
            {
                "job_id": f"JOB_{i:03d}",
                "title": f"求人タイトル{i}",
                "description": f"説明文{i}",
                "keywords": ["キーワード1", "キーワード2"]
            }
            for i in range(100)
        ]

        # バッチ処理
        results = await service.batch_calculate_seo_scores(jobs)

        assert len(results) == 100
        for result in results:
            assert "job_id" in result
            assert "seo_score" in result
            assert 0.0 <= result["seo_score"] <= 100.0


if __name__ == "__main__":
    # RED Phase: これらのテストは全て失敗するはず
    pytest.main([__file__, "-v", "--tb=short"])