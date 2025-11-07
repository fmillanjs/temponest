"""
Unit tests for schedule CRUD operations
"""
import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4


@pytest.mark.unit
class TestCreateScheduledTask:
    """Tests for creating scheduled tasks"""

    @pytest.mark.asyncio
    async def test_create_cron_schedule_success(self, db_manager, clean_db, cron_schedule_data):
        """Test creating a cron schedule"""
        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)

        assert isinstance(task_id, UUID)

        # Verify task was created
        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])
        assert task is not None
        assert task["name"] == cron_schedule_data["name"]
        assert task["schedule_type"] == "cron"
        assert task["cron_expression"] == cron_schedule_data["cron_expression"]
        assert task["agent_name"] == cron_schedule_data["agent_name"]

    @pytest.mark.asyncio
    async def test_create_interval_schedule_success(self, db_manager, clean_db, interval_schedule_data):
        """Test creating an interval schedule"""
        task_id = await db_manager.create_scheduled_task(**interval_schedule_data)

        assert isinstance(task_id, UUID)

        # Verify task was created
        task = await db_manager.get_scheduled_task(task_id, interval_schedule_data["tenant_id"])
        assert task is not None
        assert task["schedule_type"] == "interval"
        assert task["interval_seconds"] == interval_schedule_data["interval_seconds"]

    @pytest.mark.asyncio
    async def test_create_once_schedule_success(self, db_manager, clean_db, once_schedule_data):
        """Test creating a one-time schedule"""
        task_id = await db_manager.create_scheduled_task(**once_schedule_data)

        assert isinstance(task_id, UUID)

        # Verify task was created
        task = await db_manager.get_scheduled_task(task_id, once_schedule_data["tenant_id"])
        assert task is not None
        assert task["schedule_type"] == "once"
        assert task["scheduled_time"] is not None

    @pytest.mark.asyncio
    async def test_create_schedule_with_project_and_workflow(
        self, db_manager, clean_db, cron_schedule_data
    ):
        """Test creating a schedule with project and workflow IDs"""
        cron_schedule_data.update({
            "project_id": "project-123",
            "workflow_id": "workflow-456"
        })

        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)

        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])
        assert task["project_id"] == "project-123"
        assert task["workflow_id"] == "workflow-456"

    @pytest.mark.asyncio
    async def test_create_schedule_with_custom_retry_settings(
        self, db_manager, clean_db, cron_schedule_data
    ):
        """Test creating a schedule with custom retry settings"""
        cron_schedule_data.update({
            "max_retries": 5,
            "retry_delay_seconds": 120,
            "timeout_seconds": 600
        })

        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)

        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])
        assert task["max_retries"] == 5
        assert task["retry_delay_seconds"] == 120
        assert task["timeout_seconds"] == 600

    @pytest.mark.asyncio
    async def test_create_inactive_schedule(self, db_manager, clean_db, cron_schedule_data):
        """Test creating an inactive schedule"""
        cron_schedule_data["is_active"] = False

        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)

        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])
        assert task["is_active"] is False

    @pytest.mark.asyncio
    async def test_create_paused_schedule(self, db_manager, clean_db, cron_schedule_data):
        """Test creating a paused schedule"""
        cron_schedule_data["is_paused"] = True

        task_id = await db_manager.create_scheduled_task(**cron_schedule_data)

        task = await db_manager.get_scheduled_task(task_id, cron_schedule_data["tenant_id"])
        assert task["is_paused"] is True


@pytest.mark.unit
class TestGetScheduledTask:
    """Tests for retrieving scheduled tasks"""

    @pytest.mark.asyncio
    async def test_get_task_success(self, db_manager, clean_db, create_test_schedule):
        """Test getting a task by ID"""
        task_id = await create_test_schedule()

        task = await db_manager.get_scheduled_task(
            task_id,
            UUID("11111111-1111-1111-1111-111111111111")
        )

        assert task is not None
        assert task["id"] == task_id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, db_manager, clean_db):
        """Test getting a non-existent task returns None"""
        task = await db_manager.get_scheduled_task(
            uuid4(),
            UUID("11111111-1111-1111-1111-111111111111")
        )

        assert task is None

    @pytest.mark.asyncio
    async def test_get_task_wrong_tenant(self, db_manager, clean_db, create_test_schedule):
        """Test getting a task with wrong tenant ID returns None"""
        task_id = await create_test_schedule()

        task = await db_manager.get_scheduled_task(
            task_id,
            UUID("99999999-9999-9999-9999-999999999999")  # Wrong tenant
        )

        assert task is None


