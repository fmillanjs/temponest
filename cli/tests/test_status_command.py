"""
Tests for CLI status command
"""
import pytest
from unittest.mock import patch, Mock
from temponest_cli.cli import cli


class TestStatusCommand:
    """Test status command"""

    def test_status_all_healthy(self, runner):
        """Test status when all services are healthy"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Platform Status" in result.output
            assert "Healthy" in result.output
            assert mock_get.call_count == 4  # 4 services

    def test_status_some_unhealthy(self, runner):
        """Test status when some services are unhealthy"""
        def mock_get(url, timeout=5):
            response = Mock()
            if "9003" in url:  # Scheduler service
                response.status_code = 500
            else:
                response.status_code = 200
            return response

        with patch("requests.get", side_effect=mock_get):
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Platform Status" in result.output
            # Should show both healthy and unhealthy statuses

    def test_status_service_unavailable(self, runner):
        """Test status when services are unavailable"""
        with patch("requests.get", side_effect=Exception("Connection refused")):
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Platform Status" in result.output
            assert "Unavailable" in result.output

    def test_status_partial_unavailable(self, runner):
        """Test status when some services are unavailable"""
        def mock_get(url, timeout=5):
            if "grafana" in url.lower():
                raise Exception("Service not running")
            response = Mock()
            response.status_code = 200
            return response

        with patch("requests.get", side_effect=mock_get):
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Platform Status" in result.output

    def test_status_custom_base_url(self, runner, monkeypatch):
        """Test status with custom base URL"""
        monkeypatch.setenv("TEMPONEST_BASE_URL", "http://custom:8000")

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            # Should use custom URL
            calls = [str(call) for call in mock_get.call_args_list]
            assert any("custom" in str(call) for call in calls)

    def test_status_command_error(self, runner):
        """Test status command with unexpected error"""
        with patch("requests.get", side_effect=RuntimeError("Unexpected error")):
            result = runner.invoke(cli, ["status"])

            # Should handle error gracefully
            assert "Error:" in result.output or "Unavailable" in result.output
