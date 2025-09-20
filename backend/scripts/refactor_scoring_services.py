#!/usr/bin/env python3
"""
Refactor script for T022-T025 scoring services
"""

import os

# T022: SEO Scoring Service with improvements
seo_content = '''#!/usr/bin/env python3
"""
T022: SEO Scoring Service

Provides keyword-based scoring functionality using SEMrush keyword data.
Calculates scores based on keyword matching in job fields with weighted priorities.
"""
import logging
from typing import List, Dict, Any, Optional
from app.models.job import Job

logger = logging.getLogger(__name__)

class SEOScoringService:
    """Service for calculating SEO-based job scores."""

    # Field weight constants for SEO scoring
    FIELD_WEIGHTS = {
        "application_name": 1.5,  # Highest priority
        "title": 1.2,              # High priority
        "description": 1.0,         # Normal priority
        "company": 0.8              # Lower priority
    }

    # Scoring parameters
    DEFAULT_SEARCH_VOLUME = 1000
    VOLUME_NORMALIZATION_FACTOR = 10000
    SCORE_MULTIPLIER = 100
    MAX_SCORE = 100

    def __init__(self):
        """Initialize SEO scoring service."""
        self.field_weights = self.FIELD_WEIGHTS.copy()
        logger.info("SEOScoringService initialized with field weights: %s", self.field_weights)

    async def normalize_keywords(self, keywords: List[str]) -> List[str]:
        """
        Normalize keywords for consistent matching.

        Args:
            keywords: List of raw keywords

        Returns:
            List of normalized keywords
        """
        try:
            normalized = []
            for keyword in keywords:
                if keyword:
                    normalized_keyword = keyword.lower().replace("-", " ").replace("_", " ").strip()
                    if normalized_keyword:
                        normalized.append(normalized_keyword)
            return normalized
        except Exception as e:
            logger.error("Error normalizing keywords: %s", e)
            return []

    async def generate_variations(self, keyword: str) -> List[str]:
        """
        Generate keyword variations for broader matching.

        Args:
            keyword: Base keyword

        Returns:
            List of keyword variations
        """
        if not keyword:
            return []

        try:
            variations = [keyword]

            # Add common variations
            if " " in keyword:
                variations.extend([
                    keyword.replace(" ", "-"),
                    keyword.replace(" ", "_"),
                    keyword.replace(" ", "")
                ])

            # Remove duplicates while preserving order
            seen = set()
            unique_variations = []
            for var in variations:
                if var not in seen:
                    seen.add(var)
                    unique_variations.append(var)

            return unique_variations
        except Exception as e:
            logger.error("Error generating keyword variations: %s", e)
            return [keyword]

    async def calculate_seo_score(self, job: Job, semrush_keywords: List[Dict[str, Any]]) -> float:
        """
        Calculate SEO score for a job based on keyword matching.

        Args:
            job: Job object to score
            semrush_keywords: List of SEMrush keyword data with 'keyword' and 'search_volume'

        Returns:
            SEO score between 0 and 100
        """
        if not semrush_keywords:
            logger.debug("No SEMrush keywords provided for job %s", getattr(job, 'job_id', 'unknown'))
            return 0.0

        try:
            total_score = 0.0

            for kw_data in semrush_keywords:
                if not isinstance(kw_data, dict):
                    continue

                keyword = kw_data.get("keyword", "")
                if not keyword:
                    continue

                keyword = keyword.lower()
                search_volume = kw_data.get("search_volume", self.DEFAULT_SEARCH_VOLUME)

                # Calculate field scores
                field_scores = []

                # Check application name
                if hasattr(job, "application_name") and job.application_name:
                    if keyword in job.application_name.lower():
                        field_scores.append(self.field_weights["application_name"])

                # Check title
                if hasattr(job, "title") and job.title:
                    if keyword in job.title.lower():
                        field_scores.append(self.field_weights["title"])

                # Check description
                if hasattr(job, "description") and job.description:
                    if keyword in job.description.lower():
                        field_scores.append(self.field_weights["description"])

                # Check company
                if hasattr(job, "company") and job.company:
                    if keyword in job.company.lower():
                        field_scores.append(self.field_weights["company"])

                # Apply highest matching score
                if field_scores:
                    volume_factor = min(search_volume / self.VOLUME_NORMALIZATION_FACTOR, 1.0)
                    keyword_score = max(field_scores) * volume_factor * self.SCORE_MULTIPLIER
                    total_score += keyword_score
                    logger.debug("Keyword '%s' matched with score %.2f", keyword, keyword_score)

            final_score = min(self.MAX_SCORE, total_score)
            logger.info("SEO score for job %s: %.2f", getattr(job, 'job_id', 'unknown'), final_score)
            return final_score

        except Exception as e:
            logger.error("Error calculating SEO score: %s", e)
            return 0.0
'''

