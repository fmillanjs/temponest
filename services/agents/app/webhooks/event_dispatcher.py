"""
Event Dispatcher for webhook system.
Publishes events and triggers webhooks asynchronously.
"""

import asyncio
import hmac
import hashlib
import json
import httpx
import asyncpg
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

from .models import EventType, EventPayload, DeliveryStatus

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Dispatches events and triggers webhooks"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.http_client = httpx.AsyncClient()

    async def publish_event(
        self,
        event_type: EventType,
        event_id: str,
        source: str,
        tenant_id: UUID,
        data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> int:
        """
        Publish an event and trigger all matching webhooks.

        Args:
            event_type: Type of event
            event_id: Unique identifier for the event (task_id, budget_id, etc.)
            source: Source service that generated the event
            tenant_id: Tenant ID
            data: Event data payload
            user_id: Optional user ID
            project_id: Optional project ID
            workflow_id: Optional workflow ID

        Returns:
            Number of webhooks triggered
        """
        logger.info(f"Publishing event: {event_type} for {event_id}")

        # Create event payload
        payload = {
            "event_type": event_type.value,
            "event_id": event_id,
            "source": source,
            "tenant_id": str(tenant_id),
            "user_id": str(user_id) if user_id else None,
            "project_id": project_id,
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        # Log event to database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO event_log (
                    tenant_id, user_id, event_type, event_id, source,
                    payload, project_id, workflow_id, webhook_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 0)
                """,
                tenant_id, user_id, event_type.value, event_id, source,
                json.dumps(payload), project_id, workflow_id
            )

            # Get all webhooks that should receive this event
            webhooks = await conn.fetch(
                """
                SELECT * FROM get_webhooks_for_event($1, $2, $3, $4)
                """,
                tenant_id, event_type.value, project_id, workflow_id
            )

        if not webhooks:
            logger.info(f"No webhooks found for event {event_type}")
            return 0

        # Trigger webhooks asynchronously
        webhook_count = len(webhooks)
        logger.info(f"Triggering {webhook_count} webhooks for event {event_type}")

        # Schedule webhook deliveries
        tasks = []
        for webhook in webhooks:
            task = self._schedule_webhook_delivery(
                webhook_id=webhook['webhook_id'],
                webhook_url=webhook['webhook_url'],
                secret_key=webhook['secret_key'],
                custom_headers=webhook['custom_headers'],
                timeout_seconds=webhook['timeout_seconds'],
                event_type=event_type,
                event_id=event_id,
                payload=payload
            )
            tasks.append(task)

        # Execute all webhook deliveries concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

        # Update event log with webhook count
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE event_log
                SET webhook_count = $1
                WHERE event_id = $2 AND tenant_id = $3
                """,
                webhook_count, event_id, tenant_id
            )

        return webhook_count

    async def _schedule_webhook_delivery(
        self,
        webhook_id: UUID,
        webhook_url: str,
        secret_key: str,
        custom_headers: Dict[str, str],
        timeout_seconds: int,
        event_type: EventType,
        event_id: str,
        payload: Dict[str, Any]
    ):
        """Schedule a webhook delivery (creates delivery record and attempts delivery)"""

        delivery_id = uuid4()

        try:
            # Create delivery record
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO webhook_deliveries (
                        id, webhook_id, event_type, event_id, payload,
                        status, attempts, max_attempts, scheduled_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, 0, 3, $7)
                    """,
                    delivery_id, webhook_id, event_type.value, event_id,
                    json.dumps(payload), DeliveryStatus.PENDING.value,
                    datetime.utcnow()
                )

            # Attempt delivery
            await self._attempt_delivery(
                delivery_id=delivery_id,
                webhook_id=webhook_id,
                webhook_url=webhook_url,
                secret_key=secret_key,
                custom_headers=custom_headers,
                timeout_seconds=timeout_seconds,
                payload=payload
            )

        except Exception as e:
            logger.error(f"Error scheduling webhook delivery: {e}")

    async def _attempt_delivery(
        self,
        delivery_id: UUID,
        webhook_id: UUID,
        webhook_url: str,
        secret_key: str,
        custom_headers: Dict[str, str],
        timeout_seconds: int,
        payload: Dict[str, Any]
    ):
        """Attempt to deliver a webhook"""

        try:
            # Generate HMAC signature
            signature = self._generate_signature(payload, secret_key)

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-ID": str(delivery_id),
                "User-Agent": "Agentic-Platform-Webhook/1.0",
                **custom_headers
            }

            # Send webhook
            logger.info(f"Sending webhook to {webhook_url}")
            response = await self.http_client.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=timeout_seconds
            )

            success = 200 <= response.status_code < 300

            # Update delivery record
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE webhook_deliveries
                    SET
                        status = $1,
                        attempts = attempts + 1,
                        http_status_code = $2,
                        response_body = $3,
                        response_headers = $4,
                        delivered_at = CASE WHEN $5 THEN $6 ELSE NULL END,
                        updated_at = $6
                    WHERE id = $7
                    """,
                    DeliveryStatus.DELIVERED.value if success else DeliveryStatus.FAILED.value,
                    response.status_code,
                    response.text[:1000],  # Limit response body size
                    json.dumps(dict(response.headers)),
                    success,
                    datetime.utcnow(),
                    delivery_id
                )

                # Update webhook stats
                await conn.execute(
                    "SELECT increment_webhook_stats($1, $2)",
                    webhook_id, success
                )

            if success:
                logger.info(f"Webhook delivered successfully to {webhook_url}")
            else:
                logger.warning(f"Webhook delivery failed: {response.status_code}")
                # Schedule retry if needed
                await self._schedule_retry(delivery_id, webhook_id)

        except httpx.TimeoutException as e:
            logger.error(f"Webhook timeout: {webhook_url}")
            await self._record_delivery_error(delivery_id, webhook_id, "Request timeout")
            await self._schedule_retry(delivery_id, webhook_id)

        except httpx.RequestError as e:
            logger.error(f"Webhook request error: {e}")
            await self._record_delivery_error(delivery_id, webhook_id, str(e))
            await self._schedule_retry(delivery_id, webhook_id)

        except Exception as e:
            logger.error(f"Unexpected webhook error: {e}")
            await self._record_delivery_error(delivery_id, webhook_id, str(e))
            await self._schedule_retry(delivery_id, webhook_id)

    async def _record_delivery_error(
        self,
        delivery_id: UUID,
        webhook_id: UUID,
        error_message: str
    ):
        """Record delivery error in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE webhook_deliveries
                SET
                    status = $1,
                    attempts = attempts + 1,
                    error_message = $2,
                    updated_at = $3
                WHERE id = $4
                """,
                DeliveryStatus.FAILED.value,
                error_message[:500],
                datetime.utcnow(),
                delivery_id
            )

            # Update webhook stats (failure)
            await conn.execute(
                "SELECT increment_webhook_stats($1, false)",
                webhook_id
            )

    async def _schedule_retry(
        self,
        delivery_id: UUID,
        webhook_id: UUID
    ):
        """Schedule a retry for failed delivery"""

        async with self.db_pool.acquire() as conn:
            # Get current delivery info
            delivery = await conn.fetchrow(
                """
                SELECT attempts, max_attempts, scheduled_at
                FROM webhook_deliveries
                WHERE id = $1
                """,
                delivery_id
            )

            if not delivery:
                return

            attempts = delivery['attempts']
            max_attempts = delivery['max_attempts']

            if attempts < max_attempts:
                # Calculate exponential backoff: 60s, 120s, 240s, ...
                retry_delay = 60 * (2 ** (attempts - 1))
                next_retry = datetime.utcnow() + timedelta(seconds=retry_delay)

                await conn.execute(
                    """
                    UPDATE webhook_deliveries
                    SET
                        status = $1,
                        next_retry_at = $2,
                        updated_at = $3
                    WHERE id = $4
                    """,
                    DeliveryStatus.RETRYING.value,
                    next_retry,
                    datetime.utcnow(),
                    delivery_id
                )

                logger.info(f"Scheduled retry for delivery {delivery_id} in {retry_delay}s")
            else:
                logger.warning(f"Delivery {delivery_id} exceeded max retries")

    def _generate_signature(self, payload: Dict[str, Any], secret_key: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload"""
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def retry_failed_deliveries(self):
        """
        Background task to retry failed webhook deliveries.
        Should be run periodically (e.g., every minute).
        """
        logger.info("Checking for webhook deliveries to retry")

        async with self.db_pool.acquire() as conn:
            # Get deliveries ready for retry
            deliveries = await conn.fetch(
                """
                SELECT
                    wd.id as delivery_id,
                    wd.webhook_id,
                    wd.event_type,
                    wd.event_id,
                    wd.payload,
                    w.url as webhook_url,
                    w.secret_key,
                    w.custom_headers,
                    w.timeout_seconds
                FROM webhook_deliveries wd
                JOIN webhooks w ON wd.webhook_id = w.id
                WHERE wd.status = 'retrying'
                    AND wd.next_retry_at <= $1
                    AND w.is_active = true
                LIMIT 100
                """,
                datetime.utcnow()
            )

        if not deliveries:
            return

        logger.info(f"Retrying {len(deliveries)} webhook deliveries")

        # Retry each delivery
        tasks = []
        for delivery in deliveries:
            task = self._attempt_delivery(
                delivery_id=delivery['delivery_id'],
                webhook_id=delivery['webhook_id'],
                webhook_url=delivery['webhook_url'],
                secret_key=delivery['secret_key'],
                custom_headers=delivery['custom_headers'],
                timeout_seconds=delivery['timeout_seconds'],
                payload=json.loads(delivery['payload'])
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
