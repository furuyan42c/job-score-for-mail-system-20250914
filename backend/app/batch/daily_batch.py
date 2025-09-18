"""
Daily batch processing system for job matching platform
Runs at 3:00 AM JST every day

This module handles:
1. CSV Import (100K jobs)
2. User Matching (10K users)
3. Email Generation
4. Delivery Preparation
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import aiofiles
import pandas as pd
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

from app.core.database import get_async_session
from app.models.user import User
from app.models.job import Job
from app.models.batch_execution import BatchExecution
from app.services.job_selector import JobSelectorService
from app.services.scoring_engine import ScoringEngine
from app.services.email_generator import EmailGenerator
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Batch configuration
BATCH_CONFIG = {
    'csv_path': '/data/import/jobs/',
    'batch_size': 100,
    'max_parallel': 10,
    'checkpoint_interval': 1000,
    'email_queue': 'email_delivery_queue',
    'alert_recipients': ['admin@example.com'],
    'performance_targets': {
        'total_runtime': 1800,  # 30 minutes
        'import_time': 300,     # 5 minutes
        'matching_time': 1200,  # 20 minutes
        'email_time': 300       # 5 minutes
    }
}


class BatchMetrics:
    """Tracks batch execution metrics"""

    def __init__(self):
        self.start_time = None
        self.phase_times = {}
        self.processed_counts = {}
        self.error_counts = {}

    def start_phase(self, phase: str):
        """Start timing a phase"""
        self.phase_times[phase] = {'start': datetime.now()}

    def end_phase(self, phase: str):
        """End timing a phase"""
        if phase in self.phase_times:
            self.phase_times[phase]['end'] = datetime.now()
            self.phase_times[phase]['duration'] = (
                self.phase_times[phase]['end'] - self.phase_times[phase]['start']
            ).total_seconds()

    def increment_processed(self, category: str, count: int = 1):
        """Increment processed count"""
        self.processed_counts[category] = self.processed_counts.get(category, 0) + count

    def increment_errors(self, category: str, count: int = 1):
        """Increment error count"""
        self.error_counts[category] = self.error_counts.get(category, 0) + count


class DailyBatchProcessor:
    """
    Main batch processor that orchestrates daily operations:
    1. CSV Import (100K jobs)
    2. User Matching (10K users)
    3. Email Generation
    4. Delivery Preparation
    """

    def __init__(self, config: Dict = None):
        self.config = config or BATCH_CONFIG
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Tokyo'))
        self.job_selector = JobSelectorService()
        self.scoring_engine = ScoringEngine()
        self.email_generator = EmailGenerator()
        self.metrics = BatchMetrics()
        self.batch_id = None
        self.checkpoint_data = {}

    async def run_daily_batch(self):
        """
        Main batch execution flow
        Expected runtime: ~30 minutes total
        """
        self.batch_id = f"daily_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.metrics.start_time = datetime.now()

        logger.info(f"Starting daily batch {self.batch_id}")

        try:
            # Create batch execution record
            await self._create_batch_record("RUNNING")

            # Phase 1: Initialization (1 minute)
            await self._initialization_phase()

            # Phase 2: Data Import (5 minutes)
            jobs_df = await self._data_import_phase()

            # Phase 3: Matching Processing (20 minutes)
            matching_results = await self._matching_phase()

            # Phase 4: Email Generation (5 minutes)
            await self._email_generation_phase(matching_results)

            # Phase 5: Cleanup and Reporting (1 minute)
            await self._cleanup_and_reporting_phase()

            await self._update_batch_record("COMPLETED")
            logger.info(f"Daily batch {self.batch_id} completed successfully")

        except Exception as e:
            logger.error(f"Daily batch {self.batch_id} failed: {str(e)}")
            logger.error(traceback.format_exc())
            await self.handle_batch_failure("main_execution", e)
            await self._update_batch_record("FAILED", str(e))

    async def _initialization_phase(self):
        """Phase 1: Initialize services and validate prerequisites"""
        self.metrics.start_phase('initialization')
        logger.info("Phase 1: Initialization starting")

        try:
            # Validate configuration
            await self._validate_configuration()

            # Initialize services
            await self.job_selector.initialize()
            await self.scoring_engine.initialize()
            await self.email_generator.initialize()

            # Check prerequisites
            await self._check_prerequisites()

            logger.info("Phase 1: Initialization completed")

        except Exception as e:
            logger.error(f"Initialization phase failed: {str(e)}")
            raise

        finally:
            self.metrics.end_phase('initialization')

    async def _data_import_phase(self) -> pd.DataFrame:
        """Phase 2: Import and validate job data from CSV"""
        self.metrics.start_phase('data_import')
        logger.info("Phase 2: Data import starting")

        try:
            # Find latest CSV file
            csv_files = await self._find_csv_files()
            if not csv_files:
                raise Exception("No CSV files found for import")

            latest_csv = csv_files[0]  # Assuming sorted by date
            logger.info(f"Importing from {latest_csv}")

            # Import jobs from CSV
            jobs_df = await self.import_jobs_from_csv(latest_csv)

            self.metrics.increment_processed('jobs_imported', len(jobs_df))
            logger.info(f"Phase 2: Imported {len(jobs_df)} jobs")

            return jobs_df

        except Exception as e:
            logger.error(f"Data import phase failed: {str(e)}")
            raise

        finally:
            self.metrics.end_phase('data_import')

    async def _matching_phase(self) -> Dict:
        """Phase 3: Process matching for all active users"""
        self.metrics.start_phase('matching')
        logger.info("Phase 3: User matching starting")

        try:
            # Load active users
            users = await self._load_active_users()
            logger.info(f"Processing matching for {len(users)} users")

            # Process matching in batches
            matching_results = await self.process_user_matching(users)

            self.metrics.increment_processed('users_matched', len(users))
            logger.info(f"Phase 3: Completed matching for {len(users)} users")

            return matching_results

        except Exception as e:
            logger.error(f"Matching phase failed: {str(e)}")
            raise

        finally:
            self.metrics.end_phase('matching')

    async def _email_generation_phase(self, matching_results: Dict):
        """Phase 4: Generate and queue emails"""
        self.metrics.start_phase('email_generation')
        logger.info("Phase 4: Email generation starting")

        try:
            # Generate emails
            emails_generated = await self.generate_emails(matching_results)

            self.metrics.increment_processed('emails_generated', emails_generated)
            logger.info(f"Phase 4: Generated {emails_generated} emails")

        except Exception as e:
            logger.error(f"Email generation phase failed: {str(e)}")
            raise

        finally:
            self.metrics.end_phase('email_generation')

    async def _cleanup_and_reporting_phase(self):
        """Phase 5: Cleanup and generate reports"""
        self.metrics.start_phase('cleanup')
        logger.info("Phase 5: Cleanup and reporting starting")

        try:
            # Archive processed files
            await self._archive_processed_files()

            # Generate batch report
            report = await self.generate_batch_report()

            # Send success notification
            await self.send_alert_notification(
                f"Daily batch {self.batch_id} completed successfully"
            )

            logger.info("Phase 5: Cleanup and reporting completed")

        except Exception as e:
            logger.error(f"Cleanup phase failed: {str(e)}")
            # Don't raise - this is non-critical

        finally:
            self.metrics.end_phase('cleanup')

    async def import_jobs_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Import 100K jobs from CSV
        - Validate data format
        - Handle encoding (Shift-JIS/UTF-8)
        - Deduplicate entries
        - Update database
        """
        logger.info(f"Starting CSV import from {csv_path}")

        try:
            # Try different encodings
            encodings = ['utf-8', 'shift-jis', 'cp932']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    logger.info(f"Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise Exception("Could not read CSV with any supported encoding")

            # Validate CSV format
            await self.validate_csv_format(df)

            # Clean and deduplicate
            df = await self._clean_job_data(df)
            df = df.drop_duplicates(subset=['external_id'], keep='last')

            # Validate job data
            await self.validate_job_data(df)

            # Bulk insert to database
            await self._bulk_insert_jobs(df)

            logger.info(f"Successfully imported {len(df)} jobs")
            return df

        except Exception as e:
            logger.error(f"CSV import failed: {str(e)}")
            raise

    async def process_user_matching(self, users: List[User]) -> Dict:
        """
        Process matching for all active users
        - Batch size: 100 users
        - Parallel processing: 10 concurrent batches
        - Progress tracking
        - Error recovery
        """
        logger.info(f"Starting user matching for {len(users)} users")

        matching_results = {}
        batch_size = self.config['batch_size']
        max_parallel = self.config['max_parallel']

        try:
            # Split users into batches
            user_batches = [
                users[i:i + batch_size]
                for i in range(0, len(users), batch_size)
            ]

            # Process batches in parallel
            for i in range(0, len(user_batches), max_parallel):
                parallel_batches = user_batches[i:i + max_parallel]

                # Create tasks for parallel processing
                tasks = [
                    self._process_user_batch(batch, i + j)
                    for j, batch in enumerate(parallel_batches)
                ]

                # Execute parallel tasks
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Merge results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing failed: {str(result)}")
                        self.metrics.increment_errors('batch_processing')
                    else:
                        matching_results.update(result)

                # Log progress
                processed = min((i + max_parallel) * batch_size, len(users))
                progress = (processed / len(users)) * 100
                logger.info(f"Matching progress: {processed}/{len(users)} ({progress:.1f}%)")

                # Save checkpoint
                if processed % self.config['checkpoint_interval'] == 0:
                    await self._save_checkpoint('matching', matching_results)

            logger.info(f"Completed matching for {len(matching_results)} users")
            return matching_results

        except Exception as e:
            logger.error(f"User matching failed: {str(e)}")
            raise

    async def generate_emails(self, matching_results: Dict) -> int:
        """
        Generate personalized emails
        - Use email templates
        - Include top 40 jobs per user
        - Format with categories
        - Queue for delivery
        """
        logger.info(f"Generating emails for {len(matching_results)} users")

        emails_generated = 0

        try:
            # Process emails in parallel batches
            user_ids = list(matching_results.keys())
            batch_size = self.config['batch_size']

            for i in range(0, len(user_ids), batch_size):
                batch_user_ids = user_ids[i:i + batch_size]

                # Generate emails for batch
                tasks = [
                    self._generate_user_email(user_id, matching_results[user_id])
                    for user_id in batch_user_ids
                ]

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Count successful generations
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Email generation failed: {str(result)}")
                        self.metrics.increment_errors('email_generation')
                    else:
                        emails_generated += 1

                # Log progress
                progress = ((i + batch_size) / len(user_ids)) * 100
                logger.info(f"Email generation progress: {emails_generated} emails ({progress:.1f}%)")

            return emails_generated

        except Exception as e:
            logger.error(f"Email generation failed: {str(e)}")
            raise

    async def _process_user_batch(self, user_batch: List[User], batch_id: int) -> Dict:
        """Process a batch of users for matching"""
        batch_results = {}

        try:
            for user in user_batch:
                # Get job recommendations for user
                job_matches = await self.job_selector.get_recommendations(
                    user_id=user.id,
                    limit=40
                )

                # Calculate scores
                scored_matches = await self.scoring_engine.calculate_scores(
                    user=user,
                    jobs=job_matches
                )

                batch_results[user.id] = scored_matches

            return batch_results

        except Exception as e:
            logger.error(f"Batch {batch_id} processing failed: {str(e)}")
            raise

    async def _generate_user_email(self, user_id: int, job_matches: List) -> bool:
        """Generate email for a single user"""
        try:
            # Get user details
            async with get_async_session() as session:
                user = await session.get(User, user_id)

            if not user:
                raise Exception(f"User {user_id} not found")

            # Generate email content
            email_content = await self.email_generator.generate_daily_email(
                user=user,
                job_matches=job_matches
            )

            # Queue for delivery
            await self._queue_email_for_delivery(user, email_content)

            return True

        except Exception as e:
            logger.error(f"Failed to generate email for user {user_id}: {str(e)}")
            raise

    async def handle_batch_failure(self, phase: str, error: Exception):
        """Handle failures with retry logic"""
        logger.error(f"Batch failure in phase '{phase}': {str(error)}")

        try:
            # Send alert notification
            await self.send_alert_notification(
                f"Daily batch {self.batch_id} failed in phase '{phase}': {str(error)}"
            )

            # Check if recovery is possible
            if phase in ['matching', 'email_generation']:
                logger.info("Attempting recovery from checkpoint")
                await self.recover_from_checkpoint()

        except Exception as recovery_error:
            logger.error(f"Recovery failed: {str(recovery_error)}")

    async def recover_from_checkpoint(self):
        """Resume from last successful checkpoint"""
        try:
            checkpoint_file = f"/tmp/batch_checkpoint_{self.batch_id}.json"

            if Path(checkpoint_file).exists():
                async with aiofiles.open(checkpoint_file, 'r') as f:
                    self.checkpoint_data = json.loads(await f.read())

                logger.info(f"Recovered checkpoint data: {list(self.checkpoint_data.keys())}")
            else:
                logger.warning("No checkpoint file found for recovery")

        except Exception as e:
            logger.error(f"Checkpoint recovery failed: {str(e)}")
            raise

    async def send_alert_notification(self, message: str):
        """Send alerts to administrators"""
        try:
            # In a real implementation, this would send emails or Slack notifications
            logger.critical(f"ALERT: {message}")

            # Store alert in database for monitoring dashboard
            async with get_async_session() as session:
                alert_record = {
                    'batch_id': self.batch_id,
                    'message': message,
                    'created_at': datetime.now(),
                    'severity': 'HIGH'
                }
                # Save to alerts table

        except Exception as e:
            logger.error(f"Failed to send alert notification: {str(e)}")

    async def process_in_parallel(self, items, processor_func, max_concurrent=10):
        """Generic parallel processor"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(item):
            async with semaphore:
                return await processor_func(item)

        tasks = [process_with_semaphore(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def optimize_database_connections(self):
        """Connection pooling for batch operations"""
        # Configure connection pool for batch operations
        pass

    async def generate_batch_report(self) -> Dict:
        """Generate execution report with metrics"""
        total_runtime = (datetime.now() - self.metrics.start_time).total_seconds()

        report = {
            'batch_id': self.batch_id,
            'start_time': self.metrics.start_time.isoformat(),
            'total_runtime': total_runtime,
            'phase_times': self.metrics.phase_times,
            'processed_counts': self.metrics.processed_counts,
            'error_counts': self.metrics.error_counts,
            'performance_targets': self.config['performance_targets'],
            'success_rate': self._calculate_success_rate()
        }

        # Save report to file
        report_file = f"/data/reports/batch_report_{self.batch_id}.json"
        async with aiofiles.open(report_file, 'w') as f:
            await f.write(json.dumps(report, indent=2, default=str))

        logger.info(f"Batch report saved to {report_file}")
        return report

    async def update_batch_status(self, status: str, progress: float):
        """Update batch status in monitoring table"""
        try:
            async with get_async_session() as session:
                await session.execute(
                    text("""
                        UPDATE batch_executions
                        SET status = :status, progress = :progress, updated_at = NOW()
                        WHERE batch_id = :batch_id
                    """),
                    {
                        'status': status,
                        'progress': progress,
                        'batch_id': self.batch_id
                    }
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to update batch status: {str(e)}")

    async def log_performance_metrics(self):
        """Log detailed performance metrics"""
        metrics = {
            'memory_usage': await self._get_memory_usage(),
            'cpu_usage': await self._get_cpu_usage(),
            'database_connections': await self._get_db_connection_count(),
            'processing_rate': await self._calculate_processing_rate()
        }

        logger.info(f"Performance metrics: {metrics}")

    async def validate_csv_format(self, df: pd.DataFrame):
        """Validate CSV structure and data types"""
        required_columns = [
            'external_id', 'title', 'company_name', 'location',
            'employment_type', 'salary_min', 'salary_max', 'description'
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise Exception(f"Missing required columns: {missing_columns}")

        logger.info("CSV format validation passed")

    async def validate_job_data(self, jobs: pd.DataFrame):
        """Validate job data integrity"""
        # Check for required fields
        required_fields = ['external_id', 'title', 'company_name']
        for field in required_fields:
            null_count = jobs[field].isnull().sum()
            if null_count > 0:
                logger.warning(f"Found {null_count} null values in {field}")

        # Validate salary ranges
        invalid_salary = jobs[
            (jobs['salary_min'] > jobs['salary_max']) &
            (jobs['salary_max'].notnull())
        ]
        if len(invalid_salary) > 0:
            logger.warning(f"Found {len(invalid_salary)} jobs with invalid salary ranges")

        logger.info("Job data validation completed")

    async def validate_matching_results(self, results: Dict):
        """Validate matching output"""
        if not results:
            raise Exception("No matching results generated")

        # Check result structure
        for user_id, matches in results.items():
            if not isinstance(matches, list):
                raise Exception(f"Invalid matches format for user {user_id}")

            if len(matches) > 40:
                logger.warning(f"User {user_id} has {len(matches)} matches (expected max 40)")

        logger.info(f"Matching validation passed for {len(results)} users")

    def schedule_daily_job(self):
        """Schedule the daily batch at 3:00 AM JST"""
        self.scheduler.add_job(
            self.run_daily_batch,
            CronTrigger(hour=3, minute=0, timezone='Asia/Tokyo'),
            id='daily_batch',
            name='Daily Job Matching Batch',
            max_instances=1,
            replace_existing=True
        )

        logger.info("Daily batch job scheduled for 3:00 AM JST")

    async def monitor_batch_progress(self):
        """Real-time monitoring of batch progress"""
        while True:
            try:
                # Calculate overall progress
                total_phases = 5
                completed_phases = len([
                    phase for phase, timing in self.metrics.phase_times.items()
                    if 'end' in timing
                ])

                progress = (completed_phases / total_phases) * 100

                # Estimate remaining time
                if completed_phases > 0:
                    avg_phase_time = sum([
                        timing.get('duration', 0)
                        for timing in self.metrics.phase_times.values()
                    ]) / completed_phases

                    remaining_time = avg_phase_time * (total_phases - completed_phases)
                else:
                    remaining_time = None

                # Update status
                await self.update_batch_status("RUNNING", progress)

                # Log progress
                logger.info(f"Batch progress: {progress:.1f}% complete")
                if remaining_time:
                    logger.info(f"Estimated remaining time: {remaining_time:.0f} seconds")

                # Break if batch is complete
                if completed_phases >= total_phases:
                    break

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Progress monitoring error: {str(e)}")
                await asyncio.sleep(60)

    # Helper methods
    async def _validate_configuration(self):
        """Validate batch configuration"""
        required_keys = ['csv_path', 'batch_size', 'max_parallel']
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise Exception(f"Missing configuration keys: {missing_keys}")

    async def _check_prerequisites(self):
        """Check prerequisites for batch execution"""
        # Check if previous batch is still running
        async with get_async_session() as session:
            running_batches = await session.execute(
                text("SELECT COUNT(*) FROM batch_executions WHERE status = 'RUNNING'")
            )
            if running_batches.scalar() > 0:
                raise Exception("Another batch is already running")

    async def _find_csv_files(self) -> List[str]:
        """Find available CSV files for import"""
        csv_path = Path(self.config['csv_path'])
        if not csv_path.exists():
            return []

        csv_files = sorted(csv_path.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True)
        return [str(f) for f in csv_files]

    async def _load_active_users(self) -> List[User]:
        """Load active users for matching"""
        async with get_async_session() as session:
            result = await session.execute(
                select(User).where(
                    User.is_active == True,
                    User.email_notifications_enabled == True
                ).limit(10000)
            )
            return result.scalars().all()

    async def _clean_job_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize job data"""
        # Remove duplicates
        df = df.drop_duplicates()

        # Clean text fields
        text_columns = ['title', 'company_name', 'description']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Normalize salary values
        if 'salary_min' in df.columns:
            df['salary_min'] = pd.to_numeric(df['salary_min'], errors='coerce')
        if 'salary_max' in df.columns:
            df['salary_max'] = pd.to_numeric(df['salary_max'], errors='coerce')

        return df

    async def _bulk_insert_jobs(self, df: pd.DataFrame):
        """Bulk insert jobs to database"""
        # Convert DataFrame to dict records for bulk insert
        job_records = df.to_dict('records')

        async with get_async_session() as session:
            # Use bulk insert for performance
            await session.execute(
                text("""
                    INSERT INTO jobs (external_id, title, company_name, location,
                                    employment_type, salary_min, salary_max, description,
                                    created_at, updated_at)
                    VALUES (:external_id, :title, :company_name, :location,
                           :employment_type, :salary_min, :salary_max, :description,
                           NOW(), NOW())
                    ON CONFLICT (external_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        company_name = EXCLUDED.company_name,
                        location = EXCLUDED.location,
                        employment_type = EXCLUDED.employment_type,
                        salary_min = EXCLUDED.salary_min,
                        salary_max = EXCLUDED.salary_max,
                        description = EXCLUDED.description,
                        updated_at = NOW()
                """),
                job_records
            )
            await session.commit()

    async def _save_checkpoint(self, phase: str, data: Dict):
        """Save checkpoint data for recovery"""
        checkpoint_file = f"/tmp/batch_checkpoint_{self.batch_id}.json"

        checkpoint_data = {
            'phase': phase,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        async with aiofiles.open(checkpoint_file, 'w') as f:
            await f.write(json.dumps(checkpoint_data, default=str))

    async def _queue_email_for_delivery(self, user: User, email_content: Dict):
        """Queue email for delivery system"""
        # In a real implementation, this would use a message queue like Redis or RabbitMQ
        email_record = {
            'user_id': user.id,
            'email': user.email,
            'subject': email_content['subject'],
            'body': email_content['body'],
            'scheduled_for': datetime.now() + timedelta(hours=1),  # Deliver 1 hour later
            'status': 'QUEUED'
        }

        # Save to email queue table
        async with get_async_session() as session:
            await session.execute(
                text("""
                    INSERT INTO email_queue (user_id, email, subject, body, scheduled_for, status, created_at)
                    VALUES (:user_id, :email, :subject, :body, :scheduled_for, :status, NOW())
                """),
                email_record
            )
            await session.commit()

    async def _archive_processed_files(self):
        """Archive processed CSV files"""
        csv_files = await self._find_csv_files()
        archive_dir = Path('/data/archive/')
        archive_dir.mkdir(exist_ok=True)

        for csv_file in csv_files[:1]:  # Archive the file we processed
            source = Path(csv_file)
            dest = archive_dir / f"{source.stem}_{self.batch_id}{source.suffix}"
            source.rename(dest)
            logger.info(f"Archived {csv_file} to {dest}")

    async def _create_batch_record(self, status: str):
        """Create batch execution record"""
        async with get_async_session() as session:
            await session.execute(
                text("""
                    INSERT INTO batch_executions (batch_id, status, started_at, created_at)
                    VALUES (:batch_id, :status, NOW(), NOW())
                """),
                {
                    'batch_id': self.batch_id,
                    'status': status
                }
            )
            await session.commit()

    async def _update_batch_record(self, status: str, error_message: str = None):
        """Update batch execution record"""
        async with get_async_session() as session:
            await session.execute(
                text("""
                    UPDATE batch_executions
                    SET status = :status,
                        ended_at = NOW(),
                        error_message = :error_message,
                        updated_at = NOW()
                    WHERE batch_id = :batch_id
                """),
                {
                    'status': status,
                    'error_message': error_message,
                    'batch_id': self.batch_id
                }
            )
            await session.commit()

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_processed = sum(self.metrics.processed_counts.values())
        total_errors = sum(self.metrics.error_counts.values())

        if total_processed == 0:
            return 0.0

        return ((total_processed - total_errors) / total_processed) * 100

    async def _get_memory_usage(self) -> int:
        """Get current memory usage in MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss // 1024 // 1024

    async def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        import psutil
        return psutil.cpu_percent()

    async def _get_db_connection_count(self) -> int:
        """Get current database connection count"""
        async with get_async_session() as session:
            result = await session.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            )
            return result.scalar()

    async def _calculate_processing_rate(self) -> float:
        """Calculate items processed per second"""
        if not self.metrics.start_time:
            return 0.0

        elapsed = (datetime.now() - self.metrics.start_time).total_seconds()
        total_processed = sum(self.metrics.processed_counts.values())

        return total_processed / elapsed if elapsed > 0 else 0.0


# Batch scheduler instance
batch_processor = DailyBatchProcessor()

async def start_batch_scheduler():
    """Start the batch scheduler"""
    batch_processor.schedule_daily_job()
    batch_processor.scheduler.start()
    logger.info("Daily batch scheduler started")

async def stop_batch_scheduler():
    """Stop the batch scheduler"""
    batch_processor.scheduler.shutdown()
    logger.info("Daily batch scheduler stopped")

if __name__ == "__main__":
    # For testing purposes
    async def main():
        await batch_processor.run_daily_batch()

    asyncio.run(main())