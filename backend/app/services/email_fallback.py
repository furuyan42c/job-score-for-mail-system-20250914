"""
Email Generation Fallback Service

This service provides template-based email generation when GPT-5 nano is unavailable.
It generates personalized emails using predefined templates and job matching data.

Author: Claude Code Assistant
Created: 2025-09-18
Version: 1.0.0
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

from app.services.gpt5_integration import (
    UserProfile, JobMatch, EmailContent, EmailSection,
    GenerationStatus, GenerationResult
)

# ============================================================================
# LOGGER CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class FallbackReason(Enum):
    """Reasons for using fallback email generation."""
    GPT5_API_ERROR = "gpt5_api_error"
    GPT5_TIMEOUT = "gpt5_timeout"
    GPT5_QUOTA_EXCEEDED = "gpt5_quota_exceeded"
    GPT5_UNAVAILABLE = "gpt5_unavailable"
    COST_OPTIMIZATION = "cost_optimization"
    TESTING_MODE = "testing_mode"

class TemplateStyle(Enum):
    """Email template styles."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    URGENT = "urgent"
    FRIENDLY = "friendly"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class FallbackConfig:
    """Configuration for fallback email generation."""
    language: str = "ja"
    style: TemplateStyle = TemplateStyle.PROFESSIONAL
    include_personalization: bool = True
    max_jobs_per_section: int = 10
    enable_dynamic_content: bool = True
    randomize_templates: bool = True
    add_performance_note: bool = False

@dataclass
class TemplateVariables:
    """Variables available for template substitution."""
    user_name: str
    user_location: str
    current_date: str
    current_time: str
    total_job_count: int
    top_match_score: float
    user_skills: List[str]
    preferred_locations: List[str]
    salary_range: str
    custom_greeting: str

# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

