"""
Performance Monitoring Dashboard

パフォーマンス監視ダッシュボード用APIエンドポイント
- クエリ最適化統計
- 並列処理メトリクス
- キャッシュパフォーマンス
- 統合パフォーマンスレポート
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.optimizations.query_optimizer import query_optimizer
from app.optimizations.parallel_processor import default_processor
from app.services.cache_service import default_cache_manager

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/dashboard", response_class=HTMLResponse)
async def get_performance_dashboard():
    """パフォーマンス監視ダッシュボード（HTML）"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Monitoring Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metric-title {
                font-size: 18px;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 15px;
            }
            .metric-value {
                font-size: 24px;
                font-weight: 700;
                color: #1a202c;
                margin-bottom: 5px;
            }
            .metric-label {
                font-size: 14px;
                color: #718096;
            }
            .status-good { color: #38a169; }
            .status-warning { color: #d69e2e; }
            .status-critical { color: #e53e3e; }
            .refresh-btn {
                background: #3182ce;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            }
            .chart-container {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            .table th, .table td {
                padding: 8px 12px;
                text-align: left;
                border-bottom: 1px solid #e2e8f0;
            }
            .table th {
                background: #f7fafc;
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Performance Monitoring Dashboard</h1>
                <p>Real-time performance metrics for query optimization, parallel processing, and caching</p>
                <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
            </div>

            <div class="metrics-grid" id="metrics-grid">
                <!-- メトリクスカードがここに動的に追加される -->
            </div>

            <div class="chart-container">
                <h3>Query Performance Trends</h3>
                <div id="query-chart">Loading...</div>
            </div>

            <div class="chart-container">
                <h3>Recent Optimization Recommendations</h3>
                <div id="recommendations-table">Loading...</div>
            </div>
        </div>

        <script>
            async function fetchMetrics() {
                try {
                    const response = await fetch('/performance/metrics');
                    return await response.json();
                } catch (error) {
                    console.error('Failed to fetch metrics:', error);
                    return null;
                }
            }

            async function fetchRecommendations() {
                try {
                    const response = await fetch('/performance/recommendations');
                    return await response.json();
                } catch (error) {
                    console.error('Failed to fetch recommendations:', error);
                    return [];
                }
            }

            function createMetricCard(title, value, label, status = 'good') {
                return `
                    <div class="metric-card">
                        <div class="metric-title">${title}</div>
                        <div class="metric-value status-${status}">${value}</div>
                        <div class="metric-label">${label}</div>
                    </div>
                `;
            }

            function getStatusClass(value, goodThreshold, warningThreshold) {
                if (value >= goodThreshold) return 'good';
                if (value >= warningThreshold) return 'warning';
                return 'critical';
            }

            async function updateMetrics() {
                const metrics = await fetchMetrics();
                if (!metrics) return;

                const grid = document.getElementById('metrics-grid');

                // 各コンポーネントのメトリクスカードを生成
                let cards = '';

                // クエリ最適化メトリクス
                if (metrics.query_optimizer) {
                    const qm = metrics.query_optimizer;
                    cards += createMetricCard(
                        'Query Performance',
                        `${(qm.statistics.avg_execution_time * 1000).toFixed(0)}ms`,
                        'Average Query Time',
                        getStatusClass(1000 / (qm.statistics.avg_execution_time * 1000), 500, 1000)
                    );
                    cards += createMetricCard(
                        'Slow Queries',
                        `${qm.statistics.slow_queries_percentage.toFixed(1)}%`,
                        'Queries > 3 seconds',
                        getStatusClass(100 - qm.statistics.slow_queries_percentage, 90, 70)
                    );
                }

                // 並列処理メトリクス
                if (metrics.parallel_processor) {
                    const pm = metrics.parallel_processor;
                    cards += createMetricCard(
                        'CPU Utilization',
                        pm.worker_stats.cpu_utilization,
                        'Target: 80%+',
                        pm.worker_stats.cpu_utilization.includes('80') ? 'good' : 'warning'
                    );
                    cards += createMetricCard(
                        'Task Success Rate',
                        pm.task_performance.success_rate,
                        'Successful Tasks',
                        pm.task_performance.success_rate.includes('100') ? 'good' : 'warning'
                    );
                }

                // キャッシュメトリクス
                if (metrics.cache_manager) {
                    const cm = metrics.cache_manager;
                    cards += createMetricCard(
                        'Cache Hit Rate',
                        `${(cm.overall_performance.hit_rate * 100).toFixed(1)}%`,
                        'Target: 50%+ improvement',
                        getStatusClass(cm.overall_performance.hit_rate * 100, 70, 50)
                    );
                    cards += createMetricCard(
                        'Memory Usage',
                        `${cm.memory_cache.memory_usage_mb.toFixed(1)}MB`,
                        'Memory Cache',
                        getStatusClass(100 - cm.memory_cache.memory_usage_mb, 80, 50)
                    );
                }

                grid.innerHTML = cards;
            }

            async function updateRecommendations() {
                const recommendations = await fetchRecommendations();
                const container = document.getElementById('recommendations-table');

                if (!recommendations || recommendations.length === 0) {
                    container.innerHTML = '<p>No optimization recommendations at this time.</p>';
                    return;
                }

                let table = `
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Severity</th>
                                <th>Description</th>
                                <th>Suggested Action</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                recommendations.slice(0, 10).forEach(rec => {
                    table += `
                        <tr>
                            <td>${rec.recommendation_type}</td>
                            <td><span class="status-${rec.severity === 'high' ? 'critical' : rec.severity === 'medium' ? 'warning' : 'good'}">${rec.severity}</span></td>
                            <td>${rec.description}</td>
                            <td>${rec.suggested_action}</td>
                            <td>${(rec.confidence_score * 100).toFixed(0)}%</td>
                        </tr>
                    `;
                });

                table += '</tbody></table>';
                container.innerHTML = table;
            }

            async function refreshData() {
                await Promise.all([updateMetrics(), updateRecommendations()]);
            }

            // 初期データ読み込み
            refreshData();

            // 30秒ごとに自動更新
            setInterval(refreshData, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/metrics", response_model=Dict[str, Any])
async def get_performance_metrics():
    """統合パフォーマンスメトリクス取得"""
    try:
        metrics = {}

        # クエリ最適化メトリクス
        try:
            query_report = await query_optimizer.get_query_performance_report()
            metrics["query_optimizer"] = query_report
        except Exception as e:
            metrics["query_optimizer"] = {"error": str(e)}

        # 並列処理メトリクス
        try:
            parallel_report = default_processor.get_performance_report()
            metrics["parallel_processor"] = parallel_report
        except Exception as e:
            metrics["parallel_processor"] = {"error": str(e)}

        # キャッシュメトリクス
        try:
            cache_report = default_cache_manager.get_performance_report()
            metrics["cache_manager"] = cache_report
        except Exception as e:
            metrics["cache_manager"] = {"error": str(e)}

        # 統合メトリクス
        metrics["system_overview"] = {
            "timestamp": datetime.now().isoformat(),
            "optimization_targets": {
                "query_performance": "< 3 seconds per query",
                "cpu_utilization": "80%+",
                "cache_improvement": "50% faster on cached queries"
            }
        }

        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_optimization_recommendations(
    top_n: int = Query(10, ge=1, le=50)
):
    """最適化推奨事項取得"""
    try:
        recommendations = await query_optimizer.get_optimization_recommendations(top_n)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/query-stats", response_model=Dict[str, Any])
async def get_query_statistics(
    time_window_hours: int = Query(24, ge=1, le=168)
):
    """クエリ統計情報取得"""
    try:
        stats = await query_optimizer.get_query_performance_report(time_window_hours)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query stats: {str(e)}")


@router.get("/parallel-stats", response_model=Dict[str, Any])
async def get_parallel_processing_stats():
    """並列処理統計情報取得"""
    try:
        stats = default_processor.get_stats()
        report = default_processor.get_performance_report()

        return {
            "current_stats": {
                "worker_count": stats.worker_count,
                "active_tasks": stats.active_tasks,
                "queued_tasks": stats.queued_tasks,
                "completed_tasks": stats.completed_tasks,
                "failed_tasks": stats.failed_tasks,
                "cpu_utilization": f"{stats.cpu_utilization:.1%}",
                "memory_utilization": f"{stats.memory_utilization:.1%}",
                "last_updated": stats.last_update.isoformat()
            },
            "performance_report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get parallel stats: {str(e)}")


@router.get("/cache-stats", response_model=Dict[str, Any])
async def get_cache_statistics():
    """キャッシュ統計情報取得"""
    try:
        combined_stats = default_cache_manager.get_combined_stats()
        performance_report = default_cache_manager.get_performance_report()

        return {
            "detailed_stats": combined_stats,
            "performance_report": performance_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/cache/clear")
async def clear_cache():
    """キャッシュクリア"""
    try:
        await default_cache_manager.memory_cache.clear()
        await default_cache_manager.redis_cache.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/query-optimizer/clear-cache")
async def clear_query_optimizer_cache():
    """クエリ最適化キャッシュクリア"""
    try:
        query_optimizer.clear_cache()
        return {"message": "Query optimizer cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear query optimizer cache: {str(e)}")


@router.post("/parallel-processor/clear-metrics")
async def clear_parallel_processor_metrics():
    """並列処理メトリクスクリア"""
    try:
        default_processor.clear_metrics()
        return {"message": "Parallel processor metrics cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear parallel processor metrics: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def get_performance_health():
    """パフォーマンス関連コンポーネントのヘルスチェック"""
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }

    # クエリ最適化ヘルス
    try:
        query_report = await query_optimizer.get_query_performance_report(1)  # 1時間
        if query_report.get("statistics", {}).get("slow_queries_percentage", 0) > 50:
            health_status["components"]["query_optimizer"] = {
                "status": "warning",
                "message": "High percentage of slow queries detected"
            }
        else:
            health_status["components"]["query_optimizer"] = {
                "status": "healthy",
                "message": "Query performance within acceptable range"
            }
    except Exception as e:
        health_status["components"]["query_optimizer"] = {
            "status": "error",
            "message": f"Query optimizer not responding: {str(e)}"
        }
        health_status["overall_status"] = "degraded"

    # 並列処理ヘルス
    try:
        parallel_stats = default_processor.get_stats()
        if parallel_stats.cpu_utilization < 0.5:
            health_status["components"]["parallel_processor"] = {
                "status": "warning",
                "message": "Low CPU utilization - may indicate underutilization"
            }
        elif parallel_stats.failed_tasks > parallel_stats.completed_tasks * 0.1:
            health_status["components"]["parallel_processor"] = {
                "status": "warning",
                "message": "High task failure rate detected"
            }
        else:
            health_status["components"]["parallel_processor"] = {
                "status": "healthy",
                "message": "Parallel processing operating normally"
            }
    except Exception as e:
        health_status["components"]["parallel_processor"] = {
            "status": "error",
            "message": f"Parallel processor not responding: {str(e)}"
        }
        health_status["overall_status"] = "degraded"

    # キャッシュヘルス
    try:
        cache_report = default_cache_manager.get_performance_report()
        hit_rate = cache_report.get("overall_performance", {}).get("hit_rate", 0)
        if hit_rate < 0.3:
            health_status["components"]["cache_manager"] = {
                "status": "warning",
                "message": "Low cache hit rate - consider cache warming strategies"
            }
        else:
            health_status["components"]["cache_manager"] = {
                "status": "healthy",
                "message": "Cache performance within acceptable range"
            }
    except Exception as e:
        health_status["components"]["cache_manager"] = {
            "status": "error",
            "message": f"Cache manager not responding: {str(e)}"
        }
        health_status["overall_status"] = "degraded"

    return health_status


@router.get("/benchmark", response_model=Dict[str, Any])
async def run_performance_benchmark(
    db: AsyncSession = Depends(get_db),
    iterations: int = Query(10, ge=1, le=100)
):
    """パフォーマンスベンチマーク実行"""
    try:
        from app.optimizations.query_optimizer import optimize_query
        from app.optimizations.parallel_processor import parallel_execute
        from app.services.cache_service import get_cached
        import time

        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "iterations": iterations,
            "results": {}
        }

        # クエリ最適化ベンチマーク
        start_time = time.time()
        for i in range(iterations):
            result, metrics = await optimize_query(
                db,
                "SELECT COUNT(*) FROM jobs WHERE posting_date > CURRENT_DATE - INTERVAL '7 days'"
            )
        query_time = time.time() - start_time

        benchmark_results["results"]["query_optimization"] = {
            "total_time": query_time,
            "avg_time_per_query": query_time / iterations,
            "queries_per_second": iterations / query_time
        }

        # 並列処理ベンチマーク
        def cpu_intensive_task(n):
            return sum(i * i for i in range(n))

        start_time = time.time()
        tasks = [parallel_execute(cpu_intensive_task, 1000) for _ in range(iterations)]
        await asyncio.gather(*tasks)
        parallel_time = time.time() - start_time

        benchmark_results["results"]["parallel_processing"] = {
            "total_time": parallel_time,
            "avg_time_per_task": parallel_time / iterations,
            "tasks_per_second": iterations / parallel_time
        }

        # キャッシュベンチマーク
        cache_data = {"test": "data", "number": 12345}

        # キャッシュ書き込みベンチマーク
        start_time = time.time()
        for i in range(iterations):
            await default_cache_manager.set(f"benchmark_key_{i}", cache_data)
        cache_write_time = time.time() - start_time

        # キャッシュ読み込みベンチマーク
        start_time = time.time()
        for i in range(iterations):
            await default_cache_manager.get(f"benchmark_key_{i}")
        cache_read_time = time.time() - start_time

        benchmark_results["results"]["cache_performance"] = {
            "write_time": cache_write_time,
            "read_time": cache_read_time,
            "writes_per_second": iterations / cache_write_time,
            "reads_per_second": iterations / cache_read_time
        }

        return benchmark_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")