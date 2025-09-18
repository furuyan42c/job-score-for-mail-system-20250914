"""
求人API統合テスト
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestJobsAPI:
    """求人API統合テストクラス"""

    @pytest.mark.asyncio
    async def test_search_jobs_basic(self, async_client: AsyncClient):
        """基本的な求人検索テスト"""
        response = await async_client.get("/api/v1/jobs/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # レスポンス構造の確認
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "has_next" in data
        assert "has_prev" in data

        # ページネーション情報の確認
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["has_prev"] is False

    @pytest.mark.asyncio
    async def test_search_jobs_with_filters(self, async_client: AsyncClient):
        """フィルター付き求人検索テスト"""
        params = {
            "keyword": "エンジニア",
            "prefecture_codes": "13,14",
            "min_salary": 1200,
            "salary_type": "hourly",
            "page": 1,
            "size": 10
        }

        response = await async_client.get("/api/v1/jobs/", params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # フィルター適用の確認
        assert data["size"] == 10
        assert "filters_applied" in data

    @pytest.mark.asyncio
    async def test_search_jobs_invalid_params(self, async_client: AsyncClient):
        """無効なパラメータでの求人検索テスト"""
        params = {
            "page": 0,  # 無効なページ番号
            "size": 200  # 最大サイズを超える
        }

        response = await async_client.get("/api/v1/jobs/", params=params)

        # バリデーションエラーが期待される
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, async_client: AsyncClient):
        """存在しない求人の取得テスト"""
        response = await async_client.get("/api/v1/jobs/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_job_success(self, async_client: AsyncClient, sample_job_data):
        """求人作成成功テスト"""
        response = await async_client.post("/api/v1/jobs/", json=sample_job_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # 作成された求人のデータ確認
        assert "job_id" in data
        assert data["company_name"] == sample_job_data["company_name"]
        assert data["application_name"] == sample_job_data["application_name"]

    @pytest.mark.asyncio
    async def test_create_job_invalid_data(self, async_client: AsyncClient):
        """無効なデータでの求人作成テスト"""
        invalid_data = {
            "company_name": "",  # 空の会社名
            "application_name": "テスト求人",
            # 必須フィールドが不足
        }

        response = await async_client.post("/api/v1/jobs/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_job_success(self, async_client: AsyncClient, sample_job_data):
        """求人更新成功テスト"""
        # まず求人を作成
        create_response = await async_client.post("/api/v1/jobs/", json=sample_job_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        job_id = create_response.json()["job_id"]

        # 求人を更新
        update_data = {
            "company_name": "更新されたテスト株式会社",
            "application_name": "更新されたテスト求人"
        }

        response = await async_client.put(f"/api/v1/jobs/{job_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["company_name"] == update_data["company_name"]
        assert data["application_name"] == update_data["application_name"]

    @pytest.mark.asyncio
    async def test_activate_deactivate_job(self, async_client: AsyncClient, sample_job_data):
        """求人有効化・無効化テスト"""
        # 求人作成
        create_response = await async_client.post("/api/v1/jobs/", json=sample_job_data)
        job_id = create_response.json()["job_id"]

        # 無効化
        response = await async_client.post(f"/api/v1/jobs/{job_id}/deactivate")
        assert response.status_code == status.HTTP_200_OK

        # 有効化
        response = await async_client.post(f"/api/v1/jobs/{job_id}/activate")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_job_recommendations(self, async_client: AsyncClient, sample_job_data):
        """求人推薦取得テスト"""
        # 求人作成
        create_response = await async_client.post("/api/v1/jobs/", json=sample_job_data)
        job_id = create_response.json()["job_id"]

        # 推薦取得
        response = await async_client.get(f"/api/v1/jobs/{job_id}/recommendations")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_bulk_job_operations(self, async_client: AsyncClient, sample_job_data):
        """求人一括操作テスト"""
        # 複数の求人を作成
        job_ids = []
        for i in range(3):
            job_data = sample_job_data.copy()
            job_data["application_name"] = f"テスト求人{i+1}"
            response = await async_client.post("/api/v1/jobs/", json=job_data)
            job_ids.append(response.json()["job_id"])

        # 一括無効化
        bulk_operation = {
            "job_ids": job_ids,
            "operation": "deactivate"
        }

        response = await async_client.post("/api/v1/jobs/bulk-operations", json=bulk_operation)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success_count"] == 3
        assert data["error_count"] == 0

    @pytest.mark.asyncio
    async def test_job_stats_summary(self, async_client: AsyncClient):
        """求人統計サマリーテスト"""
        response = await async_client.get("/api/v1/jobs/stats/summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 統計項目の確認
        expected_keys = [
            "total_jobs", "active_jobs", "new_jobs_7d",
            "new_jobs_30d", "unique_companies"
        ]
        for key in expected_keys:
            assert key in data

    @pytest.mark.asyncio
    async def test_concurrent_job_creation(self, async_client: AsyncClient, sample_job_data):
        """並行求人作成テスト"""
        import asyncio

        # 同時に複数の求人を作成
        tasks = []
        for i in range(5):
            job_data = sample_job_data.copy()
            job_data["application_name"] = f"並行テスト求人{i+1}"
            job_data["endcl_cd"] = f"TEST{i+1:03d}"
            tasks.append(async_client.post("/api/v1/jobs/", json=job_data))

        responses = await asyncio.gather(*tasks)

        # すべての作成が成功することを確認
        for response in responses:
            assert response.status_code == status.HTTP_201_CREATED

        # 重複がないことを確認
        job_ids = [resp.json()["job_id"] for resp in responses]
        assert len(set(job_ids)) == len(job_ids)  # 重複なし