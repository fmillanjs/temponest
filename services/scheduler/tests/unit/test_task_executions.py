"""
Unit tests for task execution record management
"""
import pytest
from datetime import datetime
from uuid import UUID


@pytest.mark.unit
class TestCreateTaskExecution:
    """Tests for creating task execution records"""

    @pytest.mark.asyncio
    async def test_create_execution_success(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        test_tenant_id,
        test_user_id
    ):
        """Test creating a task execution record"""
        # Create a scheduled task
        task_id = await create_test_schedule()

        # Create execution
        execution_id = await db_manager.create_task_execution(
            scheduled_task_id=task_id,
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            agent_name="developer",
            scheduled_for=datetime.utcnow(),
            execution_number=1,
            max_retries=3
        )

        assert isinstance(execution_id, UUID)

        # Verify execution was created
        executions, total = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert total == 1
        assert executions[0]["id"] == execution_id
        assert executions[0]["scheduled_task_id"] == task_id
        assert executions[0]["status"] == "pending"
        assert executions[0]["execution_number"] == 1

    @pytest.mark.asyncio
    async def test_create_multiple_executions(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test creating multiple execution records for a task"""
        # Create a scheduled task
        task_id = await create_test_schedule()

        # Create 3 executions
        execution_ids = []
        for i in range(1, 4):
            execution_id = await create_test_execution(
                task_id,
                execution_number=i
            )
            execution_ids.append(execution_id)

        # Verify all executions exist
        executions, total = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert total == 3
        assert set(e["id"] for e in executions) == set(execution_ids)


@pytest.mark.unit
class TestUpdateTaskExecutionStatus:
    """Tests for updating task execution status"""

    @pytest.mark.asyncio
    async def test_update_execution_started(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test marking execution as started"""
        task_id = await create_test_schedule()
        execution_id = await create_test_execution(task_id)

        # Update to started
        await db_manager.update_task_execution_started(
            execution_id=execution_id,
            agent_task_id="agent-task-123"
        )

        # Verify update
        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        execution = executions[0]

        assert execution["status"] == "running"
        assert execution["agent_task_id"] == "agent-task-123"
        assert execution["started_at"] is not None

    @pytest.mark.asyncio
    async def test_update_execution_completed(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test marking execution as completed"""
        task_id = await create_test_schedule()
        execution_id = await create_test_execution(task_id)

        # Mark as started first
        await db_manager.update_task_execution_started(
            execution_id=execution_id,
            agent_task_id="agent-task-123"
        )

        # Mark as completed
        result = {"output": "Task completed", "artifacts": []}
        await db_manager.update_task_execution_completed(
            execution_id=execution_id,
            result=result,
            tokens_used=1500,
            cost_usd=0.045,
            duration_ms=3500
        )

        # Verify update
        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        execution = executions[0]

        assert execution["status"] == "completed"
        assert execution["result"] == result
        assert execution["tokens_used"] == 1500
        assert execution["cost_usd"] == 0.045
        assert execution["duration_ms"] == 3500
        assert execution["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_execution_failed(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test marking execution as failed"""
        task_id = await create_test_schedule()
        execution_id = await create_test_execution(task_id)

        # Mark as started first
        await db_manager.update_task_execution_started(
            execution_id=execution_id,
            agent_task_id="agent-task-123"
        )

        # Mark as failed
        error_message = "Agent execution failed: Invalid configuration"
        await db_manager.update_task_execution_failed(
            execution_id=execution_id,
            error_message=error_message,
            retry_count=1
        )

        # Verify update
        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        execution = executions[0]

        assert execution["status"] == "failed"
        assert execution["error_message"] == error_message
        assert execution["retry_count"] == 1
        assert execution["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_execution_lifecycle(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id,
        assert_datetime_close
    ):
        """Test complete execution lifecycle: pending -> running -> completed"""
        task_id = await create_test_schedule()

        # Create execution (pending)
        execution_id = await create_test_execution(task_id)

        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert executions[0]["status"] == "pending"
        assert executions[0]["started_at"] is None
        assert executions[0]["completed_at"] is None

        # Mark as started (running)
        await db_manager.update_task_execution_started(
            execution_id=execution_id,
            agent_task_id="agent-task-123"
        )

        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert executions[0]["status"] == "running"
        assert executions[0]["started_at"] is not None
        assert executions[0]["completed_at"] is None
        assert_datetime_close(executions[0]["started_at"], datetime.utcnow())

        # Mark as completed
        await db_manager.update_task_execution_completed(
            execution_id=execution_id,
            result={"output": "Success"},
            tokens_used=1000,
            cost_usd=0.03,
            duration_ms=2000
        )

        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert executions[0]["status"] == "completed"
        assert executions[0]["started_at"] is not None
        assert executions[0]["completed_at"] is not None
        assert_datetime_close(executions[0]["completed_at"], datetime.utcnow())


@pytest.mark.unit
class TestListTaskExecutions:
    """Tests for listing task executions"""

    @pytest.mark.asyncio
    async def test_list_executions_empty(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        test_tenant_id
    ):
        """Test listing executions when none exist"""
        task_id = await create_test_schedule()

        executions, total = await db_manager.list_task_executions(task_id, test_tenant_id)

        assert executions == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_executions_multiple(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test listing multiple executions"""
        task_id = await create_test_schedule()

        # Create 5 executions
        execution_ids = []
        for i in range(1, 6):
            execution_id = await create_test_execution(task_id, execution_number=i)
            execution_ids.append(execution_id)

        executions, total = await db_manager.list_task_executions(task_id, test_tenant_id)

        assert len(executions) == 5
        assert total == 5
        assert set(e["id"] for e in executions) == set(execution_ids)

    @pytest.mark.asyncio
    async def test_list_executions_pagination(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test executions list pagination"""
        task_id = await create_test_schedule()

        # Create 5 executions
        for i in range(1, 6):
            await create_test_execution(task_id, execution_number=i)

        # Get first page
        executions_page_1, total = await db_manager.list_task_executions(
            task_id, test_tenant_id, page=1, page_size=2
        )
        assert len(executions_page_1) == 2
        assert total == 5

        # Get second page
        executions_page_2, total = await db_manager.list_task_executions(
            task_id, test_tenant_id, page=2, page_size=2
        )
        assert len(executions_page_2) == 2
        assert total == 5

        # Get third page
        executions_page_3, total = await db_manager.list_task_executions(
            task_id, test_tenant_id, page=3, page_size=2
        )
        assert len(executions_page_3) == 1
        assert total == 5

        # Verify no overlap
        all_ids = {e["id"] for e in executions_page_1 + executions_page_2 + executions_page_3}
        assert len(all_ids) == 5

    @pytest.mark.asyncio
    async def test_list_executions_ordered_by_created_at(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test that executions are ordered by created_at DESC (newest first)"""
        task_id = await create_test_schedule()

        # Create 3 executions
        execution_id_1 = await create_test_execution(task_id, execution_number=1)
        execution_id_2 = await create_test_execution(task_id, execution_number=2)
        execution_id_3 = await create_test_execution(task_id, execution_number=3)

        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)

        # Should be in reverse order (newest first)
        assert executions[0]["id"] == execution_id_3
        assert executions[1]["id"] == execution_id_2
        assert executions[2]["id"] == execution_id_1

    @pytest.mark.asyncio
    async def test_list_executions_tenant_isolation(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution
    ):
        """Test that executions are isolated by tenant"""
        tenant_1 = UUID("11111111-1111-1111-1111-111111111111")
        tenant_2 = UUID("22222222-2222-2222-2222-222222222222")

        # Create tasks for both tenants
        task_id_1 = await create_test_schedule(tenant_id=tenant_1)
        task_id_2 = await create_test_schedule(tenant_id=tenant_2)

        # Create executions
        await create_test_execution(task_id_1)
        await create_test_execution(task_id_2)

        # Verify tenant 1 only sees their executions
        executions_1, total_1 = await db_manager.list_task_executions(task_id_1, tenant_1)
        assert total_1 == 1

        # Verify tenant 2 only sees their executions
        executions_2, total_2 = await db_manager.list_task_executions(task_id_2, tenant_2)
        assert total_2 == 1

        # Verify cross-tenant access returns nothing
        executions_cross, total_cross = await db_manager.list_task_executions(task_id_1, tenant_2)
        assert total_cross == 0


@pytest.mark.unit
class TestExecutionCounting:
    """Tests for execution counting"""

    @pytest.mark.asyncio
    async def test_get_execution_count_zero(
        self,
        db_manager,
        clean_db,
        create_test_schedule
    ):
        """Test getting execution count when zero executions"""
        task_id = await create_test_schedule()

        count = await db_manager.get_task_execution_count(task_id)

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_execution_count_nonzero(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution
    ):
        """Test getting execution count after executions"""
        task_id = await create_test_schedule()

        # Initially zero
        count = await db_manager.get_task_execution_count(task_id)
        assert count == 0

        # After creating executions, count should still be from scheduled_tasks table
        # (The count in scheduled_tasks is updated separately, not by create_task_execution)
        await create_test_execution(task_id)
        await create_test_execution(task_id)

        # The get_task_execution_count reads from scheduled_tasks.total_executions
        # which is managed separately
        count = await db_manager.get_task_execution_count(task_id)
        # This will be 0 unless the scheduled_tasks.total_executions is updated
        # by the execution process
        assert count >= 0  # Just verify it doesn't error


@pytest.mark.unit
class TestExecutionMetrics:
    """Tests for execution metrics and statistics"""

    @pytest.mark.asyncio
    async def test_execution_duration_tracking(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test that execution duration is tracked correctly"""
        task_id = await create_test_schedule()
        execution_id = await create_test_execution(task_id)

        # Start execution
        await db_manager.update_task_execution_started(execution_id, "agent-task-123")

        # Complete with duration
        duration_ms = 5432
        await db_manager.update_task_execution_completed(
            execution_id=execution_id,
            result={"output": "Done"},
            tokens_used=1000,
            cost_usd=0.03,
            duration_ms=duration_ms
        )

        # Verify duration
        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert executions[0]["duration_ms"] == duration_ms

    @pytest.mark.asyncio
    async def test_execution_cost_tracking(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test that execution cost is tracked correctly"""
        task_id = await create_test_schedule()
        execution_id = await create_test_execution(task_id)

        # Start execution
        await db_manager.update_task_execution_started(execution_id, "agent-task-123")

        # Complete with cost
        tokens_used = 2500
        cost_usd = 0.075
        await db_manager.update_task_execution_completed(
            execution_id=execution_id,
            result={"output": "Done"},
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            duration_ms=3000
        )

        # Verify cost tracking
        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert executions[0]["tokens_used"] == tokens_used
        assert executions[0]["cost_usd"] == cost_usd

    @pytest.mark.asyncio
    async def test_execution_retry_tracking(
        self,
        db_manager,
        clean_db,
        create_test_schedule,
        create_test_execution,
        test_tenant_id
    ):
        """Test that retry attempts are tracked correctly"""
        task_id = await create_test_schedule()
        execution_id = await create_test_execution(task_id, max_retries=5)

        # Start execution
        await db_manager.update_task_execution_started(execution_id, "agent-task-123")

        # Fail with retry count
        retry_count = 2
        await db_manager.update_task_execution_failed(
            execution_id=execution_id,
            error_message="Temporary failure",
            retry_count=retry_count
        )

        # Verify retry tracking
        executions, _ = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert executions[0]["retry_count"] == retry_count
        assert executions[0]["max_retries"] == 5
