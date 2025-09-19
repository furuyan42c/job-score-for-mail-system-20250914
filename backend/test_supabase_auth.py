#!/usr/bin/env python3
"""
Supabase Auth統合テストスクリプト
"""

import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:54321")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0")

async def test_supabase_connection():
    """Supabase接続テスト"""
    print("=" * 60)
    print("Supabase Auth統合テスト")
    print("=" * 60)

    try:
        # Supabaseクライアント作成
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print(f"✅ Supabase Client created successfully")
        print(f"   URL: {SUPABASE_URL}")

        # テストユーザー情報
        test_email = "test@example.com"
        test_password = "TestPassword123!"

        # 1. ユーザー登録テスト（エラーは無視 - 既に存在する可能性）
        print("\n1. User Registration Test")
        try:
            response = supabase.auth.sign_up({
                "email": test_email,
                "password": test_password
            })
            print(f"   ✅ User registered: {test_email}")
        except Exception as e:
            print(f"   ⚠️ Registration failed (may already exist): {str(e)[:50]}")

        # 2. ログインテスト
        print("\n2. Login Test")
        try:
            response = supabase.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            if response.user:
                print(f"   ✅ Login successful")
                print(f"   User ID: {response.user.id}")
                print(f"   Email: {response.user.email}")
            else:
                print(f"   ❌ Login failed - no user returned")
        except Exception as e:
            print(f"   ❌ Login error: {e}")

        # 3. セッション確認
        print("\n3. Session Test")
        session = supabase.auth.get_session()
        if session:
            print(f"   ✅ Session active")
            if hasattr(session, 'access_token'):
                print(f"   Access token: {session.access_token[:20]}...")
        else:
            print(f"   ⚠️ No active session")

        # 4. ユーザー情報取得
        print("\n4. Get User Test")
        user = supabase.auth.get_user()
        if user:
            print(f"   ✅ User data retrieved")
        else:
            print(f"   ⚠️ No user data available")

        # 5. ログアウトテスト
        print("\n5. Logout Test")
        try:
            supabase.auth.sign_out()
            print(f"   ✅ Logout successful")
        except Exception as e:
            print(f"   ❌ Logout error: {e}")

        print("\n" + "=" * 60)
        print("テスト完了")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 非同期実行
    success = asyncio.run(test_supabase_connection())
    exit(0 if success else 1)