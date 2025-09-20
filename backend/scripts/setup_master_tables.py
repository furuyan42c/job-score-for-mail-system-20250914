#!/usr/bin/env python3
"""
Setup master tables for database
Creates prefecture_master, employment_type_master, and occupation_master tables
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_master_tables():
    """Create master tables if they don't exist"""
    async with engine.begin() as conn:
        try:
            # Create prefecture_master table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS prefecture_master (
                    code INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Insert sample prefectures
            await conn.execute(text("""
                INSERT OR IGNORE INTO prefecture_master (code, name) VALUES
                (13, '東京都'),
                (27, '大阪府'),
                (14, '神奈川県'),
                (23, '愛知県'),
                (12, '千葉県'),
                (11, '埼玉県'),
                (1, '北海道'),
                (40, '福岡県')
            """))

            # Create employment_type_master table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS employment_type_master (
                    code INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Insert employment types
            await conn.execute(text("""
                INSERT OR IGNORE INTO employment_type_master (code, name) VALUES
                (1, '正社員'),
                (2, '契約社員'),
                (3, 'パート・アルバイト'),
                (4, '派遣社員'),
                (5, 'インターン'),
                (6, '業務委託')
            """))

            # Create occupation_master table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS occupation_master (
                    code INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Insert occupation types
            await conn.execute(text("""
                INSERT OR IGNORE INTO occupation_master (code, name) VALUES
                (1, 'エンジニア'),
                (2, '営業'),
                (3, 'マーケティング'),
                (4, 'デザイナー'),
                (5, '事務・管理'),
                (6, 'サービス・販売'),
                (7, 'コンサルタント'),
                (8, 'プロジェクトマネージャー')
            """))

            logger.info("✅ Master tables created successfully")

        except Exception as e:
            logger.error(f"❌ Error creating master tables: {e}")
            raise

async def validate_database():
    """Validate database setup"""
    async with engine.begin() as conn:
        try:
            # Check tables exist
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """))
            tables = [row[0] for row in result]

            logger.info(f"📊 Found {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table}")

            # Check required tables
            required_tables = [
                'prefecture_master',
                'employment_type_master',
                'occupation_master',
                'users',
                'jobs'
            ]

            missing = [t for t in required_tables if t not in tables]
            if missing:
                logger.warning(f"⚠️ Missing tables: {missing}")
                return False

            # Check data in master tables
            for table in ['prefecture_master', 'employment_type_master', 'occupation_master']:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                logger.info(f"  {table}: {count} records")

            logger.info("✅ All required tables exist")
            return True

        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return False

async def main():
    """Main setup function"""
    logger.info("🚀 Starting database master tables setup...")

    # Create master tables
    await create_master_tables()

    # Validate setup
    is_valid = await validate_database()

    if is_valid:
        logger.info("✅ Database setup complete and validated!")
    else:
        logger.error("❌ Database setup incomplete")

if __name__ == "__main__":
    asyncio.run(main())