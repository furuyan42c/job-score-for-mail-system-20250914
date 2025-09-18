"""
GPT-5 Nano Integration Service

A comprehensive service for generating personalized email content using OpenAI's GPT-5 nano model.
Supports the 6-section email structure with Japanese/English content generation,
batch processing, caching, rate limiting, and comprehensive error handling.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from contextlib import asynccontextmanager

import openai
from openai import AsyncOpenAI
import aioredis
from pydantic import BaseModel, Field, validator
import structlog

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
CACHE_TTL = 3600  # 1 hour
RATE_LIMIT_PER_MINUTE = 100
BATCH_SIZE = 10
GPT5_NANO_MODEL = "gpt-5-nano"  # Model identifier when available


class EmailLanguage(str, Enum):
    """Supported email languages"""
    JAPANESE = "ja"
    ENGLISH = "en"


class EmailSectionType(str, Enum):
    """Email section types based on the 6-section structure"""
    EDITORIAL_PICKS = "editorial_picks"
    TOP_RECOMMENDATIONS = "top_recommendations"
    PERSONALIZED_PICKS = "personalized_picks"
    NEW_ARRIVALS = "new_arrivals"
    POPULAR_JOBS = "popular_jobs"
    YOU_MIGHT_LIKE = "you_might_like"


class GenerationStatus(str, Enum):
    """Email generation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class UserProfile:
    """User profile data for personalization"""
    user_id: int
    name: str
    email: str
    preferred_language: EmailLanguage
    location: Optional[str] = None
    job_preferences: Dict[str, Any] = field(default_factory=dict)
    experience_level: Optional[str] = None
    salary_range: Optional[Dict[str, int]] = None
    work_style: Optional[str] = None
    last_active: Optional[datetime] = None


@dataclass
class JobMatch:
    """Job match data for email content"""
    job_id: int
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    description: str = ""
    match_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    is_new: bool = False
    is_popular: bool = False
    application_count: int = 0


class EmailSection(BaseModel):
    """Individual email section with generated content"""
    section_type: EmailSectionType
    title: str
    intro_text: str
    job_descriptions: List[str]
    call_to_action: str
    generated_at: datetime = Field(default_factory=datetime.now)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)


class EmailContent(BaseModel):
    """Complete email content structure"""
    user_id: int
    subject: str
    greeting: str
    introduction: str
    sections: List[EmailSection]
    closing: str
    signature: str
    language: EmailLanguage
    generated_at: datetime = Field(default_factory=datetime.now)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('sections')
    def validate_sections_count(cls, v):
        if len(v) != 6:
            raise ValueError("Email must contain exactly 6 sections")
        return v


class BatchGenerationRequest(BaseModel):
    """Batch email generation request"""
    user_profiles: List[UserProfile]
    job_matches_by_user: Dict[int, Dict[EmailSectionType, List[JobMatch]]]
    language: EmailLanguage = EmailLanguage.JAPANESE
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    dry_run: bool = False


class GenerationResult(BaseModel):
    """Email generation result"""
    user_id: int
    status: GenerationStatus
    email_content: Optional[EmailContent] = None
    error_message: Optional[str] = None
    generation_time_ms: int = 0
    token_usage: Dict[str, int] = Field(default_factory=dict)
    cache_hit: bool = False
    fallback_used: bool = False


