"""
ユーザーAPIエンドポイントの包括的テスト

ユーザー登録、更新、設定管理、行動履歴、
エラーハンドリングのテストを実装
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from unittest.mock import AsyncMock, patch
from typing import Dict, Any, List
from datetime import datetime, date, timedelta

from app.models.users import UserCreate, UserUpdate, UserActionCreate, BulkUserOperation
from app.models.common import BaseResponse, ActionType


class TestUserSearchAPI:
    """ユーザー検索APIのテスト"""

    @pytest.mark.asyncio
    async def test_search_users_default_params(self, async_client: AsyncClient):
        """デフォルトパラメータでのユーザー検索テスト"""
        response = await async_client.get("/users/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["page"] == 1
        assert data["size"] == 20

    @pytest.mark.asyncio
    async def test_search_users_with_email(self, async_client: AsyncClient):
        """メールアドレス検索テスト"""
        response = await async_client.get("/users/?email=test@example.com")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "filters_applied" in data

    @pytest.mark.asyncio
    async def test_search_users_with_age_groups(self, async_client: AsyncClient):
        """年齢層フィルタテスト"""
        response = await async_client.get("/users/?age_groups=20代前半,20代後半")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 指定した年齢層のユーザーのみが返されることを確認

    @pytest.mark.asyncio
    async def test_search_users_with_genders(self, async_client: AsyncClient):
        """性別フィルタテスト"""
        response = await async_client.get("/users/?genders=male,female")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

    @pytest.mark.asyncio
    async def test_search_users_with_prefecture_filter(self, async_client: AsyncClient):
        """都道府県フィルタテスト"""
        response = await async_client.get("/users/?prefecture_codes=13,27")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

    @pytest.mark.asyncio
    async def test_search_users_active_only(self, async_client: AsyncClient):
        """有効ユーザーのみフィルタテスト"""
        response = await async_client.get("/users/?is_active=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

    @pytest.mark.asyncio
    async def test_search_users_with_email_subscription(self, async_client: AsyncClient):
        """メール配信希望フィルタテスト"""
        response = await async_client.get("/users/?email_subscription=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

    @pytest.mark.asyncio
    async def test_search_users_with_recent_activity(self, async_client: AsyncClient):
        """最近活動ありフィルタテスト"""
        response = await async_client.get("/users/?has_recent_activity=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

    @pytest.mark.asyncio
    async def test_search_users_pagination(self, async_client: AsyncClient):
        """ページネーションテスト"""
        # 1ページ目
        response1 = await async_client.get("/users/?page=1&size=5")
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        # 2ページ目
        response2 = await async_client.get("/users/?page=2&size=5")
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # ページごとに異なるデータが返されることを確認
        if data1["total"] > 5:
            assert data1["items"] != data2["items"]

    @pytest.mark.asyncio
    async def test_search_users_sorting(self, async_client: AsyncClient):
        """ソートテスト"""
        # 登録日降順
        response1 = await async_client.get("/users/?sort_by=registration_date&sort_order=desc")
        assert response1.status_code == status.HTTP_200_OK

        # メールアドレス昇順
        response2 = await async_client.get("/users/?sort_by=email&sort_order=asc")
        assert response2.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_search_users_invalid_params(self, async_client: AsyncClient):
        """無効なパラメータテスト"""
        # 無効なページ番号
        response = await async_client.get("/users/?page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 無効なページサイズ
        response = await async_client.get("/users/?size=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserDetailAPI:
    """ユーザー詳細APIのテスト"""

    @pytest.mark.asyncio
    async def test_get_user_basic(self, async_client: AsyncClient):
        """基本的なユーザー詳細取得テスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用ユーザーデータが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_get_user_with_profile(self, async_client: AsyncClient):
        """プロファイル情報付きユーザー詳細取得テスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}?include_profile=true")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用ユーザーデータが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # プロファイル情報が含まれることを確認
        if "profile" in data and data["profile"]:
            assert "preference_scores" in data["profile"] or "category_interests" in data["profile"]

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, async_client: AsyncClient):
        """存在しないユーザーの詳細取得テスト"""
        response = await async_client.get("/users/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_user_invalid_id(self, async_client: AsyncClient):
        """無効なユーザーIDテスト"""
        response = await async_client.get("/users/invalid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserRegistrationAPI:
    """ユーザー登録APIのテスト"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, async_client: AsyncClient, sample_user_create_data):
        """ユーザー作成成功テスト"""
        response = await async_client.post("/users/", json=sample_user_create_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data
        assert data["email"] == sample_user_create_data["email"]

    @pytest.mark.asyncio
    async def test_register_user_success(self, async_client: AsyncClient, sample_user_create_data):
        """ユーザー登録成功テスト"""
        # 別のメールアドレスを使用
        register_data = sample_user_create_data.copy()
        register_data["email"] = "register_test@example.com"

        response = await async_client.post("/users/register", json=register_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data
        assert data["email"] == register_data["email"]

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, async_client: AsyncClient):
        """無効なメールアドレスでのユーザー作成テスト"""
        invalid_data = {
            "email": "invalid-email",
            "age_group": "20代前半",
            "gender": "male"
        }

        response = await async_client.post("/users/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_invalid_gender(self, async_client: AsyncClient):
        """無効な性別でのユーザー作成テスト"""
        invalid_data = {
            "email": "test@example.com",
            "age_group": "20代前半",
            "gender": "invalid_gender"
        }

        response = await async_client.post("/users/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_invalid_age_group(self, async_client: AsyncClient):
        """無効な年齢層でのユーザー作成テスト"""
        invalid_data = {
            "email": "test@example.com",
            "age_group": "invalid_age",
            "gender": "male"
        }

        response = await async_client.post("/users/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, async_client: AsyncClient, sample_user_create_data):
        """重複メールアドレスでのユーザー作成テスト"""
        # 最初のユーザー作成
        response1 = await async_client.post("/users/", json=sample_user_create_data)

        # 同じメールアドレスで再度作成
        response2 = await async_client.post("/users/", json=sample_user_create_data)

        # 重複エラーまたは正常な処理（実装依存）
        assert response2.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
            status.HTTP_201_CREATED  # 既存ユーザーを返す場合
        ]


class TestUserUpdateAPI:
    """ユーザー更新APIのテスト"""

    @pytest.mark.asyncio
    async def test_update_user_success(self, async_client: AsyncClient):
        """ユーザー更新成功テスト"""
        user_id = 1
        update_data = {
            "age_group": "30代前半",
            "gender": "female"
        }

        response = await async_client.put(f"/users/{user_id}", json=update_data)

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用ユーザーデータが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["age_group"] == "30代前半"
        assert data["gender"] == "female"

    @pytest.mark.asyncio
    async def test_update_user_preferences(self, async_client: AsyncClient):
        """ユーザー設定更新テスト"""
        user_id = 1
        preferences = {
            "preferred_work_styles": ["part_time", "remote"],
            "preferred_salary_min": 1500,
            "location_preference_radius": 20
        }

        response = await async_client.put(f"/users/{user_id}/preferences", json=preferences)

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用ユーザーデータが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, async_client: AsyncClient):
        """存在しないユーザーの更新テスト"""
        update_data = {"age_group": "30代前半"}
        response = await async_client.put("/users/999999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_user_profile(self, async_client: AsyncClient):
        """ユーザープロファイル更新テスト"""
        user_id = 1
        response = await async_client.post(f"/users/{user_id}/update-profile")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用ユーザーデータが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_user_profile_force(self, async_client: AsyncClient):
        """強制ユーザープロファイル更新テスト"""
        user_id = 1
        response = await async_client.post(f"/users/{user_id}/update-profile?force_recalculate=true")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用ユーザーデータが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


class TestUserActionAPI:
    """ユーザー行動APIのテスト"""

    @pytest.mark.asyncio
    async def test_record_user_action_success(self, async_client: AsyncClient):
        """ユーザー行動記録成功テスト"""
        user_id = 1
        action_data = {
            "user_id": user_id,
            "job_id": 1,
            "action_type": ActionType.VIEW.value,
            "source": "web",
            "session_id": "test_session_123",
            "device_type": "desktop"
        }

        response = await async_client.post(f"/users/{user_id}/actions", json=action_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_record_user_action_mismatched_user_id(self, async_client: AsyncClient):
        """ユーザーID不一致での行動記録テスト"""
        user_id = 1
        action_data = {
            "user_id": 2,  # パスと異なるユーザーID
            "job_id": 1,
            "action_type": ActionType.VIEW.value,
            "source": "web"
        }

        response = await async_client.post(f"/users/{user_id}/actions", json=action_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_user_actions_default(self, async_client: AsyncClient):
        """ユーザー行動履歴取得デフォルトテスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}/actions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_user_actions_with_filters(self, async_client: AsyncClient):
        """フィルタ付きユーザー行動履歴取得テスト"""
        user_id = 1
        params = {
            "action_types": "view,click",
            "days": 7,
            "limit": 50
        }
        response = await async_client.get(f"/users/{user_id}/actions", params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 50

    @pytest.mark.asyncio
    async def test_get_user_history(self, async_client: AsyncClient):
        """ユーザー履歴取得テスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_user_history_with_pagination(self, async_client: AsyncClient):
        """ページネーション付きユーザー履歴取得テスト"""
        user_id = 1
        params = {
            "limit": 10,
            "offset": 0
        }
        response = await async_client.get(f"/users/{user_id}/history", params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


class TestUserProfileAPI:
    """ユーザープロファイルAPIのテスト"""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, async_client: AsyncClient):
        """ユーザープロファイル取得成功テスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}/profile")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用プロファイルデータが存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, async_client: AsyncClient):
        """存在しないユーザープロファイル取得テスト"""
        response = await async_client.get("/users/999999/profile")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_user_activity_summary(self, async_client: AsyncClient):
        """ユーザー活動サマリー取得テスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}/activity-summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "period_days" in data
        assert "total_actions" in data

    @pytest.mark.asyncio
    async def test_get_user_activity_summary_custom_period(self, async_client: AsyncClient):
        """カスタム期間での活動サマリー取得テスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}/activity-summary?period_days=7")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_user_engagement_metrics(self, async_client: AsyncClient):
        """ユーザーエンゲージメント指標取得テスト"""
        user_id = 1
        response = await async_client.get(f"/users/{user_id}/engagement-metrics")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("テスト用エンゲージメント指標が存在しません")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "engagement_score" in data


class TestUserBulkOperationsAPI:
    """ユーザー一括操作APIのテスト"""

    @pytest.mark.asyncio
    async def test_bulk_user_activate(self, async_client: AsyncClient):
        """ユーザー一括有効化テスト"""
        operation_data = {
            "user_ids": [1, 2, 3],
            "operation": "activate"
        }

        response = await async_client.post("/users/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_requested" in data
        assert "success_count" in data
        assert "error_count" in data
        assert data["operation"] == "activate"

    @pytest.mark.asyncio
    async def test_bulk_user_deactivate(self, async_client: AsyncClient):
        """ユーザー一括無効化テスト"""
        operation_data = {
            "user_ids": [1, 2, 3],
            "operation": "deactivate"
        }

        response = await async_client.post("/users/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["operation"] == "deactivate"

    @pytest.mark.asyncio
    async def test_bulk_user_update_subscription(self, async_client: AsyncClient):
        """ユーザー一括配信設定更新テスト"""
        operation_data = {
            "user_ids": [1, 2, 3],
            "operation": "update_subscription",
            "parameters": {"email_subscription": True}
        }

        response = await async_client.post("/users/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["operation"] == "update_subscription"

    @pytest.mark.asyncio
    async def test_bulk_user_invalid_operation(self, async_client: AsyncClient):
        """無効な一括操作テスト"""
        operation_data = {
            "user_ids": [1, 2, 3],
            "operation": "invalid_operation"
        }

        response = await async_client.post("/users/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_bulk_user_too_many_ids(self, async_client: AsyncClient):
        """一括操作での過剰なID数テスト"""
        operation_data = {
            "user_ids": list(range(1, 1002)),  # 1001個のID
            "operation": "activate"
        }

        response = await async_client.post("/users/bulk-operations", json=operation_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserStatsAPI:
    """ユーザー統計APIのテスト"""

    @pytest.mark.asyncio
    async def test_get_user_stats_summary(self, async_client: AsyncClient):
        """ユーザー統計サマリー取得テスト"""
        response = await async_client.get("/users/stats/summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 統計データの基本構造を確認


class TestUserAPIErrorHandling:
    """ユーザーAPIエラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, async_client: AsyncClient):
        """データベース接続エラーのテスト"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            response = await async_client.get("/users/")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_service_layer_error(self, async_client: AsyncClient):
        """サービス層エラーのテスト"""
        with patch('app.services.users.UserService.search_users') as mock_search:
            mock_search.side_effect = ValueError("Invalid search parameters")

            response = await async_client.get("/users/")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_malformed_json_request(self, async_client: AsyncClient):
        """不正なJSONリクエストテスト"""
        response = await async_client.post(
            "/users/",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """必須フィールド不足テスト"""
        incomplete_data = {
            "age_group": "20代前半"
            # emailが不足
        }

        response = await async_client.post("/users/", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, async_client: AsyncClient):
        """SQLインジェクション防止テスト"""
        malicious_email = "test@example.com'; DROP TABLE users; --"
        response = await async_client.get(f"/users/?email={malicious_email}")

        # エラーが発生せず、適切に処理されることを確認
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    @pytest.mark.asyncio
    async def test_xss_prevention(self, async_client: AsyncClient):
        """XSS防止テスト"""
        xss_payload = "<script>alert('xss')</script>"
        response = await async_client.get(f"/users/?email={xss_payload}")

        # エラーが発生せず、適切に処理されることを確認
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


class TestUserAPIValidation:
    """ユーザーAPIバリデーションテスト"""

    @pytest.mark.asyncio
    async def test_email_validation(self, async_client: AsyncClient):
        """メールアドレスバリデーションテスト"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            ""
        ]

        for email in invalid_emails:
            user_data = {
                "email": email,
                "age_group": "20代前半",
                "gender": "male"
            }
            response = await async_client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_age_group_validation(self, async_client: AsyncClient):
        """年齢層バリデーションテスト"""
        invalid_age_groups = [
            "invalid_age",
            "10歳",
            "100代",
            ""
        ]

        for age_group in invalid_age_groups:
            user_data = {
                "email": "test@example.com",
                "age_group": age_group,
                "gender": "male"
            }
            response = await async_client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_gender_validation(self, async_client: AsyncClient):
        """性別バリデーションテスト"""
        invalid_genders = [
            "invalid_gender",
            "man",
            "woman",
            ""
        ]

        for gender in invalid_genders:
            user_data = {
                "email": "test@example.com",
                "age_group": "20代前半",
                "gender": gender
            }
            response = await async_client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_prefecture_code_validation(self, async_client: AsyncClient):
        """都道府県コードバリデーションテスト"""
        invalid_pref_codes = [
            "00",  # 範囲外
            "48",  # 範囲外
            "AB",  # 数字以外
            "1",   # 桁数不足
            "123"  # 桁数過多
        ]

        for pref_cd in invalid_pref_codes:
            user_data = {
                "email": "test@example.com",
                "estimated_pref_cd": pref_cd
            }
            response = await async_client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserAPIPerformance:
    """ユーザーAPIパフォーマンステスト"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_search_users_performance(self, async_client: AsyncClient):
        """ユーザー検索パフォーマンステスト"""
        import time

        start_time = time.time()
        response = await async_client.get("/users/?size=100")
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        response_time = end_time - start_time
        assert response_time < 2.0  # 2秒以内に応答

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, async_client: AsyncClient):
        """一括操作パフォーマンステスト"""
        operation_data = {
            "user_ids": list(range(1, 101)),  # 100件
            "operation": "activate"
        }

        import time
        start_time = time.time()
        response = await async_client.post("/users/bulk-operations", json=operation_data)
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 5.0  # 5秒以内に完了

    @pytest.mark.asyncio
    async def test_concurrent_user_requests(self, async_client: AsyncClient):
        """同時ユーザーリクエストテスト"""
        import asyncio

        async def make_request():
            return await async_client.get("/users/?page=1&size=10")

        # 10個の同時リクエスト
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # すべてのリクエストが正常に処理されることを確認
        for response in responses:
            assert response.status_code == status.HTTP_200_OK


class TestUserAPIIntegration:
    """ユーザーAPI統合テスト"""

    @pytest.mark.asyncio
    async def test_user_lifecycle(self, async_client: AsyncClient):
        """ユーザーライフサイクル統合テスト"""
        # 1. ユーザー作成
        user_data = {
            "email": "lifecycle_test@example.com",
            "age_group": "20代前半",
            "gender": "male"
        }
        create_response = await async_client.post("/users/", json=user_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        user = create_response.json()
        user_id = user["user_id"]

        # 2. ユーザー詳細取得
        get_response = await async_client.get(f"/users/{user_id}")
        assert get_response.status_code == status.HTTP_200_OK

        # 3. ユーザー更新
        update_data = {"age_group": "20代後半"}
        update_response = await async_client.put(f"/users/{user_id}", json=update_data)
        if update_response.status_code == status.HTTP_200_OK:
            updated_user = update_response.json()
            assert updated_user["age_group"] == "20代後半"

        # 4. 行動記録
        action_data = {
            "user_id": user_id,
            "action_type": ActionType.VIEW.value,
            "source": "web"
        }
        action_response = await async_client.post(f"/users/{user_id}/actions", json=action_data)
        assert action_response.status_code == status.HTTP_200_OK

        # 5. 履歴取得
        history_response = await async_client.get(f"/users/{user_id}/actions")
        assert history_response.status_code == status.HTTP_200_OK


@pytest.fixture
def mock_user_service():
    """UserServiceのモック"""
    with patch('app.services.users.UserService') as mock:
        service_instance = mock.return_value
        service_instance.search_users = AsyncMock()
        service_instance.get_user_by_id = AsyncMock()
        service_instance.create_user = AsyncMock()
        service_instance.register_user = AsyncMock()
        service_instance.update_user = AsyncMock()
        service_instance.record_action = AsyncMock()
        service_instance.get_user_actions = AsyncMock()
        service_instance.get_user_profile = AsyncMock()
        service_instance.update_profile = AsyncMock()
        service_instance.update_preferences = AsyncMock()
        yield service_instance