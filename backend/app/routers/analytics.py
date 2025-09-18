"""
分析関連APIエンドポイント

KPI、メトリクス、レポート生成などのAPIを提供
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.models.analytics import (
    DashboardKPIs, TimeSeriesMetric, CategoryPerformance, LocationPerformance,
    CompanyPerformance, UserSegmentAnalysis, ConversionFunnel, ABTestResult,
    PredictiveAnalytics, ReportRequest, AnalyticsReport, RealTimeMetrics,
    AlertConfig, TimeGranularity
)
from app.models.common import BaseResponse
from app.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/dashboard", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    granularity: TimeGranularity = Query(TimeGranularity.DAY, description="時間粒度"),
    compare_previous: bool = Query(True, description="前期比較"),
    db: AsyncSession = Depends(get_db)
):
    """
    ダッシュボードKPI取得

    指定期間のKPIダッシュボードデータを取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        kpis = await analytics_service.get_dashboard_kpis(
            period_start=period_start,
            period_end=period_end,
            granularity=granularity,
            compare_previous=compare_previous
        )
        return kpis

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ダッシュボードKPI取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/timeseries/{metric_name}", response_model=TimeSeriesMetric)
async def get_timeseries_metric(
    metric_name: str = Path(..., description="メトリクス名"),
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    granularity: TimeGranularity = Query(TimeGranularity.DAY, description="時間粒度"),
    filters: Optional[str] = Query(None, description="フィルター条件（JSON）"),
    db: AsyncSession = Depends(get_db)
):
    """
    時系列メトリクス取得

    指定されたメトリクスの時系列データを取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        metric = await analytics_service.get_timeseries_metric(
            metric_name=metric_name,
            period_start=period_start,
            period_end=period_end,
            granularity=granularity,
            filters=filters
        )

        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたメトリクスが見つかりません"
            )

        return metric

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"時系列メトリクス取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/performance/categories", response_model=List[CategoryPerformance])
async def get_category_performance(
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    top_n: int = Query(50, ge=1, le=1000, description="上位N件"),
    sort_by: str = Query("application_count", description="ソート項目"),
    db: AsyncSession = Depends(get_db)
):
    """
    カテゴリ別パフォーマンス取得

    職種カテゴリ別のパフォーマンス分析結果を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        performance = await analytics_service.get_category_performance(
            period_start=period_start,
            period_end=period_end,
            top_n=top_n,
            sort_by=sort_by
        )
        return performance

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"カテゴリパフォーマンス取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/performance/locations", response_model=List[LocationPerformance])
async def get_location_performance(
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    level: str = Query("prefecture", description="地域レベル（prefecture/city）"),
    top_n: int = Query(50, ge=1, le=1000, description="上位N件"),
    db: AsyncSession = Depends(get_db)
):
    """
    地域別パフォーマンス取得

    都道府県・市区町村別のパフォーマンス分析結果を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        performance = await analytics_service.get_location_performance(
            period_start=period_start,
            period_end=period_end,
            level=level,
            top_n=top_n
        )
        return performance

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"地域パフォーマンス取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/performance/companies", response_model=List[CompanyPerformance])
async def get_company_performance(
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    top_n: int = Query(100, ge=1, le=1000, description="上位N件"),
    sort_by: str = Query("total_applications", description="ソート項目"),
    db: AsyncSession = Depends(get_db)
):
    """
    企業別パフォーマンス取得

    企業別のパフォーマンス分析結果を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        performance = await analytics_service.get_company_performance(
            period_start=period_start,
            period_end=period_end,
            top_n=top_n,
            sort_by=sort_by
        )
        return performance

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"企業パフォーマンス取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/segments", response_model=List[UserSegmentAnalysis])
async def get_user_segments(
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    segment_type: Optional[str] = Query(None, description="セグメントタイプ"),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーセグメント分析

    ユーザーセグメント別の分析結果を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        segments = await analytics_service.get_user_segments(
            period_start=period_start,
            period_end=period_end,
            segment_type=segment_type
        )
        return segments

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザーセグメント分析中にエラーが発生しました: {str(e)}"
        )


