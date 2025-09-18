#!/usr/bin/env python3
"""
Quick PostgreSQL connection test for TDD GREEN phase
"""

import asyncio
import asyncpg

async def test_connection():
    try:
        # Supabase local database connection
        conn = await asyncpg.connect(
            host="localhost",
            port=54322,
            database="postgres",
            user="postgres",
            password="postgres"
        )

        # Basic query
        result = await conn.fetchval("SELECT version()")
        print(f"🟢 GREEN PHASE: PostgreSQL connection successful!")
        print(f"Database version: {result}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)