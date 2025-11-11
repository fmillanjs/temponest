"""
Unit tests for WebhooksClient
"""
import pytest
from unittest.mock import Mock, patch
from temponest_sdk.webhooks import WebhooksClient, Webhook, WebhookDelivery
from temponest_sdk.client import BaseClient


class TestWebhooksClientCreate:
    """Test webhook creation"""

    def test_create_webhook(self, clean_env, mock_webhook_data):
        """Test creating a webhook"""
        with patch.object(BaseClient, 'post', return_value=mock_webhook_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhook = webhooks_client.create(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=["agent.execution.completed", "agent.execution.failed"],
                secret="webhook-secret"
            )

            assert isinstance(webhook, Webhook)
            assert webhook.id == "webhook-123"
            assert webhook.url == "https://example.com/webhook"
            assert len(webhook.events) == 2

    def test_create_webhook_minimal(self, clean_env, mock_webhook_data):
        """Test creating webhook with minimal parameters"""
        with patch.object(BaseClient, 'post', return_value=mock_webhook_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhook = webhooks_client.create(
                name="Minimal Webhook",
                url="https://example.com/webhook",
                events=["agent.execution.completed"]
            )

            assert webhook.id == "webhook-123"


class TestWebhooksClientGet:
    """Test getting webhook"""

    def test_get_webhook_success(self, clean_env, mock_webhook_data):
        """Test getting webhook by ID"""
        with patch.object(BaseClient, 'get', return_value=mock_webhook_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhook = webhooks_client.get("webhook-123")

            assert isinstance(webhook, Webhook)
            assert webhook.id == "webhook-123"

    def test_get_webhook_not_found(self, clean_env):
        """Test getting non-existent webhook"""
        with patch.object(BaseClient, 'get', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            with pytest.raises(Exception, match="404"):
                webhooks_client.get("webhook-123")


class TestWebhooksClientList:
    """Test listing webhooks"""

    def test_list_webhooks(self, clean_env, mock_webhook_data):
        """Test listing all webhooks"""
        with patch.object(BaseClient, 'get', return_value=[mock_webhook_data]):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhooks = webhooks_client.list()

            assert len(webhooks) == 1
            assert isinstance(webhooks[0], Webhook)

    def test_list_webhooks_active_only(self, clean_env, mock_webhook_data):
        """Test listing only active webhooks"""
        with patch.object(BaseClient, 'get', return_value=[mock_webhook_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhooks = webhooks_client.list(is_active=True)

            call_args = mock_get.call_args
            assert call_args[1]['params']['is_active'] == True


class TestWebhooksClientUpdate:
    """Test updating webhook"""

    def test_update_webhook_url(self, clean_env, mock_webhook_data):
        """Test updating webhook URL"""
        updated_data = {**mock_webhook_data, "url": "https://new-url.com/webhook"}
        with patch.object(BaseClient, 'patch', return_value=updated_data) as mock_patch:
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhook = webhooks_client.update(
                "webhook-123",
                url="https://new-url.com/webhook"
            )

            assert webhook.url == "https://new-url.com/webhook"
            call_args = mock_patch.call_args
            assert call_args[1]['json']['url'] == "https://new-url.com/webhook"

    def test_update_webhook_events(self, clean_env, mock_webhook_data):
        """Test updating webhook events"""
        with patch.object(BaseClient, 'patch', return_value=mock_webhook_data) as mock_patch:
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhook = webhooks_client.update(
                "webhook-123",
                events=["agent.execution.completed"]
            )

            call_args = mock_patch.call_args
            assert call_args[1]['json']['events'] == ["agent.execution.completed"]

    def test_activate_webhook(self, clean_env, mock_webhook_data):
        """Test activating webhook"""
        with patch.object(BaseClient, 'patch', return_value=mock_webhook_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhook = webhooks_client.activate("webhook-123")

            assert webhook.is_active == True

    def test_deactivate_webhook(self, clean_env, mock_webhook_data):
        """Test deactivating webhook"""
        deactivated_data = {**mock_webhook_data, "is_active": False}
        with patch.object(BaseClient, 'patch', return_value=deactivated_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhook = webhooks_client.deactivate("webhook-123")

            assert webhook.is_active == False


class TestWebhooksClientDelete:
    """Test deleting webhook"""

    def test_delete_webhook_success(self, clean_env):
        """Test deleting a webhook"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            webhooks_client.delete("webhook-123")
            # No exception means success


class TestWebhooksClientDeliveries:
    """Test webhook deliveries"""

    def test_list_deliveries(self, clean_env, mock_webhook_delivery_data):
        """Test listing webhook deliveries"""
        with patch.object(BaseClient, 'get', return_value=[mock_webhook_delivery_data]):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            deliveries = webhooks_client.get_deliveries("webhook-123")

            assert len(deliveries) == 1
            assert isinstance(deliveries[0], WebhookDelivery)
            assert deliveries[0].webhook_id == "webhook-123"

    def test_list_deliveries_by_status(self, clean_env, mock_webhook_delivery_data):
        """Test listing deliveries filtered by status"""
        with patch.object(BaseClient, 'get', return_value=[mock_webhook_delivery_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            deliveries = webhooks_client.get_deliveries(
                "webhook-123",
                status="delivered"
            )

            call_args = mock_get.call_args
            assert call_args[1]['params']['status'] == "delivered"

    def test_get_delivery(self, clean_env, mock_webhook_delivery_data):
        """Test getting specific delivery"""
        with patch.object(BaseClient, 'get', return_value=mock_webhook_delivery_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            delivery = webhooks_client.get_delivery("delivery-123")

            assert isinstance(delivery, WebhookDelivery)
            assert delivery.id == "delivery-123"

    def test_retry_delivery(self, clean_env, mock_webhook_delivery_data):
        """Test retrying failed delivery"""
        retry_data = {**mock_webhook_delivery_data, "attempt_count": 2}
        with patch.object(BaseClient, 'post', return_value=retry_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            delivery = webhooks_client.retry_delivery("delivery-123")

            assert delivery.attempt_count == 2

    def test_test_webhook(self, clean_env, mock_webhook_delivery_data):
        """Test sending a test webhook"""
        with patch.object(BaseClient, 'post', return_value=mock_webhook_delivery_data):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            delivery = webhooks_client.test("webhook-123")

            assert isinstance(delivery, WebhookDelivery)
            assert delivery.webhook_id == "webhook-123"

    def test_get_events(self, clean_env):
        """Test getting available webhook events"""
        events = [
            "agent.execution.started",
            "agent.execution.completed",
            "agent.execution.failed"
        ]
        with patch.object(BaseClient, 'get', return_value=events):
            client = BaseClient(base_url="http://test.com")
            webhooks_client = WebhooksClient(client)

            result = webhooks_client.get_events()

            assert len(result) == 3
            assert "agent.execution.completed" in result
