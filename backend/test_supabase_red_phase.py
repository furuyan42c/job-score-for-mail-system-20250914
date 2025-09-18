#!/usr/bin/env python3
"""
Simple script to test Supabase connection - RED Phase
This should fail as Supabase is not running locally
"""

import requests
import sys
import asyncio
import asyncpg


def test_supabase_api():
    """Test Supabase API server"""
    print("🔴 RED Phase Test 1: Testing Supabase API server on localhost:54321...")
    try:
        response = requests.get("http://localhost:54321/rest/v1/", timeout=2)
        if response.status_code in [200, 401]:
            print("✅ UNEXPECTED: Supabase API server is running!")
            return False
        else:
            print(f"❌ Got unexpected status: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print("✅ EXPECTED: Supabase API server is NOT running (Connection refused)")
        return True
    except requests.exceptions.Timeout:
        print("✅ EXPECTED: Supabase API server timeout (not running)")
        return True


def test_supabase_studio():
    """Test Supabase Studio UI"""
    print("\n🔴 RED Phase Test 2: Testing Supabase Studio on localhost:54323...")
    try:
        response = requests.get("http://localhost:54323", timeout=2)
        if response.status_code == 200:
            print("✅ UNEXPECTED: Supabase Studio is running!")
            return False
        else:
            print(f"❌ Got unexpected status: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print("✅ EXPECTED: Supabase Studio is NOT running (Connection refused)")
        return True
    except requests.exceptions.Timeout:
        print("✅ EXPECTED: Supabase Studio timeout (not running)")
        return True


async def test_postgres_connection():
    """Test PostgreSQL database connection"""
    print("\n🔴 RED Phase Test 3: Testing PostgreSQL on localhost:54322...")
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=54322,
            database="postgres",
            user="postgres",
            password="postgres",
            timeout=2
        )
        await conn.close()
        print("✅ UNEXPECTED: PostgreSQL is running!")
        return False
    except (OSError, asyncpg.exceptions.CannotConnectNowError, asyncio.TimeoutError) as e:
        print(f"✅ EXPECTED: PostgreSQL is NOT running ({type(e).__name__})")
        return True


def test_config_file():
    """Test Supabase configuration file"""
    print("\n🔴 RED Phase Test 4: Testing Supabase config file...")
    import os
    import toml

    config_path = "../supabase/config.toml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = toml.load(f)

        # Check required settings
        checks = [
            (config.get('api', {}).get('port') == 54321, "API port configured"),
            (config.get('db', {}).get('port') == 54322, "DB port configured"),
            (config.get('studio', {}).get('port') == 54323, "Studio port configured"),
            (config.get('auth', {}).get('enabled') is True, "Auth enabled"),
            (config.get('realtime', {}).get('enabled') is True, "Realtime enabled"),
        ]

        all_passed = True
        for check, description in checks:
            if check:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
                all_passed = False

        if all_passed:
            print("✅ Config file is properly configured")
            return True
        else:
            print("❌ Config file has issues")
            return False
    else:
        print(f"❌ Config file not found at {config_path}")
        return False


def test_migration_file():
    """Test initial migration file"""
    print("\n🔴 RED Phase Test 5: Testing initial migration file...")
    import os

    migration_path = "../supabase/migrations/20250917000000_init.sql"
    if os.path.exists(migration_path):
        with open(migration_path, 'r') as f:
            content = f.read()

        # Check for required content
        checks = [
            ("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"" in content, "UUID extension"),
            ("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\"" in content, "Pgcrypto extension"),
            ("CREATE TABLE IF NOT EXISTS public.system_config" in content, "System config table"),
            ("CREATE TABLE IF NOT EXISTS public.audit_log" in content, "Audit log table"),
            ("CREATE OR REPLACE FUNCTION public.health_check()" in content, "Health check function"),
        ]

        all_passed = True
        for check, description in checks:
            if check:
                print(f"  ✅ {description} found")
            else:
                print(f"  ❌ {description} not found")
                all_passed = False

        if all_passed:
            print("✅ Migration file is properly configured")
            return True
        else:
            print("❌ Migration file has issues")
            return False
    else:
        print(f"❌ Migration file not found at {migration_path}")
        return False


def main():
    """Run all RED phase tests"""
    print("=" * 60)
    print("🔴 TDD RED PHASE - SUPABASE CONNECTION TESTS")
    print("These tests SHOULD FAIL because Supabase is not running")
    print("=" * 60)

    results = []

    # Test 1: API server
    results.append(test_supabase_api())

    # Test 2: Studio UI
    results.append(test_supabase_studio())

    # Test 3: PostgreSQL
    loop = asyncio.get_event_loop()
    results.append(loop.run_until_complete(test_postgres_connection()))

    # Test 4: Config file
    results.append(test_config_file())

    # Test 5: Migration file
    results.append(test_migration_file())

    print("\n" + "=" * 60)
    print("📊 RED PHASE SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests in RED state (as expected): {passed}/{total}")

    if passed == total:
        print("✅ All tests are properly in RED state!")
        print("👉 Next step: Run 'supabase start' to move to GREEN phase")
        return 0
    else:
        print("⚠️ Some tests are not in expected RED state")
        print("👉 Please check if Supabase is already running")
        return 1


if __name__ == "__main__":
    sys.exit(main())