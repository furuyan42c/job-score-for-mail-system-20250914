"""
求人サービス

求人の管理、検索、分析に関するビジネスロジック
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, update, delete, and_, or_
import logging

from app.models.jobs import (
    Job, JobCreate, JobUpdate, JobListItem, JobSearchFilters,
    JobRecommendation, JobCompanyPopularity, JobKeywordAnalysis,
    BulkJobOperation, BulkJobResult
)

logger = logging.getLogger(__name__)


class JobService:
    """求人管理サービス"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_jobs(
        self,
        filters: Dict[str, Any],
        sort_by: str = "posting_date",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """求人検索"""
        try:
            offset = (page - 1) * size

            # 基本クエリ構築
            base_query = """
                SELECT
                    j.job_id,
                    j.company_name,
                    j.application_name,
                    j.min_salary,
                    j.max_salary,
                    j.salary_type,
                    p.name as prefecture_name,
                    c.name as city_name,
                    j.feature_codes,
                    je.composite_score,
                    j.posting_date,
                    j.is_active
                FROM jobs j
                LEFT JOIN prefecture_master p ON j.pref_cd = p.code
                LEFT JOIN city_master c ON j.city_cd = c.code
                LEFT JOIN job_enrichment je ON j.job_id = je.job_id
                WHERE 1=1
            """

            conditions = []
            params = {}

            # フィルター条件構築
            if filters.get('keyword'):
                conditions.append("""
                    (j.application_name ILIKE :keyword
                     OR j.company_name ILIKE :keyword
                     OR j.description ILIKE :keyword)
                """)
                params['keyword'] = f"%{filters['keyword']}%"

            if filters.get('prefecture_codes'):
                conditions.append("j.pref_cd = ANY(:prefecture_codes)")
                params['prefecture_codes'] = filters['prefecture_codes']

            if filters.get('city_codes'):
                conditions.append("j.city_cd = ANY(:city_codes)")
                params['city_codes'] = filters['city_codes']

            if filters.get('occupation_codes'):
                conditions.append("""
                    (j.occupation_cd1 = ANY(:occupation_codes)
                     OR j.occupation_cd2 = ANY(:occupation_codes))
                """)
                params['occupation_codes'] = filters['occupation_codes']

            if filters.get('feature_codes'):
                conditions.append("j.feature_codes && :feature_codes")
                params['feature_codes'] = filters['feature_codes']

            if filters.get('min_salary'):
                conditions.append("j.min_salary >= :min_salary")
                params['min_salary'] = filters['min_salary']

            if filters.get('max_salary'):
                conditions.append("j.max_salary <= :max_salary")
                params['max_salary'] = filters['max_salary']

            if filters.get('salary_type'):
                conditions.append("j.salary_type = :salary_type")
                params['salary_type'] = filters['salary_type']

            if filters.get('min_score'):
                conditions.append("je.composite_score >= :min_score")
                params['min_score'] = filters['min_score']

            if filters.get('has_high_income'):
                conditions.append("j.has_high_income = :has_high_income")
                params['has_high_income'] = filters['has_high_income']

            if filters.get('is_active') is not None:
                conditions.append("j.is_active = :is_active")
                params['is_active'] = filters['is_active']

            # 条件追加
            if conditions:
                base_query += " AND " + " AND ".join(conditions)

            # ソート
            sort_column = self._get_sort_column(sort_by)
            base_query += f" ORDER BY {sort_column} {sort_order.upper()}"

            # ページネーション
            base_query += " LIMIT :limit OFFSET :offset"
            params.update({'limit': size, 'offset': offset})

            # 実行
            result = await self.db.execute(text(base_query), params)
            jobs = result.fetchall()

            # 総件数取得
            count_query = base_query.split("ORDER BY")[0].replace(
                "SELECT j.job_id, j.company_name, j.application_name, j.min_salary, j.max_salary, j.salary_type, p.name as prefecture_name, c.name as city_name, j.feature_codes, je.composite_score, j.posting_date, j.is_active",
                "SELECT COUNT(*)"
            )
            total_result = await self.db.execute(text(count_query), {k: v for k, v in params.items() if k not in ['limit', 'offset']})
            total = total_result.scalar()

            # レスポンス構築
            job_items = [
                JobListItem(
                    job_id=job.job_id,
                    company_name=job.company_name,
                    application_name=job.application_name,
                    min_salary=job.min_salary,
                    max_salary=job.max_salary,
                    salary_type=job.salary_type,
                    prefecture_name=job.prefecture_name,
                    city_name=job.city_name,
                    feature_codes=job.feature_codes or [],
                    composite_score=job.composite_score,
                    posting_date=job.posting_date,
                    is_active=job.is_active
                )
                for job in jobs
            ]

            return {
                'items': job_items,
                'total': total,
                'page': page,
                'size': size,
                'total_pages': (total + size - 1) // size,
                'has_next': page * size < total,
                'has_prev': page > 1,
                'filters_applied': filters,
                'sort_applied': {'sort_by': sort_by, 'sort_order': sort_order}
            }

        except Exception as e:
            logger.error(f"求人検索エラー: {e}")
            raise

    def _get_sort_column(self, sort_by: str) -> str:
        """ソートカラムの取得"""
        sort_mapping = {
            'posting_date': 'j.posting_date',
            'min_salary': 'j.min_salary',
            'max_salary': 'j.max_salary',
            'composite_score': 'je.composite_score',
            'application_count_30d': 'je.application_count_30d',
            'click_count_30d': 'je.click_count_30d',
            'company_name': 'j.company_name'
        }
        return sort_mapping.get(sort_by, 'j.posting_date')

    async def get_job_by_id(
        self,
        job_id: int,
        include_scoring: bool = False,
        include_stats: bool = False
    ) -> Optional[Job]:
        """求人詳細取得"""
        try:
            query = """
                SELECT
                    j.*,
                    p.name as prefecture_name,
                    c.name as city_name,
                    cp.popularity_score
                FROM jobs j
                LEFT JOIN prefecture_master p ON j.pref_cd = p.code
                LEFT JOIN city_master c ON j.city_cd = c.code
                LEFT JOIN company_popularity cp ON j.endcl_cd = cp.endcl_cd
                WHERE j.job_id = :job_id
            """

            result = await self.db.execute(text(query), {"job_id": job_id})
            job_data = result.fetchone()

            if not job_data:
                return None

            # 基本求人情報構築
            job = Job(
                job_id=job_data.job_id,
                endcl_cd=job_data.endcl_cd,
                company_name=job_data.company_name,
                application_name=job_data.application_name,
                # ... 他のフィールド（実装簡略化）
                created_at=job_data.created_at,
                updated_at=job_data.updated_at
            )

            # スコアリング情報
            if include_scoring:
                scoring_query = """
                    SELECT * FROM job_enrichment WHERE job_id = :job_id
                """
                scoring_result = await self.db.execute(text(scoring_query), {"job_id": job_id})
                scoring_data = scoring_result.fetchone()
                if scoring_data:
                    # スコアリング情報を設定
                    pass

            # 統計情報
            if include_stats:
                stats_query = """
                    SELECT
                        application_count_30d,
                        click_count_30d,
                        view_count_30d,
                        conversion_rate
                    FROM job_enrichment
                    WHERE job_id = :job_id
                """
                stats_result = await self.db.execute(text(stats_query), {"job_id": job_id})
                stats_data = stats_result.fetchone()
                if stats_data:
                    # 統計情報を設定
                    pass

            return job

        except Exception as e:
            logger.error(f"求人取得エラー (job_id: {job_id}): {e}")
            raise

    async def create_job(self, job_data: JobCreate) -> Job:
        """求人作成"""
        try:
            # 求人データ挿入
            insert_query = """
                INSERT INTO jobs (
                    endcl_cd, company_name, application_name,
                    pref_cd, city_cd, address,
                    salary_type, min_salary, max_salary, fee,
                    occupation_cd1, occupation_cd2, employment_type_cd,
                    feature_codes, description, posting_date
                ) VALUES (
                    :endcl_cd, :company_name, :application_name,
                    :pref_cd, :city_cd, :address,
                    :salary_type, :min_salary, :max_salary, :fee,
                    :occupation_cd1, :occupation_cd2, :employment_type_cd,
                    :feature_codes, :description, CURRENT_TIMESTAMP
                ) RETURNING job_id
            """

            params = {
                'endcl_cd': job_data.endcl_cd,
                'company_name': job_data.company_name,
                'application_name': job_data.application_name,
                'pref_cd': job_data.location.prefecture_code,
                'city_cd': job_data.location.city_code,
                'address': job_data.location.address,
                'salary_type': job_data.salary.salary_type,
                'min_salary': job_data.salary.min_salary,
                'max_salary': job_data.salary.max_salary,
                'fee': job_data.salary.fee,
                'occupation_cd1': job_data.category.occupation_cd1,
                'occupation_cd2': job_data.category.occupation_cd2,
                'employment_type_cd': job_data.work_conditions.employment_type_cd,
                'feature_codes': job_data.features.feature_codes,
                'description': job_data.seo.description
            }

            result = await self.db.execute(text(insert_query), params)
            job_id = result.scalar()

            await self.db.commit()

            # 作成された求人を取得
            return await self.get_job_by_id(job_id)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"求人作成エラー: {e}")
            raise

    async def update_job(self, job_id: int, job_data: JobUpdate) -> Optional[Job]:
        """求人更新"""
        try:
            # 既存求人の確認
            existing_job = await self.get_job_by_id(job_id)
            if not existing_job:
                return None

            # 更新フィールドの構築
            update_fields = []
            params = {'job_id': job_id}

            if job_data.company_name is not None:
                update_fields.append("company_name = :company_name")
                params['company_name'] = job_data.company_name

            if job_data.application_name is not None:
                update_fields.append("application_name = :application_name")
                params['application_name'] = job_data.application_name

            if job_data.is_active is not None:
                update_fields.append("is_active = :is_active")
                params['is_active'] = job_data.is_active

            # 他のフィールドも同様に処理...

            if not update_fields:
                return existing_job

            update_fields.append("updated_at = CURRENT_TIMESTAMP")

            update_query = f"""
                UPDATE jobs
                SET {', '.join(update_fields)}
                WHERE job_id = :job_id
            """

            await self.db.execute(text(update_query), params)
            await self.db.commit()

            return await self.get_job_by_id(job_id)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"求人更新エラー (job_id: {job_id}): {e}")
            raise

    async def delete_job(self, job_id: int) -> bool:
        """求人削除（非活性化）"""
        try:
            query = """
                UPDATE jobs
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id AND is_active = true
            """

            result = await self.db.execute(text(query), {"job_id": job_id})
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            logger.error(f"求人削除エラー (job_id: {job_id}): {e}")
            raise

    async def activate_job(self, job_id: int) -> bool:
        """求人有効化"""
        try:
            query = """
                UPDATE jobs
                SET is_active = true, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id
            """

            result = await self.db.execute(text(query), {"job_id": job_id})
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            logger.error(f"求人有効化エラー (job_id: {job_id}): {e}")
            raise

    async def deactivate_job(self, job_id: int) -> bool:
        """求人無効化"""
        try:
            query = """
                UPDATE jobs
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id
            """

            result = await self.db.execute(text(query), {"job_id": job_id})
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            logger.error(f"求人無効化エラー (job_id: {job_id}): {e}")
            raise

    async def get_similar_jobs(self, job_id: int, limit: int = 10) -> List[JobRecommendation]:
        """類似求人推薦"""
        try:
            query = """
                WITH target_job AS (
                    SELECT occupation_cd1, occupation_cd2, pref_cd, city_cd
                    FROM jobs WHERE job_id = :job_id
                )
                SELECT
                    j.job_id,
                    j.company_name,
                    j.application_name,
                    j.min_salary,
                    j.max_salary,
                    j.salary_type,
                    je.composite_score,
                    CASE
                        WHEN j.occupation_cd1 = t.occupation_cd1 AND j.occupation_cd2 = t.occupation_cd2 THEN 90
                        WHEN j.occupation_cd1 = t.occupation_cd1 THEN 70
                        WHEN j.pref_cd = t.pref_cd THEN 60
                        ELSE 40
                    END as similarity_score
                FROM jobs j
                JOIN target_job t ON 1=1
                LEFT JOIN job_enrichment je ON j.job_id = je.job_id
                WHERE j.job_id != :job_id
                AND j.is_active = true
                ORDER BY similarity_score DESC, je.composite_score DESC NULLS LAST
                LIMIT :limit
            """

            result = await self.db.execute(text(query), {"job_id": job_id, "limit": limit})
            rows = result.fetchall()

            recommendations = []
            for i, row in enumerate(rows, 1):
                job_item = JobListItem(
                    job_id=row.job_id,
                    company_name=row.company_name,
                    application_name=row.application_name,
                    min_salary=row.min_salary,
                    max_salary=row.max_salary,
                    salary_type=row.salary_type,
                    composite_score=row.composite_score,
                    posting_date=datetime.now(),  # 簡略化
                    is_active=True
                )

                recommendation = JobRecommendation(
                    job=job_item,
                    score=row.similarity_score,
                    reason=f"類似度スコア: {row.similarity_score}",
                    section="similar_jobs",
                    rank=i
                )
                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"類似求人推薦エラー (job_id: {job_id}): {e}")
            raise

    async def analyze_job_keywords(self, job_id: int) -> Optional[JobKeywordAnalysis]:
        """求人キーワード分析"""
        try:
            # 基本情報取得
            job = await self.get_job_by_id(job_id)
            if not job:
                return None

            # キーワード抽出（簡易実装）
            text_content = f"{job.application_name} {job.seo.description or ''}"
            extracted_keywords = self._extract_keywords(text_content)

            # SEMrushキーワードマッチング
            semrush_query = """
                SELECT keyword
                FROM semrush_keywords
                WHERE keyword = ANY(:keywords)
                ORDER BY search_volume DESC
                LIMIT 20
            """

            result = await self.db.execute(text(semrush_query), {"keywords": extracted_keywords})
            semrush_matches = [row.keyword for row in result.fetchall()]

            return JobKeywordAnalysis(
                job_id=job_id,
                extracted_keywords=extracted_keywords,
                keyword_scores={kw: 1.0 for kw in extracted_keywords},  # 簡略化
                semrush_matches=semrush_matches,
                category_predictions=[],  # 実装簡略化
                seo_recommendations=[]   # 実装簡略化
            )

        except Exception as e:
            logger.error(f"キーワード分析エラー (job_id: {job_id}): {e}")
            raise

    def _extract_keywords(self, text: str) -> List[str]:
        """キーワード抽出（簡易実装）"""
        # 実際の実装では形態素解析やTF-IDFを使用
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) > 2][:20]

    async def get_company_popularity(self, endcl_cd: str) -> Optional[JobCompanyPopularity]:
        """企業人気度取得"""
        try:
            query = """
                SELECT * FROM company_popularity
                WHERE endcl_cd = :endcl_cd
            """

            result = await self.db.execute(text(query), {"endcl_cd": endcl_cd})
            row = result.fetchone()

            if not row:
                return None

            return JobCompanyPopularity(
                endcl_cd=row.endcl_cd,
                company_name=row.company_name,
                total_views=row.total_views,
                total_clicks=row.total_clicks,
                total_applications=row.total_applications,
                unique_visitors=row.unique_visitors,
                views_7d=row.views_7d,
                views_30d=row.views_30d,
                applications_7d=row.applications_7d,
                applications_30d=row.applications_30d,
                application_rate=row.application_rate,
                popularity_score=row.popularity_score,
                last_calculated_at=row.last_calculated_at
            )

        except Exception as e:
            logger.error(f"企業人気度取得エラー (endcl_cd: {endcl_cd}): {e}")
            raise

    async def bulk_operations(self, operation: BulkJobOperation) -> BulkJobResult:
        """求人一括操作"""
        try:
            start_time = datetime.now()
            success_count = 0
            errors = []

            for job_id in operation.job_ids:
                try:
                    if operation.operation == "activate":
                        success = await self.activate_job(job_id)
                        if success:
                            success_count += 1
                    elif operation.operation == "deactivate":
                        success = await self.deactivate_job(job_id)
                        if success:
                            success_count += 1
                    elif operation.operation == "delete":
                        success = await self.delete_job(job_id)
                        if success:
                            success_count += 1
                    # 他の操作も同様に実装...

                except Exception as e:
                    errors.append({
                        "job_id": job_id,
                        "error": str(e)
                    })

            return BulkJobResult(
                total_requested=len(operation.job_ids),
                success_count=success_count,
                error_count=len(errors),
                errors=errors,
                operation=operation.operation,
                executed_at=start_time
            )

        except Exception as e:
            logger.error(f"一括操作エラー: {e}")
            raise

    async def recalculate_score(self, job_id: int, force: bool = False) -> bool:
        """求人スコア再計算"""
        try:
            # スコア再計算処理（実装簡略化）
            query = """
                UPDATE job_enrichment
                SET calculated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id
            """

            result = await self.db.execute(text(query), {"job_id": job_id})
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            logger.error(f"スコア再計算エラー (job_id: {job_id}): {e}")
            raise

    async def get_stats_summary(self) -> Dict[str, Any]:
        """求人統計サマリー"""
        try:
            query = """
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE is_active = true) as active_jobs,
                    COUNT(*) FILTER (WHERE posting_date > CURRENT_DATE - INTERVAL '7 days') as new_jobs_7d,
                    COUNT(*) FILTER (WHERE posting_date > CURRENT_DATE - INTERVAL '30 days') as new_jobs_30d,
                    AVG(min_salary) FILTER (WHERE salary_type = 'hourly') as avg_hourly_salary,
                    COUNT(DISTINCT endcl_cd) as unique_companies
                FROM jobs
            """

            result = await self.db.execute(text(query))
            row = result.fetchone()

            return {
                "total_jobs": row.total_jobs,
                "active_jobs": row.active_jobs,
                "new_jobs_7d": row.new_jobs_7d,
                "new_jobs_30d": row.new_jobs_30d,
                "avg_hourly_salary": round(row.avg_hourly_salary, 2) if row.avg_hourly_salary else None,
                "unique_companies": row.unique_companies
            }

        except Exception as e:
            logger.error(f"統計サマリー取得エラー: {e}")
            raise