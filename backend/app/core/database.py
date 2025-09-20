"""
データベース接続管理

Supabase PostgreSQLへの接続とSQLAlchemy設定
- 非同期データベース接続
- 接続プール管理
- セッション管理
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# 非同期エンジン（高並行性対応）
# SQLiteかPostgreSQLかで設定を分ける
if "sqlite" in settings.database_url_async:
    # SQLite用設定（プールなし、connect_args調整）
    engine = create_async_engine(
        settings.database_url_async,
        echo=settings.DB_ECHO,
        future=True,
        connect_args={
            "check_same_thread": False,  # SQLiteのマルチスレッド対応
        },
    )
else:
    # PostgreSQL/Supabase用設定
    engine = create_async_engine(
        settings.database_url_async,
        # poolclass=QueuePool を削除（非同期エンジンではデフォルトで適切なプールが使用される）
        pool_size=settings.DB_POOL_SIZE,  # 100
        max_overflow=settings.DB_MAX_OVERFLOW,  # 200
        pool_timeout=settings.DB_POOL_TIMEOUT,  # 10
        pool_recycle=settings.DB_POOL_RECYCLE,  # 3600
        pool_pre_ping=settings.DB_POOL_PRE_PING,  # True
        echo=settings.DB_ECHO,  # False in production
        future=True,
        # 高並行性のための追加設定
        connect_args={
            "server_settings": {
                "application_name": "job_matching_api",
                "tcp_keepalives_idle": "600",
                "tcp_keepalives_interval": "30",
                "tcp_keepalives_count": "3",
            }
        },
    )

# 非同期セッションファクトリ
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# パフォーマンス監視のためのイベントリスナー
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """クエリ実行前の処理"""
    context._query_start_time = time.time()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """クエリ実行後の処理"""
    total = time.time() - context._query_start_time
    if total > settings.SLOW_QUERY_THRESHOLD:
        logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")


# 接続プール統計
class ConnectionPoolStats:
    """接続プール統計情報"""

    @staticmethod
    def get_pool_stats() -> dict:
        """プール統計取得"""
        if "sqlite" in settings.database_url_async:
            # SQLiteではプール統計は利用不可
            return {
                "pool_size": "N/A",
                "checked_in": "N/A",
                "checked_out": "N/A",
                "overflow": "N/A",
                "invalidated": "N/A",
                "utilization": 0,
            }
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalidated": pool.invalidated(),
            "utilization": (
                (pool.checkedout() / (pool.size() + pool.overflow())) * 100
                if (pool.size() + pool.overflow()) > 0
                else 0
            ),
        }


async def init_db():
    """データベース初期化"""
    try:
        async with engine.begin() as conn:
            # 接続テスト
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            logger.info("Database connection established successfully")

            # テーブル作成（開発環境のみ）- 一時的に無効化（T078テスト用）
            # if settings.DEBUG:
            #     await conn.run_sync(Base.metadata.create_all)
            #     logger.info("Database tables created/updated")
            logger.info("Skipping table creation for startup test")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """データベース接続クローズ"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    データベースセッション依存性注入

    FastAPIの依存性注入で使用
    高並行性対応の強化されたセッション管理
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    トランザクション管理付きデータベースセッション

    複数操作をまとめてコミット/ロールバックする場合に使用
    """
    session = AsyncSessionLocal()
    try:
        async with session.begin():
            yield session
    except Exception as e:
        logger.error(f"Transaction error: {e}")
        raise
    finally:
        await session.close()


async def get_db_read_only() -> AsyncGenerator[AsyncSession, None]:
    """
    読み取り専用データベースセッション

    パフォーマンス最適化のための読み取り専用セッション
    """
    session = AsyncSessionLocal()
    try:
        # PostgreSQLの場合のみ読み取り専用モードに設定
        if "postgresql" in settings.database_url_async:
            await session.execute(text("SET TRANSACTION READ ONLY"))
        yield session
    except Exception as e:
        logger.error(f"Read-only session error: {e}")
        raise
    finally:
        await session.close()


class DatabaseManager:
    """データベース操作の基底クラス"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_query(self, query: str, params: dict = None):
        """生のSQL実行"""
        try:
            result = await self.session.execute(text(query), params or {})
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {query}, Error: {e}")
            raise

    async def commit(self):
        """トランザクションコミット"""
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Commit failed: {e}")
            raise

    async def rollback(self):
        """トランザクションロールバック"""
        await self.session.rollback()


# パフォーマンス監視用
class DatabaseMetrics:
    """データベースパフォーマンス監視"""

    @staticmethod
    async def get_connection_info():
        """接続情報取得"""
        if "sqlite" in settings.database_url_async:
            # SQLiteの場合は簡易的な情報のみ
            return {
                "connections": {"total": 1, "active": 1, "idle": 0},
                "database_size": "N/A (SQLite)",
            }

        async with AsyncSessionLocal() as session:
            try:
                # 接続数
                result = await session.execute(
                    text(
                        """
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """
                    )
                )
                conn_stats = result.fetchone()

                # データベースサイズ
                result = await session.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """
                    )
                )
                size_stats = result.fetchone()

                return {
                    "connections": {
                        "total": conn_stats.total_connections,
                        "active": conn_stats.active_connections,
                        "idle": conn_stats.idle_connections,
                    },
                    "database_size": size_stats.db_size,
                }
            except Exception as e:
                logger.error(f"Failed to get database metrics: {e}")
                return None

    @staticmethod
    async def get_slow_queries(limit: int = 10):
        """スロークエリ取得"""
        if "sqlite" in settings.database_url_async:
            # SQLiteではスロークエリ統計は利用不可
            return []

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    text(
                        """
                    SELECT
                        query,
                        mean_time,
                        calls,
                        total_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT :limit
                """
                    ),
                    {"limit": limit},
                )

                return [dict(row) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Failed to get slow queries: {e}")
                return []


# 接続プール監視
async def monitor_connection_pool():
    """接続プール状態監視"""
    if "sqlite" in settings.database_url_async:
        # SQLiteではプール監視は利用不可
        return {
            "size": "N/A",
            "checked_in": "N/A",
            "checked_out": "N/A",
            "overflow": "N/A",
            "invalidated": "N/A",
        }
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalidated": pool.invalidated(),
    }


# ヘルスチェック用
async def check_database_health():
    """データベースヘルスチェック"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            metrics = await DatabaseMetrics.get_connection_info()
            pool_info = await monitor_connection_pool()

            return {"status": "healthy", "metrics": metrics, "pool": pool_info}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
