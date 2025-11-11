"""
Test fixtures for CLI tests
"""
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, MagicMock
from datetime import datetime


@pytest.fixture
def runner():
    """Click test runner"""
    return CliRunner()


@pytest.fixture
def mock_agent():
    """Mock agent object"""
    agent = Mock()
    agent.id = "agent-123456789"  # Need at least 8 chars for slicing
    agent.name = "Test Agent"
    agent.description = "Test agent description"
    agent.model = "llama3.2:latest"
    agent.provider = "ollama"
    agent.temperature = 0.7
    agent.max_iterations = 10
    agent.tools = ["search", "calculator"]
    agent.created_at = datetime(2024, 1, 1, 12, 0, 0)
    return agent


@pytest.fixture
def mock_agent_execution():
    """Mock agent execution result"""
    return Mock(
        id="exec-123",
        agent_id="agent-123",
        status="completed",
        response="Test response from agent",
        tokens_used=150,
        cost_usd=0.0025,
        execution_time_seconds=2.5,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def mock_schedule():
    """Mock schedule object"""
    schedule = Mock()
    schedule.id = "schedule-123456789"  # Need at least 8 chars for slicing
    schedule.agent_id = "agent-123456789"  # Need at least 8 chars for slicing
    schedule.cron_expression = "0 9 * * *"
    schedule.is_active = True
    schedule.next_run = datetime(2024, 1, 2, 9, 0, 0)
    schedule.run_count = 5
    schedule.task_config = {"user_message": "Test message"}
    return schedule


@pytest.fixture
def mock_task_execution():
    """Mock task execution"""
    return Mock(
        id="task-exec-123",
        schedule_id="schedule-123",
        status="completed",
        started_at=datetime(2024, 1, 1, 9, 0, 0),
        completed_at=datetime(2024, 1, 1, 9, 2, 30),
    )


@pytest.fixture
def mock_cost_summary():
    """Mock cost summary"""
    return Mock(
        total_usd=125.50,
        total_tokens=500000,
        by_provider={"openai": 75.25, "anthropic": 50.25},
        by_model={"gpt-4": 60.00, "claude-3": 50.25, "gpt-3.5": 15.25},
    )


@pytest.fixture
def mock_budget():
    """Mock budget object"""
    return Mock(
        daily_limit_usd=50.0,
        monthly_limit_usd=1000.0,
        alert_threshold=0.8,
    )


@pytest.fixture
def mock_budget_status():
    """Mock budget status"""
    return {
        "daily_limit": 50.0,
        "daily_usage": 25.50,
        "daily_percentage": 0.51,
        "monthly_limit": 1000.0,
        "monthly_usage": 350.75,
        "monthly_percentage": 0.35,
    }


@pytest.fixture
def mock_client(
    mock_agent,
    mock_agent_execution,
    mock_schedule,
    mock_task_execution,
    mock_cost_summary,
    mock_budget,
    mock_budget_status,
):
    """Mock Temponest client"""
    client = MagicMock()

    # Mock agents client
    client.agents.list.return_value = [mock_agent]
    client.agents.create.return_value = mock_agent
    client.agents.get.return_value = mock_agent
    client.agents.execute.return_value = mock_agent_execution
    client.agents.execute_stream.return_value = iter(["Test ", "streaming ", "response"])
    client.agents.delete.return_value = None

    # Mock scheduler client
    client.scheduler.list.return_value = [mock_schedule]
    client.scheduler.create.return_value = mock_schedule
    client.scheduler.pause.return_value = mock_schedule
    client.scheduler.resume.return_value = mock_schedule
    client.scheduler.trigger.return_value = mock_task_execution
    client.scheduler.delete.return_value = None

    # Mock costs client
    client.costs.get_summary.return_value = mock_cost_summary
    client.costs.get_budget_status.return_value = mock_budget_status
    client.costs.set_budget.return_value = mock_budget

    return client


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("TEMPONEST_BASE_URL", "http://localhost:9000")
    monkeypatch.setenv("TEMPONEST_AUTH_TOKEN", "test-token-123")
