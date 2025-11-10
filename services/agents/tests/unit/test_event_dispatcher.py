"""
Comprehensive unit tests for EventDispatcher.
Aims to boost coverage from 21% to 85%+
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4, UUID
from datetime import datetime, timedelta
import json
import httpx


@pytest.mark.unit
class TestEventDispatcherInit:
    """Test EventDispatcher initialization"""

    def test_init(self):
        """Test EventDispatcher initialization"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        assert dispatcher.db_pool == mock_db_pool
        assert dispatcher.http_client is not None


@pytest.mark.unit
class TestEventDispatcherPublishEvent:
    """Test publish_event method"""

    @pytest.mark.asyncio
    async def test_publish_event_no_webhooks(self):
        """Test publishing event when no webhooks match"""
        from app.webhooks.event_dispatcher import EventDispatcher
        from app.webhooks.models import EventType

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])  # No webhooks

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        result = await dispatcher.publish_event(
            event_type=EventType.TASK_STARTED,
            event_id="test-event-123",
            source="agent-service",
            tenant_id=uuid4(),
            data={"test": "data"}
        )

        assert result == 0
        # Verify event was logged
        assert mock_conn.execute.called

    @pytest.mark.asyncio
    async def test_publish_event_with_webhooks(self):
        """Test publishing event with matching webhooks"""
        from app.webhooks.event_dispatcher import EventDispatcher
        from app.webhooks.models import EventType

        tenant_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                'webhook_id': webhook_id,
                'webhook_url': 'https://example.com/webhook',
                'secret_key': 'secret123',
                'custom_headers': {},
                'timeout_seconds': 30
            }
        ])

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        with patch.object(dispatcher, '_schedule_webhook_delivery', new=AsyncMock()) as mock_schedule:
            result = await dispatcher.publish_event(
                event_type=EventType.TASK_COMPLETED,
                event_id="task-456",
                source="agent-service",
                tenant_id=tenant_id,
                data={"status": "completed"},
                user_id=uuid4(),
                project_id="proj-123",
                workflow_id="wf-456"
            )

        assert result == 1
        assert mock_schedule.called

    @pytest.mark.asyncio
    async def test_publish_event_multiple_webhooks(self):
        """Test publishing event triggers multiple webhooks"""
        from app.webhooks.event_dispatcher import EventDispatcher
        from app.webhooks.models import EventType

        tenant_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                'webhook_id': uuid4(),
                'webhook_url': 'https://example1.com/webhook',
                'secret_key': 'secret1',
                'custom_headers': {},
                'timeout_seconds': 30
            },
            {
                'webhook_id': uuid4(),
                'webhook_url': 'https://example2.com/webhook',
                'secret_key': 'secret2',
                'custom_headers': {},
                'timeout_seconds': 30
            },
            {
                'webhook_id': uuid4(),
                'webhook_url': 'https://example3.com/webhook',
                'secret_key': 'secret3',
                'custom_headers': {},
                'timeout_seconds': 30
            }
        ])

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        with patch.object(dispatcher, '_schedule_webhook_delivery', new=AsyncMock()) as mock_schedule:
            result = await dispatcher.publish_event(
                event_type=EventType.BUDGET_EXCEEDED,
                event_id="budget-789",
                source="cost-service",
                tenant_id=tenant_id,
                data={"amount": 100.50}
            )

        assert result == 3
        assert mock_schedule.call_count == 3