# T023: Personalized Scoring Service with improvements
personalized_content = '''#!/usr/bin/env python3
"""
T023: Personalized Scoring Service

Provides collaborative filtering-based personalized scoring using ALS algorithm.
Generates user-specific job recommendations based on historical behavior.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.models.user import User

logger = logging.getLogger(__name__)

class PersonalizedScoringService:
    """Service for calculating personalized job scores using collaborative filtering."""

    # ALS model parameters
    ALS_FACTORS = 50
    ALS_REGULARIZATION = 0.01
    ALS_ITERATIONS = 15

    # Scoring parameters
    DEFAULT_SCORE = 50.0
    TRAINED_SCORE_BASE = 75.0
    BEHAVIOR_ANALYSIS_DAYS = 30
    MIN_HISTORY_SIZE = 5

    def __init__(self):
        """Initialize personalized scoring service."""
        self.factors = self.ALS_FACTORS
        self.regularization = self.ALS_REGULARIZATION
        self.iterations = self.ALS_ITERATIONS
        self.model = None
        logger.info("PersonalizedScoringService initialized with ALS params: factors=%d, reg=%.3f, iter=%d",
                   self.factors, self.regularization, self.iterations)

    async def initialize_als_model(self):
        """
        Initialize ALS collaborative filtering model.

        Returns:
            Initialized ALS model instance
        """
        try:
            # TODO: Replace with actual ALS implementation (e.g., implicit library)
            class ALSModel:
                """Mock ALS model for development."""
                def __init__(self, factors: int, regularization: float, iterations: int):
                    self.factors = factors
                    self.regularization = regularization
                    self.iterations = iterations
                    self.is_fitted = False

                def fit(self, user_item_matrix):
                    """Fit the model to user-item interaction data."""
                    self.is_fitted = True
                    logger.info("ALS model fitted with matrix shape: %s",
                              getattr(user_item_matrix, 'shape', 'unknown'))

                def predict(self, user_id: str, item_id: str) -> float:
                    """Predict user preference for an item."""
                    if not self.is_fitted:
                        return 0.5
                    # Mock prediction logic
                    return 0.75

            model = ALSModel(self.factors, self.regularization, self.iterations)
            logger.info("ALS model initialized successfully")
            return model

        except Exception as e:
            logger.error("Error initializing ALS model: %s", e)
            return None

    async def analyze_user_behavior(self, history: List[Dict], days: int = None) -> List[Dict[str, Any]]:
        """
        Analyze user behavior patterns from interaction history.

        Args:
            history: List of user interaction records
            days: Number of days to analyze (default: BEHAVIOR_ANALYSIS_DAYS)

        Returns:
            List of analyzed behavior patterns
        """
        if days is None:
            days = self.BEHAVIOR_ANALYSIS_DAYS

        if not history:
            logger.debug("No history provided for behavior analysis")
            return []

        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            analyzed_data = []

            for record in history:
                if not isinstance(record, dict):
                    continue

                # Check if record is within time window
                timestamp = record.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    if timestamp < cutoff_date:
                        continue

                # Extract relevant features
                analyzed_record = {
                    "job_id": record.get("job_id"),
                    "interaction_type": record.get("interaction_type", "view"),
                    "duration": record.get("duration", 0),
                    "timestamp": timestamp
                }
                analyzed_data.append(analyzed_record)

            logger.info("Analyzed %d behavior records from last %d days", len(analyzed_data), days)
            return analyzed_data

        except Exception as e:
            logger.error("Error analyzing user behavior: %s", e)
            return []

    async def train_model(self, history: List[Dict]):
        """
        Train the collaborative filtering model on user history.

        Args:
            history: List of user interaction records
        """
        try:
            if not history:
                logger.warning("Cannot train model with empty history")
                return

            # Initialize model if not exists
            if not self.model:
                self.model = await self.initialize_als_model()

            if self.model:
                # TODO: Convert history to user-item matrix format
                # For now, just mark as fitted
                self.model.is_fitted = True
                logger.info("Model training completed with %d records", len(history))

        except Exception as e:
            logger.error("Error training model: %s", e)

    async def calculate_personalized_score(self, user: User, job_id: str) -> float:
        """
        Calculate personalized score for a job based on user preferences.

        Args:
            user: User object with search history
            job_id: ID of the job to score

        Returns:
            Personalized score between 0 and 100
        """
        try:
            # Check if user has sufficient history
            if not hasattr(user, 'search_history') or not user.search_history:
                logger.debug("User %s has no search history, returning default score",
                           getattr(user, 'user_id', 'unknown'))
                return self.DEFAULT_SCORE

            history_size = len(user.search_history)

            # Return default score if history is too small
            if history_size < self.MIN_HISTORY_SIZE:
                logger.debug("User %s has insufficient history (%d records), returning default score",
                           getattr(user, 'user_id', 'unknown'), history_size)
                return self.DEFAULT_SCORE

            # Train model if needed
            if not self.model or not getattr(self.model, 'is_fitted', False):
                await self.train_model(user.search_history)

            # Calculate score using model
            if self.model and getattr(self.model, 'is_fitted', False):
                # TODO: Use actual model prediction
                prediction = self.model.predict(getattr(user, 'user_id', ''), job_id)
                score = self.TRAINED_SCORE_BASE * prediction
                logger.info("Personalized score for user %s, job %s: %.2f",
                           getattr(user, 'user_id', 'unknown'), job_id, score)
                return score

            return self.DEFAULT_SCORE

        except Exception as e:
            logger.error("Error calculating personalized score: %s", e)
            return self.DEFAULT_SCORE
'''

