"""
Unit tests for job execution logic
"""
import pytest
import asyncio
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import respx


@pytest.mark.unit
class TestExecuteScheduledTask:
    """Tests for _execute_scheduled_task method"""

    @pytest.mark.asyncio
    async def test_execute_task_success(
        self,
        scheduler,
        db_manager,
        clean_db,
        cron_schedule_data,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test successful task execution"""
        # Create a task in the database
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Mock the agent service response
        mock_agent_service.post(
            f"/agents/{task['agent_name']}/execute"
        ).mock(return_value=httpx.Response(200, json=mock_agent_success_response))

        # Execute the task
        await scheduler._execute_scheduled_task(task)

        # Verify execution record was created
        executions, total = await db_manager.list_task_executions(
            task_id,
            cron_schedule_data["tenant_id"]
        )
        assert total == 1
        assert executions[0]["status"] == "completed"
        assert executions[0]["agent_task_id"] == mock_agent_success_response["task_id"]
        assert executions[0]["tokens_used"] == mock_agent_success_response["tokens_used"]
        assert executions[0]["cost_usd"] == mock_agent_success_response["cost_info"]["total_cost_usd"]

    @pytest.mark.asyncio
    async def test_execute_task_agent_failure(
        self,
        scheduler,
        db_manager,
        clean_db,
        cron_schedule_data,
        mock_agent_service,
        mock_agent_error_response
    ):
        """Test task execution when agent returns error"""
        # Create a task in the database
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Mock the agent service to return error
        mock_agent_service.post(
            f"/agents/{task['agent_name']}/execute"
        ).mock(return_value=httpx.Response(200, json=mock_agent_error_response))

        # Execute the task
        await scheduler._execute_scheduled_task(task)

        # Verify execution record shows failure
        executions, total = await db_manager.list_task_executions(
            task_id,
            cron_schedule_data["tenant_id"]
        )
        assert total == 1
        assert executions[0]["status"] == "failed"
        assert executions[0]["error_message"] == mock_agent_error_response["error"]

    @pytest.mark.asyncio
    async def test_execute_task_http_error(
        self,
        scheduler,
        db_manager,
        clean_db,
        cron_schedule_data,
        mock_agent_service
    ):
        """Test task execution when agent service returns HTTP error"""
        # Create a task in the database
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Mock the agent service to return 500 error
        mock_agent_service.post(
            f"/agents/{task['agent_name']}/execute"
        ).mock(return_value=httpx.Response(500, text="Internal Server Error"))

        # Execute the task
        await scheduler._execute_scheduled_task(task)

        # Verify execution record shows failure
        executions, total = await db_manager.list_task_executions(
            task_id,
            cron_schedule_data["tenant_id"]
        )
        assert total == 1
        assert executions[0]["status"] == "failed"
        assert "500" in executions[0]["error_message"]

    @pytest.mark.asyncio
    async def test_execute_task_timeout(
        self,
        scheduler,
        db_manager,
        clean_db,
        cron_schedule_data,
        mock_agent_service
    ):
        """Test task execution when agent service times out"""
        # Create a task with short timeout
        cron_schedule_data["timeout_seconds"] = 1
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Mock the agent service to timeout
        async def delayed_response(request):
            await asyncio.sleep(2)  # Longer than timeout
            return httpx.Response(200, json={"status": "success"})

        mock_agent_service.post(
            f"/agents/{task['agent_name']}/execute"
        ).mock(side_effect=httpx.TimeoutException("Request timeout"))

        # Execute the task
        await scheduler._execute_scheduled_task(task)

        # Verify execution record shows failure with timeout error
        executions, total = await db_manager.list_task_executions(
            task_id,
            cron_schedule_data["tenant_id"]
        )
        assert total == 1
        assert executions[0]["status"] == "failed"
        assert "timeout" in executions[0]["error_message"].lower()

    @pytest.mark.asyncio
    async def test_execute_task_updates_next_execution(
        self,
        scheduler,
        db_manager,
        clean_db,
        cron_schedule_data,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test that next execution time is updated after task execution"""
        # Create a task in the database
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Store original next_execution_at
        original_next_execution = task["next_execution_at"]

        # Mock the agent service
        mock_agent_service.post(
            f"/agents/{task['agent_name']}/execute"
        ).mock(return_value=httpx.Response(200, json=mock_agent_success_response))

        # Execute the task
        await scheduler._execute_scheduled_task(task)

        # Get updated task
        updated_task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Verify next_execution_at was updated
        assert updated_task["next_execution_at"] is not None
        if original_next_execution:
            assert updated_task["next_execution_at"] != original_next_execution

    @pytest.mark.asyncio
    async def test_execute_task_increments_execution_number(
        self,
        scheduler,
        db_manager,
        clean_db,
        cron_schedule_data,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test that execution numbers increment correctly"""
        # Create a task
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Mock the agent service
        mock_agent_service.post(
            f"/agents/{task['agent_name']}/execute"
        ).mock(return_value=httpx.Response(200, json=mock_agent_success_response))

        # Execute the task three times
        for expected_number in [1, 2, 3]:
            await scheduler._execute_scheduled_task(task)

            # Verify execution number
            executions, total = await db_manager.list_task_executions(
                task_id,
                cron_schedule_data["tenant_id"]
            )
            latest_execution = executions[0]  # Most recent first
            assert latest_execution["execution_number"] == expected_number

    @pytest.mark.asyncio
    async def test_execute_task_exception_handling(
        self,
        scheduler,
        db_manager,
        clean_db,
        cron_schedule_data
    ):
        """Test that exceptions during task execution are handled gracefully"""
        # Create a task
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])

        # Mock _call_agent_service to raise an exception
        with patch.object(scheduler, '_call_agent_service', side_effect=Exception("Unexpected error")):
            # Execute the task - should not raise
            await scheduler._execute_scheduled_task(task)

            # Verify execution record shows failure
            executions, total = await db_manager.list_task_executions(
                task_id,
                cron_schedule_data["tenant_id"]
            )
            assert total == 1
            assert executions[0]["status"] == "failed"
            assert "Unexpected error" in executions[0]["error_message"]


@pytest.mark.unit
class TestCallAgentService:
    """Tests for _call_agent_service method"""

    @pytest.mark.asyncio
    async def test_call_agent_service_success(
        self,
        scheduler,
        mock_agent_service,
        mock_agent_success_response,
        test_tenant_id,
        test_user_id,
        test_task_payload
    ):
        """Test successful agent service call"""
        agent_name = "developer"

        # Mock the agent service
        mock_agent_service.post(
            f"/agents/{agent_name}/execute"
        ).mock(return_value=httpx.Response(200, json=mock_agent_success_response))

        # Ensure HTTP client is initialized
        if not scheduler.http_client:
            await scheduler.start()

        result = await scheduler._call_agent_service(
            agent_name=agent_name,
            task_payload=test_task_payload,
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            project_id="test-project",
            workflow_id="test-workflow",
            timeout=300
        )

        assert result["status"] == "success"
        assert result["task_id"] == mock_agent_success_response["task_id"]

        # Clean up
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_call_agent_service_sends_correct_headers(
        self,
        scheduler,
        mock_agent_service,
        mock_agent_success_response,
        test_tenant_id,
        test_user_id,
        test_task_payload
    ):
        """Test that correct headers are sent to agent service"""
        agent_name = "developer"

        # Mock the agent service and capture request
        route = mock_agent_service.post(f"/agents/{agent_name}/execute")
        route.mock(return_value=httpx.Response(200, json=mock_agent_success_response))

        # Ensure HTTP client is initialized
        if not scheduler.http_client:
            await scheduler.start()

        await scheduler._call_agent_service(
            agent_name=agent_name,
            task_payload=test_task_payload,
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            project_id="test-project",
            workflow_id="test-workflow",
            timeout=300
        )

        # Verify request was made with correct headers
        assert route.called
        request = route.calls[0].request
        assert request.headers["X-Tenant-ID"] == str(test_tenant_id)
        assert request.headers["X-User-ID"] == str(test_user_id)

        # Clean up
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_call_agent_service_sends_correct_payload(
        self,
        scheduler,
        mock_agent_service,
        mock_agent_success_response,
        test_tenant_id,
        test_user_id,
        test_task_payload
    ):
        """Test that correct payload is sent to agent service"""
        agent_name = "developer"
        project_id = "test-project-123"
        workflow_id = "test-workflow-456"

        # Mock the agent service
        route = mock_agent_service.post(f"/agents/{agent_name}/execute")
        route.mock(return_value=httpx.Response(200, json=mock_agent_success_response))

        # Ensure HTTP client is initialized
        if not scheduler.http_client:
            await scheduler.start()

        await scheduler._call_agent_service(
            agent_name=agent_name,
            task_payload=test_task_payload,
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            project_id=project_id,
            workflow_id=workflow_id,
            timeout=300
        )

        # Verify request payload
        assert route.called
        request = route.calls[0].request
        import json
        payload = json.loads(request.content)

        assert payload["task"] == test_task_payload["task"]
        assert payload["context"] == test_task_payload["context"]
        assert payload["risk_level"] == test_task_payload["risk_level"]
        assert payload["project_id"] == project_id
        assert payload["workflow_id"] == workflow_id

        # Clean up
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_call_agent_service_http_error(
        self,
        scheduler,
        mock_agent_service,
        test_tenant_id,
        test_user_id,
        test_task_payload
    ):
        """Test handling HTTP errors from agent service"""
        agent_name = "developer"

        # Mock the agent service to return 404
        mock_agent_service.post(
            f"/agents/{agent_name}/execute"
        ).mock(return_value=httpx.Response(404, text="Agent not found"))

        # Ensure HTTP client is initialized
        if not scheduler.http_client:
            await scheduler.start()

        result = await scheduler._call_agent_service(
            agent_name=agent_name,
            task_payload=test_task_payload,
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            project_id="test-project",
            workflow_id="test-workflow",
            timeout=300
        )

        assert result["status"] == "error"
        assert "404" in result["error"]

        # Clean up
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_call_agent_service_timeout_error(
        self,
        scheduler,
        mock_agent_service,
        test_tenant_id,
        test_user_id,
        test_task_payload
    ):
        """Test handling timeout errors from agent service"""
        agent_name = "developer"

        # Mock the agent service to timeout
        mock_agent_service.post(
            f"/agents/{agent_name}/execute"
        ).mock(side_effect=httpx.TimeoutException("Request timeout"))

        # Ensure HTTP client is initialized
        if not scheduler.http_client:
            await scheduler.start()

        result = await scheduler._call_agent_service(
            agent_name=agent_name,
            task_payload=test_task_payload,
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            project_id="test-project",
            workflow_id="test-workflow",
            timeout=300
        )

        assert result["status"] == "error"
        assert "timeout" in result["error"].lower()

        # Clean up
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_call_agent_service_connection_error(
        self,
        scheduler,
        mock_agent_service,
        test_tenant_id,
        test_user_id,
        test_task_payload
    ):
        """Test handling connection errors to agent service"""
        agent_name = "developer"

        # Mock the agent service to raise connection error
        mock_agent_service.post(
            f"/agents/{agent_name}/execute"
        ).mock(side_effect=httpx.ConnectError("Connection refused"))

        # Ensure HTTP client is initialized
        if not scheduler.http_client:
            await scheduler.start()

        result = await scheduler._call_agent_service(
            agent_name=agent_name,
            task_payload=test_task_payload,
            tenant_id=test_tenant_id,
            user_id=test_user_id,
            project_id="test-project",
            workflow_id="test-workflow",
            timeout=300
        )

        assert result["status"] == "error"
        assert "Failed to call agent service" in result["error"]

        # Clean up
        await scheduler.stop()


@pytest.mark.unit
class TestTriggerTaskNow:
    """Tests for trigger_task_now method"""

    @pytest.mark.asyncio
    async def test_trigger_task_now_success(
        self,
        scheduler,
        db_manager,
        clean_db,
        create_test_schedule,
        test_tenant_id,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test manually triggering a task"""
        # Create an active task
        task_id = await create_test_schedule(is_active=True)

        # Mock the agent service
        mock_agent_service.post("/agents/developer/execute").mock(
            return_value=httpx.Response(200, json=mock_agent_success_response)
        )

        # Trigger the task
        success = await scheduler.trigger_task_now(task_id, test_tenant_id)

        assert success is True

        # Verify execution was created
        executions, total = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert total == 1

    @pytest.mark.asyncio
    async def test_trigger_task_now_inactive_task(
        self,
        scheduler,
        db_manager,
        clean_db,
        create_test_schedule,
        test_tenant_id
    ):
        """Test triggering an inactive task fails"""
        # Create an inactive task
        task_id = await create_test_schedule(is_active=False)

        # Try to trigger the task
        success = await scheduler.trigger_task_now(task_id, test_tenant_id)

        assert success is False

        # Verify no execution was created
        executions, total = await db_manager.list_task_executions(task_id, test_tenant_id)
        assert total == 0

    @pytest.mark.asyncio
    async def test_trigger_task_now_not_found(
        self,
        scheduler,
        test_tenant_id
    ):
        """Test triggering a non-existent task fails"""
        # Try to trigger non-existent task
        success = await scheduler.trigger_task_now(uuid4(), test_tenant_id)

        assert success is False
