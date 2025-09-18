"""
求人選択サービス

100K求人から各ユーザーに最適な40件を効率的に選択するシステム
処理時間目標: < 200ms per user
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from functools import lru_cache

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, and_, or_, func

from app.models.jobs import Job, JobSalary, JobFeatures, JobCategory
from app.models.users import User, UserProfile, UserPreferences
from app.services.scoring_engine import ScoringEngine
from app.core.config import settings

logger = logging.getLogger(__name__)

# Performance constants
PERFORMANCE_TARGET_MS = 200
INITIAL_FILTERING_TARGET = 10000  # Reduce 100K → 10K
FINAL_SELECTION_LIMIT = 40
MAX_JOBS_PER_CATEGORY = 10
MIN_CATEGORIES_DIVERSITY = 3
BATCH_CHUNK_SIZE = 100
SCORING_CHUNK_SIZE = 1000

# Cache TTL settings
USER_PREFERENCES_CACHE_TTL = 3600  # 1 hour
RECENT_APPLICATIONS_CACHE_TTL = 300  # 5 minutes
FILTERED_JOBS_CACHE_TTL = 1800  # 30 minutes


class JobSelector:
    """
    Efficient job selection system that processes 100K jobs to find top 40 matches per user
    """

    def __init__(self, scoring_engine: ScoringEngine, db_session: AsyncSession):
        self.scoring_engine = scoring_engine
        self.db = db_session

        # Performance monitoring
        self._performance_stats = {
            'total_selections': 0,
            'avg_selection_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Multi-layer caching strategy
        self._user_preferences_cache = {}
        self._recent_applications_cache = {}
        self._filtered_jobs_cache = {}
        self._location_distance_cache = {}
        self._blocked_companies_cache = {}

        # Shared job data for batch processing
        self._jobs_df = None
        self._last_jobs_load_time = None
        self.jobs_cache_ttl = 300  # 5 minutes

    async def select_top_jobs(self, user_id: int, limit: int = 40) -> List[Dict[str, Any]]:
        """
        Select top jobs for a user with these stages:
        1. Initial Filtering (reduce 100K → ~10K)
        2. Parallel Score Calculation
        3. Category Distribution Consideration
        4. Final Selection of top 40
        """
        start_time = time.time()

        try:
            # Load user data
            user = await self._get_user_data(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return []

            # Stage 1: Initial Filtering
            logger.debug(f"Stage 1: Initial filtering for user {user_id}")
            filtering_start = time.time()

            filtered_jobs_df = await self._apply_initial_filtering(user)
            filtering_time = time.time() - filtering_start

            if filtered_jobs_df.empty:
                logger.info(f"No jobs passed initial filtering for user {user_id}")
                return []

            logger.info(f"Initial filtering: {len(filtered_jobs_df)} jobs selected in {filtering_time:.3f}s")

            # Stage 2: Score Calculation (parallel)
            logger.debug(f"Stage 2: Score calculation for user {user_id}")
            scoring_start = time.time()

            scores_df = await self._calculate_scores_parallel(user, filtered_jobs_df)
            scoring_time = time.time() - scoring_start

            logger.info(f"Score calculation completed in {scoring_time:.3f}s")

            # Stage 3: Category Distribution
            logger.debug(f"Stage 3: Category distribution for user {user_id}")
            diversity_start = time.time()

            diversified_jobs = await self._apply_diversity_rules(scores_df, user)
            diversity_time = time.time() - diversity_start

            logger.info(f"Category diversification completed in {diversity_time:.3f}s")

            # Stage 4: Final Selection
            final_jobs = diversified_jobs[:limit]

            # Add metadata
            result = []
            for idx, job_data in enumerate(final_jobs):
                result.append({
                    'job_id': int(job_data['job_id']),
                    'score': float(job_data['total_score']),
                    'rank': idx + 1,
                    'category': job_data.get('occupation_cd1'),
                    'company_name': job_data.get('company_name'),
                    'application_name': job_data.get('application_name'),
                    'salary_display': self._format_salary_display(job_data),
                    'location': self._format_location_display(job_data),
                    'features': self._extract_features(job_data),
                    'score_components': {
                        'base_score': float(job_data.get('base_score', 0)),
                        'seo_score': float(job_data.get('seo_score', 0)),
                        'personal_score': float(job_data.get('personal_score', 0))
                    }
                })

            total_time = time.time() - start_time
            self._update_performance_stats(total_time, 1)

            logger.info(f"Job selection completed for user {user_id}: {len(result)} jobs in {total_time:.3f}s")

            # Performance target check
            if total_time * 1000 > PERFORMANCE_TARGET_MS:
                logger.warning(f"Performance target missed: {total_time*1000:.1f}ms > {PERFORMANCE_TARGET_MS}ms")

            return result

        except Exception as e:
            logger.error(f"Error in job selection for user {user_id}: {e}")
            return []

    async def select_jobs_batch(self, user_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Batch process multiple users efficiently
        - Process in chunks of 100 users
        - Use parallel processing
        - Share job data loading across users
        """
        start_time = time.time()

        try:
            # Ensure job data is loaded and fresh
            await self._ensure_jobs_data_loaded()

            results = {}
            total_users = len(user_ids)

            # Process in chunks
            for i in range(0, total_users, BATCH_CHUNK_SIZE):
                chunk_users = user_ids[i:i + BATCH_CHUNK_SIZE]
                chunk_start = time.time()

                # Process chunk in parallel
                chunk_tasks = [
                    self.select_top_jobs(user_id)
                    for user_id in chunk_users
                ]

                chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)

                # Collect results
                for user_id, user_jobs in zip(chunk_users, chunk_results):
                    if isinstance(user_jobs, Exception):
                        logger.error(f"Error processing user {user_id}: {user_jobs}")
                        results[user_id] = []
                    else:
                        results[user_id] = user_jobs

                chunk_time = time.time() - chunk_start
                processed_users = min(i + BATCH_CHUNK_SIZE, total_users)

                logger.info(f"Processed chunk {i//BATCH_CHUNK_SIZE + 1}: "
                           f"{len(chunk_users)} users in {chunk_time:.2f}s")
                logger.info(f"Overall progress: {processed_users}/{total_users} users")

            total_time = time.time() - start_time
            avg_time_per_user = total_time / total_users * 1000

            logger.info(f"Batch processing completed: {total_users} users in {total_time:.2f}s "
                       f"(avg: {avg_time_per_user:.1f}ms/user)")

            return results

        except Exception as e:
            logger.error(f"Error in batch job selection: {e}")
            return {}

    async def _apply_initial_filtering(self, user: Dict[str, Any]) -> pd.DataFrame:
        """
        Initial filtering stage:
        - Location matching (prefecture, city, adjacent areas)
        - Category preferences
        - Salary range matching
        - Remove recently applied jobs
        - Remove blocked companies
        """
        # Get user preferences
        user_prefs = await self._get_user_preferences_cached(user['user_id'])
        recent_apps = await self._get_recent_applications_cached(user['user_id'])
        blocked_companies = await self._get_blocked_companies_cached(user['user_id'])

        # Start with all active jobs
        jobs_df = await self._get_jobs_dataframe()
        if jobs_df.empty:
            return pd.DataFrame()

        # Apply filters
        mask = jobs_df['is_active'] == True

        # Location filtering
        if user.get('estimated_pref_cd'):
            location_mask = await self._create_location_mask(jobs_df, user)
            mask &= location_mask

        # Category filtering
        if user_prefs.get('preferred_categories'):
            category_mask = jobs_df['occupation_cd1'].isin(user_prefs['preferred_categories'])
            # Also include adjacent categories
            adjacent_categories = await self._get_adjacent_categories(user_prefs['preferred_categories'])
            if adjacent_categories:
                category_mask |= jobs_df['occupation_cd1'].isin(adjacent_categories)
            mask &= category_mask

        # Salary filtering
        if user_prefs.get('preferred_salary_min'):
            salary_mask = self._create_salary_mask(jobs_df, user_prefs['preferred_salary_min'])
            mask &= salary_mask

        # Remove recently applied jobs
        if recent_apps:
            mask &= ~jobs_df['job_id'].isin(recent_apps)

        # Remove blocked companies
        if blocked_companies:
            mask &= ~jobs_df['endcl_cd'].isin(blocked_companies)

        filtered_df = jobs_df[mask].copy()

        # If still too many jobs, apply additional smart filtering
        if len(filtered_df) > INITIAL_FILTERING_TARGET:
            filtered_df = await self._apply_smart_reduction(filtered_df, user_prefs)

        logger.debug(f"Initial filtering: {len(jobs_df)} → {len(filtered_df)} jobs")
        return filtered_df

    async def _calculate_scores_parallel(self, user: Dict[str, Any], jobs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate scores in parallel chunks for efficiency
        """
        if jobs_df.empty:
            return pd.DataFrame()

        # Create user DataFrame for scoring engine
        user_df = pd.DataFrame([{
            'user_id': user['user_id'],
            'estimated_pref_cd': user.get('estimated_pref_cd'),
            'estimated_city_cd': user.get('estimated_city_cd'),
            'age_group': user.get('age_group'),
            'gender': user.get('gender')
        }])

        # Process in chunks for memory efficiency
        chunk_results = []
        n_jobs = len(jobs_df)

        for i in range(0, n_jobs, SCORING_CHUNK_SIZE):
            chunk_jobs = jobs_df.iloc[i:i + SCORING_CHUNK_SIZE].copy()

            # Use scoring engine's vectorized methods
            base_scores = self.scoring_engine.calculate_base_scores_vectorized(chunk_jobs)
            seo_scores = await self.scoring_engine._calculate_seo_scores_vectorized(user_df, chunk_jobs)
            personal_scores = await self.scoring_engine._calculate_personal_scores_vectorized(user_df, chunk_jobs)

            # Calculate total scores
            weights = {'base': 0.4, 'seo': 0.3, 'personal': 0.3}
            total_scores = (
                base_scores * weights['base'] +
                seo_scores * weights['seo'] +
                personal_scores * weights['personal']
            )

            # Add scores to chunk
            chunk_jobs = chunk_jobs.copy()
            chunk_jobs['base_score'] = base_scores
            chunk_jobs['seo_score'] = seo_scores
            chunk_jobs['personal_score'] = personal_scores
            chunk_jobs['total_score'] = total_scores

            chunk_results.append(chunk_jobs)

        # Combine all chunks
        scored_df = pd.concat(chunk_results, ignore_index=True)

        # Sort by total score
        scored_df = scored_df.sort_values('total_score', ascending=False)

        return scored_df

    async def _apply_diversity_rules(self, jobs_df: pd.DataFrame, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply category diversity rules:
        - Maximum 10 jobs per major category
        - At least 3 different categories if possible
        - Maintain score ordering within constraints
        """
        if jobs_df.empty:
            return []

        # Get user's preferred categories for prioritization
        user_prefs = await self._get_user_preferences_cached(user['user_id'])
        preferred_categories = set(user_prefs.get('preferred_categories', []))

        selected_jobs = []
        category_counts = defaultdict(int)
        seen_categories = set()

        # Sort by score (already sorted from previous step)
        for _, job in jobs_df.iterrows():
            job_dict = job.to_dict()
            category = job_dict.get('occupation_cd1')

            if pd.isna(category):
                category = 'unknown'

            # Check category limits
            if category_counts[category] >= MAX_JOBS_PER_CATEGORY:
                continue

            # Prioritize preferred categories
            if category in preferred_categories or category_counts[category] < 3:
                selected_jobs.append(job_dict)
                category_counts[category] += 1
                seen_categories.add(category)

                if len(selected_jobs) >= FINAL_SELECTION_LIMIT:
                    break
            elif len(seen_categories) >= MIN_CATEGORIES_DIVERSITY:
                selected_jobs.append(job_dict)
                category_counts[category] += 1
                seen_categories.add(category)

                if len(selected_jobs) >= FINAL_SELECTION_LIMIT:
                    break

        # If we don't have enough jobs, fill with remaining high-scoring jobs
        if len(selected_jobs) < FINAL_SELECTION_LIMIT:
            selected_job_ids = {job['job_id'] for job in selected_jobs}

            for _, job in jobs_df.iterrows():
                if len(selected_jobs) >= FINAL_SELECTION_LIMIT:
                    break

                job_dict = job.to_dict()
                if job_dict['job_id'] not in selected_job_ids:
                    selected_jobs.append(job_dict)

        logger.debug(f"Diversity rules applied: {len(seen_categories)} categories, "
                    f"counts: {dict(category_counts)}")

        return selected_jobs

    async def _get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Load user data efficiently"""
        try:
            result = await self.db.execute(text("""
                SELECT
                    u.user_id,
                    u.email_hash,
                    u.age_group,
                    u.gender,
                    u.estimated_pref_cd,
                    u.estimated_city_cd,
                    u.is_active,
                    u.registration_date
                FROM users u
                WHERE u.user_id = :user_id AND u.is_active = true
                LIMIT 1
            """), {"user_id": user_id})

            row = result.fetchone()
            if not row:
                return None

            return {
                'user_id': row.user_id,
                'email_hash': row.email_hash,
                'age_group': row.age_group,
                'gender': row.gender,
                'estimated_pref_cd': row.estimated_pref_cd,
                'estimated_city_cd': row.estimated_city_cd,
                'is_active': row.is_active,
                'registration_date': row.registration_date
            }

        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None

    @lru_cache(maxsize=1000)
    async def _get_user_preferences_cached(self, user_id: int) -> Dict[str, Any]:
        """Load and cache user preferences"""
        cache_key = f"prefs_{user_id}"

        if cache_key in self._user_preferences_cache:
            cached_data = self._user_preferences_cache[cache_key]
            if time.time() - cached_data['timestamp'] < USER_PREFERENCES_CACHE_TTL:
                self._performance_stats['cache_hits'] += 1
                return cached_data['data']

        try:
            result = await self.db.execute(text("""
                SELECT
                    up.preferred_categories,
                    up.preferred_salary_min,
                    up.location_preference_radius,
                    up.preferred_areas,
                    up.preferred_work_styles
                FROM user_preferences up
                WHERE up.user_id = :user_id
                LIMIT 1
            """), {"user_id": user_id})

            row = result.fetchone()
            if row:
                data = {
                    'preferred_categories': row.preferred_categories or [],
                    'preferred_salary_min': row.preferred_salary_min,
                    'location_preference_radius': row.location_preference_radius or 10,
                    'preferred_areas': row.preferred_areas or [],
                    'preferred_work_styles': row.preferred_work_styles or []
                }
            else:
                data = {
                    'preferred_categories': [],
                    'preferred_salary_min': None,
                    'location_preference_radius': 10,
                    'preferred_areas': [],
                    'preferred_work_styles': []
                }

            # Cache the result
            self._user_preferences_cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            self._performance_stats['cache_misses'] += 1

            return data

        except Exception as e:
            logger.error(f"Error loading preferences for user {user_id}: {e}")
            return {}

    async def _get_recent_applications_cached(self, user_id: int) -> List[int]:
        """Get recent application history for filtering"""
        cache_key = f"recent_apps_{user_id}"

        if cache_key in self._recent_applications_cache:
            cached_data = self._recent_applications_cache[cache_key]
            if time.time() - cached_data['timestamp'] < RECENT_APPLICATIONS_CACHE_TTL:
                self._performance_stats['cache_hits'] += 1
                return cached_data['data']

        try:
            # Get jobs applied to in last 14 days
            result = await self.db.execute(text("""
                SELECT DISTINCT ua.job_id
                FROM user_actions ua
                WHERE ua.user_id = :user_id
                AND ua.action_type = 'application'
                AND ua.action_timestamp > CURRENT_DATE - INTERVAL '14 days'
            """), {"user_id": user_id})

            job_ids = [row.job_id for row in result.fetchall()]

            # Cache the result
            self._recent_applications_cache[cache_key] = {
                'data': job_ids,
                'timestamp': time.time()
            }
            self._performance_stats['cache_misses'] += 1

            return job_ids

        except Exception as e:
            logger.error(f"Error loading recent applications for user {user_id}: {e}")
            return []

    async def _get_blocked_companies_cached(self, user_id: int) -> List[str]:
        """Get blocked companies for user"""
        try:
            result = await self.db.execute(text("""
                SELECT bc.endcl_cd
                FROM blocked_companies bc
                WHERE bc.user_id = :user_id
                AND bc.is_active = true
            """), {"user_id": user_id})

            return [row.endcl_cd for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Error loading blocked companies for user {user_id}: {e}")
            return []

    async def _ensure_jobs_data_loaded(self):
        """Ensure job data is loaded and fresh"""
        current_time = time.time()

        if (self._jobs_df is None or
            self._last_jobs_load_time is None or
            current_time - self._last_jobs_load_time > self.jobs_cache_ttl):

            logger.info("Loading fresh job data...")
            self._jobs_df = await self.scoring_engine._batch_load_jobs_optimized()
            self._last_jobs_load_time = current_time
            logger.info(f"Loaded {len(self._jobs_df)} jobs")

    async def _get_jobs_dataframe(self) -> pd.DataFrame:
        """Get the current jobs DataFrame"""
        await self._ensure_jobs_data_loaded()
        return self._jobs_df.copy() if self._jobs_df is not None else pd.DataFrame()

    async def _create_location_mask(self, jobs_df: pd.DataFrame, user: Dict[str, Any]) -> pd.Series:
        """Create location filtering mask"""
        user_pref = user.get('estimated_pref_cd')
        if not user_pref:
            return pd.Series([True] * len(jobs_df))

        # Same prefecture
        same_pref_mask = jobs_df['prefecture_code'] == user_pref

        # Adjacent prefectures
        adjacent_prefs = await self._get_adjacent_prefectures(user_pref)
        adjacent_mask = jobs_df['prefecture_code'].isin(adjacent_prefs)

        return same_pref_mask | adjacent_mask

    def _create_salary_mask(self, jobs_df: pd.DataFrame, min_salary: int) -> pd.Series:
        """Create salary filtering mask"""
        # Convert all salaries to hourly equivalent for comparison
        hourly_equivalents = jobs_df['min_salary'].copy()

        # Adjust based on salary type
        daily_mask = jobs_df['salary_type'] == 'daily'
        monthly_mask = jobs_df['salary_type'] == 'monthly'

        hourly_equivalents.loc[daily_mask] = hourly_equivalents.loc[daily_mask] / 8
        hourly_equivalents.loc[monthly_mask] = hourly_equivalents.loc[monthly_mask] / 160

        # Apply some tolerance (80% of preferred minimum)
        return hourly_equivalents >= (min_salary * 0.8)

    async def _apply_smart_reduction(self, jobs_df: pd.DataFrame, user_prefs: Dict[str, Any]) -> pd.DataFrame:
        """Apply smart reduction when too many jobs pass initial filtering"""
        if len(jobs_df) <= INITIAL_FILTERING_TARGET:
            return jobs_df

        # Prioritize based on user preferences and job quality indicators
        scoring_factors = []

        # Fee-based priority (higher fee = higher priority)
        fee_scores = jobs_df['fee'].fillna(0) / 5000
        scoring_factors.append(fee_scores * 0.3)

        # Salary attractiveness
        salary_scores = self._calculate_simple_salary_scores(jobs_df)
        scoring_factors.append(salary_scores * 0.3)

        # Company popularity (if available)
        if 'popularity_score' in jobs_df.columns:
            popularity_scores = jobs_df['popularity_score'].fillna(50) / 100
            scoring_factors.append(popularity_scores * 0.2)

        # Recency (newer jobs get higher priority)
        if 'posting_date' in jobs_df.columns:
            days_old = (datetime.now().date() - pd.to_datetime(jobs_df['posting_date']).dt.date).dt.days
            recency_scores = np.exp(-days_old / 30)  # Exponential decay
            scoring_factors.append(recency_scores * 0.2)

        # Combine all factors
        if scoring_factors:
            combined_score = sum(scoring_factors)
            jobs_df = jobs_df.copy()
            jobs_df['priority_score'] = combined_score
            jobs_df = jobs_df.nlargest(INITIAL_FILTERING_TARGET, 'priority_score')
            jobs_df = jobs_df.drop(columns=['priority_score'])
        else:
            # Fallback: random sampling
            jobs_df = jobs_df.sample(n=INITIAL_FILTERING_TARGET, random_state=42)

        return jobs_df

    def _calculate_simple_salary_scores(self, jobs_df: pd.DataFrame) -> pd.Series:
        """Simple salary scoring for pre-filtering"""
        min_salaries = jobs_df['min_salary'].fillna(0)
        salary_types = jobs_df['salary_type'].fillna('hourly')

        # Convert to hourly equivalent
        hourly_equivalents = min_salaries.copy()
        hourly_equivalents[salary_types == 'daily'] /= 8
        hourly_equivalents[salary_types == 'monthly'] /= 160

        # Simple scoring brackets
        scores = pd.Series([0.2] * len(jobs_df))  # Base score
        scores[hourly_equivalents >= 1000] = 0.4
        scores[hourly_equivalents >= 1200] = 0.6
        scores[hourly_equivalents >= 1500] = 0.8
        scores[hourly_equivalents >= 2000] = 1.0

        return scores

    async def _get_adjacent_prefectures(self, pref_code: str) -> List[str]:
        """Get adjacent prefectures with caching"""
        cache_key = f"adj_pref_{pref_code}"

        if cache_key in self._location_distance_cache:
            return self._location_distance_cache[cache_key]

        try:
            result = await self.db.execute(text("""
                SELECT adjacent_prefectures
                FROM prefecture_adjacency
                WHERE pref_code = :pref_code
                LIMIT 1
            """), {"pref_code": pref_code})

            row = result.fetchone()
            adjacent = row.adjacent_prefectures if row else []

            self._location_distance_cache[cache_key] = adjacent
            return adjacent

        except Exception as e:
            logger.error(f"Error getting adjacent prefectures for {pref_code}: {e}")
            return []

    async def _get_adjacent_categories(self, category_codes: List[int]) -> List[int]:
        """Get adjacent/similar categories"""
        try:
            result = await self.db.execute(text("""
                SELECT DISTINCT om2.code
                FROM occupation_master om1
                JOIN occupation_master om2 ON om1.major_category_code = om2.major_category_code
                WHERE om1.code = ANY(:category_codes)
                AND om2.code != ALL(:category_codes)
            """), {"category_codes": category_codes})

            return [row.code for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Error getting adjacent categories: {e}")
            return []

    def _format_salary_display(self, job_data: Dict[str, Any]) -> str:
        """Format salary for display"""
        min_salary = job_data.get('min_salary')
        max_salary = job_data.get('max_salary')
        salary_type = job_data.get('salary_type', 'hourly')

        if not min_salary:
            return "応相談"

        unit = {"hourly": "円/時", "daily": "円/日", "monthly": "円/月"}.get(salary_type, "円")

        if max_salary and max_salary != min_salary:
            return f"{min_salary:,}～{max_salary:,}{unit}"
        else:
            return f"{min_salary:,}{unit}"

    def _format_location_display(self, job_data: Dict[str, Any]) -> str:
        """Format location for display"""
        parts = []

        if job_data.get('prefecture_name'):
            parts.append(job_data['prefecture_name'])

        if job_data.get('city_name'):
            parts.append(job_data['city_name'])

        if job_data.get('station_name'):
            parts.append(f"{job_data['station_name']}駅")

        return " ".join(parts) if parts else "勤務地詳細未設定"

    def _extract_features(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract job features for display"""
        features = []

        if job_data.get('has_daily_payment'):
            features.append("日払い")
        if job_data.get('has_weekly_payment'):
            features.append("週払い")
        if job_data.get('has_no_experience'):
            features.append("未経験歓迎")
        if job_data.get('has_student_welcome'):
            features.append("学生歓迎")
        if job_data.get('has_remote_work'):
            features.append("リモートワーク")
        if job_data.get('has_transportation'):
            features.append("交通費支給")
        if job_data.get('has_high_income'):
            features.append("高収入")

        return features

    def _update_performance_stats(self, execution_time: float, count: int):
        """Update performance statistics"""
        self._performance_stats['total_selections'] += count

        if self._performance_stats['avg_selection_time'] == 0:
            self._performance_stats['avg_selection_time'] = execution_time
        else:
            # Exponential moving average
            alpha = 0.1
            self._performance_stats['avg_selection_time'] = (
                alpha * execution_time +
                (1 - alpha) * self._performance_stats['avg_selection_time']
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_cache_ops = self._performance_stats['cache_hits'] + self._performance_stats['cache_misses']
        cache_hit_rate = (
            self._performance_stats['cache_hits'] / total_cache_ops
            if total_cache_ops > 0 else 0
        )

        return {
            **self._performance_stats,
            'avg_selection_time_ms': self._performance_stats['avg_selection_time'] * 1000,
            'cache_hit_rate': cache_hit_rate,
            'performance_target_ms': PERFORMANCE_TARGET_MS,
            'target_achieved': self._performance_stats['avg_selection_time'] * 1000 <= PERFORMANCE_TARGET_MS,
            'cache_sizes': {
                'user_preferences': len(self._user_preferences_cache),
                'recent_applications': len(self._recent_applications_cache),
                'location_distance': len(self._location_distance_cache),
                'blocked_companies': len(self._blocked_companies_cache)
            }
        }

    def clear_caches(self, cache_types: List[str] = None):
        """Clear caches"""
        if cache_types is None:
            cache_types = ['all']

        if 'all' in cache_types or 'user_prefs' in cache_types:
            self._user_preferences_cache.clear()

        if 'all' in cache_types or 'recent_apps' in cache_types:
            self._recent_applications_cache.clear()

        if 'all' in cache_types or 'location' in cache_types:
            self._location_distance_cache.clear()

        if 'all' in cache_types or 'blocked' in cache_types:
            self._blocked_companies_cache.clear()

        if 'all' in cache_types or 'jobs' in cache_types:
            self._jobs_df = None
            self._last_jobs_load_time = None

        logger.info(f"Caches cleared: {cache_types}")

    async def apply_business_rules(self, jobs: List[Dict[str, Any]], user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply additional business rules (e.g., no expired jobs)"""
        if not jobs:
            return jobs

        filtered_jobs = []
        current_date = datetime.now().date()

        for job in jobs:
            # Check if job is not expired
            posting_date = job.get('posting_date')
            if posting_date:
                if isinstance(posting_date, str):
                    posting_date = datetime.strptime(posting_date, '%Y-%m-%d').date()

                # Jobs older than 60 days are considered expired
                if (current_date - posting_date).days > 60:
                    continue

            # Check if job meets minimum quality standards
            if job.get('total_score', 0) < 10:  # Minimum score threshold
                continue

            # Add any other business rules here

            filtered_jobs.append(job)

        return filtered_jobs

    async def calculate_location_distance(self, user_location: Dict[str, Any], job_locations: List[Dict[str, Any]]) -> List[float]:
        """Vectorized distance calculation for filtering"""
        # Simplified distance calculation based on prefecture/city codes
        user_pref = user_location.get('prefecture_code')
        user_city = user_location.get('city_code')

        distances = []

        for job_loc in job_locations:
            job_pref = job_loc.get('prefecture_code')
            job_city = job_loc.get('city_code')

            if user_pref == job_pref:
                if user_city == job_city:
                    distance = 0.0  # Same city
                else:
                    distance = 5.0  # Same prefecture, different city
            else:
                # Check if adjacent prefecture
                adjacent_prefs = await self._get_adjacent_prefectures(user_pref)
                if job_pref in adjacent_prefs:
                    distance = 15.0  # Adjacent prefecture
                else:
                    distance = 50.0  # Far prefecture

            distances.append(distance)

        return distances