@router.get("/funnel/{funnel_name}", response_model=ConversionFunnel)
async def get_conversion_funnel(
    funnel_name: str = Path(..., description="ファネル名"),
    period_start: str = Query(..., description="期間開始（YYYY-MM-DD）"),
    period_end: str = Query(..., description="期間終了（YYYY-MM-DD）"),
    segment_filters: Optional[str] = Query(None, description="セグメントフィルター（JSON）"),
    db: AsyncSession = Depends(get_db)
):
    """
    コンバージョンファネル分析

    指定されたファネルの分析結果を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        funnel = await analytics_service.get_conversion_funnel(
            funnel_name=funnel_name,
            period_start=period_start,
            period_end=period_end,
            segment_filters=segment_filters
        )

        if not funnel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたファネルが見つかりません"
            )

        return funnel

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"コンバージョンファネル分析中にエラーが発生しました: {str(e)}"
        )


@router.get("/ab-tests", response_model=List[ABTestResult])
async def get_ab_test_results(
    active_only: bool = Query(False, description="アクティブなテストのみ"),
    test_ids: Optional[str] = Query(None, description="テストID（カンマ区切り）"),
    db: AsyncSession = Depends(get_db)
):
    """
    A/Bテスト結果取得

    A/Bテストの結果を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        results = await analytics_service.get_ab_test_results(
            active_only=active_only,
            test_ids=test_ids.split(',') if test_ids else None
        )
        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A/Bテスト結果取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/predictions/{prediction_type}", response_model=PredictiveAnalytics)
async def get_predictive_analytics(
    prediction_type: str = Path(..., description="予測タイプ"),
    horizon_days: int = Query(30, ge=1, le=365, description="予測期間（日）"),
    confidence_level: float = Query(0.95, ge=0.8, le=0.99, description="信頼度"),
    db: AsyncSession = Depends(get_db)
):
    """
    予測分析取得

    指定されたタイプの予測分析結果を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        predictions = await analytics_service.get_predictive_analytics(
            prediction_type=prediction_type,
            horizon_days=horizon_days,
            confidence_level=confidence_level
        )

        if not predictions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された予測分析が見つかりません"
            )

        return predictions

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"予測分析取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/reports/generate", response_model=AnalyticsReport)
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    レポート生成

    指定された条件でカスタム分析レポートを生成します。
    """
    try:
        analytics_service = AnalyticsService(db)
        report = await analytics_service.generate_report(request)
        return report

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"レポート生成中にエラーが発生しました: {str(e)}"
        )


@router.get("/reports/{report_id}", response_model=AnalyticsReport)
async def get_report(
    report_id: str = Path(..., description="レポートID"),
    db: AsyncSession = Depends(get_db)
):
    """
    レポート取得

    指定されたIDのレポートを取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        report = await analytics_service.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたレポートが見つかりません"
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"レポート取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/realtime", response_model=RealTimeMetrics)
async def get_realtime_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    リアルタイムメトリクス取得

    現在のシステム状況のリアルタイムメトリクスを取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        metrics = await analytics_service.get_realtime_metrics()
        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"リアルタイムメトリクス取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/alerts", response_model=List[AlertConfig])
async def get_alerts(
    active_only: bool = Query(True, description="アクティブなアラートのみ"),
    db: AsyncSession = Depends(get_db)
):
    """
    アラート設定取得

    アラート設定の一覧を取得します。
    """
    try:
        analytics_service = AnalyticsService(db)
        alerts = await analytics_service.get_alerts(active_only)
        return alerts

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アラート設定取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/alerts", response_model=AlertConfig)
async def create_alert(
    alert: AlertConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    アラート作成

    新しいアラート設定を作成します。
    """
    try:
        analytics_service = AnalyticsService(db)
        created_alert = await analytics_service.create_alert(alert)
        return created_alert

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アラート作成中にエラーが発生しました: {str(e)}"
        )