#!/usr/bin/env python3
"""
Test script to verify Supabase schema migration - T067
Verifies all 20 tables are present in the database
"""

import asyncio
import asyncpg
import sys


async def test_schema_migration():
    """Test that all 20 tables exist in Supabase"""
    print("=" * 60)
    print("🔍 T067: SCHEMA MIGRATION VERIFICATION")
    print("=" * 60)

    # Expected tables grouped by category
    expected_tables = {
        "Master Tables (5)": [
            "prefecture_master",
            "city_master",
            "occupation_master",
            "employment_type_master",
            "feature_master"
        ],
        "Core Tables (3)": [
            "job_data",
            "user_actions",
            "matching_results"
        ],
        "Scoring Tables (4)": [
            "basic_scoring",
            "seo_scoring",
            "personalized_scoring",
            "keyword_scoring"
        ],
        "Batch Tables (2)": [
            "batch_jobs",
            "processing_logs"
        ],
        "Email Tables (3)": [
            "email_sections",
            "section_jobs",
            "email_generation_logs"
        ],
        "Statistics Tables (3)": [
            "user_statistics",
            "semrush_keywords",
            "system_metrics"
        ]
    }

    # Connection parameters for Supabase local
    db_config = {
        "host": "localhost",
        "port": 54322,
        "database": "postgres",
        "user": "postgres",
        "password": "postgres"
    }

    try:
        # Connect to database
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to Supabase database")
        print()

        # Query for all tables
        query = """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """

        existing_tables = await conn.fetch(query)
        existing_table_names = {row['tablename'] for row in existing_tables}

        total_expected = 0
        total_found = 0

        # Check each category
        for category, tables in expected_tables.items():
            print(f"\n{category}:")
            for table in tables:
                total_expected += 1
                if table in existing_table_names:
                    print(f"  ✅ {table}")
                    total_found += 1
                else:
                    print(f"  ❌ {table} - NOT FOUND")

        # Check for Supabase-specific tables
        print("\n\nSupabase System Tables Found:")
        supabase_tables = [
            "system_config",
            "audit_log",
            "_test_connection"
        ]

        for table in supabase_tables:
            if table in existing_table_names:
                print(f"  ✅ {table}")

        # Summary
        print("\n" + "=" * 60)
        print("📊 SCHEMA VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Expected Tables: {total_expected}")
        print(f"Found Tables: {total_found}")
        print(f"Total Tables in Schema: {len(existing_table_names)}")

        if total_found == total_expected:
            print("\n✅ All expected tables are present!")
            print("✅ T067: Schema migration SUCCESSFUL")

            # Test a sample query
            print("\n🔍 Testing sample query...")
            test_query = "SELECT * FROM job_data LIMIT 1;"
            result = await conn.fetch(test_query)
            print(f"✅ Query executed successfully (returned {len(result)} rows)")

            await conn.close()
            return 0
        else:
            print(f"\n⚠️ Missing {total_expected - total_found} tables")
            print("❌ T067: Schema migration INCOMPLETE")
            await conn.close()
            return 1

    except asyncpg.exceptions.CannotConnectNowError as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_schema_migration()))