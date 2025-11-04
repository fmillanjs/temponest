"""
Temponest SDK - Webhook Management Client
"""
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel
from .client import BaseClient, AsyncBaseClient


# Webhook Models
class Webhook(BaseModel):
    """Webhook configuration"""
    id: str
    tenant_id: str
    name: str
    url: str
    events: List[str]
    is_active: bool = True
    secret: Optional[str] = None
    headers: Dict[str, str] = {}
    retry_config: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class WebhookDelivery(BaseModel):
    """Webhook delivery attempt"""
    id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    status: Literal["pending", "success", "failed", "retrying"]
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    attempt_count: int = 0
    error: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None


class WebhooksClient:
    """Client for webhook management"""

    def __init__(self, client: BaseClient):
        self.client = client

    def create(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
    ) -> Webhook:
        """
        Create a new webhook

        Args:
            name: Webhook name
            url: Webhook URL
            events: List of events to subscribe to
            secret: Optional secret for HMAC signing
            headers: Optional custom headers
            max_retries: Maximum retry attempts
            retry_delay_seconds: Delay between retries

        Returns:
            Created webhook

        Available events:
            - agent.execution.started
            - agent.execution.completed
            - agent.execution.failed
            - schedule.triggered
            - schedule.completed
            - budget.alert
            - cost.threshold.exceeded

        Example:
            ```python
            webhook = client.webhooks.create(
                name="Slack Notifications",
                url="https://hooks.slack.com/services/...",
                events=["agent.execution.completed", "budget.alert"],
                secret="my-secret-key"
            )
            ```
        """
        payload = {
            "name": name,
            "url": url,
            "events": events,
            "secret": secret,
            "headers": headers or {},
            "retry_config": {
                "max_retries": max_retries,
                "retry_delay_seconds": retry_delay_seconds,
            }
        }

        response = self.client.post("/webhooks/", json=payload)
        return Webhook(**response)

    def get(self, webhook_id: str) -> Webhook:
        """
        Get a webhook by ID

        Args:
            webhook_id: Webhook ID

        Returns:
            Webhook object
        """
        response = self.client.get(f"/webhooks/{webhook_id}")
        return Webhook(**response)

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Webhook]:
        """
        List webhooks

        Args:
            skip: Number to skip
            limit: Maximum to return
            is_active: Filter by active status

        Returns:
            List of webhooks
        """
        params = {"skip": skip, "limit": limit}
        if is_active is not None:
            params["is_active"] = is_active

        response = self.client.get("/webhooks/", params=params)
        return [Webhook(**webhook) for webhook in response]

    def update(
        self,
        webhook_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Webhook:
        """
        Update a webhook

        Args:
            webhook_id: Webhook ID
            name: New name
            url: New URL
            events: New events list
            is_active: New active status
            headers: New headers

        Returns:
            Updated webhook
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if url is not None:
            update_data["url"] = url
        if events is not None:
            update_data["events"] = events
        if is_active is not None:
            update_data["is_active"] = is_active
        if headers is not None:
            update_data["headers"] = headers

        response = self.client.patch(f"/webhooks/{webhook_id}", json=update_data)
        return Webhook(**response)

    def delete(self, webhook_id: str) -> None:
        """
        Delete a webhook

        Args:
            webhook_id: Webhook ID
        """
        self.client.delete(f"/webhooks/{webhook_id}")

    def activate(self, webhook_id: str) -> Webhook:
        """
        Activate a webhook

        Args:
            webhook_id: Webhook ID

        Returns:
            Updated webhook
        """
        return self.update(webhook_id, is_active=True)

    def deactivate(self, webhook_id: str) -> Webhook:
        """
        Deactivate a webhook

        Args:
            webhook_id: Webhook ID

        Returns:
            Updated webhook
        """
        return self.update(webhook_id, is_active=False)

    def test(self, webhook_id: str) -> WebhookDelivery:
        """
        Send a test webhook

        Args:
            webhook_id: Webhook ID

        Returns:
            Webhook delivery result
        """
        response = self.client.post(f"/webhooks/{webhook_id}/test")
        return WebhookDelivery(**response)

    def get_deliveries(
        self,
        webhook_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[WebhookDelivery]:
        """
        Get webhook delivery history

        Args:
            webhook_id: Webhook ID
            skip: Number to skip
            limit: Maximum to return
            status: Filter by status

        Returns:
            List of webhook deliveries
        """
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status

        response = self.client.get(
            f"/webhooks/{webhook_id}/deliveries",
            params=params
        )
        return [WebhookDelivery(**delivery) for delivery in response]

    def get_delivery(self, delivery_id: str) -> WebhookDelivery:
        """
        Get a specific webhook delivery

        Args:
            delivery_id: Delivery ID

        Returns:
            Webhook delivery
        """
        response = self.client.get(f"/webhooks/deliveries/{delivery_id}")
        return WebhookDelivery(**response)

    def retry_delivery(self, delivery_id: str) -> WebhookDelivery:
        """
        Retry a failed webhook delivery

        Args:
            delivery_id: Delivery ID

        Returns:
            Updated webhook delivery
        """
        response = self.client.post(f"/webhooks/deliveries/{delivery_id}/retry")
        return WebhookDelivery(**response)

    def get_events(self) -> List[str]:
        """
        Get list of available webhook events

        Returns:
            List of event names
        """
        response = self.client.get("/webhooks/events")
        return response


class AsyncWebhooksClient:
    """Async client for webhook management"""

    def __init__(self, client: AsyncBaseClient):
        self.client = client

    async def create(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
    ) -> Webhook:
        """Create a new webhook (async)"""
        payload = {
            "name": name,
            "url": url,
            "events": events,
            "secret": secret,
            "headers": headers or {},
            "retry_config": {
                "max_retries": max_retries,
                "retry_delay_seconds": retry_delay_seconds,
            }
        }

        response = await self.client.post("/webhooks/", json=payload)
        return Webhook(**response)

    async def get(self, webhook_id: str) -> Webhook:
        """Get a webhook by ID (async)"""
        response = await self.client.get(f"/webhooks/{webhook_id}")
        return Webhook(**response)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Webhook]:
        """List webhooks (async)"""
        params = {"skip": skip, "limit": limit}
        if is_active is not None:
            params["is_active"] = is_active

        response = await self.client.get("/webhooks/", params=params)
        return [Webhook(**webhook) for webhook in response]

    async def update(
        self,
        webhook_id: str,
        **kwargs
    ) -> Webhook:
        """Update a webhook (async)"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        response = await self.client.patch(f"/webhooks/{webhook_id}", json=update_data)
        return Webhook(**response)

    async def delete(self, webhook_id: str) -> None:
        """Delete a webhook (async)"""
        await self.client.delete(f"/webhooks/{webhook_id}")

    async def activate(self, webhook_id: str) -> Webhook:
        """Activate a webhook (async)"""
        return await self.update(webhook_id, is_active=True)

    async def deactivate(self, webhook_id: str) -> Webhook:
        """Deactivate a webhook (async)"""
        return await self.update(webhook_id, is_active=False)

    async def test(self, webhook_id: str) -> WebhookDelivery:
        """Send a test webhook (async)"""
        response = await self.client.post(f"/webhooks/{webhook_id}/test")
        return WebhookDelivery(**response)

    async def get_deliveries(
        self,
        webhook_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[WebhookDelivery]:
        """Get webhook delivery history (async)"""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status

        response = await self.client.get(
            f"/webhooks/{webhook_id}/deliveries",
            params=params
        )
        return [WebhookDelivery(**delivery) for delivery in response]

    async def retry_delivery(self, delivery_id: str) -> WebhookDelivery:
        """Retry a failed webhook delivery (async)"""
        response = await self.client.post(f"/webhooks/deliveries/{delivery_id}/retry")
        return WebhookDelivery(**response)

    async def get_events(self) -> List[str]:
        """Get list of available webhook events (async)"""
        response = await self.client.get("/webhooks/events")
        return response
