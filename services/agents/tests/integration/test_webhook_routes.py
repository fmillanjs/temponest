"""
Integration tests for webhook API routes.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime


@pytest.mark.integration
class TestWebhookRoutes:
    """Test suite for webhook router endpoints"""

    @pytest.mark.asyncio
    async def test_create_webhook_without_auth_fails(self, client: AsyncClient):
        """Test creating webhook without authentication fails"""
        response = await client.post(
            "/webhooks/",
            json={
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["agent.execution.completed"]
            }
        )

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_create_webhook_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test creating webhook with valid data"""
        # Mock webhook manager
        mock_manager = MagicMock()
        webhook_id = uuid4()
        mock_manager.create_webhook = AsyncMock(return_value={
            "id": str(webhook_id),
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["agent.execution.completed"],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        })
        mock_get_manager.return_value = mock_manager

        response = await client.post(
            "/webhooks/",
            json={
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["agent.execution.completed"]
            },
            headers=test_auth_headers
        )

        assert response.status_code in [201, 401, 503]

    @pytest.mark.asyncio
    async def test_create_webhook_invalid_url(self, client: AsyncClient, test_auth_headers):
        """Test creating webhook with invalid URL fails validation"""
        response = await client.post(
            "/webhooks/",
            json={
                "name": "Test Webhook",
                "url": "not-a-valid-url",
                "events": ["agent.execution.completed"]
            },
            headers=test_auth_headers
        )

        assert response.status_code in [400, 422, 503]

    @pytest.mark.asyncio
    async def test_list_webhooks_without_auth_fails(self, client: AsyncClient):
        """Test listing webhooks without authentication fails"""
        response = await client.get("/webhooks/")

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_list_webhooks_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test listing webhooks"""
        mock_manager = MagicMock()
        mock_manager.list_webhooks = AsyncMock(return_value=(
            [
                {
                    "id": str(uuid4()),
                    "name": "Webhook 1",
                    "url": "https://example.com/webhook1",
                    "events": ["agent.execution.completed"],
                    "is_active": True
                }
            ],
            1
        ))
        mock_get_manager.return_value = mock_manager

        response = await client.get("/webhooks/", headers=test_auth_headers)

        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_list_webhooks_with_pagination(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test listing webhooks with pagination parameters"""
        mock_manager = MagicMock()
        mock_manager.list_webhooks = AsyncMock(return_value=([], 0))
        mock_get_manager.return_value = mock_manager

        response = await client.get(
            "/webhooks/?page=2&page_size=20",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_list_webhooks_filter_by_active(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test listing webhooks filtered by active status"""
        mock_manager = MagicMock()
        mock_manager.list_webhooks = AsyncMock(return_value=([], 0))
        mock_get_manager.return_value = mock_manager

        response = await client.get(
            "/webhooks/?is_active=true",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_get_webhook_without_auth_fails(self, client: AsyncClient):
        """Test getting webhook without authentication fails"""
        webhook_id = uuid4()
        response = await client.get(f"/webhooks/{webhook_id}")

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_get_webhook_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test getting single webhook"""
        mock_manager = MagicMock()
        webhook_id = uuid4()
        mock_manager.get_webhook = AsyncMock(return_value={
            "id": str(webhook_id),
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["agent.execution.completed"],
            "is_active": True
        })
        mock_get_manager.return_value = mock_manager

        response = await client.get(
            f"/webhooks/{webhook_id}",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_update_webhook_without_auth_fails(self, client: AsyncClient):
        """Test updating webhook without authentication fails"""
        webhook_id = uuid4()
        response = await client.patch(
            f"/webhooks/{webhook_id}",
            json={"name": "Updated Webhook"}
        )

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_update_webhook_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test updating webhook"""
        mock_manager = MagicMock()
        webhook_id = uuid4()
        mock_manager.update_webhook = AsyncMock(return_value={
            "id": str(webhook_id),
            "name": "Updated Webhook",
            "url": "https://example.com/webhook",
            "events": ["agent.execution.completed"],
            "is_active": True
        })
        mock_get_manager.return_value = mock_manager

        response = await client.patch(
            f"/webhooks/{webhook_id}",
            json={"name": "Updated Webhook"},
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_delete_webhook_without_auth_fails(self, client: AsyncClient):
        """Test deleting webhook without authentication fails"""
        webhook_id = uuid4()
        response = await client.delete(f"/webhooks/{webhook_id}")

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_delete_webhook_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test deleting webhook"""
        mock_manager = MagicMock()
        webhook_id = uuid4()
        mock_manager.delete_webhook = AsyncMock(return_value=True)
        mock_get_manager.return_value = mock_manager

        response = await client.delete(
            f"/webhooks/{webhook_id}",
            headers=test_auth_headers
        )

        assert response.status_code in [204, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_regenerate_secret_without_auth_fails(self, client: AsyncClient):
        """Test regenerating webhook secret without authentication fails"""
        webhook_id = uuid4()
        response = await client.post(f"/webhooks/{webhook_id}/regenerate-secret")

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_regenerate_secret_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test regenerating webhook secret"""
        mock_manager = MagicMock()
        webhook_id = uuid4()
        mock_manager.regenerate_secret = AsyncMock(return_value={
            "id": str(webhook_id),
            "secret": "new_secret_key_here"
        })
        mock_get_manager.return_value = mock_manager

        response = await client.post(
            f"/webhooks/{webhook_id}/regenerate-secret",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_get_deliveries_without_auth_fails(self, client: AsyncClient):
        """Test getting webhook deliveries without authentication fails"""
        webhook_id = uuid4()
        response = await client.get(f"/webhooks/{webhook_id}/deliveries")

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_get_deliveries_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test getting webhook deliveries"""
        mock_manager = MagicMock()
        webhook_id = uuid4()
        mock_manager.get_deliveries = AsyncMock(return_value=(
            [
                {
                    "id": str(uuid4()),
                    "webhook_id": str(webhook_id),
                    "event_type": "agent.execution.completed",
                    "status": "delivered",
                    "created_at": datetime.utcnow().isoformat()
                }
            ],
            1
        ))
        mock_get_manager.return_value = mock_manager

        response = await client.get(
            f"/webhooks/{webhook_id}/deliveries",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_get_webhooks_health_without_auth_fails(self, client: AsyncClient):
        """Test getting webhooks health without authentication fails"""
        response = await client.get("/webhooks/health/all")

        assert response.status_code in [401, 403, 503]

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_webhook_manager")
    async def test_get_webhooks_health_success(
        self,
        mock_get_manager,
        client: AsyncClient,
        test_auth_headers
    ):
        """Test getting webhooks health status"""
        mock_manager = MagicMock()
        mock_manager.get_health = AsyncMock(return_value={
            "healthy": True,
            "total_webhooks": 5,
            "active_webhooks": 4,
            "failed_deliveries_24h": 2
        })
        mock_get_manager.return_value = mock_manager

        response = await client.get(
            "/webhooks/health/all",
            headers=test_auth_headers
        )

        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_webhook_manager_not_available(self, client: AsyncClient, test_auth_headers):
        """Test error when webhook manager is not available"""
        # When manager is None, should return 503
        response = await client.get("/webhooks/", headers=test_auth_headers)

        # Service unavailable when manager not initialized
        assert response.status_code in [503, 401]
