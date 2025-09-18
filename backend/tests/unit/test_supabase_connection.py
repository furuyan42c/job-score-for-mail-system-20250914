"""
T066: Supabase環境セットアップ - TDD RED Phase
失敗するテストを作成（Supabase接続確認）
"""

import pytest
import requests
from unittest.mock import patch
import asyncio
import asyncpg


class TestSupabaseConnection:
    """Supabase接続テスト - RED Phase（必ず失敗する）"""

    def test_supabase_api_server_running(self):
        """
        テスト: Supabase APIサーバー起動確認
        期待結果: 現在は失敗（supabase startしていないため）
        """
        # Supabase API endpoint (localhost:54321)
        api_url = "http://localhost:54321/rest/v1/"

        try:
            response = requests.get(api_url, timeout=5)
            # サーバーが起動していれば200番台のレスポンス
            assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"

            # APIサーバーが起動している場合の確認
            assert "supabase" in response.headers.get('server', '').lower(), "Not Supabase server"

        except requests.exceptions.ConnectionError:
            # 予想される失敗: Supabaseサーバーが起動していない
            pytest.fail("🔴 EXPECTED FAILURE: Supabase server not running on localhost:54321")

    def test_supabase_studio_accessible(self):
        """
        テスト: Supabase Studio UI アクセス確認
        期待結果: 現在は失敗（supabase startしていないため）
        """
        studio_url = "http://localhost:54323"

        try:
            response = requests.get(studio_url, timeout=5)
            assert response.status_code == 200, f"Studio not accessible: {response.status_code}"

            # Studio UIの確認
            assert "supabase" in response.text.lower(), "Not Supabase Studio"

        except requests.exceptions.ConnectionError:
            # 予想される失敗: Supabase Studioが起動していない
            pytest.fail("🔴 EXPECTED FAILURE: Supabase Studio not running on localhost:54323")

    @pytest.mark.asyncio
    async def test_postgres_database_connection(self):
        """
        テスト: PostgreSQL データベース接続確認
        期待結果: 現在は失敗（supabase startしていないため）
        """
        # Supabase local database connection parameters
        db_config = {
            "host": "localhost",
            "port": 54322,
            "database": "postgres",
            "user": "postgres",
            "password": "postgres"
        }

        try:
            # PostgreSQL接続試行
            conn = await asyncpg.connect(**db_config)

            # 基本的なクエリ実行
            result = await conn.fetchval("SELECT version()")
            assert "PostgreSQL" in result, f"Not PostgreSQL: {result}"

            # 接続を閉じる
            await conn.close()

        except (OSError, asyncpg.exceptions.CannotConnectNowError):
            # 予想される失敗: PostgreSQLサーバーが起動していない
            pytest.fail("🔴 EXPECTED FAILURE: PostgreSQL not running on localhost:54322")

    def test_supabase_config_validation(self):
        """
        テスト: config.toml設定値の確認
        期待結果: これは成功する（設定ファイルは存在する）
        """
        import toml
        import os

        config_path = "supabase/config.toml"
        assert os.path.exists(config_path), f"Config file not found: {config_path}"

        with open(config_path, 'r') as f:
            config = toml.load(f)

        # 必須設定の確認
        assert config['api']['port'] == 54321, "API port mismatch"
        assert config['db']['port'] == 54322, "DB port mismatch"
        assert config['studio']['port'] == 54323, "Studio port mismatch"
        assert config['auth']['enabled'] is True, "Auth not enabled"
        assert config['realtime']['enabled'] is True, "Realtime not enabled"

        # サイトURL確認（フロントエンド用）
        expected_site_url = "http://127.0.0.1:3000"
        assert config['auth']['site_url'] == expected_site_url, f"Site URL mismatch: {config['auth']['site_url']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])