class EmailTemplates:
    """Predefined email templates for fallback generation."""

    # Japanese Templates
    JAPANESE_SUBJECTS = {
        TemplateStyle.PROFESSIONAL: [
            "{user_name}様へ - 本日の厳選求人{total_job_count}件をご紹介",
            "あなたにピッタリの求人{total_job_count}件が見つかりました",
            "{user_name}様専用 - 今週のおすすめ求人情報",
            "新着求人情報 - マッチ度{top_match_score}%の案件をご確認ください",
            "【求人マッチング】{user_location}エリアの最新案件をお届け"
        ],
        TemplateStyle.CASUAL: [
            "こんにちは！今日のオススメ求人{total_job_count}件です♪",
            "{user_name}さんにピッタリの仕事を見つけました！",
            "お疲れさまです！新しい求人情報をお届け✨",
            "良い案件が{total_job_count}件入ってきました！",
            "今日も素敵な求人をご紹介します🌟"
        ],
        TemplateStyle.URGENT: [
            "【急募】{user_name}様向け高給与案件{total_job_count}件",
            "お見逃しなく！今すぐ応募可能な求人情報",
            "【期間限定】{user_location}エリア限定求人のご案内",
            "締切間近！マッチ度{top_match_score}%の求人をチェック",
            "【今日まで】特別紹介案件{total_job_count}件"
        ]
    }

    JAPANESE_GREETINGS = {
        TemplateStyle.PROFESSIONAL: [
            "{user_name}様、いつもお世話になっております。",
            "{user_name}様、毎日お疲れさまです。",
            "拝啓　{user_name}様、いかがお過ごしでしょうか。"
        ],
        TemplateStyle.CASUAL: [
            "{user_name}さん、こんにちは！",
            "お疲れさまです、{user_name}さん！",
            "{user_name}さん、今日も一日お疲れさまでした♪"
        ],
        TemplateStyle.URGENT: [
            "{user_name}様、重要なご案内です。",
            "緊急のお知らせ - {user_name}様",
            "{user_name}様、特別なご案内があります。"
        ]
    }

    JAPANESE_SECTION_TEMPLATES = {
        "editorial_picks": {
            "title": "🎯 編集部厳選求人",
            "description": "私たちが{user_name}様に特におすすめしたい案件です。",
            "job_templates": [
                "《注目》{company_name}での{job_title} - 時給{salary_range}円",
                "★編集部イチオシ★ {job_title}《{company_name}》",
                "【厳選】{company_name} | {job_title} | {location}"
            ]
        },
        "top_recommendations": {
            "title": "🏆 あなたへのTOP5",
            "description": "マッチング度の高い順にご紹介します。",
            "job_templates": [
                "第{rank}位《マッチ度{match_score}%》{job_title} @ {company_name}",
                "ランキング{rank}位 | {job_title} | {company_name} | {salary_range}円",
                "TOP{rank} 🌟 {company_name}の{job_title}案件"
            ]
        },
        "trending_jobs": {
            "title": "📈 人気上昇中の求人",
            "description": "多くの方が注目している話題の案件です。",
            "job_templates": [
                "🔥話題沸騰🔥 {company_name}での{job_title}",
                "人気急上昇！{job_title}《{location}》",
                "注目度UP ↗️ {company_name} | {job_title}"
            ]
        },
        "near_you": {
            "title": "📍 {user_location}周辺の求人",
            "description": "あなたのお住まいの近くで見つけた案件です。",
            "job_templates": [
                "🚶‍♂️徒歩圏内 {company_name}での{job_title}",
                "近場で発見！{job_title} @ {location}",
                "通勤楽々♪ {company_name} | {job_title}"
            ]
        },
        "high_paying": {
            "title": "💰 高収入案件",
            "description": "収入アップを目指すあなたにおすすめです。",
            "job_templates": [
                "💎高時給💎 {job_title} - 時給{salary_range}円",
                "収入UP！{company_name}での{job_title}",
                "💰稼げる💰 {job_title}《{company_name}》"
            ]
        },
        "new_arrivals": {
            "title": "🆕 新着求人",
            "description": "最新の求人情報をいち早くお届けします。",
            "job_templates": [
                "✨NEW✨ {company_name}での{job_title}",
                "新着！{job_title} @ {location}",
                "🆕本日公開🆕 {company_name} | {job_title}"
            ]
        }
    }

    # English Templates
    ENGLISH_SUBJECTS = {
        TemplateStyle.PROFESSIONAL: [
            "Your Personalized Job Recommendations - {total_job_count} Matches",
            "Weekly Job Alert for {user_name} - {total_job_count} New Opportunities",
            "Top-Rated Job Matches in {user_location} Area",
            "Professional Opportunities Curated for You",
            "Your Career Update - {total_job_count} Quality Matches"
        ],
        TemplateStyle.CASUAL: [
            "Hey {user_name}! {total_job_count} awesome jobs just for you 🎯",
            "Great news! Found {total_job_count} perfect matches ✨",
            "Your daily dose of amazing opportunities!",
            "Jobs you'll love - handpicked for {user_name}",
            "Fresh opportunities are here! 🌟"
        ]
    }

    ENGLISH_GREETINGS = {
        TemplateStyle.PROFESSIONAL: [
            "Dear {user_name},",
            "Hello {user_name},",
            "Good day, {user_name},"
        ],
        TemplateStyle.CASUAL: [
            "Hi {user_name}!",
            "Hey there, {user_name}!",
            "Hello {user_name}! 👋"
        ]
    }

# ============================================================================
# EMAIL FALLBACK SERVICE
# ============================================================================

