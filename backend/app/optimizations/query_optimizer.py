"""
T053: Database Query Optimization

データベースクエリの最適化とパフォーマンス監視を提供します。
- EXPLAIN分析による実行計画の可視化
- クエリ最適化推奨事項の生成
- パフォーマンス監視とアラート
- 各クエリを3秒以内に実行することを目標
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """クエリタイプ分類"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    WITH = "WITH"
    UNKNOWN = "UNKNOWN"


class PerformanceLevel(Enum):
    """パフォーマンスレベル"""
    EXCELLENT = "excellent"  # < 0.1s
    GOOD = "good"           # 0.1s - 1s
    ACCEPTABLE = "acceptable"  # 1s - 3s
    SLOW = "slow"          # 3s - 10s
    CRITICAL = "critical"   # > 10s


@dataclass
class QueryMetrics:
    """クエリ実行メトリクス"""
    query_id: str
    query_hash: str
    query_type: QueryType
    execution_time: float
    start_time: datetime
    end_time: datetime
    rows_examined: Optional[int] = None
    rows_returned: Optional[int] = None
    cpu_time: Optional[float] = None
    memory_used: Optional[int] = None
    cache_hit: bool = False
    performance_level: Optional[PerformanceLevel] = None

    def __post_init__(self):
        """パフォーマンスレベルの自動設定"""
        if self.performance_level is None:
            if self.execution_time < 0.1:
                self.performance_level = PerformanceLevel.EXCELLENT
            elif self.execution_time < 1.0:
                self.performance_level = PerformanceLevel.GOOD
            elif self.execution_time < 3.0:
                self.performance_level = PerformanceLevel.ACCEPTABLE
            elif self.execution_time < 10.0:
                self.performance_level = PerformanceLevel.SLOW
            else:
                self.performance_level = PerformanceLevel.CRITICAL


@dataclass
class ExplainPlan:
    """EXPLAIN実行計画"""
    plan_json: Dict[str, Any]
    total_cost: float
    execution_time: float
    planning_time: float
    buffers_hit: Optional[int] = None
    buffers_read: Optional[int] = None
    buffers_dirtied: Optional[int] = None
    buffers_written: Optional[int] = None


@dataclass
class QueryRecommendation:
    """クエリ最適化推奨事項"""
    query_hash: str
    recommendation_type: str
    severity: str  # 'high', 'medium', 'low'
    description: str
    suggested_action: str
    potential_improvement: str
    sql_example: Optional[str] = None
    confidence_score: float = 0.0


