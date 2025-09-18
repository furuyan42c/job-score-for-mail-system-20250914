# FastAPI実装ガイド - バイト求人マッチングシステム

## 📋 概要

このドキュメントは、詳細API仕様（`detailed-api-spec.yaml`）をFastAPIで実装するための具体的なガイドです。

---

## 🏗️ プロジェクト構造

```
job_matching_api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPIアプリケーション
│   ├── config.py                  # 設定管理
│   ├── database.py                # DB接続設定
│   ├── dependencies.py            # 依存関係
│   ├── middleware.py              # ミドルウェア
│   ├── models/                    # SQLAlchemyモデル
│   │   ├── __init__.py
│   │   ├── job.py
│   │   ├── user.py
│   │   ├── matching.py
│   │   ├── batch.py
│   │   └── monitoring.py
│   ├── schemas/                   # Pydanticスキーマ
│   │   ├── __init__.py
│   │   ├── job.py
│   │   ├── user.py
│   │   ├── matching.py
│   │   ├── batch.py
│   │   ├── monitoring.py
│   │   └── common.py
│   ├── api/                       # APIルーター
│   │   ├── __init__.py
│   │   ├── v2/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py
│   │   │   ├── users.py
│   │   │   ├── matching.py
│   │   │   ├── batch.py
│   │   │   ├── monitoring.py
│   │   │   └── email.py
│   ├── services/                  # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── job_service.py
│   │   ├── user_service.py
│   │   ├── matching_service.py
│   │   ├── batch_service.py
│   │   ├── email_service.py
│   │   └── monitoring_service.py
│   ├── core/                      # コア機能
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   └── workers/                   # バックグラウンドワーカー
│       ├── __init__.py
│       ├── scoring_worker.py
│       ├── matching_worker.py
│       └── email_worker.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_jobs.py
    ├── test_users.py
    ├── test_matching.py
    ├── test_batch.py
    └── test_monitoring.py
```

---

## 🚀 セットアップ・設定

### requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic[email]==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
aioredis==2.0.1
celery==5.3.4
redis==5.0.1
asyncpg==0.29.0
pandas==2.1.3
scikit-learn==1.3.2
openai==1.3.7
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
loguru==0.7.2
prometheus-client==0.19.0
```

### app/config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/jobmatching"
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379"

    # API Keys
    openai_api_key: str
    supabase_url: str
    supabase_key: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_key_header: str = "X-API-Key"

    # Batch Processing
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    max_batch_workers: int = 8

    # Performance
    default_page_size: int = 50
    max_page_size: int = 1000
    request_timeout: int = 30

    # Monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True

    # Email Generation
    email_batch_size: int = 100
    max_jobs_per_section: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🏛️ データベースモデル例

### app/models/job.py
```python
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum

Base = declarative_base()

class JobStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    DELETED = "deleted"

class OccupationCategory(str, Enum):
    RESTAURANT = "restaurant"
    RETAIL = "retail"
    OFFICE = "office"
    LOGISTICS = "logistics"
    EDUCATION = "education"
    MEDICAL = "medical"
    CONSTRUCTION = "construction"
    MANUFACTURING = "manufacturing"
    IT = "it"
    SERVICE = "service"
    CREATIVE = "creative"
    OTHER = "other"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    company_name = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)

    # Salary
    salary_min = Column(Integer)
    salary_max = Column(Integer)

    # Location
    location = Column(String(200), index=True)
    prefecture = Column(String(50), index=True)
    city = Column(String(100), index=True)
    nearest_station = Column(String(100))

    # Work details
    work_hours = Column(String(200))
    work_days = Column(String(200))
    features = Column(ARRAY(String))

    # Categories
    occupation_category = Column(String(50), nullable=False, index=True)
    needs_categories = Column(ARRAY(String))

    # Scores
    basic_score = Column(Float, default=0.0, index=True)
    seo_score = Column(Float, default=0.0, index=True)
    personalized_score = Column(Float, default=0.0, index=True)
    combined_score = Column(Float, default=0.0, index=True)

    # Status
    status = Column(String(20), default=JobStatus.ACTIVE, index=True)

    # URLs
    url = Column(String(500))
    application_url = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, index=True)
