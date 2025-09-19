"""
T070: Supabase Real-time Integration

Production-ready real-time integration with Supabase channels for:
- Job updates
- User notifications
- Matching results
- System status

Provides comprehensive channel management, event routing, and monitoring.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Set, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from supabase import Client
from app.core.supabase import get_supabase_client, SupabaseClient
from app.services.realtime_service import (
    RealtimeService, SubscriptionType, RealtimeMessage, get_realtime_service
)

# Configure logger
logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """Types of real-time channels"""
    JOB_UPDATES = "job_updates"
    USER_NOTIFICATIONS = "user_notifications"
    MATCHING_RESULTS = "matching_results"
    SYSTEM_STATUS = "system_status"
    EMAIL_PROCESSING = "email_processing"
    SCORE_CALCULATION = "score_calculation"
    AUDIT_LOGS = "audit_logs"


class EventType(Enum):
    """Types of real-time events"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CUSTOM = "CUSTOM"


@dataclass
class ChannelConfig:
    """Configuration for a real-time channel"""
    channel_id: str
    channel_type: ChannelType
    table_name: str
    schema: str = "public"
    event_types: List[EventType] = None
    filters: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None  # events per second
    buffer_size: int = 1000
    retry_count: int = 3
    auto_reconnect: bool = True
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.event_types is None:
            self.event_types = [EventType.INSERT, EventType.UPDATE, EventType.DELETE]


@dataclass
class ChannelMetrics:
    """Metrics for a real-time channel"""
    events_received: int = 0
    events_processed: int = 0
    events_failed: int = 0
    last_event_time: Optional[float] = None
    average_processing_time: float = 0.0
    error_rate: float = 0.0
    connection_count: int = 0
    bytes_transferred: int = 0


