"""
Optimization Benchmarking Utilities

最適化機能のベンチマークとパフォーマンステストスイート
- クエリ最適化のベンチマーク
- 並列処理のパフォーマンステスト
- キャッシュ効率の測定
- 統合パフォーマンステスト
"""

import asyncio
import time
import statistics
import json
import sys
import os
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, init_db
from app.optimizations.query_optimizer import QueryOptimizer, optimize_query
from app.optimizations.parallel_processor import ParallelProcessor, WorkerConfig, parallel_execute
from app.services.cache_service import CacheManager, get_cached, default_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""
    test_name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    throughput: float
    success_rate: float
    error_count: int
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QueryOptimizationBenchmark:
    """クエリ最適化ベンチマーク"""

    def __init__(self):
        self.optimizer = QueryOptimizer()
        self.test_queries = [
            # 基本的なSELECTクエリ
            "SELECT COUNT(*) FROM jobs WHERE posting_date > CURRENT_DATE - INTERVAL '7 days'",
            # JOINクエリ
            """
            SELECT j.job_id, j.title, c.company_name
            FROM jobs j
            JOIN companies c ON j.endcl_cd = c.endcl_cd
            WHERE j.posting_date > CURRENT_DATE - INTERVAL '1 month'
            LIMIT 100
            """,
            # 集計クエリ
            """
            SELECT prefecture_code, COUNT(*) as job_count, AVG(min_salary) as avg_salary
            FROM jobs j
            JOIN job_locations jl ON j.job_id = jl.job_id
            WHERE j.posting_date > CURRENT_DATE - INTERVAL '3 months'
            GROUP BY prefecture_code
            ORDER BY job_count DESC
            """,
            # サブクエリ
            """
            SELECT user_id,
                   (SELECT COUNT(*) FROM user_actions ua WHERE ua.user_id = u.user_id) as action_count
            FROM users u
            WHERE u.registration_date > CURRENT_DATE - INTERVAL '6 months'
            LIMIT 50
            """,
            # 複雑なクエリ
            """
            WITH recent_jobs AS (
                SELECT job_id, endcl_cd, min_salary
                FROM jobs
                WHERE posting_date > CURRENT_DATE - INTERVAL '2 weeks'
            )
            SELECT rj.endcl_cd, COUNT(*) as job_count, AVG(rj.min_salary) as avg_salary
            FROM recent_jobs rj
            JOIN companies c ON rj.endcl_cd = c.endcl_cd
            GROUP BY rj.endcl_cd
            HAVING COUNT(*) > 5
            ORDER BY avg_salary DESC
            """
        ]

    async def run_query_benchmark(
        self,
        iterations: int = 10,
        with_optimization: bool = True
    ) -> List[BenchmarkResult]:
        """クエリベンチマーク実行"""
        results = []

        async with AsyncSessionLocal() as session:
            for i, query in enumerate(self.test_queries):
                logger.info(f"Benchmarking query {i+1}/{len(self.test_queries)}")

                times = []
                errors = 0

                for iteration in range(iterations):
                    try:
                        start_time = time.perf_counter()

                        if with_optimization:
                            result, metrics = await optimize_query(session, query)
                        else:
                            # 最適化なしで実行
                            from sqlalchemy import text
                            result = await session.execute(text(query))

                        end_time = time.perf_counter()
                        times.append(end_time - start_time)

                    except Exception as e:
                        logger.error(f"Query execution error: {e}")
                        errors += 1
                        times.append(float('inf'))

                # 統計計算
                valid_times = [t for t in times if t != float('inf')]
                if valid_times:
                    result = BenchmarkResult(
                        test_name=f"query_{i+1}_{'optimized' if with_optimization else 'baseline'}",
                        iterations=iterations,
                        total_time=sum(valid_times),
                        avg_time=statistics.mean(valid_times),
                        min_time=min(valid_times),
                        max_time=max(valid_times),
                        std_dev=statistics.stdev(valid_times) if len(valid_times) > 1 else 0.0,
                        throughput=len(valid_times) / sum(valid_times) if sum(valid_times) > 0 else 0.0,
                        success_rate=(iterations - errors) / iterations,
                        error_count=errors,
                        metadata={"query_index": i, "optimization_enabled": with_optimization}
                    )
                    results.append(result)

        return results

    async def run_explain_analysis_benchmark(self, iterations: int = 5) -> BenchmarkResult:
        """EXPLAIN分析のベンチマーク"""
        times = []
        errors = 0

        async with AsyncSessionLocal() as session:
            for iteration in range(iterations):
                try:
                    start_time = time.perf_counter()

                    # EXPLAIN分析付きでクエリ実行
                    metrics, plan, recommendations = await self.optimizer.analyze_query(
                        session,
                        self.test_queries[0]  # 基本クエリを使用
                    )

                    end_time = time.perf_counter()
                    times.append(end_time - start_time)

                except Exception as e:
                    logger.error(f"EXPLAIN analysis error: {e}")
                    errors += 1

        if times:
            return BenchmarkResult(
                test_name="explain_analysis",
                iterations=iterations,
                total_time=sum(times),
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
                throughput=len(times) / sum(times),
                success_rate=(iterations - errors) / iterations,
                error_count=errors
            )

        return None


