"""
Unit tests for webhook models.
"""

import pytest
from pydantic import ValidationError
from app.webhooks.models import (
    EventType,
    DeliveryStatus,
    WebhookCreate,
    WebhookUpdate
)


@pytest.mark.unit
class TestWebhookModels:
    """Test suite for webhook Pydantic models"""

    def test_event_type_enum_values(self):
        """Test EventType enum has expected values"""
        assert EventType.TASK_STARTED == "task.started"
        assert EventType.TASK_COMPLETED == "task.completed"
        assert EventType.TASK_FAILED == "task.failed"
        assert EventType.BUDGET_WARNING == "budget.warning"
        assert EventType.BUDGET_EXCEEDED == "budget.exceeded"
        assert EventType.BUDGET_CRITICAL == "budget.critical"

    def test_delivery_status_enum_values(self):
        """Test DeliveryStatus enum values"""
        assert DeliveryStatus.PENDING == "pending"
        assert DeliveryStatus.DELIVERED == "delivered"
        assert DeliveryStatus.FAILED == "failed"
        assert DeliveryStatus.RETRYING == "retrying"

    def test_webhook_create_valid(self):
        """Test creating a valid webhook"""
        webhook = WebhookCreate(
            name="Test Webhook",
            url="https://example.com/webhook",
            description="Test webhook for agent events",
            events=[EventType.TASK_COMPLETED, EventType.TASK_FAILED],
            project_filter="project-123",
            max_retries=5,
            retry_delay_seconds=120,
            timeout_seconds=60
        )

        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/webhook"
        assert len(webhook.events) == 2
        assert webhook.max_retries == 5

    def test_webhook_create_http_url_allowed(self):
        """Test that HTTP URLs are allowed (for local testing)"""
        webhook = WebhookCreate(
            name="Test Webhook",
            url="http://localhost:8000/webhook",
            events=[EventType.TASK_COMPLETED]
        )

        assert webhook.url == "http://localhost:8000/webhook"

    def test_webhook_create_invalid_url(self):
        """Test webhook creation fails with invalid URL"""
        with pytest.raises(ValidationError) as exc_info:
            WebhookCreate(
                name="Test Webhook",
                url="invalid-url",
                events=[EventType.TASK_COMPLETED]
            )

        assert "URL must start with http:// or https://" in str(exc_info.value)

    def test_webhook_create_empty_name_fails(self):
        """Test webhook creation fails with empty name"""
        with pytest.raises(ValidationError):
            WebhookCreate(
                name="",
                url="https://example.com/webhook",
                events=[EventType.TASK_COMPLETED]
            )

    def test_webhook_create_empty_events_fails(self):
        """Test webhook creation fails with no events"""
        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=[]
            )

    def test_webhook_create_default_values(self):
        """Test webhook creation uses default values"""
        webhook = WebhookCreate(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=[EventType.TASK_COMPLETED]
        )

        assert webhook.max_retries == 3
        assert webhook.retry_delay_seconds == 60
        assert webhook.timeout_seconds == 30
        assert webhook.is_active is True
        assert webhook.custom_headers == {}

    def test_webhook_create_max_retries_validation(self):
        """Test max_retries must be within range"""
        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=[EventType.TASK_COMPLETED],
                max_retries=15  # Too high
            )

        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=[EventType.TASK_COMPLETED],
                max_retries=-1  # Negative
            )

    def test_webhook_create_retry_delay_validation(self):
        """Test retry_delay_seconds must be within range"""
        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=[EventType.TASK_COMPLETED],
                retry_delay_seconds=5  # Too low
            )

        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=[EventType.TASK_COMPLETED],
                retry_delay_seconds=4000  # Too high
            )

    def test_webhook_create_timeout_validation(self):
        """Test timeout_seconds must be within range"""
        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=[EventType.TASK_COMPLETED],
                timeout_seconds=3  # Too low
            )

        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=[EventType.TASK_COMPLETED],
                timeout_seconds=200  # Too high
            )

    def test_webhook_create_custom_headers(self):
        """Test webhook with custom headers"""
        webhook = WebhookCreate(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=[EventType.TASK_COMPLETED],
            custom_headers={
                "X-API-Key": "secret-key",
                "X-Custom-Header": "custom-value"
            }
        )

        assert webhook.custom_headers["X-API-Key"] == "secret-key"
        assert len(webhook.custom_headers) == 2

    def test_webhook_update_partial(self):
        """Test updating webhook with partial data"""
        update = WebhookUpdate(
            name="Updated Name",
            is_active=False
        )

        assert update.name == "Updated Name"
        assert update.is_active is False
        assert update.url is None  # Other fields None

    def test_webhook_update_all_fields(self):
        """Test updating all webhook fields"""
        update = WebhookUpdate(
            name="Updated Webhook",
            url="https://new-url.com/webhook",
            description="Updated description",
            events=[EventType.BUDGET_WARNING],
            project_filter="new-project",
            max_retries=7,
            retry_delay_seconds=180,
            timeout_seconds=45,
            is_active=False
        )

        assert update.name == "Updated Webhook"
        assert update.url == "https://new-url.com/webhook"
        assert update.max_retries == 7
        assert update.is_active is False

    def test_webhook_update_invalid_url(self):
        """Test webhook update fails with invalid URL"""
        with pytest.raises(ValidationError) as exc_info:
            WebhookUpdate(
                url="ftp://invalid-protocol.com"
            )

        assert "URL must start with http:// or https://" in str(exc_info.value)

    def test_webhook_update_empty_events_fails(self):
        """Test webhook update fails with empty events array"""
        with pytest.raises(ValidationError):
            WebhookUpdate(
                events=[]
            )

    def test_webhook_create_multiple_event_types(self):
        """Test webhook with multiple event types"""
        webhook = WebhookCreate(
            name="Multi-Event Webhook",
            url="https://example.com/webhook",
            events=[
                EventType.TASK_STARTED,
                EventType.TASK_COMPLETED,
                EventType.TASK_FAILED,
                EventType.BUDGET_WARNING,
                EventType.BUDGET_CRITICAL
            ]
        )

        assert len(webhook.events) == 5
        assert EventType.TASK_STARTED in webhook.events
        assert EventType.BUDGET_WARNING in webhook.events
