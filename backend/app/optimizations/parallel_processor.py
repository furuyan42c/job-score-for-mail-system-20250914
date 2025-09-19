"""
T054: Parallel Processing Optimization

並列処理の最適化とワーカー管理を提供します。
- ProcessPoolExecutorの動的設定
- CPU使用率に基づくワーカー数の動的スケーリング
- タスクバッチング処理と負荷分散
- 目標CPU使用率: 80%+
"""

import asyncio
import concurrent.futures
import multiprocessing as mp
import time
import psutil
import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import queue
import math
import sys

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class WorkerStrategy(Enum):
    """ワーカー戦略"""
    FIXED = "fixed"              # 固定ワーカー数
    DYNAMIC = "dynamic"          # 動的スケーリング
    CPU_ADAPTIVE = "cpu_adaptive"  # CPU使用率に基づく調整
    LOAD_ADAPTIVE = "load_adaptive"  # 負荷に基づく調整


class TaskPriority(Enum):
    """タスク優先度"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkerConfig:
    """ワーカー設定"""
    strategy: WorkerStrategy = WorkerStrategy.CPU_ADAPTIVE
    min_workers: int = 2
    max_workers: int = mp.cpu_count()
    target_cpu_utilization: float = 0.8  # 80%
    scale_up_threshold: float = 0.85      # 85%でスケールアップ
    scale_down_threshold: float = 0.60    # 60%でスケールダウン
    monitoring_interval: float = 5.0      # 5秒間隔で監視
    task_timeout: float = 300.0           # 5分でタイムアウト
    batch_size: int = 100
    queue_size_limit: int = 1000

    def __post_init__(self):
        """設定値の検証と調整"""
        self.min_workers = max(1, min(self.min_workers, mp.cpu_count()))
        self.max_workers = max(self.min_workers, min(self.max_workers, mp.cpu_count() * 2))
        self.target_cpu_utilization = max(0.1, min(0.95, self.target_cpu_utilization))


@dataclass
class TaskMetrics:
    """タスクメトリクス"""
    task_id: str
    priority: TaskPriority
    submit_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    queue_time: Optional[float] = None
    worker_id: Optional[int] = None
    cpu_time: Optional[float] = None
    memory_used: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class WorkerStats:
    """ワーカー統計"""
    worker_count: int
    active_tasks: int
    queued_tasks: int
    completed_tasks: int
    failed_tasks: int
    cpu_utilization: float
    memory_utilization: float
    avg_task_time: float
    queue_wait_time: float
    last_update: datetime = field(default_factory=datetime.now)


class TaskBatcher(Generic[T, R]):
    """タスクバッチング処理"""

    def __init__(self, batch_size: int = 100, max_wait_time: float = 1.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_tasks: List[Tuple[T, asyncio.Future[R]]] = []
        self.last_batch_time = time.time()
        self._lock = asyncio.Lock()

    async def add_task(self, task: T) -> R:
        """タスクをバッチに追加"""
        future: asyncio.Future[R] = asyncio.Future()

        async with self._lock:
            self.pending_tasks.append((task, future))

            # バッチサイズまたは時間しきい値に到達した場合
            should_process = (
                len(self.pending_tasks) >= self.batch_size or
                time.time() - self.last_batch_time >= self.max_wait_time
            )

            if should_process:
                await self._process_batch()

        return await future

    async def _process_batch(self):
        """バッチ処理実行"""
        if not self.pending_tasks:
            return

        batch = self.pending_tasks.copy()
        self.pending_tasks.clear()
        self.last_batch_time = time.time()

        try:
            # バッチ処理の実装はサブクラスで定義
            await self._execute_batch(batch)
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # 全てのFutureにエラーを設定
            for _, future in batch:
                if not future.done():
                    future.set_exception(e)

    async def _execute_batch(self, batch: List[Tuple[T, asyncio.Future[R]]]):
        """バッチ実行（サブクラスで実装）"""
        raise NotImplementedError("Subclasses must implement _execute_batch")

    async def flush(self):
        """残りのタスクを強制処理"""
        async with self._lock:
            if self.pending_tasks:
                await self._process_batch()


class LoadBalancer:
    """負荷分散管理"""

    def __init__(self, worker_config: WorkerConfig):
        self.config = worker_config
        self.worker_loads: Dict[int, float] = {}
        self.last_update = time.time()

    def select_worker(self, workers: List[int]) -> int:
        """最適なワーカーを選択"""
        if not workers:
            raise ValueError("No workers available")

        current_time = time.time()

        # 負荷情報を更新
        if current_time - self.last_update > 1.0:  # 1秒ごとに更新
            self._update_worker_loads(workers)
            self.last_update = current_time

        # 最も負荷の低いワーカーを選択
        return min(workers, key=lambda w: self.worker_loads.get(w, 0.0))

    def _update_worker_loads(self, workers: List[int]):
        """ワーカー負荷の更新"""
        try:
            # プロセス単位のCPU使用率を取得
            for worker_id in workers:
                try:
                    process = psutil.Process(worker_id)
                    cpu_percent = process.cpu_percent()
                    self.worker_loads[worker_id] = cpu_percent
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.worker_loads[worker_id] = 0.0
        except Exception as e:
            logger.warning(f"Failed to update worker loads: {e}")


class ParallelProcessor:
    """並列処理エンジン"""

    def __init__(self, config: Optional[WorkerConfig] = None):
        self.config = config or WorkerConfig()
        self.executor: Optional[concurrent.futures.ProcessPoolExecutor] = None
        self.current_workers = self.config.min_workers
        self.is_running = False
        self.stats = WorkerStats(
            worker_count=0,
            active_tasks=0,
            queued_tasks=0,
            completed_tasks=0,
            failed_tasks=0,
            cpu_utilization=0.0,
            memory_utilization=0.0,
            avg_task_time=0.0,
            queue_wait_time=0.0
        )

        # メトリクス管理
        self.task_metrics: List[TaskMetrics] = []
        self.task_queue = asyncio.Queue(maxsize=self.config.queue_size_limit)
        self.load_balancer = LoadBalancer(self.config)

        # 監視タスク
        self._monitor_task: Optional[asyncio.Task] = None
        self._scaling_lock = asyncio.Lock()

    async def start(self):
        """並列処理開始"""
        if self.is_running:
            return

        self.is_running = True
        await self._create_executor()

        # 監視タスクを開始
        if self.config.strategy in [WorkerStrategy.DYNAMIC, WorkerStrategy.CPU_ADAPTIVE, WorkerStrategy.LOAD_ADAPTIVE]:
            self._monitor_task = asyncio.create_task(self._monitor_and_scale())

        logger.info(f"Parallel processor started with {self.current_workers} workers")

    async def stop(self):
        """並列処理停止"""
        if not self.is_running:
            return

        self.is_running = False

        # 監視タスクを停止
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # エグゼキューターを停止
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None

        logger.info("Parallel processor stopped")

    async def submit_task(
        self,
        func: Callable[..., R],
        *args,
        priority: TaskPriority = TaskPriority.MEDIUM,
        task_id: Optional[str] = None,
        **kwargs
    ) -> R:
        """
        タスクを並列実行キューに投入

        Args:
            func: 実行する関数
            *args: 関数の引数
            priority: タスク優先度
            task_id: タスクID（省略時は自動生成）
            **kwargs: 関数のキーワード引数

        Returns:
            タスクの実行結果
        """
        if not self.is_running:
            await self.start()

        task_id = task_id or f"task_{int(time.time() * 1000000)}"
        submit_time = datetime.now()

        # タスクメトリクス作成
        metrics = TaskMetrics(
            task_id=task_id,
            priority=priority,
            submit_time=submit_time
        )

        try:
            # キューサイズ制限チェック
            if self.task_queue.qsize() >= self.config.queue_size_limit:
                raise RuntimeError(f"Task queue is full (limit: {self.config.queue_size_limit})")

            # タスクを実行
            start_time = time.time()
            metrics.start_time = datetime.now()
            metrics.queue_time = (metrics.start_time - submit_time).total_seconds()

            # 実際の並列実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                functools.partial(self._execute_task_with_metrics, func, metrics, *args, **kwargs)
            )

            # 成功メトリクス更新
            metrics.end_time = datetime.now()
            metrics.execution_time = time.time() - start_time
            metrics.success = True

            self.stats.completed_tasks += 1
            self.task_metrics.append(metrics)

            return result

        except Exception as e:
            # エラーメトリクス更新
            metrics.end_time = datetime.now()
            metrics.success = False
            metrics.error_message = str(e)

            self.stats.failed_tasks += 1
            self.task_metrics.append(metrics)

            logger.error(f"Task {task_id} failed: {e}")
            raise

    def _execute_task_with_metrics(
        self,
        func: Callable[..., R],
        metrics: TaskMetrics,
        *args,
        **kwargs
    ) -> R:
        """メトリクス付きでタスクを実行"""
        process = psutil.Process()
        start_cpu_time = process.cpu_times()
        start_memory = process.memory_info().rss

        try:
            # 実際のタスク実行
            result = func(*args, **kwargs)

            # メトリクス収集
            end_cpu_time = process.cpu_times()
            end_memory = process.memory_info().rss

            metrics.worker_id = process.pid
            metrics.cpu_time = (end_cpu_time.user + end_cpu_time.system) - (start_cpu_time.user + start_cpu_time.system)
            metrics.memory_used = end_memory - start_memory

            return result

        except Exception as e:
            metrics.error_message = str(e)
            raise

    async def submit_batch(
        self,
        func: Callable[[List[T]], List[R]],
        tasks: List[T],
        batch_size: Optional[int] = None
    ) -> List[R]:
        """
        バッチタスクの並列実行

        Args:
            func: バッチ処理関数
            tasks: タスクリスト
            batch_size: バッチサイズ

        Returns:
            結果リスト
        """
        batch_size = batch_size or self.config.batch_size
        results = []

        # バッチに分割
        batches = [tasks[i:i+batch_size] for i in range(0, len(tasks), batch_size)]

        # 並列実行
        batch_futures = [
            self.submit_task(func, batch, task_id=f"batch_{i}")
            for i, batch in enumerate(batches)
        ]

        # 結果収集
        batch_results = await asyncio.gather(*batch_futures)

        # 結果を平坦化
        for batch_result in batch_results:
            results.extend(batch_result)

        return results

    async def _create_executor(self):
        """エグゼキューター作成"""
        if self.executor:
            self.executor.shutdown(wait=False)

        self.executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.current_workers,
            initializer=self._worker_initializer
        )

        self.stats.worker_count = self.current_workers

    def _worker_initializer(self):
        """ワーカープロセス初期化"""
        # ワーカープロセス固有の初期化処理
        import signal
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    async def _monitor_and_scale(self):
        """監視とスケーリング"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.monitoring_interval)
                await self._update_stats()

                if self.config.strategy == WorkerStrategy.CPU_ADAPTIVE:
                    await self._scale_by_cpu_usage()
                elif self.config.strategy == WorkerStrategy.LOAD_ADAPTIVE:
                    await self._scale_by_queue_load()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

    async def _update_stats(self):
        """統計情報更新"""
        try:
            # CPU使用率取得
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # タスクメトリクスから統計計算
            recent_tasks = [
                m for m in self.task_metrics
                if m.end_time and m.end_time > datetime.now() - timedelta(minutes=5)
            ]

            if recent_tasks:
                avg_execution_time = sum(
                    m.execution_time for m in recent_tasks if m.execution_time
                ) / len(recent_tasks)

                avg_queue_time = sum(
                    m.queue_time for m in recent_tasks if m.queue_time
                ) / len(recent_tasks)
            else:
                avg_execution_time = 0.0
                avg_queue_time = 0.0

            # 統計更新
            self.stats.cpu_utilization = cpu_percent / 100.0
            self.stats.memory_utilization = memory.percent / 100.0
            self.stats.avg_task_time = avg_execution_time
            self.stats.queue_wait_time = avg_queue_time
            self.stats.queued_tasks = self.task_queue.qsize()
            self.stats.last_update = datetime.now()

        except Exception as e:
            logger.warning(f"Failed to update stats: {e}")

    async def _scale_by_cpu_usage(self):
        """CPU使用率に基づくスケーリング"""
        async with self._scaling_lock:
            current_cpu = self.stats.cpu_utilization
            target_cpu = self.config.target_cpu_utilization

            should_scale_up = (
                current_cpu > self.config.scale_up_threshold and
                self.current_workers < self.config.max_workers and
                self.stats.queued_tasks > 0
            )

            should_scale_down = (
                current_cpu < self.config.scale_down_threshold and
                self.current_workers > self.config.min_workers and
                self.stats.queued_tasks == 0
            )

            if should_scale_up:
                new_workers = min(
                    self.current_workers + 1,
                    self.config.max_workers
                )
                await self._scale_workers(new_workers)
                logger.info(f"Scaled up workers: {self.current_workers} -> {new_workers} (CPU: {current_cpu:.1%})")

            elif should_scale_down:
                new_workers = max(
                    self.current_workers - 1,
                    self.config.min_workers
                )
                await self._scale_workers(new_workers)
                logger.info(f"Scaled down workers: {self.current_workers} -> {new_workers} (CPU: {current_cpu:.1%})")

    async def _scale_by_queue_load(self):
        """キュー負荷に基づくスケーリング"""
        async with self._scaling_lock:
            queue_size = self.stats.queued_tasks
            queue_ratio = queue_size / self.config.queue_size_limit

            # キューが多い場合はスケールアップ
            if queue_ratio > 0.7 and self.current_workers < self.config.max_workers:
                new_workers = min(
                    self.current_workers + math.ceil(queue_ratio * 2),
                    self.config.max_workers
                )
                await self._scale_workers(new_workers)

            # キューが少ない場合はスケールダウン
            elif queue_ratio < 0.1 and self.current_workers > self.config.min_workers:
                new_workers = max(
                    self.current_workers - 1,
                    self.config.min_workers
                )
                await self._scale_workers(new_workers)

    async def _scale_workers(self, new_worker_count: int):
        """ワーカー数変更"""
        if new_worker_count == self.current_workers:
            return

        old_count = self.current_workers
        self.current_workers = new_worker_count

        # エグゼキューターを再作成
        await self._create_executor()

        logger.info(f"Worker count scaled: {old_count} -> {new_worker_count}")

    def get_stats(self) -> WorkerStats:
        """現在の統計情報取得"""
        return self.stats

    def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート生成"""
        recent_tasks = [
            m for m in self.task_metrics
            if m.end_time and m.end_time > datetime.now() - timedelta(hours=1)
        ]

        if not recent_tasks:
            return {"message": "No recent tasks"}

        successful_tasks = [m for m in recent_tasks if m.success]
        failed_tasks = [m for m in recent_tasks if not m.success]

        report = {
            "worker_stats": {
                "current_workers": self.current_workers,
                "cpu_utilization": f"{self.stats.cpu_utilization:.1%}",
                "memory_utilization": f"{self.stats.memory_utilization:.1%}",
                "target_cpu": f"{self.config.target_cpu_utilization:.1%}"
            },
            "task_performance": {
                "total_tasks": len(recent_tasks),
                "successful_tasks": len(successful_tasks),
                "failed_tasks": len(failed_tasks),
                "success_rate": f"{len(successful_tasks) / len(recent_tasks):.1%}" if recent_tasks else "0%",
                "avg_execution_time": f"{self.stats.avg_task_time:.3f}s",
                "avg_queue_time": f"{self.stats.queue_wait_time:.3f}s"
            },
            "queue_stats": {
                "current_queue_size": self.stats.queued_tasks,
                "queue_limit": self.config.queue_size_limit,
                "queue_utilization": f"{self.stats.queued_tasks / self.config.queue_size_limit:.1%}"
            },
            "optimization_metrics": {
                "cpu_efficiency": self.stats.cpu_utilization / self.config.target_cpu_utilization,
                "worker_efficiency": self.stats.avg_task_time / (self.stats.avg_task_time + self.stats.queue_wait_time) if (self.stats.avg_task_time + self.stats.queue_wait_time) > 0 else 1.0,
                "scaling_effective": self.current_workers > self.config.min_workers
            }
        }

        return report

    def clear_metrics(self):
        """メトリクスクリア"""
        self.task_metrics.clear()
        logger.info("Task metrics cleared")


# グローバルインスタンス
default_processor = ParallelProcessor()


async def parallel_execute(
    func: Callable[..., R],
    *args,
    priority: TaskPriority = TaskPriority.MEDIUM,
    processor: Optional[ParallelProcessor] = None,
    **kwargs
) -> R:
    """
    便利関数：並列実行

    使用例:
        result = await parallel_execute(expensive_function, arg1, arg2, priority=TaskPriority.HIGH)
    """
    proc = processor or default_processor
    return await proc.submit_task(func, *args, priority=priority, **kwargs)


async def parallel_batch_execute(
    func: Callable[[List[T]], List[R]],
    tasks: List[T],
    batch_size: Optional[int] = None,
    processor: Optional[ParallelProcessor] = None
) -> List[R]:
    """
    便利関数：バッチ並列実行

    使用例:
        results = await parallel_batch_execute(batch_process_function, task_list, batch_size=50)
    """
    proc = processor or default_processor
    return await proc.submit_batch(func, tasks, batch_size)