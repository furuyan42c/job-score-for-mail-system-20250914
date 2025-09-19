"""
バッチ処理サービス - T005-T009 REFACTOR フェーズ実装
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import random
import asyncio
from enum import Enum


class BatchType(str, Enum):
    """バッチタイプ定義"""
    DAILY_MATCHING = "daily_matching"
    SCORING = "scoring"
    EMAIL_GENERATION = "email_generation"
    DATA_IMPORT = "data_import"
    CLEANUP = "cleanup"
    ANALYTICS = "analytics"


class BatchStatus(str, Enum):
    """バッチステータス定義"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchService:
    """バッチ処理関連のビジネスロジック"""

    def __init__(self):
        self.batch_jobs = {}
        self.batch_counter = 0
        self.running_batches = {}

    def trigger_batch(self, batch_type: str, force: bool = False,
                     parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """バッチ処理をトリガー"""

        # バッチタイプ検証
        if batch_type not in [t.value for t in BatchType]:
            raise ValueError(f"Invalid batch type: {batch_type}")

        # 既存バッチの実行チェック
        if not force:
            running_batch = self._get_running_batch(batch_type)
            if running_batch:
                raise RuntimeError(f"Batch {batch_type} is already running. Use force=True to override.")

        # 新しいバッチジョブ作成
        self.batch_counter += 1
        batch_id = self.batch_counter

        job = {
            "batch_id": batch_id,
            "job_type": batch_type,
            "started_at": datetime.now().isoformat(),
            "status": BatchStatus.PENDING.value,
            "parameters": parameters or {},
            "force": force,
            "created_by": "api",
            "total_records": None,
            "processed_records": 0,
            "success_count": 0,
            "error_count": 0,
            "progress_percentage": 0,
            "estimated_completion": None,
            "error_logs": [],
            "metrics": {}
        }

        # バッチジョブを保存
        self.batch_jobs[batch_id] = job

        # 実行中バッチとして追跡
        self.running_batches[batch_type] = batch_id

        # 非同期でバッチ処理を開始（シミュレーション）
        self._start_batch_async(batch_id, batch_type)

        return {
            "batch_id": batch_id,
            "job_type": batch_type,
            "started_at": job["started_at"],
            "status": job["status"]
        }

    def get_batch_status(self, batch_id: int) -> Dict[str, Any]:
        """バッチ処理ステータス取得"""

        if batch_id not in self.batch_jobs:
            return {
                "error": "Batch not found",
                "batch_id": batch_id,
                "status": "not_found"
            }

        job = self.batch_jobs[batch_id]

        # 進行中の場合は進捗を更新
        if job["status"] == BatchStatus.RUNNING.value:
            self._update_batch_progress(batch_id)

        return {
            "batch_id": batch_id,
            "job_type": job["job_type"],
            "status": job["status"],
            "started_at": job["started_at"],
            "progress_percentage": job["progress_percentage"],
            "total_records": job["total_records"],
            "processed_records": job["processed_records"],
            "success_count": job["success_count"],
            "error_count": job["error_count"],
            "estimated_completion": job["estimated_completion"],
            "completed_at": job.get("completed_at"),
            "error_logs": job["error_logs"][-5:] if job["error_logs"] else [],  # 最新5件のエラー
            "metrics": job["metrics"]
        }

    def list_batches(self, status: Optional[str] = None,
                    job_type: Optional[str] = None,
                    limit: int = 10) -> Dict[str, Any]:
        """バッチ一覧取得"""

        batches = list(self.batch_jobs.values())

        # フィルタリング
        if status:
            batches = [b for b in batches if b["status"] == status]
        if job_type:
            batches = [b for b in batches if b["job_type"] == job_type]

        # 開始時刻の降順でソート
        batches.sort(key=lambda x: x["started_at"], reverse=True)

        # 制限適用
        batches = batches[:limit]

        # 簡略化された情報で返す
        result_batches = []
        for batch in batches:
            result_batches.append({
                "batch_id": batch["batch_id"],
                "job_type": batch["job_type"],
                "status": batch["status"],
                "started_at": batch["started_at"],
                "progress_percentage": batch["progress_percentage"],
                "completed_at": batch.get("completed_at")
            })

        return {
            "batches": result_batches,
            "total_count": len(result_batches),
            "filters": {
                "status": status,
                "job_type": job_type,
                "limit": limit
            }
        }

    def cancel_batch(self, batch_id: int) -> Dict[str, Any]:
        """バッチ処理をキャンセル"""

        if batch_id not in self.batch_jobs:
            return {
                "error": "Batch not found",
                "batch_id": batch_id,
                "success": False
            }

        job = self.batch_jobs[batch_id]

        if job["status"] not in [BatchStatus.PENDING.value, BatchStatus.RUNNING.value]:
            return {
                "error": f"Cannot cancel batch in status: {job['status']}",
                "batch_id": batch_id,
                "success": False
            }

        # キャンセル処理
        job["status"] = BatchStatus.CANCELLED.value
        job["completed_at"] = datetime.now().isoformat()
        job["cancelled_by"] = "api"

        # 実行中バッチリストから削除
        job_type = job["job_type"]
        if job_type in self.running_batches and self.running_batches[job_type] == batch_id:
            del self.running_batches[job_type]

        return {
            "batch_id": batch_id,
            "status": job["status"],
            "completed_at": job["completed_at"],
            "success": True
        }

    def get_batch_metrics(self, batch_id: int) -> Dict[str, Any]:
        """バッチメトリクス取得"""

        if batch_id not in self.batch_jobs:
            return {"error": "Batch not found"}

        job = self.batch_jobs[batch_id]

        # 実行時間計算
        started_at = datetime.fromisoformat(job["started_at"])
        if job.get("completed_at"):
            completed_at = datetime.fromisoformat(job["completed_at"])
            execution_time = (completed_at - started_at).total_seconds()
        else:
            execution_time = (datetime.now() - started_at).total_seconds()

        # スループット計算
        throughput = job["processed_records"] / execution_time if execution_time > 0 else 0

        return {
            "batch_id": batch_id,
            "execution_time_seconds": execution_time,
            "throughput_records_per_second": throughput,
            "success_rate": (job["success_count"] / max(job["processed_records"], 1)) * 100,
            "error_rate": (job["error_count"] / max(job["processed_records"], 1)) * 100,
            "memory_usage_mb": job["metrics"].get("memory_usage_mb", 0),
            "cpu_usage_percent": job["metrics"].get("cpu_usage_percent", 0),
            "estimated_total_time": job["metrics"].get("estimated_total_time", 0)
        }

    # プライベートメソッド
    def _get_running_batch(self, batch_type: str) -> Optional[int]:
        """実行中のバッチを取得"""
        batch_id = self.running_batches.get(batch_type)
        if batch_id and batch_id in self.batch_jobs:
            job = self.batch_jobs[batch_id]
            if job["status"] in [BatchStatus.PENDING.value, BatchStatus.RUNNING.value]:
                return batch_id
        return None

    def _start_batch_async(self, batch_id: int, batch_type: str):
        """非同期でバッチ処理を開始（シミュレーション）"""
        # 実際の実装ではここでバックグラウンドタスクを開始
        # 現在はシミュレーションとして即座にRUNNINGに変更
        job = self.batch_jobs[batch_id]
        job["status"] = BatchStatus.RUNNING.value

        # バッチタイプに応じた処理時間とレコード数を設定
        batch_configs = {
            BatchType.DAILY_MATCHING.value: {"records": 10000, "duration_minutes": 30},
            BatchType.SCORING.value: {"records": 100000, "duration_minutes": 45},
            BatchType.EMAIL_GENERATION.value: {"records": 5000, "duration_minutes": 15},
            BatchType.DATA_IMPORT.value: {"records": 50000, "duration_minutes": 20},
            BatchType.CLEANUP.value: {"records": 1000, "duration_minutes": 5},
            BatchType.ANALYTICS.value: {"records": 25000, "duration_minutes": 60}
        }

        config = batch_configs.get(batch_type, {"records": 1000, "duration_minutes": 10})
        job["total_records"] = config["records"]

        # 完了予定時刻を設定
        estimated_completion = datetime.now() + timedelta(minutes=config["duration_minutes"])
        job["estimated_completion"] = estimated_completion.isoformat()

    def _update_batch_progress(self, batch_id: int):
        """バッチ進捗を更新（シミュレーション）"""
        job = self.batch_jobs[batch_id]

        if job["status"] != BatchStatus.RUNNING.value:
            return

        # 開始からの経過時間
        started_at = datetime.fromisoformat(job["started_at"])
        elapsed_seconds = (datetime.now() - started_at).total_seconds()

        # 推定完了時刻から進捗計算
        if job["estimated_completion"]:
            estimated_completion = datetime.fromisoformat(job["estimated_completion"])
            total_duration = (estimated_completion - started_at).total_seconds()
            progress = min(100, (elapsed_seconds / total_duration) * 100)
        else:
            progress = min(100, elapsed_seconds / 600 * 100)  # 10分で100%と仮定

        job["progress_percentage"] = round(progress, 1)

        # レコード処理数を更新
        if job["total_records"]:
            job["processed_records"] = int(job["total_records"] * progress / 100)
            job["success_count"] = int(job["processed_records"] * 0.95)  # 95%成功と仮定
            job["error_count"] = job["processed_records"] - job["success_count"]

        # 完了チェック
        if progress >= 100:
            job["status"] = BatchStatus.COMPLETED.value
            job["completed_at"] = datetime.now().isoformat()
            job["progress_percentage"] = 100

            # 実行中バッチリストから削除
            job_type = job["job_type"]
            if job_type in self.running_batches:
                del self.running_batches[job_type]

        # メトリクス更新
        job["metrics"].update({
            "memory_usage_mb": random.uniform(50, 200),
            "cpu_usage_percent": random.uniform(10, 80),
            "disk_io_mb": random.uniform(10, 100)
        })


# シングルトンインスタンス
batch_service = BatchService()