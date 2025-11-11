"""
Unit tests for SchedulerClient
"""
import pytest
from unittest.mock import Mock, patch
from temponest_sdk.scheduler import SchedulerClient
from temponest_sdk.client import BaseClient
from temponest_sdk.models import ScheduledTask, TaskExecution
from temponest_sdk.exceptions import ScheduleNotFoundError


class TestSchedulerClientCreate:
    """Test schedule creation"""

    def test_create_schedule(self, clean_env, mock_schedule_data):
        """Test creating a scheduled task"""
        with patch.object(BaseClient, 'post', return_value=mock_schedule_data):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            schedule = scheduler_client.create(
                agent_id="agent-123",
                cron_expression="0 9 * * *",
                task_config={"message": "Daily report"}
            )

            assert isinstance(schedule, ScheduledTask)
            assert schedule.id == "schedule-123"
            assert schedule.cron_expression == "0 9 * * *"


class TestSchedulerClientGet:
    """Test getting schedule"""

    def test_get_schedule_success(self, clean_env, mock_schedule_data):
        """Test getting schedule by ID"""
        with patch.object(BaseClient, 'get', return_value=mock_schedule_data):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            schedule = scheduler_client.get("schedule-123")

            assert isinstance(schedule, ScheduledTask)
            assert schedule.id == "schedule-123"

    def test_get_schedule_not_found(self, clean_env):
        """Test getting non-existent schedule"""
        with patch.object(BaseClient, 'get', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            with pytest.raises(ScheduleNotFoundError):
                scheduler_client.get("schedule-123")


class TestSchedulerClientList:
    """Test listing schedules"""

    def test_list_schedules_default(self, clean_env, mock_schedule_data):
        """Test listing schedules with default parameters"""
        with patch.object(BaseClient, 'get', return_value=[mock_schedule_data]):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            schedules = scheduler_client.list()

            assert len(schedules) == 1
            assert isinstance(schedules[0], ScheduledTask)

    def test_list_schedules_by_agent(self, clean_env, mock_schedule_data):
        """Test listing schedules filtered by agent"""
        with patch.object(BaseClient, 'get', return_value=[mock_schedule_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            schedules = scheduler_client.list(agent_id="agent-123")

            call_args = mock_get.call_args
            assert call_args[1]['params']['agent_id'] == "agent-123"

    def test_list_schedules_by_active_status(self, clean_env, mock_schedule_data):
        """Test listing schedules filtered by active status"""
        with patch.object(BaseClient, 'get', return_value=[mock_schedule_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            schedules = scheduler_client.list(is_active=True)

            call_args = mock_get.call_args
            assert call_args[1]['params']['is_active'] == True


class TestSchedulerClientUpdate:
    """Test updating schedule"""

    def test_pause_schedule(self, clean_env, mock_schedule_data):
        """Test pausing a schedule"""
        paused_data = {**mock_schedule_data, "is_active": False}
        with patch.object(BaseClient, 'patch', return_value=paused_data):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            schedule = scheduler_client.pause("schedule-123")

            assert schedule.is_active == False

    def test_resume_schedule(self, clean_env, mock_schedule_data):
        """Test resuming a schedule"""
        with patch.object(BaseClient, 'patch', return_value=mock_schedule_data):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            schedule = scheduler_client.resume("schedule-123")

            assert schedule.is_active == True

    def test_trigger_schedule(self, clean_env, mock_task_execution_data):
        """Test manually triggering a schedule"""
        with patch.object(BaseClient, 'post', return_value=mock_task_execution_data):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            execution = scheduler_client.trigger("schedule-123")

            assert isinstance(execution, TaskExecution)
            assert execution.task_id == "schedule-123"


class TestSchedulerClientDelete:
    """Test deleting schedule"""

    def test_delete_schedule_success(self, clean_env):
        """Test deleting a schedule"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            scheduler_client.delete("schedule-123")
            # No exception means success

    def test_delete_schedule_not_found(self, clean_env):
        """Test deleting non-existent schedule"""
        with patch.object(BaseClient, 'delete', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            with pytest.raises(ScheduleNotFoundError):
                scheduler_client.delete("schedule-123")


class TestSchedulerClientExecutions:
    """Test execution management"""

    def test_get_executions(self, clean_env, mock_task_execution_data):
        """Test getting executions for a schedule"""
        with patch.object(BaseClient, 'get', return_value=[mock_task_execution_data]):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            executions = scheduler_client.get_executions("schedule-123")

            assert len(executions) == 1
            assert isinstance(executions[0], TaskExecution)
            assert executions[0].id == "task-exec-123"

    def test_get_executions_with_pagination(self, clean_env, mock_task_execution_data):
        """Test getting executions with pagination"""
        with patch.object(BaseClient, 'get', return_value=[mock_task_execution_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            executions = scheduler_client.get_executions("schedule-123", skip=10, limit=20)

            assert len(executions) == 1
            call_args = mock_get.call_args
            assert call_args[1]['params']['skip'] == 10
            assert call_args[1]['params']['limit'] == 20

    def test_get_executions_empty(self, clean_env):
        """Test getting executions returns empty list"""
        with patch.object(BaseClient, 'get', return_value=[]):
            client = BaseClient(base_url="http://test.com")
            scheduler_client = SchedulerClient(client)

            executions = scheduler_client.get_executions("schedule-123")

            assert len(executions) == 0
            assert executions == []
