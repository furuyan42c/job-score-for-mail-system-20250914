#!/usr/bin/env python3
"""
T090: Base Score Calculation Script

Calculates base scores for jobs based on multiple factors:
- Salary score (min/max salary vs market average)
- Location score (prefecture popularity, urban/rural)
- Company score (company size, reputation)
- Freshness score (posting date recency)
- Completeness score (data quality)

Usage:
    python scripts/calculate_base_scores.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta
import json
import math

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


class BaseScoreCalculator:
    """Base score calculation handler"""

    def __init__(self):
        self.logger = setup_logging()
        self.batch_size = 1000
        self.scores_calculated = 0

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

    async def add_score_columns(self, session: AsyncSession):
        """Add score columns to jobs table if they don't exist"""
        try:
            # Check if columns exist
            result = await session.execute(
                text("PRAGMA table_info(jobs)")
            )
            columns = [row[1] for row in result.fetchall()]

            # Add score columns if missing
            score_columns = [
                ('base_score', 'REAL DEFAULT 0'),
                ('salary_score', 'REAL DEFAULT 0'),
                ('location_score', 'REAL DEFAULT 0'),
                ('company_score', 'REAL DEFAULT 0'),
                ('freshness_score', 'REAL DEFAULT 0'),
                ('completeness_score', 'REAL DEFAULT 0'),
                ('score_calculated_at', 'TIMESTAMP')
            ]

            for col_name, col_def in score_columns:
                if col_name not in columns:
                    await session.execute(
                        text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_def}")
                    )
                    self.logger.info(f"Added column {col_name} to jobs table")

            await session.commit()

        except Exception as e:
            self.logger.error(f"Error adding score columns: {e}")
            await session.rollback()

    def calculate_salary_score(self, min_salary: int, max_salary: int, avg_market_salary: float) -> float:
        """
        Calculate salary score (0-100)
        Higher salary relative to market average = higher score
        """
        if min_salary is None and max_salary is None:
            return 50.0  # Default score for missing salary

        # Use the average of min and max, or whichever is available
        if min_salary is not None and max_salary is not None:
            avg_salary = (min_salary + max_salary) / 2
        elif min_salary is not None:
            avg_salary = min_salary
        else:
            avg_salary = max_salary

        # Normalize to market average (market avg = 50 points)
        if avg_market_salary > 0:
            ratio = avg_salary / avg_market_salary
            # Scale: 0.5x market = 25 points, 1x = 50 points, 2x = 75 points, 3x+ = 100 points
            score = min(100, max(0, 25 * ratio))
        else:
            score = 50.0

        return round(score, 2)

    def calculate_location_score(self, pref_cd: int, city_cd: int = None) -> float:
        """
        Calculate location score (0-100)
        Major cities and popular prefectures score higher
        """
        if pref_cd is None:
            return 50.0

        # Prefecture popularity scores (based on job demand)
        prefecture_scores = {
            13: 100,  # Tokyo
            27: 90,   # Osaka
            14: 85,   # Kanagawa
            23: 85,   # Aichi
            40: 80,   # Fukuoka
            11: 75,   # Saitama
            12: 75,   # Chiba
            28: 70,   # Hyogo
            1: 65,    # Hokkaido
            26: 65,   # Kyoto
        }

        # Get base prefecture score
        score = prefecture_scores.get(pref_cd, 50)  # Default 50 for other prefectures

        # Bonus for major cities within prefectures
        major_city_codes = {
            # Tokyo special wards
            13100: 10,  # Chiyoda
            13102: 10,  # Chuo
            13103: 10,  # Minato
            13104: 8,   # Shinjuku
            13113: 8,   # Shibuya
            # Other major cities
            27100: 10,  # Osaka city
            14100: 8,   # Yokohama
            23100: 8,   # Nagoya
            40100: 8,   # Fukuoka city
        }

        if city_cd and city_cd in major_city_codes:
            score = min(100, score + major_city_codes[city_cd])

        return round(score, 2)

    def calculate_company_score(self, company_name: str, job_count: int = 1) -> float:
        """
        Calculate company score (0-100)
        Based on company presence (number of job postings)
        """
        if not company_name:
            return 50.0

        # More job postings = larger/more established company
        # 1 job = 50, 10 jobs = 70, 50+ jobs = 90+
        if job_count <= 1:
            score = 50.0
        elif job_count <= 5:
            score = 50 + (job_count - 1) * 5  # 50-70
        elif job_count <= 20:
            score = 70 + (job_count - 5) * 1.3  # 70-90
        else:
            score = min(100, 90 + (job_count - 20) * 0.5)  # 90-100

        return round(score, 2)

    def calculate_freshness_score(self, start_at: str, end_at: str) -> float:
        """
        Calculate freshness score (0-100)
        Recent postings score higher
        """
        # Since we don't have real posting dates in the sample data,
        # we'll simulate based on start/end dates if available
        score = 75.0  # Default good freshness

        if end_at:
            try:
                # Parse end date
                if len(end_at) == 8:  # YYYYMMDD format
                    end_date = datetime.strptime(end_at, '%Y%m%d')
                else:
                    end_date = datetime.strptime(end_at[:10], '%Y-%m-%d')

                # Check if job has expired
                if end_date < datetime.now():
                    score = 25.0  # Low score for expired jobs
                elif end_date < datetime.now() + timedelta(days=7):
                    score = 50.0  # Medium score for expiring soon
                else:
                    score = 90.0  # High score for active jobs
            except:
                pass

        return round(score, 2)

    def calculate_completeness_score(self, job_data: Dict[str, Any]) -> float:
        """
        Calculate data completeness score (0-100)
        More complete data = higher score
        """
        important_fields = [
            'company_name',
            'job_contents',
            'job_contents_detail',
            'salary',
            'min_salary',
            'max_salary',
            'area',
            'area_address',
            'hours',
            'employment_type',
            'welfare',
            'requirement'
        ]

        filled_count = 0
        for field in important_fields:
            if job_data.get(field) and str(job_data[field]).strip():
                filled_count += 1

        score = (filled_count / len(important_fields)) * 100
        return round(score, 2)

    def calculate_base_score(
        self,
        salary_score: float,
        location_score: float,
        company_score: float,
        freshness_score: float,
        completeness_score: float
    ) -> float:
        """
        Calculate overall base score as weighted average
        """
        # Weights for each component
        weights = {
            'salary': 0.30,
            'location': 0.25,
            'company': 0.15,
            'freshness': 0.20,
            'completeness': 0.10
        }

        base_score = (
            salary_score * weights['salary'] +
            location_score * weights['location'] +
            company_score * weights['company'] +
            freshness_score * weights['freshness'] +
            completeness_score * weights['completeness']
        )

        return round(base_score, 2)

    async def calculate_scores_batch(self, session: AsyncSession, offset: int = 0):
        """Calculate scores for a batch of jobs"""
        # Get market average salary
        result = await session.execute(
            text("SELECT AVG((min_salary + max_salary) / 2) FROM jobs WHERE min_salary IS NOT NULL AND max_salary IS NOT NULL")
        )
        avg_market_salary = result.scalar() or 100000

        # Get company job counts
        result = await session.execute(
            text("SELECT company_name, COUNT(*) as cnt FROM jobs GROUP BY company_name")
        )
        company_counts = {row[0]: row[1] for row in result.fetchall() if row[0]}

        # Get batch of jobs
        result = await session.execute(
            text(f"""
                SELECT id, job_id, company_name, min_salary, max_salary,
                       pref_cd, city_cd, start_at, end_at,
                       job_contents, job_contents_detail, salary,
                       area, area_address, hours, employment_type,
                       welfare, requirement
                FROM jobs
                LIMIT {self.batch_size} OFFSET {offset}
            """)
        )

        jobs = result.fetchall()

        for job in jobs:
            job_dict = {
                'id': job[0],
                'job_id': job[1],
                'company_name': job[2],
                'min_salary': job[3],
                'max_salary': job[4],
                'pref_cd': job[5],
                'city_cd': job[6],
                'start_at': job[7],
                'end_at': job[8],
                'job_contents': job[9],
                'job_contents_detail': job[10],
                'salary': job[11],
                'area': job[12],
                'area_address': job[13],
                'hours': job[14],
                'employment_type': job[15],
                'welfare': job[16],
                'requirement': job[17]
            }

            # Calculate individual scores
            salary_score = self.calculate_salary_score(
                job_dict['min_salary'],
                job_dict['max_salary'],
                avg_market_salary
            )

            location_score = self.calculate_location_score(
                job_dict['pref_cd'],
                job_dict['city_cd']
            )

            company_job_count = company_counts.get(job_dict['company_name'], 1)
            company_score = self.calculate_company_score(
                job_dict['company_name'],
                company_job_count
            )

            freshness_score = self.calculate_freshness_score(
                job_dict['start_at'],
                job_dict['end_at']
            )

            completeness_score = self.calculate_completeness_score(job_dict)

            # Calculate overall base score
            base_score = self.calculate_base_score(
                salary_score,
                location_score,
                company_score,
                freshness_score,
                completeness_score
            )

            # Update job record with scores
            await session.execute(
                text("""
                    UPDATE jobs
                    SET base_score = :base_score,
                        salary_score = :salary_score,
                        location_score = :location_score,
                        company_score = :company_score,
                        freshness_score = :freshness_score,
                        completeness_score = :completeness_score,
                        score_calculated_at = :calculated_at
                    WHERE id = :id
                """),
                {
                    'id': job_dict['id'],
                    'base_score': base_score,
                    'salary_score': salary_score,
                    'location_score': location_score,
                    'company_score': company_score,
                    'freshness_score': freshness_score,
                    'completeness_score': completeness_score,
                    'calculated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )

            self.scores_calculated += 1

        await session.commit()
        return len(jobs)

    async def calculate_all_scores(self):
        """Calculate scores for all jobs"""
        async with await self.get_db_session() as session:
            # Add score columns if needed
            await self.add_score_columns(session)

            # Get total job count
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            total_jobs = result.scalar()

            self.logger.info(f"Starting score calculation for {total_jobs} jobs...")

            # Process in batches
            offset = 0
            while offset < total_jobs:
                batch_size = await self.calculate_scores_batch(session, offset)

                if batch_size == 0:
                    break

                offset += batch_size
                progress = min(100, (offset / total_jobs) * 100)

                self.logger.info(f"Progress: {offset}/{total_jobs} jobs ({progress:.1f}%)")

            self.logger.info(f"Completed score calculation for {self.scores_calculated} jobs")

    async def analyze_score_distribution(self):
        """Analyze the distribution of calculated scores"""
        async with await self.get_db_session() as session:
            # Get score statistics
            result = await session.execute(
                text("""
                    SELECT
                        COUNT(*) as total,
                        MIN(base_score) as min_score,
                        MAX(base_score) as max_score,
                        AVG(base_score) as avg_score,
                        COUNT(CASE WHEN base_score >= 80 THEN 1 END) as excellent,
                        COUNT(CASE WHEN base_score >= 60 AND base_score < 80 THEN 1 END) as good,
                        COUNT(CASE WHEN base_score >= 40 AND base_score < 60 THEN 1 END) as average,
                        COUNT(CASE WHEN base_score < 40 THEN 1 END) as poor
                    FROM jobs
                    WHERE base_score IS NOT NULL
                """)
            )

            stats = result.fetchone()

            print("\n📊 Score Distribution Analysis:")
            print(f"  Total Scored Jobs: {stats[0]}")
            print(f"  Score Range: {stats[1]:.2f} - {stats[2]:.2f}")
            print(f"  Average Score: {stats[3]:.2f}")
            print("\n  Distribution:")
            print(f"    Excellent (80-100): {stats[4]} jobs ({stats[4]/stats[0]*100:.1f}%)")
            print(f"    Good (60-79): {stats[5]} jobs ({stats[5]/stats[0]*100:.1f}%)")
            print(f"    Average (40-59): {stats[6]} jobs ({stats[6]/stats[0]*100:.1f}%)")
            print(f"    Poor (0-39): {stats[7]} jobs ({stats[7]/stats[0]*100:.1f}%)")

            # Get top scored jobs
            result = await session.execute(
                text("""
                    SELECT job_id, company_name, base_score, salary_score, location_score
                    FROM jobs
                    WHERE base_score IS NOT NULL
                    ORDER BY base_score DESC
                    LIMIT 5
                """)
            )

            top_jobs = result.fetchall()

            print("\n🏆 Top 5 Jobs by Base Score:")
            for job in top_jobs:
                print(f"    {job[1] or 'Unknown Company'} (Job {job[0]})")
                print(f"      Base Score: {job[2]:.2f} (Salary: {job[3]:.2f}, Location: {job[4]:.2f})")

            return stats


async def main():
    """Main calculation function"""
    calculator = BaseScoreCalculator()

    print("🚀 Starting base score calculation...")
    print("  Calculating scores based on:")
    print("    • Salary (30% weight)")
    print("    • Location (25% weight)")
    print("    • Company (15% weight)")
    print("    • Freshness (20% weight)")
    print("    • Completeness (10% weight)")
    print("")

    # Calculate scores
    await calculator.calculate_all_scores()

    # Analyze distribution
    stats = await calculator.analyze_score_distribution()

    if stats and stats[0] > 0:
        print("\n✨ Base score calculation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Base score calculation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())