# T024: Job Selector Service with improvements
selector_content = '''#!/usr/bin/env python3
"""
T024: Job Selector Service

Provides job selection algorithms for different email sections.
Implements editorial picks, top-rated, and personalized selection strategies.
"""
import logging
from typing import List, Dict, Optional
from app.models.job import Job
from app.models.user import User

logger = logging.getLogger(__name__)

class JobSelectorService:
    """Service for selecting jobs for different email sections."""

    # Selection limits for each section
    SECTION_LIMITS = {
        "editorial_picks": 5,
        "top5": 5,
        "recommended": 5,
        "new_arrivals": 5,
        "popular": 5,
        "personalized": 5
    }

    # Scoring weights
    EDITORIAL_FEE_WEIGHT = 1.0
    EDITORIAL_CLICKS_WEIGHT = 1.0

    def __init__(self):
        """Initialize job selector service."""
        self.section_limits = self.SECTION_LIMITS.copy()
        logger.info("JobSelectorService initialized with section limits: %s", self.section_limits)

    async def select_editorial_picks(self, jobs: List[Job], user: User) -> List[Job]:
        """
        Select editorial picks based on fee and click metrics.

        Args:
            jobs: List of available jobs
            user: User object for context

        Returns:
            List of selected editorial pick jobs
        """
        if not jobs:
            logger.debug("No jobs available for editorial picks")
            return []

        try:
            # Calculate composite scores for editorial selection
            scored_jobs = []

            for job in jobs:
                # Skip jobs without required metrics
                if not hasattr(job, "fee") or not hasattr(job, "application_clicks"):
                    continue

                fee = getattr(job, "fee", 0) or 0
                clicks = getattr(job, "application_clicks", 0) or 0

                # Calculate editorial score (fee * clicks as business value metric)
                editorial_score = (fee * self.EDITORIAL_FEE_WEIGHT) * (clicks * self.EDITORIAL_CLICKS_WEIGHT)
                scored_jobs.append((job, editorial_score))

            # Sort by score and select top N
            scored_jobs.sort(key=lambda x: x[1], reverse=True)
            selected = [job for job, score in scored_jobs[:self.section_limits["editorial_picks"]]]

            logger.info("Selected %d editorial picks from %d candidates", len(selected), len(jobs))
            return selected

        except Exception as e:
            logger.error("Error selecting editorial picks: %s", e)
            return []

    async def select_top5(self, jobs: List[Job], user: User) -> List[Job]:
        """
        Select top 5 jobs based on basic scoring.

        Args:
            jobs: List of available jobs
            user: User object for context

        Returns:
            List of top 5 jobs
        """
        if not jobs:
            logger.debug("No jobs available for top5 selection")
            return []

        try:
            # Sort by basic score
            jobs_with_scores = []

            for job in jobs:
                score = getattr(job, "basic_score", 0)
                jobs_with_scores.append((job, score))

            # Sort and select top N
            jobs_with_scores.sort(key=lambda x: x[1], reverse=True)
            selected = [job for job, score in jobs_with_scores[:self.section_limits["top5"]]]

            logger.info("Selected %d top5 jobs from %d candidates", len(selected), len(jobs))
            return selected

        except Exception as e:
            logger.error("Error selecting top5 jobs: %s", e)
            return []

    async def select_all_sections(self, jobs: List[Job], user: User) -> Dict[str, List[Job]]:
        """
        Select jobs for all email sections with no duplicates between sections.

        Args:
            jobs: List of available jobs
            user: User object for context

        Returns:
            Dictionary mapping section names to job lists
        """
        if not jobs:
            logger.warning("No jobs available for section selection")
            return {section: [] for section in self.section_limits.keys()}

        try:
            used_job_ids = set()
            sections = {}

            # 1. Editorial picks (highest priority)
            editorial = await self.select_editorial_picks(jobs, user)
            sections["editorial_picks"] = editorial
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in editorial)
            logger.debug("Editorial picks selected: %d jobs", len(editorial))

            # 2. Top 5 (from remaining jobs)
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            top5 = await self.select_top5(remaining, user)
            sections["top5"] = top5
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in top5)
            logger.debug("Top5 selected: %d jobs from %d remaining", len(top5), len(remaining))

            # 3. Other sections (simplified selection from remaining)
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]

            # Recommended section
            recommended_limit = self.section_limits["recommended"]
            sections["recommended"] = remaining[:recommended_limit]
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in sections["recommended"])

            # New arrivals section
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            new_arrivals_limit = self.section_limits["new_arrivals"]
            sections["new_arrivals"] = remaining[:new_arrivals_limit]
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in sections["new_arrivals"])

            # Popular section
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            popular_limit = self.section_limits["popular"]
            sections["popular"] = remaining[:popular_limit]
            used_job_ids.update(getattr(j, "job_id", id(j)) for j in sections["popular"])

            # Personalized section
            remaining = [j for j in jobs if getattr(j, "job_id", id(j)) not in used_job_ids]
            personalized_limit = self.section_limits["personalized"]
            sections["personalized"] = remaining[:personalized_limit]

            # Log section statistics
            total_selected = sum(len(jobs) for jobs in sections.values())
            logger.info("Selected %d unique jobs across %d sections from %d candidates",
                       total_selected, len(sections), len(jobs))

            for section_name, section_jobs in sections.items():
                logger.debug("Section '%s': %d jobs", section_name, len(section_jobs))

            return sections

        except Exception as e:
            logger.error("Error selecting all sections: %s", e)
            return {section: [] for section in self.section_limits.keys()}
'''

