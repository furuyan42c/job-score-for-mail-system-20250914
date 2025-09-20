"""
アプリケーション設定管理

環境変数から設定を読み込み、型安全な設定オブジェクトを提供
高並行性（10,000+同時接続）に最適化された設定
"""

import os
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    # 基本設定
    APP_NAME: str = "バイト求人マッチングシステム"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    # データベース設定（環境別対応）
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    @validator("DATABASE_URL")
    def validate_database_url(cls, v, values):
        """環境別DATABASE_URL検証"""
        environment = values.get("ENVIRONMENT", "development")

        if environment == "development":
            # 開発環境：SQLiteまたはローカルPostgreSQL許可
            if v.startswith(("sqlite", "postgresql://postgres:postgres@localhost")):
                return v
            elif v.startswith("postgresql://") and "localhost" in v:
                return v
            else:
                # 開発環境でもSupabase URLは許可
                return v
        elif environment in ["staging", "production"]:
            # 本番/ステージング：PostgreSQL必須
            if not v.startswith("postgresql://"):
                raise ValueError(
                    f"Production environment requires PostgreSQL URL, got: {v[:50]}..."
                )
            return v
        else:
            # その他の環境：すべて許可
            return v

    # データベース接続プール設定（高並行性対応）
    DB_POOL_SIZE: int = Field(default=100, description="基本接続プール数")
    DB_MAX_OVERFLOW: int = Field(default=200, description="追加接続数")
    DB_POOL_TIMEOUT: int = Field(default=10, description="接続タイムアウト（秒）")
    DB_POOL_RECYCLE: int = Field(default=3600, description="接続リサイクル時間（秒）")
    DB_POOL_PRE_PING: bool = Field(default=True, description="接続前ping確認")
    DB_ECHO: bool = Field(default=False, description="SQLログ出力")

    # CORS設定
    ALLOWED_HOSTS: List[str] = ["*"]

    # Redis設定（キャッシュ・セッション）
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1時間

    # バッチ処理設定
    BATCH_SIZE: int = 1000
    MAX_WORKERS: int = 4
    SCORING_BATCH_SIZE: int = 5000
    EMAIL_BATCH_SIZE: int = 100

    # マッチング設定
    MATCHING_SCORE_THRESHOLD: float = 60.0
    MAX_DAILY_PICKS_PER_USER: int = 40
    RECOMMENDATION_SECTIONS: int = 6

    # メール設定
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    FROM_NAME: str = "バイト求人マッチング"

    # AI・ML設定
    OPENAI_API_KEY: Optional[str] = None
    ML_MODEL_PATH: str = "./models"
    SCORING_MODEL_VERSION: str = "v1.0"

    # 外部API設定
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    SEMRUSH_API_KEY: Optional[str] = None

    # 監視・エラー追跡設定
    SENTRY_DSN: Optional[str] = None
    VERSION: str = "1.0.0"

    # ファイルアップロード設定
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # セキュリティ設定
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24時間
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8

    # パフォーマンス設定（高並行性対応）
    QUERY_TIMEOUT: int = Field(default=30, description="クエリタイムアウト（秒）")
    API_RATE_LIMIT: int = Field(default=10000, description="レート制限（requests per minute）")
    SLOW_QUERY_THRESHOLD: float = Field(default=1.0, description="スロークエリ閾値（秒）")
    MAX_CONCURRENT_REQUESTS: int = Field(default=10000, description="最大同時リクエスト数")
    REQUEST_TIMEOUT: int = Field(default=30, description="リクエストタイムアウト（秒）")
    KEEP_ALIVE_TIMEOUT: int = Field(default=5, description="Keep-Aliveタイムアウト（秒）")

    # ワーカー設定
    UVICORN_WORKERS: int = Field(default=4, description="Uvicornワーカー数")
    UVICORN_WORKER_CONNECTIONS: int = Field(default=1000, description="ワーカー当たり接続数")
    UVICORN_BACKLOG: int = Field(default=2048, description="接続バックログ")

    # 非同期設定
    ASYNC_POOL_SIZE: int = Field(default=100, description="非同期プールサイズ")
    ASYNC_MAX_WORKERS: int = Field(default=32, description="非同期最大ワーカー数")

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """ALLOWED_HOSTSを文字列からリストに変換"""
        if isinstance(v, str):
            if v.strip() == "":
                return ["*"]  # Default if empty
            return [host.strip() for host in v.split(",")]
        if isinstance(v, list):
            return v
        return ["*"]  # Default fallback

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """シークレットキーの検証"""
        if len(v) < 32:
            raise ValueError("SECRET_KEYは32文字以上である必要があります")
        return v

    @property
    def database_url_sync(self) -> str:
        """同期データベースURL"""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def database_url_async(self) -> str:
        """非同期データベースURL"""
        if "+asyncpg" not in self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# 設定インスタンス
settings = Settings()


# 環境別設定
class DevelopmentSettings(Settings):
    """開発環境設定"""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """本番環境設定"""

    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    ALLOWED_HOSTS: List[str] = ["api.jobmatching.com"]


class TestSettings(Settings):
    """テスト環境設定"""

    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    CACHE_TTL: int = 1

    # Required fields with test defaults
    SECRET_KEY: str = "test-secret-key-for-testing-only-minimum-32-characters"
    SUPABASE_URL: str = "https://test.supabase.co"
    SUPABASE_ANON_KEY: str = "test-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "test-service-role-key"
    SMTP_USER: str = "test@example.com"
    SMTP_PASSWORD: str = "testpassword"
    FROM_EMAIL: str = "test@example.com"

    # Override defaults for testing
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    BATCH_SIZE: int = 10
    MAX_WORKERS: int = 1


def get_settings() -> Settings:
    """環境に応じた設定を取得"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# アプリケーションで使用する設定
settings = get_settings()
