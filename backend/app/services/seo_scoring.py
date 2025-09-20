#!/usr/bin/env python3
"""
T022: SEO Scoring Service (GREEN Phase)

Provides keyword-based scoring functionality using SEMrush keyword data.
Calculates scores based on keyword matching in job fields with weighted priorities.
Updated with minimal implementation to pass tests.
"""
import logging
from typing import List, Dict, Any, Optional
from app.models.job import Job
import unicodedata
import re

logger = logging.getLogger(__name__)

class SEOScoringService:
    """Service for calculating SEO-based job scores."""

    # Field weight constants for SEO scoring
    FIELD_WEIGHTS = {
        "application_name": 1.5,  # Highest priority
        "title": 1.2,              # High priority
        "description": 1.0,         # Normal priority
        "company": 0.8              # Lower priority
    }

    # Scoring parameters
    DEFAULT_SEARCH_VOLUME = 1000
    VOLUME_NORMALIZATION_FACTOR = 10000
    SCORE_MULTIPLIER = 100
    MAX_SCORE = 100

    def __init__(self):
        """Initialize SEO scoring service."""
        self.field_weights = self.FIELD_WEIGHTS.copy()
        logger.info("SEOScoringService initialized with field weights: %s", self.field_weights)

    async def normalize_keywords(self, keywords: List[str]) -> List[str]:
        """
        Normalize keywords for consistent matching.

        Args:
            keywords: List of raw keywords

        Returns:
            List of normalized keywords
        """
        try:
            normalized = []
            for keyword in keywords:
                if keyword:
                    normalized_keyword = keyword.lower().replace("-", " ").replace("_", " ").strip()
                    if normalized_keyword:
                        normalized.append(normalized_keyword)
            return normalized
        except Exception as e:
            logger.error("Error normalizing keywords: %s", e)
            return []

    async def generate_variations(self, keyword: str) -> List[str]:
        """
        Generate keyword variations for broader matching.

        Args:
            keyword: Base keyword

        Returns:
            List of keyword variations
        """
        if not keyword:
            return []

        try:
            variations = [keyword]

            # Add common variations
            if " " in keyword:
                variations.extend([
                    keyword.replace(" ", "-"),
                    keyword.replace(" ", "_"),
                    keyword.replace(" ", "")
                ])

            # Remove duplicates while preserving order
            seen = set()
            unique_variations = []
            for var in variations:
                if var not in seen:
                    seen.add(var)
                    unique_variations.append(var)

            return unique_variations
        except Exception as e:
            logger.error("Error generating keyword variations: %s", e)
            return [keyword]

    async def calculate_seo_score(self, job: Job, semrush_keywords: List[Dict[str, Any]]) -> float:
        """
        Calculate SEO score for a job based on keyword matching.

        Args:
            job: Job object to score
            semrush_keywords: List of SEMrush keyword data with 'keyword' and 'search_volume'

        Returns:
            SEO score between 0 and 100
        """
        if not semrush_keywords:
            logger.debug("No SEMrush keywords provided for job %s", getattr(job, 'job_id', 'unknown'))
            return 0.0

        try:
            total_score = 0.0

            for kw_data in semrush_keywords:
                if not isinstance(kw_data, dict):
                    continue

                keyword = kw_data.get("keyword", "")
                if not keyword:
                    continue

                keyword = keyword.lower()
                search_volume = kw_data.get("search_volume", self.DEFAULT_SEARCH_VOLUME)

                # Calculate field scores
                field_scores = []

                # Check application name
                if hasattr(job, "application_name") and job.application_name:
                    if keyword in job.application_name.lower():
                        field_scores.append(self.field_weights["application_name"])

                # Check title
                if hasattr(job, "title") and job.title:
                    if keyword in job.title.lower():
                        field_scores.append(self.field_weights["title"])

                # Check description
                if hasattr(job, "description") and job.description:
                    if keyword in job.description.lower():
                        field_scores.append(self.field_weights["description"])

                # Check company
                if hasattr(job, "company") and job.company:
                    if keyword in job.company.lower():
                        field_scores.append(self.field_weights["company"])

                # Apply highest matching score
                if field_scores:
                    volume_factor = min(search_volume / self.VOLUME_NORMALIZATION_FACTOR, 1.0)
                    keyword_score = max(field_scores) * volume_factor * self.SCORE_MULTIPLIER
                    total_score += keyword_score
                    logger.debug("Keyword '%s' matched with score %.2f", keyword, keyword_score)

            final_score = min(self.MAX_SCORE, total_score)
            logger.info("SEO score for job %s: %.2f", getattr(job, 'job_id', 'unknown'), final_score)
            return final_score

        except Exception as e:
            logger.error("Error calculating SEO score: %s", e)
            return 0.0

    # New methods for T022 GREEN phase - minimal implementation to pass tests

    def _normalize_text(self, text: str) -> str:
        """テキスト正規化（全角半角、大文字小文字の統一）"""
        # 全角を半角に変換
        text = unicodedata.normalize('NFKC', text)
        # 小文字に変換
        text = text.lower()
        # ひらがなをカタカナに統一
        text = text.translate(str.maketrans('ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろわをん',
                                           'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロワヲン'))
        return text

    async def calculate_title_match_score(self, title: str, keywords: List[str]) -> float:
        """タイトルとキーワードのマッチングスコア計算"""
        if not keywords:
            return 0.0

        normalized_title = self._normalize_text(title)
        matches = 0

        for keyword in keywords:
            normalized_keyword = self._normalize_text(keyword)
            if normalized_keyword in normalized_title:
                matches += 1

        # マッチ率をスコアに変換（0-100）
        return (matches / len(keywords)) * 100.0

    async def calculate_with_variations(
        self,
        text: str,
        keywords: List[str],
        variations: Dict[str, List[str]]
    ) -> float:
        """キーワードバリエーションを考慮したスコア計算"""
        normalized_text = self._normalize_text(text)
        matches = 0

        for keyword in keywords:
            # バリエーションがある場合
            if keyword in variations:
                for variant in variations[keyword]:
                    normalized_variant = self._normalize_text(variant)
                    if normalized_variant in normalized_text:
                        matches += 1
                        break  # 1つでもマッチしたらOK
            else:
                # バリエーションがない場合は通常マッチング
                normalized_keyword = self._normalize_text(keyword)
                if normalized_keyword in normalized_text:
                    matches += 1

        if not keywords:
            return 0.0

        return (matches / len(keywords)) * 100.0

    async def calculate_keyword_density(
        self,
        description: str,
        keywords: List[str]
    ) -> float:
        """キーワード密度の計算"""
        if not description or not keywords:
            return 0.0

        normalized_desc = self._normalize_text(description)
        word_count = len(normalized_desc.split())

        if word_count == 0:
            return 0.0

        keyword_count = 0
        for keyword in keywords:
            normalized_keyword = self._normalize_text(keyword)
            keyword_count += normalized_desc.count(normalized_keyword)

        # 密度をパーセンテージで返す
        density = (keyword_count / word_count) * 100
        return min(density, 10.0)  # 最大10%に制限

    async def calculate_combined_seo_score(
        self,
        title: str,
        description: str,
        keywords: List[str]
    ) -> float:
        """タイトルと説明文を組み合わせたSEOスコア計算"""
        if not keywords:
            return 50.0  # デフォルトスコア

        # タイトルスコア（重み70%）
        title_score = await self.calculate_title_match_score(title, keywords)

        # 説明文スコア（重み30%）
        desc_score = 0.0
        if description:
            normalized_desc = self._normalize_text(description)
            matches = 0
            for keyword in keywords:
                normalized_keyword = self._normalize_text(keyword)
                if normalized_keyword in normalized_desc:
                    matches += 1
            desc_score = (matches / len(keywords)) * 100.0

        # 重み付け合計（タイトルの重みを高く）
        combined = title_score * 0.7 + desc_score * 0.3

        # 複数キーワードボーナス
        if title and description:
            title_matches = sum(1 for k in keywords if self._normalize_text(k) in self._normalize_text(title))
            if title_matches >= 3:
                combined *= 1.2  # 20%ボーナス

        return min(combined, 100.0)

    async def calculate_with_catch_copy(
        self,
        title: str,
        description: str,
        catch_copy: str,
        keywords: List[str]
    ) -> float:
        """キャッチコピーを含めたSEOスコア計算"""
        base_score = await self.calculate_combined_seo_score(title, description, keywords)

        if not catch_copy or not keywords:
            return base_score

        # キャッチコピーのスコア計算
        normalized_catch = self._normalize_text(catch_copy)
        matches = 0
        for keyword in keywords:
            normalized_keyword = self._normalize_text(keyword)
            if normalized_keyword in normalized_catch:
                matches += 1

        if matches > 0:
            # キャッチコピーにマッチがあればボーナスとして加算
            catch_bonus = (matches / len(keywords)) * 10.0  # 最大10ポイントのボーナス
            return min(base_score + catch_bonus, 100.0)

        return base_score

    async def batch_calculate_seo_scores(
        self,
        jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """バッチ処理でSEOスコアを計算"""
        results = []

        for job in jobs:
            title = job.get("title", "")
            description = job.get("description", "")
            keywords = job.get("keywords", [])

            score = await self.calculate_combined_seo_score(
                title, description, keywords
            )

            results.append({
                "job_id": job.get("job_id"),
                "seo_score": score
            })

        return results
