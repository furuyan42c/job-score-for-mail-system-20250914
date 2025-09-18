#!/usr/bin/env python3
"""
GPT-5 Nano Email Generation Service - Usage Examples

This file demonstrates how to use the EmailGenerationService for:
- Single user email generation
- Batch processing
- Different language support
- Performance monitoring
- Error handling

To run this example:
1. Set environment variables:
   export OPENAI_API_KEY="your-openai-api-key"
   export REDIS_URL="redis://localhost:6379/0"

2. Run the script:
   python examples/gpt5_email_generation_example.py
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, List

from app.services.gpt5_integration import (
    EmailGenerationService,
    create_email_generation_service,
    UserProfile,
    JobMatch,
    EmailSectionType,
    EmailLanguage,
    BatchGenerationRequest,
    GenerationStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_users() -> List[UserProfile]:
    """Create sample user profiles for testing"""
    return [
        UserProfile(
            user_id=1,
            name="田中太郎",
            email="tanaka@example.com",
            preferred_language=EmailLanguage.JAPANESE,
            location="東京都",
            job_preferences={
                "industry": "IT",
                "work_type": "full_time",
                "salary_min": 400000,
                "remote_ok": True
            },
            experience_level="mid_level"
        ),
        UserProfile(
            user_id=2,
            name="佐藤花子",
            email="sato@example.com",
            preferred_language=EmailLanguage.JAPANESE,
            location="大阪府",
            job_preferences={
                "industry": "Marketing",
                "work_type": "part_time",
                "salary_min": 1200
            },
            experience_level="entry_level"
        ),
        UserProfile(
            user_id=3,
            name="John Smith",
            email="john@example.com",
            preferred_language=EmailLanguage.ENGLISH,
            location="Tokyo",
            job_preferences={
                "industry": "Finance",
                "work_type": "full_time",
                "salary_min": 500000
            },
            experience_level="senior_level"
        )
    ]


def create_sample_job_matches() -> Dict[EmailSectionType, List[JobMatch]]:
    """Create sample job matches for the 6-section email structure"""
    return {
        EmailSectionType.EDITORIAL_PICKS: [
            JobMatch(
                job_id=1,
                title="Senior Software Engineer",
                company="TechCorp Japan",
                location="東京都渋谷区",
                salary="年収600-800万円",
                description="最新のクラウド技術を使った大規模システム開発に携わっていただきます。",
                match_score=95.0,
                tags=["Python", "AWS", "Kubernetes"],
                is_new=False,
                is_popular=True
            ),
            JobMatch(
                job_id=2,
                title="フルスタックエンジニア",
                company="スタートアップAI",
                location="東京都港区",
                salary="年収500-700万円",
                description="AI/ML分野での新しいプロダクト開発をお任せします。",
                match_score=92.0,
                tags=["React", "Node.js", "TensorFlow"],
                is_new=True,
                is_popular=False
            ),
            JobMatch(
                job_id=3,
                title="DevOpsエンジニア",
                company="クラウドソリューションズ",
                location="東京都新宿区",
                salary="年収550-750万円",
                description="CI/CDパイプラインの構築・運用をご担当いただきます。",
                match_score=88.0,
                tags=["Docker", "Jenkins", "Terraform"],
                is_new=False,
                is_popular=True
            ),
            JobMatch(
                job_id=4,
                title="プロダクトマネージャー",
                company="モバイルゲーム会社",
                location="東京都品川区",
                salary="年収700-900万円",
                description="ヒットゲームの企画・開発・運営を統括していただきます。",
                match_score=85.0,
                tags=["Product Management", "Unity", "Analytics"],
                is_new=False,
                is_popular=True
            ),
            JobMatch(
                job_id=5,
                title="データサイエンティスト",
                company="ECプラットフォーム",
                location="東京都中央区",
                salary="年収600-800万円",
                description="大規模ECデータの分析・機械学習モデル構築をお願いします。",
                match_score=90.0,
                tags=["Python", "SQL", "Machine Learning"],
                is_new=True,
                is_popular=False
            )
        ],
        EmailSectionType.TOP_RECOMMENDATIONS: [
            JobMatch(
                job_id=6,
                title="Backend Engineer",
                company="FinTech Startup",
                location="東京都千代田区",
                salary="年収550-700万円",
                description="金融系APIの開発・運用をご担当いただきます。",
                match_score=94.0,
                tags=["Go", "PostgreSQL", "API Design"],
                is_new=False,
                is_popular=True,
                application_count=45
            ),
            JobMatch(
                job_id=7,
                title="Frontend Developer",
                company="EdTech Company",
                location="東京都世田谷区",
                salary="年収480-620万円",
                description="教育プラットフォームのUI/UX開発をお任せします。",
                match_score=89.0,
                tags=["React", "TypeScript", "CSS"],
                is_new=True,
                is_popular=False,
                application_count=23
            ),
            JobMatch(
                job_id=8,
                title="Mobile App Developer",
                company="ヘルスケアテック",
                location="東京都目黒区",
                salary="年収520-680万円",
                description="ヘルスケアアプリの開発・改善をご担当いただきます。",
                match_score=87.0,
                tags=["Flutter", "Firebase", "Healthcare"],
                is_new=False,
                is_popular=True,
                application_count=67
            ),
            JobMatch(
                job_id=9,
                title="QA Engineer",
                company="ゲーム開発スタジオ",
                location="東京都杉並区",
                salary="年収420-550万円",
                description="モバイルゲームの品質保証・テスト自動化をお願いします。",
                match_score=82.0,
                tags=["Test Automation", "Selenium", "JIRA"],
                is_new=True,
                is_popular=False,
                application_count=34
            ),
            JobMatch(
                job_id=10,
                title="Infrastructure Engineer",
                company="SaaS企業",
                location="東京都豊島区",
                salary="年収580-720万円",
                description="クラウドインフラの設計・構築・運用をご担当いただきます。",
                match_score=91.0,
                tags=["AWS", "Terraform", "Monitoring"],
                is_new=False,
                is_popular=True,
                application_count=52
            )
        ],
        EmailSectionType.PERSONALIZED_PICKS: [
            JobMatch(
                job_id=i,
                title=f"Personalized Job {i}",
                company=f"Company {i}",
                location="東京都",
                salary=f"年収{400 + i*20}-{600 + i*20}万円",
                description=f"あなたのスキルに最適化された求人です。",
                match_score=85.0 - i,
                tags=["Personalized", "Match"],
                is_new=i % 3 == 0,
                is_popular=i % 2 == 0
            )
            for i in range(11, 21)  # 10 jobs
        ],
        EmailSectionType.NEW_ARRIVALS: [
            JobMatch(
                job_id=i,
                title=f"New Job {i}",
                company=f"New Company {i}",
                location="東京都",
                salary=f"年収{350 + i*15}-{550 + i*15}万円",
                description="最新の求人情報です。",
                match_score=80.0 - (i-21),
                tags=["New", "Fresh"],
                is_new=True,
                is_popular=False
            )
            for i in range(21, 31)  # 10 jobs
        ],
        EmailSectionType.POPULAR_JOBS: [
            JobMatch(
                job_id=i,
                title=f"Popular Job {i}",
                company=f"Popular Company {i}",
                location="東京都",
                salary=f"年収{500 + i*10}-{700 + i*10}万円",
                description="人気の高い求人です。",
                match_score=88.0 - (i-31),
                tags=["Popular", "Trending"],
                is_new=False,
                is_popular=True,
                application_count=100 + i*10
            )
            for i in range(31, 36)  # 5 jobs
        ],
        EmailSectionType.YOU_MIGHT_LIKE: [
            JobMatch(
                job_id=i,
                title=f"Recommended Job {i}",
                company=f"Recommended Company {i}",
                location="東京都",
                salary=f"年収{450 + i*12}-{650 + i*12}万円",
                description="こちらの求人もおすすめです。",
                match_score=83.0 - (i-36),
                tags=["Recommended", "Similar"],
                is_new=False,
                is_popular=False
            )
            for i in range(36, 41)  # 5 jobs
        ]
    }


async def example_single_user_generation():
    """Example: Generate email for a single user"""
    logger.info("=== Single User Email Generation Example ===")

    # Get API keys from environment
    openai_api_key = os.getenv("OPENAI_API_KEY", "demo-key")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Create service (using mock mode if no real API key)
    mock_mode = openai_api_key == "demo-key"
    service = await create_email_generation_service(
        openai_api_key=openai_api_key,
        redis_url=redis_url,
        mock_mode=mock_mode
    )

    try:
        # Create user profile
        user = create_sample_users()[0]  # Japanese user
        job_matches = create_sample_job_matches()

        # Validate job matches
        validation_result = await service.validate_job_matches(job_matches)
        logger.info(f"Job matches validation: {validation_result}")

        # Generate email
        logger.info(f"Generating email for {user.name} (User ID: {user.user_id})")
        start_time = datetime.now()

        result = await service.generate_email(
            user_profile=user,
            job_matches=job_matches,
            template_variables={"campaign_name": "Weekly Picks"}
        )

        generation_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Generation completed in {generation_time:.2f} seconds")

        # Display results
        if result.status == GenerationStatus.COMPLETED:
            email = result.email_content
            logger.info(f"✅ Email generated successfully!")
            logger.info(f"Subject: {email.subject}")
            logger.info(f"Language: {email.language.value}")
            logger.info(f"Greeting: {email.greeting}")
            logger.info(f"Introduction: {email.introduction[:100]}...")

            # Show section details
            for section in email.sections:
                logger.info(f"\n--- {section.title} ---")
                logger.info(f"Intro: {section.intro_text}")
                logger.info(f"Jobs: {len(section.job_descriptions)} jobs")
                logger.info(f"CTA: {section.call_to_action}")

            logger.info(f"\nClosing: {email.closing}")
            logger.info(f"Signature: {email.signature}")

        elif result.status == GenerationStatus.CACHED:
            logger.info(f"✅ Email retrieved from cache!")
            logger.info(f"Cache hit: {result.cache_hit}")

        else:
            logger.error(f"❌ Email generation failed: {result.error_message}")

        # Show performance metrics
        metrics = await service.get_performance_metrics()
        logger.info(f"\nPerformance Metrics:")
        logger.info(f"Total requests: {metrics['total_requests']}")
        logger.info(f"Successful requests: {metrics['successful_requests']}")
        logger.info(f"Cache hits: {metrics['cache_hits']}")
        logger.info(f"Average response time: {metrics['avg_response_time']:.2f}ms")

    finally:
        await service.close()


async def example_batch_generation():
    """Example: Generate emails for multiple users in batch"""
    logger.info("\n=== Batch Email Generation Example ===")

    # Get API keys from environment
    openai_api_key = os.getenv("OPENAI_API_KEY", "demo-key")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Create service
    mock_mode = openai_api_key == "demo-key"
    service = await create_email_generation_service(
        openai_api_key=openai_api_key,
        redis_url=redis_url,
        mock_mode=mock_mode
    )

    try:
        # Create multiple users
        users = create_sample_users()
        job_matches = create_sample_job_matches()

        # Create job matches for each user (in real scenario, these would be different)
        job_matches_by_user = {
            user.user_id: job_matches for user in users
        }

        # Create batch request
        batch_request = BatchGenerationRequest(
            user_profiles=users,
            job_matches_by_user=job_matches_by_user,
            language=EmailLanguage.JAPANESE,  # Default language
            template_variables={"campaign_name": "Weekly Batch"},
            priority=8,
            dry_run=False
        )

        # Generate emails in batch
        logger.info(f"Generating emails for {len(users)} users...")
        start_time = datetime.now()

        results = await service.generate_emails_batch(batch_request)

        generation_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Batch generation completed in {generation_time:.2f} seconds")

        # Analyze results
        successful = [r for r in results if r.status == GenerationStatus.COMPLETED]
        cached = [r for r in results if r.status == GenerationStatus.CACHED]
        failed = [r for r in results if r.status == GenerationStatus.FAILED]

        logger.info(f"\n📊 Batch Results:")
        logger.info(f"Total users: {len(results)}")
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"🏠 Cached: {len(cached)}")
        logger.info(f"❌ Failed: {len(failed)}")

        # Show details for each result
        for i, result in enumerate(results):
            user = users[i]
            status_emoji = "✅" if result.status == GenerationStatus.COMPLETED else "❌"
            logger.info(f"{status_emoji} {user.name} ({user.preferred_language.value}): "
                       f"{result.status.value} - {result.generation_time_ms}ms")

            if result.email_content:
                logger.info(f"   Subject: {result.email_content.subject}")

        # Performance summary
        avg_time = sum(r.generation_time_ms for r in results) / len(results)
        logger.info(f"\n⚡ Performance Summary:")
        logger.info(f"Average generation time: {avg_time:.2f}ms")
        logger.info(f"Total time: {generation_time:.2f}s")
        logger.info(f"Throughput: {len(results)/generation_time:.2f} emails/second")

    finally:
        await service.close()


async def example_error_handling():
    """Example: Demonstrate error handling and fallback mechanisms"""
    logger.info("\n=== Error Handling Example ===")

    # Create service with invalid configuration to test error handling
    service = EmailGenerationService(
        openai_api_key="invalid-key",
        redis_url="redis://invalid-host:6379/0",
        mock_mode=True  # Keep in mock mode to avoid actual errors
    )

    try:
        # Test with invalid job matches
        user = create_sample_users()[0]
        invalid_job_matches = {}  # Empty matches

        result = await service.generate_email(
            user_profile=user,
            job_matches=invalid_job_matches
        )

        logger.info(f"Result with invalid data: {result.status.value}")

        # Test rate limiting
        service.rate_limiter = AsyncMock()
        service.rate_limiter.check_limit.return_value = False

        result = await service.generate_email(
            user_profile=user,
            job_matches=create_sample_job_matches()
        )

        logger.info(f"Rate limited result: {result.status.value}")
        logger.info(f"Error message: {result.error_message}")

        # Test fallback content
        fallback_section = service._fallback_section_content(
            EmailSectionType.EDITORIAL_PICKS,
            [JobMatch(job_id=1, title="Test", company="Test", location="Test")],
            EmailLanguage.JAPANESE
        )

        logger.info(f"Fallback section generated: {fallback_section.title}")
        logger.info(f"Fallback metadata: {fallback_section.generation_metadata}")

    finally:
        await service.close()


async def example_performance_monitoring():
    """Example: Performance monitoring and metrics collection"""
    logger.info("\n=== Performance Monitoring Example ===")

    service = await create_email_generation_service(
        openai_api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
        mock_mode=True
    )

    try:
        user = create_sample_users()[0]
        job_matches = create_sample_job_matches()

        # Generate multiple emails to collect metrics
        for i in range(5):
            await service.generate_email(user, job_matches)

        # Get detailed metrics
        metrics = await service.get_performance_metrics()

        logger.info("📈 Performance Metrics:")
        for key, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")

        # Test cache management
        await service.clear_cache(user_id=user.user_id)
        logger.info("🗑️  Cache cleared for user")

        # Test global cache clear
        await service.clear_cache()
        logger.info("🗑️  Global cache cleared")

    finally:
        await service.close()


async def example_language_comparison():
    """Example: Compare email generation in Japanese vs English"""
    logger.info("\n=== Language Comparison Example ===")

    service = await create_email_generation_service(
        openai_api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
        mock_mode=True
    )

    try:
        job_matches = create_sample_job_matches()

        # Japanese user
        japanese_user = UserProfile(
            user_id=1,
            name="田中太郎",
            email="tanaka@example.com",
            preferred_language=EmailLanguage.JAPANESE,
            location="東京都"
        )

        # English user
        english_user = UserProfile(
            user_id=2,
            name="John Smith",
            email="john@example.com",
            preferred_language=EmailLanguage.ENGLISH,
            location="Tokyo"
        )

        # Generate emails for both users
        japanese_result = await service.generate_email(japanese_user, job_matches)
        english_result = await service.generate_email(english_user, job_matches)

        # Compare results
        logger.info("🇯🇵 Japanese Email:")
        if japanese_result.email_content:
            logger.info(f"  Subject: {japanese_result.email_content.subject}")
            logger.info(f"  Greeting: {japanese_result.email_content.greeting}")
            logger.info(f"  First section: {japanese_result.email_content.sections[0].title}")

        logger.info("\n🇺🇸 English Email:")
        if english_result.email_content:
            logger.info(f"  Subject: {english_result.email_content.subject}")
            logger.info(f"  Greeting: {english_result.email_content.greeting}")
            logger.info(f"  First section: {english_result.email_content.sections[0].title}")

        # Compare section names across languages
        if japanese_result.email_content and english_result.email_content:
            logger.info("\n📝 Section Name Comparison:")
            for i, (jp_section, en_section) in enumerate(zip(
                japanese_result.email_content.sections,
                english_result.email_content.sections
            )):
                logger.info(f"  {i+1}. JP: {jp_section.title} | EN: {en_section.title}")

    finally:
        await service.close()


async def main():
    """Run all examples"""
    logger.info("🚀 GPT-5 Nano Email Generation Service Examples")
    logger.info("=" * 60)

    try:
        # Run examples
        await example_single_user_generation()
        await example_batch_generation()
        await example_error_handling()
        await example_performance_monitoring()
        await example_language_comparison()

        logger.info("\n✅ All examples completed successfully!")

    except Exception as e:
        logger.error(f"❌ Example execution failed: {e}")
        raise


if __name__ == "__main__":
    # Configure environment for demo
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  No OPENAI_API_KEY found, running in mock mode")
        os.environ["OPENAI_API_KEY"] = "demo-key"

    if not os.getenv("REDIS_URL"):
        logger.warning("⚠️  No REDIS_URL found, using default")
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    # Run examples
    asyncio.run(main())