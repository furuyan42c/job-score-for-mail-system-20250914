"""
T085: パフォーマンス・負荷テスト
TDD RED Phase - 失敗するテストを作成
"""

import pytest
import time
import asyncio
import concurrent.futures
from fastapi.testclient import TestClient
from typing import Dict, Any, List
import statistics


class TestPerformance:
    """パフォーマンス・負荷テスト"""

    @pytest.fixture
    def client(self):
        """テストクライアントのセットアップ"""
        from test_simple_server import app
        return TestClient(app)

    def test_api_response_time(self, client):
        """API応答時間のテスト（目標: 200ms以内）"""
        endpoints = [
            "/health",
            "/api/v1/jobs",
            "/api/v1/jobs/1",
        ]

        for endpoint in endpoints:
            times = []
            for _ in range(10):  # 10回測定
                start = time.time()
                response = client.get(endpoint)
                end = time.time()
                times.append((end - start) * 1000)  # ミリ秒に変換

            avg_time = statistics.mean(times)
            max_time = max(times)

            # 平均応答時間が200ms以内であること
            assert avg_time < 200, f"{endpoint} avg response time {avg_time:.2f}ms exceeds 200ms"
            # 最大応答時間が500ms以内であること
            assert max_time < 500, f"{endpoint} max response time {max_time:.2f}ms exceeds 500ms"

    def test_concurrent_requests(self, client):
        """並行リクエストのテスト（目標: 100並行接続）"""
        def make_request():
            response = client.get("/api/v1/jobs")
            return response.status_code

        concurrent_requests = 100
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # すべてのリクエストが成功すること
        success_count = sum(1 for status in results if status == 200)
        success_rate = success_count / concurrent_requests
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} is below 95%"

    def test_data_load_performance(self, client):
        """大量データロードのパフォーマンステスト（目標: 10万件を5分以内）"""
        # 10万件のデータロードシミュレーション
        batch_size = 1000
        total_records = 100000
        batches = total_records // batch_size

        start_time = time.time()

        for i in range(min(batches, 10)):  # テストでは10バッチのみ
            job_data = {
                "title": f"Test Job {i}",
                "company": f"Company {i}",
                "description": f"Description {i}",
                "batch_number": i
            }
            response = client.post("/api/v1/jobs/batch", json=[job_data] * batch_size)
            assert response.status_code in [200, 201, 202]

        elapsed_time = time.time() - start_time
        estimated_total_time = elapsed_time * (batches / 10)

        # 推定時間が5分（300秒）以内であること
        assert estimated_total_time < 300, f"Estimated load time {estimated_total_time:.2f}s exceeds 5 minutes"

    def test_memory_usage(self, client):
        """メモリ使用量のテスト（目標: 8GB以内）"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 負荷をかける
        for _ in range(100):
            client.get("/api/v1/jobs")

        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory

        # メモリ増加が1GB（1024MB）以内であること
        assert memory_increase < 1024, f"Memory increase {memory_increase:.2f}MB exceeds 1GB"

    def test_database_query_performance(self, client):
        """データベースクエリパフォーマンステスト（目標: 各クエリ3秒以内）"""
        # 複雑なクエリのシミュレーション
        complex_queries = [
            "/api/v1/jobs/search?q=Python&location=Tokyo&salary_min=500000",
            "/api/v1/matching/generate?user_id=1&limit=40",
            "/api/v1/scoring/calculate/batch",
        ]

        for query in complex_queries:
            start = time.time()
            response = client.get(query)
            elapsed = time.time() - start

            # 各クエリが3秒以内に完了すること
            assert elapsed < 3, f"Query {query} took {elapsed:.2f}s, exceeds 3s limit"

    def test_throughput(self, client):
        """スループットテスト（目標: 1000 req/s）"""
        duration = 1  # 1秒間
        requests_made = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            client.get("/health")
            requests_made += 1

        throughput = requests_made / duration
        # スループットが100 req/s以上であること（テスト環境では制限）
        assert throughput >= 100, f"Throughput {throughput:.2f} req/s is below 100 req/s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])