```

### app/models/user.py
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON
from sqlalchemy.sql import func
from .job import Base
from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NOT_SPECIFIED = "not_specified"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))

    # Location
    location = Column(JSON)  # {"prefecture": "東京都", "city": "渋谷区", "address": "..."}

    # Status
    status = Column(String(20), default=UserStatus.ACTIVE, index=True)
    email_verified = Column(Boolean, default=False)

    # Engagement
    engagement_score = Column(Float, default=0.0, index=True)
    last_login = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Work preferences
    work_preferences = Column(JSON)
    # Example: {
    #   "preferred_occupations": ["restaurant", "retail"],
    #   "preferred_locations": ["東京都", "神奈川県"],
    #   "salary_expectation": {"min": 1200, "max": 2000},
    #   "work_style": ["part_time", "flexible"]
    # }

    # Experience
    experience = Column(JSON)
    # Example: {
    #   "work_history": [
    #     {"occupation": "restaurant", "duration_months": 12, "skills": ["接客", "調理補助"]}
    #   ],
    #   "education": "university"
    # }

    # Personal info
    personal_info = Column(JSON)
    # Example: {
    #   "transportation": ["public_transport", "bicycle"],
    #   "availability": {
    #     "weekdays": true, "weekends": false,
    #     "mornings": true, "afternoons": true, "evenings": false, "nights": false
    #   }
    # }

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserBehaviorLog(Base):
    __tablename__ = "user_behavior_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    target_id = Column(Integer)
    target_type = Column(String(50))
    metadata = Column(JSON)
    session_id = Column(String(255), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
```

---

## 🔌 APIルーター実装例

### app/api/v2/jobs.py
```python
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session
from ...database import get_db
from ...schemas.job import (
    Job, JobCreateRequest, JobUpdateRequest, JobListResponse,
    JobSearchRequest, JobSearchResponse
)
from ...services.job_service import JobService
from ...core.security import get_api_key
from ...core.exceptions import JobNotFoundError

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/", response_model=JobListResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    keyword: Optional[str] = Query(None, max_length=100),
    location: Optional[str] = Query(None),
    salary_min: Optional[int] = Query(None, ge=0),
    salary_max: Optional[int] = Query(None, ge=0),
    occupation_categories: Optional[List[str]] = Query(None),
    needs_categories: Optional[List[str]] = Query(None),
    status: str = Query("active"),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """求人一覧取得"""
    service = JobService(db)

    filters = {
        "keyword": keyword,
        "location": location,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "occupation_categories": occupation_categories,
        "needs_categories": needs_categories,
        "status": status
    }

    result = await service.get_jobs(
        page=page,
        limit=limit,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return result

@router.post("/", response_model=Job, status_code=201)
async def create_job(
    job_data: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """求人作成"""
    service = JobService(db)

    job = await service.create_job(job_data)

    # バックグラウンドでスコアリングとカテゴリ分類を実行
    background_tasks.add_task(service.calculate_scores, job.id)
    background_tasks.add_task(service.categorize_job, job.id)

    return job

@router.get("/{job_id}", response_model=Job)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """求人詳細取得"""
    service = JobService(db)

    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job

@router.put("/{job_id}", response_model=Job)
async def update_job(
    job_id: int,
    job_data: JobUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """求人更新"""
    service = JobService(db)

    job = await service.update_job(job_id, job_data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # スコア再計算
    background_tasks.add_task(service.calculate_scores, job.id)

    return job

@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """求人削除（論理削除）"""
    service = JobService(db)

    success = await service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    search_request: JobSearchRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """高度な求人検索"""
    service = JobService(db)

    result = await service.search_jobs(search_request)
    return result

@router.post("/bulk")
async def bulk_jobs(
    # マルチパート/JSONでの一括処理実装
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """求人一括処理"""
    # 実装詳細は省略
    pass

@router.post("/{job_id}/scoring")
async def score_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """求人スコア再計算"""
    service = JobService(db)

    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    background_tasks.add_task(service.calculate_scores, job_id)

    return {"message": "Scoring job started", "job_id": job_id}
```

