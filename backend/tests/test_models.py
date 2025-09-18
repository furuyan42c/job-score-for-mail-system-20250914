"""
Pydanticモデルの包括的バリデーションテスト

全データモデルのバリデーション、シリアライゼーション、
エッジケースのテストを実装
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any

from app.models.common import (
    BaseResponse, ErrorResponse, PaginationParams, PaginatedResponse,
    ScoreRange, DateRange, SalaryRange, ContactInfo, APIKey, HealthCheck,
    SalaryType, JobStatus, ActionType, EmploymentType, Constants
)
from app.models.jobs import (
    JobFeatures, JobSalary, JobWorkConditions, JobCategory, JobSEO,
    JobScoring, JobStats, JobBase, JobCreate, JobUpdate, Job, JobListItem,
    JobSearchFilters, JobSearchSort, JobSearchRequest, JobRecommendation,
    BulkJobOperation, BulkJobResult
)
from app.models.users import (
    UserPreferences, UserBehaviorStats, UserProfile, UserBase, UserCreate,
    UserUpdate, User, UserListItem, UserAction, UserActionCreate,
    UserSearchFilters, UserSearchRequest, UserActivitySummary,
    UserRecommendationPreferences, UserEngagementMetrics, BulkUserOperation
)


class TestCommonModels:
    """共通モデルのテスト"""

    def test_base_response_creation(self):
        """BaseResponseの作成テスト"""
        response = BaseResponse()
        assert response.success is True
        assert response.message == "処理が完了しました"
        assert isinstance(response.timestamp, datetime)

    def test_error_response_creation(self):
        """ErrorResponseの作成テスト"""
        error = ErrorResponse(error="テストエラー")
        assert error.success is False
        assert error.error == "テストエラー"
        assert error.detail is None
        assert isinstance(error.timestamp, datetime)

    def test_pagination_params_validation(self):
        """PaginationParamsのバリデーションテスト"""
        # 正常ケース
        params = PaginationParams(page=2, size=50)
        assert params.page == 2
        assert params.size == 50
        assert params.offset == 50

        # デフォルト値
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 20
        assert params.offset == 0

        # 無効な値
        with pytest.raises(ValidationError):
            PaginationParams(page=0)  # page < 1

        with pytest.raises(ValidationError):
            PaginationParams(size=0)  # size < 1

        with pytest.raises(ValidationError):
            PaginationParams(size=101)  # size > 100

    def test_paginated_response_creation(self):
        """PaginatedResponseの作成テスト"""
        items = [{"id": 1}, {"id": 2}]
        response = PaginatedResponse.create(
            items=items, total=10, page=1, size=20
        )

        assert len(response.items) == 2
        assert response.total == 10
        assert response.page == 1
        assert response.size == 20
        assert response.total_pages == 1
        assert response.has_next is False
        assert response.has_prev is False

        # 複数ページの場合
        response = PaginatedResponse.create(
            items=items, total=50, page=2, size=20
        )
        assert response.total_pages == 3
        assert response.has_next is True
        assert response.has_prev is True

    def test_score_range_validation(self):
        """ScoreRangeのバリデーションテスト"""
        # 正常ケース
        score_range = ScoreRange(min_score=10.0, max_score=90.0)
        assert score_range.min_score == 10.0
        assert score_range.max_score == 90.0

        # 無効な範囲
        with pytest.raises(ValidationError):
            ScoreRange(min_score=90.0, max_score=10.0)

        # 境界値
        ScoreRange(min_score=0.0, max_score=100.0)  # 正常

        with pytest.raises(ValidationError):
            ScoreRange(min_score=-1.0)  # 範囲外

        with pytest.raises(ValidationError):
            ScoreRange(max_score=101.0)  # 範囲外

    def test_date_range_validation(self):
        """DateRangeのバリデーションテスト"""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        # 正常ケース
        date_range = DateRange(start_date=start, end_date=end)
        assert date_range.start_date == start
        assert date_range.end_date == end

        # 無効な範囲
        with pytest.raises(ValidationError):
            DateRange(start_date=end, end_date=start)

        # Noneの場合
        DateRange(start_date=None, end_date=None)  # 正常

    def test_salary_range_validation(self):
        """SalaryRangeのバリデーションテスト"""
        # 正常ケース
        salary_range = SalaryRange(
            min_salary=1000,
            max_salary=2000,
            salary_type=SalaryType.HOURLY
        )
        assert salary_range.min_salary == 1000
        assert salary_range.max_salary == 2000

        # 無効な範囲
        with pytest.raises(ValidationError):
            SalaryRange(min_salary=2000, max_salary=1000)

        # 負の値
        with pytest.raises(ValidationError):
            SalaryRange(min_salary=-100)

    def test_contact_info_validation(self):
        """ContactInfoのバリデーションテスト"""
        # 正常ケース
        contact = ContactInfo(
            email="test@example.com",
            phone="03-1234-5678",
            company_name="テスト株式会社"
        )
        assert contact.email == "test@example.com"

        # 無効なメール
        with pytest.raises(ValidationError):
            ContactInfo(email="invalid-email")

        # 無効な電話番号
        with pytest.raises(ValidationError):
            ContactInfo(email="test@example.com", phone="invalid-phone")

        # メールの大文字小文字正規化
        contact = ContactInfo(email="TEST@EXAMPLE.COM")
        assert contact.email == "test@example.com"

    def test_api_key_validation(self):
        """APIKeyのバリデーションテスト"""
        key = "a" * 32  # 32文字のキー
        api_key = APIKey(key=key, name="test-key")
        assert api_key.key == key

        # 短すぎるキー
        with pytest.raises(ValidationError):
            APIKey(key="short")

    def test_enum_values(self):
        """Enumの値テスト"""
        # SalaryType
        assert SalaryType.HOURLY == "hourly"
        assert SalaryType.DAILY == "daily"
        assert SalaryType.MONTHLY == "monthly"

        # ActionType
        assert ActionType.VIEW == "view"
        assert ActionType.CLICK == "click"
        assert ActionType.APPLY == "apply"

        # JobStatus
        assert JobStatus.ACTIVE == "active"
        assert JobStatus.INACTIVE == "inactive"

    def test_constants(self):
        """定数のテスト"""
        assert Constants.MAX_SCORE == 100.0
        assert Constants.MIN_SCORE == 0.0
        assert Constants.DEFAULT_PAGE_SIZE == 20
        assert "D01" in Constants.FEATURE_CODES


class TestJobModels:
    """求人モデルのテスト"""

    def test_job_features_validation(self, sample_job_features):
        """JobFeaturesのバリデーションテスト"""
        features = JobFeatures(**sample_job_features)
        assert "D01" in features.feature_codes
        assert features.has_daily_payment is True

        # 無効な特徴コード
        invalid_features = sample_job_features.copy()
        invalid_features["feature_codes"] = ["INVALID"]
        with pytest.raises(ValidationError):
            JobFeatures(**invalid_features)

    def test_job_salary_validation(self, sample_job_salary):
        """JobSalaryのバリデーションテスト"""
        salary = JobSalary(**sample_job_salary)
        assert salary.min_salary == 1200
        assert salary.max_salary == 1500
        assert salary.fee == 1000

        # 給与表示テスト
        assert "1,200～1,500円/時" in salary.salary_display

        # 無効な給与範囲
        invalid_salary = sample_job_salary.copy()
        invalid_salary["min_salary"] = 2000
        invalid_salary["max_salary"] = 1000
        with pytest.raises(ValidationError):
            JobSalary(**invalid_salary)

        # 無効な手数料
        invalid_salary = sample_job_salary.copy()
        invalid_salary["fee"] = 100  # 最小値未満
        with pytest.raises(ValidationError):
            JobSalary(**invalid_salary)

    def test_job_work_conditions_validation(self):
        """JobWorkConditionsのバリデーションテスト"""
        conditions = JobWorkConditions(
            hours="9:00-18:00",
            work_days="月-金",
            employment_type_cd=1
        )
        assert conditions.hours == "9:00-18:00"

    def test_job_category_validation(self):
        """JobCategoryのバリデーションテスト"""
        category = JobCategory(
            occupation_cd1=100,
            occupation_cd2=101,
            occupation_name="営業"
        )
        assert category.occupation_cd1 == 100

    def test_job_seo_validation(self):
        """JobSEOのバリデーションテスト"""
        seo = JobSEO(
            search_keywords=["営業", "未経験"],
            description="営業職の求人です"
        )
        assert len(seo.search_keywords) == 2

    def test_job_scoring_validation(self):
        """JobScoringのバリデーションテスト"""
        scoring = JobScoring(
            basic_score=75.5,
            seo_score=82.3,
            composite_score=78.9
        )
        assert scoring.basic_score == 75.5

        # スコア範囲外
        with pytest.raises(ValidationError):
            JobScoring(basic_score=150.0)

    def test_job_base_validation(self, sample_job_data):
        """JobBaseのバリデーションテスト"""
        job = JobBase(**sample_job_data)
        assert job.endcl_cd == "TEST001"
        assert job.company_name == "テスト株式会社"

    def test_job_create_validation(self, sample_job_data):
        """JobCreateのバリデーションテスト"""
        job_create = JobCreate(**sample_job_data)
        assert isinstance(job_create, JobBase)

    def test_job_update_validation(self):
        """JobUpdateのバリデーションテスト"""
        update_data = {
            "company_name": "更新後の会社名",
            "is_active": False
        }
        job_update = JobUpdate(**update_data)
        assert job_update.company_name == "更新後の会社名"
        assert job_update.is_active is False

    def test_job_search_filters_validation(self):
        """JobSearchFiltersのバリデーションテスト"""
        filters = JobSearchFilters(
            keyword="営業",
            prefecture_codes=["13", "27"],
            min_score=60.0,
            within_radius_km=10
        )
        assert filters.keyword == "営業"
        assert len(filters.prefecture_codes) == 2

        # 無効な半径
        with pytest.raises(ValidationError):
            JobSearchFilters(within_radius_km=200)

    def test_job_search_sort_validation(self):
        """JobSearchSortのバリデーションテスト"""
        sort = JobSearchSort(sort_by="posting_date", sort_order="desc")
        assert sort.sort_by == "posting_date"

        # 無効なソート項目
        with pytest.raises(ValidationError):
            JobSearchSort(sort_by="invalid_field")

        # 無効なソート順序
        with pytest.raises(ValidationError):
            JobSearchSort(sort_order="invalid")

    def test_bulk_job_operation_validation(self):
        """BulkJobOperationのバリデーションテスト"""
        operation = BulkJobOperation(
            job_ids=[1, 2, 3],
            operation="activate"
        )
        assert len(operation.job_ids) == 3

        # 無効な操作
        with pytest.raises(ValidationError):
            BulkJobOperation(job_ids=[1], operation="invalid_operation")

        # IDリストが多すぎる
        with pytest.raises(ValidationError):
            BulkJobOperation(
                job_ids=list(range(1001)),
                operation="activate"
            )


class TestUserModels:
    """ユーザーモデルのテスト"""

    def test_user_preferences_validation(self):
        """UserPreferencesのバリデーションテスト"""
        preferences = UserPreferences(
            preferred_work_styles=["part_time"],
            preferred_categories=[100, 200],
            preferred_salary_min=1200,
            location_preference_radius=15
        )
        assert len(preferences.preferred_work_styles) == 1
        assert preferences.location_preference_radius == 15

        # 無効な半径
        with pytest.raises(ValidationError):
            UserPreferences(location_preference_radius=200)

    def test_user_behavior_stats_validation(self):
        """UserBehaviorStatsのバリデーションテスト"""
        stats = UserBehaviorStats(
            application_count=5,
            click_count=25,
            view_count=100,
            last_application_date=date.today()
        )
        assert stats.application_count == 5

    def test_user_base_validation(self):
        """UserBaseのバリデーションテスト"""
        user = UserBase(
            email="test@example.com",
            age_group="20代前半",
            gender="male"
        )
        assert user.email == "test@example.com"

        # 無効なメール
        with pytest.raises(ValidationError):
            UserBase(email="invalid-email")

        # 無効な性別
        with pytest.raises(ValidationError):
            UserBase(email="test@example.com", gender="invalid")

        # 無効な年齢層
        with pytest.raises(ValidationError):
            UserBase(email="test@example.com", age_group="invalid")

        # メールの正規化
        user = UserBase(email="TEST@EXAMPLE.COM")
        assert user.email == "test@example.com"

    def test_user_create_validation(self, sample_user_create_data):
        """UserCreateのバリデーションテスト"""
        user_create = UserCreate(**sample_user_create_data)
        assert user_create.email == "test@example.com"
        assert user_create.preferences is not None

    def test_user_action_validation(self):
        """UserActionのバリデーションテスト"""
        action = UserAction(
            action_id=1,
            user_id=1,
            job_id=1,
            action_type=ActionType.VIEW,
            action_timestamp=datetime.now(),
            source="web"
        )
        assert action.action_type == ActionType.VIEW

    def test_user_action_create_validation(self):
        """UserActionCreateのバリデーションテスト"""
        action_create = UserActionCreate(
            user_id=1,
            job_id=1,
            action_type=ActionType.CLICK,
            source="mobile"
        )
        assert action_create.action_type == ActionType.CLICK

    def test_user_search_filters_validation(self):
        """UserSearchFiltersのバリデーションテスト"""
        filters = UserSearchFilters(
            email="test@example.com",
            age_groups=["20代前半", "20代後半"],
            min_application_count=1
        )
        assert len(filters.age_groups) == 2

        # 無効な最小応募数
        with pytest.raises(ValidationError):
            UserSearchFilters(min_application_count=-1)

    def test_user_recommendation_preferences_validation(self):
        """UserRecommendationPreferencesのバリデーションテスト"""
        prefs = UserRecommendationPreferences(
            user_id=1,
            recommendation_frequency="daily",
            max_daily_recommendations=40
        )
        assert prefs.recommendation_frequency == "daily"

        # 無効な頻度
        with pytest.raises(ValidationError):
            UserRecommendationPreferences(
                user_id=1,
                recommendation_frequency="invalid"
            )

        # 無効な推薦数
        with pytest.raises(ValidationError):
            UserRecommendationPreferences(
                user_id=1,
                max_daily_recommendations=200
            )

    def test_user_engagement_metrics_validation(self):
        """UserEngagementMetricsのバリデーションテスト"""
        metrics = UserEngagementMetrics(
            user_id=1,
            engagement_score=85.5,
            click_through_rate=0.15,
            application_rate=0.05
        )
        assert metrics.engagement_score == 85.5

        # スコア範囲外
        with pytest.raises(ValidationError):
            UserEngagementMetrics(user_id=1, engagement_score=150.0)

        # 率の範囲外
        with pytest.raises(ValidationError):
            UserEngagementMetrics(user_id=1, click_through_rate=1.5)

    def test_bulk_user_operation_validation(self):
        """BulkUserOperationのバリデーションテスト"""
        operation = BulkUserOperation(
            user_ids=[1, 2, 3],
            operation="activate"
        )
        assert len(operation.user_ids) == 3

        # 無効な操作
        with pytest.raises(ValidationError):
            BulkUserOperation(user_ids=[1], operation="invalid_operation")


class TestModelSerialization:
    """モデルシリアライゼーションのテスト"""

    def test_job_model_serialization(self, sample_job_data):
        """求人モデルのシリアライゼーションテスト"""
        job = JobBase(**sample_job_data)

        # JSON変換
        json_data = job.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["endcl_cd"] == "TEST001"

        # JSON文字列変換
        json_str = job.model_dump_json()
        assert isinstance(json_str, str)
        assert "TEST001" in json_str

        # デシリアライゼーション
        job_restored = JobBase.model_validate(json_data)
        assert job_restored.endcl_cd == job.endcl_cd

    def test_user_model_serialization(self, sample_user_create_data):
        """ユーザーモデルのシリアライゼーションテスト"""
        user = UserCreate(**sample_user_create_data)

        # JSON変換
        json_data = user.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["email"] == "test@example.com"

        # 復元
        user_restored = UserCreate.model_validate(json_data)
        assert user_restored.email == user.email

    def test_nested_model_serialization(self, sample_job_data):
        """ネストしたモデルのシリアライゼーションテスト"""
        job = JobBase(**sample_job_data)

        # ネストしたオブジェクトの確認
        json_data = job.model_dump()
        assert "location" in json_data
        assert "salary" in json_data
        assert isinstance(json_data["location"], dict)
        assert isinstance(json_data["salary"], dict)

    def test_model_exclude_fields(self, sample_job_data):
        """フィールド除外のテスト"""
        job = JobBase(**sample_job_data)

        # 特定フィールドを除外
        json_data = job.model_dump(exclude={"seo"})
        assert "seo" not in json_data
        assert "endcl_cd" in json_data

    def test_model_include_fields(self, sample_job_data):
        """フィールド包含のテスト"""
        job = JobBase(**sample_job_data)

        # 特定フィールドのみ包含
        json_data = job.model_dump(include={"endcl_cd", "company_name"})
        assert len(json_data) == 2
        assert "endcl_cd" in json_data
        assert "company_name" in json_data


class TestModelEdgeCases:
    """モデルのエッジケーステスト"""

    def test_empty_lists_and_dicts(self):
        """空のリストと辞書の処理テスト"""
        features = JobFeatures(
            feature_codes=[],
            has_daily_payment=False
        )
        assert len(features.feature_codes) == 0

        user_action = UserAction(
            action_id=1,
            user_id=1,
            action_type=ActionType.VIEW,
            action_timestamp=datetime.now(),
            action_metadata={}
        )
        assert len(user_action.action_metadata) == 0

    def test_null_optional_fields(self):
        """オプションフィールドのNull値テスト"""
        user = UserBase(email="test@example.com")
        assert user.age_group is None
        assert user.gender is None

        job_salary = JobSalary(
            salary_type=SalaryType.HOURLY,
            fee=1000
        )
        assert job_salary.min_salary is None
        assert job_salary.max_salary is None

    def test_boundary_values(self):
        """境界値のテスト"""
        # スコアの境界値
        score_range = ScoreRange(min_score=0.0, max_score=100.0)
        assert score_range.min_score == 0.0
        assert score_range.max_score == 100.0

        # ページサイズの境界値
        pagination = PaginationParams(page=1, size=100)
        assert pagination.size == 100

        # 給与の境界値
        salary = JobSalary(
            salary_type=SalaryType.HOURLY,
            min_salary=0,
            fee=500
        )
        assert salary.min_salary == 0

    def test_unicode_and_special_characters(self):
        """Unicode文字と特殊文字のテスト"""
        user = UserBase(
            email="テスト@example.com"  # 日本語を含むメール（無効）
        )
        # メールバリデーションで引っかかるはず
        with pytest.raises(ValidationError):
            user = UserBase(email="テスト@example.com")

        # 有効な日本語含有データ
        job = JobBase(
            endcl_cd="TEST001",
            company_name="株式会社テスト（東京）",
            application_name="営業職★未経験歓迎！",
            location={"prefecture_code": "13"},
            salary={"salary_type": "hourly", "fee": 1000},
            work_conditions={"employment_type_cd": 1},
            category={"occupation_cd1": 100}
        )
        assert "★" in job.application_name

    def test_very_long_strings(self):
        """非常に長い文字列のテスト"""
        long_string = "a" * 1000

        # 最大長制限のあるフィールド
        with pytest.raises(ValidationError):
            JobBase(
                endcl_cd=long_string,  # max_length=20を超える
                company_name="テスト",
                application_name="テスト",
                location={"prefecture_code": "13"},
                salary={"salary_type": "hourly", "fee": 1000},
                work_conditions={"employment_type_cd": 1},
                category={"occupation_cd1": 100}
            )

    def test_date_edge_cases(self):
        """日付のエッジケーステスト"""
        # 同じ日付
        date_range = DateRange(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1)
        )
        assert date_range.start_date == date_range.end_date

        # 遠い未来の日付
        future_date = date(9999, 12, 31)
        user_action = UserAction(
            action_id=1,
            user_id=1,
            action_type=ActionType.VIEW,
            action_timestamp=datetime.combine(future_date, datetime.min.time())
        )
        assert user_action.action_timestamp.date() == future_date

    def test_model_copy_and_update(self, sample_job_data):
        """モデルのコピーと更新テスト"""
        job = JobBase(**sample_job_data)

        # コピー作成
        job_copy = job.model_copy()
        assert job_copy.endcl_cd == job.endcl_cd
        assert job_copy is not job

        # 更新付きコピー
        job_updated = job.model_copy(update={"company_name": "更新後の会社"})
        assert job_updated.company_name == "更新後の会社"
        assert job_updated.endcl_cd == job.endcl_cd
        assert job.company_name != job_updated.company_name  # 元は変更されない