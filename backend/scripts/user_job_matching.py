#!/usr/bin/env python3
"""
T092: User-Job Matching Script

Performs user-job matching based on:
- User preferences (location, salary, job type)
- Job scores (base score, SEO score)
- Match scoring algorithm
- Recommendation generation

Usage:
    python scripts/user_job_matching.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime
import random
import json

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


class UserJobMatcher:
    """User-job matching handler"""

    def __init__(self):
        self.logger = setup_logging()
        self.matches_generated = 0

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

    async def create_users_table(self, session: AsyncSession):
        """Create users table if it doesn't exist"""
        try:
            # Check if table exists
            result = await session.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = 'users'")
            )
            if result.scalar() > 0:
                self.logger.info("Users table already exists")
                return

            # Create users table
            create_table_sql = """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                name TEXT,
                pref_cd INTEGER,
                desired_salary_min INTEGER,
                desired_salary_max INTEGER,
                desired_employment_type TEXT,
                desired_occupation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            await session.execute(text(create_table_sql))
            await session.commit()
            self.logger.info("Created users table")

        except Exception as e:
            self.logger.error(f"Error creating users table: {e}")
            await session.rollback()

    async def create_matches_table(self, session: AsyncSession):
        """Create user_job_matches table if it doesn't exist"""
        try:
            # Check if table exists
            result = await session.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = 'user_job_matches'")
            )
            if result.scalar() > 0:
                self.logger.info("User_job_matches table already exists")
                return

            # Create matches table
            create_table_sql = """
            CREATE TABLE user_job_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                match_score REAL NOT NULL,
                location_match REAL,
                salary_match REAL,
                type_match REAL,
                base_score_weight REAL,
                seo_score_weight REAL,
                match_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, job_id)
            )
            """

            await session.execute(text(create_table_sql))

            # Create indexes
            await session.execute(
                text("CREATE INDEX idx_matches_user_id ON user_job_matches(user_id)")
            )
            await session.execute(
                text("CREATE INDEX idx_matches_score ON user_job_matches(match_score DESC)")
            )

            await session.commit()
            self.logger.info("Created user_job_matches table")

        except Exception as e:
            self.logger.error(f"Error creating matches table: {e}")
            await session.rollback()

    async def generate_test_users(self, session: AsyncSession, num_users: int = 100):
        """Generate test users with various preferences"""
        self.logger.info(f"Generating {num_users} test users...")

        # Get prefecture codes from jobs
        result = await session.execute(
            text("SELECT DISTINCT pref_cd FROM jobs WHERE pref_cd IS NOT NULL LIMIT 47")
        )
        pref_codes = [row[0] for row in result.fetchall()]

        # Employment types
        employment_types = ['正社員', '契約社員', 'パート・アルバイト', '派遣社員', '業務委託']

        # Generate users
        for i in range(num_users):
            user_id = f"user_{i+1:04d}"
            email = f"user{i+1}@example.com"
            name = f"テストユーザー {i+1}"

            # Random preferences
            pref_cd = random.choice(pref_codes) if pref_codes else 13
            desired_salary_min = random.choice([50000, 80000, 100000, 120000, 150000, 200000])
            desired_salary_max = desired_salary_min + random.choice([50000, 100000, 200000, 300000])
            desired_employment_type = random.choice(employment_types)

            try:
                await session.execute(
                    text("""
                        INSERT INTO users (user_id, email, name, pref_cd,
                            desired_salary_min, desired_salary_max,
                            desired_employment_type, created_at, updated_at)
                        VALUES (:user_id, :email, :name, :pref_cd,
                            :desired_salary_min, :desired_salary_max,
                            :desired_employment_type, :created_at, :updated_at)
                        ON CONFLICT (user_id) DO UPDATE SET
                            updated_at = :updated_at
                    """),
                    {
                        'user_id': user_id,
                        'email': email,
                        'name': name,
                        'pref_cd': pref_cd,
                        'desired_salary_min': desired_salary_min,
                        'desired_salary_max': desired_salary_max,
                        'desired_employment_type': desired_employment_type,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                )
            except Exception as e:
                self.logger.warning(f"Error creating user {user_id}: {e}")

        await session.commit()
        self.logger.info(f"Generated {num_users} test users")

    def calculate_location_match(self, user_pref: int, job_pref: int) -> float:
        """Calculate location match score (0-100)"""
        if user_pref == job_pref:
            return 100.0  # Perfect match

        # Same region gives partial score
        regions = {
            'kanto': [11, 12, 13, 14, 15, 16, 17],  # 関東
            'kansai': [26, 27, 28, 29, 30],  # 関西
            'chubu': [21, 22, 23, 24],  # 中部
            'kyushu': [40, 41, 42, 43, 44, 45, 46, 47],  # 九州
            'tohoku': [1, 2, 3, 4, 5, 6, 7],  # 東北・北海道
            'chugoku': [31, 32, 33, 34, 35],  # 中国
            'shikoku': [36, 37, 38, 39],  # 四国
        }

        for region, codes in regions.items():
            if user_pref in codes and job_pref in codes:
                return 70.0  # Same region

        return 30.0  # Different region

    def calculate_salary_match(
        self,
        user_min: int,
        user_max: int,
        job_min: int,
        job_max: int
    ) -> float:
        """Calculate salary match score (0-100)"""
        if not job_min and not job_max:
            return 50.0  # Unknown salary

        # Use available salary data
        job_avg = 0
        if job_min and job_max:
            job_avg = (job_min + job_max) / 2
        elif job_min:
            job_avg = job_min
        elif job_max:
            job_avg = job_max

        user_avg = (user_min + user_max) / 2 if user_min and user_max else user_min or user_max or 100000

        # Check if job meets minimum requirement
        if job_avg < user_min:
            # Penalize jobs below minimum
            ratio = job_avg / user_min
            return max(0, ratio * 50)  # 0-50 points

        # Check if job is within range
        if user_min <= job_avg <= user_max:
            return 100.0  # Perfect match

        # Job exceeds maximum (still good but not perfect)
        if job_avg > user_max:
            # Higher salary is still attractive
            over_ratio = min(2.0, job_avg / user_max)
            return 70 + (over_ratio - 1) * 30  # 70-100 points

        return 50.0

    def calculate_type_match(self, user_type: str, job_type: str) -> float:
        """Calculate employment type match (0-100)"""
        if not user_type or not job_type:
            return 50.0

        if user_type.lower() == job_type.lower():
            return 100.0

        # Partial matches
        type_similarity = {
            '正社員': {'契約社員': 70, '派遣社員': 50},
            '契約社員': {'正社員': 80, '派遣社員': 60},
            'パート・アルバイト': {'派遣社員': 60},
            '派遣社員': {'契約社員': 60, 'パート・アルバイト': 50},
        }

        if user_type in type_similarity:
            return type_similarity[user_type].get(job_type, 30.0)

        return 30.0

    def calculate_match_score(
        self,
        location_match: float,
        salary_match: float,
        type_match: float,
        base_score: float,
        seo_score: float
    ) -> float:
        """Calculate overall match score"""
        # Weights for different factors
        weights = {
            'location': 0.25,
            'salary': 0.30,
            'type': 0.15,
            'base_score': 0.20,
            'seo_score': 0.10
        }

        match_score = (
            location_match * weights['location'] +
            salary_match * weights['salary'] +
            type_match * weights['type'] +
            base_score * weights['base_score'] +
            seo_score * weights['seo_score']
        )

        return round(match_score, 2)

    async def generate_matches_for_user(
        self,
        session: AsyncSession,
        user: Dict[str, Any],
        limit: int = 50
    ) -> int:
        """Generate job matches for a single user"""
        # Get top jobs based on scores
        result = await session.execute(
            text("""
                SELECT id, job_id, pref_cd, min_salary, max_salary,
                       employment_type, base_score, seo_score, company_name
                FROM jobs
                WHERE base_score > 40  -- Only consider decent jobs
                ORDER BY (base_score * 0.7 + seo_score * 0.3) DESC
                LIMIT :limit
            """),
            {'limit': limit * 2}  # Get more to filter
        )

        jobs = result.fetchall()
        matches_created = 0

        for job in jobs:
            # Calculate match scores
            location_match = self.calculate_location_match(
                user['pref_cd'] or 13,
                job[2] or 13  # pref_cd
            )

            salary_match = self.calculate_salary_match(
                user['desired_salary_min'] or 100000,
                user['desired_salary_max'] or 500000,
                job[3],  # min_salary
                job[4]   # max_salary
            )

            type_match = self.calculate_type_match(
                user['desired_employment_type'],
                job[5]  # employment_type
            )

            # Overall match score
            match_score = self.calculate_match_score(
                location_match,
                salary_match,
                type_match,
                job[6] or 50.0,  # base_score
                job[7] or 0.0    # seo_score
            )

            # Only save good matches
            if match_score >= 50:
                # Generate match reason
                reasons = []
                if location_match >= 70:
                    reasons.append("Location match")
                if salary_match >= 70:
                    reasons.append("Salary match")
                if job[6] and job[6] >= 70:
                    reasons.append("High quality job")
                if job[7] and job[7] >= 20:
                    reasons.append("SEO optimized")

                match_reason = ", ".join(reasons) if reasons else "General match"

                try:
                    await session.execute(
                        text("""
                            INSERT INTO user_job_matches (
                                user_id, job_id, match_score,
                                location_match, salary_match, type_match,
                                base_score_weight, seo_score_weight,
                                match_reason, created_at
                            ) VALUES (
                                :user_id, :job_id, :match_score,
                                :location_match, :salary_match, :type_match,
                                :base_score, :seo_score,
                                :match_reason, :created_at
                            )
                            ON CONFLICT (user_id, job_id) DO UPDATE SET
                                match_score = :match_score,
                                created_at = :created_at
                        """),
                        {
                            'user_id': user['user_id'],
                            'job_id': job[1],
                            'match_score': match_score,
                            'location_match': location_match,
                            'salary_match': salary_match,
                            'type_match': type_match,
                            'base_score': job[6] or 0,
                            'seo_score': job[7] or 0,
                            'match_reason': match_reason,
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    )
                    matches_created += 1

                    if matches_created >= limit:
                        break

                except Exception as e:
                    self.logger.warning(f"Error creating match: {e}")

        await session.commit()
        return matches_created

    async def generate_all_matches(self):
        """Generate matches for all users"""
        async with await self.get_db_session() as session:
            # Create tables if needed
            await self.create_users_table(session)
            await self.create_matches_table(session)

            # Check if we have users
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()

            if user_count == 0:
                # Generate test users
                await self.generate_test_users(session, 100)
                user_count = 100

            # Get all users
            result = await session.execute(
                text("""
                    SELECT user_id, pref_cd, desired_salary_min,
                           desired_salary_max, desired_employment_type
                    FROM users
                """)
            )

            users = result.fetchall()
            total_matches = 0

            self.logger.info(f"Generating matches for {len(users)} users...")

            for idx, user_row in enumerate(users):
                user = {
                    'user_id': user_row[0],
                    'pref_cd': user_row[1],
                    'desired_salary_min': user_row[2],
                    'desired_salary_max': user_row[3],
                    'desired_employment_type': user_row[4]
                }

                matches = await self.generate_matches_for_user(session, user, limit=20)
                total_matches += matches

                if (idx + 1) % 10 == 0:
                    self.logger.info(f"Progress: {idx+1}/{len(users)} users processed")

            self.matches_generated = total_matches
            self.logger.info(f"Generated {total_matches} total matches")

    async def analyze_matching_results(self):
        """Analyze the matching results"""
        async with await self.get_db_session() as session:
            # Overall statistics
            result = await session.execute(
                text("""
                    SELECT
                        COUNT(DISTINCT user_id) as users_with_matches,
                        COUNT(DISTINCT job_id) as matched_jobs,
                        COUNT(*) as total_matches,
                        AVG(match_score) as avg_score,
                        MAX(match_score) as max_score,
                        MIN(match_score) as min_score
                    FROM user_job_matches
                """)
            )

            stats = result.fetchone()

            print("\n📊 Matching Results Analysis:")
            print(f"  Users with Matches: {stats[0]}")
            print(f"  Unique Jobs Matched: {stats[1]}")
            print(f"  Total Matches: {stats[2]}")
            print(f"  Score Range: {stats[5]:.2f} - {stats[4]:.2f}")
            print(f"  Average Match Score: {stats[3]:.2f}")

            # Distribution
            result = await session.execute(
                text("""
                    SELECT
                        COUNT(CASE WHEN match_score >= 80 THEN 1 END) as excellent,
                        COUNT(CASE WHEN match_score >= 70 AND match_score < 80 THEN 1 END) as good,
                        COUNT(CASE WHEN match_score >= 60 AND match_score < 70 THEN 1 END) as fair,
                        COUNT(CASE WHEN match_score >= 50 AND match_score < 60 THEN 1 END) as acceptable
                    FROM user_job_matches
                """)
            )

            dist = result.fetchone()

            print("\n  Match Quality Distribution:")
            print(f"    Excellent (80-100): {dist[0]} matches")
            print(f"    Good (70-79): {dist[1]} matches")
            print(f"    Fair (60-69): {dist[2]} matches")
            print(f"    Acceptable (50-59): {dist[3]} matches")

            # Top matches
            result = await session.execute(
                text("""
                    SELECT m.user_id, m.job_id, j.company_name, m.match_score, m.match_reason
                    FROM user_job_matches m
                    JOIN jobs j ON j.job_id = m.job_id
                    ORDER BY m.match_score DESC
                    LIMIT 5
                """)
            )

            top_matches = result.fetchall()

            print("\n🏆 Top 5 Matches:")
            for match in top_matches:
                print(f"    User {match[0]} → {match[2] or 'Unknown Company'}")
                print(f"      Score: {match[3]:.2f} | Reason: {match[4]}")

            # User coverage
            result = await session.execute(
                text("""
                    SELECT u.user_id, COUNT(m.id) as match_count
                    FROM users u
                    LEFT JOIN user_job_matches m ON u.user_id = m.user_id
                    GROUP BY u.user_id
                    ORDER BY match_count DESC
                """)
            )

            user_matches = result.fetchall()
            users_with_no_matches = sum(1 for u in user_matches if u[1] == 0)

            print(f"\n📈 User Coverage:")
            print(f"    Users with matches: {len(user_matches) - users_with_no_matches}/{len(user_matches)}")
            print(f"    Average matches per user: {stats[2] / len(user_matches) if user_matches else 0:.1f}")

            return stats


async def main():
    """Main matching function"""
    matcher = UserJobMatcher()

    print("🚀 Starting user-job matching...")
    print("  Creating test users if needed")
    print("  Matching based on preferences and scores")
    print("")

    # Generate matches
    await matcher.generate_all_matches()

    # Analyze results
    stats = await matcher.analyze_matching_results()

    if stats and stats[2] > 0:  # total_matches > 0
        print("\n✨ User-job matching completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ User-job matching failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())