# T025: Duplicate Control Service with improvements
duplicate_content = '''#!/usr/bin/env python3
"""
T025: Duplicate Control Service

Prevents duplicate job recommendations by filtering jobs from companies
where the user has recently applied within a configurable time window.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.models.job import Job

logger = logging.getLogger(__name__)

class DuplicateControlService:
    """Service for filtering duplicate job recommendations."""

    # Configuration constants
    DEFAULT_WINDOW_DAYS = 14
    MIN_WINDOW_DAYS = 1
    MAX_WINDOW_DAYS = 90

    def __init__(self, window_days: int = DEFAULT_WINDOW_DAYS):
        """
        Initialize duplicate control service.

        Args:
            window_days: Number of days to check for duplicates (default: 14)
        """
        # Validate window_days parameter
        if window_days < self.MIN_WINDOW_DAYS:
            logger.warning("Window days %d is below minimum (%d), using minimum",
                         window_days, self.MIN_WINDOW_DAYS)
            window_days = self.MIN_WINDOW_DAYS
        elif window_days > self.MAX_WINDOW_DAYS:
            logger.warning("Window days %d exceeds maximum (%d), using maximum",
                         window_days, self.MAX_WINDOW_DAYS)
            window_days = self.MAX_WINDOW_DAYS

        self.window_days = window_days
        logger.info("DuplicateControlService initialized with %d day window", self.window_days)

    async def filter_duplicates(self, jobs: List[Job], applications: List[Dict[str, Any]]) -> List[Job]:
        """
        Filter out jobs from companies where user has recently applied.

        Args:
            jobs: List of candidate jobs
            applications: List of user's application history with 'company_id' and 'applied_at' fields

        Returns:
            Filtered list of jobs excluding recent company applications
        """
        # Return all jobs if no application history
        if not applications:
            logger.debug("No application history provided, returning all %d jobs", len(jobs) if jobs else 0)
            return jobs if jobs else []

        # Return empty list if no jobs
        if not jobs:
            logger.debug("No jobs provided for duplicate filtering")
            return []

        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=self.window_days)
            recent_company_ids = set()

            # Identify companies with recent applications
            for application in applications:
                if not isinstance(application, dict):
                    logger.warning("Skipping invalid application record: %s", type(application))
                    continue

                # Extract and validate company_id
                company_id = application.get("company_id")
                if not company_id:
                    continue

                # Extract and parse applied_at timestamp
                applied_at = application.get("applied_at")
                if not applied_at:
                    continue

                # Convert string timestamp if needed
                if isinstance(applied_at, str):
                    try:
                        applied_at = datetime.fromisoformat(applied_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError) as e:
                        logger.warning("Invalid timestamp format: %s", applied_at)
                        continue

                # Check if application is within window
                if applied_at >= cutoff_date:
                    recent_company_ids.add(company_id)
                    days_ago = (now - applied_at).days
                    logger.debug("Found recent application to company %s (%d days ago)",
                               company_id, days_ago)

            logger.info("Identified %d companies with applications in last %d days",
                       len(recent_company_ids), self.window_days)

            # Filter jobs
            filtered_jobs = []
            filtered_count = 0

            for job in jobs:
                job_company_id = getattr(job, "company_id", None)

                # Keep job if no company_id or not in recent applications
                if not job_company_id or job_company_id not in recent_company_ids:
                    filtered_jobs.append(job)
                else:
                    filtered_count += 1
                    logger.debug("Filtering job %s from recently applied company %s",
                               getattr(job, "job_id", "unknown"), job_company_id)

            logger.info("Filtered %d duplicate jobs, returning %d unique jobs",
                       filtered_count, len(filtered_jobs))
            return filtered_jobs

        except Exception as e:
            logger.error("Error filtering duplicates: %s", e)
            # Return original jobs on error to avoid losing recommendations
            return jobs

    async def get_recent_companies(self, applications: List[Dict[str, Any]]) -> List[str]:
        """
        Get list of company IDs with recent applications.

        Args:
            applications: List of user's application history

        Returns:
            List of company IDs with recent applications
        """
        if not applications:
            return []

        try:
            now = datetime.now()
            cutoff_date = now - timedelta(days=self.window_days)
            recent_companies = []

            for application in applications:
                if not isinstance(application, dict):
                    continue

                company_id = application.get("company_id")
                if not company_id:
                    continue

                applied_at = application.get("applied_at")
                if not applied_at:
                    continue

                if isinstance(applied_at, str):
                    try:
                        applied_at = datetime.fromisoformat(applied_at.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        continue

                if applied_at >= cutoff_date:
                    recent_companies.append(company_id)

            return recent_companies

        except Exception as e:
            logger.error("Error getting recent companies: %s", e)
            return []
'''

# Write refactored files
base_path = "backend/app/services/"

with open(base_path + "seo_scoring.py", "w") as f:
    f.write(seo_content)

with open(base_path + "personalized_scoring.py", "w") as f:
    f.write(personalized_content)

with open(base_path + "job_selector.py", "w") as f:
    f.write(selector_content)

with open(base_path + "duplicate_control.py", "w") as f:
    f.write(duplicate_content)

print("✅ All services refactored successfully!")
print("Improvements made:")
print("  - Added comprehensive docstrings")
print("  - Added type hints")
print("  - Added logging support")
print("  - Added constants for magic numbers")
print("  - Added error handling")
print("  - Improved code organization")
print("  - Added validation logic")