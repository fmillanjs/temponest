"""
Integration tests for Schedule API endpoints
"""
import pytest
import httpx
from datetime import datetime, timedelta
from uuid import uuid4


@pytest.mark.integration
class TestCreateScheduleEndpoint:
    """Tests for POST /schedules endpoint"""

    @pytest.mark.asyncio
    async def test_create_cron_schedule(self, test_client, clean_db):
        """Test creating a cron schedule via API"""
        payload = {
            "name": "Daily Backup",
            "description": "Backup database daily",
            "schedule_type": "cron",
            "cron_expression": "0 2 * * *",
            "timezone": "UTC",
            "agent_name": "devops",
            "task_payload": {
                "task": "Run database backup",
                "context": {"database": "production"}
            },
            "timeout_seconds": 600,
            "max_retries": 3,
            "retry_delay_seconds": 60
        }

        response = await test_client.post("/schedules", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["schedule_type"] == "cron"
        assert data["cron_expression"] == payload["cron_expression"]
        assert data["agent_name"] == payload["agent_name"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_interval_schedule(self, test_client, clean_db):
        """Test creating an interval schedule via API"""
        payload = {
            "name": "Hourly Check",
            "schedule_type": "interval",
            "interval_seconds": 3600,
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "Check system status"}
        }

        response = await test_client.post("/schedules", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["schedule_type"] == "interval"
        assert data["interval_seconds"] == 3600

    @pytest.mark.asyncio
    async def test_create_once_schedule(self, test_client, clean_db):
        """Test creating a one-time schedule via API"""
        scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        payload = {
            "name": "One-time Deployment",
            "schedule_type": "once",
            "scheduled_time": scheduled_time,
            "timezone": "UTC",
            "agent_name": "devops",
            "task_payload": {"task": "Deploy application"}
        }

        response = await test_client.post("/schedules", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["schedule_type"] == "once"

    @pytest.mark.asyncio
    async def test_create_schedule_validation_cron_missing(self, test_client, clean_db):
        """Test validation error when cron_expression is missing for cron type"""
        payload = {
            "name": "Invalid Cron",
            "schedule_type": "cron",
            # Missing cron_expression
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "Test"}
        }

        response = await test_client.post("/schedules", json=payload)

        assert response.status_code == 400
        assert "cron_expression required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_schedule_validation_interval_missing(self, test_client, clean_db):
        """Test validation error when interval_seconds is missing for interval type"""
        payload = {
            "name": "Invalid Interval",
            "schedule_type": "interval",
            # Missing interval_seconds
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "Test"}
        }

        response = await test_client.post("/schedules", json=payload)

        assert response.status_code == 400
        assert "interval_seconds required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_schedule_validation_once_missing(self, test_client, clean_db):
        """Test validation error when scheduled_time is missing for once type"""
        payload = {
            "name": "Invalid Once",
            "schedule_type": "once",
            # Missing scheduled_time
            "timezone": "UTC",
            "agent_name": "developer",
            "task_payload": {"task": "Test"}
        }

        response = await test_client.post("/schedules", json=payload)

        assert response.status_code == 400
        assert "scheduled_time required" in response.json()["detail"]


@pytest.mark.integration
class TestListSchedulesEndpoint:
    """Tests for GET /schedules endpoint"""

    @pytest.mark.asyncio
    async def test_list_schedules_empty(self, test_client, clean_db):
        """Test listing schedules when none exist"""
        response = await test_client.get("/schedules")

        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 50

    @pytest.mark.asyncio
    async def test_list_schedules_multiple(self, test_client, clean_db, create_test_schedule):
        """Test listing multiple schedules"""
        # Create 3 schedules
        await create_test_schedule(name="Task 1")
        await create_test_schedule(name="Task 2")
        await create_test_schedule(name="Task 3")

        response = await test_client.get("/schedules")

        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_schedules_pagination(self, test_client, clean_db, create_test_schedule):
        """Test schedule listing with pagination"""
        # Create 5 schedules
        for i in range(5):
            await create_test_schedule(name=f"Task {i}")

        # Get first page
        response = await test_client.get("/schedules?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1

        # Get second page
        response = await test_client.get("/schedules?page=2&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 5
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_list_schedules_filter_active(self, test_client, clean_db, create_test_schedule):
        """Test filtering schedules by active status"""
        # Create active and inactive schedules
        await create_test_schedule(name="Active 1", is_active=True)
        await create_test_schedule(name="Active 2", is_active=True)
        await create_test_schedule(name="Inactive", is_active=False)

        # Get only active
        response = await test_client.get("/schedules?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert all(t["is_active"] for t in data["tasks"])

        # Get only inactive
        response = await test_client.get("/schedules?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert not data["tasks"][0]["is_active"]


@pytest.mark.integration
class TestGetScheduleEndpoint:
    """Tests for GET /schedules/{task_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_schedule_success(self, test_client, clean_db, create_test_schedule):
        """Test getting a schedule by ID"""
        task_id = await create_test_schedule(name="Test Task")

        response = await test_client.get(f"/schedules/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task_id)
        assert data["name"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, test_client, clean_db):
        """Test getting a non-existent schedule returns 404"""
        response = await test_client.get(f"/schedules/{uuid4()}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
class TestUpdateScheduleEndpoint:
    """Tests for PATCH /schedules/{task_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_schedule_name(self, test_client, clean_db, create_test_schedule):
        """Test updating schedule name"""
        task_id = await create_test_schedule(name="Old Name")

        response = await test_client.patch(
            f"/schedules/{task_id}",
            json={"name": "New Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_schedule_cron_expression(self, test_client, clean_db, create_test_schedule):
        """Test updating cron expression"""
        task_id = await create_test_schedule(cron_expression="0 2 * * *")

        response = await test_client.patch(
            f"/schedules/{task_id}",
            json={"cron_expression": "0 3 * * *"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cron_expression"] == "0 3 * * *"

    @pytest.mark.asyncio
    async def test_update_schedule_multiple_fields(self, test_client, clean_db, create_test_schedule):
        """Test updating multiple fields at once"""
        task_id = await create_test_schedule()

        updates = {
            "name": "Updated Name",
            "description": "Updated Description",
            "timeout_seconds": 600
        }

        response = await test_client.patch(f"/schedules/{task_id}", json=updates)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated Description"
        assert data["timeout_seconds"] == 600

    @pytest.mark.asyncio
    async def test_update_schedule_not_found(self, test_client, clean_db):
        """Test updating a non-existent schedule returns 404"""
        response = await test_client.patch(
            f"/schedules/{uuid4()}",
            json={"name": "New Name"}
        )

        assert response.status_code == 404


@pytest.mark.integration
class TestDeleteScheduleEndpoint:
    """Tests for DELETE /schedules/{task_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_schedule_success(self, test_client, clean_db, create_test_schedule):
        """Test deleting a schedule"""
        task_id = await create_test_schedule()

        response = await test_client.delete(f"/schedules/{task_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await test_client.get(f"/schedules/{task_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_schedule_not_found(self, test_client, clean_db):
        """Test deleting a non-existent schedule returns 404"""
        response = await test_client.delete(f"/schedules/{uuid4()}")

        assert response.status_code == 404


@pytest.mark.integration
class TestPauseResumeScheduleEndpoints:
    """Tests for POST /schedules/{task_id}/pause and /resume endpoints"""

    @pytest.mark.asyncio
    async def test_pause_schedule(self, test_client, clean_db, create_test_schedule):
        """Test pausing a schedule"""
        task_id = await create_test_schedule(is_paused=False)

        response = await test_client.post(f"/schedules/{task_id}/pause")

        assert response.status_code == 200
        data = response.json()
        assert data["is_paused"] is True

    @pytest.mark.asyncio
    async def test_resume_schedule(self, test_client, clean_db, create_test_schedule):
        """Test resuming a paused schedule"""
        task_id = await create_test_schedule(is_paused=True)

        response = await test_client.post(f"/schedules/{task_id}/resume")

        assert response.status_code == 200
        data = response.json()
        assert data["is_paused"] is False

    @pytest.mark.asyncio
    async def test_pause_schedule_not_found(self, test_client, clean_db):
        """Test pausing a non-existent schedule returns 404"""
        response = await test_client.post(f"/schedules/{uuid4()}/pause")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_resume_schedule_not_found(self, test_client, clean_db):
        """Test resuming a non-existent schedule returns 404"""
        response = await test_client.post(f"/schedules/{uuid4()}/resume")

        assert response.status_code == 404


@pytest.mark.integration
class TestTriggerScheduleEndpoint:
    """Tests for POST /schedules/{task_id}/trigger endpoint"""

    @pytest.mark.asyncio
    async def test_trigger_schedule_success(
        self,
        test_client,
        clean_db,
        create_test_schedule,
        mock_agent_service,
        mock_agent_success_response
    ):
        """Test manually triggering a schedule"""
        task_id = await create_test_schedule(is_active=True)

        # Mock agent service
        mock_agent_service.post("/agents/developer/execute").mock(
            return_value=httpx.Response(200, json=mock_agent_success_response)
        )

        response = await test_client.post(f"/schedules/{task_id}/trigger")

        assert response.status_code == 202
        assert "triggered successfully" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_trigger_schedule_inactive(self, test_client, clean_db, create_test_schedule):
        """Test triggering an inactive schedule fails"""
        task_id = await create_test_schedule(is_active=False)

        response = await test_client.post(f"/schedules/{task_id}/trigger")

        assert response.status_code == 404
        assert "not active" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_schedule_not_found(self, test_client, clean_db):
        """Test triggering a non-existent schedule returns 404"""
        response = await test_client.post(f"/schedules/{uuid4()}/trigger")

        assert response.status_code == 404


@pytest.mark.integration
class TestListTaskExecutionsEndpoint:
    """Tests for GET /schedules/{task_id}/executions endpoint"""

    @pytest.mark.asyncio
    async def test_list_executions_empty(self, test_client, clean_db, create_test_schedule):
        """Test listing executions when none exist"""
        task_id = await create_test_schedule()

        response = await test_client.get(f"/schedules/{task_id}/executions")

        assert response.status_code == 200
        data = response.json()
        assert data["executions"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_executions_multiple(
        self,
        test_client,
        clean_db,
        create_test_schedule,
        create_test_execution
    ):
        """Test listing multiple executions"""
        task_id = await create_test_schedule()

        # Create 3 executions
        for i in range(3):
            await create_test_execution(task_id, execution_number=i+1)

        response = await test_client.get(f"/schedules/{task_id}/executions")

        assert response.status_code == 200
        data = response.json()
        assert len(data["executions"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_executions_pagination(
        self,
        test_client,
        clean_db,
        create_test_schedule,
        create_test_execution
    ):
        """Test execution listing with pagination"""
        task_id = await create_test_schedule()

        # Create 5 executions
        for i in range(5):
            await create_test_execution(task_id, execution_number=i+1)

        # Get first page
        response = await test_client.get(f"/schedules/{task_id}/executions?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["executions"]) == 2
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_list_executions_task_not_found(self, test_client, clean_db):
        """Test listing executions for non-existent task returns 404"""
        response = await test_client.get(f"/schedules/{uuid4()}/executions")

        assert response.status_code == 404
