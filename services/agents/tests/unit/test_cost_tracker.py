"""
Unit tests for cost tracker.
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from app.cost.tracker import CostTracker
from app.cost.calculator import CostCalculator


@pytest.mark.unit
class TestCostTracker:
    """Test suite for CostTracker"""

    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        pool = MagicMock()
        conn = AsyncMock()

        # Create a proper async context manager
        async def mock_acquire():
            return conn

        pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn), __aexit__=AsyncMock(return_value=None)))
        return pool, conn

    @pytest.fixture
    def calculator(self):
        """Create cost calculator"""
        return CostCalculator()

    @pytest.fixture
    def tracker(self, mock_db_pool, calculator):
        """Create cost tracker with mocked dependencies"""
        pool, _ = mock_db_pool
        return CostTracker(db_pool=pool, calculator=calculator)

    @pytest.mark.asyncio
    async def test_record_execution_success(self, tracker, mock_db_pool):
        """Test recording an execution successfully"""
        pool, conn = mock_db_pool

        # Mock budget check to return no alerts
        conn.fetch.return_value = []

        result = await tracker.record_execution(
            task_id="task-123",
            agent_name="developer",
            user_id=uuid4(),
            tenant_id=uuid4(),
            model_provider="claude",
            model_name="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500,
            status="completed"
        )

        # Verify execution was recorded
        assert conn.execute.called
        assert result["task_id"] == "task-123"
        assert result["total_tokens"] == 1500
        assert result["total_cost_usd"] > 0
        assert result["budget_status"]["within_budget"] is True

    @pytest.mark.asyncio
    async def test_record_execution_with_project_and_workflow(self, tracker, mock_db_pool):
        """Test recording execution with project and workflow IDs"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        result = await tracker.record_execution(
            task_id="task-456",
            agent_name="qa_tester",
            user_id=uuid4(),
            tenant_id=uuid4(),
            model_provider="openai",
            model_name="gpt-4o",
            input_tokens=2000,
            output_tokens=1000,
            latency_ms=2000,
            status="completed",
            project_id="project-123",
            workflow_id="workflow-456"
        )

        # Check that execute was called with project/workflow IDs
        call_args = conn.execute.call_args[0]
        assert "project-123" in call_args
        assert "workflow-456" in call_args

    @pytest.mark.asyncio
    async def test_record_execution_calculates_correct_cost(self, tracker, mock_db_pool):
        """Test that costs are calculated correctly"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        result = await tracker.record_execution(
            task_id="task-789",
            agent_name="overseer",
            user_id=uuid4(),
            tenant_id=uuid4(),
            model_provider="claude",
            model_name="claude-haiku-4-20250514",
            input_tokens=10000,
            output_tokens=5000,
            latency_ms=800,
            status="completed"
        )

        # Haiku: $0.25/1M input, $1.25/1M output
        # 10k * 0.25/1M = 0.0025, 5k * 1.25/1M = 0.00625
        assert result["input_cost_usd"] == pytest.approx(0.0025, abs=0.000001)
        assert result["output_cost_usd"] == pytest.approx(0.00625, abs=0.000001)
        assert result["total_cost_usd"] == pytest.approx(0.00875, abs=0.000001)

    @pytest.mark.asyncio
    async def test_record_execution_ollama_free(self, tracker, mock_db_pool):
        """Test that Ollama executions have zero cost"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        result = await tracker.record_execution(
            task_id="task-ollama",
            agent_name="developer",
            user_id=uuid4(),
            tenant_id=uuid4(),
            model_provider="ollama",
            model_name="mistral:7b-instruct",
            input_tokens=5000,
            output_tokens=3000,
            latency_ms=1200,
            status="completed"
        )

        assert result["total_cost_usd"] == 0.0
        assert result["input_cost_usd"] == 0.0
        assert result["output_cost_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_check_budgets_within_budget(self, tracker, mock_db_pool):
        """Test budget check when within limits"""
        pool, conn = mock_db_pool

        # Mock response: no budget exceeded
        conn.fetch.return_value = [{
            "budget_id": uuid4(),
            "exceeded": False,
            "alert_type": None
        }]

        budget_status = await tracker._check_budgets(
            conn=conn,
            tenant_id=uuid4(),
            user_id=uuid4(),
            project_id="project-123",
            cost_usd=Decimal("0.50")
        )

        assert budget_status["within_budget"] is True
        assert budget_status["budget_exceeded"] is False
        assert len(budget_status["alerts"]) == 0

    @pytest.mark.asyncio
    async def test_check_budgets_warning_alert(self, tracker, mock_db_pool):
        """Test budget check when warning threshold reached"""
        pool, conn = mock_db_pool

        budget_id = uuid4()
        conn.fetch.return_value = [{
            "budget_id": budget_id,
            "exceeded": False,
            "alert_type": "warning"
        }]

        # Mock budget details query
        conn.fetchrow.return_value = {
            "budget_type": "daily",
            "budget_amount_usd": Decimal("100.00"),
            "current_spend_usd": Decimal("85.00"),
            "alert_threshold_pct": 80,
            "critical_threshold_pct": 95,
            "tenant_id": uuid4(),
            "user_id": uuid4(),
            "project_id": "project-123"
        }

        budget_status = await tracker._check_budgets(
            conn=conn,
            tenant_id=uuid4(),
            user_id=uuid4(),
            project_id="project-123",
            cost_usd=Decimal("5.00")
        )

        assert budget_status["within_budget"] is True
        assert budget_status["budget_exceeded"] is False
        assert len(budget_status["alerts"]) == 1
        assert budget_status["alerts"][0]["alert_type"] == "warning"

    @pytest.mark.asyncio
    async def test_check_budgets_exceeded(self, tracker, mock_db_pool):
        """Test budget check when budget exceeded"""
        pool, conn = mock_db_pool

        budget_id = uuid4()
        conn.fetch.return_value = [{
            "budget_id": budget_id,
            "exceeded": True,
            "alert_type": "critical"
        }]

        conn.fetchrow.return_value = {
            "budget_type": "daily",
            "budget_amount_usd": Decimal("100.00"),
            "current_spend_usd": Decimal("102.00"),
            "alert_threshold_pct": 80,
            "critical_threshold_pct": 95,
            "tenant_id": uuid4(),
            "user_id": uuid4(),
            "project_id": "project-123"
        }

        budget_status = await tracker._check_budgets(
            conn=conn,
            tenant_id=uuid4(),
            user_id=uuid4(),
            project_id="project-123",
            cost_usd=Decimal("5.00")
        )

        assert budget_status["within_budget"] is False
        assert budget_status["budget_exceeded"] is True
        assert len(budget_status["alerts"]) == 1
        assert budget_status["alerts"][0]["alert_type"] == "critical"

    @pytest.mark.asyncio
    async def test_budget_alert_publishes_event(self, mock_db_pool, calculator):
        """Test that budget alerts publish webhook events"""
        pool, conn = mock_db_pool
        mock_event_dispatcher = AsyncMock()

        tracker = CostTracker(
            db_pool=pool,
            calculator=calculator,
            event_dispatcher=mock_event_dispatcher
        )

        budget_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()

        conn.fetch.return_value = [{
            "budget_id": budget_id,
            "exceeded": False,
            "alert_type": "warning"
        }]

        conn.fetchrow.return_value = {
            "budget_type": "daily",
            "budget_amount_usd": Decimal("100.00"),
            "current_spend_usd": Decimal("85.00"),
            "alert_threshold_pct": 80,
            "critical_threshold_pct": 95,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "project_id": "project-123"
        }

        await tracker._check_budgets(
            conn=conn,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id="project-123",
            cost_usd=Decimal("5.00")
        )

        # Verify event was published
        assert mock_event_dispatcher.publish_event.called

    @pytest.mark.asyncio
    async def test_record_execution_with_context(self, tracker, mock_db_pool):
        """Test recording execution with custom context"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        context = {
            "user_action": "code_generation",
            "file_count": 3,
            "language": "python"
        }

        result = await tracker.record_execution(
            task_id="task-ctx",
            agent_name="developer",
            user_id=uuid4(),
            tenant_id=uuid4(),
            model_provider="claude",
            model_name="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500,
            status="completed",
            context=context
        )

        # Verify context was passed to database
        call_args = conn.execute.call_args[0]
        assert any("user_action" in str(arg) for arg in call_args)

    @pytest.mark.asyncio
    async def test_record_execution_failed_status(self, tracker, mock_db_pool):
        """Test recording a failed execution"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        result = await tracker.record_execution(
            task_id="task-failed",
            agent_name="developer",
            user_id=uuid4(),
            tenant_id=uuid4(),
            model_provider="claude",
            model_name="claude-sonnet-4-20250514",
            input_tokens=500,
            output_tokens=0,  # No output due to failure
            latency_ms=100,
            status="failed"
        )

        # Even failed executions should record costs
        assert result["total_cost_usd"] > 0
        assert result["task_id"] == "task-failed"
