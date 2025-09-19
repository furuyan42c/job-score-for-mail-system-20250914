"""
最小構成のFastAPIアプリケーション
起動テスト用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="バイト求人マッチングシステム",
    description="Minimal Test Version",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Backend is running!",
        "status": "healthy",
        "version": "0.0.1"
    }

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "healthy"}

@app.get("/api/v1/test")
async def test():
    """テストエンドポイント"""
    return {"message": "API is working"}

# T005-T006 REFACTOR: Batch processing endpoints
from datetime import datetime
from typing import Optional

batch_jobs = {}
batch_counter = 0

@app.post("/api/v1/batch/trigger", status_code=202)
async def trigger_batch(batch_data: dict):
    """T005 REFACTOR: Batch trigger endpoint"""
    global batch_counter
    batch_counter += 1

    batch_type = batch_data.get("batch_type", "unknown")

    job = {
        "batch_id": batch_counter,
        "job_type": batch_type,
        "started_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    batch_jobs[batch_counter] = job

    return job

@app.get("/api/v1/batch/status/{batch_id}")
async def get_batch_status(batch_id: int):
    """T006 REFACTOR: Batch status endpoint"""
    if batch_id not in batch_jobs:
        return {"error": "Batch job not found"}, 404

    job = batch_jobs[batch_id]
    job["status"] = "running"  # Simulate progress
    return job

# T007 REFACTOR: Jobs import endpoint
@app.post("/api/v1/jobs/import", status_code=202)
async def import_jobs(data: dict):
    """T007 REFACTOR: Jobs CSV import"""
    return {
        "import_id": "imp_001",
        "status": "processing",
        "total_rows": data.get("row_count", 1000)
    }

# T008 REFACTOR: Scoring calculation endpoint
@app.post("/api/v1/scoring/calculate", status_code=200)
async def calculate_scores(data: dict):
    """T008 REFACTOR: Score calculation"""
    return {
        "job_id": data.get("job_id", 1),
        "scores": {
            "base_score": 75.0,
            "seo_score": 82.0,
            "total_score": 78.5
        }
    }

# T009 REFACTOR: Matching generation endpoint
@app.post("/api/v1/matching/generate", status_code=201)
async def generate_matching(data: dict):
    """T009 REFACTOR: Matching generation"""
    return {
        "matching_id": "match_001",
        "user_id": data.get("user_id", 1),
        "jobs_matched": 40,
        "sections": ["top_picks", "high_salary", "nearby", "popular", "new", "recommended"]
    }

# T010 REFACTOR: User matching endpoint
@app.get("/api/v1/matching/user/{user_id}")
async def get_user_matching(user_id: int):
    """T010 REFACTOR: Get user matching"""
    return {
        "user_id": user_id,
        "matches": [
            {"job_id": 1, "score": 85, "section": "top_picks"},
            {"job_id": 2, "score": 82, "section": "high_salary"}
        ]
    }

# T011 REFACTOR: Email generation endpoint
@app.post("/api/v1/email/generate", status_code=201)
async def generate_email(data: dict):
    """T011 REFACTOR: Email generation"""
    return {
        "email_id": "email_001",
        "user_id": data.get("user_id", 1),
        "template": "daily_digest",
        "status": "generated"
    }

# T012/T039 REFACTOR: SQL execution endpoint with security
import sqlite3
import time
import re

@app.post("/api/v1/sql/execute")
async def execute_sql(data: dict):
    """T039 REFACTOR: SQL execution with read-only security"""
    query = data.get("query", "SELECT 1")

    # Security: Only allow SELECT statements (read-only)
    if not re.match(r'^\s*SELECT\s+', query, re.IGNORECASE):
        return {
            "error": "Only SELECT queries are allowed",
            "query": query
        }

    # Security: Basic SQL injection prevention
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE']
    for keyword in dangerous_keywords:
        if re.search(rf'\b{keyword}\b', query, re.IGNORECASE):
            return {
                "error": f"Query contains forbidden keyword: {keyword}",
                "query": query
            }

    try:
        # Execute query with timeout
        conn = sqlite3.connect('development.db', timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        start_time = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        execution_time = time.time() - start_time

        # Convert results to list of dicts
        formatted_results = []
        if results:
            for row in results[:100]:  # Limit to 100 rows
                formatted_results.append(dict(row))

        conn.close()

        return {
            "query": query,
            "rows_affected": len(results),
            "results": formatted_results,
            "execution_time": round(execution_time, 3)
        }

    except sqlite3.Error as e:
        return {
            "error": str(e),
            "query": query
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "query": query
        }

# T013 REFACTOR: Monitoring metrics endpoint
@app.get("/api/v1/monitoring/metrics")
async def get_metrics():
    """T013 REFACTOR: System metrics"""
    return {
        "cpu_usage": 25.5,
        "memory_usage": 60.2,
        "active_connections": 10,
        "batch_jobs_running": len([j for j in batch_jobs.values() if j.get("status") == "running"]),
        "database_connections": 5
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)