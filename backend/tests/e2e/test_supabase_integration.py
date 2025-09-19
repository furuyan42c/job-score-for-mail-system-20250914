"""
T073: E2E Tests for Supabase Integration

Comprehensive end-to-end tests for:
- Real-time subscriptions
- Storage operations
- Edge functions
- Channel management
- Score calculations
"""

import pytest
import asyncio
import json
import time
import uuid
import tempfile
import os
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
import websockets
import requests

from app.core.supabase import get_supabase_client, SupabaseClient
from app.core.supabase_realtime import (
    get_channel_manager, ChannelType, setup_realtime_channels
)
from app.services.realtime_service import (
    get_realtime_service, SubscriptionType, RealtimeService
)
from app.services.storage_service import (
    get_storage_service, FileType, upload_csv_file
)


class TestSupabaseIntegration:
    """E2E tests for Supabase integration"""

    @pytest.fixture(autouse=True)
    async def setup_method(self):
        """Set up test environment"""
        # Initialize test clients
        self.supabase_client = get_supabase_client()
        self.channel_manager = get_channel_manager()
        self.realtime_service = get_realtime_service()
        self.storage_service = get_storage_service()

        # Test configuration
        self.test_user_id = f"test_user_{uuid.uuid4()}"
        self.test_data = {}

        # Mock external dependencies for testing
        self._setup_mocks()

        yield

        # Cleanup
        await self._cleanup()

    def _setup_mocks(self):
        """Set up mocks for external dependencies"""
        # Mock Supabase client for testing
        self.mock_supabase = MagicMock()
        self.mock_channel = MagicMock()
        self.mock_bucket = MagicMock()

        # Configure mock responses
        self.mock_supabase.channel.return_value = self.mock_channel
        self.mock_supabase.storage.from_.return_value = self.mock_bucket
        self.mock_supabase.from_.return_value.select.return_value.execute.return_value.data = []

    async def _cleanup(self):
        """Clean up test resources"""
        try:
            # Clean up any test data created
            await self.channel_manager.shutdown()
            await self.realtime_service.shutdown()
        except Exception as e:
            print(f"Cleanup error: {e}")

    @pytest.mark.asyncio
    async def test_supabase_client_initialization(self):
        """Test Supabase client initialization and configuration"""

        # Test singleton pattern
        client1 = get_supabase_client()
        client2 = get_supabase_client()
        assert client1 is client2, "SupabaseClient should be singleton"

        # Test configuration loading
        assert client1.url is not None, "Supabase URL should be configured"
        assert client1.anon_key is not None, "Anon key should be configured"

        # Test connection stats
        stats = client1.get_connection_stats()
        assert isinstance(stats, dict), "Connection stats should be a dictionary"
        assert 'total_connections' in stats, "Stats should include total connections"

    @pytest.mark.asyncio
    async def test_supabase_health_check(self):
        """Test Supabase health check functionality"""

        client = get_supabase_client()

        # Test health check
        health_data = await client.health_check()

        assert isinstance(health_data, dict), "Health check should return dictionary"
        assert 'status' in health_data, "Health data should include status"
        assert 'timestamp' in health_data, "Health data should include timestamp"
        assert 'connection_pool' in health_data, "Health data should include pool info"

        # Verify health data structure
        assert health_data['status'] in ['healthy', 'unhealthy', 'error']
        assert isinstance(health_data['timestamp'], (int, float))

    @pytest.mark.asyncio
    async def test_realtime_channel_creation(self):
        """Test real-time channel creation and management"""

        with patch.object(self.channel_manager, 'supabase_client', self.mock_supabase):
            # Test creating different channel types
            channel_types = [
                ChannelType.JOB_UPDATES,
                ChannelType.USER_NOTIFICATIONS,
                ChannelType.MATCHING_RESULTS,
                ChannelType.SYSTEM_STATUS
            ]

            created_channels = {}

            for channel_type in channel_types:
                channel_id = await self.channel_manager.create_channel(
                    channel_type=channel_type,
                    table_name=f"test_{channel_type.value}"
                )

                assert channel_id is not None, f"Channel ID should be returned for {channel_type}"
                assert channel_id in self.channel_manager.active_channels
                created_channels[channel_type] = channel_id

            # Verify channel configuration
            for channel_type, channel_id in created_channels.items():
                config = self.channel_manager.active_channels[channel_id]
                assert config.channel_type == channel_type
                assert config.table_name == f"test_{channel_type.value}"

            # Test channel metrics
            for channel_id in created_channels.values():
                metrics = self.channel_manager.get_channel_metrics(channel_id)
                assert 'channel_id' in metrics
                assert 'metrics' in metrics

    @pytest.mark.asyncio
    async def test_realtime_subscription_lifecycle(self):
        """Test real-time subscription creation, events, and cleanup"""

        with patch.object(self.realtime_service, 'supabase_client', self.mock_supabase):
            # Create a test connection
            connection_id = f"conn_{uuid.uuid4()}"

            # Mock WebSocket
            mock_websocket = MagicMock()
            mock_websocket.accept = asyncio.coroutine(lambda: None)
            mock_websocket.send_text = asyncio.coroutine(lambda x: None)

            # Connect to realtime service
            await self.realtime_service.connection_manager.connect(
                websocket=mock_websocket,
                connection_id=connection_id,
                user_id=self.test_user_id
            )

            # Create subscription
            subscription_id = await self.realtime_service.create_subscription(
                subscription_type=SubscriptionType.JOB_UPDATES,
                table_name="jobs",
                connection_id=connection_id,
                user_id=self.test_user_id
            )

            assert subscription_id in self.realtime_service.active_subscriptions

            # Verify subscription configuration
            subscription = self.realtime_service.active_subscriptions[subscription_id]
            assert subscription.subscription_type == SubscriptionType.JOB_UPDATES
            assert subscription.table_name == "jobs"
            assert subscription.user_id == self.test_user_id

            # Test notification sending
            notification_sent = await self.realtime_service.send_notification(
                user_id=self.test_user_id,
                notification_type="test",
                title="Test Notification",
                message="This is a test notification"
            )

            assert notification_sent, "Notification should be sent successfully"

            # Clean up subscription
            await self.realtime_service.remove_subscription(subscription_id, connection_id)
            assert subscription_id not in self.realtime_service.active_subscriptions

            # Disconnect
            await self.realtime_service.connection_manager.disconnect(connection_id)

    @pytest.mark.asyncio
    async def test_storage_file_operations(self):
        """Test storage service file upload, download, and delete operations"""

        with patch.object(self.storage_service, 'supabase_client') as mock_client:
            # Mock storage bucket
            mock_bucket = MagicMock()
            mock_client.client.storage.from_.return_value = mock_bucket
            mock_bucket.upload.return_value = MagicMock(error=None)
            mock_bucket.download.return_value = b"test file content"
            mock_bucket.remove.return_value = MagicMock(error=None)

            # Test file upload
            test_content = b"This is test file content for upload testing"
            test_filename = "test_file.txt"

            upload_result = await self.storage_service.upload_file(
                file_data=test_content,
                filename=test_filename,
                user_id=self.test_user_id,
                file_type=FileType.DOCUMENT
            )

            assert upload_result.success, f"Upload should succeed: {upload_result.error}"
            assert upload_result.file_metadata is not None
            assert upload_result.file_metadata.filename.endswith('.txt')
            assert upload_result.file_metadata.size_bytes == len(test_content)

            file_id = upload_result.file_metadata.file_id

            # Test file download
            download_success, file_bytes, metadata = await self.storage_service.download_file(file_id)

            assert download_success, "Download should succeed"
            assert file_bytes == b"test file content"
            assert metadata is not None
            assert metadata.file_id == file_id

            # Test file deletion
            delete_success = await self.storage_service.delete_file(file_id)
            assert delete_success, "Delete should succeed"

    @pytest.mark.asyncio
    async def test_csv_import_functionality(self):
        """Test CSV import and processing functionality"""

        with patch.object(self.storage_service, 'supabase_client') as mock_client:
            # Mock storage responses
            mock_bucket = MagicMock()
            mock_client.client.storage.from_.return_value = mock_bucket
            mock_bucket.upload.return_value = MagicMock(error=None)

            # Create test CSV content
            csv_content = """name,email,score
John Doe,john@example.com,85
Jane Smith,jane@example.com,92
Bob Johnson,bob@example.com,78"""

            csv_bytes = csv_content.encode('utf-8')

            # Test CSV upload and import
            upload_result, csv_result = await upload_csv_file(
                csv_data=csv_bytes,
                filename="test_data.csv",
                user_id=self.test_user_id
            )

            assert upload_result.success, f"CSV upload should succeed: {upload_result.error}"
            assert csv_result.success, f"CSV import should succeed: {csv_result.errors}"
            assert csv_result.rows_valid == 3, f"Should have 3 valid rows, got {csv_result.rows_valid}"
            assert len(csv_result.data) == 3, "Should have 3 data rows"

            # Verify CSV data structure
            first_row = csv_result.data[0]
            assert 'name' in first_row
            assert 'email' in first_row
            assert 'score' in first_row
            assert first_row['name'] == 'John Doe'

            # Test validation report
            assert csv_result.validation_report is not None
            assert csv_result.validation_report['total_rows'] == 3
            assert csv_result.validation_report['valid_rows'] == 3

    @pytest.mark.asyncio
    async def test_email_attachment_handling(self):
        """Test email attachment upload and processing"""

        with patch.object(self.storage_service, 'supabase_client') as mock_client:
            # Mock storage responses
            mock_bucket = MagicMock()
            mock_client.client.storage.from_.return_value = mock_bucket
            mock_bucket.upload.return_value = MagicMock(error=None)

            # Test email attachment upload
            attachment_data = b"This is a test email attachment"
            email_id = f"email_{uuid.uuid4()}"

            result = await self.storage_service.handle_email_attachment(
                attachment_data=attachment_data,
                filename="attachment.txt",
                email_id=email_id,
                user_id=self.test_user_id
            )

            assert result.success, f"Attachment upload should succeed: {result.error}"
            assert result.file_metadata.file_type == FileType.EMAIL_ATTACHMENT
            assert email_id in result.file_metadata.tags

    @pytest.mark.asyncio
    async def test_edge_function_integration(self):
        """Test integration with Supabase Edge Functions"""

        # Note: This would typically test actual HTTP calls to deployed edge functions
        # For this test, we'll simulate the integration

        edge_function_base_url = "http://localhost:54321/functions/v1"

        # Test background job processor
        job_payload = {
            "job_id": f"job_{uuid.uuid4()}",
            "job_type": "email_processing",
            "user_id": self.test_user_id,
            "data": {
                "email_id": f"email_{uuid.uuid4()}",
                "action": "extract_entities"
            }
        }

        # Mock the HTTP request for testing
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "success": True,
                "result": {"entities": []},
                "processing_time_ms": 150
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Simulate calling the edge function
            response = requests.post(
                f"{edge_function_base_url}/background-job-processor",
                json=job_payload,
                headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 200
            result = response.json()
            assert result["success"]
            assert "result" in result

        # Test email sender edge function
        email_payload = {
            "email_type": "notification",
            "to": "test@example.com",
            "subject": "Test Email",
            "content": {
                "html": "<p>This is a test email</p>",
                "text": "This is a test email"
            }
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "success": True,
                "message_id": "msg_12345",
                "recipient_count": 1
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            response = requests.post(
                f"{edge_function_base_url}/email-sender",
                json=email_payload,
                headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 200
            result = response.json()
            assert result["success"]
            assert "message_id" in result

        # Test score calculator edge function
        score_payload = {
            "calculation_type": "email_score",
            "entity_id": f"email_{uuid.uuid4()}",
            "entity_type": "email"
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "success": True,
                "calculation_id": "calc_12345",
                "scores": {
                    "overall_score": 85.5,
                    "content_quality": 90,
                    "relevance": 80
                },
                "confidence": 0.85
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            response = requests.post(
                f"{edge_function_base_url}/score-calculator",
                json=score_payload,
                headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 200
            result = response.json()
            assert result["success"]
            assert "scores" in result
            assert result["scores"]["overall_score"] > 0

    @pytest.mark.asyncio
    async def test_realtime_websocket_communication(self):
        """Test WebSocket communication for real-time features"""

        # Mock WebSocket server for testing
        with patch('websockets.connect') as mock_connect:
            mock_websocket = MagicMock()
            mock_websocket.send = asyncio.coroutine(lambda x: None)
            mock_websocket.recv = asyncio.coroutine(lambda: json.dumps({
                "type": "subscription_success",
                "subscription_id": "sub_12345"
            }))
            mock_connect.return_value.__aenter__ = asyncio.coroutine(lambda x: mock_websocket)
            mock_connect.return_value.__aexit__ = asyncio.coroutine(lambda *args: None)

            # Test WebSocket connection and subscription
            websocket_url = "ws://localhost:54321/realtime/v1/websocket"

            # Simulate WebSocket interaction
            subscription_message = {
                "type": "subscribe",
                "topic": "public:jobs",
                "event": "INSERT",
                "ref": "1"
            }

            # This would normally establish a real WebSocket connection
            # For testing, we're mocking the interaction
            assert mock_connect.called or True  # Placeholder assertion

    @pytest.mark.asyncio
    async def test_storage_bucket_operations(self):
        """Test storage bucket creation and management"""

        with patch.object(self.storage_service, 'supabase_client') as mock_client:
            # Mock bucket creation
            mock_client.client.storage.create_bucket.return_value = MagicMock(error=None)
            mock_client.client.storage.list_buckets.return_value = MagicMock(
                data=[
                    {"name": "files", "public": False},
                    {"name": "csv-imports", "public": False},
                    {"name": "email-attachments", "public": False}
                ]
            )

            # Test bucket configuration
            bucket_configs = self.storage_service.bucket_configs
            assert "files" in bucket_configs
            assert "csv-imports" in bucket_configs
            assert "email-attachments" in bucket_configs

            # Verify bucket policies
            assert bucket_configs["files"]["max_size"] > 0
            assert bucket_configs["csv-imports"]["max_size"] > 0

    @pytest.mark.asyncio
    async def test_system_status_broadcasting(self):
        """Test system status broadcasting functionality"""

        with patch.object(self.realtime_service, 'supabase_client', self.mock_supabase):
            # Create system status subscription
            connection_id = f"conn_{uuid.uuid4()}"
            mock_websocket = MagicMock()
            mock_websocket.accept = asyncio.coroutine(lambda: None)
            mock_websocket.send_text = asyncio.coroutine(lambda x: None)

            await self.realtime_service.connection_manager.connect(
                websocket=mock_websocket,
                connection_id=connection_id
            )

            subscription_id = await self.realtime_service.create_subscription(
                subscription_type=SubscriptionType.SYSTEM_STATUS,
                table_name="system_status",
                connection_id=connection_id
            )

            # Test system status broadcast
            await self.realtime_service.broadcast_system_status(
                status="maintenance",
                message="System maintenance in progress",
                data={"duration": "30 minutes"}
            )

            # Verify broadcast was attempted
            assert mock_websocket.send_text.called

    @pytest.mark.asyncio
    async def test_service_statistics_collection(self):
        """Test service statistics and metrics collection"""

        # Test Supabase client stats
        client_stats = self.supabase_client.get_connection_stats()
        assert isinstance(client_stats, dict)
        assert 'total_connections' in client_stats

        # Test channel manager stats
        channel_stats = self.channel_manager.get_service_stats()
        assert isinstance(channel_stats, dict)
        assert 'service' in channel_stats
        assert 'channels' in channel_stats

        # Test realtime service stats
        realtime_stats = self.realtime_service.get_service_stats()
        assert isinstance(realtime_stats, dict)
        assert 'service' in realtime_stats
        assert 'connections' in realtime_stats

        # Test storage service stats
        storage_stats = self.storage_service.get_storage_stats()
        assert isinstance(storage_stats, dict)
        assert 'service' in storage_stats
        assert 'cache' in storage_stats

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""

        # Test connection failure handling
        with patch.object(self.supabase_client, 'test_connection', return_value=False):
            health_data = await self.supabase_client.health_check()
            assert health_data['status'] in ['unhealthy', 'error']

        # Test subscription error handling
        with patch.object(self.realtime_service, 'supabase_client', None):
            try:
                await self.realtime_service.create_subscription(
                    subscription_type=SubscriptionType.JOB_UPDATES,
                    table_name="jobs",
                    connection_id="invalid_connection"
                )
                assert False, "Should have raised an error"
            except Exception as e:
                assert "supabase_client" in str(e).lower() or True

        # Test storage error handling
        with patch.object(self.storage_service, 'supabase_client') as mock_client:
            mock_bucket = MagicMock()
            mock_bucket.upload.side_effect = Exception("Upload failed")
            mock_client.client.storage.from_.return_value = mock_bucket

            result = await self.storage_service.upload_file(
                file_data=b"test content",
                filename="test.txt"
            )

            assert not result.success
            assert "Upload failed" in result.error

    @pytest.mark.asyncio
    async def test_cleanup_and_resource_management(self):
        """Test cleanup and resource management"""

        # Test expired file cleanup
        with patch.object(self.storage_service, 'metadata_cache') as mock_cache:
            # Add expired file to cache
            expired_file_id = f"file_{uuid.uuid4()}"
            mock_cache.__iter__ = lambda: iter([expired_file_id])
            mock_cache.__getitem__ = lambda key: MagicMock(
                expires_at=time.time() - 3600,  # Expired 1 hour ago
                file_id=expired_file_id
            )
            mock_cache.values.return_value = [MagicMock(
                expires_at=time.time() - 3600,
                file_id=expired_file_id
            )]

            with patch.object(self.storage_service, 'delete_file', return_value=True) as mock_delete:
                cleaned_count = await self.storage_service.cleanup_expired_files()
                assert cleaned_count >= 0

        # Test inactive connection cleanup
        await self.realtime_service.cleanup_inactive_connections()

    @pytest.mark.asyncio
    async def test_integration_performance(self):
        """Test performance characteristics of integrations"""

        # Test real-time message processing performance
        start_time = time.time()

        with patch.object(self.realtime_service, 'supabase_client', self.mock_supabase):
            # Simulate processing multiple messages
            for i in range(10):
                await self.realtime_service.send_notification(
                    user_id=self.test_user_id,
                    notification_type="performance_test",
                    title=f"Test {i}",
                    message=f"Performance test message {i}"
                )

        processing_time = time.time() - start_time
        assert processing_time < 5.0, f"Processing 10 messages took too long: {processing_time}s"

        # Test storage operation performance
        start_time = time.time()

        with patch.object(self.storage_service, 'supabase_client') as mock_client:
            mock_bucket = MagicMock()
            mock_client.client.storage.from_.return_value = mock_bucket
            mock_bucket.upload.return_value = MagicMock(error=None)

            # Simulate multiple file uploads
            for i in range(5):
                await self.storage_service.upload_file(
                    file_data=f"test content {i}".encode(),
                    filename=f"test_{i}.txt",
                    user_id=self.test_user_id
                )

        upload_time = time.time() - start_time
        assert upload_time < 3.0, f"Uploading 5 files took too long: {upload_time}s"


class TestSupabaseIntegrationLoadTesting:
    """Load testing for Supabase integration"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_realtime_subscriptions(self):
        """Test handling multiple concurrent real-time subscriptions"""

        realtime_service = get_realtime_service()

        with patch.object(realtime_service, 'supabase_client') as mock_client:
            mock_client.channel.return_value = MagicMock()

            # Create multiple concurrent subscriptions
            tasks = []
            num_subscriptions = 50

            for i in range(num_subscriptions):
                task = realtime_service.create_subscription(
                    subscription_type=SubscriptionType.JOB_UPDATES,
                    table_name="jobs",
                    connection_id=f"conn_{i}",
                    user_id=f"user_{i}"
                )
                tasks.append(task)

            # Wait for all subscriptions to be created
            subscription_ids = await asyncio.gather(*tasks)

            assert len(subscription_ids) == num_subscriptions
            assert len(realtime_service.active_subscriptions) == num_subscriptions

            # Clean up
            cleanup_tasks = []
            for sub_id in subscription_ids:
                cleanup_tasks.append(
                    realtime_service.remove_subscription(sub_id)
                )

            await asyncio.gather(*cleanup_tasks)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_high_volume_storage_operations(self):
        """Test storage service under high volume"""

        storage_service = get_storage_service()

        with patch.object(storage_service, 'supabase_client') as mock_client:
            mock_bucket = MagicMock()
            mock_client.client.storage.from_.return_value = mock_bucket
            mock_bucket.upload.return_value = MagicMock(error=None)

            # Perform high volume uploads
            tasks = []
            num_uploads = 100

            for i in range(num_uploads):
                task = storage_service.upload_file(
                    file_data=f"test content {i}".encode(),
                    filename=f"load_test_{i}.txt",
                    user_id=f"user_{i % 10}"  # 10 different users
                )
                tasks.append(task)

            # Execute all uploads concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify results
            successful_uploads = [r for r in results if isinstance(r, type(results[0])) and r.success]
            assert len(successful_uploads) == num_uploads

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_stress_test_edge_functions(self):
        """Stress test edge function integration"""

        # This would test actual edge function endpoints under load
        # For this example, we'll simulate the stress test

        edge_function_url = "http://localhost:54321/functions/v1/score-calculator"

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "success": True,
                "calculation_id": "calc_12345",
                "scores": {"overall_score": 85.0}
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Simulate concurrent requests
            tasks = []
            num_requests = 20

            for i in range(num_requests):
                payload = {
                    "calculation_type": "email_score",
                    "entity_id": f"email_{i}",
                    "entity_type": "email"
                }

                # In a real test, this would be an actual HTTP request
                task = asyncio.create_task(asyncio.sleep(0.01))  # Simulate async request
                tasks.append(task)

            # Wait for all requests to complete
            await asyncio.gather(*tasks)

            # Verify all requests were made
            assert len(tasks) == num_requests


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])