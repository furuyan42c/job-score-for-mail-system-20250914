#!/usr/bin/env python3
"""
T010-T013: 契約テストスイート
APIエンドポイントの契約を検証
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.api.endpoints.contract_endpoints import router

# テスト用アプリケーション
app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)


class TestT010UserMatching:
    """T010: ユーザーマッチング結果取得の契約テスト"""

    def test_get_user_matching_success(self):
        """正常系: ユーザーマッチング結果取得"""
        response = client.get("/api/v1/matching/user/123")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "user_id" in data
        assert data["user_id"] == 123
        assert "matches" in data
        assert isinstance(data["matches"], list)
        assert len(data["matches"]) > 0

        # マッチング結果の構造検証
        match = data["matches"][0]
        assert "job_id" in match
        assert "score" in match
        assert "match_date" in match
        assert "sections" in match
        assert isinstance(match["sections"], list)

    def test_get_user_matching_invalid_user(self):
        """異常系: 無効なユーザーID"""
        response = client.get("/api/v1/matching/user/invalid")
        # FastAPIの型検証により422エラー
        assert response.status_code == 422


class TestT011EmailGenerate:
    """T011: メール生成の契約テスト"""

    def test_generate_email_success(self):
        """正常系: メール生成成功"""
        request_data = {
            "user_id": 456,
            "job_ids": ["JOB_001", "JOB_002", "JOB_003"],
            "template": "weekly_recommendation"
        }

        response = client.post("/api/v1/email/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "user_id" in data
        assert data["user_id"] == 456
        assert "email" in data

        email = data["email"]
        assert "subject" in email
        assert "body" in email
        assert "html_body" in email
        assert "template_used" in email

    def test_generate_email_empty_jobs(self):
        """境界値: 空のジョブリスト"""
        request_data = {
            "user_id": 789,
            "job_ids": []
        }

        response = client.post("/api/v1/email/generate", json=request_data)
        assert response.status_code == 200

    def test_generate_email_missing_fields(self):
        """異常系: 必須フィールド欠落"""
        request_data = {
            "job_ids": ["JOB_001"]
            # user_id missing
        }

        response = client.post("/api/v1/email/generate", json=request_data)
        assert response.status_code == 422


class TestT012SQLExecute:
    """T012: SQL実行APIの契約テスト"""

    def test_execute_select_query(self):
        """正常系: SELECT文の実行"""
        request_data = {
            "query": "SELECT * FROM jobs WHERE status = 'active'",
            "params": {"limit": 10}
        }

        response = client.post("/api/v1/sql/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "query" in data
        assert "rows" in data
        assert isinstance(data["rows"], list)
        assert "row_count" in data
        assert "execution_time_ms" in data

    def test_execute_dangerous_query(self):
        """セキュリティ: 危険なSQL文の拒否"""
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM jobs",
            "TRUNCATE TABLE logs",
            "ALTER TABLE schema"
        ]

        for query in dangerous_queries:
            request_data = {"query": query}
            response = client.post("/api/v1/sql/execute", json=request_data)

            # 危険なクエリは403で拒否
            assert response.status_code == 403

    def test_execute_non_select_query(self):
        """制限: SELECT以外のクエリ拒否"""
        request_data = {
            "query": "UPDATE jobs SET status = 'inactive'"
        }

        response = client.post("/api/v1/sql/execute", json=request_data)
        assert response.status_code == 400


class TestT013MonitoringMetrics:
    """T013: モニタリングメトリクスの契約テスト"""

    def test_get_monitoring_metrics(self):
        """正常系: メトリクス取得"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200
        data = response.json()

        # システムメトリクス検証
        assert "system" in data
        system = data["system"]
        assert "cpu_usage_percent" in system
        assert "memory_usage_percent" in system
        assert "disk_usage_percent" in system
        assert 0 <= system["cpu_usage_percent"] <= 100
        assert 0 <= system["memory_usage_percent"] <= 100
        assert 0 <= system["disk_usage_percent"] <= 100

        # アプリケーションメトリクス検証
        assert "application" in data
        app_metrics = data["application"]
        assert "active_users" in app_metrics
        assert "requests_per_minute" in app_metrics
        assert "average_response_time_ms" in app_metrics
        assert "error_rate" in app_metrics
        assert 0 <= app_metrics["error_rate"] <= 1

        # データベースメトリクス検証
        assert "database" in data
        db = data["database"]
        assert "connection_pool_size" in db
        assert "active_connections" in db
        assert db["active_connections"] <= db["connection_pool_size"]

        # ジョブメトリクス検証
        assert "jobs" in data
        jobs = data["jobs"]
        assert "total_jobs" in jobs
        assert "active_jobs" in jobs
        assert jobs["active_jobs"] <= jobs["total_jobs"]

    def test_metrics_timestamp(self):
        """メトリクスにタイムスタンプが含まれること"""
        response = client.get("/api/v1/monitoring/metrics")
        data = response.json()

        assert "timestamp" in data
        # ISO形式の日時文字列
        assert "T" in data["timestamp"]


def test_health_check():
    """ヘルスチェックエンドポイント"""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])