### app/services/job_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from ..models.job import Job, JobStatus
from ..schemas.job import JobCreateRequest, JobUpdateRequest, JobSearchRequest
from ..core.exceptions import JobNotFoundError
import logging

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self, db: Session):
        self.db = db

    async def get_jobs(
        self,
        page: int,
        limit: int,
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str
    ):
        """求人一覧取得"""
        query = self.db.query(Job)

        # フィルタリング
        if filters.get("keyword"):
            keyword = f"%{filters['keyword']}%"
            query = query.filter(
                or_(
                    Job.title.ilike(keyword),
                    Job.company_name.ilike(keyword),
                    Job.description.ilike(keyword)
                )
            )

        if filters.get("location"):
            location = f"%{filters['location']}%"
            query = query.filter(Job.location.ilike(location))

        if filters.get("salary_min"):
            query = query.filter(Job.salary_min >= filters["salary_min"])

        if filters.get("salary_max"):
            query = query.filter(Job.salary_max <= filters["salary_max"])

        if filters.get("occupation_categories"):
            query = query.filter(Job.occupation_category.in_(filters["occupation_categories"]))

        if filters.get("status"):
            query = query.filter(Job.status == filters["status"])

        # ソート
        sort_column = getattr(Job, sort_by, Job.updated_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # ページネーション
        total = query.count()
        offset = (page - 1) * limit
        jobs = query.offset(offset).limit(limit).all()

        return {
            "jobs": jobs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": total,
                "total_pages": (total + limit - 1) // limit,
                "has_next": page * limit < total,
                "has_prev": page > 1
            }
        }

    async def create_job(self, job_data: JobCreateRequest) -> Job:
        """求人作成"""
        job = Job(**job_data.dict())
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        logger.info(f"Created job {job.id}: {job.title}")
        return job

    async def get_job(self, job_id: int) -> Optional[Job]:
        """求人詳細取得"""
        return self.db.query(Job).filter(Job.id == job_id).first()

    async def update_job(self, job_id: int, job_data: JobUpdateRequest) -> Optional[Job]:
        """求人更新"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        for field, value in job_data.dict(exclude_unset=True).items():
            setattr(job, field, value)

        self.db.commit()
        self.db.refresh(job)

        logger.info(f"Updated job {job_id}")
        return job

    async def delete_job(self, job_id: int) -> bool:
        """求人削除（論理削除）"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False

        job.status = JobStatus.DELETED
        self.db.commit()

        logger.info(f"Deleted job {job_id}")
        return True

    async def calculate_scores(self, job_id: int):
        """求人スコア計算"""
        job = await self.get_job(job_id)
        if not job:
            return

        # 基礎スコア計算
        basic_score = self._calculate_basic_score(job)

        # SEOスコア計算
        seo_score = self._calculate_seo_score(job)

        # パーソナライズスコア計算（実装省略）
        personalized_score = 0.0

        # 統合スコア計算
        combined_score = (basic_score * 0.4 + seo_score * 0.3 + personalized_score * 0.3)

        # DB更新
        job.basic_score = basic_score
        job.seo_score = seo_score
        job.personalized_score = personalized_score
        job.combined_score = combined_score

        self.db.commit()
        logger.info(f"Calculated scores for job {job_id}: basic={basic_score:.2f}, seo={seo_score:.2f}")

    def _calculate_basic_score(self, job: Job) -> float:
        """基礎スコア計算"""
        score = 0.0

        # タイトルの長さ
        if job.title and 10 <= len(job.title) <= 30:
            score += 20

        # 説明の充実度
        if job.description and len(job.description) >= 100:
            score += 15

        # 給与情報の有無
        if job.salary_min and job.salary_max:
            score += 25

        # 勤務地情報の詳細度
        if job.prefecture and job.city:
            score += 20

        # 最寄り駅情報
        if job.nearest_station:
            score += 10

        # 特徴の数
        if job.features:
            score += min(len(job.features) * 2, 10)

        return min(score, 100.0)

    def _calculate_seo_score(self, job: Job) -> float:
        """SEOスコア計算"""
        score = 0.0

        # キーワード密度チェック（簡易版）
        if job.title and job.description:
            title_words = set(job.title.lower().split())
            desc_words = job.description.lower().split()

            # タイトルキーワードが説明文にも含まれる
            for word in title_words:
                if word in desc_words:
                    score += 5

        # URL構造
        if job.url and 'https' in job.url:
            score += 10

        # 地域キーワード
        if job.location and any(region in job.location for region in ['東京', '大阪', '名古屋']):
            score += 15

        return min(score, 100.0)

    async def search_jobs(self, search_request: JobSearchRequest):
        """高度検索"""
        # Elasticsearch等の実装が理想だが、簡易版をPostgreSQLで実装
        query = self.db.query(Job)

        # 全文検索（PostgreSQLのfull-text searchを使用）
        if search_request.query:
            # 実際の実装では全文検索インデックスを使用
            pass

        # 地理的検索
        if search_request.location and search_request.location.point:
            # PostGISを使用した地理的検索
            pass

        # その他のフィルタリング実装

        return {"jobs": [], "pagination": {}, "search_meta": {}}
