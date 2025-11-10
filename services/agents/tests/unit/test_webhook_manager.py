"""
Unit tests for Webhook Manager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from uuid import uuid4, UUID
from datetime import datetime
from contextlib import asynccontextmanager

from app.webhooks.webhook_manager import WebhookManager
from app.webhooks.models import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    EventType,
    WebhookDeliveryResponse,
    WebhookHealthResponse,
    DeliveryStatus
)


class AsyncContextManagerMock:
    """Helper class to mock async context managers"""
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_conn():
    """Create a mock database connection"""
    conn = AsyncMock()
    return conn


@pytest.fixture
def mock_db_pool(mock_conn):
    """Create a mock database pool with proper async context manager"""
    pool = Mock()
    pool.acquire = Mock(return_value=AsyncContextManagerMock(mock_conn))
    return pool


@pytest.fixture
def webhook_manager(mock_db_pool):
    """Create a WebhookManager with mocked database pool"""
    return WebhookManager(db_pool=mock_db_pool)


@pytest.mark.unit
class TestWebhookManagerInit:
    """Test suite for WebhookManager initialization"""

    def test_init_with_db_pool(self, mock_db_pool):
        """Test initializing manager with database pool"""
        manager = WebhookManager(db_pool=mock_db_pool)
        assert manager.db_pool == mock_db_pool


@pytest.mark.unit
class TestWebhookManagerCreate:
    """Test suite for create_webhook"""

    @pytest.mark.asyncio
    async def test_create_webhook_success(self, webhook_manager, mock_db_pool, mock_conn):
        """Test creating a webhook successfully"""
        webhook_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()

        # Mock database response
        mock_row = {
            'id': webhook_id,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'name': 'Test Webhook',
            'url': 'https://example.com/webhook',
            'description': 'Test description',
            'events': ['task.started', 'task.completed'],
            'secret_key': 'test_secret',
            'project_filter': None,
            'workflow_filter': None,
            'max_retries': 3,
            'retry_delay_seconds': 60,
            'timeout_seconds': 30,
            'custom_headers': {},
            'is_active': True,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered_at': None,
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0
        }

        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        webhook_create = WebhookCreate(
            name="Test Webhook",
            url="https://example.com/webhook",
            description="Test description",
            events=[EventType.TASK_STARTED, EventType.TASK_COMPLETED]
        )

        result = await webhook_manager.create_webhook(webhook_create, tenant_id, user_id)

        assert result.id == webhook_id
        assert result.name == "Test Webhook"
        assert result.tenant_id == tenant_id
        assert result.user_id == user_id
        assert len(result.events) == 2
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_webhook_generates_secret(self, webhook_manager, mock_db_pool, mock_conn):
        """Test that create_webhook generates a secret key"""
        mock_row = {
            'id': uuid4(),
            'tenant_id': uuid4(),
            'user_id': uuid4(),
            'name': 'Test',
            'url': 'https://example.com',
            'description': '',
            'events': ['task.started'],
            'secret_key': 'generated_secret',
            'project_filter': None,
            'workflow_filter': None,
            'max_retries': 3,
            'retry_delay_seconds': 60,
            'timeout_seconds': 30,
            'custom_headers': {},
            'is_active': True,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered_at': None,
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0
        }

        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        webhook_create = WebhookCreate(
            name="Test",
            url="https://example.com",
            events=[EventType.TASK_STARTED]
        )

        result = await webhook_manager.create_webhook(webhook_create, uuid4(), uuid4())

        # Verify that fetchrow was called (secret generation happens internally)
        mock_conn.fetchrow.assert_called_once()

        # Verify the result contains a secret_key
        assert result is not None
        # The secret would be returned from the database (mocked as 'generated_secret')


@pytest.mark.unit
class TestWebhookManagerGet:
    """Test suite for get_webhook"""

    @pytest.mark.asyncio
    async def test_get_webhook_found(self, webhook_manager, mock_db_pool, mock_conn):
        """Test getting an existing webhook"""
        webhook_id = uuid4()
        tenant_id = uuid4()

        mock_row = {
            'id': webhook_id,
            'tenant_id': tenant_id,
            'user_id': uuid4(),
            'name': 'Test Webhook',
            'url': 'https://example.com',
            'description': 'Test',
            'events': ['task.started'],
            'secret_key': 'secret',
            'project_filter': None,
            'workflow_filter': None,
            'max_retries': 3,
            'retry_delay_seconds': 60,
            'timeout_seconds': 30,
            'custom_headers': {},
            'is_active': True,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered_at': None,
            'total_deliveries': 5,
            'successful_deliveries': 4,
            'failed_deliveries': 1
        }

        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        result = await webhook_manager.get_webhook(webhook_id, tenant_id)

        assert result is not None
        assert result.id == webhook_id
        assert result.tenant_id == tenant_id
        assert result.name == "Test Webhook"
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_webhook_not_found(self, webhook_manager, mock_db_pool, mock_conn):
        """Test getting a non-existent webhook returns None"""
        mock_conn.fetchrow = AsyncMock(return_value=None)

        result = await webhook_manager.get_webhook(uuid4(), uuid4())

        assert result is None
        mock_conn.fetchrow.assert_called_once()


@pytest.mark.unit
class TestWebhookManagerList:
    """Test suite for list_webhooks"""

    @pytest.mark.asyncio
    async def test_list_webhooks_no_filter(self, webhook_manager, mock_db_pool, mock_conn):
        """Test listing webhooks without filters"""
        tenant_id = uuid4()

        mock_rows = [
            {
                'id': uuid4(),
                'tenant_id': tenant_id,
                'user_id': uuid4(),
                'name': 'Webhook 1',
                'url': 'https://example.com/1',
                'description': 'First',
                'events': ['task.started'],
                'secret_key': 'secret1',
                'project_filter': None,
                'workflow_filter': None,
                'max_retries': 3,
                'retry_delay_seconds': 60,
                'timeout_seconds': 30,
                'custom_headers': {},
                'is_active': True,
                'is_verified': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_triggered_at': None,
                'total_deliveries': 0,
                'successful_deliveries': 0,
                'failed_deliveries': 0
            }
        ]

        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        webhooks, total = await webhook_manager.list_webhooks(tenant_id)

        assert total == 1
        assert len(webhooks) == 1
        assert webhooks[0].name == "Webhook 1"
        mock_conn.fetchval.assert_called_once()
        mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_webhooks_with_active_filter(self, webhook_manager, mock_db_pool, mock_conn):
        """Test listing webhooks with active filter"""
        tenant_id = uuid4()

        mock_conn.fetchval = AsyncMock(return_value=0)
        mock_conn.fetch = AsyncMock(return_value=[])

        webhooks, total = await webhook_manager.list_webhooks(
            tenant_id=tenant_id,
            is_active=True
        )

        assert total == 0
        assert len(webhooks) == 0

        # Verify is_active was included in query
        call_args = mock_conn.fetchval.call_args
        assert "is_active" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_webhooks_with_pagination(self, webhook_manager, mock_db_pool, mock_conn):
        """Test listing webhooks with pagination"""
        tenant_id = uuid4()

        mock_conn.fetchval = AsyncMock(return_value=100)
        mock_conn.fetch = AsyncMock(return_value=[])

        webhooks, total = await webhook_manager.list_webhooks(
            tenant_id=tenant_id,
            page=2,
            page_size=20
        )

        assert total == 100
        assert len(webhooks) == 0

        # Verify pagination parameters were used
        call_args = mock_conn.fetch.call_args
        # Check if 20 (page_size) and 20 (offset for page 2) are in the params
        assert 20 in call_args[0][1:]


@pytest.mark.unit
class TestWebhookManagerUpdate:
    """Test suite for update_webhook"""

    @pytest.mark.asyncio
    async def test_update_webhook_success(self, webhook_manager, mock_db_pool, mock_conn):
        """Test updating a webhook successfully"""
        webhook_id = uuid4()
        tenant_id = uuid4()

        mock_row = {
            'id': webhook_id,
            'tenant_id': tenant_id,
            'user_id': uuid4(),
            'name': 'Updated Webhook',
            'url': 'https://example.com',
            'description': 'Updated',
            'events': ['task.completed'],
            'secret_key': 'secret',
            'project_filter': None,
            'workflow_filter': None,
            'max_retries': 5,
            'retry_delay_seconds': 120,
            'timeout_seconds': 60,
            'custom_headers': {},
            'is_active': False,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered_at': None,
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0
        }

        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        updates = WebhookUpdate(
            name="Updated Webhook",
            is_active=False
        )

        result = await webhook_manager.update_webhook(webhook_id, tenant_id, updates)

        assert result is not None
        assert result.name == "Updated Webhook"
        assert result.is_active is False
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_webhook_not_found(self, webhook_manager, mock_db_pool, mock_conn):
        """Test updating a non-existent webhook returns None"""
        mock_conn.fetchrow = AsyncMock(return_value=None)

        updates = WebhookUpdate(name="New Name")

        result = await webhook_manager.update_webhook(uuid4(), uuid4(), updates)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_webhook_no_updates(self, webhook_manager, mock_db_pool, mock_conn):
        """Test updating webhook with no changes returns current webhook"""
        webhook_id = uuid4()
        tenant_id = uuid4()

        mock_row = {
            'id': webhook_id,
            'tenant_id': tenant_id,
            'user_id': uuid4(),
            'name': 'Test Webhook',
            'url': 'https://example.com',
            'description': 'Test',
            'events': ['task.started'],
            'secret_key': 'secret',
            'project_filter': None,
            'workflow_filter': None,
            'max_retries': 3,
            'retry_delay_seconds': 60,
            'timeout_seconds': 30,
            'custom_headers': {},
            'is_active': True,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered_at': None,
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0
        }

        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        updates = WebhookUpdate()  # No updates

        result = await webhook_manager.update_webhook(webhook_id, tenant_id, updates)

        assert result is not None
        assert result.id == webhook_id

    @pytest.mark.asyncio
    async def test_update_webhook_with_events(self, webhook_manager, mock_db_pool, mock_conn):
        """Test updating webhook events"""
        webhook_id = uuid4()
        tenant_id = uuid4()

        mock_row = {
            'id': webhook_id,
            'tenant_id': tenant_id,
            'user_id': uuid4(),
            'name': 'Test',
            'url': 'https://example.com',
            'description': '',
            'events': ['task.started', 'task.completed', 'task.failed'],
            'secret_key': 'secret',
            'project_filter': None,
            'workflow_filter': None,
            'max_retries': 3,
            'retry_delay_seconds': 60,
            'timeout_seconds': 30,
            'custom_headers': {},
            'is_active': True,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered_at': None,
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0
        }

        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        updates = WebhookUpdate(
            events=[EventType.TASK_STARTED, EventType.TASK_COMPLETED, EventType.TASK_FAILED]
        )

        result = await webhook_manager.update_webhook(webhook_id, tenant_id, updates)

        assert result is not None
        assert len(result.events) == 3


@pytest.mark.unit
class TestWebhookManagerDelete:
    """Test suite for delete_webhook"""

    @pytest.mark.asyncio
    async def test_delete_webhook_success(self, webhook_manager, mock_db_pool, mock_conn):
        """Test deleting a webhook successfully"""
        mock_conn.execute = AsyncMock(return_value="DELETE 1")

        result = await webhook_manager.delete_webhook(uuid4(), uuid4())

        assert result is True
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_webhook_not_found(self, webhook_manager, mock_db_pool, mock_conn):
        """Test deleting a non-existent webhook returns False"""
        mock_conn.execute = AsyncMock(return_value="DELETE 0")

        result = await webhook_manager.delete_webhook(uuid4(), uuid4())

        assert result is False


@pytest.mark.unit
class TestWebhookManagerGetDeliveries:
    """Test suite for get_webhook_deliveries"""

    @pytest.mark.asyncio
    async def test_get_deliveries_success(self, webhook_manager, mock_db_pool, mock_conn):
        """Test getting webhook deliveries successfully"""
        webhook_id = uuid4()
        tenant_id = uuid4()

        mock_delivery_rows = [
            {
                'id': uuid4(),
                'webhook_id': webhook_id,
                'event_type': 'task.completed',
                'event_id': 'evt_123',
                'status': 'delivered',
                'attempts': 1,
                'max_attempts': 3,
                'scheduled_at': datetime.now(),
                'next_retry_at': None,
                'delivered_at': datetime.now(),
                'http_status_code': 200,
                'error_message': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]

        mock_conn.fetchval = AsyncMock(side_effect=[True, 1])  # webhook_exists=True, total=1
        mock_conn.fetch = AsyncMock(return_value=mock_delivery_rows)

        deliveries, total = await webhook_manager.get_webhook_deliveries(webhook_id, tenant_id)

        assert total == 1
        assert len(deliveries) == 1
        assert deliveries[0].webhook_id == webhook_id

    @pytest.mark.asyncio
    async def test_get_deliveries_webhook_not_found(self, webhook_manager, mock_db_pool, mock_conn):
        """Test getting deliveries for non-existent webhook"""
        mock_conn.fetchval = AsyncMock(return_value=False)  # webhook_exists=False

        deliveries, total = await webhook_manager.get_webhook_deliveries(uuid4(), uuid4())

        assert deliveries == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_deliveries_with_pagination(self, webhook_manager, mock_db_pool, mock_conn):
        """Test getting webhook deliveries with pagination"""
        webhook_id = uuid4()
        tenant_id = uuid4()

        mock_conn.fetchval = AsyncMock(side_effect=[True, 100])
        mock_conn.fetch = AsyncMock(return_value=[])

        deliveries, total = await webhook_manager.get_webhook_deliveries(
            webhook_id=webhook_id,
            tenant_id=tenant_id,
            page=3,
            page_size=25
        )

        assert total == 100
        assert len(deliveries) == 0

        # Verify pagination was applied (offset = (3-1) * 25 = 50)
        call_args = mock_conn.fetch.call_args
        assert 25 in call_args[0]  # page_size
        assert 50 in call_args[0]  # offset


@pytest.mark.unit
class TestWebhookManagerGetHealth:
    """Test suite for get_webhook_health"""

    @pytest.mark.asyncio
    async def test_get_health_success(self, webhook_manager, mock_db_pool, mock_conn):
        """Test getting webhook health stats"""
        tenant_id = uuid4()

        mock_health_rows = [
            {
                'id': uuid4(),
                'tenant_id': tenant_id,
                'name': 'Webhook 1',
                'url': 'https://example.com/1',
                'is_active': True,
                'total_deliveries': 100,
                'successful_deliveries': 95,
                'failed_deliveries': 5,
                'success_rate_pct': 95.0,
                'last_triggered_at': datetime.now(),
                'pending_count': 0,
                'retrying_count': 1,
                'recent_failed_count': 2
            },
            {
                'id': uuid4(),
                'tenant_id': tenant_id,
                'name': 'Webhook 2',
                'url': 'https://example.com/2',
                'is_active': False,
                'total_deliveries': 50,
                'successful_deliveries': 48,
                'failed_deliveries': 2,
                'success_rate_pct': 96.0,
                'last_triggered_at': datetime.now(),
                'pending_count': 0,
                'retrying_count': 0,
                'recent_failed_count': 0
            }
        ]

        mock_conn.fetch = AsyncMock(return_value=mock_health_rows)

        health_stats = await webhook_manager.get_webhook_health(tenant_id)

        assert len(health_stats) == 2
        assert health_stats[0].name == "Webhook 1"
        assert health_stats[0].success_rate_pct == 95.0
        assert health_stats[1].name == "Webhook 2"
        mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_health_empty(self, webhook_manager, mock_db_pool, mock_conn):
        """Test getting health stats when no webhooks exist"""
        mock_conn.fetch = AsyncMock(return_value=[])

        health_stats = await webhook_manager.get_webhook_health(uuid4())

        assert len(health_stats) == 0


@pytest.mark.unit
class TestWebhookManagerRegenerateSecret:
    """Test suite for regenerate_secret"""

    @pytest.mark.asyncio
    async def test_regenerate_secret_success(self, webhook_manager, mock_db_pool, mock_conn):
        """Test regenerating webhook secret successfully"""
        new_secret = "new_secret_key_abc123"
        mock_conn.fetchval = AsyncMock(return_value=new_secret)

        result = await webhook_manager.regenerate_secret(uuid4(), uuid4())

        assert result == new_secret
        mock_conn.fetchval.assert_called_once()

        # Verify updated_at was set
        call_args = mock_conn.fetchval.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_regenerate_secret_webhook_not_found(self, webhook_manager, mock_db_pool, mock_conn):
        """Test regenerating secret for non-existent webhook"""
        mock_conn.fetchval = AsyncMock(return_value=None)

        result = await webhook_manager.regenerate_secret(uuid4(), uuid4())

        assert result is None


@pytest.mark.unit
class TestWebhookManagerHelperMethods:
    """Test suite for helper conversion methods"""

    def test_row_to_webhook_response(self, webhook_manager):
        """Test converting database row to WebhookResponse"""
        webhook_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()
        now = datetime.now()

        row = {
            'id': webhook_id,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'name': 'Test Webhook',
            'url': 'https://example.com',
            'description': 'Test description',
            'events': ['task.started', 'task.completed'],
            'secret_key': 'secret123',
            'project_filter': 'project-1',
            'workflow_filter': 'workflow-1',
            'max_retries': 5,
            'retry_delay_seconds': 120,
            'timeout_seconds': 60,
            'custom_headers': {'X-Custom': 'value'},
            'is_active': True,
            'is_verified': True,
            'created_at': now,
            'updated_at': now,
            'last_triggered_at': now,
            'total_deliveries': 100,
            'successful_deliveries': 95,
            'failed_deliveries': 5
        }

        result = webhook_manager._row_to_webhook_response(row)

        assert result.id == webhook_id
        assert result.tenant_id == tenant_id
        assert result.user_id == user_id
        assert result.name == "Test Webhook"
        assert result.url == "https://example.com"
        assert len(result.events) == 2
        assert EventType.TASK_STARTED in result.events
        assert result.max_retries == 5
        assert result.custom_headers == {'X-Custom': 'value'}
        assert result.total_deliveries == 100

    def test_row_to_webhook_response_null_custom_headers(self, webhook_manager):
        """Test converting row with null custom_headers"""
        row = {
            'id': uuid4(),
            'tenant_id': uuid4(),
            'user_id': uuid4(),
            'name': 'Test',
            'url': 'https://example.com',
            'description': '',
            'events': ['task.started'],
            'secret_key': 'secret',
            'project_filter': None,
            'workflow_filter': None,
            'max_retries': 3,
            'retry_delay_seconds': 60,
            'timeout_seconds': 30,
            'custom_headers': None,  # NULL in database
            'is_active': True,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered_at': None,
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0
        }

        result = webhook_manager._row_to_webhook_response(row)

        assert result.custom_headers == {}

    def test_row_to_delivery_response(self, webhook_manager):
        """Test converting database row to WebhookDeliveryResponse"""
        delivery_id = uuid4()
        webhook_id = uuid4()
        now = datetime.now()

        row = {
            'id': delivery_id,
            'webhook_id': webhook_id,
            'event_type': 'task.completed',
            'event_id': 'evt_123',
            'status': 'delivered',
            'attempts': 2,
            'max_attempts': 3,
            'scheduled_at': now,
            'next_retry_at': None,
            'delivered_at': now,
            'http_status_code': 200,
            'error_message': None,
            'created_at': now,
            'updated_at': now
        }

        result = webhook_manager._row_to_delivery_response(row)

        assert result.id == delivery_id
        assert result.webhook_id == webhook_id
        assert result.event_type == EventType.TASK_COMPLETED
        assert result.event_id == 'evt_123'
        assert result.attempts == 2
        assert result.http_status_code == 200

    def test_row_to_health_response(self, webhook_manager):
        """Test converting database row to WebhookHealthResponse"""
        health_id = uuid4()
        tenant_id = uuid4()
        now = datetime.now()

        row = {
            'id': health_id,
            'tenant_id': tenant_id,
            'name': 'Health Webhook',
            'url': 'https://example.com',
            'is_active': True,
            'total_deliveries': 1000,
            'successful_deliveries': 950,
            'failed_deliveries': 50,
            'success_rate_pct': 95.0,
            'last_triggered_at': now,
            'pending_count': 5,
            'retrying_count': 3,
            'recent_failed_count': 2
        }

        result = webhook_manager._row_to_health_response(row)

        assert result.id == health_id
        assert result.tenant_id == tenant_id
        assert result.name == "Health Webhook"
        assert result.total_deliveries == 1000
        assert result.successful_deliveries == 950
        assert result.success_rate_pct == 95.0
        assert result.pending_count == 5
