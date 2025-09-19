#!/usr/bin/env python3
"""
T088: Job Data Import Script

Imports job data from CSV files:
- sample_job_data.csv (195,683 records)

Creates jobs table with all necessary fields and indexes.

Usage:
    python scripts/import_job_data.py --data-dir ../data
"""

import asyncio
import pandas as pd
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime
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


class JobDataImporter:
    """Job data import handler"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.logger = setup_logging()
        self.csv_file = 'sample_job_data.csv'
        self.sample_csv = 'sample_job_data_1000.csv'

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

    async def check_table_exists(self, session: AsyncSession) -> bool:
        """Check if jobs table exists"""
        try:
            # SQLite compatible check
            result = await session.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = 'jobs'")
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking table: {e}")
            return False

    async def create_jobs_table(self, session: AsyncSession):
        """Create jobs table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            import_from TEXT,
            client_cd TEXT,
            endcl_cd TEXT,
            application_cd TEXT,
            application_name TEXT,
            company_name TEXT,
            company_kana TEXT,
            occupation_cd1 TEXT,
            occupation_cd2 TEXT,
            occupation_cd3 TEXT,
            job_contents TEXT,
            job_contents_detail TEXT,
            salary TEXT,
            salary_type_cd INTEGER,
            min_salary INTEGER,
            max_salary INTEGER,
            age TEXT,
            max_age_cd INTEGER,
            min_age_cd INTEGER,
            max_age INTEGER,
            min_age INTEGER,
            area TEXT,
            area_address TEXT,
            pref_cd INTEGER,
            city_cd INTEGER,
            hours TEXT,
            area_eki TEXT,
            ensen_block_cd TEXT,
            route_cd TEXT,
            station_cd TEXT,
            business TEXT,
            traffic TEXT,
            employment_type TEXT,
            employment_type_cd INTEGER,
            welfare TEXT,
            requirement_way TEXT,
            requirement TEXT,
            special_edition_cd TEXT,
            url TEXT,
            transfer_url TEXT,
            employment_term_cd INTEGER,
            start_at TEXT,
            end_at TEXT,
            features TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        try:
            await session.execute(text(create_table_sql))
            await session.commit()
            self.logger.info("Created jobs table")

            # Create indexes for faster queries
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_company_name ON jobs(company_name)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_pref_cd ON jobs(pref_cd)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_city_cd ON jobs(city_cd)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_occupation_cd1 ON jobs(occupation_cd1)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_employment_type_cd ON jobs(employment_type_cd)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_salary ON jobs(min_salary, max_salary)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_age ON jobs(min_age, max_age)"
            ]

            for index_sql in indexes:
                await session.execute(text(index_sql))

            await session.commit()
            self.logger.info("Created job table indexes")

        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            await session.rollback()

    async def import_job_data(self, test_mode: bool = False) -> Dict[str, int]:
        """Import job data from CSV"""
        results = {'imported': 0, 'skipped': 0, 'errors': 0}

        # Choose file based on test mode
        csv_file = self.sample_csv if test_mode else self.csv_file
        csv_path = self.data_dir / csv_file

        if not csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            return results

        async with await self.get_db_session() as session:
            # Ensure table exists
            if not await self.check_table_exists(session):
                await self.create_jobs_table(session)

            # Check if data already exists
            existing_count_result = await session.execute(
                text("SELECT COUNT(*) FROM jobs")
            )
            existing_count = existing_count_result.scalar()

            if existing_count > 0:
                self.logger.info(f"Jobs table already has {existing_count} records")
                if not test_mode and existing_count >= 195000:
                    self.logger.info("Full dataset appears to be already imported")
                    results['skipped'] = existing_count
                    return results

            # Read CSV
            self.logger.info(f"Reading CSV: {csv_path}")

            # Read in chunks for large file
            chunk_size = 10000
            total_chunks = 0

            for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size):
                total_chunks += 1

                # Replace NaN with None for SQL compatibility
                chunk_df = chunk_df.where(pd.notnull(chunk_df), None)

                # Process each row in chunk
                for idx, row in chunk_df.iterrows():
                    try:
                        # Prepare job data
                        job_data = {
                            'job_id': str(row.get('job_id', '')),
                            'import_from': row.get('import_from'),
                            'client_cd': row.get('client_cd'),
                            'endcl_cd': row.get('endcl_cd'),
                            'application_cd': row.get('application_cd'),
                            'application_name': row.get('application_name'),
                            'company_name': row.get('company_name'),
                            'company_kana': row.get('company_kana'),
                            'occupation_cd1': row.get('occupation_cd1'),
                            'occupation_cd2': row.get('occupation_cd2'),
                            'occupation_cd3': row.get('occupation_cd3'),
                            'job_contents': row.get('job_contents'),
                            'job_contents_detail': row.get('job_contents_detail'),
                            'salary': row.get('salary'),
                            'salary_type_cd': int(row.get('salary_type_cd')) if pd.notna(row.get('salary_type_cd')) else None,
                            'min_salary': int(row.get('min_salary')) if pd.notna(row.get('min_salary')) else None,
                            'max_salary': int(row.get('max_salary')) if pd.notna(row.get('max_salary')) else None,
                            'age': row.get('age'),
                            'max_age_cd': int(row.get('max_age_cd')) if pd.notna(row.get('max_age_cd')) else None,
                            'min_age_cd': int(row.get('min_age_cd')) if pd.notna(row.get('min_age_cd')) else None,
                            'max_age': int(row.get('max_age')) if pd.notna(row.get('max_age')) else None,
                            'min_age': int(row.get('min_age')) if pd.notna(row.get('min_age')) else None,
                            'area': row.get('area'),
                            'area_address': row.get('area_address'),
                            'pref_cd': int(row.get('pref_cd')) if pd.notna(row.get('pref_cd')) else None,
                            'city_cd': int(row.get('city_cd')) if pd.notna(row.get('city_cd')) else None,
                            'hours': row.get('hours'),
                            'area_eki': row.get('area_eki'),
                            'ensen_block_cd': row.get('ensen_block_cd'),
                            'route_cd': row.get('route_cd'),
                            'station_cd': row.get('station_cd'),
                            'business': row.get('business'),
                            'traffic': row.get('traffic'),
                            'employment_type': row.get('employment_type'),
                            'employment_type_cd': int(row.get('employment_type_cd')) if pd.notna(row.get('employment_type_cd')) else None,
                            'welfare': row.get('welfare'),
                            'requirement_way': row.get('requirement_way'),
                            'requirement': row.get('requirement'),
                            'special_edition_cd': row.get('special_edition_cd'),
                            'url': row.get('url'),
                            'transfer_url': row.get('transfer_url'),
                            'employment_term_cd': int(row.get('employment_term_cd')) if pd.notna(row.get('employment_term_cd')) else None,
                            'start_at': row.get('start_at'),
                            'end_at': row.get('end_at'),
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                        # Handle features as JSON if present
                        if 'features' in row and pd.notna(row['features']):
                            job_data['features'] = str(row['features'])
                        else:
                            job_data['features'] = None

                        # Insert into database
                        insert_query = """
                            INSERT INTO jobs (job_id, import_from, client_cd, endcl_cd, application_cd,
                                application_name, company_name, company_kana, occupation_cd1, occupation_cd2,
                                occupation_cd3, job_contents, job_contents_detail, salary, salary_type_cd,
                                min_salary, max_salary, age, max_age_cd, min_age_cd, max_age, min_age,
                                area, area_address, pref_cd, city_cd, hours, area_eki, ensen_block_cd,
                                route_cd, station_cd, business, traffic, employment_type, employment_type_cd,
                                welfare, requirement_way, requirement, special_edition_cd, url, transfer_url,
                                employment_term_cd, start_at, end_at, features, created_at, updated_at)
                            VALUES (:job_id, :import_from, :client_cd, :endcl_cd, :application_cd,
                                :application_name, :company_name, :company_kana, :occupation_cd1, :occupation_cd2,
                                :occupation_cd3, :job_contents, :job_contents_detail, :salary, :salary_type_cd,
                                :min_salary, :max_salary, :age, :max_age_cd, :min_age_cd, :max_age, :min_age,
                                :area, :area_address, :pref_cd, :city_cd, :hours, :area_eki, :ensen_block_cd,
                                :route_cd, :station_cd, :business, :traffic, :employment_type, :employment_type_cd,
                                :welfare, :requirement_way, :requirement, :special_edition_cd, :url, :transfer_url,
                                :employment_term_cd, :start_at, :end_at, :features, :created_at, :updated_at)
                            ON CONFLICT (job_id) DO UPDATE SET
                                updated_at = :updated_at
                        """

                        await session.execute(text(insert_query), job_data)
                        results['imported'] += 1

                    except Exception as e:
                        self.logger.warning(f"Error importing job {row.get('job_id', 'unknown')}: {e}")
                        results['errors'] += 1
                        continue

                # Commit after each chunk
                await session.commit()
                self.logger.info(f"Imported chunk {total_chunks}: {results['imported']} records total...")

                # Limit chunks in test mode
                if test_mode and total_chunks >= 1:
                    break

            # Get final count
            count_result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
            final_count = count_result.scalar()
            self.logger.info(f"Total jobs in database: {final_count}")

        return results

    async def create_fts_index(self):
        """Create full-text search capabilities for jobs"""
        async with await self.get_db_session() as session:
            try:
                # For SQLite, create FTS virtual table for job searching
                fts_sql = """
                CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts
                USING fts5(
                    job_id,
                    company_name,
                    job_contents,
                    job_contents_detail,
                    area,
                    content=jobs,
                    content_rowid=id
                )
                """

                await session.execute(text(fts_sql))
                await session.commit()

                # Populate FTS table
                populate_sql = """
                INSERT INTO jobs_fts (rowid, job_id, company_name, job_contents, job_contents_detail, area)
                SELECT id, job_id, company_name, job_contents, job_contents_detail, area FROM jobs
                WHERE id NOT IN (SELECT rowid FROM jobs_fts)
                """

                await session.execute(text(populate_sql))
                await session.commit()

                self.logger.info("Created full-text search index for jobs")

            except Exception as e:
                self.logger.warning(f"FTS not available or already exists: {e}")

    async def analyze_imported_data(self):
        """Analyze imported job data"""
        async with await self.get_db_session() as session:
            # Get statistics
            stats_query = """
            SELECT
                COUNT(*) as total_jobs,
                COUNT(DISTINCT company_name) as unique_companies,
                COUNT(DISTINCT pref_cd) as prefectures,
                AVG(min_salary) as avg_min_salary,
                MAX(max_salary) as max_salary_offered,
                COUNT(DISTINCT occupation_cd1) as occupation_types,
                COUNT(DISTINCT employment_type_cd) as employment_types
            FROM jobs
            """

            result = await session.execute(text(stats_query))
            stats = result.fetchone()

            print("\n📊 Job Data Statistics:")
            print(f"  Total Jobs: {stats[0]:,}")
            print(f"  Unique Companies: {stats[1]:,}")
            print(f"  Prefectures Covered: {stats[2]}")
            print(f"  Average Min Salary: ¥{int(stats[3]):,}" if stats[3] else "  Average Min Salary: N/A")
            print(f"  Max Salary Offered: ¥{int(stats[4]):,}" if stats[4] else "  Max Salary Offered: N/A")
            print(f"  Occupation Types: {stats[5]}")
            print(f"  Employment Types: {stats[6]}")

            # Get top companies by job count
            top_companies_query = """
            SELECT company_name, COUNT(*) as job_count
            FROM jobs
            WHERE company_name IS NOT NULL
            GROUP BY company_name
            ORDER BY job_count DESC
            LIMIT 5
            """

            result = await session.execute(text(top_companies_query))
            top_companies = result.fetchall()

            print("\n🏢 Top 5 Companies by Job Postings:")
            for company in top_companies:
                if company[0]:
                    print(f"  - {company[0]}: {company[1]} jobs")

            # Get prefecture distribution
            prefecture_query = """
            SELECT pref_cd, COUNT(*) as job_count
            FROM jobs
            WHERE pref_cd IS NOT NULL
            GROUP BY pref_cd
            ORDER BY job_count DESC
            LIMIT 5
            """

            result = await session.execute(text(prefecture_query))
            top_prefectures = result.fetchall()

            print("\n📍 Top 5 Prefectures by Job Count:")
            for pref in top_prefectures:
                print(f"  - Prefecture {pref[0]}: {pref[1]:,} jobs")


async def main():
    """Main import function"""
    parser = argparse.ArgumentParser(description='Import job data from CSV files')
    parser.add_argument(
        '--data-dir',
        type=str,
        default='../data',
        help='Directory containing CSV files'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: import only 1000 records'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze existing data, do not import'
    )

    args = parser.parse_args()

    importer = JobDataImporter(args.data_dir)

    if args.analyze_only:
        await importer.analyze_imported_data()
    else:
        print("🚀 Starting job data import...")
        if args.test:
            print("📝 Running in test mode (1000 records)")
        else:
            print("📚 Importing full dataset (195,683 records)...")
            print("⏳ This may take several minutes...")

        results = await importer.import_job_data(test_mode=args.test)

        print(f"\n📊 Import Results:")
        print(f"  ✅ Imported: {results['imported']:,} jobs")
        print(f"  ⚠️ Skipped: {results['skipped']:,} jobs")
        print(f"  ❌ Errors: {results['errors']}")

        if results['imported'] > 0:
            print("\n🔍 Creating full-text search index...")
            await importer.create_fts_index()

            print("\n📈 Analyzing imported data...")
            await importer.analyze_imported_data()

            print("\n✨ Job data import completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ No jobs were imported!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())