```

---

## 🔐 セキュリティ実装

### app/core/security.py
```python
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config import settings
import hashlib
import secrets

security = HTTPBearer(auto_error=False)

# APIキー認証
async def get_api_key(authorization: HTTPAuthorizationCredentials = Depends(security)):
    """APIキー認証"""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 実際の実装では、データベースでAPIキーを検証
    api_key = authorization.credentials
    if not validate_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key

def validate_api_key(api_key: str) -> bool:
    """APIキー検証"""
    # 実際の実装では、データベースでAPIキーを検証
    # ハッシュ化されたAPIキーとの比較等
    return len(api_key) >= 32  # 仮の実装

def create_access_token(data: dict, expires_delta: timedelta = None):
    """JWTトークン作成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(security)):
    """JWT認証"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # ユーザー取得ロジック
    return user_id
```

---

## 🔄 バックグラウンドタスク

### app/workers/matching_worker.py
```python
from celery import Celery
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.matching_service import MatchingService
from ..config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "job_matching",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

@celery_app.task(bind=True, max_retries=3)
def process_user_matching(self, user_id: int, batch_date: str):
    """ユーザーマッチング処理"""
    try:
        db = next(get_db())
        service = MatchingService(db)

        result = service.generate_recommendations(user_id, batch_date)

        logger.info(f"Completed matching for user {user_id}, generated {len(result)} recommendations")
        return result

    except Exception as exc:
        logger.error(f"Matching failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True)
def batch_scoring(self, job_ids: list = None):
    """バッチスコアリング"""
    try:
        db = next(get_db())
        from ..services.job_service import JobService

        service = JobService(db)

        if job_ids is None:
            # 全求人を対象
            jobs = db.query(Job).filter(Job.status == "active").all()
            job_ids = [job.id for job in jobs]

        for job_id in job_ids:
            service.calculate_scores(job_id)

        logger.info(f"Completed batch scoring for {len(job_ids)} jobs")
        return {"processed": len(job_ids)}

    except Exception as exc:
        logger.error(f"Batch scoring failed: {exc}")
        raise
```

---

## 📊 モニタリング・ログ

### app/core/logging.py
```python
import logging
import sys
from loguru import logger
from ..config import settings

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """ログ設定"""
    # Remove default handlers
    logger.remove()

    # Add custom handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )

    # Add file handler
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
```

### app/middleware.py
```python
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import uuid
from loguru import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host
            }
        )

        response = await call_next(request)

        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed",
            extra={
                "trace_id": trace_id,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )

        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Process-Time"] = str(process_time)

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Clean old entries
        self.clients = {
            ip: timestamps for ip, timestamps in self.clients.items()
            if any(ts > now - self.period for ts in timestamps)
        }

        # Check rate limit
        if client_ip in self.clients:
            recent_calls = [ts for ts in self.clients[client_ip] if ts > now - self.period]
            if len(recent_calls) >= self.calls:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": str(self.period)}
                )
            self.clients[client_ip] = recent_calls + [now]
        else:
            self.clients[client_ip] = [now]

        return await call_next(request)
