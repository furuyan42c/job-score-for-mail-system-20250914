"""
ビジネスロジックサービス

- スコアリングエンジン
- マッチング処理
- 求人管理
- ユーザー管理
- 分析処理
- バッチ処理
- GPT-5 メール生成
- メール生成フォールバック
"""

from app.services.basic_scoring import BasicScoringService
from app.services.email_fallback import (
    EmailFallbackService,
    FallbackConfig,
    FallbackReason,
    TemplateStyle,
    create_fallback_service,
    get_fallback_reason_from_error,
)
from app.services.gpt5_integration import (
    BatchGenerationRequest,
    EmailGenerationService,
    EmailLanguage,
    EmailSectionType,
    GenerationStatus,
    JobMatch,
    UserProfile,
    create_email_generation_service,
)
from app.services.scoring import ScoringEngine
from app.services.scoring_service import ScoringService

__all__ = [
    "ScoringEngine",
    "BasicScoringService",
    "ScoringService",
    "EmailGenerationService",
    "create_email_generation_service",
    "EmailFallbackService",
    "create_fallback_service",
    "UserProfile",
    "JobMatch",
    "EmailSectionType",
    "EmailLanguage",
    "GenerationStatus",
    "BatchGenerationRequest",
    "FallbackConfig",
    "FallbackReason",
    "TemplateStyle",
    "get_fallback_reason_from_error",
]
