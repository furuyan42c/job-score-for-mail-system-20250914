#!/usr/bin/env python3
"""
Supabaseテーブル状況調査スクリプト
_2025_09サフィックステーブルの確認
"""

import os
import sys
from supabase import create_client
import json

def check_supabase_tables():
    """Supabaseのテーブル状況を確認"""

    # 環境変数取得
    supabase_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0")

    try:
        # Supabaseクライアント作成
        supabase = create_client(supabase_url, supabase_key)

        print("🔍 Supabaseテーブル調査開始...")
        print(f"URL: {supabase_url}")

        # すべてのテーブル一覧取得
        try:
            # public スキーマのテーブル一覧を取得
            response = supabase.rpc('get_table_list').execute()

            if response.data:
                all_tables = response.data
            else:
                # 代替方法でテーブル一覧取得
                response = supabase.table('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
                all_tables = [row['table_name'] for row in response.data] if response.data else []

        except Exception as e:
            print(f"❌ テーブル一覧取得失敗: {e}")
            # 直接SQLでテーブル確認を試行
            try:
                query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%2025_09%'
                ORDER BY table_name;
                """
                response = supabase.rpc('exec_sql', {'sql': query}).execute()
                all_tables = [row[0] for row in response.data] if response.data else []
            except Exception as e2:
                print(f"❌ SQL実行も失敗: {e2}")
                return False

        # _2025_09 サフィックスのテーブルを検索
        target_suffixes = ['_2025_09', '_2025_09_18']
        found_tables = []

        for table in all_tables:
            for suffix in target_suffixes:
                if suffix in str(table):
                    found_tables.append(table)

        print(f"\n📋 発見されたテーブル数: {len(found_tables)}")

        if found_tables:
            print("\n🎯 対象テーブル:")
            for i, table in enumerate(found_tables, 1):
                print(f"  {i}. {table}")

                # テーブルの行数確認
                try:
                    count_response = supabase.table(table).select('*', count='exact').limit(1).execute()
                    row_count = count_response.count if hasattr(count_response, 'count') else 0
                    print(f"     └─ 行数: {row_count}")
                except Exception as e:
                    print(f"     └─ 行数取得失敗: {e}")
        else:
            print("\n✅ _2025_09 サフィックスのテーブルは見つかりませんでした")

        # 特定テーブルの存在確認
        target_tables = [
            'user_actions',
            'daily_job_picks',
            'user_job_mapping'
        ]

        print(f"\n🔍 特定テーブル存在確認:")
        for table in target_tables:
            try:
                response = supabase.table(table).select('*').limit(1).execute()
                exists = True
                row_count = len(response.data) if response.data else 0
                print(f"  ✅ {table} - 存在 (サンプル行数: {row_count})")
            except Exception as e:
                print(f"  ❌ {table} - 存在しない ({str(e)[:50]}...)")

        return True

    except Exception as e:
        print(f"❌ Supabase接続エラー: {e}")
        return False

if __name__ == "__main__":
    success = check_supabase_tables()
    sys.exit(0 if success else 1)