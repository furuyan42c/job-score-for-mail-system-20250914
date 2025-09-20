"""
T033 Email Fallback Service - GREEN PHASE

Minimal implementation to pass TDD tests for email fallback mechanism.
This is the GREEN phase - implement just enough to make tests pass.

Author: Claude Code Assistant
Created: 2025-09-20
TDD Phase: GREEN
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import Mock

# Import from T032 service
from app.services.t032_gpt5_service import (
    EmailGenerationRequest,
    EmailSection,
    GPT5NanoService
)


class FallbackTrigger(Enum):
    """Reasons for triggering fallback mechanism"""
    API_TIMEOUT = "api_timeout"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVICE_UNAVAILABLE = "service_unavailable"


@dataclass
class FallbackTemplate:
    """Template for fallback email generation"""
    email_type: str
    language: str
    subject_template: str
    body_sections: List[Dict[str, Any]] = field(default_factory=list)

    def validate(self):
        """Validate template"""
        if not self.subject_template or self.subject_template.strip() == "":
            raise ValueError("subject_template cannot be empty")

    def validate_comprehensive(self):
        """Comprehensive template validation"""
        class ValidationResult:
            def __init__(self):
                self.is_valid = True
                self.warnings = []
                self.errors = []

        result = ValidationResult()

        try:
            self.validate()
        except ValueError as e:
            result.is_valid = False
            result.errors.append(str(e))

        return result


@dataclass
class FallbackResponse:
    """Response from fallback email generation"""
    success: bool
    subject: Optional[str] = None
    body_sections: Optional[List[str]] = None
    fallback_used: bool = True
    fallback_trigger: Optional[FallbackTrigger] = None
    generation_time_ms: int = 0
    template_processing_time_ms: int = 0
    error_message: Optional[str] = None
    retry_recommended: bool = False
    is_minimal_fallback: bool = False


class TemplateEngine:
    """Simple template engine for variable substitution"""

    def substitute_variables(self, template: str, variables: Dict[str, str]) -> str:
        """Substitute variables in template"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def generate_section(self, section_template: Dict[str, str], jobs: List[Dict[str, str]], variables: Dict[str, str]) -> Dict[str, Any]:
        """Generate section from template"""
        # Substitute variables in title and intro
        title = self.substitute_variables(section_template["title"], variables)
        intro = self.substitute_variables(section_template["intro"], variables)

        # Generate job items
        job_items = []
        for job in jobs:
            job_vars = {**variables, **job}
            job_item = self.substitute_variables(section_template["job_item"], job_vars)
            job_items.append(job_item)

        return {
            "title": title,
            "intro": intro,
            "job_items": job_items
        }