@pytest.mark.unit
class TestListScheduledTasks:
    """Tests for listing scheduled tasks"""

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, db_manager, clean_db, test_tenant_id):
        """Test listing tasks when none exist"""
        tasks, total = await db_manager.list_scheduled_tasks(test_tenant_id)

        assert tasks == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_tasks_multiple(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test listing multiple tasks"""
        # Create 3 tasks
        task_id_1 = await create_test_schedule(name="Task 1")
        task_id_2 = await create_test_schedule(name="Task 2")
        task_id_3 = await create_test_schedule(name="Task 3")

        tasks, total = await db_manager.list_scheduled_tasks(test_tenant_id)

        assert len(tasks) == 3
        assert total == 3
        assert {t["id"] for t in tasks} == {task_id_1, task_id_2, task_id_3}

    @pytest.mark.asyncio
    async def test_list_tasks_pagination(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test task listing pagination"""
        # Create 5 tasks
        for i in range(5):
            await create_test_schedule(name=f"Task {i}")

        # Get first page (2 items)
        tasks_page_1, total = await db_manager.list_scheduled_tasks(
            test_tenant_id, page=1, page_size=2
        )
        assert len(tasks_page_1) == 2
        assert total == 5

        # Get second page (2 items)
        tasks_page_2, total = await db_manager.list_scheduled_tasks(
            test_tenant_id, page=2, page_size=2
        )
        assert len(tasks_page_2) == 2
        assert total == 5

        # Get third page (1 item)
        tasks_page_3, total = await db_manager.list_scheduled_tasks(
            test_tenant_id, page=3, page_size=2
        )
        assert len(tasks_page_3) == 1
        assert total == 5

        # Verify no overlap
        all_ids = {t["id"] for t in tasks_page_1 + tasks_page_2 + tasks_page_3}
        assert len(all_ids) == 5

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_active(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test filtering tasks by active status"""
        # Create active and inactive tasks
        await create_test_schedule(name="Active Task 1", is_active=True)
        await create_test_schedule(name="Active Task 2", is_active=True)
        await create_test_schedule(name="Inactive Task", is_active=False)

        # Get only active tasks
        active_tasks, total = await db_manager.list_scheduled_tasks(
            test_tenant_id, is_active=True
        )
        assert len(active_tasks) == 2
        assert total == 2
        assert all(t["is_active"] for t in active_tasks)

        # Get only inactive tasks
        inactive_tasks, total = await db_manager.list_scheduled_tasks(
            test_tenant_id, is_active=False
        )
        assert len(inactive_tasks) == 1
        assert total == 1
        assert not inactive_tasks[0]["is_active"]

    @pytest.mark.asyncio
    async def test_list_tasks_tenant_isolation(
        self, db_manager, clean_db, create_test_schedule
    ):
        """Test that tasks are isolated by tenant"""
        tenant_1 = UUID("11111111-1111-1111-1111-111111111111")
        tenant_2 = UUID("22222222-2222-2222-2222-222222222222")

        # Create tasks for tenant 1
        await create_test_schedule(name="Tenant 1 Task 1", tenant_id=tenant_1)
        await create_test_schedule(name="Tenant 1 Task 2", tenant_id=tenant_1)

        # Create task for tenant 2
        await create_test_schedule(name="Tenant 2 Task", tenant_id=tenant_2)

        # Verify tenant 1 only sees their tasks
        tenant_1_tasks, total = await db_manager.list_scheduled_tasks(tenant_1)
        assert len(tenant_1_tasks) == 2
        assert total == 2

        # Verify tenant 2 only sees their tasks
        tenant_2_tasks, total = await db_manager.list_scheduled_tasks(tenant_2)
        assert len(tenant_2_tasks) == 1
        assert total == 1


@pytest.mark.unit
class TestUpdateScheduledTask:
    """Tests for updating scheduled tasks"""

    @pytest.mark.asyncio
    async def test_update_task_name(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test updating task name"""
        task_id = await create_test_schedule(name="Old Name")

        success = await db_manager.update_scheduled_task(
            task_id, test_tenant_id, name="New Name"
        )
        assert success is True

        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_task_description(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test updating task description"""
        task_id = await create_test_schedule()

        success = await db_manager.update_scheduled_task(
            task_id, test_tenant_id, description="Updated description"
        )
        assert success is True

        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_task_schedule_config(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test updating schedule configuration"""
        task_id = await create_test_schedule(cron_expression="0 2 * * *")

        success = await db_manager.update_scheduled_task(
            task_id, test_tenant_id, cron_expression="0 3 * * *"
        )
        assert success is True

        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task["cron_expression"] == "0 3 * * *"

    @pytest.mark.asyncio
    async def test_update_task_pause_status(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test pausing and resuming a task"""
        task_id = await create_test_schedule(is_paused=False)

        # Pause the task
        success = await db_manager.update_scheduled_task(
            task_id, test_tenant_id, is_paused=True
        )
        assert success is True

        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task["is_paused"] is True

        # Resume the task
        success = await db_manager.update_scheduled_task(
            task_id, test_tenant_id, is_paused=False
        )
        assert success is True

        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task["is_paused"] is False

    @pytest.mark.asyncio
    async def test_update_task_multiple_fields(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test updating multiple fields at once"""
        task_id = await create_test_schedule()

        updates = {
            "name": "Updated Name",
            "description": "Updated Description",
            "timeout_seconds": 600,
            "max_retries": 5
        }

        success = await db_manager.update_scheduled_task(
            task_id, test_tenant_id, **updates
        )
        assert success is True

        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task["name"] == "Updated Name"
        assert task["description"] == "Updated Description"
        assert task["timeout_seconds"] == 600
        assert task["max_retries"] == 5

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, db_manager, clean_db, test_tenant_id):
        """Test updating a non-existent task returns False"""
        success = await db_manager.update_scheduled_task(
            uuid4(), test_tenant_id, name="New Name"
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_update_task_wrong_tenant(
        self, db_manager, clean_db, create_test_schedule
    ):
        """Test updating a task with wrong tenant ID returns False"""
        task_id = await create_test_schedule()

        success = await db_manager.update_scheduled_task(
            task_id,
            UUID("99999999-9999-9999-9999-999999999999"),  # Wrong tenant
            name="New Name"
        )
        assert success is False


@pytest.mark.unit
class TestDeleteScheduledTask:
    """Tests for deleting scheduled tasks"""

    @pytest.mark.asyncio
    async def test_delete_task_success(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test deleting a task"""
        task_id = await create_test_schedule()

        # Verify task exists
        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task is not None

        # Delete task
        success = await db_manager.delete_scheduled_task(task_id, test_tenant_id)
        assert success is True

        # Verify task is gone
        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, db_manager, clean_db, test_tenant_id):
        """Test deleting a non-existent task returns False"""
        success = await db_manager.delete_scheduled_task(uuid4(), test_tenant_id)
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_task_wrong_tenant(
        self, db_manager, clean_db, create_test_schedule
    ):
        """Test deleting a task with wrong tenant ID returns False"""
        task_id = await create_test_schedule()

        success = await db_manager.delete_scheduled_task(
            task_id,
            UUID("99999999-9999-9999-9999-999999999999")  # Wrong tenant
        )
        assert success is False

        # Verify task still exists for correct tenant
        task = await db_manager.get_scheduled_task(
            task_id,
            UUID("11111111-1111-1111-1111-111111111111")
        )
        assert task is not None


@pytest.mark.unit
class TestTaskExecutionTracking:
    """Tests for task execution tracking"""

    @pytest.mark.asyncio
    async def test_get_execution_count_new_task(
        self, db_manager, clean_db, create_test_schedule
    ):
        """Test getting execution count for a new task"""
        task_id = await create_test_schedule()

        count = await db_manager.get_task_execution_count(task_id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_update_next_execution_time(
        self, db_manager, clean_db, create_test_schedule, test_tenant_id
    ):
        """Test updating next execution time"""
        task_id = await create_test_schedule()

        next_execution = datetime.utcnow() + timedelta(hours=1)
        await db_manager.update_next_execution_time(task_id, next_execution)

        task = await db_manager.get_scheduled_task(task_id, test_tenant_id)
        assert task["next_execution_at"] is not None
        # Check it's within 5 seconds (to account for execution time)
        time_diff = abs((task["next_execution_at"] - next_execution).total_seconds())
        assert time_diff < 5
