"""
Unit tests for Temporal activities.
Tests all activity functions with various scenarios.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from datetime import datetime

from activities import (
    invoke_overseer,
    invoke_developer,
    request_approval,
    check_approval_status,
    send_telegram_notification,
    execute_deployment,
    validate_output
)


class TestInvokeOverseer:
    """Test invoke_overseer activity"""

    @pytest.mark.asyncio
    @patch('activities.activity.heartbeat')
    @patch('activities.httpx.AsyncClient')
    async def test_invoke_overseer_success(self, mock_httpx_class, mock_heartbeat, mock_overseer_response, mock_httpx_client):
        """Test successful Overseer invocation"""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_overseer_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {
            "task": "Create a TODO app",
            "context": {},
            "idempotency_key": "test-key"
        }

        result = await invoke_overseer(request)

        assert "plan" in result
        assert len(result["plan"]) == 3
        assert result["citations"] is not None
        mock_httpx_client.post.assert_called_once()
        mock_heartbeat.assert_called_once()

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_invoke_overseer_http_error(self, mock_httpx_class, mock_httpx_client):
        """Test Overseer invocation with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("API Error")
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {"task": "test", "context": {}, "idempotency_key": "key"}

        with pytest.raises(httpx.HTTPError):
            await invoke_overseer(request)

    @pytest.mark.asyncio
    @patch('activities.activity.heartbeat')
    @patch('activities.httpx.AsyncClient')
    async def test_invoke_overseer_correct_url(self, mock_httpx_class, mock_heartbeat, mock_overseer_response, mock_httpx_client):
        """Test that Overseer is called with correct URL"""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_overseer_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {"task": "test", "context": {}, "idempotency_key": "key"}
        await invoke_overseer(request)

        call_args = mock_httpx_client.post.call_args
        assert "/overseer/run" in call_args[0][0]
        assert call_args[1]["json"] == request


class TestInvokeDeveloper:
    """Test invoke_developer activity"""

    @pytest.mark.asyncio
    @patch('activities.activity.heartbeat')
    @patch('activities.httpx.AsyncClient')
    async def test_invoke_developer_success(self, mock_httpx_class, mock_heartbeat, mock_developer_response, mock_httpx_client):
        """Test successful Developer invocation"""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_developer_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {
            "task": "Implement REST API",
            "context": {},
            "idempotency_key": "dev-key"
        }

        result = await invoke_developer(request)

        assert "code" in result
        assert "implementation" in result["code"]
        assert "tests" in result["code"]
        assert len(result["citations"]) >= 2
        mock_heartbeat.assert_called_once()

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_invoke_developer_http_error(self, mock_httpx_class, mock_httpx_client):
        """Test Developer invocation with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Service unavailable")
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {"task": "test", "context": {}, "idempotency_key": "key"}

        with pytest.raises(httpx.HTTPError):
            await invoke_developer(request)

    @pytest.mark.asyncio
    @patch('activities.activity.heartbeat')
    @patch('activities.httpx.AsyncClient')
    async def test_invoke_developer_correct_url(self, mock_httpx_class, mock_heartbeat, mock_developer_response, mock_httpx_client):
        """Test that Developer is called with correct URL"""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_developer_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {"task": "test", "context": {}, "idempotency_key": "key"}
        await invoke_developer(request)

        call_args = mock_httpx_client.post.call_args
        assert "/developer/run" in call_args[0][0]


class TestRequestApproval:
    """Test request_approval activity"""

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_request_approval_success(self, mock_httpx_class, mock_approval_response, mock_httpx_client):
        """Test successful approval request creation"""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_approval_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {
            "workflow_id": "wf-123",
            "run_id": "run-456",
            "task_description": "Deploy to prod",
            "risk_level": "high",
            "context": {}
        }

        approval_id = await request_approval(request)

        assert approval_id == "test-approval-123"
        mock_httpx_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_request_approval_http_error(self, mock_httpx_class, mock_httpx_client):
        """Test approval request with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Database error")
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {
            "workflow_id": "wf-123",
            "run_id": "run-456",
            "task_description": "test",
            "risk_level": "low",
            "context": {}
        }

        with pytest.raises(httpx.HTTPError):
            await request_approval(request)

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_request_approval_correct_payload(self, mock_httpx_class, mock_approval_response, mock_httpx_client):
        """Test that approval request sends correct payload"""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_approval_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        request = {
            "workflow_id": "wf-123",
            "run_id": "run-456",
            "task_description": "Test task",
            "risk_level": "medium",
            "context": {"key": "value"}
        }

        await request_approval(request)

        call_args = mock_httpx_client.post.call_args
        assert "/api/approvals" in call_args[0][0]
        assert call_args[1]["json"] == request