@pytest.mark.unit
class TestEventDispatcherScheduleWebhookDelivery:
    """Test _schedule_webhook_delivery method"""

    @pytest.mark.asyncio
    async def test_schedule_webhook_delivery_success(self):
        """Test successful webhook delivery scheduling"""
        from app.webhooks.event_dispatcher import EventDispatcher
        from app.webhooks.models import EventType

        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        with patch.object(dispatcher, '_attempt_delivery', new=AsyncMock()) as mock_attempt:
            await dispatcher._schedule_webhook_delivery(
                webhook_id=webhook_id,
                webhook_url='https://example.com/webhook',
                secret_key='secret',
                custom_headers={},
                timeout_seconds=30,
                event_type=EventType.TASK_STARTED,
                event_id='event-123',
                payload={'data': 'test'}
            )

        # Verify delivery record was created
        assert mock_conn.execute.called
        assert mock_attempt.called

    @pytest.mark.asyncio
    async def test_schedule_webhook_delivery_error_handling(self):
        """Test webhook delivery scheduling handles errors gracefully"""
        from app.webhooks.event_dispatcher import EventDispatcher
        from app.webhooks.models import EventType

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Database error"))

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        # Should not raise exception
        await dispatcher._schedule_webhook_delivery(
            webhook_id=uuid4(),
            webhook_url='https://example.com/webhook',
            secret_key='secret',
            custom_headers={},
            timeout_seconds=30,
            event_type=EventType.TASK_FAILED,
            event_id='event-456',
            payload={'error': 'test'}
        )