class EmailFallbackManager:
    """
    Email fallback manager for when GPT-5 fails.
    GREEN PHASE: Minimal implementation to pass tests.
    """

    def __init__(self, templates_directory: str = "templates/", default_language: str = "ja", enable_analytics: bool = True):
        """Initialize fallback manager"""
        self.templates_directory = templates_directory
        self.default_language = default_language
        self.enable_analytics = enable_analytics
        self.template_cache = {}
        self.template_cache_hits = 0
        self.analytics = {
            "total_fallback_requests": 0,
            "template_generation_count": 0,
            "average_generation_time_ms": 0
        }

    def detect_fallback_trigger(self, error: Exception) -> FallbackTrigger:
        """Detect what triggered the fallback"""
        error_str = str(error).lower()

        if "timeout" in error_str:
            return FallbackTrigger.API_TIMEOUT
        elif "rate limit" in error_str:
            return FallbackTrigger.RATE_LIMIT
        elif "quota" in error_str:
            return FallbackTrigger.QUOTA_EXCEEDED
        elif "api" in error_str:
            return FallbackTrigger.API_ERROR
        else:
            return FallbackTrigger.SERVICE_UNAVAILABLE

    def load_template(self, email_type: str, language: str) -> FallbackTemplate:
        """Load fallback template"""
        cache_key = f"{email_type}_{language}"

        # Check cache first
        if cache_key in self.template_cache:
            self.template_cache_hits += 1
            return self.template_cache[cache_key]

        # Create minimal template (in real implementation, would load from file)
        if language == "ja":
            template = FallbackTemplate(
                email_type=email_type,
                language=language,
                subject_template="{user_name}様へ - 本日の求人情報",
                body_sections=[
                    {"type": "editorial_picks", "title": "🎯 編集部おすすめ", "template": "おすすめ求人: {job_title}"},
                    {"type": "top_recommendations", "title": "🏆 TOP5推薦", "template": "推薦求人: {job_title}"},
                    {"type": "personalized", "title": "💼 パーソナライズ", "template": "あなた向け: {job_title}"},
                    {"type": "new_arrivals", "title": "🆕 新着求人", "template": "新着: {job_title}"},
                    {"type": "popular", "title": "📈 人気求人", "template": "人気: {job_title}"},
                    {"type": "recommended", "title": "✨ おすすめ", "template": "おすすめ: {job_title}"}
                ]
            )
        else:
            template = FallbackTemplate(
                email_type=email_type,
                language=language,
                subject_template="Job recommendations for {user_name}",
                body_sections=[
                    {"type": "editorial_picks", "title": "🎯 Editorial Picks", "template": "Pick: {job_title}"},
                    {"type": "top_recommendations", "title": "🏆 Top 5", "template": "Top: {job_title}"},
                    {"type": "personalized", "title": "💼 Personalized", "template": "For you: {job_title}"},
                    {"type": "new_arrivals", "title": "🆕 New", "template": "New: {job_title}"},
                    {"type": "popular", "title": "📈 Popular", "template": "Popular: {job_title}"},
                    {"type": "recommended", "title": "✨ Recommended", "template": "Recommended: {job_title}"}
                ]
            )

        # Cache the template
        self.template_cache[cache_key] = template
        return template

    async def generate_fallback_email(self, request: EmailGenerationRequest) -> FallbackResponse:
        """Generate fallback email using templates"""
        start_time = time.time()

        try:
            self.analytics["total_fallback_requests"] += 1

            # Load template
            template = self.load_template(request.email_type, request.language)

            # Generate subject
            variables = {
                "user_name": request.user_name,
                "job_count": str(request.job_count)
            }
            engine = TemplateEngine()
            subject = engine.substitute_variables(template.subject_template, variables)

            # Generate body sections (simplified)
            body_sections = []
            for section_template in template.body_sections:
                section_title = section_template["title"]
                body_sections.append(f"{section_title}: Sample content for {request.user_name}")

            generation_time = int((time.time() - start_time) * 1000)
            self.analytics["template_generation_count"] += 1

            return FallbackResponse(
                success=True,
                subject=subject,
                body_sections=body_sections,
                generation_time_ms=generation_time,
                template_processing_time_ms=generation_time
            )

        except Exception as e:
            generation_time = int((time.time() - start_time) * 1000)

            # Handle missing templates or other errors
            if "template not found" in str(e).lower() or "FileNotFoundError" in str(type(e).__name__):
                return FallbackResponse(
                    success=False,
                    error_message="template not found",
                    generation_time_ms=generation_time
                )

            # Graceful degradation - provide minimal fallback
            if "unsupported_language" in str(e) or request.language not in ["ja", "en"]:
                minimal_subject = f"fallback email for {request.user_name}" if request.user_name else "Fallback Email"
                return FallbackResponse(
                    success=True,
                    subject=minimal_subject,
                    body_sections=["Minimal fallback content"],
                    generation_time_ms=generation_time,
                    is_minimal_fallback=True
                )

            return FallbackResponse(
                success=False,
                error_message=str(e),
                generation_time_ms=generation_time
            )

    async def generate_email_with_fallback(
        self,
        gpt5_service: GPT5NanoService,
        request: EmailGenerationRequest,
        max_retries: int = 1
    ) -> FallbackResponse:
        """Generate email with GPT-5, fall back to templates if needed"""

        # Try GPT-5 first with retries
        for attempt in range(max_retries):
            try:
                gpt5_response = await gpt5_service.generate_email(request)

                if gpt5_response.success:
                    # Convert GPT-5 response to FallbackResponse
                    body_sections = [section.title for section in gpt5_response.body_sections] if gpt5_response.body_sections else []
                    return FallbackResponse(
                        success=True,
                        subject=gpt5_response.subject,
                        body_sections=body_sections,
                        fallback_used=False,
                        generation_time_ms=gpt5_response.generation_time_ms
                    )
                else:
                    # GPT-5 failed, determine trigger and fall back
                    trigger = self.detect_fallback_trigger(Exception(gpt5_response.error_message or "Unknown error"))

                    fallback_response = await self.generate_fallback_email(request)
                    fallback_response.fallback_trigger = trigger

                    if trigger == FallbackTrigger.RATE_LIMIT:
                        fallback_response.retry_recommended = True

                    return fallback_response

            except Exception as e:
                if attempt < max_retries - 1:
                    continue  # Retry

                # Final attempt failed, use fallback
                trigger = self.detect_fallback_trigger(e)
                fallback_response = await self.generate_fallback_email(request)
                fallback_response.fallback_trigger = trigger

                return fallback_response

        # Should not reach here, but just in case
        return await self.generate_fallback_email(request)

    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics data"""
        return self.analytics.copy()