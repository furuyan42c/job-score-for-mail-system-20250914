#!/usr/bin/env python3
"""
T028: Scoring Batch Service Utility Methods - REFACTOR Phase

Utility methods for the refactored ScoringBatchService including:
- Performance monitoring and metrics
- Memory management and optimization
- Progress tracking and reporting
- Cache management
- Data chunking and filtering
"""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ScoringBatchUtils:
    """Utility methods for scoring batch operations"""

    @staticmethod
    def chunk_list(items: List, chunk_size: int) -> List[List]:
        """Split list into chunks of specified size"""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]

    @staticmethod
    async def filter_scores_by_threshold(scores: List[Dict], threshold: float) -> List[Dict]:
        """Filter scores below threshold"""
        try:
            filtered = [
                score for score in scores
                if score.get('composite_score', 0) >= threshold
            ]

            logger.debug("Filtered %d/%d scores above threshold %.3f",
                        len(filtered), len(scores), threshold)
            return filtered

        except Exception as e:
            logger.error("Error filtering scores: %s", e)
            return scores

    @staticmethod
    async def validate_score_quality(scores: List[Dict]) -> Dict[str, Any]:
        """Validate score quality and return validation results"""
        try:
            if not scores:
                return {'valid': True, 'message': 'No scores to validate'}

            validation_results = {
                'total_scores': len(scores),
                'valid_scores': 0,
                'invalid_scores': 0,
                'validation_errors': [],
                'quality_metrics': {}
            }

            for i, score in enumerate(scores):
                try:
                    # Validate score structure
                    required_fields = ['user_id', 'job_id', 'basic_score', 'seo_score',
                                     'personalized_score', 'composite_score']

                    missing_fields = [field for field in required_fields if field not in score]
                    if missing_fields:
                        validation_results['validation_errors'].append(
                            f"Score {i}: Missing fields {missing_fields}"
                        )
                        validation_results['invalid_scores'] += 1
                        continue

                    # Validate score ranges
                    score_fields = ['basic_score', 'seo_score', 'personalized_score', 'composite_score']
                    invalid_ranges = []

                    for field in score_fields:
                        value = score.get(field, 0)
                        if not (0 <= value <= 1):
                            invalid_ranges.append(f"{field}={value}")

                    if invalid_ranges:
                        validation_results['validation_errors'].append(
                            f"Score {i}: Invalid ranges {invalid_ranges}"
                        )
                        validation_results['invalid_scores'] += 1
                        continue

                    validation_results['valid_scores'] += 1

                except Exception as e:
                    validation_results['validation_errors'].append(f"Score {i}: {str(e)}")
                    validation_results['invalid_scores'] += 1

            # Calculate quality metrics
            if validation_results['total_scores'] > 0:
                validation_results['quality_metrics'] = {
                    'validity_rate': validation_results['valid_scores'] / validation_results['total_scores'],
                    'average_composite_score': sum(
                        score.get('composite_score', 0)
                        for score in scores
                        if 'composite_score' in score
                    ) / len(scores),
                    'score_distribution': ScoringBatchUtils._calculate_score_distribution(scores)
                }

            validation_results['valid'] = validation_results['invalid_scores'] == 0

            return validation_results

        except Exception as e:
            logger.error("Error in score quality validation: %s", e)
            return {'valid': False, 'error': str(e)}

    @staticmethod
    def _calculate_score_distribution(scores: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of composite scores"""
        try:
            distribution = {
                '0.0-0.2': 0,
                '0.2-0.4': 0,
                '0.4-0.6': 0,
                '0.6-0.8': 0,
                '0.8-1.0': 0
            }

            for score in scores:
                composite = score.get('composite_score', 0)
                if composite < 0.2:
                    distribution['0.0-0.2'] += 1
                elif composite < 0.4:
                    distribution['0.2-0.4'] += 1
                elif composite < 0.6:
                    distribution['0.4-0.6'] += 1
                elif composite < 0.8:
                    distribution['0.6-0.8'] += 1
                else:
                    distribution['0.8-1.0'] += 1

            return distribution

        except Exception:
            return {}

    @staticmethod
    async def aggregate_scoring_results(partial_results: List[List[Dict]]) -> List[Dict]:
        """Aggregate scoring results from parallel workers"""
        try:
            aggregated = []

            for result_batch in partial_results:
                if isinstance(result_batch, list):
                    aggregated.extend(result_batch)
                else:
                    logger.warning("Skipping non-list result: %s", type(result_batch))

            # Remove duplicates based on user_id and job_id
            seen = set()
            deduplicated = []

            for result in aggregated:
                key = (result.get('user_id'), result.get('job_id'))
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(result)
                else:
                    logger.debug("Duplicate result removed for user %s, job %s",
                               result.get('user_id'), result.get('job_id'))

            logger.info("Aggregated %d results from %d batches, removed %d duplicates",
                       len(deduplicated), len(partial_results), len(aggregated) - len(deduplicated))

            return deduplicated

        except Exception as e:
            logger.error("Error aggregating results: %s", e)
            return []


# Add these methods to the main ScoringBatchService class
def extend_scoring_batch_service():
    """Extend ScoringBatchService with utility methods"""

    def _chunk_list(self, items: List, chunk_size: int) -> List[List]:
        """Split list into chunks of specified size"""
        return list(ScoringBatchUtils.chunk_list(items, chunk_size))

    def _update_score_metrics(self, score_type: str, calculation_time: float):
        """Update metrics for score calculation"""
        try:
            self._metrics['scores_calculated'] += 1

            # Update average calculation time
            current_avg = self._metrics['average_score_time']
            total_scores = self._metrics['scores_calculated']

            if total_scores > 1:
                self._metrics['average_score_time'] = (
                    (current_avg * (total_scores - 1) + calculation_time) / total_scores
                )
            else:
                self._metrics['average_score_time'] = calculation_time

            logger.debug("Updated metrics for %s score: %.3fs", score_type, calculation_time)

        except Exception as e:
            logger.error("Error updating score metrics: %s", e)

    async def _memory_management_checkpoint(self):
        """Perform memory management checkpoint"""
        try:
            if self._job_cache and len(self._job_cache) > 10000:
                # Clear old cache entries
                logger.info("Clearing job cache (%d entries)", len(self._job_cache))
                self._job_cache.clear()

            if self._user_cache and len(self._user_cache) > 10000:
                # Clear old cache entries
                logger.info("Clearing user cache (%d entries)", len(self._user_cache))
                self._user_cache.clear()

        except Exception as e:
            logger.error("Error in memory management checkpoint: %s", e)

    async def initialize_progress_tracking(self, total_users: int, total_jobs: int):
        """Initialize progress tracking"""
        self._progress.update({
            'total_users': total_users,
            'total_jobs': total_jobs,
            'total_calculations': total_users * total_jobs,
            'processed_users': 0,
            'calculated_scores': 0,
            'failed_scores': 0,
            'start_time': datetime.now()
        })

        logger.info("Progress tracking initialized: %d users × %d jobs = %d total calculations",
                   total_users, total_jobs, total_users * total_jobs)

    async def update_progress(self, processed_users: int, calculated_scores: int):
        """Update progress tracking"""
        self._progress.update({
            'processed_users': processed_users,
            'calculated_scores': calculated_scores
        })

    async def get_progress_status(self) -> Dict[str, Any]:
        """Get current progress status"""
        try:
            total_calculations = self._progress.get('total_calculations', 0)
            calculated_scores = self._progress.get('calculated_scores', 0)

            progress_percentage = (
                (calculated_scores / total_calculations * 100)
                if total_calculations > 0 else 0
            )

            start_time = self._progress.get('start_time')
            elapsed_time = (
                (datetime.now() - start_time).total_seconds()
                if start_time else 0
            )

            return {
                'total_users': self._progress.get('total_users', 0),
                'total_jobs': self._progress.get('total_jobs', 0),
                'total_calculations': total_calculations,
                'processed_users': self._progress.get('processed_users', 0),
                'calculated_scores': calculated_scores,
                'failed_scores': self._progress.get('failed_scores', 0),
                'progress_percentage': round(progress_percentage, 2),
                'elapsed_seconds': round(elapsed_time, 2)
            }

        except Exception as e:
            logger.error("Error getting progress status: %s", e)
            return {'error': str(e)}

    # Add methods to ScoringBatchService
    ScoringBatchService._chunk_list = _chunk_list
    ScoringBatchService._update_score_metrics = _update_score_metrics
    ScoringBatchService._memory_management_checkpoint = _memory_management_checkpoint
    ScoringBatchService.initialize_progress_tracking = initialize_progress_tracking
    ScoringBatchService.update_progress = update_progress
    ScoringBatchService.get_progress_status = get_progress_status
    ScoringBatchService.filter_scores_by_threshold = ScoringBatchUtils.filter_scores_by_threshold
    ScoringBatchService.validate_score_quality = ScoringBatchUtils.validate_score_quality
    ScoringBatchService.aggregate_scoring_results = ScoringBatchUtils.aggregate_scoring_results


# Apply the extensions
if __name__ != "__main__":
    try:
        from app.services.scoring_batch import ScoringBatchService
        extend_scoring_batch_service()
        logger.info("Extended ScoringBatchService with utility methods")
    except ImportError:
        logger.warning("Could not extend ScoringBatchService - import failed")