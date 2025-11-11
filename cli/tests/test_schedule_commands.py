"""
Tests for CLI schedule commands
"""
import pytest
from unittest.mock import patch
from temponest_cli.cli import cli
from temponest_sdk.exceptions import ScheduleNotFoundError


class TestScheduleList:
    """Test schedule list command"""

    def test_list_schedules_success(self, runner, mock_client):
        """Test successful schedule listing"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "list"])

        assert result.exit_code == 0
        assert "Schedules" in result.output
        assert "0 9 * * *" in result.output
        mock_client.scheduler.list.assert_called_once()

    def test_list_schedules_with_limit(self, runner, mock_client):
        """Test schedule listing with custom limit"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "list", "--limit", "10"])

        assert result.exit_code == 0
        mock_client.scheduler.list.assert_called_once()
        call_args = mock_client.scheduler.list.call_args
        assert call_args.kwargs["limit"] == 10

    def test_list_schedules_by_agent(self, runner, mock_client):
        """Test schedule listing filtered by agent"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "schedule", "list",
                "--agent-id", "agent-123",
            ])

        assert result.exit_code == 0
        call_args = mock_client.scheduler.list.call_args
        assert call_args.kwargs["agent_id"] == "agent-123"

    def test_list_schedules_active_only(self, runner, mock_client):
        """Test listing only active schedules"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "schedule", "list",
                "--active-only",
            ])

        assert result.exit_code == 0
        call_args = mock_client.scheduler.list.call_args
        assert call_args.kwargs["is_active"] is True

    def test_list_schedules_empty(self, runner, mock_client):
        """Test listing when no schedules exist"""
        mock_client.scheduler.list.return_value = []

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "list"])

        assert result.exit_code == 0
        assert "No schedules found" in result.output

    def test_list_schedules_error(self, runner, mock_client):
        """Test schedule listing with error"""
        mock_client.scheduler.list.side_effect = Exception("API Error")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "list"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestScheduleCreate:
    """Test schedule create command"""

    def test_create_schedule_success(self, runner, mock_client):
        """Test successful schedule creation"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "schedule", "create",
                "--agent-id", "agent-123",
                "--cron", "0 9 * * *",
                "--message", "Daily task",
            ])

        assert result.exit_code == 0
        assert "Schedule created successfully" in result.output
        assert "0 9 * * *" in result.output
        mock_client.scheduler.create.assert_called_once()

    def test_create_schedule_missing_required(self, runner, mock_client):
        """Test schedule creation with missing required fields"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "create"])

        assert result.exit_code != 0

    def test_create_schedule_error(self, runner, mock_client):
        """Test schedule creation with error"""
        mock_client.scheduler.create.side_effect = Exception("Invalid cron expression")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "schedule", "create",
                "--agent-id", "agent-123",
                "--cron", "invalid",
                "--message", "Test",
            ])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestSchedulePause:
    """Test schedule pause command"""

    def test_pause_schedule_success(self, runner, mock_client):
        """Test successful schedule pausing"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "pause", "schedule-123"])

        assert result.exit_code == 0
        assert "Schedule paused" in result.output
        mock_client.scheduler.pause.assert_called_once_with("schedule-123")

    def test_pause_schedule_not_found(self, runner, mock_client):
        """Test pausing non-existent schedule"""
        mock_client.scheduler.pause.side_effect = ScheduleNotFoundError("Not found")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "pause", "nonexistent"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestScheduleResume:
    """Test schedule resume command"""

    def test_resume_schedule_success(self, runner, mock_client):
        """Test successful schedule resuming"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "resume", "schedule-123"])

        assert result.exit_code == 0
        assert "Schedule resumed" in result.output
        mock_client.scheduler.resume.assert_called_once_with("schedule-123")

    def test_resume_schedule_error(self, runner, mock_client):
        """Test resuming with error"""
        mock_client.scheduler.resume.side_effect = Exception("Error")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "resume", "schedule-123"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestScheduleTrigger:
    """Test schedule trigger command"""

    def test_trigger_schedule_success(self, runner, mock_client):
        """Test successful schedule triggering"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "trigger", "schedule-123"])

        assert result.exit_code == 0
        assert "Schedule triggered" in result.output
        assert "task-exec-123" in result.output
        mock_client.scheduler.trigger.assert_called_once_with("schedule-123")

    def test_trigger_schedule_not_found(self, runner, mock_client):
        """Test triggering non-existent schedule"""
        mock_client.scheduler.trigger.side_effect = ScheduleNotFoundError("Not found")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["schedule", "trigger", "nonexistent"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestScheduleDelete:
    """Test schedule delete command"""

    def test_delete_schedule_success(self, runner, mock_client):
        """Test successful schedule deletion"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "schedule", "delete",
                "schedule-123",
                "--yes",
            ])

        assert result.exit_code == 0
        assert "Schedule deleted" in result.output
        mock_client.scheduler.delete.assert_called_once_with("schedule-123")

    def test_delete_schedule_abort(self, runner, mock_client):
        """Test aborting schedule deletion"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "schedule", "delete",
                "schedule-123",
            ], input="n\n")

        assert result.exit_code == 1  # Aborted
        mock_client.scheduler.delete.assert_not_called()

    def test_delete_schedule_error(self, runner, mock_client):
        """Test schedule deletion with error"""
        mock_client.scheduler.delete.side_effect = Exception("Error")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "schedule", "delete",
                "schedule-123",
                "--yes",
            ])

        assert result.exit_code == 1
        assert "Error:" in result.output
