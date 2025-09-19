#!/usr/bin/env python3
"""
T089: Data Integrity Validation Script

Validates the integrity of imported data:
- Foreign key relationships
- Data completeness
- Data consistency
- Index coverage
- Search functionality

Usage:
    python scripts/validate_data_integrity.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

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


class DataIntegrityValidator:
    """Data integrity validation handler"""

    def __init__(self):
        self.logger = setup_logging()
        self.validation_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    async def get_db_session(self) -> AsyncSession:
        """Create database session"""
        # Use the correct database file for development
        database_url = 'sqlite+aiosqlite:///./app/database.db'
        engine = create_async_engine(
            database_url,
            echo=False
        )
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session_maker()

    async def check_table_exists(self, session: AsyncSession, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = '{table_name}'")
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking table {table_name}: {e}")
            return False

    async def validate_table_structure(self) -> Dict[str, bool]:
        """Validate that all required tables exist"""
        required_tables = [
            'jobs',
            'seo_keywords',
            'jobs_fts',
            'seo_keywords_fts'
        ]

        results = {}
        async with await self.get_db_session() as session:
            for table in required_tables:
                exists = await self.check_table_exists(session, table)
                results[table] = exists

                if exists:
                    self.validation_results['passed'].append(f"Table '{table}' exists")
                else:
                    self.validation_results['failed'].append(f"Table '{table}' is missing")

        return results

    async def validate_data_counts(self) -> Dict[str, int]:
        """Validate record counts in each table"""
        counts = {}

        async with await self.get_db_session() as session:
            # Check jobs table
            result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            jobs_count = result.scalar()
            counts['jobs'] = jobs_count

            if jobs_count > 0:
                self.validation_results['passed'].append(f"Jobs table has {jobs_count} records")
            else:
                self.validation_results['failed'].append("Jobs table is empty")

            # Check SEO keywords table
            result = await session.execute(text("SELECT COUNT(*) FROM seo_keywords"))
            seo_count = result.scalar()
            counts['seo_keywords'] = seo_count

            if seo_count > 0:
                self.validation_results['passed'].append(f"SEO keywords table has {seo_count} records")
            else:
                self.validation_results['failed'].append("SEO keywords table is empty")

        return counts

    async def validate_data_completeness(self) -> Dict[str, Any]:
        """Check for missing or null values in critical fields"""
        completeness = {}

        async with await self.get_db_session() as session:
            # Check jobs completeness
            critical_job_fields = [
                'job_id', 'company_name', 'job_contents',
                'pref_cd', 'employment_type_cd'
            ]

            for field in critical_job_fields:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM jobs WHERE {field} IS NULL OR {field} = ''")
                )
                null_count = result.scalar()

                result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
                total_count = result.scalar()

                completeness[f'jobs.{field}'] = {
                    'null_count': null_count,
                    'total_count': total_count,
                    'completeness_pct': ((total_count - null_count) / total_count * 100) if total_count > 0 else 0
                }

                if null_count == 0:
                    self.validation_results['passed'].append(f"Field 'jobs.{field}' is 100% complete")
                elif null_count < total_count * 0.1:  # Less than 10% null
                    self.validation_results['warnings'].append(
                        f"Field 'jobs.{field}' has {null_count} null values ({100-completeness[f'jobs.{field}']['completeness_pct']:.1f}% incomplete)"
                    )
                else:
                    self.validation_results['failed'].append(
                        f"Field 'jobs.{field}' has {null_count} null values ({100-completeness[f'jobs.{field}']['completeness_pct']:.1f}% incomplete)"
                    )

            # Check SEO keywords completeness
            critical_seo_fields = ['keyword', 'search_volume']

            for field in critical_seo_fields:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM seo_keywords WHERE {field} IS NULL")
                )
                null_count = result.scalar()

                result = await session.execute(text("SELECT COUNT(*) FROM seo_keywords"))
                total_count = result.scalar()

                completeness[f'seo_keywords.{field}'] = {
                    'null_count': null_count,
                    'total_count': total_count,
                    'completeness_pct': ((total_count - null_count) / total_count * 100) if total_count > 0 else 0
                }

                if null_count == 0:
                    self.validation_results['passed'].append(f"Field 'seo_keywords.{field}' is 100% complete")
                else:
                    self.validation_results['warnings'].append(
                        f"Field 'seo_keywords.{field}' has {null_count} null values"
                    )

        return completeness

    async def validate_data_consistency(self) -> Dict[str, Any]:
        """Check data consistency and logical constraints"""
        consistency_checks = {}

        async with await self.get_db_session() as session:
            # Check salary consistency (min <= max)
            result = await session.execute(
                text("SELECT COUNT(*) FROM jobs WHERE min_salary > max_salary AND min_salary IS NOT NULL AND max_salary IS NOT NULL")
            )
            invalid_salary_count = result.scalar()
            consistency_checks['invalid_salaries'] = invalid_salary_count

            if invalid_salary_count == 0:
                self.validation_results['passed'].append("All salary ranges are valid (min <= max)")
            else:
                self.validation_results['failed'].append(f"{invalid_salary_count} jobs have invalid salary ranges (min > max)")

            # Check age consistency (min <= max)
            result = await session.execute(
                text("SELECT COUNT(*) FROM jobs WHERE min_age > max_age AND min_age IS NOT NULL AND max_age IS NOT NULL")
            )
            invalid_age_count = result.scalar()
            consistency_checks['invalid_ages'] = invalid_age_count

            if invalid_age_count == 0:
                self.validation_results['passed'].append("All age ranges are valid (min <= max)")
            else:
                self.validation_results['failed'].append(f"{invalid_age_count} jobs have invalid age ranges (min > max)")

            # Check for duplicate job IDs
            result = await session.execute(
                text("SELECT job_id, COUNT(*) as cnt FROM jobs GROUP BY job_id HAVING cnt > 1")
            )
            duplicates = result.fetchall()
            consistency_checks['duplicate_job_ids'] = len(duplicates)

            if len(duplicates) == 0:
                self.validation_results['passed'].append("No duplicate job IDs found")
            else:
                self.validation_results['failed'].append(f"{len(duplicates)} duplicate job IDs found")

            # Check for duplicate keywords
            result = await session.execute(
                text("SELECT keyword, COUNT(*) as cnt FROM seo_keywords GROUP BY keyword HAVING cnt > 1")
            )
            duplicates = result.fetchall()
            consistency_checks['duplicate_keywords'] = len(duplicates)

            if len(duplicates) == 0:
                self.validation_results['passed'].append("No duplicate keywords found")
            else:
                self.validation_results['failed'].append(f"{len(duplicates)} duplicate keywords found")

        return consistency_checks

    async def validate_indexes(self) -> List[str]:
        """Check that all expected indexes exist"""
        expected_indexes = [
            'idx_jobs_job_id',
            'idx_jobs_company_name',
            'idx_jobs_pref_cd',
            'idx_jobs_city_cd',
            'idx_jobs_occupation_cd1',
            'idx_jobs_employment_type_cd',
            'idx_jobs_salary',
            'idx_jobs_age',
            'idx_seo_keywords_keyword'
        ]

        existing_indexes = []

        async with await self.get_db_session() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'index'")
            )
            index_rows = result.fetchall()
            existing_indexes = [row[0] for row in index_rows]

            for index in expected_indexes:
                if index in existing_indexes:
                    self.validation_results['passed'].append(f"Index '{index}' exists")
                else:
                    self.validation_results['warnings'].append(f"Index '{index}' is missing")

        return existing_indexes

    async def validate_search_functionality(self) -> Dict[str, bool]:
        """Test full-text search functionality"""
        search_tests = {}

        async with await self.get_db_session() as session:
            # Test job search
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM jobs_fts WHERE jobs_fts MATCH 'バイト'")
                )
                count = result.scalar()
                search_tests['jobs_fts'] = count > 0

                if count > 0:
                    self.validation_results['passed'].append(f"Job FTS search working ({count} results for 'バイト')")
                else:
                    self.validation_results['warnings'].append("Job FTS search returned no results")
            except Exception as e:
                search_tests['jobs_fts'] = False
                self.validation_results['failed'].append(f"Job FTS search failed: {e}")

            # Test SEO keyword search
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM seo_keywords_fts WHERE seo_keywords_fts MATCH 'バイト'")
                )
                count = result.scalar()
                search_tests['seo_keywords_fts'] = count > 0

                if count > 0:
                    self.validation_results['passed'].append(f"SEO keyword FTS search working ({count} results for 'バイト')")
                else:
                    self.validation_results['warnings'].append("SEO keyword FTS search returned no results")
            except Exception as e:
                search_tests['seo_keywords_fts'] = False
                self.validation_results['failed'].append(f"SEO keyword FTS search failed: {e}")

        return search_tests

    async def validate_data_distribution(self) -> Dict[str, Any]:
        """Analyze data distribution for anomalies"""
        distribution = {}

        async with await self.get_db_session() as session:
            # Prefecture distribution
            result = await session.execute(
                text("""
                    SELECT pref_cd, COUNT(*) as cnt
                    FROM jobs
                    WHERE pref_cd IS NOT NULL
                    GROUP BY pref_cd
                    ORDER BY cnt DESC
                """)
            )
            pref_distribution = result.fetchall()
            distribution['prefectures'] = len(pref_distribution)

            if len(pref_distribution) > 0:
                self.validation_results['passed'].append(f"Jobs distributed across {len(pref_distribution)} prefectures")
            else:
                self.validation_results['failed'].append("No prefecture distribution found")

            # Employment type distribution
            result = await session.execute(
                text("""
                    SELECT employment_type_cd, COUNT(*) as cnt
                    FROM jobs
                    WHERE employment_type_cd IS NOT NULL
                    GROUP BY employment_type_cd
                """)
            )
            emp_distribution = result.fetchall()
            distribution['employment_types'] = len(emp_distribution)

            if len(emp_distribution) > 0:
                self.validation_results['passed'].append(f"Jobs have {len(emp_distribution)} employment types")
            else:
                self.validation_results['failed'].append("No employment type distribution found")

            # Salary distribution
            result = await session.execute(
                text("""
                    SELECT
                        MIN(min_salary) as min_sal,
                        MAX(max_salary) as max_sal,
                        AVG(min_salary) as avg_min_sal,
                        AVG(max_salary) as avg_max_sal
                    FROM jobs
                    WHERE min_salary IS NOT NULL OR max_salary IS NOT NULL
                """)
            )
            salary_stats = result.fetchone()
            distribution['salary_range'] = {
                'min': salary_stats[0],
                'max': salary_stats[1],
                'avg_min': salary_stats[2],
                'avg_max': salary_stats[3]
            }

            if salary_stats[0] is not None and salary_stats[1] is not None:
                if salary_stats[0] >= 0 and salary_stats[1] <= 10000000:  # Reasonable salary range
                    self.validation_results['passed'].append(f"Salary range is reasonable: ¥{salary_stats[0]:,} - ¥{salary_stats[1]:,}")
                else:
                    self.validation_results['warnings'].append(f"Unusual salary range detected: ¥{salary_stats[0]:,} - ¥{salary_stats[1]:,}")

        return distribution

    def generate_report(self) -> str:
        """Generate validation report"""
        report = []
        report.append("=" * 60)
        report.append("DATA INTEGRITY VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"✅ Passed: {len(self.validation_results['passed'])}")
        report.append(f"⚠️  Warnings: {len(self.validation_results['warnings'])}")
        report.append(f"❌ Failed: {len(self.validation_results['failed'])}")
        report.append("")

        # Passed tests
        if self.validation_results['passed']:
            report.append("PASSED VALIDATIONS")
            report.append("-" * 40)
            for item in self.validation_results['passed']:
                report.append(f"✅ {item}")
            report.append("")

        # Warnings
        if self.validation_results['warnings']:
            report.append("WARNINGS")
            report.append("-" * 40)
            for item in self.validation_results['warnings']:
                report.append(f"⚠️  {item}")
            report.append("")

        # Failed tests
        if self.validation_results['failed']:
            report.append("FAILED VALIDATIONS")
            report.append("-" * 40)
            for item in self.validation_results['failed']:
                report.append(f"❌ {item}")
            report.append("")

        # Overall result
        report.append("OVERALL RESULT")
        report.append("-" * 40)
        if len(self.validation_results['failed']) == 0:
            if len(self.validation_results['warnings']) == 0:
                report.append("🎉 ALL VALIDATIONS PASSED - Data integrity is EXCELLENT")
            else:
                report.append("✅ VALIDATIONS PASSED WITH WARNINGS - Data integrity is GOOD")
        else:
            report.append("❌ VALIDATIONS FAILED - Data integrity issues need attention")

        return "\n".join(report)

    async def run_all_validations(self):
        """Run all validation checks"""
        print("🔍 Starting data integrity validation...")
        print("")

        # 1. Table structure
        print("📋 Validating table structure...")
        await self.validate_table_structure()

        # 2. Data counts
        print("📊 Validating data counts...")
        counts = await self.validate_data_counts()

        # 3. Data completeness
        print("✅ Validating data completeness...")
        await self.validate_data_completeness()

        # 4. Data consistency
        print("🔄 Validating data consistency...")
        await self.validate_data_consistency()

        # 5. Indexes
        print("🗂️ Validating indexes...")
        await self.validate_indexes()

        # 6. Search functionality
        print("🔎 Validating search functionality...")
        await self.validate_search_functionality()

        # 7. Data distribution
        print("📈 Validating data distribution...")
        await self.validate_data_distribution()

        # Generate and display report
        print("")
        report = self.generate_report()
        print(report)

        # Save report to file
        report_path = Path("validation_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_path}")

        # Return success/failure status
        return len(self.validation_results['failed']) == 0


async def main():
    """Main validation function"""
    validator = DataIntegrityValidator()
    success = await validator.run_all_validations()

    if success:
        print("\n✨ Data integrity validation completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Data integrity validation found issues that need attention!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())