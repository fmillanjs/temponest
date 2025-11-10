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

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_agent(self, tracker, mock_db_pool):
        """Test getting cost summary grouped by agent"""
        pool, conn = mock_db_pool

        # Mock query results
        conn.fetch.return_value = [
            {
                "agent_name": "developer",
                "total_executions": 100,
                "total_tokens": 500000,
                "total_cost_usd": Decimal("12.50"),
                "avg_cost_per_execution": Decimal("0.125"),
                "avg_latency_ms": 1500.0
            },
            {
                "agent_name": "qa_tester",
                "total_executions": 50,
                "total_tokens": 250000,
                "total_cost_usd": Decimal("6.25"),
                "avg_cost_per_execution": Decimal("0.125"),
                "avg_latency_ms": 1200.0
            }
        ]

        tenant_id = uuid4()
        results = await tracker.get_cost_summary(
            tenant_id=tenant_id,
            group_by="agent"
        )

        assert len(results) == 2
        assert results[0]["agent_name"] == "developer"
        assert results[0]["total_cost_usd"] == 12.50
        assert results[1]["agent_name"] == "qa_tester"
        conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_project(self, tracker, mock_db_pool):
        """Test getting cost summary grouped by project"""
        pool, conn = mock_db_pool

        conn.fetch.return_value = [
            {
                "project_id": "project-123",
                "total_executions": 75,
                "total_tokens": 400000,
                "total_cost_usd": Decimal("10.00"),
                "avg_cost_per_execution": Decimal("0.133")
            }
        ]

        tenant_id = uuid4()
        results = await tracker.get_cost_summary(
            tenant_id=tenant_id,
            group_by="project"
        )

        assert len(results) == 1
        assert results[0]["project_id"] == "project-123"
        assert results[0]["total_cost_usd"] == 10.00

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_user(self, tracker, mock_db_pool):
        """Test getting cost summary grouped by user"""
        pool, conn = mock_db_pool

        user_id = uuid4()
        conn.fetch.return_value = [
            {
                "user_id": user_id,
                "total_executions": 30,
                "total_tokens": 150000,
                "total_cost_usd": Decimal("3.75"),
                "avg_cost_per_execution": Decimal("0.125")
            }
        ]

        tenant_id = uuid4()
        results = await tracker.get_cost_summary(
            tenant_id=tenant_id,
            group_by="user"
        )

        assert len(results) == 1
        assert results[0]["user_id"] == str(user_id)
        assert results[0]["total_cost_usd"] == 3.75

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_daily(self, tracker, mock_db_pool):
        """Test getting cost summary grouped by day"""
        pool, conn = mock_db_pool

        from datetime import date
        conn.fetch.return_value = [
            {
                "date": date(2025, 1, 15),
                "total_executions": 200,
                "total_tokens": 1000000,
                "total_cost_usd": Decimal("25.00")
            },
            {
                "date": date(2025, 1, 14),
                "total_executions": 150,
                "total_tokens": 750000,
                "total_cost_usd": Decimal("18.75")
            }
        ]

        tenant_id = uuid4()
        results = await tracker.get_cost_summary(
            tenant_id=tenant_id,
            group_by="daily"
        )

        assert len(results) == 2
        assert results[0]["total_cost_usd"] == 25.00
        assert results[1]["total_cost_usd"] == 18.75

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_date_range(self, tracker, mock_db_pool):
        """Test getting cost summary with date filters"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        from datetime import datetime
        tenant_id = uuid4()
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)

        await tracker.get_cost_summary(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            group_by="agent"
        )

        # Verify dates were passed to query
        call_args = conn.fetch.call_args[0]
        assert start_date in call_args
        assert end_date in call_args

    @pytest.mark.asyncio
    async def test_get_cost_summary_invalid_group_by(self, tracker, mock_db_pool):
        """Test that invalid group_by raises ValueError"""
        with pytest.raises(ValueError, match="Invalid group_by"):
            await tracker.get_cost_summary(
                tenant_id=uuid4(),
                group_by="invalid"
            )

    @pytest.mark.asyncio
    async def test_get_budgets_all(self, tracker, mock_db_pool):
        """Test getting all budgets for a tenant"""
        pool, conn = mock_db_pool

        budget_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()

        conn.fetch.return_value = [
            {
                "id": budget_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "project_id": None,
                "budget_type": "monthly",
                "budget_amount_usd": Decimal("1000.00"),
                "current_spend_usd": Decimal("750.00"),
                "period_start": None,
                "period_end": None,
                "alert_threshold_pct": 80,
                "critical_threshold_pct": 95,
                "is_active": True,
                "last_reset_at": None,
                "notes": "Monthly budget",
                "created_at": None,
                "updated_at": None
            }
        ]

        results = await tracker.get_budgets(tenant_id=tenant_id)

        assert len(results) == 1
        assert results[0]["id"] == str(budget_id)
        assert results[0]["budget_amount_usd"] == 1000.00
        assert results[0]["current_spend_usd"] == 750.00
        assert results[0]["utilization_pct"] == 75.0

    @pytest.mark.asyncio
    async def test_get_budgets_filtered_by_user(self, tracker, mock_db_pool):
        """Test getting budgets filtered by user"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        tenant_id = uuid4()
        user_id = uuid4()

        await tracker.get_budgets(
            tenant_id=tenant_id,
            user_id=user_id
        )

        call_args = conn.fetch.call_args[0]
        assert tenant_id in call_args
        assert user_id in call_args

    @pytest.mark.asyncio
    async def test_get_budgets_filtered_by_project(self, tracker, mock_db_pool):
        """Test getting budgets filtered by project"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        tenant_id = uuid4()
        project_id = "project-456"

        await tracker.get_budgets(
            tenant_id=tenant_id,
            project_id=project_id
        )

        call_args = conn.fetch.call_args[0]
        assert project_id in call_args

    @pytest.mark.asyncio
    async def test_get_budgets_active_only(self, tracker, mock_db_pool):
        """Test getting only active budgets"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        await tracker.get_budgets(
            tenant_id=uuid4(),
            active_only=True
        )

        call_args = conn.fetch.call_args[0]
        assert True in call_args  # active_only parameter

    @pytest.mark.asyncio
    async def test_get_budgets_utilization_calculation(self, tracker, mock_db_pool):
        """Test budget utilization percentage calculation"""
        pool, conn = mock_db_pool

        conn.fetch.return_value = [
            {
                "id": uuid4(),
                "tenant_id": uuid4(),
                "user_id": None,
                "project_id": None,
                "budget_type": "daily",
                "budget_amount_usd": Decimal("100.00"),
                "current_spend_usd": Decimal("45.50"),
                "period_start": None,
                "period_end": None,
                "alert_threshold_pct": 80,
                "critical_threshold_pct": 95,
                "is_active": True,
                "last_reset_at": None,
                "notes": None,
                "created_at": None,
                "updated_at": None
            }
        ]

        results = await tracker.get_budgets(tenant_id=uuid4())

        assert results[0]["utilization_pct"] == 45.5

    @pytest.mark.asyncio
    async def test_get_budgets_zero_budget_amount(self, tracker, mock_db_pool):
        """Test budget with zero amount"""
        pool, conn = mock_db_pool

        conn.fetch.return_value = [
            {
                "id": uuid4(),
                "tenant_id": uuid4(),
                "user_id": None,
                "project_id": None,
                "budget_type": "daily",
                "budget_amount_usd": Decimal("0.00"),
                "current_spend_usd": Decimal("0.00"),
                "period_start": None,
                "period_end": None,
                "alert_threshold_pct": 80,
                "critical_threshold_pct": 95,
                "is_active": True,
                "last_reset_at": None,
                "notes": None,
                "created_at": None,
                "updated_at": None
            }
        ]

        results = await tracker.get_budgets(tenant_id=uuid4())

        assert results[0]["utilization_pct"] == 0

    @pytest.mark.asyncio
    async def test_create_budget_tenant_level(self, tracker, mock_db_pool):
        """Test creating a tenant-level budget"""
        pool, conn = mock_db_pool

        budget_id = uuid4()
        from datetime import datetime
        created_at = datetime.utcnow()

        conn.fetchrow.return_value = {
            "id": budget_id,
            "created_at": created_at
        }

        tenant_id = uuid4()
        result = await tracker.create_budget(
            tenant_id=tenant_id,
            user_id=None,
            project_id=None,
            budget_type="monthly",
            budget_amount_usd=Decimal("5000.00"),
            alert_threshold_pct=75,
            critical_threshold_pct=90
        )

        assert result["id"] == str(budget_id)
        assert result["budget_type"] == "monthly"
        assert result["budget_amount_usd"] == 5000.00
        assert result["alert_threshold_pct"] == 75
        assert result["critical_threshold_pct"] == 90

    @pytest.mark.asyncio
    async def test_create_budget_user_level(self, tracker, mock_db_pool):
        """Test creating a user-level budget"""
        pool, conn = mock_db_pool

        budget_id = uuid4()
        from datetime import datetime
        conn.fetchrow.return_value = {
            "id": budget_id,
            "created_at": datetime.utcnow()
        }

        user_id = uuid4()
        result = await tracker.create_budget(
            tenant_id=None,
            user_id=user_id,
            project_id=None,
            budget_type="daily",
            budget_amount_usd=Decimal("100.00")
        )

        assert result["id"] == str(budget_id)
        assert result["budget_type"] == "daily"

    @pytest.mark.asyncio
    async def test_create_budget_project_level(self, tracker, mock_db_pool):
        """Test creating a project-level budget"""
        pool, conn = mock_db_pool

        budget_id = uuid4()
        from datetime import datetime
        conn.fetchrow.return_value = {
            "id": budget_id,
            "created_at": datetime.utcnow()
        }

        result = await tracker.create_budget(
            tenant_id=None,
            user_id=None,
            project_id="project-789",
            budget_type="total",
            budget_amount_usd=Decimal("10000.00"),
            period_days=90,
            notes="Q1 budget"
        )

        assert result["id"] == str(budget_id)
        assert result["budget_type"] == "total"

    @pytest.mark.asyncio
    async def test_create_budget_invalid_scope(self, tracker, mock_db_pool):
        """Test that creating budget with multiple scopes raises ValueError"""
        with pytest.raises(ValueError, match="Exactly one"):
            await tracker.create_budget(
                tenant_id=uuid4(),
                user_id=uuid4(),  # Both set - invalid
                project_id=None,
                budget_type="monthly",
                budget_amount_usd=Decimal("1000.00")
            )

    @pytest.mark.asyncio
    async def test_create_budget_no_scope(self, tracker, mock_db_pool):
        """Test that creating budget with no scope raises ValueError"""
        with pytest.raises(ValueError, match="Exactly one"):
            await tracker.create_budget(
                tenant_id=None,
                user_id=None,
                project_id=None,
                budget_type="monthly",
                budget_amount_usd=Decimal("1000.00")
            )

    @pytest.mark.asyncio
    async def test_create_budget_daily_type(self, tracker, mock_db_pool):
        """Test creating daily budget sets period_days=1"""
        pool, conn = mock_db_pool

        from datetime import datetime
        conn.fetchrow.return_value = {
            "id": uuid4(),
            "created_at": datetime.utcnow()
        }

        await tracker.create_budget(
            tenant_id=uuid4(),
            user_id=None,
            project_id=None,
            budget_type="daily",
            budget_amount_usd=Decimal("50.00")
        )

        # Check that period_days was set in the query
        call_args = conn.fetchrow.call_args[0]
        assert 1 in call_args  # period_days for daily

    @pytest.mark.asyncio
    async def test_create_budget_weekly_type(self, tracker, mock_db_pool):
        """Test creating weekly budget sets period_days=7"""
        pool, conn = mock_db_pool

        from datetime import datetime
        conn.fetchrow.return_value = {
            "id": uuid4(),
            "created_at": datetime.utcnow()
        }

        await tracker.create_budget(
            tenant_id=uuid4(),
            user_id=None,
            project_id=None,
            budget_type="weekly",
            budget_amount_usd=Decimal("350.00")
        )

        call_args = conn.fetchrow.call_args[0]
        assert 7 in call_args  # period_days for weekly

    @pytest.mark.asyncio
    async def test_create_budget_monthly_type(self, tracker, mock_db_pool):
        """Test creating monthly budget sets period_days=30"""
        pool, conn = mock_db_pool

        from datetime import datetime
        conn.fetchrow.return_value = {
            "id": uuid4(),
            "created_at": datetime.utcnow()
        }

        await tracker.create_budget(
            tenant_id=uuid4(),
            user_id=None,
            project_id=None,
            budget_type="monthly",
            budget_amount_usd=Decimal("1500.00")
        )

        call_args = conn.fetchrow.call_args[0]
        assert 30 in call_args  # period_days for monthly

    @pytest.mark.asyncio
    async def test_get_alerts_unacknowledged(self, tracker, mock_db_pool):
        """Test getting unacknowledged alerts"""
        pool, conn = mock_db_pool

        alert_id = uuid4()
        budget_id = uuid4()

        from datetime import datetime
        conn.fetch.return_value = [
            {
                "id": alert_id,
                "budget_id": budget_id,
                "alert_type": "warning",
                "threshold_pct": 80,
                "current_spend_usd": Decimal("85.00"),
                "budget_amount_usd": Decimal("100.00"),
                "is_acknowledged": False,
                "acknowledged_by": None,
                "acknowledged_at": None,
                "message": "Budget at 85%",
                "created_at": datetime.utcnow(),
                "budget_type": "daily",
                "scope_name": "project-123"
            }
        ]

        tenant_id = uuid4()
        results = await tracker.get_alerts(
            tenant_id=tenant_id,
            unacknowledged_only=True
        )

        assert len(results) == 1
        assert results[0]["id"] == str(alert_id)
        assert results[0]["alert_type"] == "warning"
        assert results[0]["is_acknowledged"] is False
        assert results[0]["current_spend_usd"] == 85.00

    @pytest.mark.asyncio
    async def test_get_alerts_all(self, tracker, mock_db_pool):
        """Test getting all alerts including acknowledged"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        tenant_id = uuid4()
        await tracker.get_alerts(
            tenant_id=tenant_id,
            unacknowledged_only=False,
            limit=100
        )

        call_args = conn.fetch.call_args[0]
        assert tenant_id in call_args
        assert False in call_args  # unacknowledged_only
        assert 100 in call_args  # limit

    @pytest.mark.asyncio
    async def test_get_alerts_with_limit(self, tracker, mock_db_pool):
        """Test getting alerts with custom limit"""
        pool, conn = mock_db_pool
        conn.fetch.return_value = []

        await tracker.get_alerts(
            tenant_id=uuid4(),
            limit=10
        )

        call_args = conn.fetch.call_args[0]
        assert 10 in call_args

    @pytest.mark.asyncio
    async def test_acknowledge_alert_success(self, tracker, mock_db_pool):
        """Test acknowledging an alert"""
        pool, conn = mock_db_pool

        # Mock successful update
        conn.execute.return_value = "UPDATE 1"

        alert_id = uuid4()
        acknowledged_by = uuid4()

        result = await tracker.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=acknowledged_by
        )

        assert result is True
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(self, tracker, mock_db_pool):
        """Test acknowledging non-existent alert"""
        pool, conn = mock_db_pool

        # Mock no rows updated
        conn.execute.return_value = "UPDATE 0"

        alert_id = uuid4()
        acknowledged_by = uuid4()

        result = await tracker.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=acknowledged_by
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_budgets_empty_results(self, tracker, mock_db_pool):
        """Test budget check with empty database results"""
        pool, conn = mock_db_pool

        # Empty results
        conn.fetch.return_value = []

        budget_status = await tracker._check_budgets(
            conn=conn,
            tenant_id=uuid4(),
            user_id=None,
            project_id=None,
            cost_usd=Decimal("1.00")
        )

        assert budget_status["within_budget"] is True
        assert budget_status["alerts"] == []

    @pytest.mark.asyncio
    async def test_check_budgets_null_exceeded(self, tracker, mock_db_pool):
        """Test budget check with null exceeded field"""
        pool, conn = mock_db_pool

        conn.fetch.return_value = [{
            "budget_id": uuid4(),
            "exceeded": None,
            "alert_type": None
        }]

        budget_status = await tracker._check_budgets(
            conn=conn,
            tenant_id=uuid4(),
            user_id=None,
            project_id=None,
            cost_usd=Decimal("1.00")
        )

        assert budget_status["within_budget"] is True

    @pytest.mark.asyncio
    async def test_budget_alert_event_publish_failure(self, mock_db_pool, calculator):
        """Test that budget alert event publish failures are handled gracefully"""
        pool, conn = mock_db_pool
        mock_event_dispatcher = AsyncMock()
        mock_event_dispatcher.publish_event.side_effect = Exception("Event dispatch failed")

        tracker = CostTracker(
            db_pool=pool,
            calculator=calculator,
            event_dispatcher=mock_event_dispatcher
        )

        budget_id = uuid4()
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
            "tenant_id": uuid4(),
            "user_id": uuid4(),
            "project_id": None
        }

        # Should not raise exception despite event publish failure
        budget_status = await tracker._check_budgets(
            conn=conn,
            tenant_id=uuid4(),
            user_id=uuid4(),
            project_id=None,
            cost_usd=Decimal("5.00")
        )

        # Alert should still be returned even if event publish failed
        assert len(budget_status["alerts"]) == 1

    @pytest.mark.asyncio
    async def test_budget_alert_critical_event(self, mock_db_pool, calculator):
        """Test critical budget alert event"""
        pool, conn = mock_db_pool
        mock_event_dispatcher = AsyncMock()

        tracker = CostTracker(
            db_pool=pool,
            calculator=calculator,
            event_dispatcher=mock_event_dispatcher
        )

        budget_id = uuid4()
        tenant_id = uuid4()

        conn.fetch.return_value = [{
            "budget_id": budget_id,
            "exceeded": True,
            "alert_type": "critical"
        }]

        conn.fetchrow.return_value = {
            "budget_type": "monthly",
            "budget_amount_usd": Decimal("1000.00"),
            "current_spend_usd": Decimal("980.00"),
            "alert_threshold_pct": 80,
            "critical_threshold_pct": 95,
            "tenant_id": tenant_id,
            "user_id": None,
            "project_id": "project-critical"
        }

        await tracker._check_budgets(
            conn=conn,
            tenant_id=tenant_id,
            user_id=None,
            project_id="project-critical",
            cost_usd=Decimal("10.00")
        )

        # Verify critical event was published
        assert mock_event_dispatcher.publish_event.called
        call_kwargs = mock_event_dispatcher.publish_event.call_args[1]
        assert call_kwargs["data"]["alert_type"] == "critical"

    @pytest.mark.asyncio
    async def test_budget_alert_exceeded_event(self, mock_db_pool, calculator):
        """Test exceeded budget alert event"""
        pool, conn = mock_db_pool
        mock_event_dispatcher = AsyncMock()

        tracker = CostTracker(
            db_pool=pool,
            calculator=calculator,
            event_dispatcher=mock_event_dispatcher
        )

        budget_id = uuid4()
        tenant_id = uuid4()

        conn.fetch.return_value = [{
            "budget_id": budget_id,
            "exceeded": True,
            "alert_type": "exceeded"
        }]

        conn.fetchrow.return_value = {
            "budget_type": "weekly",
            "budget_amount_usd": Decimal("500.00"),
            "current_spend_usd": Decimal("520.00"),
            "alert_threshold_pct": 80,
            "critical_threshold_pct": 95,
            "tenant_id": tenant_id,
            "user_id": None,
            "project_id": None
        }

        await tracker._check_budgets(
            conn=conn,
            tenant_id=tenant_id,
            user_id=None,
            project_id=None,
            cost_usd=Decimal("25.00")
        )

        # Verify exceeded event was published
        assert mock_event_dispatcher.publish_event.called
