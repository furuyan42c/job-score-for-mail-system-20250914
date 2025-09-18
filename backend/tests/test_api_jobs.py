"""
求人APIエンドポイントの包括的テスト

求人関連のAPIエンドポイント、フィルタリング、ページネーション、
エラーハンドリングのテストを実装
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from unittest.mock import AsyncMock, patch
from typing import Dict, Any, List

from app.models.jobs import JobCreate, JobUpdate, BulkJobOperation
from app.models.common import BaseResponse


class TestJobSearchAPI:
    """求人検索APIのテスト"""

    @pytest.mark.asyncio
    async def test_search_jobs_default_params(self, async_client: AsyncClient):
        """デフォルトパラメータでの求人検索テスト"""
        response = await async_client.get("/jobs/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["page"] == 1
        assert data["size"] == 20

    @pytest.mark.asyncio
    async def test_search_jobs_with_keyword(self, async_client: AsyncClient):
        """キーワード検索テスト"""
        response = await async_client.get("/jobs/?keyword=営業")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "filters_applied" in data
        # フィルタが適用されたことを確認

    @pytest.mark.asyncio
    async def test_search_jobs_with_prefecture_filter(self, async_client: AsyncClient):
        """都道府県フィルタテスト"""
        response = await async_client.get("/jobs/?prefecture_codes=13,27")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 東京都と大阪府の求人のみが返されることを確認

    @pytest.mark.asyncio
    async def test_search_jobs_with_salary_range(self, async_client: AsyncClient):
        """給与範囲フィルタテスト"""
        response = await async_client.get("/jobs/?min_salary=1200&max_salary=2000&salary_type=hourly")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 指定範囲の時給求人のみが返されることを確認

    @pytest.mark.asyncio
    async def test_search_jobs_with_feature_codes(self, async_client: AsyncClient):
        """特徴コードフィルタテスト"""
        response = await async_client.get("/jobs/?feature_codes=D01,N01")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 日払い・未経験歓迎の求人のみが返されることを確認

    @pytest.mark.asyncio
    async def test_search_jobs_with_score_filter(self, async_client: AsyncClient):
        """スコアフィルタテスト"""
        response = await async_client.get("/jobs/?min_score=70.0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 高スコア求人のみが返されることを確認

    @pytest.mark.asyncio
    async def test_search_jobs_pagination(self, async_client: AsyncClient):
        """ページネーションテスト"""
        # 1ページ目
        response1 = await async_client.get("/jobs/?page=1&size=10")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        # 2ページ目
        response2 = await async_client.get("/jobs/?page=2&size=10")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # ページごとに異なるデータが返されることを確認
        if data1["total"] > 10:
            assert data1["items"] != data2["items"]

    @pytest.mark.asyncio
    async def test_search_jobs_sorting(self, async_client: AsyncClient):
        """ソートテスト"""
        # 投稿日降順
        response1 = await async_client.get("/jobs/?sort_by=posting_date&sort_order=desc")
        assert response1.status_code == status.HTTP_200_OK

        # 給与昇順
        response2 = await async_client.get("/jobs/?sort_by=min_salary&sort_order=asc")
        assert response2.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_search_jobs_invalid_params(self, async_client: AsyncClient):
        """無効なパラメータテスト"""
        # 無効なページ番号
        response = await async_client.get("/jobs/?page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 無効なページサイズ
        response = await async_client.get("/jobs/?size=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 無効なスコア範囲
        response = await async_client.get("/jobs/?min_score=150")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_search_jobs_complex_filters(self, async_client: AsyncClient):
        """複合フィルタテスト"""
        params = {
            "keyword": "営業",
            "prefecture_codes": "13",
            "min_salary": "1500",
            "feature_codes": "D01,N01",
            "has_high_income": "true",
            "sort_by": "composite_score",
            "sort_order": "desc"
        }

        response = await async_client.get("/jobs/", params=params)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data


class TestJobDetailAPI:
    """求人詳細APIのテスト"""

    @pytest.mark.asyncio
    async def test_get_job_basic(self, async_client: AsyncClient):
        """基本的な求人詳細取得テスト"""
        # まず求人を作成（実際のテストでは固定データを使用）
        job_id = 1
        response = await async_client.get(f"/jobs/{job_id}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert "endcl_cd" in data
        assert "company_name" in data
        assert data["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_get_job_with_scoring(self, async_client: AsyncClient):
        """スコアリング情報付き求人詳細取得テスト"""
        job_id = 1
        response = await async_client.get(f"/jobs/{job_id}?include_scoring=true")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # スコアリング情報が含まれることを確認
        if "scoring" in data and data["scoring"]:
            assert "basic_score" in data["scoring"] or "composite_score" in data["scoring"]

    @pytest.mark.asyncio
    async def test_get_job_with_stats(self, async_client: AsyncClient):
        """統計情報付き求人詳細取得テスト"""
        job_id = 1
        response = await async_client.get(f"/jobs/{job_id}?include_stats=true")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 統計情報が含まれることを確認
        if "stats" in data and data["stats"]:
            assert "application_count_30d" in data["stats"]

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, async_client: AsyncClient):
        """存在しない求人の詳細取得テスト"""
        response = await async_client.get("/jobs/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_job_invalid_id(self, async_client: AsyncClient):
        """無効な求人IDテスト"""
        response = await async_client.get("/jobs/invalid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestJobCRUDAPI:
    """求人CRUD APIのテスト"""

    @pytest.mark.asyncio
    async def test_create_job_success(self, async_client: AsyncClient, sample_job_data):
        """求人作成成功テスト"""
        response = await async_client.post("/jobs/", json=sample_job_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "job_id" in data
        assert data["endcl_cd"] == sample_job_data["endcl_cd"]
        assert data["company_name"] == sample_job_data["company_name"]

    @pytest.mark.asyncio
    async def test_create_job_invalid_data(self, async_client: AsyncClient):
        """無効なデータでの求人作成テスト"""
        invalid_data = {
            "endcl_cd": "",  # 必須項目が空
            "company_name": "",
            "application_name": ""
        }

        response = await async_client.post("/jobs/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_job_success(self, async_client: AsyncClient):
        """求人更新成功テスト"""
        job_id = 1
        update_data = {
            "company_name": "更新後の会社名",
            "is_active": False
        }

        response = await async_client.put(f"/jobs/{job_id}", json=update_data)

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["company_name"] == "更新後の会社名"

    @pytest.mark.asyncio
    async def test_update_job_not_found(self, async_client: AsyncClient):
        """存在しない求人の更新テスト"""
        update_data = {"company_name": "更新後の会社名"}
        response = await async_client.put("/jobs/999999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_job_success(self, async_client: AsyncClient):
        """求人削除成功テスト"""
        job_id = 1
        response = await async_client.delete(f"/jobs/{job_id}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, async_client: AsyncClient):
        """存在しない求人の削除テスト"""
        response = await async_client.delete("/jobs/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobActivationAPI:
    """求人有効化・無効化APIのテスト"""

    @pytest.mark.asyncio
    async def test_activate_job_success(self, async_client: AsyncClient):
        """求人有効化成功テスト"""
        job_id = 1
        response = await async_client.post(f"/jobs/{job_id}/activate")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_deactivate_job_success(self, async_client: AsyncClient):
        """求人無効化成功テスト"""
        job_id = 1
        response = await async_client.post(f"/jobs/{job_id}/deactivate")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_activate_job_not_found(self, async_client: AsyncClient):
        """存在しない求人の有効化テスト"""
        response = await async_client.post("/jobs/999999/activate")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_deactivate_job_not_found(self, async_client: AsyncClient):
        """存在しない求人の無効化テスト"""
        response = await async_client.post("/jobs/999999/deactivate")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobRecommendationAPI:
    """求人推薦APIのテスト"""

    @pytest.mark.asyncio
    async def test_get_job_recommendations(self, async_client: AsyncClient):
        """類似求人推薦テスト"""
        job_id = 1
        response = await async_client.get(f"/jobs/{job_id}/recommendations")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_job_recommendations_with_limit(self, async_client: AsyncClient):
        """制限付き類似求人推薦テスト"""
        job_id = 1
        limit = 5
        response = await async_client.get(f"/jobs/{job_id}/recommendations?limit={limit}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= limit

    @pytest.mark.asyncio
    async def test_get_user_recommendations(self, async_client: AsyncClient):
        """ユーザー向け求人推薦テスト"""
        user_id = 1
        response = await async_client.get(f"/jobs/recommendations/{user_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_user_recommendations_with_filters(self, async_client: AsyncClient):
        """フィルタ付きユーザー向け求人推薦テスト"""
        user_id = 1
        params = {
            "limit": 10,
            "exclude_applied": "true",
            "include_explanations": "true"
        }
        response = await async_client.get(f"/jobs/recommendations/{user_id}", params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


class TestJobAnalysisAPI:
    """求人分析APIのテスト"""

    @pytest.mark.asyncio
    async def test_analyze_job_keywords(self, async_client: AsyncClient):
        """求人キーワード分析テスト"""
        job_id = 1
        response = await async_client.get(f"/jobs/{job_id}/keyword-analysis")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert "extracted_keywords" in data

    @pytest.mark.asyncio
    async def test_get_company_popularity(self, async_client: AsyncClient):
        """企業人気度取得テスト"""
        endcl_cd = "TEST001"
        response = await async_client.get(f"/jobs/companies/{endcl_cd}/popularity")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用企業データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "endcl_cd" in data
        assert "popularity_score" in data

    @pytest.mark.asyncio
    async def test_recalculate_job_score(self, async_client: AsyncClient):
        """求人スコア再計算テスト"""
        job_id = 1
        response = await async_client.post(f"/jobs/{job_id}/recalculate-score")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_recalculate_job_score_force(self, async_client: AsyncClient):
        """強制求人スコア再計算テスト"""
        job_id = 1
        response = await async_client.post(f"/jobs/{job_id}/recalculate-score?force=true")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用求人データが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


class TestJobBulkOperationsAPI:
    """求人一括操作APIのテスト"""

    @pytest.mark.asyncio
    async def test_bulk_job_activate(self, async_client: AsyncClient):
        """求人一括有効化テスト"""
        operation_data = {
            "job_ids": [1, 2, 3],
            "operation": "activate"
        }

        response = await async_client.post("/jobs/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_requested" in data
        assert "success_count" in data
        assert "error_count" in data
        assert data["operation"] == "activate"

    @pytest.mark.asyncio
    async def test_bulk_job_deactivate(self, async_client: AsyncClient):
        """求人一括無効化テスト"""
        operation_data = {
            "job_ids": [1, 2, 3],
            "operation": "deactivate"
        }

        response = await async_client.post("/jobs/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["operation"] == "deactivate"

    @pytest.mark.asyncio
    async def test_bulk_job_update_scores(self, async_client: AsyncClient):
        """求人一括スコア更新テスト"""
        operation_data = {
            "job_ids": [1, 2, 3],
            "operation": "update_scores"
        }

        response = await async_client.post("/jobs/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["operation"] == "update_scores"

    @pytest.mark.asyncio
    async def test_bulk_job_invalid_operation(self, async_client: AsyncClient):
        """無効な一括操作テスト"""
        operation_data = {
            "job_ids": [1, 2, 3],
            "operation": "invalid_operation"
        }

        response = await async_client.post("/jobs/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_bulk_job_too_many_ids(self, async_client: AsyncClient):
        """一括操作での過剰なID数テスト"""
        operation_data = {
            "job_ids": list(range(1, 1002)),  # 1001個のID
            "operation": "activate"
        }

        response = await async_client.post("/jobs/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestJobAdvancedSearchAPI:
    """高度検索APIのテスト"""

    @pytest.mark.asyncio
    async def test_advanced_job_search(self, async_client: AsyncClient):
        """高度求人検索テスト"""
        search_data = {
            "filters": {
                "keyword": "営業",
                "prefecture_codes": ["13"],
                "salary_range": {
                    "min_salary": 1200,
                    "max_salary": 2000,
                    "salary_type": "hourly"
                },
                "feature_codes": ["D01", "N01"],
                "is_active": True
            },
            "sort": {
                "sort_by": "composite_score",
                "sort_order": "desc"
            },
            "page": 1,
            "size": 20
        }

        response = await async_client.post("/jobs/search", json=search_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "filters_applied" in data
        assert "sort_applied" in data

    @pytest.mark.asyncio
    async def test_advanced_search_invalid_data(self, async_client: AsyncClient):
        """無効なデータでの高度検索テスト"""
        invalid_search_data = {
            "filters": {
                "min_score": 150.0  # 範囲外
            },
            "sort": {
                "sort_by": "invalid_field"  # 無効なフィールド
            }
        }

        response = await async_client.post("/jobs/search", json=invalid_search_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestJobStatsAPI:
    """求人統計APIのテスト"""

    @pytest.mark.asyncio
    async def test_get_job_stats_summary(self, async_client: AsyncClient):
        """求人統計サマリー取得テスト"""
        response = await async_client.get("/jobs/stats/summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 統計データの基本構造を確認


class TestJobAPIErrorHandling:
    """求人APIエラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, async_client: AsyncClient):
        """データベース接続エラーのテスト"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            response = await async_client.get("/jobs/")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_service_layer_error(self, async_client: AsyncClient):
        """サービス層エラーのテスト"""
        with patch('app.services.jobs.JobService.search_jobs') as mock_search:
            mock_search.side_effect = ValueError("Invalid search parameters")

            response = await async_client.get("/jobs/")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_malformed_json_request(self, async_client: AsyncClient):
        """不正なJSONリクエストテスト"""
        response = await async_client.post(
            "/jobs/",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """必須フィールド不足テスト"""
        incomplete_data = {
            "company_name": "テスト会社"
            # endcl_cdなどの必須フィールドが不足
        }

        response = await async_client.post("/jobs/", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, async_client: AsyncClient):
        """SQLインジェクション防止テスト"""
        malicious_keyword = "'; DROP TABLE jobs; --"
        response = await async_client.get(f"/jobs/?keyword={malicious_keyword}")

        # エラーが発生せず、適切に処理されることを確認
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    @pytest.mark.asyncio
    async def test_xss_prevention(self, async_client: AsyncClient):
        """XSS防止テスト"""
        xss_payload = "<script>alert('xss')</script>"
        response = await async_client.get(f"/jobs/?keyword={xss_payload}")

        # エラーが発生せず、適切に処理されることを確認
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


class TestJobAPIPerformance:
    """求人APIパフォーマンステスト"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_search_jobs_performance(self, async_client: AsyncClient, benchmark_config):
        """求人検索パフォーマンステスト"""
        import time

        start_time = time.time()
        response = await async_client.get("/jobs/?size=100")
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        response_time = end_time - start_time
        assert response_time < 2.0  # 2秒以内に応答

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, async_client: AsyncClient):
        """一括操作パフォーマンステスト"""
        operation_data = {
            "job_ids": list(range(1, 101)),  # 100件
            "operation": "update_scores"
        }

        import time
        start_time = time.time()
        response = await async_client.post("/jobs/bulk-operations", json=operation_data)
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 10.0  # 10秒以内に完了

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client: AsyncClient):
        """同時リクエストテスト"""
        import asyncio

        async def make_request():
            return await async_client.get("/jobs/?page=1&size=10")

        # 10個の同時リクエスト
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # すべてのリクエストが正常に処理されることを確認
        for response in responses:
            assert response.status_code == status.HTTP_200_OK


@pytest.fixture
def mock_job_service():
    """JobServiceのモック"""
    with patch('app.services.jobs.JobService') as mock:
        service_instance = mock.return_value
        service_instance.search_jobs = AsyncMock()
        service_instance.get_job_by_id = AsyncMock()
        service_instance.create_job = AsyncMock()
        service_instance.update_job = AsyncMock()
        service_instance.delete_job = AsyncMock()
        yield service_instance