"""
T069: Real-time Query Execution Service

Production-ready real-time service with WebSocket connections,
subscription management, and live data streaming capabilities.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from enum import Enum
import weakref
from concurrent.futures import ThreadPoolExecutor

from fastapi import WebSocket, WebSocketDisconnect
from supabase import Client
from app.core.supabase import get_supabase_client

# Configure logger
logger = logging.getLogger(__name__)


class SubscriptionType(Enum):
    """Subscription types for real-time updates"""
    JOB_UPDATES = "job_updates"
    USER_NOTIFICATIONS = "user_notifications"
    MATCHING_RESULTS = "matching_results"
    SYSTEM_STATUS = "system_status"
    CUSTOM = "custom"


class ConnectionStatus(Enum):
    """WebSocket connection status"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class SubscriptionConfig:
    """Configuration for real-time subscriptions"""
    subscription_id: str
    subscription_type: SubscriptionType
    table_name: str
    schema: str = "public"
    filter_conditions: Optional[Dict[str, Any]] = None
    callback: Optional[Callable] = None
    user_id: Optional[str] = None
    channel_name: Optional[str] = None
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

        if self.channel_name is None:
            self.channel_name = f"{self.schema}:{self.table_name}"


@dataclass
class RealtimeMessage:
    """Structure for real-time messages"""
    message_id: str
    subscription_id: str
    event_type: str
    table: str
    schema: str
    old_record: Optional[Dict[str, Any]] = None
    record: Optional[Dict[str, Any]] = None
    timestamp: float = None
    user_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class ConnectionManager:
    """Manages WebSocket connections with subscription tracking"""

    def __init__(self):
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}

        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        # User to connections mapping
        self.user_connections: Dict[str, Set[str]] = {}

        # Subscription to connections mapping
        self.subscription_connections: Dict[str, Set[str]] = {}

        # Connection statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'subscriptions_created': 0,
            'last_activity': time.time()
        }

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None) -> str:
        """Connect a new WebSocket client"""
        await websocket.accept()

        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            'user_id': user_id,
            'connected_at': time.time(),
            'status': ConnectionStatus.CONNECTED,
            'subscriptions': set(),
            'last_ping': time.time()
        }

        # Track user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

        # Update statistics
        self.stats['total_connections'] += 1
        self.stats['active_connections'] += 1
        self.stats['last_activity'] = time.time()

        logger.info(f"WebSocket connected: {connection_id}, user: {user_id}")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if connection_id in self.active_connections:
            # Get connection metadata
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get('user_id')

            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from subscription connections
            subscriptions = metadata.get('subscriptions', set()).copy()
            for sub_id in subscriptions:
                if sub_id in self.subscription_connections:
                    self.subscription_connections[sub_id].discard(connection_id)
                    if not self.subscription_connections[sub_id]:
                        del self.subscription_connections[sub_id]

            # Clean up connection
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]

            # Update statistics
            self.stats['active_connections'] -= 1
            self.stats['last_activity'] = time.time()

            logger.info(f"WebSocket disconnected: {connection_id}, user: {user_id}")

    async def send_personal_message(self, message: Union[str, Dict], connection_id: str) -> bool:
        """Send a message to a specific connection"""
        if connection_id not in self.active_connections:
            logger.warning(f"Connection {connection_id} not found")
            return False

        try:
            websocket = self.active_connections[connection_id]

            if isinstance(message, dict):
                message = json.dumps(message)

            await websocket.send_text(message)

            self.stats['messages_sent'] += 1
            self.stats['last_activity'] = time.time()
            return True

        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.stats['messages_failed'] += 1
            await self.disconnect(connection_id)
            return False

    async def broadcast_to_subscription(self, subscription_id: str, message: Union[str, Dict]) -> int:
        """Broadcast a message to all connections subscribed to a subscription"""
        if subscription_id not in self.subscription_connections:
            logger.debug(f"No connections for subscription {subscription_id}")
            return 0

        connections = self.subscription_connections[subscription_id].copy()
        successful_sends = 0

        for connection_id in connections:
            if await self.send_personal_message(message, connection_id):
                successful_sends += 1

        return successful_sends

    async def broadcast_to_user(self, user_id: str, message: Union[str, Dict]) -> int:
        """Broadcast a message to all connections for a user"""
        if user_id not in self.user_connections:
            logger.debug(f"No connections for user {user_id}")
            return 0

        connections = self.user_connections[user_id].copy()
        successful_sends = 0

        for connection_id in connections:
            if await self.send_personal_message(message, connection_id):
                successful_sends += 1

        return successful_sends

    def add_subscription_to_connection(self, connection_id: str, subscription_id: str):
        """Add a subscription to a connection"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]['subscriptions'].add(subscription_id)

        if subscription_id not in self.subscription_connections:
            self.subscription_connections[subscription_id] = set()
        self.subscription_connections[subscription_id].add(connection_id)

    def remove_subscription_from_connection(self, connection_id: str, subscription_id: str):
        """Remove a subscription from a connection"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]['subscriptions'].discard(subscription_id)

        if subscription_id in self.subscription_connections:
            self.subscription_connections[subscription_id].discard(connection_id)
            if not self.subscription_connections[subscription_id]:
                del self.subscription_connections[subscription_id]

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            **self.stats,
            'connections_by_user': {
                user_id: len(connections)
                for user_id, connections in self.user_connections.items()
            },
            'subscriptions_count': len(self.subscription_connections)
        }


