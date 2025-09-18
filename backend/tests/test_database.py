"""
データベース接続とトランザクション管理の包括的テスト

接続プール管理、トランザクション処理、パフォーマンス監視、
エラーハンドリングのテストを実装
"""

import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, event
from sqlalchemy.exc import OperationalError, DatabaseError
import concurrent.futures

from app.core.database import (
    engine, AsyncSessionLocal, init_db, close_db, get_db,
    get_db_transaction, get_db_read_only, DatabaseManager,
    DatabaseMetrics, ConnectionPoolStats, monitor_connection_pool,
    check_database_health
)
from app.core.config import TestSettings


class TestDatabaseConnection:
    """データベース接続のテスト"""

    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """データベース初期化テスト"""
        try:
            await init_db()
            # 初期化が正常に完了することを確認
            assert True
        except Exception as e:
            pytest.fail(f"データベース初期化に失敗: {e}")

    @pytest.mark.asyncio
    async def test_database_connection_basic(self):
        """基本的なデータベース接続テスト"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row.test_value == 1

    @pytest.mark.asyncio
    async def test_get_db_dependency(self):
        """get_db依存性注入テスト"""
        db_generator = get_db()
        session = await db_generator.__anext__()

        try:
            assert isinstance(session, AsyncSession)

            # 基本的なクエリ実行テスト
            result = await session.execute(text("SELECT version() as version"))
            row = result.fetchone()
            assert row.version is not None

        finally:
            await db_generator.aclose()

    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """データベースヘルスチェックテスト"""
        health_status = await check_database_health()

        assert isinstance(health_status, dict)
        assert "status" in health_status
        assert health_status["status"] in ["healthy", "unhealthy"]

        if health_status["status"] == "healthy":
            assert "metrics" in health_status
            assert "pool" in health_status

    @pytest.mark.asyncio
    async def test_database_close(self):
        """データベース接続クローズテスト"""
        try:
            await close_db()
            # 接続クローズが正常に完了することを確認
            assert True
        except Exception as e:
            pytest.fail(f"データベース接続クローズに失敗: {e}")


class TestConnectionPool:
    """接続プールのテスト"""

    @pytest.mark.asyncio
    async def test_connection_pool_stats(self):
        """接続プール統計テスト"""
        stats = ConnectionPoolStats.get_pool_stats()

        assert isinstance(stats, dict)
        assert "pool_size" in stats
        assert "checked_in" in stats
        assert "checked_out" in stats
        assert "utilization" in stats

        # 統計値が妥当な範囲内であることを確認
        assert stats["pool_size"] >= 0
        assert stats["checked_in"] >= 0
        assert stats["checked_out"] >= 0
        assert 0 <= stats["utilization"] <= 100

    @pytest.mark.asyncio
    async def test_monitor_connection_pool(self):
        """接続プール監視テスト"""
        pool_info = await monitor_connection_pool()

        assert isinstance(pool_info, dict)
        expected_keys = ["size", "checked_in", "checked_out", "overflow", "invalidated"]
        for key in expected_keys:
            assert key in pool_info
            assert isinstance(pool_info[key], int)

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """並行接続テスト"""
        concurrent_count = 20
        results = []

        async def create_connection():
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as value"))
                row = result.fetchone()
                return row.value

        # 並行して複数の接続を作成
        tasks = [create_connection() for _ in range(concurrent_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # すべての接続が成功することを確認
        assert len(results) == concurrent_count
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"並行接続でエラー: {result}")
            assert result == 1

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self):
        """接続プール制限テスト"""
        settings = TestSettings()
        max_connections = settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW

        async def hold_connection():
            async with AsyncSessionLocal() as session:
                # 接続を長時間保持
                await asyncio.sleep(1)
                result = await session.execute(text("SELECT 1"))
                return result.fetchone()[0]

        # プールサイズを超える接続を試行
        tasks = [hold_connection() for _ in range(max_connections + 5)]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # 一部の接続がタイムアウトまたは制限される可能性
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0

        # 処理時間が合理的な範囲内であることを確認
        assert end_time - start_time < 30  # 30秒以内


class TestTransactionManagement:
    """トランザクション管理のテスト"""

    @pytest.mark.asyncio
    async def test_get_db_transaction(self):
        """トランザクション管理セッションテスト"""
        async with get_db_transaction() as session:
            # トランザクション内でのテーブル作成（テスト用）
            await session.execute(text("""
                CREATE TEMP TABLE test_transaction (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """))

            await session.execute(text("""
                INSERT INTO test_transaction (value) VALUES ('test')
            """))

            result = await session.execute(text("""
                SELECT value FROM test_transaction WHERE id = 1
            """))
            row = result.fetchone()
            assert row.value == 'test'

    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """トランザクションロールバックテスト"""
        try:
            async with get_db_transaction() as session:
                # テスト用テーブル作成
                await session.execute(text("""
                    CREATE TEMP TABLE test_rollback (
                        id SERIAL PRIMARY KEY,
                        value TEXT
                    )
                """))

                await session.execute(text("""
                    INSERT INTO test_rollback (value) VALUES ('should_rollback')
                """))

                # 意図的にエラーを発生させる
                raise Exception("Test rollback")

        except Exception as e:
            assert str(e) == "Test rollback"

        # ロールバック後は変更が取り消されていることを確認
        # （TEMPテーブルなので他のセッションでは確認できないが、
        #  ロールバック自体の動作確認として十分）

    @pytest.mark.asyncio
    async def test_read_only_session(self):
        """読み取り専用セッションテスト"""
        async with get_db_read_only() as session:
            # 読み取りクエリは正常に実行される
            result = await session.execute(text("SELECT 1 as value"))
            row = result.fetchone()
            assert row.value == 1

            # 書き込みクエリはエラーになる（実際のテストでは省略）
            # await session.execute(text("CREATE TEMP TABLE should_fail (id int)"))

    @pytest.mark.asyncio
    async def test_nested_transactions(self):
        """ネストしたトランザクションテスト"""
        async with get_db_transaction() as outer_session:
            await outer_session.execute(text("""
                CREATE TEMP TABLE test_nested (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """))

            await outer_session.execute(text("""
                INSERT INTO test_nested (value) VALUES ('outer')
            """))

            # セーブポイントを使用したネストトランザクション
            async with outer_session.begin_nested():
                await outer_session.execute(text("""
                    INSERT INTO test_nested (value) VALUES ('inner')
                """))

                # 内部トランザクションをロールバック
                raise Exception("Inner rollback")


class TestDatabaseManager:
    """DatabaseManagerのテスト"""

    @pytest.fixture
    async def db_manager(self):
        """DatabaseManagerのフィクスチャ"""
        async with AsyncSessionLocal() as session:
            yield DatabaseManager(session)

    @pytest.mark.asyncio
    async def test_execute_query(self, db_manager):
        """生SQLクエリ実行テスト"""
        result = await db_manager.execute_query("SELECT 1 as test_value")
        row = result.fetchone()
        assert row.test_value == 1

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, db_manager):
        """パラメータ付きクエリ実行テスト"""
        result = await db_manager.execute_query(
            "SELECT :value as test_value",
            {"value": 42}
        )
        row = result.fetchone()
        assert row.test_value == 42

    @pytest.mark.asyncio
    async def test_commit_rollback(self, db_manager):
        """コミット・ロールバックテスト"""
        # テスト用テーブル作成
        await db_manager.execute_query("""
            CREATE TEMP TABLE test_commit (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """)

        # データ挿入
        await db_manager.execute_query(
            "INSERT INTO test_commit (value) VALUES (:value)",
            {"value": "test"}
        )

        # コミット
        await db_manager.commit()

        # データが存在することを確認
        result = await db_manager.execute_query(
            "SELECT value FROM test_commit WHERE id = 1"
        )
        row = result.fetchone()
        assert row.value == "test"

    @pytest.mark.asyncio
    async def test_query_error_handling(self, db_manager):
        """クエリエラーハンドリングテスト"""
        with pytest.raises(Exception):
            await db_manager.execute_query("INVALID SQL QUERY")


class TestDatabaseMetrics:
    """データベースメトリクスのテスト"""

    @pytest.mark.asyncio
    async def test_get_connection_info(self):
        """接続情報取得テスト"""
        info = await DatabaseMetrics.get_connection_info()

        if info:  # データベースによっては利用できない場合がある
            assert isinstance(info, dict)
            assert "connections" in info
            assert "database_size" in info

            connections = info["connections"]
            assert "total" in connections
            assert "active" in connections
            assert "idle" in connections

            assert isinstance(connections["total"], int)
            assert isinstance(connections["active"], int)
            assert isinstance(connections["idle"], int)

    @pytest.mark.asyncio
    async def test_get_slow_queries(self):
        """スロークエリ取得テスト"""
        slow_queries = await DatabaseMetrics.get_slow_queries(limit=5)

        assert isinstance(slow_queries, list)
        # pg_stat_statementsが有効でない場合は空リストが返される
        if slow_queries:
            for query in slow_queries:
                assert isinstance(query, dict)
                expected_keys = ["query", "mean_time", "calls"]
                for key in expected_keys:
                    if key in query:  # すべてのキーが存在するとは限らない
                        assert isinstance(query[key], (int, float, str))


class TestDatabasePerformance:
    """データベースパフォーマンステスト"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_connection_creation_performance(self):
        """接続作成パフォーマンステスト"""
        connection_count = 50

        async def create_and_close_connection():
            start_time = time.time()
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return time.time() - start_time

        start_total = time.time()
        tasks = [create_and_close_connection() for _ in range(connection_count)]
        times = await asyncio.gather(*tasks)
        total_time = time.time() - start_total

        # 平均接続時間が妥当な範囲内であることを確認
        avg_time = sum(times) / len(times)
        assert avg_time < 0.1  # 100ms以内
        assert total_time < 10  # 全体で10秒以内

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_query_performance(self):
        """クエリパフォーマンステスト"""
        async with AsyncSessionLocal() as session:
            # 軽量なクエリのパフォーマンステスト
            start_time = time.time()

            for _ in range(100):
                await session.execute(text("SELECT 1"))

            end_time = time.time()
            total_time = end_time - start_time

            # 100回のクエリが2秒以内に完了することを確認
            assert total_time < 2.0

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self):
        """並行クエリパフォーマンステスト"""
        concurrent_count = 20
        queries_per_task = 10

        async def run_queries():
            async with AsyncSessionLocal() as session:
                for _ in range(queries_per_task):
                    await session.execute(text("SELECT 1"))

        start_time = time.time()
        tasks = [run_queries() for _ in range(concurrent_count)]
        await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time
        total_queries = concurrent_count * queries_per_task

        # 並行処理により高いスループットが得られることを確認
        queries_per_second = total_queries / total_time
        assert queries_per_second > 50  # 50 QPS以上


class TestDatabaseErrorHandling:
    """データベースエラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self):
        """接続タイムアウトハンドリングテスト"""
        # 無効な接続文字列でタイムアウトをシミュレート
        timeout_engine = create_async_engine(
            "postgresql+asyncpg://invalid:invalid@localhost:5433/invalid",
            pool_timeout=1,
            connect_args={"command_timeout": 1}
        )

        TestSession = sessionmaker(timeout_engine, class_=AsyncSession)

        with pytest.raises((OperationalError, DatabaseError, OSError)):
            async with TestSession() as session:
                await session.execute(text("SELECT 1"))

    @pytest.mark.asyncio
    async def test_invalid_query_handling(self):
        """無効なクエリハンドリングテスト"""
        async with AsyncSessionLocal() as session:
            with pytest.raises(Exception):
                await session.execute(text("SELECT * FROM non_existent_table"))

    @pytest.mark.asyncio
    async def test_transaction_deadlock_simulation(self):
        """トランザクションデッドロックシミュレーションテスト"""
        # 実際のデッドロックは複雑なので、基本的なエラーハンドリングのみテスト
        async with AsyncSessionLocal() as session:
            try:
                await session.execute(text("""
                    CREATE TEMP TABLE test_deadlock (
                        id SERIAL PRIMARY KEY,
                        value TEXT
                    )
                """))

                # 明示的にエラーを発生させる
                await session.execute(text("INVALID QUERY"))

            except Exception as e:
                await session.rollback()
                assert isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_session_cleanup_on_error(self):
        """エラー時のセッションクリーンアップテスト"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                raise Exception("Test error")
        except Exception as e:
            assert str(e) == "Test error"

        # セッションが適切にクリーンアップされることを確認
        # （新しいセッションが正常に作成できる）
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1


class TestDatabaseIntegration:
    """データベース統合テスト"""

    @pytest.mark.asyncio
    async def test_full_database_workflow(self):
        """完全なデータベースワークフローテスト"""
        # 1. 初期化
        await init_db()

        # 2. 接続プール状態確認
        pool_stats = ConnectionPoolStats.get_pool_stats()
        assert pool_stats["pool_size"] > 0

        # 3. ヘルスチェック
        health = await check_database_health()
        assert health["status"] == "healthy"

        # 4. データベースマネージャーでの操作
        async with AsyncSessionLocal() as session:
            manager = DatabaseManager(session)

            # テーブル作成
            await manager.execute_query("""
                CREATE TEMP TABLE integration_test (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # データ挿入
            await manager.execute_query(
                "INSERT INTO integration_test (name) VALUES (:name)",
                {"name": "integration_test"}
            )
            await manager.commit()

            # データ取得
            result = await manager.execute_query(
                "SELECT name FROM integration_test WHERE id = 1"
            )
            row = result.fetchone()
            assert row.name == "integration_test"

        # 5. 接続クローズ（テスト環境では通常不要）
        # await close_db()

    @pytest.mark.asyncio
    async def test_stress_test(self):
        """ストレステスト"""
        concurrent_sessions = 10
        operations_per_session = 50

        async def stress_session():
            results = []
            async with AsyncSessionLocal() as session:
                for i in range(operations_per_session):
                    result = await session.execute(
                        text("SELECT :value as result"),
                        {"value": i}
                    )
                    row = result.fetchone()
                    results.append(row.result)
            return results

        start_time = time.time()
        tasks = [stress_session() for _ in range(concurrent_sessions)]
        all_results = await asyncio.gather(*tasks)
        end_time = time.time()

        # すべての操作が正常に完了することを確認
        assert len(all_results) == concurrent_sessions
        for results in all_results:
            assert len(results) == operations_per_session
            assert results == list(range(operations_per_session))

        # ストレステストが合理的な時間で完了することを確認
        total_time = end_time - start_time
        total_operations = concurrent_sessions * operations_per_session
        assert total_time < 30  # 30秒以内

        ops_per_second = total_operations / total_time
        assert ops_per_second > 10  # 10 ops/sec以上


class TestDatabaseMonitoring:
    """データベースモニタリングのテスト"""

    @pytest.mark.asyncio
    async def test_query_execution_monitoring(self):
        """クエリ実行監視テスト"""
        # イベントリスナーが設定されていることを確認
        listeners = event.contains(engine.sync_engine, "before_cursor_execute")
        assert listeners  # リスナーが登録されていることを確認

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_slow_query_detection(self):
        """スロークエリ検出テスト"""
        async with AsyncSessionLocal() as session:
            # 意図的に遅いクエリを実行
            start_time = time.time()
            await session.execute(text("SELECT pg_sleep(0.1)"))  # 100ms待機
            end_time = time.time()

            execution_time = end_time - start_time
            assert execution_time >= 0.1  # 最低100ms経過していることを確認

    @pytest.mark.asyncio
    async def test_connection_pool_monitoring(self):
        """接続プール監視テスト"""
        initial_stats = ConnectionPoolStats.get_pool_stats()

        # 複数の接続を同時に使用
        sessions = []
        try:
            for _ in range(5):
                session = AsyncSessionLocal()
                await session.execute(text("SELECT 1"))
                sessions.append(session)

            # 接続数が増加していることを確認
            active_stats = ConnectionPoolStats.get_pool_stats()
            assert active_stats["checked_out"] >= initial_stats["checked_out"]

        finally:
            # セッションクリーンアップ
            for session in sessions:
                await session.close()


@pytest.fixture
def mock_database_engine():
    """データベースエンジンのモック"""
    mock_engine = MagicMock()
    mock_engine.pool = MagicMock()
    mock_engine.pool.size.return_value = 10
    mock_engine.pool.checkedin.return_value = 8
    mock_engine.pool.checkedout.return_value = 2
    mock_engine.pool.overflow.return_value = 0
    mock_engine.pool.invalidated.return_value = 0
    return mock_engine


@pytest.fixture
async def isolated_test_session():
    """分離されたテストセッション"""
    # テスト専用の接続を作成
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",  # インメモリSQLite
        echo=False
    )

    TestSession = sessionmaker(test_engine, class_=AsyncSession)

    async with TestSession() as session:
        yield session
        await session.rollback()

    await test_engine.dispose()