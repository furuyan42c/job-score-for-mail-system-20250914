#!/usr/bin/env python3
"""
T086: Master Data Import Script

Imports master data from CSV files into the database:
- prefecture_view.csv (50 records)
- city_view.csv (1,919 records)
- occupation_view.csv (173 records)
- employment_type_view.csv (11 records)
- salary_type_view.csv (7 records)
- feature_view.csv (79 records)

Usage:
    python scripts/import_master_data.py --data-dir ../data
"""

import asyncio
import pandas as pd
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


class MasterDataImporter:
    """Master data import handler"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.logger = setup_logging()

        # CSV file configurations
        self.csv_configs = {
            'prefecture_view.csv': {
                'table': 'prefecture_master',
                'csv_columns': ['pref_cd', 'name', 'region'],
                'db_columns': ['code', 'name', 'region'],
                'expected_count': 50
            },
            'city_view.csv': {
                'table': 'city_master',
                'csv_columns': ['city_cd', 'pref_cd', 'name', 'latitude', 'longitude'],
                'db_columns': ['code', 'pref_cd', 'name', 'latitude', 'longitude'],
                'expected_count': 1919
            },
            'employment_type_view.csv': {
                'table': 'employment_type_master',
                'csv_columns': ['employment_type_cd', 'name'],
                'db_columns': ['code', 'name'],
                'expected_count': 11
            },
            'feature_view.csv': {
                'table': 'feature_master',
                'csv_columns': ['feature_cd', 'name', 'group_name'],
                'db_columns': ['feature_code', 'feature_name', 'category'],
                'expected_count': 79
            },
            'occupation_view.csv': {
                'table': 'occupation_master',
                'csv_columns': ['occupation_cd1_v2', 'occupation_cd_name'],
                'db_columns': ['code', 'name'],
                'expected_count': 173
            }
        }

    async def get_db_session(self) -> AsyncSession:
        """Create database session"""
        engine = create_async_engine(
            settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
            echo=False
        )
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session_maker()

    async def check_table_exists(self, session: AsyncSession, table_name: str) -> bool:
        """Check if table exists in database"""
        try:
            # SQLite compatible table existence check
            result = await session.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = :table_name"),
                {"table_name": table_name}
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking table {table_name}: {e}")
            return False

    async def get_table_count(self, session: AsyncSession, table_name: str) -> int:
        """Get current record count in table"""
        try:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
        except Exception as e:
            self.logger.error(f"Error getting count from {table_name}: {e}")
            return 0

    def get_primary_key_for_table(self, table_name: str) -> str:
        """Get the primary key column name for a table"""
        primary_keys = {
            'prefecture_master': 'code',
            'city_master': 'code',
            'employment_type_master': 'code',
            'feature_master': 'feature_code',
            'occupation_master': 'code'
        }
        return primary_keys.get(table_name, 'id')

    def validate_csv_file(self, csv_path: Path, config: Dict[str, Any]) -> bool:
        """Validate CSV file structure"""
        if not csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            return False

        try:
            # Read first few rows to check structure
            df = pd.read_csv(csv_path, nrows=5)
            self.logger.info(f"CSV {csv_path.name} has {len(df.columns)} columns: {list(df.columns)}")

            # Check if required columns exist (flexible approach)
            csv_columns = config['csv_columns']
            if len(df.columns) < len(csv_columns):
                self.logger.warning(f"CSV {csv_path.name} has fewer columns than expected")

            return True

        except Exception as e:
            self.logger.error(f"Error validating CSV {csv_path}: {e}")
            return False

    async def import_csv_to_table(
        self,
        session: AsyncSession,
        csv_path: Path,
        config: Dict[str, Any]
    ) -> int:
        """Import CSV data to database table"""
        table_name = config['table']

        try:
            # Check if table exists
            if not await self.check_table_exists(session, table_name):
                self.logger.error(f"Table {table_name} does not exist")
                return 0

            # Check current data
            current_count = await self.get_table_count(session, table_name)
            if current_count > 0:
                self.logger.info(f"Table {table_name} already has {current_count} records")
                return current_count

            # Read CSV
            self.logger.info(f"Reading CSV: {csv_path}")
            df = pd.read_csv(csv_path)

            # Clean and prepare data
            df = df.dropna()  # Remove empty rows
            df = df.drop_duplicates()  # Remove duplicates

            # Map CSV columns to database columns
            csv_columns = config['csv_columns']
            db_columns = config['db_columns']

            # Create column mapping dictionary
            column_mapping = {}
            for i, csv_col in enumerate(csv_columns):
                if i < len(db_columns) and csv_col in df.columns:
                    column_mapping[csv_col] = db_columns[i]

            # Rename columns according to mapping
            df = df.rename(columns=column_mapping)

            # Keep only mapped columns
            df = df[list(column_mapping.values())]

            # Add metadata columns if they don't exist
            if 'created_at' not in df.columns:
                df['created_at'] = datetime.now()
            if 'updated_at' not in df.columns:
                df['updated_at'] = datetime.now()

            self.logger.info(f"Importing {len(df)} records to {table_name}")

            # Insert data in batches
            batch_size = 1000
            imported_count = 0

            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]

                # Convert to list of dictionaries
                records = batch_df.to_dict('records')

                # Build insert query
                columns = ', '.join(batch_df.columns)
                placeholders = ', '.join([f":{col}" for col in batch_df.columns])

                # Use appropriate primary key for conflict resolution
                primary_key = self.get_primary_key_for_table(table_name)
                insert_query = f"""
                    INSERT INTO {table_name} ({columns})
                    VALUES ({placeholders})
                    ON CONFLICT ({primary_key}) DO NOTHING
                """

                # Execute batch insert
                for record in records:
                    try:
                        await session.execute(text(insert_query), record)
                        imported_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to insert record: {e}")
                        continue

                await session.commit()
                self.logger.info(f"Imported batch {i//batch_size + 1}: {len(batch_df)} records")

            self.logger.info(f"Successfully imported {imported_count} records to {table_name}")
            return imported_count

        except Exception as e:
            self.logger.error(f"Error importing CSV {csv_path} to {table_name}: {e}")
            await session.rollback()
            return 0

    async def import_all_master_data(self) -> Dict[str, int]:
        """Import all master data CSV files"""
        results = {}

        async with await self.get_db_session() as session:
            self.logger.info("Starting master data import...")

            for csv_filename, config in self.csv_configs.items():
                csv_path = self.data_dir / csv_filename

                self.logger.info(f"\n--- Processing {csv_filename} ---")

                # Validate CSV
                if not self.validate_csv_file(csv_path, config):
                    results[csv_filename] = 0
                    continue

                # Import data
                imported_count = await self.import_csv_to_table(session, csv_path, config)
                results[csv_filename] = imported_count

                # Verify import
                final_count = await self.get_table_count(session, config['table'])
                expected_count = config['expected_count']

                if final_count >= expected_count * 0.9:  # Allow 10% variance
                    self.logger.info(f"✅ {csv_filename}: {final_count} records (expected ~{expected_count})")
                else:
                    self.logger.warning(f"⚠️ {csv_filename}: {final_count} records (expected ~{expected_count})")

        return results

    async def verify_master_data(self) -> bool:
        """Verify all master data was imported correctly"""
        self.logger.info("\n--- Verifying Master Data ---")
        all_good = True

        async with await self.get_db_session() as session:
            for csv_filename, config in self.csv_configs.items():
                table_name = config['table']
                expected_count = config['expected_count']

                current_count = await self.get_table_count(session, table_name)

                if current_count >= expected_count * 0.9:
                    self.logger.info(f"✅ {table_name}: {current_count} records")
                else:
                    self.logger.error(f"❌ {table_name}: {current_count} records (expected ~{expected_count})")
                    all_good = False

        return all_good


async def main():
    """Main import function"""
    parser = argparse.ArgumentParser(description='Import master data from CSV files')
    parser.add_argument(
        '--data-dir',
        type=str,
        required=True,
        help='Directory containing CSV files'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing data, do not import'
    )

    args = parser.parse_args()

    # Initialize importer
    importer = MasterDataImporter(args.data_dir)

    if args.verify_only:
        # Verify existing data
        success = await importer.verify_master_data()
        if success:
            print("\n🎉 All master data verified successfully!")
            sys.exit(0)
        else:
            print("\n❌ Master data verification failed!")
            sys.exit(1)
    else:
        # Import data
        print("🚀 Starting master data import...")
        results = await importer.import_all_master_data()

        # Print summary
        print("\n📊 Import Summary:")
        total_imported = 0
        for csv_file, count in results.items():
            print(f"  {csv_file}: {count} records")
            total_imported += count

        print(f"\nTotal imported: {total_imported} records")

        # Verify final state
        print("\n🔍 Verifying import...")
        success = await importer.verify_master_data()

        if success:
            print("\n🎉 Master data import completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Master data import completed with errors!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())