class RealtimeService:
    """Main real-time service with comprehensive subscription management"""

    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase_client = supabase_client or get_supabase_client().client
        self.connection_manager = ConnectionManager()

        # Subscription management
        self.active_subscriptions: Dict[str, SubscriptionConfig] = {}
        self.supabase_channels: Dict[str, Any] = {}

        # Thread pool for background tasks
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Service statistics
        self.service_stats = {
            'service_started': time.time(),
            'total_subscriptions': 0,
            'active_subscriptions': 0,
            'messages_processed': 0,
            'errors': 0
        }

        logger.info("RealtimeService initialized")

    async def create_subscription(
        self,
        subscription_type: SubscriptionType,
        table_name: str,
        connection_id: str,
        user_id: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        schema: str = "public"
    ) -> str:
        """Create a new real-time subscription"""

        subscription_id = str(uuid.uuid4())

        subscription_config = SubscriptionConfig(
            subscription_id=subscription_id,
            subscription_type=subscription_type,
            table_name=table_name,
            schema=schema,
            filter_conditions=filter_conditions,
            user_id=user_id
        )

        try:
            # Create Supabase channel
            channel = self.supabase_client.channel(subscription_config.channel_name)

            # Set up the callback for this subscription
            def subscription_callback(payload):
                asyncio.create_task(
                    self._handle_supabase_event(subscription_id, payload)
                )

            # Subscribe to postgres changes
            channel.on(
                'postgres_changes',
                event='*',
                schema=schema,
                table=table_name,
                callback=subscription_callback
            )

            # Apply filters if specified
            if filter_conditions:
                for key, value in filter_conditions.items():
                    channel.on(
                        'postgres_changes',
                        event='*',
                        schema=schema,
                        table=table_name,
                        filter=f"{key}=eq.{value}",
                        callback=subscription_callback
                    )

            # Subscribe to the channel
            channel.subscribe()

            # Store subscription and channel
            self.active_subscriptions[subscription_id] = subscription_config
            self.supabase_channels[subscription_id] = channel

            # Add subscription to connection
            self.connection_manager.add_subscription_to_connection(connection_id, subscription_id)

            # Update statistics
            self.service_stats['total_subscriptions'] += 1
            self.service_stats['active_subscriptions'] += 1
            self.connection_manager.stats['subscriptions_created'] += 1

            logger.info(f"Created subscription {subscription_id} for table {table_name}")
            return subscription_id

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            self.service_stats['errors'] += 1
            raise

    async def remove_subscription(self, subscription_id: str, connection_id: Optional[str] = None):
        """Remove a real-time subscription"""

        if subscription_id not in self.active_subscriptions:
            logger.warning(f"Subscription {subscription_id} not found")
            return

        try:
            # Unsubscribe from Supabase channel
            if subscription_id in self.supabase_channels:
                channel = self.supabase_channels[subscription_id]
                channel.unsubscribe()
                del self.supabase_channels[subscription_id]

            # Remove from active subscriptions
            del self.active_subscriptions[subscription_id]

            # Remove from connection if specified
            if connection_id:
                self.connection_manager.remove_subscription_from_connection(
                    connection_id, subscription_id
                )

            # Update statistics
            self.service_stats['active_subscriptions'] -= 1

            logger.info(f"Removed subscription {subscription_id}")

        except Exception as e:
            logger.error(f"Failed to remove subscription {subscription_id}: {e}")
            self.service_stats['errors'] += 1

    async def _handle_supabase_event(self, subscription_id: str, payload: Dict[str, Any]):
        """Handle events from Supabase real-time"""

        try:
            subscription_config = self.active_subscriptions.get(subscription_id)
            if not subscription_config:
                logger.warning(f"Received event for unknown subscription {subscription_id}")
                return

            # Create real-time message
            message = RealtimeMessage(
                message_id=str(uuid.uuid4()),
                subscription_id=subscription_id,
                event_type=payload.get('eventType', 'unknown'),
                table=payload.get('table', subscription_config.table_name),
                schema=payload.get('schema', subscription_config.schema),
                old_record=payload.get('old'),
                record=payload.get('new'),
                user_id=subscription_config.user_id
            )

            # Broadcast to subscribed connections
            message_dict = message.to_dict()
            connections_notified = await self.connection_manager.broadcast_to_subscription(
                subscription_id, message_dict
            )

            # Update statistics
            self.service_stats['messages_processed'] += 1

            logger.debug(
                f"Processed event for subscription {subscription_id}, "
                f"notified {connections_notified} connections"
            )

        except Exception as e:
            logger.error(f"Failed to handle Supabase event: {e}")
            self.service_stats['errors'] += 1

    async def execute_realtime_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        subscription_type: SubscriptionType = SubscriptionType.CUSTOM
    ) -> Dict[str, Any]:
        """Execute a query and set up real-time subscription for changes"""

        try:
            # Execute the initial query
            if params:
                response = self.supabase_client.rpc('execute_sql', {
                    'query': query,
                    'params': params
                }).execute()
            else:
                response = self.supabase_client.rpc('execute_sql', {
                    'query': query
                }).execute()

            result = {
                'query_id': str(uuid.uuid4()),
                'data': response.data,
                'subscription_type': subscription_type.value,
                'executed_at': time.time()
            }

            logger.info(f"Executed real-time query, returned {len(response.data or [])} rows")
            return result

        except Exception as e:
            logger.error(f"Failed to execute real-time query: {e}")
            self.service_stats['errors'] += 1
            raise

    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a notification to a specific user"""

        notification = {
            'notification_id': str(uuid.uuid4()),
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': time.time(),
            'user_id': user_id
        }

        connections_notified = await self.connection_manager.broadcast_to_user(
            user_id, notification
        )

        logger.info(f"Sent notification to user {user_id}, reached {connections_notified} connections")
        return connections_notified > 0

    async def broadcast_system_status(self, status: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Broadcast system status to all connected clients"""

        status_message = {
            'message_id': str(uuid.uuid4()),
            'type': 'system_status',
            'status': status,
            'message': message,
            'data': data or {},
            'timestamp': time.time()
        }

        total_sent = 0
        for subscription_id in self.active_subscriptions:
            subscription = self.active_subscriptions[subscription_id]
            if subscription.subscription_type == SubscriptionType.SYSTEM_STATUS:
                sent = await self.connection_manager.broadcast_to_subscription(
                    subscription_id, status_message
                )
                total_sent += sent

        logger.info(f"Broadcasted system status to {total_sent} connections")

    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        uptime = time.time() - self.service_stats['service_started']

        return {
            'service': {
                **self.service_stats,
                'uptime_seconds': uptime,
                'subscriptions': {
                    'active': len(self.active_subscriptions),
                    'by_type': self._get_subscriptions_by_type()
                }
            },
            'connections': self.connection_manager.get_connection_stats()
        }

    def _get_subscriptions_by_type(self) -> Dict[str, int]:
        """Get subscription count by type"""
        counts = {}
        for subscription in self.active_subscriptions.values():
            sub_type = subscription.subscription_type.value
            counts[sub_type] = counts.get(sub_type, 0) + 1
        return counts

    async def cleanup_inactive_connections(self):
        """Clean up inactive connections (heartbeat mechanism)"""
        current_time = time.time()
        timeout_threshold = 300  # 5 minutes

        inactive_connections = []
        for connection_id, metadata in self.connection_manager.connection_metadata.items():
            if current_time - metadata.get('last_ping', 0) > timeout_threshold:
                inactive_connections.append(connection_id)

        for connection_id in inactive_connections:
            logger.info(f"Cleaning up inactive connection: {connection_id}")
            await self.connection_manager.disconnect(connection_id)

    async def shutdown(self):
        """Gracefully shutdown the real-time service"""
        logger.info("Shutting down RealtimeService...")

        # Unsubscribe from all Supabase channels
        for subscription_id, channel in self.supabase_channels.items():
            try:
                channel.unsubscribe()
            except Exception as e:
                logger.error(f"Error unsubscribing from channel {subscription_id}: {e}")

        # Close all WebSocket connections
        for connection_id in list(self.connection_manager.active_connections.keys()):
            await self.connection_manager.disconnect(connection_id)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("RealtimeService shutdown complete")


# Global service instance
_realtime_service: Optional[RealtimeService] = None


def get_realtime_service() -> RealtimeService:
    """Get or create the global real-time service instance"""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealtimeService()
    return _realtime_service


@asynccontextmanager
async def realtime_subscription(
    subscription_type: SubscriptionType,
    table_name: str,
    connection_id: str,
    user_id: Optional[str] = None,
    filter_conditions: Optional[Dict[str, Any]] = None
):
    """Context manager for real-time subscriptions"""
    service = get_realtime_service()

    subscription_id = await service.create_subscription(
        subscription_type=subscription_type,
        table_name=table_name,
        connection_id=connection_id,
        user_id=user_id,
        filter_conditions=filter_conditions
    )

    try:
        yield subscription_id
    finally:
        await service.remove_subscription(subscription_id, connection_id)


# Export all public functions and classes
__all__ = [
    'RealtimeService',
    'ConnectionManager',
    'SubscriptionType',
    'ConnectionStatus',
    'SubscriptionConfig',
    'RealtimeMessage',
    'get_realtime_service',
    'realtime_subscription'
]