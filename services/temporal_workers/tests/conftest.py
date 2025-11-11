"""
Pytest configuration and shared fixtures for Temporal Workers tests.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Dict, Any
from datetime import datetime

# Set test environment variables
os.environ["AGENTS_URL"] = "http://test-agents:9000"
os.environ["APPROVAL_UI_URL"] = "http://test-approval:9001"
os.environ["N8N_WEBHOOK_URL"] = "http://test-n8n:5678/webhook/approval"
os.environ["TEMPORAL_HOST"] = "test-temporal:7233"
os.environ["TEMPORAL_NAMESPACE"] = "test"


@pytest.fixture
def mock_overseer_response():
    """Mock Overseer agent response"""
    return {
        "result": {
            "plan": [
                {"task": "Create database schema", "agent": "developer"},
                {"task": "Implement API endpoints", "agent": "developer"},
                {"task": "Write unit tests", "agent": "developer"}
            ],
            "citations": [
                {"source": "doc1.md", "content": "Schema design"},
                {"source": "doc2.md", "content": "API patterns"}
            ]
        },
        "latency_ms": 1234
    }


@pytest.fixture
def mock_developer_response():
    """Mock Developer agent response"""
    return {
        "result": {
            "code": {
                "implementation": "def hello_world():\n    return 'Hello, World!'\n" * 10,
                "tests": "def test_hello():\n    assert hello_world() == 'Hello, World!'\n" * 5
            },
            "setup": "pip install requirements.txt",
            "citations": [
                {"source": "best_practices.md", "content": "Code structure"},
                {"source": "testing.md", "content": "Test patterns"},
                {"source": "setup.md", "content": "Setup instructions"}
            ]
        },
        "latency_ms": 5678
    }


@pytest.fixture
def mock_approval_response():
    """Mock approval creation response"""
    return {
        "approval_id": "test-approval-123",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient"""
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return client


@pytest.fixture
def project_request():
    """Sample ProjectRequest"""
    return {
        "goal": "Create a TODO app",
        "context": {"language": "Python", "framework": "FastAPI"},
        "requester": "test-user",
        "idempotency_key": "test-key-123"
    }


@pytest.fixture
def approval_request():
    """Sample ApprovalRequest"""
    return {
        "task_description": "Deploy to production",
        "risk_level": "high",
        "context": {"environment": "production"},
        "required_approvers": 2
    }
