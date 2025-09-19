#!/usr/bin/env python3
"""
T087: SEO Keyword Data Import Script

Imports SEO keyword data from SEMRush export:
- semrush_kw20250824_sample.csv (1,001 records)

Includes search volume, difficulty, and creates full-text search indexes.

Usage:
    python scripts/import_seo_keywords.py --data-dir ../data
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


class SEOKeywordImporter:
    """SEO Keyword data import handler"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.logger = setup_logging()
        self.csv_file = 'semrush_kw20250824_sample.csv'

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
        """Check if SEO keywords table exists"""
        try:
            # SQLite compatible check
            result = await session.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = 'seo_keywords'")
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking table: {e}")
            return False

    async def create_seo_keywords_table(self, session: AsyncSession):
        """Create SEO keywords table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS seo_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            search_volume INTEGER,
            difficulty REAL,
            cpc REAL,
            category TEXT,
            intent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        try:
            await session.execute(text(create_table_sql))
            await session.commit()
            self.logger.info("Created seo_keywords table")

            # Create index for full-text search
            await session.execute(
                text("CREATE INDEX IF NOT EXISTS idx_seo_keywords_keyword ON seo_keywords(keyword)")
            )
            await session.commit()
            self.logger.info("Created keyword index")

        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            await session.rollback()

    async def import_seo_data(self) -> Dict[str, int]:
        """Import SEO keyword data from CSV"""
        results = {'imported': 0, 'skipped': 0, 'errors': 0}

        csv_path = self.data_dir / self.csv_file

        if not csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            return results

        async with await self.get_db_session() as session:
            # Ensure table exists
            if not await self.check_table_exists(session):
                await self.create_seo_keywords_table(session)

            # Read CSV
            self.logger.info(f"Reading CSV: {csv_path}")
            try:
                # Read with different encodings to handle Japanese text
                df = pd.read_csv(csv_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, encoding='shift-jis')

            self.logger.info(f"CSV columns: {list(df.columns)}")
            self.logger.info(f"Total records: {len(df)}")

            # Process data
            for idx, row in df.iterrows():
                try:
                    # Map columns based on typical SEMRush export
                    keyword_data = {
                        'keyword': str(row.get('Keyword', row.get('keyword', row.iloc[0]))),
                        'search_volume': int(row.get('Search Volume', row.get('Volume', row.get('search_volume', 0))) if pd.notna(row.get('Search Volume', row.get('Volume', row.get('search_volume', 0)))) else 0),
                        'difficulty': float(row.get('Keyword Difficulty', row.get('KD %', row.get('difficulty', 0))) if pd.notna(row.get('Keyword Difficulty', row.get('KD %', row.get('difficulty', 0)))) else 0.0),
                        'cpc': float(row.get('CPC', row.get('cpc', 0))) if pd.notna(row.get('CPC', row.get('cpc', 0))) else 0.0,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    # Insert into database
                    insert_query = """
                        INSERT INTO seo_keywords (keyword, search_volume, difficulty, cpc, created_at, updated_at)
                        VALUES (:keyword, :search_volume, :difficulty, :cpc, :created_at, :updated_at)
                        ON CONFLICT (keyword) DO UPDATE SET
                            search_volume = :search_volume,
                            difficulty = :difficulty,
                            cpc = :cpc,
                            updated_at = :updated_at
                    """

                    await session.execute(text(insert_query), keyword_data)
                    results['imported'] += 1

                    if (idx + 1) % 100 == 0:
                        await session.commit()
                        self.logger.info(f"Imported {idx + 1} records...")

                except Exception as e:
                    self.logger.warning(f"Error importing row {idx}: {e}")
                    results['errors'] += 1
                    continue

            # Final commit
            await session.commit()

            # Get final count
            count_result = await session.execute(text("SELECT COUNT(*) FROM seo_keywords"))
            final_count = count_result.scalar()
            self.logger.info(f"Total keywords in database: {final_count}")

        return results

    async def create_fts_index(self):
        """Create full-text search capabilities"""
        async with await self.get_db_session() as session:
            try:
                # For SQLite, create FTS virtual table
                fts_sql = """
                CREATE VIRTUAL TABLE IF NOT EXISTS seo_keywords_fts
                USING fts5(
                    keyword,
                    content=seo_keywords,
                    content_rowid=id
                )
                """

                await session.execute(text(fts_sql))
                await session.commit()

                # Populate FTS table
                populate_sql = """
                INSERT INTO seo_keywords_fts (rowid, keyword)
                SELECT id, keyword FROM seo_keywords
                WHERE id NOT IN (SELECT rowid FROM seo_keywords_fts)
                """

                await session.execute(text(populate_sql))
                await session.commit()

                self.logger.info("Created full-text search index")

            except Exception as e:
                self.logger.warning(f"FTS not available or already exists: {e}")

    async def analyze_imported_data(self):
        """Analyze imported SEO data"""
        async with await self.get_db_session() as session:
            # Get statistics
            stats_query = """
            SELECT
                COUNT(*) as total_keywords,
                AVG(search_volume) as avg_volume,
                MAX(search_volume) as max_volume,
                MIN(search_volume) as min_volume,
                AVG(difficulty) as avg_difficulty
            FROM seo_keywords
            """

            result = await session.execute(text(stats_query))
            stats = result.fetchone()

            print("\n📊 SEO Keyword Data Statistics:")
            print(f"  Total Keywords: {stats[0]}")
            print(f"  Average Search Volume: {stats[1]:.0f}" if stats[1] else "  Average Search Volume: 0")
            print(f"  Max Search Volume: {stats[2]}" if stats[2] else "  Max Search Volume: 0")
            print(f"  Min Search Volume: {stats[3]}" if stats[3] else "  Min Search Volume: 0")
            print(f"  Average Difficulty: {stats[4]:.2f}%" if stats[4] else "  Average Difficulty: 0%")

            # Get top keywords by volume
            top_keywords_query = """
            SELECT keyword, search_volume, difficulty
            FROM seo_keywords
            ORDER BY search_volume DESC
            LIMIT 5
            """

            result = await session.execute(text(top_keywords_query))
            top_keywords = result.fetchall()

            print("\n🔝 Top 5 Keywords by Search Volume:")
            for kw in top_keywords:
                print(f"  - {kw[0]}: {kw[1]} searches (difficulty: {kw[2]:.0f}%)")


async def main():
    """Main import function"""
    parser = argparse.ArgumentParser(description='Import SEO keyword data from SEMRush CSV')
    parser.add_argument(
        '--data-dir',
        type=str,
        default='../data',
        help='Directory containing CSV files'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze existing data, do not import'
    )

    args = parser.parse_args()

    importer = SEOKeywordImporter(args.data_dir)

    if args.analyze_only:
        await importer.analyze_imported_data()
    else:
        print("🚀 Starting SEO keyword data import...")
        results = await importer.import_seo_data()

        print(f"\n📊 Import Results:")
        print(f"  ✅ Imported: {results['imported']} keywords")
        print(f"  ⚠️ Skipped: {results['skipped']} keywords")
        print(f"  ❌ Errors: {results['errors']}")

        if results['imported'] > 0:
            print("\n🔍 Creating full-text search index...")
            await importer.create_fts_index()

            print("\n📈 Analyzing imported data...")
            await importer.analyze_imported_data()

            print("\n✨ SEO keyword import completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ No keywords were imported!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())