class RateLimiter:
    """Redis-based rate limiter"""

    def __init__(self, redis_client: aioredis.Redis, limit_per_minute: int = RATE_LIMIT_PER_MINUTE):
        self.redis = redis_client
        self.limit = limit_per_minute

    async def check_limit(self, key: str) -> bool:
        """Check if request is within rate limit"""
        now = int(time.time())
        window_start = now - 60

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, 60)

        results = await pipe.execute()
        current_requests = results[1]

        return current_requests < self.limit


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""

    def __init__(self):
        self.logger = structlog.get_logger("gpt5_integration.performance")
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "total_tokens_used": 0
        }

    @asynccontextmanager
    async def track_request(self, operation: str, user_id: int):
        """Context manager for tracking request performance"""
        start_time = time.time()
        self.metrics["total_requests"] += 1

        try:
            yield
            self.metrics["successful_requests"] += 1

        except Exception as e:
            self.metrics["failed_requests"] += 1
            await self.logger.aerror(
                "Request failed",
                operation=operation,
                user_id=user_id,
                error=str(e)
            )
            raise

        finally:
            duration = (time.time() - start_time) * 1000
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (self.metrics["total_requests"] - 1) + duration)
                / self.metrics["total_requests"]
            )

            await self.logger.ainfo(
                "Request completed",
                operation=operation,
                user_id=user_id,
                duration_ms=duration
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()


class EmailGenerationService:
    """
    Main service class for GPT-5 nano email generation.

    Provides comprehensive email generation capabilities with:
    - Personalized content generation using GPT-5 nano
    - 6-section email structure support
    - Japanese and English content generation
    - Batch processing for multiple users
    - Rate limiting and quota management
    - Caching for improved performance
    - Comprehensive error handling and retry logic
    - Performance monitoring and logging
    - Mock testing capabilities
    """

    def __init__(
        self,
        openai_api_key: str,
        redis_url: str = "redis://localhost:6379/0",
        rate_limit_per_minute: int = RATE_LIMIT_PER_MINUTE,
        cache_ttl: int = CACHE_TTL,
        mock_mode: bool = False,
        log_level: str = "INFO"
    ):
        """
        Initialize the email generation service.

        Args:
            openai_api_key: OpenAI API key for GPT-5 nano access
            redis_url: Redis connection URL for caching and rate limiting
            rate_limit_per_minute: Maximum requests per minute
            cache_ttl: Cache time-to-live in seconds
            mock_mode: Enable mock mode for testing
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.cache_ttl = cache_ttl
        self.mock_mode = mock_mode

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()

        # Configure logging
        logging.basicConfig(level=getattr(logging, log_level.upper()))
        self.logger = structlog.get_logger("gpt5_integration")

        # Email section configurations
        self.section_configs = {
            EmailSectionType.EDITORIAL_PICKS: {
                "job_count": 5,
                "style": "curated",
                "focus": "quality"
            },
            EmailSectionType.TOP_RECOMMENDATIONS: {
                "job_count": 5,
                "style": "personalized",
                "focus": "match_score"
            },
            EmailSectionType.PERSONALIZED_PICKS: {
                "job_count": 10,
                "style": "preference_based",
                "focus": "user_history"
            },
            EmailSectionType.NEW_ARRIVALS: {
                "job_count": 10,
                "style": "fresh",
                "focus": "recency"
            },
            EmailSectionType.POPULAR_JOBS: {
                "job_count": 5,
                "style": "trending",
                "focus": "popularity"
            },
            EmailSectionType.YOU_MIGHT_LIKE: {
                "job_count": 5,
                "style": "discovery",
                "focus": "exploration"
            }
        }

    async def initialize(self):
        """Initialize Redis connection and rate limiter"""
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            self.rate_limiter = RateLimiter(self.redis)
            await self.logger.ainfo("Service initialized successfully")
        except Exception as e:
            await self.logger.aerror("Failed to initialize service", error=str(e))
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

    def _generate_cache_key(self, user_id: int, job_matches: Dict[EmailSectionType, List[JobMatch]], language: EmailLanguage) -> str:
        """Generate cache key for email content"""
        # Create deterministic hash of job matches
        jobs_data = {}
        for section_type, jobs in job_matches.items():
            jobs_data[section_type.value] = [
                {"id": job.job_id, "title": job.title, "score": job.match_score}
                for job in jobs
            ]

        content_hash = hashlib.md5(
            json.dumps(jobs_data, sort_keys=True).encode()
        ).hexdigest()

        return f"email_content:{user_id}:{language.value}:{content_hash}"

    async def _get_cached_content(self, cache_key: str) -> Optional[EmailContent]:
        """Retrieve cached email content"""
        if not self.redis:
            return None

        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return EmailContent(**data)
        except Exception as e:
            await self.logger.awarn("Cache retrieval failed", error=str(e))

        return None

    async def _cache_content(self, cache_key: str, content: EmailContent):
        """Cache email content"""
        if not self.redis:
            return

        try:
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                content.json()
            )
        except Exception as e:
            await self.logger.awarn("Cache storage failed", error=str(e))

    async def _check_rate_limit(self, user_id: int) -> bool:
        """Check rate limit for user"""
        if not self.rate_limiter:
            return True

        rate_key = f"rate_limit:user:{user_id}"
        return await self.rate_limiter.check_limit(rate_key)

    async def _generate_subject_line(
        self,
        user_profile: UserProfile,
        job_counts: Dict[EmailSectionType, int],
        language: EmailLanguage
    ) -> str:
        """Generate personalized email subject line"""
        if self.mock_mode:
            return self._mock_subject_line(user_profile.name, language)

        total_jobs = sum(job_counts.values())

        # Subject line prompts by language
        prompts = {
            EmailLanguage.JAPANESE: f"""
あなたは求人情報メール配信システムの件名作成の専門家です。
以下の情報を基に、魅力的で個人的な件名を作成してください：

ユーザー名: {user_profile.name}
総求人数: {total_jobs}件
言語: 日本語

要件:
- 30文字以内
- 個人的で親しみやすい
- 開封率を高める工夫
- 数字を効果的に使用
- 緊急性や特別感を演出

例: "{user_profile.name}さん限定✨{total_jobs}件の厳選求人をお届け"

件名のみを出力してください。
""",
            EmailLanguage.ENGLISH: f"""
You are an expert at creating compelling email subject lines for job recommendation emails.
Create an engaging, personalized subject line based on the following information:

User name: {user_profile.name}
Total jobs: {total_jobs}
Language: English

Requirements:
- Maximum 50 characters
- Personal and friendly tone
- Optimized for high open rates
- Use numbers effectively
- Create urgency or exclusivity

Example: "{user_profile.name}, {total_jobs} perfect jobs picked for you!"

Output only the subject line.
"""
        }

        try:
            response = await self._call_gpt5_nano(
                prompts[language],
                max_tokens=100,
                temperature=0.8
            )

            subject = response.strip().strip('"').strip("'")
            return subject

        except Exception as e:
            await self.logger.awarn("Subject generation failed, using fallback", error=str(e))
            return self._fallback_subject_line(user_profile.name, total_jobs, language)

    async def _generate_section_content(
        self,
        section_type: EmailSectionType,
        user_profile: UserProfile,
        job_matches: List[JobMatch],
        language: EmailLanguage
    ) -> EmailSection:
        """Generate content for a specific email section"""
        if self.mock_mode:
            return self._mock_section_content(section_type, job_matches, language)

        config = self.section_configs[section_type]
        section_names = self._get_section_names(language)

        # Create detailed prompt for GPT-5 nano
        prompt = self._build_section_prompt(
            section_type, user_profile, job_matches, language, config
        )

        try:
            response = await self._call_gpt5_nano(
                prompt,
                max_tokens=800,
                temperature=0.7
            )

            # Parse structured response
            content = self._parse_section_response(response, section_type, language)
            content.generated_at = datetime.now()
            content.generation_metadata = {
                "model": GPT5_NANO_MODEL,
                "config": config,
                "job_count": len(job_matches),
                "user_preferences": user_profile.job_preferences
            }

            return content

        except Exception as e:
            await self.logger.awarn(
                "Section generation failed, using fallback",
                section=section_type.value,
                error=str(e)
            )
            return self._fallback_section_content(section_type, job_matches, language)

    def _build_section_prompt(
        self,
        section_type: EmailSectionType,
        user_profile: UserProfile,
        job_matches: List[JobMatch],
        language: EmailLanguage,
        config: Dict[str, Any]
    ) -> str:
        """Build detailed prompt for section content generation"""
        job_details = []
        for job in job_matches:
            job_details.append(
                f"- {job.title} at {job.company} ({job.location}) "
                f"- Match: {job.match_score:.1f}% - {job.description[:100]}..."
            )

        section_names = self._get_section_names(language)
        section_title = section_names[section_type]

        if language == EmailLanguage.JAPANESE:
            return f"""
あなたは求人情報メール作成の専門家です。
以下の情報を基に、魅力的なメールセクションを作成してください：

セクション: {section_title}
ユーザー: {user_profile.name}さん
職歴レベル: {user_profile.experience_level or '情報なし'}
希望勤務地: {user_profile.location or '情報なし'}
スタイル: {config['style']}
フォーカス: {config['focus']}

求人一覧:
{chr(10).join(job_details)}

出力形式（JSON）:
{{
    "title": "セクションタイトル（魅力的で簡潔）",
    "intro_text": "セクション導入文（ユーザーへの呼びかけ、50文字程度）",
    "job_descriptions": ["求人1の魅力的な説明文", "求人2の説明文", ...],
    "call_to_action": "行動促進文（応募を促す一言）"
}}

要件:
- ユーザーに親しみやすく、個人的な文体
- 各求人の魅力的なポイントを強調
- 簡潔で読みやすい文章
- セクションの特徴を活かした内容
"""
        else:
            return f"""
You are an expert at creating compelling job recommendation email content.
Create an engaging email section based on the following information:

Section: {section_title}
User: {user_profile.name}
Experience Level: {user_profile.experience_level or 'Not specified'}
Preferred Location: {user_profile.location or 'Not specified'}
Style: {config['style']}
Focus: {config['focus']}

Job Listings:
{chr(10).join(job_details)}

Output Format (JSON):
{{
    "title": "Section title (engaging and concise)",
    "intro_text": "Section introduction (personal greeting, ~30 words)",
    "job_descriptions": ["Compelling description for job 1", "Description for job 2", ...],
    "call_to_action": "Action prompt (encourage applications)"
}}

Requirements:
- Personal and friendly tone
- Highlight unique selling points of each job
- Concise and scannable content
- Leverage section characteristics
"""

    async def _call_gpt5_nano(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        retries: int = MAX_RETRIES
    ) -> str:
        """Call GPT-5 nano with retry logic"""
        for attempt in range(retries):
            try:
                response = await self.openai_client.chat.completions.create(
                    model=GPT5_NANO_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=DEFAULT_TIMEOUT
                )

                # Update metrics
                if hasattr(response, 'usage') and response.usage:
                    self.performance_monitor.metrics["total_tokens_used"] += response.usage.total_tokens

                return response.choices[0].message.content.strip()

            except openai.RateLimitError:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise

            except openai.APITimeoutError:
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise

            except Exception as e:
                await self.logger.aerror(
                    "GPT-5 nano API call failed",
                    attempt=attempt,
                    error=str(e)
                )
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise

    def _parse_section_response(self, response: str, section_type: EmailSectionType, language: EmailLanguage) -> EmailSection:
        """Parse GPT-5 nano response into EmailSection object"""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            return EmailSection(
                section_type=section_type,
                title=data.get("title", ""),
                intro_text=data.get("intro_text", ""),
                job_descriptions=data.get("job_descriptions", []),
                call_to_action=data.get("call_to_action", "")
            )

        except Exception as e:
            # Fallback parsing
            lines = response.strip().split('\n')
            return EmailSection(
                section_type=section_type,
                title=lines[0] if lines else "",
                intro_text=lines[1] if len(lines) > 1 else "",
                job_descriptions=lines[2:] if len(lines) > 2 else [],
                call_to_action="今すぐ応募してみましょう！" if language == EmailLanguage.JAPANESE else "Apply now!"
            )

    async def generate_email(
        self,
        user_profile: UserProfile,
        job_matches: Dict[EmailSectionType, List[JobMatch]],
        template_variables: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Generate a complete personalized email for a single user.

        Args:
            user_profile: User profile for personalization
            job_matches: Job matches organized by section type
            template_variables: Additional template variables

        Returns:
            GenerationResult with email content and metadata
        """
        start_time = time.time()

        async with self.performance_monitor.track_request("generate_email", user_profile.user_id):
            # Check rate limit
            if not await self._check_rate_limit(user_profile.user_id):
                return GenerationResult(
                    user_id=user_profile.user_id,
                    status=GenerationStatus.FAILED,
                    error_message="Rate limit exceeded",
                    generation_time_ms=int((time.time() - start_time) * 1000)
                )

            # Check cache
            cache_key = self._generate_cache_key(
                user_profile.user_id,
                job_matches,
                user_profile.preferred_language
            )

            cached_content = await self._get_cached_content(cache_key)
            if cached_content:
                self.performance_monitor.metrics["cache_hits"] += 1
                return GenerationResult(
                    user_id=user_profile.user_id,
                    status=GenerationStatus.CACHED,
                    email_content=cached_content,
                    generation_time_ms=int((time.time() - start_time) * 1000),
                    cache_hit=True
                )

            try:
                # Generate subject line
                job_counts = {section: len(jobs) for section, jobs in job_matches.items()}
                subject = await self._generate_subject_line(
                    user_profile,
                    job_counts,
                    user_profile.preferred_language
                )

                # Generate sections in parallel
                section_tasks = []
                for section_type, jobs in job_matches.items():
                    task = self._generate_section_content(
                        section_type,
                        user_profile,
                        jobs,
                        user_profile.preferred_language
                    )
                    section_tasks.append(task)

                sections = await asyncio.gather(*section_tasks)

                # Generate greeting and closing
                greeting = self._generate_greeting(user_profile)
                introduction = self._generate_introduction(user_profile, job_counts)
                closing = self._generate_closing(user_profile.preferred_language)
                signature = self._generate_signature(user_profile.preferred_language)

                # Create email content
                email_content = EmailContent(
                    user_id=user_profile.user_id,
                    subject=subject,
                    greeting=greeting,
                    introduction=introduction,
                    sections=sections,
                    closing=closing,
                    signature=signature,
                    language=user_profile.preferred_language,
                    generation_metadata={
                        "template_variables": template_variables or {},
                        "generation_time_ms": int((time.time() - start_time) * 1000),
                        "model": GPT5_NANO_MODEL,
                        "mock_mode": self.mock_mode
                    }
                )

                # Cache the result
                await self._cache_content(cache_key, email_content)

                return GenerationResult(
                    user_id=user_profile.user_id,
                    status=GenerationStatus.COMPLETED,
                    email_content=email_content,
                    generation_time_ms=int((time.time() - start_time) * 1000)
                )

            except Exception as e:
                await self.logger.aerror(
                    "Email generation failed",
                    user_id=user_profile.user_id,
                    error=str(e)
                )

                return GenerationResult(
                    user_id=user_profile.user_id,
                    status=GenerationStatus.FAILED,
                    error_message=str(e),
                    generation_time_ms=int((time.time() - start_time) * 1000)
                )

    async def generate_emails_batch(
        self,
        batch_request: BatchGenerationRequest
    ) -> List[GenerationResult]:
        """
        Generate emails for multiple users in batch.

        Args:
            batch_request: Batch generation request with user profiles and job matches

        Returns:
            List of GenerationResult for each user
        """
        await self.logger.ainfo(
            "Starting batch email generation",
            user_count=len(batch_request.user_profiles),
            language=batch_request.language.value
        )

        if batch_request.dry_run:
            await self.logger.ainfo("Dry run mode - no actual generation will occur")
            return [
                GenerationResult(
                    user_id=profile.user_id,
                    status=GenerationStatus.COMPLETED,
                    generation_time_ms=0
                )
                for profile in batch_request.user_profiles
            ]

        # Process users in batches to avoid overwhelming the API
        results = []
        for i in range(0, len(batch_request.user_profiles), BATCH_SIZE):
            batch_users = batch_request.user_profiles[i:i + BATCH_SIZE]

            # Create tasks for parallel processing
            tasks = []
            for user_profile in batch_users:
                user_job_matches = batch_request.job_matches_by_user.get(
                    user_profile.user_id, {}
                )

                task = self.generate_email(
                    user_profile,
                    user_job_matches,
                    batch_request.template_variables
                )
                tasks.append(task)

            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(GenerationResult(
                        user_id=0,  # Unknown user
                        status=GenerationStatus.FAILED,
                        error_message=str(result)
                    ))
                else:
                    results.append(result)

            # Brief pause between batches to respect rate limits
            if i + BATCH_SIZE < len(batch_request.user_profiles):
                await asyncio.sleep(0.5)

        await self.logger.ainfo(
            "Batch email generation completed",
            total_users=len(batch_request.user_profiles),
            successful=len([r for r in results if r.status == GenerationStatus.COMPLETED]),
            failed=len([r for r in results if r.status == GenerationStatus.FAILED])
        )

        return results

    # Helper methods for content generation

    def _generate_greeting(self, user_profile: UserProfile) -> str:
        """Generate personalized greeting"""
        if user_profile.preferred_language == EmailLanguage.JAPANESE:
            return f"{user_profile.name}さん、こんにちは！"
        else:
            return f"Hello {user_profile.name}!"

    def _generate_introduction(
        self,
        user_profile: UserProfile,
        job_counts: Dict[EmailSectionType, int]
    ) -> str:
        """Generate email introduction"""
        total_jobs = sum(job_counts.values())

        if user_profile.preferred_language == EmailLanguage.JAPANESE:
            return (
                f"今週も{user_profile.name}さんにぴったりの求人情報をお届けします。"
                f"厳選された{total_jobs}件の求人をセクション別にご紹介いたします。"
            )
        else:
            return (
                f"We've carefully curated {total_jobs} job opportunities just for you this week. "
                f"Each section features jobs tailored to your preferences and career goals."
            )

    def _generate_closing(self, language: EmailLanguage) -> str:
        """Generate email closing"""
        if language == EmailLanguage.JAPANESE:
            return (
                "気になる求人がございましたら、ぜひお早めにご応募ください。"
                "あなたの転職活動を心から応援しています！"
            )
        else:
            return (
                "If any of these opportunities interest you, we encourage you to apply soon. "
                "We're here to support your career journey every step of the way!"
            )

    def _generate_signature(self, language: EmailLanguage) -> str:
        """Generate email signature"""
        if language == EmailLanguage.JAPANESE:
            return "バイト求人マッチングチーム一同"
        else:
            return "The Job Matching Team"

    def _get_section_names(self, language: EmailLanguage) -> Dict[EmailSectionType, str]:
        """Get localized section names"""
        if language == EmailLanguage.JAPANESE:
            return {
                EmailSectionType.EDITORIAL_PICKS: "編集部おすすめ",
                EmailSectionType.TOP_RECOMMENDATIONS: "あなたへのおすすめTOP5",
                EmailSectionType.PERSONALIZED_PICKS: "パーソナライズド求人",
                EmailSectionType.NEW_ARRIVALS: "新着求人",
                EmailSectionType.POPULAR_JOBS: "人気の求人",
                EmailSectionType.YOU_MIGHT_LIKE: "こんな求人はいかがですか？"
            }
        else:
            return {
                EmailSectionType.EDITORIAL_PICKS: "Editorial Picks",
                EmailSectionType.TOP_RECOMMENDATIONS: "Top 5 Recommendations",
                EmailSectionType.PERSONALIZED_PICKS: "Personalized Picks",
                EmailSectionType.NEW_ARRIVALS: "New Arrivals",
                EmailSectionType.POPULAR_JOBS: "Popular Jobs",
                EmailSectionType.YOU_MIGHT_LIKE: "You Might Also Like"
            }

    # Fallback methods for when GPT-5 nano is unavailable

    def _fallback_subject_line(self, name: str, job_count: int, language: EmailLanguage) -> str:
        """Fallback subject line generation"""
        if language == EmailLanguage.JAPANESE:
            return f"{name}さんへ💼{job_count}件の新着求人をお届け"
        else:
            return f"{name}, {job_count} new job matches for you!"

    def _fallback_section_content(
        self,
        section_type: EmailSectionType,
        job_matches: List[JobMatch],
        language: EmailLanguage
    ) -> EmailSection:
        """Fallback section content generation"""
        section_names = self._get_section_names(language)

        if language == EmailLanguage.JAPANESE:
            intro_text = "こちらの求人をチェックしてみてください："
            call_to_action = "詳細を見る・応募する"
            job_descriptions = [
                f"{job.title}（{job.company}）- {job.location}"
                for job in job_matches
            ]
        else:
            intro_text = "Check out these opportunities:"
            call_to_action = "View details & apply"
            job_descriptions = [
                f"{job.title} at {job.company} - {job.location}"
                for job in job_matches
            ]

        return EmailSection(
            section_type=section_type,
            title=section_names[section_type],
            intro_text=intro_text,
            job_descriptions=job_descriptions,
            call_to_action=call_to_action,
            generation_metadata={"fallback": True}
        )

    # Mock methods for testing

    def _mock_subject_line(self, name: str, language: EmailLanguage) -> str:
        """Mock subject line for testing"""
        if language == EmailLanguage.JAPANESE:
            return f"[MOCK] {name}さんへの求人情報"
        else:
            return f"[MOCK] Job recommendations for {name}"

    def _mock_section_content(
        self,
        section_type: EmailSectionType,
        job_matches: List[JobMatch],
        language: EmailLanguage
    ) -> EmailSection:
        """Mock section content for testing"""
        section_names = self._get_section_names(language)

        return EmailSection(
            section_type=section_type,
            title=f"[MOCK] {section_names[section_type]}",
            intro_text="This is mock content for testing.",
            job_descriptions=[f"Mock job description {i+1}" for i in range(len(job_matches))],
            call_to_action="Mock call to action",
            generation_metadata={"mock": True}
        )

    # Public utility methods

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_monitor.get_metrics()

    async def clear_cache(self, user_id: Optional[int] = None):
        """Clear cache for specific user or all users"""
        if not self.redis:
            return

        if user_id:
            pattern = f"email_content:{user_id}:*"
        else:
            pattern = "email_content:*"

        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
            await self.logger.ainfo(f"Cleared {len(keys)} cache entries", pattern=pattern)

    async def validate_job_matches(
        self,
        job_matches: Dict[EmailSectionType, List[JobMatch]]
    ) -> Dict[str, Any]:
        """Validate job matches structure and content"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "section_counts": {}
        }

        # Check that all 6 sections are present
        expected_sections = set(EmailSectionType)
        provided_sections = set(job_matches.keys())

        missing_sections = expected_sections - provided_sections
        if missing_sections:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Missing sections: {[s.value for s in missing_sections]}"
            )

        # Check job counts per section
        for section_type, jobs in job_matches.items():
            expected_count = self.section_configs[section_type]["job_count"]
            actual_count = len(jobs)
            validation_result["section_counts"][section_type.value] = actual_count

            if actual_count != expected_count:
                validation_result["warnings"].append(
                    f"Section {section_type.value}: expected {expected_count} jobs, got {actual_count}"
                )

        return validation_result


# Usage example and factory function
async def create_email_generation_service(
    openai_api_key: str,
    redis_url: str = "redis://localhost:6379/0",
    mock_mode: bool = False
) -> EmailGenerationService:
    """
    Factory function to create and initialize EmailGenerationService.

    Args:
        openai_api_key: OpenAI API key
        redis_url: Redis connection URL
        mock_mode: Enable mock mode for testing

    Returns:
        Initialized EmailGenerationService
    """
    service = EmailGenerationService(
        openai_api_key=openai_api_key,
        redis_url=redis_url,
        mock_mode=mock_mode
    )

    await service.initialize()
    return service


# Example usage:
"""
# Initialize service
service = await create_email_generation_service(
    openai_api_key="your-api-key",
    redis_url="redis://localhost:6379/0"
)

# Create user profile
user_profile = UserProfile(
    user_id=1,
    name="田中太郎",
    email="tanaka@example.com",
    preferred_language=EmailLanguage.JAPANESE,
    location="東京都",
    job_preferences={"industry": "IT", "work_type": "full_time"}
)

# Define job matches for each section
job_matches = {
    EmailSectionType.EDITORIAL_PICKS: [
        JobMatch(job_id=1, title="Software Engineer", company="Tech Corp", location="Tokyo", match_score=95.0),
        # ... more jobs
    ],
    # ... other sections
}

# Generate email
result = await service.generate_email(user_profile, job_matches)

if result.status == GenerationStatus.COMPLETED:
    print(f"Subject: {result.email_content.subject}")
    for section in result.email_content.sections:
        print(f"\n{section.title}:")
        print(section.intro_text)
        for desc in section.job_descriptions:
            print(f"- {desc}")

# Cleanup
await service.close()
"""