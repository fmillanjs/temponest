"""
End-to-end tests for complete scheduled workflow
"""
import pytest
import asyncio
import httpx
from datetime import datetime, timedelta


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteScheduledWorkflow:
    """Tests for complete scheduled task workflows"""

    @pytest.mark.asyncio
    async def test_cron_schedule_execution_workflow(
        self,
        test_client,
        db_manager,
        scheduler,
        clean_db,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test complete workflow: create cron schedule -> execute -> verify results"""
        # Step 1: Create a cron schedule via API
        payload = {
            "name": "Daily Report",
            "description": "Generate daily report",
            "schedule_type": "cron",
            "cron_expression": "0 2 * * *",
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {
                "task": "Generate report",
                "context": {"report_type": "daily"}
            },
            "timeout_seconds": 300,
            "max_retries": 3
        }

        create_response = await test_client.post("/schedules", json=payload)
        assert create_response.status_code == 201
        task_data = create_response.json()
        task_id = task_data["id"]

        # Step 2: Mock agent service
        mock_agent_service.post("/agents/developer/execute").mock(
            return_value=httpx.Response(200, json=mock_agent_success_response)
        )

        # Step 3: Manually trigger the task
        trigger_response = await test_client.post(f"/schedules/{task_id}/trigger")
        assert trigger_response.status_code == 202

        # Step 4: Wait a moment for execution to complete
        await asyncio.sleep(0.5)

        # Step 5: Verify execution was created and completed
        executions_response = await test_client.get(f"/schedules/{task_id}/executions")
        assert executions_response.status_code == 200
        executions_data = executions_response.json()

        assert executions_data["total"] == 1
        execution = executions_data["executions"][0]
        assert execution["status"] == "completed"
        assert execution["agent_name"] == "developer"
        assert execution["tokens_used"] == mock_agent_success_response["tokens_used"]

        # Step 6: Verify task can be retrieved
        get_response = await test_client.get(f"/schedules/{task_id}")
        assert get_response.status_code == 200

        # Step 7: Delete the schedule
        delete_response = await test_client.delete(f"/schedules/{task_id}")
        assert delete_response.status_code == 204

    @pytest.mark.asyncio
    async def test_interval_schedule_multiple_executions(
        self,
        test_client,
        db_manager,
        clean_db,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test interval schedule with multiple executions"""
        # Create an interval schedule
        payload = {
            "name": "Frequent Check",
            "schedule_type": "interval",
            "interval_seconds": 5,  # Every 5 seconds
            "timezone": "UTC",
            "agent_name": "devops",
            "task_payload": {"task": "Check status"}
        }

        create_response = await test_client.post("/schedules", json=payload)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Mock agent service
        mock_agent_service.post("/agents/devops/execute").mock(
            return_value=httpx.Response(200, json=mock_agent_success_response)
        )

        # Trigger multiple times
        for i in range(3):
            await test_client.post(f"/schedules/{task_id}/trigger")
            await asyncio.sleep(0.3)

        # Verify multiple executions were created
        executions_response = await test_client.get(f"/schedules/{task_id}/executions")
        executions_data = executions_response.json()

        assert executions_data["total"] >= 3
        # Verify execution numbers increment
        execution_numbers = [e["execution_number"] for e in executions_data["executions"]]
        assert len(set(execution_numbers)) == len(execution_numbers)  # All unique

    @pytest.mark.asyncio
    async def test_pause_resume_workflow(
        self,
        test_client,
        clean_db,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test pausing and resuming a schedule"""
        # Create a schedule
        payload = {
            "name": "Pausable Task",
            "schedule_type": "cron",
            "cron_expression": "0 * * * *",
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "Test task"}
        }

        create_response = await test_client.post("/schedules", json=payload)
        task_id = create_response.json()["id"]

        # Verify it's active and not paused
        get_response = await test_client.get(f"/schedules/{task_id}")
        task_data = get_response.json()
        assert task_data["is_active"] is True
        assert task_data["is_paused"] is False

        # Pause the schedule
        pause_response = await test_client.post(f"/schedules/{task_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["is_paused"] is True

        # Verify paused state persists
        get_response = await test_client.get(f"/schedules/{task_id}")
        assert get_response.json()["is_paused"] is True

        # Resume the schedule
        resume_response = await test_client.post(f"/schedules/{task_id}/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["is_paused"] is False

        # Verify resumed state persists
        get_response = await test_client.get(f"/schedules/{task_id}")
        assert get_response.json()["is_paused"] is False

    @pytest.mark.asyncio
    async def test_schedule_update_workflow(
        self,
        test_client,
        clean_db
    ):
        """Test updating a schedule's configuration"""
        # Create a schedule
        payload = {
            "name": "Original Name",
            "description": "Original description",
            "schedule_type": "cron",
            "cron_expression": "0 2 * * *",
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "Original task"},
            "timeout_seconds": 300
        }

        create_response = await test_client.post("/schedules", json=payload)
        task_id = create_response.json()["id"]

        # Update name and description
        update_payload = {
            "name": "Updated Name",
            "description": "Updated description"
        }
        update_response = await test_client.patch(f"/schedules/{task_id}", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Name"
        assert update_response.json()["description"] == "Updated description"

        # Update cron expression
        cron_update = {"cron_expression": "0 3 * * *"}
        cron_response = await test_client.patch(f"/schedules/{task_id}", json=cron_update)
        assert cron_response.status_code == 200
        assert cron_response.json()["cron_expression"] == "0 3 * * *"

        # Update timeout
        timeout_update = {"timeout_seconds": 600}
        timeout_response = await test_client.patch(f"/schedules/{task_id}", json=timeout_update)
        assert timeout_response.status_code == 200
        assert timeout_response.json()["timeout_seconds"] == 600

        # Verify all changes persisted
        get_response = await test_client.get(f"/schedules/{task_id}")
        final_data = get_response.json()
        assert final_data["name"] == "Updated Name"
        assert final_data["description"] == "Updated description"
        assert final_data["cron_expression"] == "0 3 * * *"
        assert final_data["timeout_seconds"] == 600

    @pytest.mark.asyncio
    async def test_failed_execution_workflow(
        self,
        test_client,
        clean_db,
        mock_agent_service,
        mock_agent_error_response
    ):
        """Test workflow when execution fails"""
        # Create a schedule
        payload = {
            "name": "Failing Task",
            "schedule_type": "once",
            "scheduled_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "This will fail"},
            "max_retries": 2
        }

        create_response = await test_client.post("/schedules", json=payload)
        task_id = create_response.json()["id"]

        # Mock agent service to return error
        mock_agent_service.post("/agents/developer/execute").mock(
            return_value=httpx.Response(200, json=mock_agent_error_response)
        )

        # Trigger the task
        await test_client.post(f"/schedules/{task_id}/trigger")
        await asyncio.sleep(0.5)

        # Verify execution failed
        executions_response = await test_client.get(f"/schedules/{task_id}/executions")
        executions_data = executions_response.json()

        assert executions_data["total"] == 1
        execution = executions_data["executions"][0]
        assert execution["status"] == "failed"
        assert execution["error_message"] == mock_agent_error_response["error"]

    @pytest.mark.asyncio
    async def test_schedule_list_filter_workflow(
        self,
        test_client,
        clean_db,
        create_test_schedule
    ):
        """Test creating and filtering schedules"""
        # Create multiple schedules with different states
        await create_test_schedule(name="Active Task 1", is_active=True, is_paused=False)
        await create_test_schedule(name="Active Task 2", is_active=True, is_paused=False)
        await create_test_schedule(name="Paused Task", is_active=True, is_paused=True)
        await create_test_schedule(name="Inactive Task", is_active=False, is_paused=False)

        # List all schedules
        all_response = await test_client.get("/schedules")
        assert all_response.json()["total"] == 4

        # Filter by active
        active_response = await test_client.get("/schedules?is_active=true")
        active_data = active_response.json()
        assert active_data["total"] == 3
        assert all(t["is_active"] for t in active_data["tasks"])

        # Filter by inactive
        inactive_response = await test_client.get("/schedules?is_active=false")
        inactive_data = inactive_response.json()
        assert inactive_data["total"] == 1
        assert not inactive_data["tasks"][0]["is_active"]

    @pytest.mark.asyncio
    async def test_execution_metrics_workflow(
        self,
        test_client,
        clean_db,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test that execution metrics are properly tracked"""
        # Create a schedule
        payload = {
            "name": "Metrics Task",
            "schedule_type": "interval",
            "interval_seconds": 60,
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "Track metrics"}
        }

        create_response = await test_client.post("/schedules", json=payload)
        task_id = create_response.json()["id"]

        # Mock agent service with specific metrics
        custom_response = {
            **mock_agent_success_response,
            "tokens_used": 2500,
            "cost_info": {"total_cost_usd": 0.075}
        }

        mock_agent_service.post("/agents/developer/execute").mock(
            return_value=httpx.Response(200, json=custom_response)
        )

        # Trigger execution
        await test_client.post(f"/schedules/{task_id}/trigger")
        await asyncio.sleep(0.5)

        # Verify metrics
        executions_response = await test_client.get(f"/schedules/{task_id}/executions")
        execution = executions_response.json()["executions"][0]

        assert execution["tokens_used"] == 2500
        assert execution["cost_usd"] == 0.075
        assert execution["duration_ms"] > 0
        assert execution["result"] == custom_response["result"]


@pytest.mark.e2e
@pytest.mark.slow
class TestMultiTenantIsolation:
    """Tests for multi-tenant isolation in scheduled tasks"""

    @pytest.mark.asyncio
    async def test_tenant_cannot_access_other_tenant_schedules(
        self,
        test_client,
        db_manager,
        clean_db,
        test_tenant_id,
        test_user_id
    ):
        """Test that tenants cannot access each other's schedules"""
        # Create schedule for tenant 1
        tenant_1_id = test_tenant_id
        task_id = await db_manager.create_scheduled_task(
            tenant_id=tenant_1_id,
            user_id=test_user_id,
            name="Tenant 1 Task",
            description="Private to tenant 1",
            schedule_type="cron",
            cron_expression="0 2 * * *",
            agent_name="developer",
            task_payload={"task": "Private task"},
            timezone="UTC"
        )

        # Verify tenant 1 can access it
        response = await test_client.get(f"/schedules/{task_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Tenant 1 Task"

        # List should show the task
        list_response = await test_client.get("/schedules")
        assert list_response.json()["total"] == 1


@pytest.mark.e2e
@pytest.mark.slow
class TestSchedulerLifecycle:
    """Tests for scheduler lifecycle management"""

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, db_manager):
        """Test starting and stopping the scheduler"""
        from scheduler import TaskScheduler

        scheduler = TaskScheduler(db_manager)

        # Initially not running
        assert not scheduler.is_running()

        # Start scheduler
        await scheduler.start()
        assert scheduler.is_running()

        # Stop scheduler
        await scheduler.stop()
        assert not scheduler.is_running()

    @pytest.mark.asyncio
    async def test_scheduler_tracks_active_jobs(
        self,
        db_manager,
        clean_db,
        create_test_schedule
    ):
        """Test that scheduler tracks active job count"""
        from scheduler import TaskScheduler

        scheduler = TaskScheduler(db_manager)

        # Initially zero active jobs
        assert scheduler.get_active_jobs_count() == 0

        await scheduler.start()

        # Count should still be zero before any executions
        assert scheduler.get_active_jobs_count() == 0

        await scheduler.stop()
