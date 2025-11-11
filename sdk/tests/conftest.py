"""
Pytest configuration and fixtures for SDK tests
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import Dict, Any


# ==================== Mock Data ====================

@pytest.fixture
def mock_agent_data() -> Dict[str, Any]:
    """Mock agent data"""
    return {
        "id": "agent-123",
        "tenant_id": "tenant-1",
        "name": "TestAgent",
        "model": "llama3.2:latest",
        "provider": "ollama",
        "description": "A test agent",
        "system_prompt": "You are a helpful assistant.",
        "tools": ["web_search", "code_executor"],
        "rag_collection_ids": ["collection-1"],
        "max_iterations": 10,
        "temperature": 0.7,
        "metadata": {"key": "value"},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_agent_execution_data() -> Dict[str, Any]:
    """Mock agent execution data"""
    return {
        "id": "exec-123",
        "agent_id": "agent-123",
        "tenant_id": "tenant-1",
        "user_message": "Hello!",
        "response": "Hi there! How can I help you?",
        "status": "completed",
        "context": {"session_id": "session-1"},
        "tools_used": [],
        "tokens_used": {},
        "cost_usd": 0.001,
        "execution_time_seconds": 5.0,
        "error": None,
        "created_at": "2024-01-01T00:00:00",
        "completed_at": "2024-01-01T00:01:00",
    }


@pytest.fixture
def mock_schedule_data() -> Dict[str, Any]:
    """Mock scheduled task data"""
    return {
        "id": "schedule-123",
        "tenant_id": "tenant-1",
        "agent_id": "agent-123",
        "cron_expression": "0 9 * * *",
        "task_config": {"message": "Generate daily report"},
        "is_active": True,
        "last_run": "2024-01-01T09:00:00",
        "next_run": "2024-01-02T09:00:00",
        "run_count": 10,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_task_execution_data() -> Dict[str, Any]:
    """Mock task execution data"""
    return {
        "id": "task-exec-123",
        "task_id": "schedule-123",
        "agent_execution_id": "exec-456",
        "status": "completed",
        "error": None,
        "started_at": "2024-01-01T09:00:00",
        "completed_at": "2024-01-01T09:05:00",
    }


@pytest.fixture
def mock_collection_data() -> Dict[str, Any]:
    """Mock RAG collection data"""
    return {
        "id": "collection-123",
        "tenant_id": "tenant-1",
        "name": "Documentation",
        "description": "Product documentation",
        "embedding_model": "nomic-embed-text",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "metadata": {},
        "document_count": 50,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_document_data() -> Dict[str, Any]:
    """Mock document data"""
    return {
        "id": "doc-123",
        "collection_id": "collection-123",
        "filename": "readme.md",
        "content_type": "text/markdown",
        "size_bytes": 1024,
        "chunk_count": 5,
        "metadata": {"category": "guide"},
        "created_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_query_result_data() -> Dict[str, Any]:
    """Mock query result data"""
    return {
        "query": "How to install?",
        "chunks": [
            {
                "content": "Installation guide...",
                "metadata": {"filename": "install.md"},
                "score": 0.95,
            },
            {
                "content": "Quick start guide...",
                "metadata": {"filename": "quickstart.md"},
                "score": 0.85,
            },
        ],
        "collection_id": "collection-123",
        "total_results": 2,
    }


@pytest.fixture
def mock_collaboration_session_data() -> Dict[str, Any]:
    """Mock collaboration session data"""
    return {
        "id": "collab-123",
        "tenant_id": "tenant-1",
        "pattern": "sequential",
        "agent_ids": ["agent-1", "agent-2", "agent-3"],
        "status": "completed",
        "results": [
            {"agent_id": "agent-1", "output": "Design complete"},
            {"agent_id": "agent-2", "output": "Implementation complete"},
            {"agent_id": "agent-3", "output": "Tests complete"},
        ],
        "created_at": "2024-01-01T10:00:00",
        "completed_at": "2024-01-01T11:00:00",
    }


@pytest.fixture
def mock_cost_summary_data() -> Dict[str, Any]:
    """Mock cost summary data"""
    return {
        "total_usd": 15.50,
        "by_provider": {
            "openai": 10.00,
            "anthropic": 5.50,
        },
        "by_model": {
            "gpt-4": 10.00,
            "claude-3": 5.50,
        },
        "by_agent": {
            "agent-1": 10.00,
            "agent-2": 5.50,
        },
        "total_tokens": {
            "input": 250000,
            "output": 250000,
        },
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-31T23:59:59",
    }


@pytest.fixture
def mock_budget_config_data() -> Dict[str, Any]:
    """Mock budget configuration data"""
    return {
        "daily_limit_usd": 10.00,
        "monthly_limit_usd": 100.00,
        "alert_threshold": 0.8,
    }


@pytest.fixture
def mock_webhook_data() -> Dict[str, Any]:
    """Mock webhook data"""
    return {
        "id": "webhook-123",
        "tenant_id": "tenant-1",
        "name": "Test Webhook",
        "url": "https://example.com/webhook",
        "events": ["agent.execution.completed", "agent.execution.failed"],
        "secret": "webhook-secret",
        "is_active": True,
        "headers": {},
        "retry_config": {},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_webhook_delivery_data() -> Dict[str, Any]:
    """Mock webhook delivery data"""
    return {
        "id": "delivery-123",
        "webhook_id": "webhook-123",
        "event_type": "agent.execution.completed",
        "payload": {"execution_id": "exec-123"},
        "status": "success",
        "response_status": 200,
        "response_body": "OK",
        "attempt_count": 1,
        "error": None,
        "delivered_at": "2024-01-01T10:00:00",
        "created_at": "2024-01-01T10:00:00",
    }


# ==================== HTTP Mocking ====================

@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx.Response"""
    def _create_response(
        status_code: int = 200,
        json_data: Any = None,
        text: str = "",
        headers: Dict[str, str] = None
    ):
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.headers = headers or {}
        response.content = b""

        if json_data is not None:
            response.json.return_value = json_data
            response.content = b"{}"
        else:
            response.text = text
            response.json.side_effect = Exception("No JSON")

        return response

    return _create_response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Create a mock httpx.Client"""
    client = Mock(spec=httpx.Client)

    # Set default response
    client.request.return_value = mock_httpx_response()

    return client


@pytest.fixture
def mock_async_httpx_client():
    """Create a mock httpx.AsyncClient"""
    client = AsyncMock(spec=httpx.AsyncClient)

    # Set default response
    response = AsyncMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {}
    response.content = b""

    client.request.return_value = response

    return client


# ==================== Environment ====================

@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables"""
    monkeypatch.delenv("TEMPONEST_BASE_URL", raising=False)
    monkeypatch.delenv("TEMPONEST_AUTH_TOKEN", raising=False)


@pytest.fixture
def set_env(monkeypatch):
    """Set environment variables"""
    monkeypatch.setenv("TEMPONEST_BASE_URL", "http://localhost:9000")
    monkeypatch.setenv("TEMPONEST_AUTH_TOKEN", "test-token")
