"""
Webhook Manager for CRUD operations.
"""

import asyncpg
import secrets
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from .models import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    EventType,
    WebhookDeliveryResponse,
    WebhookHealthResponse
)


class WebhookManager:
    """Manages webhook CRUD operations"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def create_webhook(
        self,
        webhook: WebhookCreate,
        tenant_id: UUID,
        user_id: UUID
    ) -> WebhookResponse:
        """Create a new webhook"""

        # Generate secret key for HMAC signatures
        secret_key = secrets.token_hex(32)

        async with self.db_pool.acquire() as conn:
            # Convert events enum to strings for PostgreSQL
            events_array = [e.value for e in webhook.events]

            row = await conn.fetchrow(
                """
                INSERT INTO webhooks (
                    tenant_id, user_id, name, url, description,
                    events, secret_key, project_filter, workflow_filter,
                    max_retries, retry_delay_seconds, timeout_seconds,
                    custom_headers, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING *
                """,
                tenant_id, user_id, webhook.name, webhook.url, webhook.description,
                events_array, secret_key, webhook.project_filter, webhook.workflow_filter,
                webhook.max_retries, webhook.retry_delay_seconds, webhook.timeout_seconds,
                webhook.custom_headers, webhook.is_active
            )

        return self._row_to_webhook_response(row)

    async def get_webhook(
        self,
        webhook_id: UUID,
        tenant_id: UUID
    ) -> Optional[WebhookResponse]:
        """Get webhook by ID"""

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM webhooks
                WHERE id = $1 AND tenant_id = $2
                """,
                webhook_id, tenant_id
            )

        if not row:
            return None

        return self._row_to_webhook_response(row)

    async def list_webhooks(
        self,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 50,
        is_active: Optional[bool] = None
    ) -> tuple[List[WebhookResponse], int]:
        """List webhooks for a tenant with pagination"""

        offset = (page - 1) * page_size

        async with self.db_pool.acquire() as conn:
            # Build query based on filters
            where_clauses = ["tenant_id = $1"]
            params = [tenant_id]
            param_count = 1

            if is_active is not None:
                param_count += 1
                where_clauses.append(f"is_active = ${param_count}")
                params.append(is_active)

            where_clause = " AND ".join(where_clauses)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM webhooks WHERE {where_clause}"
            total = await conn.fetchval(count_query, *params)

            # Get paginated results
            query = f"""
                SELECT * FROM webhooks
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([page_size, offset])

            rows = await conn.fetch(query, *params)

        webhooks = [self._row_to_webhook_response(row) for row in rows]
        return webhooks, total

    async def update_webhook(
        self,
        webhook_id: UUID,
        tenant_id: UUID,
        updates: WebhookUpdate
    ) -> Optional[WebhookResponse]:
        """Update a webhook"""

        # Build dynamic update query
        update_fields = []
        params = [webhook_id, tenant_id]
        param_count = 2

        update_data = updates.dict(exclude_unset=True)

        for field, value in update_data.items():
            param_count += 1
            if field == 'events':
                # Convert event enums to strings
                update_fields.append(f"{field} = ${param_count}")
                params.append([e.value for e in value])
            else:
                update_fields.append(f"{field} = ${param_count}")
                params.append(value)

        if not update_fields:
            # No updates provided, just return current webhook
            return await self.get_webhook(webhook_id, tenant_id)

        # Add updated_at
        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())

        query = f"""
            UPDATE webhooks
            SET {', '.join(update_fields)}
            WHERE id = $1 AND tenant_id = $2
            RETURNING *
        """

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if not row:
            return None

        return self._row_to_webhook_response(row)

    async def delete_webhook(
        self,
        webhook_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """Delete a webhook"""

        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM webhooks
                WHERE id = $1 AND tenant_id = $2
                """,
                webhook_id, tenant_id
            )

        return result == "DELETE 1"

    async def get_webhook_deliveries(
        self,
        webhook_id: UUID,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[WebhookDeliveryResponse], int]:
        """Get delivery history for a webhook"""

        offset = (page - 1) * page_size

        async with self.db_pool.acquire() as conn:
            # Verify webhook belongs to tenant
            webhook_exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM webhooks
                    WHERE id = $1 AND tenant_id = $2
                )
                """,
                webhook_id, tenant_id
            )

            if not webhook_exists:
                return [], 0

            # Get total count
            total = await conn.fetchval(
                """
                SELECT COUNT(*) FROM webhook_deliveries
                WHERE webhook_id = $1
                """,
                webhook_id
            )

            # Get paginated deliveries
            rows = await conn.fetch(
                """
                SELECT * FROM webhook_deliveries
                WHERE webhook_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                webhook_id, page_size, offset
            )

        deliveries = [self._row_to_delivery_response(row) for row in rows]
        return deliveries, total

    async def get_webhook_health(
        self,
        tenant_id: UUID
    ) -> List[WebhookHealthResponse]:
        """Get health stats for all webhooks"""

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM webhook_health
                WHERE tenant_id = $1
                ORDER BY name
                """,
                tenant_id
            )

        return [self._row_to_health_response(row) for row in rows]

    async def regenerate_secret(
        self,
        webhook_id: UUID,
        tenant_id: UUID
    ) -> Optional[str]:
        """Regenerate webhook secret key"""

        new_secret = secrets.token_hex(32)

        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                UPDATE webhooks
                SET secret_key = $1, updated_at = $2
                WHERE id = $3 AND tenant_id = $4
                RETURNING secret_key
                """,
                new_secret, datetime.utcnow(), webhook_id, tenant_id
            )

        return result

    def _row_to_webhook_response(self, row: asyncpg.Record) -> WebhookResponse:
        """Convert database row to WebhookResponse"""
        return WebhookResponse(
            id=row['id'],
            tenant_id=row['tenant_id'],
            user_id=row['user_id'],
            name=row['name'],
            url=row['url'],
            description=row['description'],
            events=[EventType(e) for e in row['events']],
            project_filter=row['project_filter'],
            workflow_filter=row['workflow_filter'],
            max_retries=row['max_retries'],
            retry_delay_seconds=row['retry_delay_seconds'],
            timeout_seconds=row['timeout_seconds'],
            custom_headers=row['custom_headers'] or {},
            is_active=row['is_active'],
            is_verified=row['is_verified'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_triggered_at=row['last_triggered_at'],
            total_deliveries=row['total_deliveries'],
            successful_deliveries=row['successful_deliveries'],
            failed_deliveries=row['failed_deliveries']
        )

    def _row_to_delivery_response(self, row: asyncpg.Record) -> WebhookDeliveryResponse:
        """Convert database row to WebhookDeliveryResponse"""
        return WebhookDeliveryResponse(
            id=row['id'],
            webhook_id=row['webhook_id'],
            event_type=EventType(row['event_type']),
            event_id=row['event_id'],
            status=row['status'],
            attempts=row['attempts'],
            max_attempts=row['max_attempts'],
            scheduled_at=row['scheduled_at'],
            next_retry_at=row['next_retry_at'],
            delivered_at=row['delivered_at'],
            http_status_code=row['http_status_code'],
            error_message=row['error_message'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_health_response(self, row: asyncpg.Record) -> WebhookHealthResponse:
        """Convert database row to WebhookHealthResponse"""
        return WebhookHealthResponse(
            id=row['id'],
            tenant_id=row['tenant_id'],
            name=row['name'],
            url=row['url'],
            is_active=row['is_active'],
            total_deliveries=row['total_deliveries'],
            successful_deliveries=row['successful_deliveries'],
            failed_deliveries=row['failed_deliveries'],
            success_rate_pct=float(row['success_rate_pct']),
            last_triggered_at=row['last_triggered_at'],
            pending_count=row['pending_count'],
            retrying_count=row['retrying_count'],
            recent_failed_count=row['recent_failed_count']
        )