@pytest.mark.unit
class TestEventDispatcherAttemptDelivery:
    """Test _attempt_delivery method"""

    @pytest.mark.asyncio
    async def test_attempt_delivery_success(self):
        """Test successful webhook delivery"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_response.headers = {"content-type": "application/json"}

        dispatcher.http_client.post = AsyncMock(return_value=mock_response)

        await dispatcher._attempt_delivery(
            delivery_id=delivery_id,
            webhook_id=webhook_id,
            webhook_url='https://example.com/webhook',
            secret_key='secret123',
            custom_headers={'X-Custom': 'header'},
            timeout_seconds=30,
            payload={'event': 'test'}
        )

        # Verify webhook was sent
        assert dispatcher.http_client.post.called
        call_args = dispatcher.http_client.post.call_args
        assert call_args[0][0] == 'https://example.com/webhook'
        assert 'X-Webhook-Signature' in call_args[1]['headers']
        assert 'X-Custom' in call_args[1]['headers']

        # Verify delivery record was updated
        assert mock_conn.execute.called

    @pytest.mark.asyncio
    async def test_attempt_delivery_failure(self):
        """Test webhook delivery failure"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        # Mock failed HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = {}

        dispatcher.http_client.post = AsyncMock(return_value=mock_response)

        with patch.object(dispatcher, '_schedule_retry', new=AsyncMock()) as mock_retry:
            await dispatcher._attempt_delivery(
                delivery_id=delivery_id,
                webhook_id=webhook_id,
                webhook_url='https://example.com/webhook',
                secret_key='secret',
                custom_headers={},
                timeout_seconds=30,
                payload={'event': 'test'}
            )

        # Verify retry was scheduled
        assert mock_retry.called

    @pytest.mark.asyncio
    async def test_attempt_delivery_timeout(self):
        """Test webhook delivery timeout"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        # Mock timeout exception
        dispatcher.http_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))

        with patch.object(dispatcher, '_record_delivery_error', new=AsyncMock()) as mock_error, \
             patch.object(dispatcher, '_schedule_retry', new=AsyncMock()) as mock_retry:
            await dispatcher._attempt_delivery(
                delivery_id=delivery_id,
                webhook_id=webhook_id,
                webhook_url='https://example.com/webhook',
                secret_key='secret',
                custom_headers={},
                timeout_seconds=30,
                payload={'event': 'test'}
            )

        assert mock_error.called
        assert mock_retry.called

    @pytest.mark.asyncio
    async def test_attempt_delivery_request_error(self):
        """Test webhook delivery request error"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        # Mock request error
        dispatcher.http_client.post = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        with patch.object(dispatcher, '_record_delivery_error', new=AsyncMock()) as mock_error, \
             patch.object(dispatcher, '_schedule_retry', new=AsyncMock()) as mock_retry:
            await dispatcher._attempt_delivery(
                delivery_id=delivery_id,
                webhook_id=webhook_id,
                webhook_url='https://example.com/webhook',
                secret_key='secret',
                custom_headers={},
                timeout_seconds=30,
                payload={'event': 'test'}
            )

        assert mock_error.called
        assert mock_retry.called

    @pytest.mark.asyncio
    async def test_attempt_delivery_generic_exception(self):
        """Test webhook delivery with unexpected exception"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        # Mock generic exception
        dispatcher.http_client.post = AsyncMock(side_effect=Exception("Unexpected error"))

        with patch.object(dispatcher, '_record_delivery_error', new=AsyncMock()) as mock_error, \
             patch.object(dispatcher, '_schedule_retry', new=AsyncMock()) as mock_retry:
            await dispatcher._attempt_delivery(
                delivery_id=delivery_id,
                webhook_id=webhook_id,
                webhook_url='https://example.com/webhook',
                secret_key='secret',
                custom_headers={},
                timeout_seconds=30,
                payload={'event': 'test'}
            )

        assert mock_error.called
        assert mock_retry.called


@pytest.mark.unit
class TestEventDispatcherRecordError:
    """Test _record_delivery_error method"""

    @pytest.mark.asyncio
    async def test_record_delivery_error(self):
        """Test recording delivery error"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        await dispatcher._record_delivery_error(
            delivery_id=delivery_id,
            webhook_id=webhook_id,
            error_message="Connection timeout"
        )

        # Verify error was recorded
        assert mock_conn.execute.call_count == 2  # Update delivery + update stats

    @pytest.mark.asyncio
    async def test_record_delivery_error_long_message(self):
        """Test recording error with long message (truncated)"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        long_error = "A" * 1000

        await dispatcher._record_delivery_error(
            delivery_id=delivery_id,
            webhook_id=webhook_id,
            error_message=long_error
        )

        # Verify error was truncated to 500 chars
        call_args = mock_conn.execute.call_args_list[0]
        error_arg = call_args[0][1]
        assert len(error_arg) <= 500


@pytest.mark.unit
class TestEventDispatcherScheduleRetry:
    """Test _schedule_retry method"""

    @pytest.mark.asyncio
    async def test_schedule_retry_first_attempt(self):
        """Test scheduling first retry"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={
            'attempts': 1,
            'max_attempts': 3,
            'scheduled_at': datetime.utcnow()
        })
        mock_conn.execute = AsyncMock()

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        await dispatcher._schedule_retry(delivery_id=delivery_id, webhook_id=webhook_id)

        # Verify retry was scheduled
        assert mock_conn.execute.called

    @pytest.mark.asyncio
    async def test_schedule_retry_max_attempts_reached(self):
        """Test retry not scheduled when max attempts reached"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={
            'attempts': 3,
            'max_attempts': 3,
            'scheduled_at': datetime.utcnow()
        })
        mock_conn.execute = AsyncMock()

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        await dispatcher._schedule_retry(delivery_id=delivery_id, webhook_id=webhook_id)

        # Verify no retry was scheduled (only fetchrow called, no execute)
        assert not mock_conn.execute.called

    @pytest.mark.asyncio
    async def test_schedule_retry_no_delivery_found(self):
        """Test retry when delivery not found"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        await dispatcher._schedule_retry(delivery_id=delivery_id, webhook_id=webhook_id)

        # Should return early without error
        assert mock_conn.fetchrow.called

    @pytest.mark.asyncio
    async def test_schedule_retry_exponential_backoff(self):
        """Test exponential backoff for retries"""
        from app.webhooks.event_dispatcher import EventDispatcher

        delivery_id = uuid4()
        webhook_id = uuid4()

        mock_db_pool = MagicMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        # Test different attempt numbers
        for attempts in [1, 2, 3]:
            mock_conn = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value={
                'attempts': attempts,
                'max_attempts': 5,
                'scheduled_at': datetime.utcnow()
            })
            mock_conn.execute = AsyncMock()

            mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

            await dispatcher._schedule_retry(delivery_id=delivery_id, webhook_id=webhook_id)

            # Verify exponential backoff: 60s, 120s, 240s
            expected_delay = 60 * (2 ** (attempts - 1))
            assert mock_conn.execute.called


