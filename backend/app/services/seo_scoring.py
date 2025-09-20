#!/usr/bin/env python3
"""
T022: SEO Scoring Service (REFACTOR Phase)

Provides keyword-based scoring functionality using SEMrush keyword data.
Calculates scores based on keyword matching in job fields with weighted priorities.
Refactored for improved code quality and maintainability.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import unicodedata
import re

from app.models.job import Job

logger = logging.getLogger(__name__)


@dataclass
class SEOConfig:
    """Configuration for SEO scoring"""
    field_weights: Dict[str, float]
    default_search_volume: int = 1000
    volume_normalization_factor: int = 10000
    score_multiplier: int = 100
    max_score: int = 100
    title_weight: float = 0.7
    description_weight: float = 0.3
    catch_copy_weight: float = 0.1
    multiple_keyword_bonus: float = 1.2
    keyword_density_limit: float = 10.0

class SEOScoringService:
    """Service for calculating SEO-based job scores."""

    # Default field weight constants for SEO scoring
    DEFAULT_FIELD_WEIGHTS = {
        "application_name": 1.5,  # Highest priority
        "title": 1.2,              # High priority
        "description": 1.0,         # Normal priority
        "company": 0.8              # Lower priority
    }

    def __init__(self, config: Optional[SEOConfig] = None):
        """Initialize SEO scoring service with optional configuration.

        Args:
            config: Optional SEO configuration. Uses defaults if not provided.
        """
        if config is None:
            config = SEOConfig(
                field_weights=self.DEFAULT_FIELD_WEIGHTS.copy(),
            )
        self.config = config
        self.field_weights = config.field_weights
        logger.info("SEOScoringService initialized with config: %s", self.config)

    def _normalize_text(self, text: str) -> str:
        """Advanced text normalization for consistent matching.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Unicode normalization (全角→半角変換)
        text = unicodedata.normalize('NFKC', text)

        # Convert to lowercase
        text = text.lower()

        # Convert hiragana to katakana for Japanese text
        hiragana_to_katakana = str.maketrans(
            'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろわをん',
            'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロワヲン'
        )
        text = text.translate(hiragana_to_katakana)

        # Replace common separators with spaces for better matching
        text = re.sub(r'[-_]+', ' ', text)

        return text.strip()

    async def normalize_keywords(self, keywords: List[str]) -> List[str]:
        """Normalize keywords for consistent matching.

        Args:
            keywords: List of raw keywords

        Returns:
            List of normalized keywords
        """
        try:
            normalized = []
            for keyword in keywords:
                if keyword:
                    normalized_keyword = self._normalize_text(keyword)
                    if normalized_keyword and normalized_keyword not in normalized:
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

    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords match in the text.

        Args:
            text: Text to search in
            keywords: Keywords to search for

        Returns:
            Number of matching keywords
        """
        if not text or not keywords:
            return 0

        normalized_text = self._normalize_text(text)
        matches = 0

        for keyword in keywords:
            normalized_keyword = self._normalize_text(keyword)
            if normalized_keyword and normalized_keyword in normalized_text:
                matches += 1

        return matches

    async def calculate_seo_score(self, job: Job, semrush_keywords: List[Dict[str, Any]]) -> float:
        """Calculate SEO score for a job based on keyword matching.

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
            # Extract keywords from SEMrush data
            keywords = []
            for kw_data in semrush_keywords:
                if isinstance(kw_data, dict):
                    keyword = kw_data.get("keyword", "")
                    if keyword:
                        keywords.append(keyword)

            if not keywords:
                return 0.0

            # Get job text fields
            title = getattr(job, "title", "") or ""
            description = getattr(job, "description", "") or ""

            # Use the combined SEO score calculation
            return await self.calculate_combined_seo_score(title, description, keywords)

        except Exception as e:
            logger.error("Error calculating SEO score: %s", e)
            return 0.0

    # Methods required for test compatibility

    async def calculate_title_match_score(self, title: str, keywords: List[str]) -> float:
        """Calculate keyword matching score for title.

        Args:
            title: Job title text
            keywords: Keywords to match

        Returns:
            Score between 0 and 100
        """
        if not keywords:
            return 0.0

        matches = self._count_keyword_matches(title, keywords)
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
        """Calculate keyword density in text.

        Args:
            description: Text to analyze
            keywords: Keywords to count

        Returns:
            Keyword density percentage (max 10%)
        """
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

        density = (keyword_count / word_count) * 100
        return min(density, self.config.keyword_density_limit)

    async def calculate_combined_seo_score(
        self,
        title: str,
        description: str,
        keywords: List[str]
    ) -> float:
        """Calculate combined SEO score from title and description.

        Args:
            title: Job title
            description: Job description
            keywords: Keywords to match

        Returns:
            Combined SEO score between 0 and 100
        """
        if not keywords:
            return 50.0  # Default score for no keywords

        # Calculate title score
        title_score = await self.calculate_title_match_score(title, keywords)

        # Calculate description score
        desc_score = 0.0
        if description:
            desc_matches = self._count_keyword_matches(description, keywords)
            desc_score = (desc_matches / len(keywords)) * 100.0

        # Weighted combination
        combined = (
            title_score * self.config.title_weight +
            desc_score * self.config.description_weight
        )

        # Multiple keyword bonus
        if title and description:
            title_matches = self._count_keyword_matches(title, keywords)
            if title_matches >= 3:
                combined *= self.config.multiple_keyword_bonus

        return min(combined, float(self.config.max_score))

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
