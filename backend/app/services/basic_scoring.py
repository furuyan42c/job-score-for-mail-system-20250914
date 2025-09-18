"""
T021: 基礎スコア計算実装
仕様書準拠の基本スコアリングエンジン

Requirements:
- fee > 500チェック
- 時給正規化（エリア統計使用）
- 企業人気度計算（360日データ）
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import numpy as np

from app.models.jobs import Job
from app.models.users import User

logger = logging.getLogger(__name__)

# スコアリング設定定数
VALID_EMPLOYMENT_TYPE_CDS = [1, 3, 6, 8]  # アルバイト・パート
MIN_FEE_THRESHOLD = 500  # 500円以下のfeeは除外


class BasicScoringEngine:
    """
    T021仕様準拠の基礎スコア計算エンジン
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._area_stats_cache = {}
        self._company_popularity_cache = {}

    async def calculate_basic_score(
        self,
        job: Job,
        area_stats: Optional[Dict[str, float]] = None,
        user_location: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        基礎スコアを0-100の範囲で計算

        Args:
            job: 求人情報
            area_stats: エリア統計データ
            user_location: ユーザー位置情報

        Returns:
            float: 0-100の基礎スコア
        """
        # Fee チェック - 500円以下はスコア0
        if hasattr(job, 'fee') and job.fee <= MIN_FEE_THRESHOLD:
            logger.info(f"Job {job.job_id} filtered: fee={job.fee} <= {MIN_FEE_THRESHOLD}")
            return 0.0

        # Employment type チェック
        if hasattr(job, 'employment_type_cd'):
            if job.employment_type_cd not in VALID_EMPLOYMENT_TYPE_CDS:
                logger.info(f"Job {job.job_id} filtered: invalid employment_type_cd={job.employment_type_cd}")
                return 0.0

        # エリア統計の取得
        if not area_stats:
            area_stats = await self._get_area_statistics(job)

        # 各スコアコンポーネントの計算
        try:
            # 1. 時給スコア（40%）
            hourly_wage_score = await self._calculate_hourly_wage_score(job, area_stats)

            # 2. Fee スコア（30%）
            fee_score = self._calculate_fee_score(job)

            # 3. 企業人気度スコア（30%）
            popularity_score = await self._calculate_company_popularity_score(job)

            # 加重平均で総合スコア計算
            basic_score = (
                hourly_wage_score * 0.40 +
                fee_score * 0.30 +
                popularity_score * 0.30
            )

            logger.debug(
                f"Job {job.job_id} scores: wage={hourly_wage_score:.1f}, "
                f"fee={fee_score:.1f}, popularity={popularity_score:.1f}, "
                f"total={basic_score:.1f}"
            )

            return min(100.0, max(0.0, basic_score))

        except Exception as e:
            logger.error(f"Error calculating basic score for job {job.job_id}: {e}")
            return 0.0

    async def _calculate_hourly_wage_score(
        self,
        job: Job,
        area_stats: Dict[str, float]
    ) -> float:
        """
        時給の正規化（エリア平均を基準に）
        z-scoreを使用した統計的正規化
        """
        # 平均時給の計算
        if job.salary and job.salary.min_salary and job.salary.max_salary:
            avg_wage = (job.salary.min_salary + job.salary.max_salary) / 2
        elif job.salary and job.salary.min_salary:
            avg_wage = job.salary.min_salary
        else:
            # 給与情報がない場合はデフォルト値
            avg_wage = area_stats.get('avg_salary', 1200)

        # 時給への変換（日給・月給の場合）
        if job.salary and job.salary.salary_type == "daily":
            avg_wage = avg_wage / 8  # 8時間労働想定
        elif job.salary and job.salary.salary_type == "monthly":
            avg_wage = avg_wage / 160  # 月160時間想定

        # エリア統計を使用したz-score計算
        area_avg = area_stats.get('avg_salary', 1200)
        area_std = area_stats.get('std_salary', 200)

        if area_std > 0:
            z_score = (avg_wage - area_avg) / area_std
        else:
            z_score = 0

        # z-score (-2 to +2) を 0-100 にマッピング
        # z=-2: 0点, z=0: 50点, z=+2: 100点
        normalized_score = min(100, max(0, (z_score + 2) * 25))

        return normalized_score

    def _calculate_fee_score(self, job: Job) -> float:
        """
        応募単価報酬（fee）の正規化
        500円以下は0点、5000円以上は100点
        """
        if not hasattr(job, 'fee'):
            return 30.0  # デフォルト中間値

        fee = job.fee

        if fee <= 500:
            return 0.0
        elif fee >= 5000:
            return 100.0
        else:
            # 500-5000円を0-100にリニアマッピング
            return (fee - 500) / (5000 - 500) * 100

    async def _calculate_company_popularity_score(self, job: Job) -> float:
        """
        企業人気度スコア（endcl_cdベース、360日データ）
        """
        if not hasattr(job, 'endcl_cd'):
            return 30.0  # デフォルト中間スコア

        # キャッシュチェック
        if job.endcl_cd in self._company_popularity_cache:
            stats = self._company_popularity_cache[job.endcl_cd]
        else:
            stats = await self._get_company_popularity_360d(job.endcl_cd)
            self._company_popularity_cache[job.endcl_cd] = stats

        if not stats:
            return 30.0  # データがない場合のデフォルト

        # 360日間の応募率で判定
        views = max(1, stats.get('views_360d', 1))
        applications = stats.get('applications_360d', 0)
        application_rate = applications / views

        # 応募率に基づくスコアリング
        if application_rate >= 0.15:  # 15%以上が応募
            return 100.0
        elif application_rate >= 0.10:  # 10%以上
            return 80.0
        elif application_rate >= 0.05:  # 5%以上
            return 60.0
        elif application_rate >= 0.02:  # 2%以上
            return 40.0
        else:
            return 20.0

    async def _get_area_statistics(self, job: Job) -> Dict[str, float]:
        """
        エリア統計データの取得
        """
        # キャッシュチェック
        cache_key = f"{job.location.prefecture_code}_{job.location.city_code}"
        if cache_key in self._area_stats_cache:
            return self._area_stats_cache[cache_key]

        try:
            # エリアの平均給与・標準偏差を取得
            query = text("""
                SELECT
                    AVG((min_salary + max_salary) / 2) as avg_salary,
                    STDDEV((min_salary + max_salary) / 2) as std_salary,
                    COUNT(*) as job_count
                FROM jobs j
                JOIN job_locations jl ON j.job_id = jl.job_id
                WHERE jl.prefecture_code = :pref_code
                AND (:city_code IS NULL OR jl.city_code = :city_code)
                AND j.min_salary > 0
                AND j.max_salary > 0
                AND j.employment_type_cd IN :employment_types
            """)

            result = await self.db.execute(query, {
                'pref_code': job.location.prefecture_code,
                'city_code': job.location.city_code,
                'employment_types': tuple(VALID_EMPLOYMENT_TYPE_CDS)
            })

            row = result.fetchone()
            if row and row.avg_salary:
                stats = {
                    'avg_salary': float(row.avg_salary),
                    'std_salary': float(row.std_salary) if row.std_salary else 200,
                    'job_count': int(row.job_count)
                }
            else:
                # デフォルト値（全国平均的な値）
                stats = {
                    'avg_salary': 1200,
                    'std_salary': 200,
                    'job_count': 0
                }

            self._area_stats_cache[cache_key] = stats
            return stats

        except Exception as e:
            logger.error(f"Error getting area statistics: {e}")
            return {'avg_salary': 1200, 'std_salary': 200, 'job_count': 0}

    async def _get_company_popularity_360d(self, endcl_cd: str) -> Optional[Dict[str, Any]]:
        """
        過去360日の企業人気度データ取得
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=360)

            query = text("""
                SELECT
                    COUNT(DISTINCT CASE WHEN action_type = 'view' THEN user_id END) as views_360d,
                    COUNT(DISTINCT CASE WHEN action_type IN ('apply', 'application') THEN user_id END) as applications_360d,
                    COUNT(CASE WHEN action_type IN ('apply', 'application')
                           AND action_timestamp > CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as applications_7d
                FROM user_actions
                WHERE endcl_cd = :endcl_cd
                AND action_timestamp > :cutoff_date
            """)

            result = await self.db.execute(query, {
                'endcl_cd': endcl_cd,
                'cutoff_date': cutoff_date
            })

            row = result.fetchone()
            if row:
                return {
                    'views_360d': int(row.views_360d) if row.views_360d else 0,
                    'applications_360d': int(row.applications_360d) if row.applications_360d else 0,
                    'applications_7d': int(row.applications_7d) if row.applications_7d else 0
                }

            return None

        except Exception as e:
            logger.warning(f"Error getting company popularity for {endcl_cd}: {e}")
            return None

    async def calculate_editorial_popularity_score(
        self,
        job: Job,
        user_location: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        編集部おすすめ用の人気度スコア（fee × 応募クリック数）
        """
        # Fee スコア
        fee_score = self._calculate_fee_score(job)

        # 応募クリック数スコア
        if hasattr(job, 'recent_applications'):
            # 応募1件 = 2点として計算
            click_score = min(100, job.recent_applications * 2)
        else:
            # DBから取得
            popularity = await self._get_company_popularity_360d(job.endcl_cd)
            if popularity:
                click_score = min(100, popularity.get('applications_7d', 0) * 2)
            else:
                click_score = 30

        # 地域重み付け
        location_weight = self._get_location_weight(job, user_location)

        # 総合スコア
        return (fee_score * 0.5 + click_score * 0.5) * location_weight

    def _get_location_weight(
        self,
        job: Job,
        user_location: Optional[Dict[str, Any]]
    ) -> float:
        """
        地域による重み付け
        市区町村: 1.0、周辺市区町村: 0.7、同じ都道府県: 0.5、それ以外: 0.3
        """
        if not user_location:
            return 1.0

        # 市区町村が完全一致
        if (hasattr(job, 'location') and
            job.location.city_code == user_location.get('city_code')):
            return 1.0

        # 周辺市区町村
        if (hasattr(job, 'location') and
            user_location.get('nearby_cities') and
            job.location.city_code in user_location['nearby_cities']):
            return 0.7

        # 同じ都道府県
        if (hasattr(job, 'location') and
            job.location.prefecture_code == user_location.get('pref_code')):
            return 0.5

        # それ以外
        return 0.3