class QueryAnalyzer:
    """クエリ分析エンジン"""

    def __init__(self):
        self.query_patterns = self._load_query_patterns()
        self.optimization_rules = self._load_optimization_rules()

    def _load_query_patterns(self) -> Dict[str, re.Pattern]:
        """クエリパターンの読み込み"""
        return {
            'missing_index': re.compile(r'Seq Scan.*cost=(\d+\.\d+)\.\.(\d+\.\d+)', re.IGNORECASE),
            'nested_loop': re.compile(r'Nested Loop.*cost=(\d+\.\d+)\.\.(\d+\.\d+)', re.IGNORECASE),
            'sort_operation': re.compile(r'Sort.*cost=(\d+\.\d+)\.\.(\d+\.\d+)', re.IGNORECASE),
            'hash_join': re.compile(r'Hash Join.*cost=(\d+\.\d+)\.\.(\d+\.\d+)', re.IGNORECASE),
            'aggregate': re.compile(r'(Aggregate|GroupAggregate).*cost=(\d+\.\d+)\.\.(\d+\.\d+)', re.IGNORECASE),
            'subquery': re.compile(r'SubPlan.*cost=(\d+\.\d+)\.\.(\d+\.\d+)', re.IGNORECASE)
        }

    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """最適化ルールの読み込み"""
        return [
            {
                'pattern': 'Seq Scan',
                'condition': lambda cost: cost > 1000,
                'recommendation': 'missing_index',
                'severity': 'high',
                'description': 'Sequential scan detected with high cost',
                'action': 'Consider adding an index on the filtered columns'
            },
            {
                'pattern': 'Nested Loop',
                'condition': lambda cost: cost > 5000,
                'recommendation': 'join_optimization',
                'severity': 'medium',
                'description': 'Expensive nested loop join detected',
                'action': 'Consider using hash join or merge join'
            },
            {
                'pattern': 'Sort',
                'condition': lambda cost: cost > 2000,
                'recommendation': 'sort_optimization',
                'severity': 'medium',
                'description': 'Expensive sort operation detected',
                'action': 'Consider adding an index on sorted columns or using LIMIT'
            },
            {
                'pattern': 'Hash',
                'condition': lambda cost: cost > 10000,
                'recommendation': 'memory_optimization',
                'severity': 'high',
                'description': 'Hash operation with high memory usage',
                'action': 'Consider increasing work_mem or optimizing query structure'
            }
        ]

    def analyze_explain_plan(self, explain_plan: ExplainPlan, query_sql: str) -> List[QueryRecommendation]:
        """EXPLAIN実行計画の分析"""
        recommendations = []
        plan_text = json.dumps(explain_plan.plan_json, indent=2)
        query_hash = hashlib.md5(query_sql.encode()).hexdigest()

        try:
            # コスト分析
            if explain_plan.total_cost > 10000:
                recommendations.append(QueryRecommendation(
                    query_hash=query_hash,
                    recommendation_type="high_cost_query",
                    severity="high",
                    description=f"Query has very high cost: {explain_plan.total_cost:.2f}",
                    suggested_action="Review query structure and consider optimization",
                    potential_improvement="Up to 80% performance improvement possible",
                    confidence_score=0.9
                ))

            # 実行時間分析
            if explain_plan.execution_time > 3.0:
                recommendations.append(QueryRecommendation(
                    query_hash=query_hash,
                    recommendation_type="slow_execution",
                    severity="high" if explain_plan.execution_time > 10.0 else "medium",
                    description=f"Query execution time exceeds target: {explain_plan.execution_time:.2f}s",
                    suggested_action="Optimize query or add appropriate indexes",
                    potential_improvement=f"Target: <3s (current: {explain_plan.execution_time:.2f}s)",
                    confidence_score=0.95
                ))

            # パターンベース分析
            for rule in self.optimization_rules:
                if re.search(rule['pattern'], plan_text, re.IGNORECASE):
                    cost_match = re.search(r'cost=(\d+\.\d+)\.\.(\d+\.\d+)', plan_text)
                    if cost_match:
                        max_cost = float(cost_match.group(2))
                        if rule['condition'](max_cost):
                            recommendations.append(QueryRecommendation(
                                query_hash=query_hash,
                                recommendation_type=rule['recommendation'],
                                severity=rule['severity'],
                                description=rule['description'],
                                suggested_action=rule['action'],
                                potential_improvement=f"Reduce cost from {max_cost:.0f}",
                                confidence_score=0.8
                            ))

            # バッファ分析
            if explain_plan.buffers_read and explain_plan.buffers_hit:
                hit_ratio = explain_plan.buffers_hit / (explain_plan.buffers_hit + explain_plan.buffers_read)
                if hit_ratio < 0.8:
                    recommendations.append(QueryRecommendation(
                        query_hash=query_hash,
                        recommendation_type="low_cache_hit_ratio",
                        severity="medium",
                        description=f"Low buffer cache hit ratio: {hit_ratio:.1%}",
                        suggested_action="Consider query optimization or memory tuning",
                        potential_improvement="Improve cache efficiency",
                        confidence_score=0.7
                    ))

            # SQL構造分析
            sql_recommendations = self._analyze_sql_structure(query_sql, query_hash)
            recommendations.extend(sql_recommendations)

        except Exception as e:
            logger.error(f"Error analyzing explain plan: {e}")

        return recommendations

    def _analyze_sql_structure(self, query_sql: str, query_hash: str) -> List[QueryRecommendation]:
        """SQL構造分析"""
        recommendations = []
        sql_lower = query_sql.lower()

        # N+1クエリパターンの検出
        if 'select' in sql_lower and 'where' in sql_lower and 'in (' in sql_lower:
            in_values = re.findall(r'in\s*\([^)]+\)', sql_lower)
            for in_clause in in_values:
                value_count = in_clause.count(',') + 1
                if value_count > 100:
                    recommendations.append(QueryRecommendation(
                        query_hash=query_hash,
                        recommendation_type="large_in_clause",
                        severity="medium",
                        description=f"Large IN clause with {value_count} values",
                        suggested_action="Consider using JOIN or temporary table",
                        potential_improvement="Reduce query complexity",
                        confidence_score=0.8
                    ))

        # SELECT * パターンの検出
        if re.search(r'select\s+\*', sql_lower):
            recommendations.append(QueryRecommendation(
                query_hash=query_hash,
                recommendation_type="select_star",
                severity="low",
                description="SELECT * statement detected",
                suggested_action="Specify only required columns",
                potential_improvement="Reduce data transfer and memory usage",
                confidence_score=0.6
            ))

        # サブクエリ分析
        subquery_count = sql_lower.count('select') - 1
        if subquery_count > 3:
            recommendations.append(QueryRecommendation(
                query_hash=query_hash,
                recommendation_type="complex_subqueries",
                severity="medium",
                description=f"Query contains {subquery_count} subqueries",
                suggested_action="Consider using CTEs or JOINs",
                potential_improvement="Improve query readability and performance",
                confidence_score=0.7
            ))

        return recommendations

    def classify_query_type(self, query_sql: str) -> QueryType:
        """クエリタイプの分類"""
        sql_normalized = re.sub(r'\s+', ' ', query_sql.strip().upper())

        if sql_normalized.startswith('SELECT'):
            return QueryType.SELECT
        elif sql_normalized.startswith('INSERT'):
            return QueryType.INSERT
        elif sql_normalized.startswith('UPDATE'):
            return QueryType.UPDATE
        elif sql_normalized.startswith('DELETE'):
            return QueryType.DELETE
        elif sql_normalized.startswith('WITH'):
            return QueryType.WITH
        else:
            return QueryType.UNKNOWN


