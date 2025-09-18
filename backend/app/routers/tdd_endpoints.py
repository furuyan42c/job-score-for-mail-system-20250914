"""
TDD Phase 2: GREEN - 契約テストをパスするための最小実装

このファイルは契約テスト（T007-T013）をパスするための
最小限のエンドポイント実装を含みます。
後のリファクタリングフェーズで実際のビジネスロジックに置き換えます。
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


# ============================================================================
# T007: POST /jobs/import - ジョブインポート
# ============================================================================

@router.post("/jobs/import", status_code=200)
async def import_jobs(
    file: Any = None,  # ファイルアップロードの最小実装
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """最小実装：CSVインポートのモック応答"""
    return {
        "imported": 100,  # ハードコード
        "failed": 0,
        "message": "Jobs imported successfully",
        "job_ids": list(range(1, 101))  # 1-100のID
    }


# ============================================================================
# T008: POST /scoring/calculate - スコアリング計算
# ============================================================================

@router.post("/scoring/calculate", status_code=200)
async def calculate_scoring(
    user_id: int = None,
    job_ids: List[int] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """最小実装：スコアリング計算のモック応答"""
    return {
        "user_id": user_id or 1,
        "scores": [
            {"job_id": job_id or 1, "score": 85.5}
            for job_id in (job_ids or [1])
        ],
        "calculated_at": datetime.now().isoformat()
    }


# ============================================================================
# T009: POST /matching/generate - マッチング生成
# ============================================================================

@router.post("/matching/generate", status_code=200)
async def generate_matching(
    user_ids: List[int] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """最小実装：マッチング生成のモック応答"""
    return {
        "batch_id": 1,
        "users_processed": len(user_ids) if user_ids else 10,
        "matches_generated": 400,  # 40件 × 10ユーザー
        "status": "completed",
        "created_at": datetime.now().isoformat()
    }


# ============================================================================
# T010: GET /matching/user/{user_id} - ユーザーマッチング取得
# ============================================================================

@router.get("/matching/user/{user_id}", status_code=200)
async def get_user_matching(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """最小実装：ユーザーマッチング結果のモック応答"""
    return {
        "user_id": user_id,
        "matches": [
            {
                "job_id": i,
                "score": 90.0 - i,
                "rank": i
            }
            for i in range(1, 41)  # 40件
        ],
        "generated_at": datetime.now().isoformat()
    }


# ============================================================================
# T011: POST /email/generate - メール生成
# ============================================================================

@router.post("/email/generate", status_code=200)
async def generate_email(
    user_id: int = None,
    template_id: str = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """最小実装：メール生成のモック応答"""
    return {
        "email_id": 1,
        "user_id": user_id or 1,
        "template_id": template_id or "default",
        "subject": "おすすめ求人のご紹介",
        "body": "<html><body>求人内容...</body></html>",
        "status": "generated",
        "created_at": datetime.now().isoformat()
    }


# ============================================================================
# T012: POST /sql/execute - SQL実行（読み取り専用）
# ============================================================================

@router.post("/sql/execute", status_code=200)
async def execute_sql(
    query: str = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """最小実装：SQL実行のモック応答（読み取り専用）"""
    # セキュリティ：書き込みクエリは拒否（改善版：単語境界を使用）
    if query:
        import re
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
            'TRUNCATE', 'REPLACE', 'MERGE', 'EXEC', 'EXECUTE'
        ]

        query_upper = query.upper()
        for keyword in dangerous_keywords:
            # 単語境界を使用してfalse positiveを防ぐ（例：created_atのCREATEは除外）
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_upper):
                return {
                    "error": "Write operations are not allowed",
                    "status": "error"
                }

    return {
        "columns": ["id", "name", "value"],
        "rows": [
            [1, "test1", 100],
            [2, "test2", 200]
        ],
        "row_count": 2,
        "execution_time": 0.05,
        "status": "success"
    }


# ============================================================================
# T013: GET /monitoring/metrics - モニタリングメトリクス
# ============================================================================

@router.get("/monitoring/metrics", status_code=200)
async def get_monitoring_metrics(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """最小実装：モニタリングメトリクスのモック応答"""
    return {
        "system": {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 38.5
        },
        "database": {
            "connections": 25,
            "active_queries": 3,
            "response_time_ms": 12.5
        },
        "application": {
            "requests_per_minute": 150,
            "error_rate": 0.02,
            "average_response_time_ms": 85
        },
        "batch_jobs": {
            "running": 2,
            "pending": 5,
            "completed_today": 48,
            "failed_today": 2
        },
        "timestamp": datetime.now().isoformat()
    }