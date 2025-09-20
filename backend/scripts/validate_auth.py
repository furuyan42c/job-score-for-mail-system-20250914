#!/usr/bin/env python3
"""
Simple validation script for auth endpoints after refactoring
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

async def test_auth_flow():
    """Test basic auth flow"""
    async with httpx.AsyncClient() as client:
        # Test registration
        print("1. Testing registration...")
        register_data = {
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "TestPass123!",
            "name": "Test User"
        }

        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code == 201:
                print("✅ Registration successful")
                result = response.json()
                access_token = result.get("access_token")
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return

        # Test login
        print("2. Testing login...")
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }

        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                print("✅ Login successful")
                result = response.json()
                access_token = result.get("access_token")
            else:
                print(f"❌ Login failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return

        # Test protected endpoint
        print("3. Testing protected endpoint...")
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            if response.status_code == 200:
                print("✅ Protected endpoint access successful")
                user_data = response.json()
                print(f"   User: {user_data.get('email')}")
            else:
                print(f"❌ Protected endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")

        # Test logout
        print("4. Testing logout...")
        try:
            response = await client.post(f"{BASE_URL}/auth/logout", headers=headers)
            if response.status_code == 200:
                print("✅ Logout successful")
            else:
                print(f"❌ Logout failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Logout error: {e}")

        # Test that token is now invalid
        print("5. Testing token invalidation...")
        try:
            response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            if response.status_code == 401:
                print("✅ Token correctly invalidated")
            else:
                print(f"❌ Token still valid: {response.status_code}")
        except Exception as e:
            print(f"❌ Token validation error: {e}")

        print("\n✅ Auth validation complete!")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())