class EmailFallbackService:
    """
    Fallback email generation service using templates.

    This service generates emails when GPT-5 is unavailable, using
    predefined templates with personalization and job matching data.
    """

    def __init__(self, config: Optional[FallbackConfig] = None):
        """Initialize the fallback service with configuration."""
        self.config = config or FallbackConfig()
        self.templates = EmailTemplates()

        logger.info(f"EmailFallbackService initialized with language: {self.config.language}")

    async def generate_email(
        self,
        user_profile: UserProfile,
        job_matches: List[JobMatch],
        reason: FallbackReason = FallbackReason.GPT5_UNAVAILABLE,
        style: Optional[TemplateStyle] = None
    ) -> GenerationResult:
        """
        Generate a fallback email using templates.

        Args:
            user_profile: User information for personalization
            job_matches: List of job matches to include
            reason: Reason for using fallback
            style: Template style override

        Returns:
            GenerationResult with generated email content
        """
        start_time = datetime.now()

        try:
            # Use provided style or default from config
            email_style = style or self.config.style

            # Generate template variables
            template_vars = self._create_template_variables(user_profile, job_matches)

            # Generate email content
            email_content = await self._generate_email_content(
                user_profile, job_matches, template_vars, email_style
            )

            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Fallback email generated successfully for user {user_profile.user_id} "
                f"in {generation_time:.2f}s (reason: {reason.value})"
            )

            return GenerationResult(
                status=GenerationStatus.COMPLETED,
                email_content=email_content,
                generation_time_ms=int(generation_time * 1000),
                tokens_used=0,  # Templates don't use tokens
                cache_hit=False,
                fallback_used=True,
                metadata={
                    "fallback_reason": reason.value,
                    "template_style": email_style.value,
                    "language": self.config.language,
                    "total_jobs": len(job_matches),
                    "generation_method": "template_based"
                }
            )

        except Exception as e:
            logger.error(f"Fallback email generation failed: {str(e)}", exc_info=True)

            # Return error result with basic template
            return GenerationResult(
                status=GenerationStatus.FAILED,
                error_message=f"Fallback generation failed: {str(e)}",
                generation_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                fallback_used=True,
                metadata={
                    "fallback_reason": reason.value,
                    "error_type": type(e).__name__
                }
            )

    async def generate_batch_emails(
        self,
        user_profiles: List[UserProfile],
        job_matches_list: List[List[JobMatch]],
        reason: FallbackReason = FallbackReason.GPT5_UNAVAILABLE
    ) -> List[GenerationResult]:
        """
        Generate multiple fallback emails in parallel.

        Args:
            user_profiles: List of user profiles
            job_matches_list: List of job matches for each user
            reason: Reason for using fallback

        Returns:
            List of generation results
        """
        if len(user_profiles) != len(job_matches_list):
            raise ValueError("user_profiles and job_matches_list must have same length")

        logger.info(f"Starting batch fallback generation for {len(user_profiles)} users")

        # Generate emails concurrently
        tasks = [
            self.generate_email(profile, matches, reason)
            for profile, matches in zip(user_profiles, job_matches_list)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch generation failed for user {i}: {str(result)}")
                processed_results.append(GenerationResult(
                    status=GenerationStatus.FAILED,
                    error_message=str(result),
                    fallback_used=True,
                    metadata={"batch_index": i, "fallback_reason": reason.value}
                ))
            else:
                processed_results.append(result)

        success_count = sum(1 for r in processed_results if r.status == GenerationStatus.COMPLETED)
        logger.info(f"Batch fallback generation completed: {success_count}/{len(user_profiles)} successful")

        return processed_results

    def _create_template_variables(
        self,
        user_profile: UserProfile,
        job_matches: List[JobMatch]
    ) -> TemplateVariables:
        """Create template variables for substitution."""
        now = datetime.now()

        # Calculate top match score
        top_match_score = max((job.match_score for job in job_matches), default=0.0)

        # Extract salary range
        salary_ranges = [job.salary_range for job in job_matches if job.salary_range]
        salary_range = salary_ranges[0] if salary_ranges else "応相談"

        return TemplateVariables(
            user_name=user_profile.name or "お客様",
            user_location=user_profile.location or "お近く",
            current_date=now.strftime("%Y年%m月%d日"),
            current_time=now.strftime("%H:%M"),
            total_job_count=len(job_matches),
            top_match_score=round(top_match_score * 100, 1),
            user_skills=user_profile.skills[:3],  # Top 3 skills
            preferred_locations=user_profile.preferred_locations[:2],  # Top 2 locations
            salary_range=salary_range,
            custom_greeting=self._generate_custom_greeting(user_profile)
        )

    def _generate_custom_greeting(self, user_profile: UserProfile) -> str:
        """Generate a personalized greeting based on user profile."""
        if self.config.language == "ja":
            if user_profile.age and user_profile.age < 25:
                return f"{user_profile.name or 'お客'}様、今日も一日お疲れさまです！"
            else:
                return f"{user_profile.name or 'お客'}様、いつもお世話になっております。"
        else:
            return f"Hello {user_profile.name or 'there'}!"

    async def _generate_email_content(
        self,
        user_profile: UserProfile,
        job_matches: List[JobMatch],
        template_vars: TemplateVariables,
        style: TemplateStyle
    ) -> EmailContent:
        """Generate complete email content using templates."""

        # Generate subject
        subject = self._generate_subject(template_vars, style)

        # Generate sections
        sections = await self._generate_sections(user_profile, job_matches, template_vars, style)

        # Generate greeting and footer
        greeting = self._generate_greeting(template_vars, style)
        footer = self._generate_footer(user_profile, template_vars)

        return EmailContent(
            subject=subject,
            greeting=greeting,
            sections=sections,
            footer=footer,
            personalization_note=self._generate_personalization_note(user_profile, template_vars),
            language=self.config.language,
            generated_at=datetime.now(),
            template_version="fallback_v1.0",
            total_jobs=len(job_matches)
        )

    def _generate_subject(self, template_vars: TemplateVariables, style: TemplateStyle) -> str:
        """Generate email subject using templates."""
        if self.config.language == "ja":
            subjects = self.templates.JAPANESE_SUBJECTS[style]
        else:
            subjects = self.templates.ENGLISH_SUBJECTS[style]

        # Select random template if randomization is enabled
        if self.config.randomize_templates:
            subject_template = random.choice(subjects)
        else:
            subject_template = subjects[0]

        return subject_template.format(**asdict(template_vars))

    def _generate_greeting(self, template_vars: TemplateVariables, style: TemplateStyle) -> str:
        """Generate email greeting using templates."""
        if self.config.language == "ja":
            greetings = self.templates.JAPANESE_GREETINGS[style]
        else:
            greetings = self.templates.ENGLISH_GREETINGS[style]

        if self.config.randomize_templates:
            greeting_template = random.choice(greetings)
        else:
            greeting_template = greetings[0]

        return greeting_template.format(**asdict(template_vars))

    async def _generate_sections(
        self,
        user_profile: UserProfile,
        job_matches: List[JobMatch],
        template_vars: TemplateVariables,
        style: TemplateStyle
    ) -> List[EmailSection]:
        """Generate all email sections using templates."""

        # Define section distribution (total 40 jobs)
        section_configs = [
            ("editorial_picks", 5),
            ("top_recommendations", 5),
            ("trending_jobs", 10),
            ("near_you", 10),
            ("high_paying", 5),
            ("new_arrivals", 5)
        ]

        sections = []
        job_index = 0

        for section_key, job_count in section_configs:
            # Get jobs for this section
            section_jobs = job_matches[job_index:job_index + job_count]
            job_index += job_count

            if not section_jobs:
                continue

            # Generate section
            section = await self._generate_section(
                section_key, section_jobs, template_vars, style, user_profile
            )
            sections.append(section)

        return sections

    async def _generate_section(
        self,
        section_key: str,
        jobs: List[JobMatch],
        template_vars: TemplateVariables,
        style: TemplateStyle,
        user_profile: UserProfile
    ) -> EmailSection:
        """Generate a single email section."""

        if self.config.language == "ja":
            section_template = self.templates.JAPANESE_SECTION_TEMPLATES[section_key]
        else:
            # For now, use Japanese templates for all
            section_template = self.templates.JAPANESE_SECTION_TEMPLATES[section_key]

        # Generate section title and description
        title = section_template["title"].format(**asdict(template_vars))
        description = section_template["description"].format(**asdict(template_vars))

        # Generate job items
        job_templates = section_template["job_templates"]
        job_items = []

        for i, job in enumerate(jobs):
            if self.config.randomize_templates:
                job_template = random.choice(job_templates)
            else:
                job_template = job_templates[i % len(job_templates)]

            # Create job-specific variables
            job_vars = {
                "rank": i + 1,
                "company_name": job.company_name,
                "job_title": job.title,
                "location": job.location,
                "salary_range": job.salary_range or "応相談",
                "match_score": round(job.match_score * 100, 1),
                **asdict(template_vars)
            }

            job_item = job_template.format(**job_vars)
            job_items.append(job_item)

        return EmailSection(
            section_type=section_key,
            title=title,
            description=description,
            job_items=job_items,
            job_count=len(jobs),
            metadata={
                "template_used": True,
                "randomized": self.config.randomize_templates,
                "style": style.value
            }
        )

    def _generate_footer(self, user_profile: UserProfile, template_vars: TemplateVariables) -> str:
        """Generate email footer."""
        if self.config.language == "ja":
            footer_lines = [
                "今回ご紹介した求人情報は、あなたのプロフィールを基に厳選いたしました。",
                "より詳しい情報や応募については、各求人をクリックしてご確認ください。",
                "",
                "引き続き、あなたに最適な求人情報をお届けいたします。",
                "何かご不明な点がございましたら、お気軽にお問い合わせください。",
                "",
                "────────────────────────────",
                "このメールは自動配信されています。",
                "配信停止をご希望の場合は、こちらから設定を変更してください。"
            ]
        else:
            footer_lines = [
                "These job recommendations were carefully selected based on your profile.",
                "Click on each job for more details and to apply.",
                "",
                "We'll continue to send you the best job matches.",
                "If you have any questions, please don't hesitate to contact us.",
                "",
                "────────────────────────────",
                "This email was sent automatically.",
                "To unsubscribe, please update your preferences here."
            ]

        if self.config.add_performance_note:
            footer_lines.insert(0, "※ このメールはテンプレートベースで生成されました。")

        return "\n".join(footer_lines)

    def _generate_personalization_note(
        self,
        user_profile: UserProfile,
        template_vars: TemplateVariables
    ) -> str:
        """Generate personalization explanation."""
        if self.config.language == "ja":
            return (
                f"このメールは{template_vars.user_name}様の興味・経験"
                f"（{', '.join(template_vars.user_skills[:2])}など）を考慮して作成されています。"
            )
        else:
            return (
                f"This email was personalized based on your interests and experience "
                f"in {', '.join(template_vars.user_skills[:2])}."
            )

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def create_fallback_service(
    language: str = "ja",
    style: TemplateStyle = TemplateStyle.PROFESSIONAL,
    **kwargs
) -> EmailFallbackService:
    """
    Create and configure an email fallback service.

    Args:
        language: Email language ("ja" or "en")
        style: Template style
        **kwargs: Additional configuration options

    Returns:
        Configured EmailFallbackService instance
    """
    config = FallbackConfig(
        language=language,
        style=style,
        **kwargs
    )

    return EmailFallbackService(config)

def get_fallback_reason_from_error(error: Exception) -> FallbackReason:
    """
    Determine appropriate fallback reason from error type.

    Args:
        error: Exception that triggered fallback

    Returns:
        Appropriate FallbackReason
    """
    error_str = str(error).lower()

    if "timeout" in error_str:
        return FallbackReason.GPT5_TIMEOUT
    elif "quota" in error_str or "limit" in error_str:
        return FallbackReason.GPT5_QUOTA_EXCEEDED
    elif "api" in error_str or "connection" in error_str:
        return FallbackReason.GPT5_API_ERROR
    else:
        return FallbackReason.GPT5_UNAVAILABLE

# ============================================================================
# TESTING UTILITIES
# ============================================================================

async def test_fallback_generation(
    user_count: int = 3,
    jobs_per_user: int = 40
) -> List[GenerationResult]:
    """
    Test fallback email generation with sample data.

    Args:
        user_count: Number of test users
        jobs_per_user: Number of jobs per user

    Returns:
        List of generation results
    """
    # Create test service
    service = await create_fallback_service(
        language="ja",
        style=TemplateStyle.PROFESSIONAL,
        randomize_templates=True
    )

    # Generate test data
    test_users = []
    test_jobs_list = []

    for i in range(user_count):
        # Create test user
        user = UserProfile(
            user_id=f"test_user_{i}",
            name=f"テストユーザー{i+1}",
            location=f"東京都{['渋谷区', '新宿区', '港区'][i % 3]}",
            age=25 + i * 5,
            skills=[f"スキル{j}" for j in range(1, 4)],
            preferred_locations=[f"エリア{j}" for j in range(1, 3)]
        )
        test_users.append(user)

        # Create test jobs
        jobs = []
        for j in range(jobs_per_user):
            job = JobMatch(
                job_id=f"job_{i}_{j}",
                title=f"職種{j+1}",
                company_name=f"企業{j+1}",
                location=f"勤務地{j+1}",
                salary_range=f"{1000 + j*50}-{1200 + j*50}",
                match_score=(90 - j*2) / 100.0,
                description=f"求人説明{j+1}"
            )
            jobs.append(job)
        test_jobs_list.append(jobs)

    # Generate emails
    results = await service.generate_batch_emails(
        test_users,
        test_jobs_list,
        FallbackReason.TESTING_MODE
    )

    logger.info(f"Fallback test completed: {len(results)} emails generated")
    return results

if __name__ == "__main__":
    # Run test when script is executed directly
    import asyncio

    async def main():
        results = await test_fallback_generation()
        for i, result in enumerate(results):
            print(f"\n=== Test User {i+1} ===")
            print(f"Status: {result.status}")
            if result.email_content:
                print(f"Subject: {result.email_content.subject}")
                print(f"Sections: {len(result.email_content.sections)}")
            print(f"Generation Time: {result.generation_time_ms}ms")

    asyncio.run(main())