class TestCheckApprovalStatus:
    """Test check_approval_status activity"""

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_check_approval_status_success(self, mock_httpx_class, mock_httpx_client):
        """Test successful approval status check"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "approved",
            "approved_by": "user@example.com",
            "approved_at": "2025-11-10T12:00:00"
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        result = await check_approval_status("approval-123")

        assert result["status"] == "approved"
        assert result["approved_by"] == "user@example.com"
        mock_httpx_client.get.assert_called_once()

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_check_approval_status_pending(self, mock_httpx_class, mock_httpx_client):
        """Test checking pending approval status"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "pending"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        result = await check_approval_status("approval-456")

        assert result["status"] == "pending"

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_check_approval_status_http_error(self, mock_httpx_class, mock_httpx_client):
        """Test approval status check with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Not found")
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        with pytest.raises(httpx.HTTPError):
            await check_approval_status("nonexistent")


class TestSendTelegramNotification:
    """Test send_telegram_notification activity"""

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_send_telegram_notification_success(self, mock_httpx_class, mock_httpx_client):
        """Test successful Telegram notification"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        notification = {
            "approval_id": "approval-123",
            "task": "Deploy to production",
            "risk_level": "high"
        }

        result = await send_telegram_notification(notification)

        assert result is True
        mock_httpx_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_send_telegram_notification_failure(self, mock_httpx_class, mock_httpx_client):
        """Test Telegram notification failure (should not raise)"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Webhook failed")
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        notification = {
            "approval_id": "approval-123",
            "task": "Test task",
            "risk_level": "low"
        }

        result = await send_telegram_notification(notification)

        # Should return False but not raise exception
        assert result is False

    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_send_telegram_notification_correct_payload(self, mock_httpx_class, mock_httpx_client):
        """Test that notification sends correct payload"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_class.return_value = mock_httpx_client

        notification = {
            "approval_id": "approval-789",
            "task": "Update database schema",
            "risk_level": "medium"
        }

        await send_telegram_notification(notification)

        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["type"] == "approval_request"
        assert payload["approval_id"] == "approval-789"
        assert payload["task"] == "Update database schema"
        assert payload["risk_level"] == "medium"
        assert "timestamp" in payload


class TestExecuteDeployment:
    """Test execute_deployment activity"""

    @pytest.mark.asyncio
    async def test_execute_deployment_success(self):
        """Test successful deployment execution"""
        deployment = {
            "tasks": [
                {"task": "Task 1", "result": {}},
                {"task": "Task 2", "result": {}}
            ],
            "idempotency_key": "deploy-key-123"
        }

        result = await execute_deployment(deployment)

        assert result["status"] == "success"
        assert result["tasks_deployed"] == 2
        assert result["idempotency_key"] == "deploy-key-123"
        assert "deployment_id" in result
        assert "deployed_at" in result

    @pytest.mark.asyncio
    async def test_execute_deployment_empty_tasks(self):
        """Test deployment with no tasks"""
        deployment = {
            "tasks": [],
            "idempotency_key": "empty-deploy"
        }

        result = await execute_deployment(deployment)

        assert result["status"] == "success"
        assert result["tasks_deployed"] == 0

    @pytest.mark.asyncio
    async def test_execute_deployment_idempotency(self):
        """Test deployment idempotency key is preserved"""
        deployment = {
            "tasks": [{"task": "test"}],
            "idempotency_key": "unique-key-789"
        }

        result = await execute_deployment(deployment)

        assert result["idempotency_key"] == "unique-key-789"


class TestValidateOutput:
    """Test validate_output activity"""

    @pytest.mark.asyncio
    async def test_validate_output_success(self):
        """Test validation of valid output"""
        output = {
            "code": {
                "implementation": "def main():\n    print('Hello, World!')\n" * 10,
                "tests": "def test_main():\n    assert True\n" * 5
            },
            "citations": [
                {"source": "doc1.md"},
                {"source": "doc2.md"},
                {"source": "doc3.md"}
            ]
        }

        result = await validate_output(output)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_output_insufficient_citations(self):
        """Test validation fails with insufficient citations"""
        output = {
            "code": {
                "implementation": "def main(): pass\n" * 10,
                "tests": "def test(): pass\n" * 5
            },
            "citations": [{"source": "doc1.md"}]  # Only 1 citation
        }

        result = await validate_output(output)

        assert result["valid"] is False
        assert any("citations" in err.lower() for err in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_output_missing_implementation(self):
        """Test validation fails with missing implementation"""
        output = {
            "code": {
                "implementation": "",  # Empty
                "tests": "def test(): pass\n" * 5
            },
            "citations": [{"source": "doc1.md"}, {"source": "doc2.md"}]
        }

        result = await validate_output(output)

        assert result["valid"] is False
        assert any("implementation" in err.lower() for err in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_output_missing_tests(self):
        """Test validation fails with missing tests"""
        output = {
            "code": {
                "implementation": "def main(): pass\n" * 10,
                "tests": "# test"  # Too short
            },
            "citations": [{"source": "doc1.md"}, {"source": "doc2.md"}]
        }

        result = await validate_output(output)

        assert result["valid"] is False
        assert any("tests" in err.lower() for err in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_output_short_implementation(self):
        """Test validation fails with too short implementation"""
        output = {
            "code": {
                "implementation": "pass",  # < 50 chars
                "tests": "def test(): pass\n" * 5
            },
            "citations": [{"source": "doc1.md"}, {"source": "doc2.md"}]
        }

        result = await validate_output(output)

        assert result["valid"] is False
        assert any("implementation" in err.lower() for err in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_output_multiple_errors(self):
        """Test validation captures multiple errors"""
        output = {
            "code": {
                "implementation": "",
                "tests": ""
            },
            "citations": []
        }

        result = await validate_output(output)

        assert result["valid"] is False
        assert len(result["errors"]) >= 3  # citations, implementation, tests
