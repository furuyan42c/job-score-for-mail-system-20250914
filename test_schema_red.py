#!/usr/bin/env python3
"""
T067: TDD RED Phase - Quick schema test (should fail)
"""

import asyncio
import asyncpg

async def test_schema_red_phase():
    """現在のSupabaseスキーマ状態確認（失敗期待）"""
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=54322,
            database="postgres",
            user="postgres",
            password="postgres"
        )

        # 期待される20テーブル
        expected_tables = [
            'prefecture_master', 'city_master', 'occupation_master',
            'employment_type_master', 'feature_master', 'job_data',
            'user_actions', 'matching_results', 'basic_scoring',
            'seo_scoring', 'personalized_scoring', 'keyword_scoring',
            'batch_jobs', 'processing_logs', 'email_sections',
            'section_jobs', 'email_generation_logs', 'user_statistics',
            'semrush_keywords', 'system_metrics'
        ]

        # 実際のテーブル一覧を取得
        actual_tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        actual_table_names = [row['table_name'] for row in actual_tables]

        print(f"Expected {len(expected_tables)} tables: {expected_tables}")
        print(f"Actual {len(actual_table_names)} tables: {actual_table_names}")

        missing_tables = [table for table in expected_tables if table not in actual_table_names]

        if missing_tables:
            print(f"🔴 RED PHASE SUCCESS: Missing {len(missing_tables)} tables: {missing_tables}")
            await conn.close()
            return True  # RED phaseが正常（テストが失敗）

        print(f"🟢 All {len(expected_tables)} tables exist - need to run GREEN phase")
        await conn.close()
        return False

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_schema_red_phase())
    exit(0)