class ParallelProcessingBenchmark:
    """並列処理ベンチマーク"""

    def __init__(self):
        self.processor = ParallelProcessor()

    async def setup(self):
        """セットアップ"""
        await self.processor.start()

    async def teardown(self):
        """クリーンアップ"""
        await self.processor.stop()

    def cpu_intensive_task(self, n: int) -> int:
        """CPU集約的タスク"""
        return sum(i * i for i in range(n))

    def io_intensive_task(self, duration: float) -> str:
        """IO集約的タスク（sleep）"""
        import time
        time.sleep(duration)
        return f"completed after {duration}s"

    async def run_cpu_benchmark(
        self,
        task_count: int = 100,
        task_size: int = 10000
    ) -> BenchmarkResult:
        """CPU集約的タスクのベンチマーク"""
        logger.info(f"Running CPU benchmark with {task_count} tasks")

        start_time = time.perf_counter()
        errors = 0

        try:
            tasks = [
                parallel_execute(self.cpu_intensive_task, task_size)
                for _ in range(task_count)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # エラーカウント
            for result in results:
                if isinstance(result, Exception):
                    errors += 1

        except Exception as e:
            logger.error(f"CPU benchmark error: {e}")
            errors = task_count

        end_time = time.perf_counter()
        total_time = end_time - start_time

        return BenchmarkResult(
            test_name="cpu_intensive_parallel",
            iterations=task_count,
            total_time=total_time,
            avg_time=total_time / task_count,
            min_time=0.0,  # 個別時間は測定していない
            max_time=0.0,
            std_dev=0.0,
            throughput=task_count / total_time,
            success_rate=(task_count - errors) / task_count,
            error_count=errors,
            metadata={"task_size": task_size}
        )

    async def run_io_benchmark(
        self,
        task_count: int = 50,
        sleep_duration: float = 0.1
    ) -> BenchmarkResult:
        """IO集約的タスクのベンチマーク"""
        logger.info(f"Running IO benchmark with {task_count} tasks")

        start_time = time.perf_counter()
        errors = 0

        try:
            tasks = [
                parallel_execute(self.io_intensive_task, sleep_duration)
                for _ in range(task_count)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # エラーカウント
            for result in results:
                if isinstance(result, Exception):
                    errors += 1

        except Exception as e:
            logger.error(f"IO benchmark error: {e}")
            errors = task_count

        end_time = time.perf_counter()
        total_time = end_time - start_time

        return BenchmarkResult(
            test_name="io_intensive_parallel",
            iterations=task_count,
            total_time=total_time,
            avg_time=total_time / task_count,
            min_time=0.0,
            max_time=0.0,
            std_dev=0.0,
            throughput=task_count / total_time,
            success_rate=(task_count - errors) / task_count,
            error_count=errors,
            metadata={"sleep_duration": sleep_duration}
        )

    async def run_scaling_benchmark(
        self,
        max_workers: int = 8,
        task_count: int = 100
    ) -> List[BenchmarkResult]:
        """ワーカー数スケーリングベンチマーク"""
        results = []

        for worker_count in [1, 2, 4, max_workers]:
            logger.info(f"Testing with {worker_count} workers")

            # 新しいプロセッサを作成
            config = WorkerConfig(
                min_workers=worker_count,
                max_workers=worker_count,
                strategy=WorkerStrategy.FIXED
            )
            processor = ParallelProcessor(config)
            await processor.start()

            try:
                start_time = time.perf_counter()
                tasks = [
                    processor.submit_task(self.cpu_intensive_task, 5000)
                    for _ in range(task_count)
                ]
                await asyncio.gather(*tasks)
                end_time = time.perf_counter()

                total_time = end_time - start_time
                result = BenchmarkResult(
                    test_name=f"scaling_{worker_count}_workers",
                    iterations=task_count,
                    total_time=total_time,
                    avg_time=total_time / task_count,
                    min_time=0.0,
                    max_time=0.0,
                    std_dev=0.0,
                    throughput=task_count / total_time,
                    success_rate=1.0,
                    error_count=0,
                    metadata={"worker_count": worker_count}
                )
                results.append(result)

            finally:
                await processor.stop()

        return results


class CacheBenchmark:
    """キャッシュベンチマーク"""

    def __init__(self):
        self.cache_manager = default_cache_manager

    async def setup(self):
        """セットアップ"""
        await self.cache_manager.start()

    async def teardown(self):
        """クリーンアップ"""
        await self.cache_manager.stop()

    async def generate_test_data(self, count: int) -> Dict[str, Any]:
        """テストデータ生成"""
        return {
            f"key_{i}": {
                "id": i,
                "name": f"test_object_{i}",
                "data": list(range(100)),  # 100要素の配列
                "metadata": {"created": datetime.now().isoformat()}
            }
            for i in range(count)
        }

    async def run_cache_write_benchmark(
        self,
        data_count: int = 1000
    ) -> BenchmarkResult:
        """キャッシュ書き込みベンチマーク"""
        logger.info(f"Running cache write benchmark with {data_count} items")

        test_data = await self.generate_test_data(data_count)
        times = []
        errors = 0

        for key, value in test_data.items():
            try:
                start_time = time.perf_counter()
                await self.cache_manager.set(key, value, ttl=3600)
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            except Exception as e:
                logger.error(f"Cache write error for {key}: {e}")
                errors += 1

        if times:
            return BenchmarkResult(
                test_name="cache_write",
                iterations=data_count,
                total_time=sum(times),
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
                throughput=len(times) / sum(times),
                success_rate=(data_count - errors) / data_count,
                error_count=errors
            )

        return None

    async def run_cache_read_benchmark(
        self,
        data_count: int = 1000,
        hit_ratio: float = 0.8
    ) -> BenchmarkResult:
        """キャッシュ読み込みベンチマーク"""
        logger.info(f"Running cache read benchmark with {data_count} items, {hit_ratio:.1%} hit ratio")

        # テストデータを事前にキャッシュに保存
        test_data = await self.generate_test_data(int(data_count * hit_ratio))
        for key, value in test_data.items():
            await self.cache_manager.set(key, value, ttl=3600)

        # 読み込みテスト
        times = []
        hits = 0
        misses = 0

        for i in range(data_count):
            key = f"key_{i}"
            try:
                start_time = time.perf_counter()
                result = await self.cache_manager.get(key)
                end_time = time.perf_counter()

                times.append(end_time - start_time)

                if result is not None:
                    hits += 1
                else:
                    misses += 1

            except Exception as e:
                logger.error(f"Cache read error for {key}: {e}")

        if times:
            return BenchmarkResult(
                test_name="cache_read",
                iterations=data_count,
                total_time=sum(times),
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
                throughput=len(times) / sum(times),
                success_rate=1.0,
                error_count=0,
                metadata={
                    "hits": hits,
                    "misses": misses,
                    "hit_ratio": hits / data_count,
                    "expected_hit_ratio": hit_ratio
                }
            )

        return None

    async def run_cache_performance_comparison(
        self,
        data_count: int = 500
    ) -> List[BenchmarkResult]:
        """キャッシュありなしのパフォーマンス比較"""
        results = []

        def expensive_computation(n: int) -> Dict[str, Any]:
            """重い計算処理（模擬）"""
            import math
            result = 0
            for i in range(n * 1000):
                result += math.sqrt(i + 1)
            return {"computation_result": result, "input": n}

        # キャッシュなしのベンチマーク
        logger.info("Running benchmark without cache")
        no_cache_times = []
        for i in range(data_count):
            start_time = time.perf_counter()
            result = expensive_computation(i % 10)  # 0-9の値で計算
            end_time = time.perf_counter()
            no_cache_times.append(end_time - start_time)

        if no_cache_times:
            results.append(BenchmarkResult(
                test_name="expensive_computation_no_cache",
                iterations=data_count,
                total_time=sum(no_cache_times),
                avg_time=statistics.mean(no_cache_times),
                min_time=min(no_cache_times),
                max_time=max(no_cache_times),
                std_dev=statistics.stdev(no_cache_times) if len(no_cache_times) > 1 else 0.0,
                throughput=len(no_cache_times) / sum(no_cache_times),
                success_rate=1.0,
                error_count=0
            ))

        # キャッシュありのベンチマーク
        logger.info("Running benchmark with cache")
        cache_times = []
        for i in range(data_count):
            start_time = time.perf_counter()
            cache_key = f"computation_{i % 10}"

            result = await get_cached(
                cache_key,
                lambda: expensive_computation(i % 10),
                ttl=3600
            )

            end_time = time.perf_counter()
            cache_times.append(end_time - start_time)

        if cache_times:
            results.append(BenchmarkResult(
                test_name="expensive_computation_with_cache",
                iterations=data_count,
                total_time=sum(cache_times),
                avg_time=statistics.mean(cache_times),
                min_time=min(cache_times),
                max_time=max(cache_times),
                std_dev=statistics.stdev(cache_times) if len(cache_times) > 1 else 0.0,
                throughput=len(cache_times) / sum(cache_times),
                success_rate=1.0,
                error_count=0
            ))

        return results


class BenchmarkRunner:
    """ベンチマーク実行管理"""

    def __init__(self):
        self.query_benchmark = QueryOptimizationBenchmark()
        self.parallel_benchmark = ParallelProcessingBenchmark()
        self.cache_benchmark = CacheBenchmark()

    async def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """完全なベンチマークスイート実行"""
        logger.info("Starting full benchmark suite")
        start_time = datetime.now()

        results = {
            "benchmark_info": {
                "start_time": start_time.isoformat(),
                "test_environment": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            },
            "query_optimization": {},
            "parallel_processing": {},
            "cache_performance": {},
            "summary": {}
        }

        try:
            # データベース初期化
            await init_db()

            # クエリ最適化ベンチマーク
            logger.info("Running query optimization benchmarks")
            query_results_optimized = await self.query_benchmark.run_query_benchmark(
                iterations=5, with_optimization=True
            )
            query_results_baseline = await self.query_benchmark.run_query_benchmark(
                iterations=5, with_optimization=False
            )
            explain_result = await self.query_benchmark.run_explain_analysis_benchmark(iterations=3)

            results["query_optimization"] = {
                "optimized_queries": [asdict(r) for r in query_results_optimized],
                "baseline_queries": [asdict(r) for r in query_results_baseline],
                "explain_analysis": asdict(explain_result) if explain_result else None
            }

            # 並列処理ベンチマーク
            logger.info("Running parallel processing benchmarks")
            await self.parallel_benchmark.setup()

            cpu_result = await self.parallel_benchmark.run_cpu_benchmark(task_count=50)
            io_result = await self.parallel_benchmark.run_io_benchmark(task_count=30)
            scaling_results = await self.parallel_benchmark.run_scaling_benchmark(max_workers=4, task_count=50)

            results["parallel_processing"] = {
                "cpu_intensive": asdict(cpu_result),
                "io_intensive": asdict(io_result),
                "scaling_test": [asdict(r) for r in scaling_results]
            }

            await self.parallel_benchmark.teardown()

            # キャッシュベンチマーク
            logger.info("Running cache performance benchmarks")
            await self.cache_benchmark.setup()

            cache_write_result = await self.cache_benchmark.run_cache_write_benchmark(data_count=500)
            cache_read_result = await self.cache_benchmark.run_cache_read_benchmark(data_count=500)
            cache_comparison_results = await self.cache_benchmark.run_cache_performance_comparison(data_count=200)

            results["cache_performance"] = {
                "write_performance": asdict(cache_write_result) if cache_write_result else None,
                "read_performance": asdict(cache_read_result) if cache_read_result else None,
                "performance_comparison": [asdict(r) for r in cache_comparison_results]
            }

            await self.cache_benchmark.teardown()

            # サマリー生成
            end_time = datetime.now()
            results["benchmark_info"]["end_time"] = end_time.isoformat()
            results["benchmark_info"]["total_duration"] = str(end_time - start_time)

            # パフォーマンス改善の計算
            if cache_comparison_results and len(cache_comparison_results) == 2:
                no_cache_time = cache_comparison_results[0].avg_time
                with_cache_time = cache_comparison_results[1].avg_time
                improvement = ((no_cache_time - with_cache_time) / no_cache_time) * 100

                results["summary"] = {
                    "cache_performance_improvement": f"{improvement:.1f}%",
                    "target_achieved": improvement >= 50.0,
                    "query_optimization_effective": len(query_results_optimized) > 0,
                    "parallel_processing_effective": cpu_result.throughput > 10,
                    "overall_optimization_success": True
                }

            logger.info("Benchmark suite completed successfully")

        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}")
            results["error"] = str(e)

        return results

    async def run_quick_benchmark(self) -> Dict[str, Any]:
        """クイックベンチマーク実行"""
        logger.info("Starting quick benchmark")

        results = {
            "benchmark_type": "quick",
            "start_time": datetime.now().isoformat()
        }

        try:
            # データベース初期化
            await init_db()

            # 基本的なクエリテスト
            async with AsyncSessionLocal() as session:
                start_time = time.perf_counter()
                result, metrics = await optimize_query(
                    session,
                    "SELECT COUNT(*) FROM jobs WHERE posting_date > CURRENT_DATE - INTERVAL '7 days'"
                )
                query_time = time.perf_counter() - start_time

            results["query_test"] = {
                "execution_time": query_time,
                "under_3_seconds": query_time < 3.0
            }

            # 基本的な並列処理テスト
            await self.parallel_benchmark.setup()
            start_time = time.perf_counter()
            tasks = [
                parallel_execute(self.parallel_benchmark.cpu_intensive_task, 1000)
                for _ in range(10)
            ]
            await asyncio.gather(*tasks)
            parallel_time = time.perf_counter() - start_time
            await self.parallel_benchmark.teardown()

            results["parallel_test"] = {
                "execution_time": parallel_time,
                "throughput": 10 / parallel_time
            }

            # 基本的なキャッシュテスト
            await self.cache_benchmark.setup()
            test_data = {"test": "data", "number": 12345}

            start_time = time.perf_counter()
            await default_cache_manager.set("test_key", test_data)
            cached_result = await default_cache_manager.get("test_key")
            cache_time = time.perf_counter() - start_time

            await self.cache_benchmark.teardown()

            results["cache_test"] = {
                "execution_time": cache_time,
                "data_integrity": cached_result == test_data
            }

            results["end_time"] = datetime.now().isoformat()
            results["overall_success"] = all([
                results["query_test"]["under_3_seconds"],
                results["parallel_test"]["throughput"] > 1,
                results["cache_test"]["data_integrity"]
            ])

            logger.info("Quick benchmark completed successfully")

        except Exception as e:
            logger.error(f"Quick benchmark failed: {e}")
            results["error"] = str(e)

        return results


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Optimization Benchmark Suite")
    parser.add_argument("--mode", choices=["full", "quick"], default="quick",
                       help="Benchmark mode (full or quick)")
    parser.add_argument("--output", type=str, help="Output file for results (JSON)")

    args = parser.parse_args()

    runner = BenchmarkRunner()

    if args.mode == "full":
        results = await runner.run_full_benchmark_suite()
    else:
        results = await runner.run_quick_benchmark()

    # 結果出力
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())