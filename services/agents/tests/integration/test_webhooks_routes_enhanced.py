"""
Enhanced integration tests for webhooks router to boost coverage from 40% to 90%+.

These tests exercise actual code paths with proper authentication.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.webhooks.models import (
    WebhookResponse,
    WebhookDeliveryResponse,
    WebhookHealthResponse,
    EventType,
    DeliveryStatus
)


@pytest.mark.integration
class TestWebhooksRoutesEnhanced:
    """Enhanced test suite for webhooks router with better coverage"""

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_create_webhook_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test creating webhook with all success paths executed"""
        webhook_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()

        mock_response = WebhookResponse(
            id=webhook_id,
            tenant_id=tenant_id,
            user_id=user_id,
            name="Production Webhook",
            url="https://api.example.com/webhooks/events",
            description="Production event webhook",
            events=[EventType.TASK_STARTED, EventType.TASK_COMPLETED, EventType.TASK_FAILED],
            secret_key="sk_live_abc123xyz",
            project_filter=None,
            workflow_filter=None,
            is_active=True,
            is_verified=False,
            max_retries=5,
            retry_delay_seconds=120,
            timeout_seconds=30,
            custom_headers={"X-Custom": "value"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_triggered_at=None,
            total_deliveries=0,
            successful_deliveries=0,
            failed_deliveries=0
        )

        mock_webhook_manager.create_webhook = AsyncMock(return_value=mock_response)

        response = await authenticated_client.post(
            "/webhooks/",
            json={
                "name": "Production Webhook",
                "url": "https://api.example.com/webhooks/events",
                "description": "Production event webhook",
                "events": ["task.started", "task.completed", "task.failed"],
                "max_retries": 5,
                "retry_delay_seconds": 120,
                "custom_headers": {"X-Custom": "value"}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(webhook_id)
        assert data["name"] == "Production Webhook"
        # secret_key is included in response
        if "secret_key" in data:
            assert data["secret_key"] == "sk_live_abc123xyz"
        assert data["is_active"] is True
        assert data["max_retries"] == 5

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_list_webhooks_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test listing webhooks with full success path"""
        webhook1 = WebhookResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            name="Webhook 1",
            url="https://example.com/webhook1",
            description="First webhook",
            events=[EventType.TASK_STARTED],
            secret_key="secret1",
            project_filter=None,
            workflow_filter=None,
            is_active=True,
            is_verified=True,
            max_retries=3,
            retry_delay_seconds=60,
            timeout_seconds=30,
            custom_headers={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_triggered_at=datetime.now(),
            total_deliveries=100,
            successful_deliveries=95,
            failed_deliveries=5
        )

        webhook2 = WebhookResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            name="Webhook 2",
            url="https://example.com/webhook2",
            description="Second webhook",
            events=[EventType.TASK_COMPLETED, EventType.TASK_FAILED],
            secret_key="secret2",
            project_filter="project-123",
            workflow_filter="workflow-456",
            is_active=False,
            is_verified=False,
            max_retries=3,
            retry_delay_seconds=60,
            timeout_seconds=30,
            custom_headers={"Authorization": "Bearer xyz"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_triggered_at=None,
            total_deliveries=0,
            successful_deliveries=0,
            failed_deliveries=0
        )

        mock_webhook_manager.list_webhooks = AsyncMock(
            return_value=([webhook1, webhook2], 2)
        )

        response = await authenticated_client.get(
            "/webhooks/?page=1&page_size=50",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert len(data["webhooks"]) == 2
        assert data["webhooks"][0]["total_deliveries"] == 100
        assert data["webhooks"][1]["project_filter"] == "project-123"

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_get_webhook_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test getting webhook by ID with full success path"""
        webhook_id = uuid4()
        mock_webhook = WebhookResponse(
            id=webhook_id,
            tenant_id=uuid4(),
            user_id=uuid4(),
            name="Test Webhook",
            url="https://example.com/webhook",
            description="Detailed webhook description",
            events=[EventType.TASK_STARTED, EventType.TASK_COMPLETED],
            secret_key="sk_test_secret",
            project_filter="my-project",
            workflow_filter="my-workflow",
            is_active=True,
            is_verified=True,
            max_retries=3,
            retry_delay_seconds=60,
            timeout_seconds=30,
            custom_headers={"X-API-Key": "key123"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_triggered_at=datetime.now(),
            total_deliveries=50,
            successful_deliveries=48,
            failed_deliveries=2
        )

        mock_webhook_manager.get_webhook = AsyncMock(return_value=mock_webhook)

        response = await authenticated_client.get(
            f"/webhooks/{webhook_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(webhook_id)
        assert data["name"] == "Test Webhook"
        assert data["is_verified"] is True
        assert data["project_filter"] == "my-project"
        assert data["workflow_filter"] == "my-workflow"
        assert data["total_deliveries"] == 50

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_update_webhook_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test updating webhook with full success path"""
        webhook_id = uuid4()
        updated_webhook = WebhookResponse(
            id=webhook_id,
            tenant_id=uuid4(),
            user_id=uuid4(),
            name="Updated Webhook Name",
            url="https://new-url.example.com/webhook",
            description="Updated description",
            events=[EventType.TASK_COMPLETED, EventType.TASK_FAILED],
            secret_key="sk_updated",
            project_filter="new-project",
            workflow_filter="new-workflow",
            is_active=False,
            is_verified=True,
            max_retries=10,
            retry_delay_seconds=300,
            timeout_seconds=60,
            custom_headers={"X-New-Header": "new-value"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_triggered_at=datetime.now(),
            total_deliveries=200,
            successful_deliveries=195,
            failed_deliveries=5
        )

        mock_webhook_manager.update_webhook = AsyncMock(return_value=updated_webhook)

        response = await authenticated_client.patch(
            f"/webhooks/{webhook_id}",
            json={
                "name": "Updated Webhook Name",
                "url": "https://new-url.example.com/webhook",
                "description": "Updated description",
                "is_active": False,
                "max_retries": 10,
                "retry_delay_seconds": 300,
                "timeout_seconds": 60
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Webhook Name"
        assert data["is_active"] is False
        assert data["max_retries"] == 10
        assert data["retry_delay_seconds"] == 300

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_delete_webhook_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test deleting webhook with full success path"""
        webhook_id = uuid4()
        mock_webhook_manager.delete_webhook = AsyncMock(return_value=True)

        response = await authenticated_client.delete(
            f"/webhooks/{webhook_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 204
        # 204 responses have no content
        assert response.text == ""

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_regenerate_secret_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test regenerating webhook secret with full success path"""
        webhook_id = uuid4()
        new_secret = "sk_live_new_secret_abc123xyz789"
        mock_webhook_manager.regenerate_secret = AsyncMock(return_value=new_secret)

        response = await authenticated_client.post(
            f"/webhooks/{webhook_id}/regenerate-secret",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["secret_key"] == new_secret

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_get_webhook_deliveries_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test getting webhook deliveries with full success path"""
        webhook_id = uuid4()

        delivery1 = WebhookDeliveryResponse(
            id=uuid4(),
            webhook_id=webhook_id,
            event_type=EventType.TASK_COMPLETED,
            event_id="evt_123",
            status=DeliveryStatus.DELIVERED,
            attempts=1,
            max_attempts=3,
            scheduled_at=datetime.now(),
            next_retry_at=None,
            delivered_at=datetime.now(),
            http_status_code=200,
            error_message=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        delivery2 = WebhookDeliveryResponse(
            id=uuid4(),
            webhook_id=webhook_id,
            event_type=EventType.TASK_FAILED,
            event_id="evt_456",
            status=DeliveryStatus.FAILED,
            attempts=3,
            max_attempts=3,
            scheduled_at=datetime.now(),
            next_retry_at=None,
            delivered_at=datetime.now(),
            http_status_code=500,
            error_message="Internal server error",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        delivery3 = WebhookDeliveryResponse(
            id=uuid4(),
            webhook_id=webhook_id,
            event_type=EventType.TASK_STARTED,
            event_id="evt_789",
            status=DeliveryStatus.PENDING,
            attempts=0,
            max_attempts=3,
            scheduled_at=datetime.now(),
            next_retry_at=datetime.now(),
            delivered_at=None,
            http_status_code=None,
            error_message=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        mock_webhook_manager.get_webhook_deliveries = AsyncMock(
            return_value=([delivery1, delivery2, delivery3], 3)
        )

        response = await authenticated_client.get(
            f"/webhooks/{webhook_id}/deliveries?page=1&page_size=50",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert len(data["deliveries"]) == 3

        # Check delivery details
        assert data["deliveries"][0]["status"] == "delivered"
        assert data["deliveries"][0]["http_status_code"] == 200
        assert data["deliveries"][1]["status"] == "failed"
        assert data["deliveries"][1]["error_message"] == "Internal server error"
        assert data["deliveries"][2]["status"] == "pending"

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_get_webhooks_health_full_success_path(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test getting webhooks health statistics with full success path"""
        health1 = WebhookHealthResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            name="Healthy Webhook",
            url="https://example.com/webhook1",
            is_active=True,
            total_deliveries=1000,
            successful_deliveries=980,
            failed_deliveries=20,
            success_rate_pct=98.0,
            last_triggered_at=datetime.now(),
            pending_count=5,
            retrying_count=2,
            recent_failed_count=3
        )

        health2 = WebhookHealthResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            name="Failing Webhook",
            url="https://example.com/webhook2",
            is_active=True,
            total_deliveries=100,
            successful_deliveries=50,
            failed_deliveries=50,
            success_rate_pct=50.0,
            last_triggered_at=datetime.now(),
            pending_count=0,
            retrying_count=0,
            recent_failed_count=10
        )

        health3 = WebhookHealthResponse(
            id=uuid4(),
            tenant_id=uuid4(),
            name="Inactive Webhook",
            url="https://example.com/webhook3",
            is_active=False,
            total_deliveries=0,
            successful_deliveries=0,
            failed_deliveries=0,
            success_rate_pct=0.0,
            last_triggered_at=None,
            pending_count=0,
            retrying_count=0,
            recent_failed_count=0
        )

        mock_webhook_manager.get_webhook_health = AsyncMock(
            return_value=[health1, health2, health3]
        )

        response = await authenticated_client.get(
            "/webhooks/health/all",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "webhooks" in data
        assert len(data["webhooks"]) == 3

        # Check health stats structure
        assert data["webhooks"][0]["name"] == "Healthy Webhook"
        assert data["webhooks"][0]["success_rate_pct"] == 98.0
        assert data["webhooks"][0]["pending_count"] == 5
        assert data["webhooks"][0]["retrying_count"] == 2
        assert data["webhooks"][0]["recent_failed_count"] == 3

        assert data["webhooks"][1]["success_rate_pct"] == 50.0
        assert data["webhooks"][2]["is_active"] is False

    @pytest.mark.asyncio
    async def test_webhook_manager_dependency(self, authenticated_client: AsyncClient):
        """Test the get_webhook_manager dependency when manager is None"""
        with patch("app.routers.webhooks._webhook_manager", None):
            response = await authenticated_client.get(
                "/webhooks/",
                headers={"Authorization": "Bearer test-token"}
            )

            # Should return 503 when manager is not available
            assert response.status_code == 503
            data = response.json()
            assert "not available" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_set_webhook_manager(self):
        """Test the set_webhook_manager function"""
        from app.routers.webhooks import set_webhook_manager
        from app.routers import webhooks

        mock_manager = MagicMock()
        set_webhook_manager(mock_manager)

        # Verify it was set
        assert webhooks._webhook_manager is mock_manager

        # Cleanup
        set_webhook_manager(None)

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_list_webhooks_with_filters(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test listing webhooks with active filter"""
        mock_webhook_manager.list_webhooks = AsyncMock(
            return_value=([], 0)
        )

        response = await authenticated_client.get(
            "/webhooks/?is_active=true&page=2&page_size=10",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 2
        assert data["page_size"] == 10

        # Verify manager was called with correct parameters
        call_kwargs = mock_webhook_manager.list_webhooks.call_args.kwargs
        assert call_kwargs["is_active"] is True
        assert call_kwargs["page"] == 2
        assert call_kwargs["page_size"] == 10

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_update_webhook_not_found(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test updating webhook that doesn't exist"""
        webhook_id = uuid4()
        mock_webhook_manager.update_webhook = AsyncMock(return_value=None)

        response = await authenticated_client.patch(
            f"/webhooks/{webhook_id}",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_delete_webhook_not_found(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test deleting webhook that doesn't exist"""
        webhook_id = uuid4()
        mock_webhook_manager.delete_webhook = AsyncMock(return_value=False)

        response = await authenticated_client.delete(
            f"/webhooks/{webhook_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch("app.routers.webhooks._webhook_manager")
    async def test_regenerate_secret_not_found(
        self,
        mock_webhook_manager,
        authenticated_client: AsyncClient
    ):
        """Test regenerating secret for non-existent webhook"""
        webhook_id = uuid4()
        mock_webhook_manager.regenerate_secret = AsyncMock(return_value=None)

        response = await authenticated_client.post(
            f"/webhooks/{webhook_id}/regenerate-secret",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