class QueryOptimizer:
    """データベースクエリ最適化管理"""

    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.query_cache: Dict[str, QueryMetrics] = {}
        self.explain_cache: Dict[str, ExplainPlan] = {}
        self.slow_query_threshold = 3.0  # 3秒
        self.monitoring_enabled = True

    async def analyze_query(
        self,
        session: AsyncSession,
        query_sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[QueryMetrics, ExplainPlan, List[QueryRecommendation]]:
        """
        クエリの包括的分析

        Args:
            session: データベースセッション
            query_sql: SQL文
            params: クエリパラメータ

        Returns:
            クエリメトリクス、実行計画、推奨事項のタプル
        """
        query_hash = self._generate_query_hash(query_sql, params)
        query_id = f"query_{int(time.time() * 1000000)}"

        # 実行時間測定
        start_time = datetime.now()
        start_perf = time.perf_counter()

        try:
            # EXPLAIN ANALYZE実行
            explain_plan = await self._execute_explain_analyze(session, query_sql, params)

            # 実際のクエリ実行（必要に応じて）
            if params:
                result = await session.execute(text(query_sql), params)
            else:
                result = await session.execute(text(query_sql))

            end_perf = time.perf_counter()
            end_time = datetime.now()
            execution_time = end_perf - start_perf

            # メトリクス作成
            query_metrics = QueryMetrics(
                query_id=query_id,
                query_hash=query_hash,
                query_type=self.analyzer.classify_query_type(query_sql),
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                rows_returned=result.rowcount if hasattr(result, 'rowcount') else None
            )

            # 推奨事項生成
            recommendations = self.analyzer.analyze_explain_plan(explain_plan, query_sql)

            # キャッシュに保存
            self.query_cache[query_hash] = query_metrics
            self.explain_cache[query_hash] = explain_plan

            # スロークエリ警告
            if execution_time > self.slow_query_threshold:
                await self._log_slow_query(query_metrics, query_sql, recommendations)

            return query_metrics, explain_plan, recommendations

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            raise

    async def _execute_explain_analyze(
        self,
        session: AsyncSession,
        query_sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> ExplainPlan:
        """EXPLAIN ANALYZE実行"""
        explain_sql = f"EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON) {query_sql}"

        start_time = time.perf_counter()

        if params:
            result = await session.execute(text(explain_sql), params)
        else:
            result = await session.execute(text(explain_sql))

        end_time = time.perf_counter()

        explain_data = result.fetchone()[0]
        plan_json = explain_data[0] if isinstance(explain_data, list) else explain_data

        # 実行計画から情報抽出
        total_cost = plan_json.get('Plan', {}).get('Total Cost', 0.0)
        execution_time = plan_json.get('Execution Time', 0.0)
        planning_time = plan_json.get('Planning Time', 0.0)

        # バッファ情報の抽出
        buffers = plan_json.get('Plan', {}).get('Shared Hit Blocks', 0)
        buffers_read = plan_json.get('Plan', {}).get('Shared Read Blocks', 0)

        return ExplainPlan(
            plan_json=plan_json,
            total_cost=total_cost,
            execution_time=execution_time,
            planning_time=planning_time,
            buffers_hit=buffers,
            buffers_read=buffers_read
        )

    async def execute_optimized_query(
        self,
        session: AsyncSession,
        query_sql: str,
        params: Optional[Dict[str, Any]] = None,
        analyze: bool = True
    ) -> Tuple[Any, Optional[QueryMetrics]]:
        """
        最適化されたクエリ実行

        Args:
            session: データベースセッション
            query_sql: SQL文
            params: パラメータ
            analyze: 分析を実行するかどうか

        Returns:
            クエリ結果とメトリクス
        """
        if analyze and self.monitoring_enabled:
            metrics, plan, recommendations = await self.analyze_query(session, query_sql, params)

            # 重要な推奨事項がある場合は警告
            high_severity_recommendations = [r for r in recommendations if r.severity == 'high']
            if high_severity_recommendations:
                logger.warning(
                    f"High severity optimization recommendations for query {metrics.query_hash}: "
                    f"{[r.description for r in high_severity_recommendations]}"
                )

            # 結果を返す（すでに実行済み）
            if params:
                result = await session.execute(text(query_sql), params)
            else:
                result = await session.execute(text(query_sql))

            return result, metrics
        else:
            # 通常実行
            start_time = time.perf_counter()

            if params:
                result = await session.execute(text(query_sql), params)
            else:
                result = await session.execute(text(query_sql))

            execution_time = time.perf_counter() - start_time

            # 簡易メトリクス
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {execution_time:.2f}s")

            return result, None

    async def get_query_performance_report(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """クエリパフォーマンスレポート生成"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        # 最近のクエリメトリクスをフィルタ
        recent_queries = {
            k: v for k, v in self.query_cache.items()
            if v.start_time >= cutoff_time
        }

        if not recent_queries:
            return {"message": "No queries in the specified time window"}

        # 統計計算
        execution_times = [q.execution_time for q in recent_queries.values()]
        performance_levels = [q.performance_level.value for q in recent_queries.values()]

        report = {
            "time_window_hours": time_window_hours,
            "total_queries": len(recent_queries),
            "statistics": {
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "max_execution_time": max(execution_times),
                "min_execution_time": min(execution_times),
                "slow_queries_count": len([t for t in execution_times if t > self.slow_query_threshold]),
                "slow_queries_percentage": len([t for t in execution_times if t > self.slow_query_threshold]) / len(execution_times) * 100
            },
            "performance_distribution": {
                level: performance_levels.count(level)
                for level in set(performance_levels)
            },
            "slowest_queries": [
                {
                    "query_hash": k,
                    "execution_time": v.execution_time,
                    "query_type": v.query_type.value,
                    "performance_level": v.performance_level.value
                }
                for k, v in sorted(
                    recent_queries.items(),
                    key=lambda x: x[1].execution_time,
                    reverse=True
                )[:10]
            ]
        }

        return report

    async def get_optimization_recommendations(
        self,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """上位最適化推奨事項の取得"""
        all_recommendations = []

        for query_hash, explain_plan in self.explain_cache.items():
            if query_hash in self.query_cache:
                query_sql = f"-- Query hash: {query_hash}"  # 実際のSQLは別途保存が必要
                recommendations = self.analyzer.analyze_explain_plan(explain_plan, query_sql)

                for rec in recommendations:
                    rec_dict = asdict(rec)
                    rec_dict['query_metrics'] = asdict(self.query_cache[query_hash])
                    all_recommendations.append(rec_dict)

        # 重要度でソート
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        all_recommendations.sort(
            key=lambda x: (
                severity_order.get(x['severity'], 0),
                x['confidence_score']
            ),
            reverse=True
        )

        return all_recommendations[:top_n]

    async def _log_slow_query(
        self,
        metrics: QueryMetrics,
        query_sql: str,
        recommendations: List[QueryRecommendation]
    ):
        """スロークエリのログ記録"""
        logger.warning(
            f"SLOW QUERY DETECTED - "
            f"ID: {metrics.query_id}, "
            f"Time: {metrics.execution_time:.2f}s, "
            f"Type: {metrics.query_type.value}, "
            f"Recommendations: {len(recommendations)}"
        )

        # 推奨事項をログ出力
        for rec in recommendations[:3]:  # 上位3件
            logger.info(
                f"RECOMMENDATION - "
                f"Type: {rec.recommendation_type}, "
                f"Severity: {rec.severity}, "
                f"Action: {rec.suggested_action}"
            )

    def _generate_query_hash(
        self,
        query_sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """クエリハッシュ生成"""
        # SQLを正規化（パラメータプレースホルダーを統一）
        normalized_sql = re.sub(r'\s+', ' ', query_sql.strip())
        normalized_sql = re.sub(r':[a-zA-Z_][a-zA-Z0-9_]*', ':param', normalized_sql)

        # パラメータキーのソート済み文字列を追加
        param_str = ""
        if params:
            param_keys = sorted(params.keys())
            param_str = ",".join(param_keys)

        hash_input = f"{normalized_sql}|{param_str}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def clear_cache(self):
        """キャッシュクリア"""
        self.query_cache.clear()
        self.explain_cache.clear()
        logger.info("Query optimizer cache cleared")

    def set_monitoring(self, enabled: bool):
        """監視機能の有効/無効切り替え"""
        self.monitoring_enabled = enabled
        logger.info(f"Query monitoring {'enabled' if enabled else 'disabled'}")


# シングルトンインスタンス
query_optimizer = QueryOptimizer()


async def optimize_query(
    session: AsyncSession,
    query_sql: str,
    params: Optional[Dict[str, Any]] = None
) -> Tuple[Any, Optional[QueryMetrics]]:
    """
    便利関数：クエリ最適化実行

    使用例:
        result, metrics = await optimize_query(session, "SELECT * FROM jobs WHERE id = :id", {"id": 123})
    """
    return await query_optimizer.execute_optimized_query(session, query_sql, params)


async def analyze_query_performance(
    session: AsyncSession,
    query_sql: str,
    params: Optional[Dict[str, Any]] = None
) -> Tuple[QueryMetrics, ExplainPlan, List[QueryRecommendation]]:
    """
    便利関数：クエリパフォーマンス分析

    使用例:
        metrics, plan, recommendations = await analyze_query_performance(
            session, "SELECT * FROM jobs WHERE id = :id", {"id": 123}
        )
    """
    return await query_optimizer.analyze_query(session, query_sql, params)