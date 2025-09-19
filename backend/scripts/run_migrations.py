#!/usr/bin/env python3
"""
データベースマイグレーション実行スクリプト
SQLiteとPostgreSQL両対応
"""

import os
import sys
import sqlite3
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import engine, get_db


class MigrationRunner:
    """マイグレーション実行クラス"""

    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.migrations_dir = self.backend_dir / "migrations"
        self.db_url = settings.DATABASE_URL
        self.is_sqlite = "sqlite" in self.db_url

    def get_migration_files(self) -> List[Path]:
        """マイグレーションファイル一覧を取得"""
        sql_files = sorted(self.migrations_dir.glob("*.sql"))
        return sql_files

    def run_sqlite_migrations(self) -> None:
        """SQLite用マイグレーション実行"""
        print("🗄️ SQLite migrations starting...")

        # SQLiteデータベースパスを取得
        db_path = self.db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = self.backend_dir / db_path[2:]

        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # マイグレーション履歴テーブル作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 既に適用済みのマイグレーションを取得
        cursor.execute("SELECT filename FROM migration_history")
        applied = {row[0] for row in cursor.fetchall()}

        # マイグレーションファイルを順次実行
        migration_files = self.get_migration_files()

        for migration_file in migration_files:
            filename = migration_file.name

            # スキップ条件
            if filename in applied:
                print(f"⏭️  Skipping {filename} (already applied)")
                continue

            if "supabase" in filename.lower() or "rls" in filename.lower():
                print(f"⏭️  Skipping {filename} (Supabase-specific)")
                continue

            print(f"📝 Applying {filename}...")

            # SQLを読み込み、SQLite用に変換
            with open(migration_file, "r", encoding="utf-8") as f:
                sql = f.read()

            # SQLite用に変換
            sql = self.convert_to_sqlite(sql)

            # 実行
            try:
                # 複数のステートメントを実行
                cursor.executescript(sql)

                # 履歴に記録
                cursor.execute(
                    "INSERT INTO migration_history (filename) VALUES (?)",
                    (filename,)
                )
                conn.commit()
                print(f"✅ {filename} applied successfully")

            except Exception as e:
                print(f"❌ Error applying {filename}: {e}")
                conn.rollback()
                raise

        conn.close()
        print("✅ SQLite migrations completed")

    def convert_to_sqlite(self, sql: str) -> str:
        """PostgreSQL SQLをSQLite用に変換"""
        # コメントを除去
        lines = sql.split('\n')
        cleaned_lines = []

        for line in lines:
            # COMMENTステートメントをスキップ
            if line.strip().upper().startswith('COMMENT ON'):
                continue

            # CREATE INDEXステートメントはスキップ（後で別途処理）
            if 'CREATE INDEX' in line.upper():
                continue

            # 型変換
            line = line.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
            line = line.replace('BIGSERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
            line = line.replace('SERIAL', 'INTEGER')
            line = line.replace('BIGSERIAL', 'INTEGER')
            line = line.replace('VARCHAR', 'TEXT')
            line = line.replace('CHAR(2)', 'TEXT')
            line = line.replace('CHAR(5)', 'TEXT')
            line = line.replace('TIMESTAMPTZ', 'TIMESTAMP')
            line = line.replace('TIMESTAMP WITH TIME ZONE', 'TIMESTAMP')
            line = line.replace('JSONB', 'TEXT')
            line = line.replace('JSON', 'TEXT')
            line = line.replace('UUID', 'TEXT')
            line = line.replace('DECIMAL', 'REAL')
            line = line.replace('NUMERIC', 'REAL')
            line = line.replace('BYTEA', 'BLOB')
            line = line.replace('[]', '')  # 配列型を削除

            # 外部キー参照を簡略化（SQLiteでは制約名はオプション）
            if 'REFERENCES' in line:
                line = line.replace('NOT NULL REFERENCES', 'REFERENCES')

            # デフォルト値の変換
            line = line.replace('DEFAULT CURRENT_TIMESTAMP', "DEFAULT (datetime('now'))")
            line = line.replace('DEFAULT NOW()', "DEFAULT (datetime('now'))")
            line = line.replace('DEFAULT gen_random_uuid()', "")

            # IF NOT EXISTS をサポート
            # SQLiteは3.3.0以降でサポート

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    async def run_postgresql_migrations(self) -> None:
        """PostgreSQL/Supabase用マイグレーション実行"""
        print("🐘 PostgreSQL/Supabase migrations starting...")

        async with engine.begin() as conn:
            # マイグレーション履歴テーブル作成
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    filename TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 既に適用済みのマイグレーションを取得
            result = await conn.execute("SELECT filename FROM migration_history")
            applied = {row[0] for row in result}

            # マイグレーションファイルを順次実行
            migration_files = self.get_migration_files()

            for migration_file in migration_files:
                filename = migration_file.name

                if filename in applied:
                    print(f"⏭️  Skipping {filename} (already applied)")
                    continue

                print(f"📝 Applying {filename}...")

                # SQLを読み込み
                with open(migration_file, "r", encoding="utf-8") as f:
                    sql = f.read()

                try:
                    # 実行
                    await conn.execute(sql)

                    # 履歴に記録
                    await conn.execute(
                        "INSERT INTO migration_history (filename) VALUES (:filename)",
                        {"filename": filename}
                    )

                    print(f"✅ {filename} applied successfully")

                except Exception as e:
                    print(f"❌ Error applying {filename}: {e}")
                    raise

        print("✅ PostgreSQL migrations completed")

    def run(self) -> None:
        """マイグレーション実行"""
        print(f"🚀 Starting database migrations")
        print(f"📍 Database: {self.db_url[:50]}...")
        print(f"📂 Migrations directory: {self.migrations_dir}")

        if self.is_sqlite:
            self.run_sqlite_migrations()
        else:
            asyncio.run(self.run_postgresql_migrations())

        print("✨ All migrations completed successfully!")

    def create_test_tables(self) -> None:
        """テスト用の簡易テーブル作成（開発用）"""
        if not self.is_sqlite:
            print("⚠️  Test tables are only for SQLite development")
            return

        print("🧪 Creating test tables for development...")

        db_path = self.db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = self.backend_dir / db_path[2:]

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 最小限のテストテーブル作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                salary INTEGER,
                created_at TIMESTAMP DEFAULT (datetime('now'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now'))
            )
        """)

        # サンプルデータ挿入（テーブル存在時のみ）
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (title, company, salary)
                VALUES
                    ('Backend Developer', 'Tech Corp', 500000),
                    ('Frontend Developer', 'Web Inc', 450000),
                    ('Full Stack Developer', 'Startup Co', 480000)
            """)
        except sqlite3.OperationalError as e:
            print(f"⚠️  Could not insert sample data: {e}")

        cursor.execute("""
            INSERT OR IGNORE INTO users (email, name)
            VALUES
                ('test@example.com', 'Test User'),
                ('admin@example.com', 'Admin User')
        """)

        conn.commit()
        conn.close()

        print("✅ Test tables created successfully")


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--test-tables",
        action="store_true",
        help="Create test tables for development"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run all migrations (dangerous!)"
    )

    args = parser.parse_args()

    runner = MigrationRunner()

    if args.test_tables:
        runner.create_test_tables()
    else:
        runner.run()


if __name__ == "__main__":
    main()