```

---

## 🧪 テスト実装例

### tests/test_jobs.py
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_job_data():
    return {
        "company_name": "テスト株式会社",
        "title": "アルバイトスタッフ募集",
        "description": "カフェでのアルバイトスタッフを募集しています。",
        "salary_min": 1200,
        "salary_max": 1500,
        "location": "東京都渋谷区",
        "occupation_category": "restaurant"
    }

def test_create_job(test_job_data):
    """求人作成テスト"""
    response = client.post(
        "/api/v2/jobs/",
        json=test_job_data,
        headers={"X-API-Key": "test-api-key"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == test_job_data["company_name"]
    assert data["title"] == test_job_data["title"]

def test_get_jobs():
    """求人一覧取得テスト"""
    response = client.get(
        "/api/v2/jobs/",
        headers={"X-API-Key": "test-api-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "pagination" in data

def test_search_jobs():
    """求人検索テスト"""
    search_data = {
        "query": "アルバイト",
        "page": 1,
        "limit": 10
    }
    response = client.post(
        "/api/v2/jobs/search",
        json=search_data,
        headers={"X-API-Key": "test-api-key"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_job_scoring():
    """求人スコアリングテスト"""
    # 求人作成後、スコアリング処理をテスト
    pass
```

---

## 🚀 デプロイメント

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/jobmatching
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=jobmatching
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A app.workers.matching_worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/jobmatching
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

---

## 📈 パフォーマンス最適化

### 1. データベース最適化
```sql
-- インデックス作成
CREATE INDEX idx_jobs_status_score ON jobs(status, combined_score DESC);
CREATE INDEX idx_jobs_location_gin ON jobs USING gin(to_tsvector('japanese', location));
CREATE INDEX idx_user_behavior_user_action ON user_behavior_logs(user_id, action_type, timestamp);

-- パーティショニング（大規模データ用）
CREATE TABLE user_behavior_logs_2025_09 PARTITION OF user_behavior_logs
FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
```

### 2. キャッシュ戦略
```python
import redis
from functools import wraps

redis_client = redis.Redis.from_url(settings.redis_url)

def cache_result(expiry: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キー生成
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # キャッシュ確認
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 実行してキャッシュ
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, json.dumps(result, default=str))

            return result
        return wrapper
    return decorator

# 使用例
@cache_result(expiry=1800)  # 30分キャッシュ
async def get_user_recommendations(user_id: int):
    # 推薦処理
    pass
```

### 3. 非同期処理
```python
import asyncio
from typing import List

async def batch_process_users(user_ids: List[int], batch_size: int = 100):
    """ユーザーの並列処理"""
    semaphore = asyncio.Semaphore(8)  # 最大8並列

    async def process_user(user_id: int):
        async with semaphore:
            return await generate_user_recommendations(user_id)

    # バッチごとに処理
    results = []
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_user(user_id) for user_id in batch],
            return_exceptions=True
        )
        results.extend(batch_results)

    return results
```

---

このガイドにより、OpenAPI 3.0仕様書を基にしたFastAPIアプリケーションの実装が可能になります。スケーラブルで保守性の高いシステム構築を支援する包括的な実装例を提供しています。