class ChannelManager:
    """Manages Supabase real-time channels with advanced features"""

    def __init__(self, supabase_client: Optional[SupabaseClient] = None):
        self.supabase_client = supabase_client or get_supabase_client()
        self.realtime_service = get_realtime_service()

        # Channel management
        self.active_channels: Dict[str, ChannelConfig] = {}
        self.supabase_channels: Dict[str, Any] = {}
        self.channel_metrics: Dict[str, ChannelMetrics] = {}

        # Event routing
        self.event_handlers: Dict[ChannelType, List[Callable]] = defaultdict(list)
        self.custom_handlers: Dict[str, Callable] = {}

        # Rate limiting and buffering
        self.event_buffers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}

        # Threading for background processing
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.processing_lock = threading.Lock()

        # Service statistics
        self.service_stats = {
            'service_started': time.time(),
            'total_channels': 0,
            'active_channels': 0,
            'total_events': 0,
            'events_per_second': 0.0,
            'errors': 0,
            'last_error': None
        }

        logger.info("ChannelManager initialized")

    async def create_channel(
        self,
        channel_type: ChannelType,
        table_name: str,
        config: Optional[ChannelConfig] = None
    ) -> str:
        """Create a new real-time channel"""

        channel_id = str(uuid.uuid4())

        if config is None:
            config = ChannelConfig(
                channel_id=channel_id,
                channel_type=channel_type,
                table_name=table_name
            )
        else:
            config.channel_id = channel_id

        try:
            # Create Supabase channel
            channel_name = f"{config.schema}:{table_name}"
            channel = self.supabase_client.client.channel(channel_name)

            # Create metrics
            self.channel_metrics[channel_id] = ChannelMetrics()

            # Set up event handler for this channel
            def channel_event_handler(payload):
                asyncio.create_task(
                    self._handle_channel_event(channel_id, payload)
                )

            # Subscribe to specified event types
            for event_type in config.event_types:
                subscription_config = {
                    'event': event_type.value,
                    'schema': config.schema,
                    'table': table_name,
                    'callback': channel_event_handler
                }

                # Add filters if specified
                if config.filters:
                    for key, value in config.filters.items():
                        subscription_config['filter'] = f"{key}=eq.{value}"

                channel.on('postgres_changes', **subscription_config)

            # Subscribe to the channel
            channel.subscribe()

            # Store channel configuration and instance
            self.active_channels[channel_id] = config
            self.supabase_channels[channel_id] = channel

            # Initialize rate limiter if needed
            if config.rate_limit:
                self.rate_limiters[channel_id] = {
                    'events': [],
                    'limit': config.rate_limit
                }

            # Update statistics
            self.service_stats['total_channels'] += 1
            self.service_stats['active_channels'] += 1

            logger.info(f"Created channel {channel_id} for {channel_type.value} on table {table_name}")
            return channel_id

        except Exception as e:
            logger.error(f"Failed to create channel: {e}")
            self.service_stats['errors'] += 1
            self.service_stats['last_error'] = str(e)
            raise

    async def remove_channel(self, channel_id: str):
        """Remove a real-time channel"""

        if channel_id not in self.active_channels:
            logger.warning(f"Channel {channel_id} not found")
            return

        try:
            # Unsubscribe from Supabase channel
            if channel_id in self.supabase_channels:
                channel = self.supabase_channels[channel_id]
                channel.unsubscribe()
                del self.supabase_channels[channel_id]

            # Clean up
            del self.active_channels[channel_id]
            if channel_id in self.channel_metrics:
                del self.channel_metrics[channel_id]
            if channel_id in self.event_buffers:
                del self.event_buffers[channel_id]
            if channel_id in self.rate_limiters:
                del self.rate_limiters[channel_id]

            # Update statistics
            self.service_stats['active_channels'] -= 1

            logger.info(f"Removed channel {channel_id}")

        except Exception as e:
            logger.error(f"Failed to remove channel {channel_id}: {e}")
            self.service_stats['errors'] += 1

    async def _handle_channel_event(self, channel_id: str, payload: Dict[str, Any]):
        """Handle events from a Supabase channel"""

        start_time = time.time()

        try:
            config = self.active_channels.get(channel_id)
            metrics = self.channel_metrics.get(channel_id)

            if not config or not metrics:
                logger.warning(f"Received event for unknown channel {channel_id}")
                return

            # Update metrics
            metrics.events_received += 1
            metrics.last_event_time = start_time

            # Check rate limiting
            if config.rate_limit and not self._check_rate_limit(channel_id):
                logger.warning(f"Rate limit exceeded for channel {channel_id}")
                return

            # Process the event
            await self._process_channel_event(channel_id, config, payload)

            # Update metrics
            processing_time = time.time() - start_time
            metrics.events_processed += 1

            # Update average processing time
            if metrics.average_processing_time == 0:
                metrics.average_processing_time = processing_time
            else:
                metrics.average_processing_time = (
                    metrics.average_processing_time * 0.9 + processing_time * 0.1
                )

            # Update service statistics
            self.service_stats['total_events'] += 1

        except Exception as e:
            logger.error(f"Failed to handle channel event for {channel_id}: {e}")
            if channel_id in self.channel_metrics:
                self.channel_metrics[channel_id].events_failed += 1
            self.service_stats['errors'] += 1

    async def _process_channel_event(
        self,
        channel_id: str,
        config: ChannelConfig,
        payload: Dict[str, Any]
    ):
        """Process a channel event based on its type"""

        # Route event based on channel type
        if config.channel_type == ChannelType.JOB_UPDATES:
            await self._handle_job_update(channel_id, payload)
        elif config.channel_type == ChannelType.USER_NOTIFICATIONS:
            await self._handle_user_notification(channel_id, payload)
        elif config.channel_type == ChannelType.MATCHING_RESULTS:
            await self._handle_matching_result(channel_id, payload)
        elif config.channel_type == ChannelType.SYSTEM_STATUS:
            await self._handle_system_status(channel_id, payload)
        elif config.channel_type == ChannelType.EMAIL_PROCESSING:
            await self._handle_email_processing(channel_id, payload)
        elif config.channel_type == ChannelType.SCORE_CALCULATION:
            await self._handle_score_calculation(channel_id, payload)
        elif config.channel_type == ChannelType.AUDIT_LOGS:
            await self._handle_audit_log(channel_id, payload)

        # Call registered handlers
        handlers = self.event_handlers.get(config.channel_type, [])
        for handler in handlers:
            try:
                await handler(channel_id, payload)
            except Exception as e:
                logger.error(f"Handler error for {config.channel_type}: {e}")

    async def _handle_job_update(self, channel_id: str, payload: Dict[str, Any]):
        """Handle job update events"""

        event_type = payload.get('eventType', 'unknown')
        new_record = payload.get('new', {})
        old_record = payload.get('old', {})

        job_id = new_record.get('id') or old_record.get('id')
        job_status = new_record.get('status')
        user_id = new_record.get('user_id')

        if not job_id:
            logger.warning("Job update event missing job ID")
            return

        # Create notification message
        notification = {
            'type': 'job_update',
            'job_id': job_id,
            'status': job_status,
            'event_type': event_type,
            'timestamp': time.time(),
            'data': new_record
        }

        # Send to user if available
        if user_id:
            await self.realtime_service.send_notification(
                user_id=user_id,
                notification_type='job_update',
                title=f'Job {job_status}',
                message=f'Job {job_id} status changed to {job_status}',
                data=notification
            )

        logger.debug(f"Processed job update for job {job_id}: {job_status}")

    async def _handle_user_notification(self, channel_id: str, payload: Dict[str, Any]):
        """Handle user notification events"""

        new_record = payload.get('new', {})
        user_id = new_record.get('user_id')
        notification_type = new_record.get('type', 'general')
        title = new_record.get('title', 'Notification')
        message = new_record.get('message', '')

        if user_id:
            await self.realtime_service.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=new_record
            )

        logger.debug(f"Processed user notification for user {user_id}")

    async def _handle_matching_result(self, channel_id: str, payload: Dict[str, Any]):
        """Handle matching result events"""

        new_record = payload.get('new', {})
        job_id = new_record.get('job_id')
        user_id = new_record.get('user_id')
        score = new_record.get('score')

        if user_id and job_id:
            await self.realtime_service.send_notification(
                user_id=user_id,
                notification_type='matching_result',
                title='Matching Complete',
                message=f'Job {job_id} matching completed with score {score}',
                data=new_record
            )

        logger.debug(f"Processed matching result for job {job_id}")

    async def _handle_system_status(self, channel_id: str, payload: Dict[str, Any]):
        """Handle system status events"""

        new_record = payload.get('new', {})
        status = new_record.get('status', 'unknown')
        message = new_record.get('message', '')

        await self.realtime_service.broadcast_system_status(
            status=status,
            message=message,
            data=new_record
        )

        logger.debug(f"Processed system status: {status}")

    async def _handle_email_processing(self, channel_id: str, payload: Dict[str, Any]):
        """Handle email processing events"""

        new_record = payload.get('new', {})
        email_id = new_record.get('id')
        status = new_record.get('status')
        user_id = new_record.get('user_id')

        if user_id:
            await self.realtime_service.send_notification(
                user_id=user_id,
                notification_type='email_processing',
                title='Email Processing Update',
                message=f'Email {email_id} is now {status}',
                data=new_record
            )

        logger.debug(f"Processed email processing event for email {email_id}")

    async def _handle_score_calculation(self, channel_id: str, payload: Dict[str, Any]):
        """Handle score calculation events"""

        new_record = payload.get('new', {})
        calculation_id = new_record.get('id')
        score = new_record.get('score')
        user_id = new_record.get('user_id')

        if user_id:
            await self.realtime_service.send_notification(
                user_id=user_id,
                notification_type='score_calculation',
                title='Score Calculated',
                message=f'New score calculated: {score}',
                data=new_record
            )

        logger.debug(f"Processed score calculation {calculation_id}: {score}")

    async def _handle_audit_log(self, channel_id: str, payload: Dict[str, Any]):
        """Handle audit log events"""

        new_record = payload.get('new', {})
        action = new_record.get('action')
        user_id = new_record.get('user_id')

        # Audit logs are typically for monitoring, not user notifications
        logger.info(f"Audit log: {action} by user {user_id}")

    def _check_rate_limit(self, channel_id: str) -> bool:
        """Check if channel is within rate limits"""

        if channel_id not in self.rate_limiters:
            return True

        limiter = self.rate_limiters[channel_id]
        current_time = time.time()

        # Remove events older than 1 second
        limiter['events'] = [
            event_time for event_time in limiter['events']
            if current_time - event_time < 1.0
        ]

        # Check if we're under the limit
        if len(limiter['events']) >= limiter['limit']:
            return False

        # Add current event
        limiter['events'].append(current_time)
        return True

    def register_event_handler(self, channel_type: ChannelType, handler: Callable):
        """Register a custom event handler for a channel type"""
        self.event_handlers[channel_type].append(handler)
        logger.info(f"Registered handler for {channel_type.value}")

    def unregister_event_handler(self, channel_type: ChannelType, handler: Callable):
        """Unregister an event handler"""
        if handler in self.event_handlers[channel_type]:
            self.event_handlers[channel_type].remove(handler)
            logger.info(f"Unregistered handler for {channel_type.value}")

    async def setup_default_channels(self) -> Dict[str, str]:
        """Set up default real-time channels"""

        default_channels = {}

        try:
            # Job updates channel
            job_channel_id = await self.create_channel(
                ChannelType.JOB_UPDATES,
                'jobs'
            )
            default_channels['jobs'] = job_channel_id

            # User notifications channel
            notifications_channel_id = await self.create_channel(
                ChannelType.USER_NOTIFICATIONS,
                'notifications'
            )
            default_channels['notifications'] = notifications_channel_id

            # Matching results channel
            matching_channel_id = await self.create_channel(
                ChannelType.MATCHING_RESULTS,
                'matching_results'
            )
            default_channels['matching'] = matching_channel_id

            # System status channel
            system_channel_id = await self.create_channel(
                ChannelType.SYSTEM_STATUS,
                'system_status'
            )
            default_channels['system'] = system_channel_id

            # Email processing channel
            email_channel_id = await self.create_channel(
                ChannelType.EMAIL_PROCESSING,
                'emails'
            )
            default_channels['emails'] = email_channel_id

            # Score calculation channel
            score_channel_id = await self.create_channel(
                ChannelType.SCORE_CALCULATION,
                'score_calculations'
            )
            default_channels['scores'] = score_channel_id

            # Audit logs channel
            audit_channel_id = await self.create_channel(
                ChannelType.AUDIT_LOGS,
                'audit_logs'
            )
            default_channels['audit'] = audit_channel_id

            logger.info(f"Set up {len(default_channels)} default channels")
            return default_channels

        except Exception as e:
            logger.error(f"Failed to set up default channels: {e}")
            raise

    def get_channel_metrics(self, channel_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for channels"""

        if channel_id:
            if channel_id in self.channel_metrics:
                config = self.active_channels.get(channel_id)
                metrics = self.channel_metrics[channel_id]

                return {
                    'channel_id': channel_id,
                    'channel_type': config.channel_type.value if config else 'unknown',
                    'table_name': config.table_name if config else 'unknown',
                    'metrics': asdict(metrics)
                }
            else:
                return {'error': f'Channel {channel_id} not found'}

        # Return all metrics
        all_metrics = {}
        for cid, metrics in self.channel_metrics.items():
            config = self.active_channels.get(cid)
            all_metrics[cid] = {
                'channel_type': config.channel_type.value if config else 'unknown',
                'table_name': config.table_name if config else 'unknown',
                'metrics': asdict(metrics)
            }

        return all_metrics

    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""

        uptime = time.time() - self.service_stats['service_started']

        # Calculate events per second
        if uptime > 0:
            self.service_stats['events_per_second'] = self.service_stats['total_events'] / uptime

        return {
            'service': self.service_stats,
            'uptime_seconds': uptime,
            'channels': {
                'active': len(self.active_channels),
                'by_type': self._get_channels_by_type()
            },
            'metrics_summary': self._get_metrics_summary()
        }

    def _get_channels_by_type(self) -> Dict[str, int]:
        """Get channel count by type"""
        counts = {}
        for config in self.active_channels.values():
            channel_type = config.channel_type.value
            counts[channel_type] = counts.get(channel_type, 0) + 1
        return counts

    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        total_events_received = sum(m.events_received for m in self.channel_metrics.values())
        total_events_processed = sum(m.events_processed for m in self.channel_metrics.values())
        total_events_failed = sum(m.events_failed for m in self.channel_metrics.values())

        avg_processing_time = 0.0
        if self.channel_metrics:
            avg_processing_time = sum(
                m.average_processing_time for m in self.channel_metrics.values()
            ) / len(self.channel_metrics)

        return {
            'total_events_received': total_events_received,
            'total_events_processed': total_events_processed,
            'total_events_failed': total_events_failed,
            'success_rate': (
                total_events_processed / total_events_received * 100
                if total_events_received > 0 else 0
            ),
            'average_processing_time': avg_processing_time
        }

    async def shutdown(self):
        """Gracefully shutdown the channel manager"""
        logger.info("Shutting down ChannelManager...")

        # Remove all channels
        for channel_id in list(self.active_channels.keys()):
            await self.remove_channel(channel_id)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("ChannelManager shutdown complete")


# Global channel manager instance
_channel_manager: Optional[ChannelManager] = None


def get_channel_manager() -> ChannelManager:
    """Get or create the global channel manager instance"""
    global _channel_manager
    if _channel_manager is None:
        _channel_manager = ChannelManager()
    return _channel_manager


# Convenience functions for common operations
async def setup_realtime_channels() -> Dict[str, str]:
    """Set up all default real-time channels"""
    manager = get_channel_manager()
    return await manager.setup_default_channels()


async def subscribe_to_job_updates(user_id: str, job_id: Optional[str] = None) -> str:
    """Subscribe to job updates for a user"""
    manager = get_channel_manager()
    filters = {'user_id': user_id}
    if job_id:
        filters['id'] = job_id

    config = ChannelConfig(
        channel_id="",  # Will be set by create_channel
        channel_type=ChannelType.JOB_UPDATES,
        table_name="jobs",
        filters=filters
    )

    return await manager.create_channel(ChannelType.JOB_UPDATES, "jobs", config)


async def subscribe_to_user_notifications(user_id: str) -> str:
    """Subscribe to notifications for a user"""
    manager = get_channel_manager()
    config = ChannelConfig(
        channel_id="",
        channel_type=ChannelType.USER_NOTIFICATIONS,
        table_name="notifications",
        filters={'user_id': user_id}
    )

    return await manager.create_channel(ChannelType.USER_NOTIFICATIONS, "notifications", config)


async def subscribe_to_system_status() -> str:
    """Subscribe to system status updates"""
    manager = get_channel_manager()
    return await manager.create_channel(ChannelType.SYSTEM_STATUS, "system_status")


# Export all public functions and classes
__all__ = [
    'ChannelManager',
    'ChannelType',
    'EventType',
    'ChannelConfig',
    'ChannelMetrics',
    'get_channel_manager',
    'setup_realtime_channels',
    'subscribe_to_job_updates',
    'subscribe_to_user_notifications',
    'subscribe_to_system_status'
]