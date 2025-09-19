#!/usr/bin/env python3
"""
T091: SEO Score Calculation Script

Calculates SEO scores for jobs based on keyword matching:
- Matches job content with SEO keywords
- Considers search volume and difficulty
- Calculates relevance scores
- Updates jobs with SEO optimization potential

Usage:
    python scripts/calculate_seo_scores.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging
from datetime import datetime
import re
import unicodedata

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


class SEOScoreCalculator:
    """SEO score calculation handler"""

    def __init__(self):
        self.logger = setup_logging()
        self.batch_size = 100
        self.scores_calculated = 0
        self.keyword_cache = {}

    async def get_db_session(self) -> AsyncSession:
        """Create database session"""
        database_url = 'sqlite+aiosqlite:///./app/database.db'
        engine = create_async_engine(
            database_url,
            echo=False
        )
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session_maker()

    async def add_seo_columns(self, session: AsyncSession):
        """Add SEO score columns to jobs table if they don't exist"""
        try:
            # Check if columns exist
            result = await session.execute(
                text("PRAGMA table_info(jobs)")
            )
            columns = [row[1] for row in result.fetchall()]

            # Add SEO columns if missing
            seo_columns = [
                ('seo_score', 'REAL DEFAULT 0'),
                ('seo_keyword_matches', 'TEXT'),
                ('seo_total_volume', 'INTEGER DEFAULT 0'),
                ('seo_avg_difficulty', 'REAL DEFAULT 0'),
                ('seo_calculated_at', 'TIMESTAMP')
            ]

            for col_name, col_def in seo_columns:
                if col_name not in columns:
                    await session.execute(
                        text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_def}")
                    )
                    self.logger.info(f"Added column {col_name} to jobs table")

            await session.commit()

        except Exception as e:
            self.logger.error(f"Error adding SEO columns: {e}")
            await session.rollback()

    async def load_keywords(self, session: AsyncSession) -> Dict[str, Dict]:
        """Load SEO keywords into memory for efficient matching"""
        if self.keyword_cache:
            return self.keyword_cache

        result = await session.execute(
            text("SELECT keyword, search_volume, difficulty FROM seo_keywords")
        )

        keywords = result.fetchall()

        for keyword, volume, difficulty in keywords:
            # Normalize keyword for matching
            normalized_keyword = self.normalize_text(keyword)
            self.keyword_cache[normalized_keyword] = {
                'original': keyword,
                'volume': volume or 0,
                'difficulty': difficulty or 50.0
            }

        self.logger.info(f"Loaded {len(self.keyword_cache)} SEO keywords")
        return self.keyword_cache

    def normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove extra spaces
        text = ' '.join(text.split())

        # Normalize unicode characters (handle Japanese properly)
        text = unicodedata.normalize('NFKC', text)

        return text

    def extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract potential keywords from text"""
        if not text:
            return set()

        normalized = self.normalize_text(text)

        # Split by common delimiters
        words = re.split(r'[,、。！？\s\n\r]+', normalized)

        # Also create n-grams (2-3 word combinations)
        keywords = set(words)

        # Add bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            keywords.add(bigram)

        # Add trigrams
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            keywords.add(trigram)

        return keywords

    def find_keyword_matches(
        self,
        job_text: str,
        keywords: Dict[str, Dict]
    ) -> List[Dict]:
        """Find matching keywords in job text"""
        if not job_text:
            return []

        normalized_text = self.normalize_text(job_text)
        matches = []

        # Check each keyword
        for normalized_keyword, keyword_data in keywords.items():
            # Check if keyword appears in text
            if normalized_keyword in normalized_text:
                # Count occurrences
                occurrences = normalized_text.count(normalized_keyword)

                matches.append({
                    'keyword': keyword_data['original'],
                    'volume': keyword_data['volume'],
                    'difficulty': keyword_data['difficulty'],
                    'occurrences': occurrences
                })

        return matches

    def calculate_seo_score(
        self,
        matches: List[Dict]
    ) -> Tuple[float, int, float]:
        """
        Calculate SEO score based on keyword matches
        Returns: (seo_score, total_volume, avg_difficulty)
        """
        if not matches:
            return 0.0, 0, 0.0

        total_volume = 0
        weighted_difficulty_sum = 0
        score = 0.0

        for match in matches:
            volume = match['volume']
            difficulty = match['difficulty']
            occurrences = match['occurrences']

            # Add to totals
            total_volume += volume

            # Weight difficulty by volume
            weighted_difficulty_sum += difficulty * volume

            # Calculate score component for this keyword
            # Higher volume = better
            # Lower difficulty = better
            # More occurrences = better (but with diminishing returns)
            occurrence_factor = min(1.0, 0.5 + (occurrences * 0.25))  # Max 1.0

            # Score formula: volume weight * difficulty factor * occurrence factor
            volume_score = min(100, volume / 1000)  # Normalize to 0-100
            difficulty_factor = max(0.1, (100 - difficulty) / 100)  # 0.1 to 1.0

            keyword_score = volume_score * difficulty_factor * occurrence_factor

            score += keyword_score

        # Calculate average difficulty
        avg_difficulty = weighted_difficulty_sum / total_volume if total_volume > 0 else 50.0

        # Normalize score to 0-100 range
        # Score can theoretically be higher than 100 if many keywords match
        final_score = min(100, score)

        return round(final_score, 2), total_volume, round(avg_difficulty, 2)

    async def calculate_job_seo_scores(
        self,
        session: AsyncSession,
        offset: int = 0
    ) -> int:
        """Calculate SEO scores for a batch of jobs"""
        # Get batch of jobs
        result = await session.execute(
            text(f"""
                SELECT id, job_id, company_name, job_contents, job_contents_detail,
                       area, employment_type, requirement, welfare
                FROM jobs
                LIMIT {self.batch_size} OFFSET {offset}
            """)
        )

        jobs = result.fetchall()

        for job in jobs:
            # Combine all searchable text
            searchable_text = ' '.join(filter(None, [
                str(job[2]) if job[2] else '',  # company_name
                str(job[3]) if job[3] else '',  # job_contents
                str(job[4]) if job[4] else '',  # job_contents_detail
                str(job[5]) if job[5] else '',  # area
                str(job[6]) if job[6] else '',  # employment_type
                str(job[7]) if job[7] else '',  # requirement
                str(job[8]) if job[8] else ''   # welfare
            ]))

            # Find keyword matches
            matches = self.find_keyword_matches(searchable_text, self.keyword_cache)

            # Calculate SEO score
            seo_score, total_volume, avg_difficulty = self.calculate_seo_score(matches)

            # Prepare matched keywords for storage (top 5 by volume)
            top_keywords = sorted(matches, key=lambda x: x['volume'], reverse=True)[:5]
            keyword_matches_json = ','.join([
                f"{kw['keyword']}:{kw['volume']}"
                for kw in top_keywords
            ]) if top_keywords else None

            # Update job with SEO scores
            await session.execute(
                text("""
                    UPDATE jobs
                    SET seo_score = :seo_score,
                        seo_keyword_matches = :keyword_matches,
                        seo_total_volume = :total_volume,
                        seo_avg_difficulty = :avg_difficulty,
                        seo_calculated_at = :calculated_at
                    WHERE id = :id
                """),
                {
                    'id': job[0],
                    'seo_score': seo_score,
                    'keyword_matches': keyword_matches_json,
                    'total_volume': total_volume,
                    'avg_difficulty': avg_difficulty,
                    'calculated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )

            self.scores_calculated += 1

        await session.commit()
        return len(jobs)

    async def calculate_all_seo_scores(self):
        """Calculate SEO scores for all jobs"""
        async with await self.get_db_session() as session:
            # Add SEO columns if needed
            await self.add_seo_columns(session)

            # Load keywords
            await self.load_keywords(session)

            # Get total job count
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            total_jobs = result.scalar()

            self.logger.info(f"Starting SEO score calculation for {total_jobs} jobs...")

            # Process in batches
            offset = 0
            while offset < total_jobs:
                batch_size = await self.calculate_job_seo_scores(session, offset)

                if batch_size == 0:
                    break

                offset += batch_size
                progress = min(100, (offset / total_jobs) * 100)

                self.logger.info(f"Progress: {offset}/{total_jobs} jobs ({progress:.1f}%)")

            self.logger.info(f"Completed SEO score calculation for {self.scores_calculated} jobs")

    async def analyze_seo_performance(self):
        """Analyze SEO score distribution and top performers"""
        async with await self.get_db_session() as session:
            # Get score statistics
            result = await session.execute(
                text("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN seo_score > 0 THEN 1 END) as with_seo,
                        MIN(seo_score) as min_score,
                        MAX(seo_score) as max_score,
                        AVG(seo_score) as avg_score,
                        COUNT(CASE WHEN seo_score >= 80 THEN 1 END) as excellent,
                        COUNT(CASE WHEN seo_score >= 60 AND seo_score < 80 THEN 1 END) as good,
                        COUNT(CASE WHEN seo_score >= 40 AND seo_score < 60 THEN 1 END) as average,
                        COUNT(CASE WHEN seo_score >= 20 AND seo_score < 40 THEN 1 END) as fair,
                        COUNT(CASE WHEN seo_score > 0 AND seo_score < 20 THEN 1 END) as poor,
                        COUNT(CASE WHEN seo_score = 0 THEN 1 END) as no_match
                    FROM jobs
                """)
            )

            stats = result.fetchone()

            print("\n📊 SEO Score Distribution Analysis:")
            print(f"  Total Jobs: {stats[0]}")
            print(f"  Jobs with SEO Matches: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
            print(f"  Score Range: {stats[2]:.2f} - {stats[3]:.2f}")
            print(f"  Average Score: {stats[4]:.2f}")
            print("\n  Distribution:")
            print(f"    Excellent (80-100): {stats[5]} jobs ({stats[5]/stats[0]*100:.1f}%)")
            print(f"    Good (60-79): {stats[6]} jobs ({stats[6]/stats[0]*100:.1f}%)")
            print(f"    Average (40-59): {stats[7]} jobs ({stats[7]/stats[0]*100:.1f}%)")
            print(f"    Fair (20-39): {stats[8]} jobs ({stats[8]/stats[0]*100:.1f}%)")
            print(f"    Poor (1-19): {stats[9]} jobs ({stats[9]/stats[0]*100:.1f}%)")
            print(f"    No Match (0): {stats[10]} jobs ({stats[10]/stats[0]*100:.1f}%)")

            # Get top SEO optimized jobs
            result = await session.execute(
                text("""
                    SELECT job_id, company_name, seo_score, seo_keyword_matches, seo_total_volume
                    FROM jobs
                    WHERE seo_score > 0
                    ORDER BY seo_score DESC
                    LIMIT 5
                """)
            )

            top_jobs = result.fetchall()

            print("\n🏆 Top 5 Jobs by SEO Score:")
            for job in top_jobs:
                print(f"    {job[1] or 'Unknown Company'} (Job {job[0]})")
                print(f"      SEO Score: {job[2]:.2f}")
                print(f"      Keywords: {job[3] if job[3] else 'N/A'}")
                print(f"      Total Search Volume: {job[4]:,}")

            # Get most matched keywords
            result = await session.execute(
                text("""
                    SELECT seo_keyword_matches, COUNT(*) as match_count
                    FROM jobs
                    WHERE seo_keyword_matches IS NOT NULL
                    GROUP BY seo_keyword_matches
                    ORDER BY match_count DESC
                    LIMIT 5
                """)
            )

            top_keyword_groups = result.fetchall()

            print("\n🔑 Most Common Keyword Matches:")
            for keywords, count in top_keyword_groups:
                if keywords:
                    primary_keyword = keywords.split(',')[0].split(':')[0]
                    print(f"    {primary_keyword}: {count} jobs")

            return stats


async def main():
    """Main SEO calculation function"""
    calculator = SEOScoreCalculator()

    print("🚀 Starting SEO score calculation...")
    print("  Analyzing job content for SEO keyword matches")
    print("  Considering search volume and difficulty")
    print("")

    # Calculate scores
    await calculator.calculate_all_seo_scores()

    # Analyze performance
    stats = await calculator.analyze_seo_performance()

    if stats and stats[0] > 0:
        print("\n✨ SEO score calculation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ SEO score calculation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())