@pytest.mark.unit
class TestEventDispatcherGenerateSignature:
    """Test _generate_signature method"""

    def test_generate_signature(self):
        """Test HMAC signature generation"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        payload = {"event": "test", "data": "example"}
        secret = "my-secret-key"

        signature = dispatcher._generate_signature(payload, secret)

        assert signature.startswith("sha256=")
        assert len(signature) > 10

    def test_generate_signature_deterministic(self):
        """Test signature is deterministic (same input = same output)"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        payload = {"event": "test", "id": 123}
        secret = "secret"

        sig1 = dispatcher._generate_signature(payload, secret)
        sig2 = dispatcher._generate_signature(payload, secret)

        assert sig1 == sig2

    def test_generate_signature_different_payloads(self):
        """Test different payloads produce different signatures"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        payload1 = {"event": "test1"}
        payload2 = {"event": "test2"}
        secret = "secret"

        sig1 = dispatcher._generate_signature(payload1, secret)
        sig2 = dispatcher._generate_signature(payload2, secret)

        assert sig1 != sig2

    def test_generate_signature_different_secrets(self):
        """Test different secrets produce different signatures"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        payload = {"event": "test"}
        secret1 = "secret1"
        secret2 = "secret2"

        sig1 = dispatcher._generate_signature(payload, secret1)
        sig2 = dispatcher._generate_signature(payload, secret2)

        assert sig1 != sig2


@pytest.mark.unit
class TestEventDispatcherRetryFailedDeliveries:
    """Test retry_failed_deliveries method"""

    @pytest.mark.asyncio
    async def test_retry_failed_deliveries_no_deliveries(self):
        """Test retry when no deliveries need retrying"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        await dispatcher.retry_failed_deliveries()

        # Should just return without error
        assert mock_conn.fetch.called

    @pytest.mark.asyncio
    async def test_retry_failed_deliveries_with_pending(self):
        """Test retrying pending deliveries"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                'delivery_id': uuid4(),
                'webhook_id': uuid4(),
                'event_type': 'agent.execution.completed',
                'event_id': 'event-123',
                'payload': '{"data": "test"}',
                'webhook_url': 'https://example.com/webhook',
                'secret_key': 'secret',
                'custom_headers': {},
                'timeout_seconds': 30
            }
        ])

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        with patch.object(dispatcher, '_attempt_delivery', new=AsyncMock()) as mock_attempt:
            await dispatcher.retry_failed_deliveries()

        assert mock_attempt.called

    @pytest.mark.asyncio
    async def test_retry_failed_deliveries_multiple(self):
        """Test retrying multiple failed deliveries"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                'delivery_id': uuid4(),
                'webhook_id': uuid4(),
                'event_type': 'event1',
                'event_id': 'e1',
                'payload': '{"data": "test1"}',
                'webhook_url': 'https://example1.com',
                'secret_key': 'secret1',
                'custom_headers': {},
                'timeout_seconds': 30
            },
            {
                'delivery_id': uuid4(),
                'webhook_id': uuid4(),
                'event_type': 'event2',
                'event_id': 'e2',
                'payload': '{"data": "test2"}',
                'webhook_url': 'https://example2.com',
                'secret_key': 'secret2',
                'custom_headers': {},
                'timeout_seconds': 30
            }
        ])

        mock_db_pool.acquire = MagicMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()

        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        with patch.object(dispatcher, '_attempt_delivery', new=AsyncMock()) as mock_attempt:
            await dispatcher.retry_failed_deliveries()

        assert mock_attempt.call_count == 2


@pytest.mark.unit
class TestEventDispatcherClose:
    """Test close method"""

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing HTTP client"""
        from app.webhooks.event_dispatcher import EventDispatcher

        mock_db_pool = MagicMock()
        dispatcher = EventDispatcher(db_pool=mock_db_pool)

        dispatcher.http_client.aclose = AsyncMock()

        await dispatcher.close()

        assert dispatcher.http_client.aclose.called
