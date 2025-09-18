"""
T067: Supabaseスキーマ移行 - TDD RED Phase
失敗するテストを作成（20テーブルスキーマ確認）
"""

import pytest
import asyncio
import asyncpg
from typing import List, Dict


class TestSupabaseSchema:
    """Supabaseスキーマ移行テスト - RED Phase（必ず失敗する）"""

    @pytest.fixture
    async def db_connection(self):
        """Supabase PostgreSQL接続"""
        conn = await asyncpg.connect(
            host="localhost",
            port=54322,
            database="postgres",
            user="postgres",
            password="postgres"
        )
        yield conn
        await conn.close()

    @pytest.mark.asyncio
    async def test_job_matching_tables_count(self, db_connection):
        """
        テスト: ジョブマッチングシステム用テーブル数確認
        期待結果: 現在は失敗（20テーブルが存在しない）
        """
        # 期待される20テーブル
        expected_tables = [
            # マスターデータ (5 tables)
            'prefecture_master',
            'city_master',
            'occupation_master',
            'employment_type_master',
            'feature_master',

            # コアデータ (3 tables)
            'job_data',
            'user_actions',
            'matching_results',

            # スコアリング (4 tables)
            'basic_scoring',
            'seo_scoring',
            'personalized_scoring',
            'keyword_scoring',

            # バッチ処理 (2 tables)
            'batch_jobs',
            'processing_logs',

            # セクション・メール (3 tables)
            'email_sections',
            'section_jobs',
            'email_generation_logs',

            # 統計・監視 (3 tables)
            'user_statistics',
            'semrush_keywords',
            'system_metrics'
        ]

        # 実際のテーブル一覧を取得
        actual_tables = await db_connection.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        actual_table_names = [row['table_name'] for row in actual_tables]

        # デバッグ出力
        print(f"Expected {len(expected_tables)} tables: {expected_tables}")
        print(f"Actual {len(actual_table_names)} tables: {actual_table_names}")

        # 20テーブルの存在確認
        missing_tables = [table for table in expected_tables if table not in actual_table_names]

        if missing_tables:
            pytest.fail(
                f"🔴 EXPECTED FAILURE: Missing {len(missing_tables)} tables: {missing_tables}"
            )

        # 期待される20テーブルが全て存在する場合
        assert len(actual_table_names) >= 20, f"Expected at least 20 tables, got {len(actual_table_names)}"

    @pytest.mark.asyncio
    async def test_master_data_tables_structure(self, db_connection):
        """
        テスト: マスターデータテーブル構造確認
        期待結果: 現在は失敗（テーブル構造が未定義）
        """
        # prefecture_master テーブル構造確認
        columns = await db_connection.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'prefecture_master'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

        if not columns:
            pytest.fail("🔴 EXPECTED FAILURE: prefecture_master table does not exist")

        # 必須カラムの確認
        expected_columns = {'code', 'name', 'region', 'created_at', 'updated_at'}
        actual_columns = {row['column_name'] for row in columns}

        missing_columns = expected_columns - actual_columns
        if missing_columns:
            pytest.fail(f"🔴 Missing columns in prefecture_master: {missing_columns}")

    @pytest.mark.asyncio
    async def test_job_data_table_structure(self, db_connection):
        """
        テスト: job_dataテーブル構造確認
        期待結果: 現在は失敗（メインテーブルが未定義）
        """
        columns = await db_connection.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'job_data'
            AND table_schema = 'public'
        """)

        if not columns:
            pytest.fail("🔴 EXPECTED FAILURE: job_data table does not exist")

        # 重要カラムの確認
        column_names = {row['column_name'] for row in columns}
        critical_columns = {
            'job_id', 'endcl_cd', 'fee', 'hourly_wage',
            'application_name', 'employment_type_code',
            'prefecture_cd', 'city_cd', 'occupation_code'
        }

        missing_critical = critical_columns - column_names
        if missing_critical:
            pytest.fail(f"🔴 Missing critical columns in job_data: {missing_critical}")

    @pytest.mark.asyncio
    async def test_scoring_tables_exist(self, db_connection):
        """
        テスト: スコアリングテーブル存在確認
        期待結果: 現在は失敗（スコアリングテーブルが未作成）
        """
        scoring_tables = [
            'basic_scoring',
            'seo_scoring',
            'personalized_scoring',
            'keyword_scoring'
        ]

        for table_name in scoring_tables:
            table_exists = await db_connection.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = $1 AND table_schema = 'public'
                )
            """, table_name)

            if not table_exists:
                pytest.fail(f"🔴 EXPECTED FAILURE: {table_name} table does not exist")

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_connection):
        """
        テスト: 外部キー制約の確認
        期待結果: 現在は失敗（制約が未設定）
        """
        # 重要な外部キー制約を確認
        constraints = await db_connection.fetch("""
            SELECT
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """)

        if len(constraints) == 0:
            pytest.fail("🔴 EXPECTED FAILURE: No foreign key constraints found")

        # 最低限の外部キー制約数を確認
        assert len(constraints) >= 10, f"Expected at least 10 FK constraints, got {len(constraints)}"

    @pytest.mark.asyncio
    async def test_indexes_exist(self, db_connection):
        """
        テスト: 重要インデックスの存在確認
        期待結果: 現在は失敗（インデックスが未作成）
        """
        indexes = await db_connection.fetch("""
            SELECT indexname, tablename, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname NOT LIKE '%_pkey'
        """)

        if len(indexes) == 0:
            pytest.fail("🔴 EXPECTED FAILURE: No custom indexes found")

        # 最低限のインデックス数を確認（主キー以外）
        assert len(indexes) >= 15, f"Expected at least 15 custom indexes, got {len(indexes)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])