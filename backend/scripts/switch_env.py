#!/usr/bin/env python3
"""
環境切り替えスクリプト
開発環境とSupabase環境を簡単に切り替えるためのユーティリティ
"""

import os
import sys
from pathlib import Path
import shutil
import argparse
from typing import Optional

# プロジェクトのルートディレクトリを取得
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"
ENV_BACKUP_DIR = BACKEND_DIR / "env_backups"


def create_backup(env_name: str) -> None:
    """現在の.envファイルをバックアップ"""
    if not ENV_BACKUP_DIR.exists():
        ENV_BACKUP_DIR.mkdir(parents=True)

    if ENV_FILE.exists():
        backup_file = ENV_BACKUP_DIR / f".env.{env_name}.backup"
        shutil.copy2(ENV_FILE, backup_file)
        print(f"✅ Current .env backed up to {backup_file}")


def switch_to_environment(env_name: str) -> None:
    """指定された環境に切り替え"""
    env_file_map = {
        "development": BACKEND_DIR / ".env.development",
        "test": BACKEND_DIR / ".env.test",
        "supabase-local": BACKEND_DIR / ".env.supabase-local",
        "production": BACKEND_DIR / ".env.production",
    }

    if env_name not in env_file_map:
        print(f"❌ Unknown environment: {env_name}")
        print(f"Available environments: {', '.join(env_file_map.keys())}")
        sys.exit(1)

    source_file = env_file_map[env_name]

    if not source_file.exists() and env_name == "supabase-local":
        # Supabaseローカル環境用の.envファイルを生成
        create_supabase_local_env()
        source_file = BACKEND_DIR / ".env.supabase-local"

    if not source_file.exists():
        print(f"❌ Environment file not found: {source_file}")
        print(f"Please create {source_file} first.")
        sys.exit(1)

    # 現在の環境をバックアップ
    create_backup("previous")

    # 環境ファイルをコピー
    shutil.copy2(source_file, ENV_FILE)
    print(f"✅ Switched to {env_name} environment")
    print(f"   Source: {source_file}")
    print(f"   Target: {ENV_FILE}")

    # 環境固有の追加設定
    if env_name == "supabase-local":
        print("\n📝 Supabase Local Instructions:")
        print("   1. Run: supabase start")
        print("   2. Update .env with the actual Supabase local URLs and keys")
        print("   3. Run migrations: alembic upgrade head")
    elif env_name == "production":
        print("\n⚠️  Production environment selected!")
        print("   Make sure to update DATABASE_URL and other sensitive keys")


def create_supabase_local_env() -> None:
    """Supabaseローカル環境用の.envファイルを生成"""
    content = """# Supabase Local Environment Configuration
# Supabaseローカル開発環境用設定

# Basic settings
APP_NAME="バイト求人マッチングシステム"
VERSION="1.0.0"
DEBUG=True
ENVIRONMENT=development
SECRET_KEY=development-secret-key-for-dev-only-minimum-32-characters-long

# Database - Supabase Local
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres

# Supabase Local (supabase start後に自動生成される値で更新)
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

# Database pool
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
DB_POOL_TIMEOUT=10
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=True
DB_ECHO=False

# Rest of settings (same as development)
ALLOWED_HOSTS=["*"]
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
BATCH_SIZE=1000
MAX_WORKERS=4
SCORING_BATCH_SIZE=5000
EMAIL_BATCH_SIZE=100
MATCHING_SCORE_THRESHOLD=60.0
MAX_DAILY_PICKS_PER_USER=40
RECOMMENDATION_SECTIONS=6
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=dev@localhost
SMTP_PASSWORD=devpassword
FROM_EMAIL=noreply@localhost
FROM_NAME="バイト求人マッチング (Supabase Local)"
OPENAI_API_KEY=sk-dev-test-key
ML_MODEL_PATH=./models
SCORING_MODEL_VERSION=v1.0
GOOGLE_MAPS_API_KEY=
SEMRUSH_API_KEY=
SENTRY_DSN=
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
LOG_LEVEL=INFO
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
QUERY_TIMEOUT=30
API_RATE_LIMIT=10000
SLOW_QUERY_THRESHOLD=1.0
MAX_CONCURRENT_REQUESTS=10000
REQUEST_TIMEOUT=30
KEEP_ALIVE_TIMEOUT=5
UVICORN_WORKERS=2
UVICORN_WORKER_CONNECTIONS=1000
UVICORN_BACKLOG=2048
ASYNC_POOL_SIZE=100
ASYNC_MAX_WORKERS=32
"""

    env_file = BACKEND_DIR / ".env.supabase-local"
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Created {env_file}")


def show_current_environment() -> None:
    """現在の環境を表示"""
    if not ENV_FILE.exists():
        print("❌ No .env file found")
        return

    with open(ENV_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    env_vars = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=")[0].strip()
            if key in ["ENVIRONMENT", "DATABASE_URL", "SUPABASE_URL"]:
                value = line.split("=", 1)[1].strip()
                env_vars[key] = value

    print("📋 Current Environment:")
    print(f"   ENVIRONMENT: {env_vars.get('ENVIRONMENT', 'Not set')}")
    print(f"   DATABASE_URL: {env_vars.get('DATABASE_URL', 'Not set')[:50]}...")
    print(f"   SUPABASE_URL: {env_vars.get('SUPABASE_URL', 'Not set')}")


def main():
    parser = argparse.ArgumentParser(
        description="Switch between different environment configurations"
    )
    parser.add_argument(
        "action",
        choices=["switch", "show", "backup"],
        help="Action to perform"
    )
    parser.add_argument(
        "--env",
        choices=["development", "test", "supabase-local", "production"],
        help="Environment to switch to"
    )

    args = parser.parse_args()

    if args.action == "show":
        show_current_environment()
    elif args.action == "backup":
        if args.env:
            create_backup(args.env)
        else:
            create_backup("manual")
        print("✅ Backup created")
    elif args.action == "switch":
        if not args.env:
            print("❌ Please specify environment with --env")
            sys.exit(1)
        switch_to_environment(args.env)


if __name__ == "__main__":
    main()