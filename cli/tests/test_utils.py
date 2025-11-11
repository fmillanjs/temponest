"""
Tests for CLI utility functions
"""
import pytest
from unittest.mock import patch
from temponest_cli.cli import get_client


class TestGetClient:
    """Test get_client utility function"""

    def test_get_client_with_env_vars(self, monkeypatch):
        """Test client creation with environment variables"""
        monkeypatch.setenv("TEMPONEST_BASE_URL", "http://localhost:9000")
        monkeypatch.setenv("TEMPONEST_AUTH_TOKEN", "test-token")

        with patch("temponest_cli.cli.TemponestClient") as mock_client_class:
            client = get_client()

            mock_client_class.assert_called_once_with(
                base_url="http://localhost:9000",
                auth_token="test-token"
            )

    def test_get_client_with_default_url(self, monkeypatch):
        """Test client creation with default URL"""
        monkeypatch.delenv("TEMPONEST_BASE_URL", raising=False)
        monkeypatch.setenv("TEMPONEST_AUTH_TOKEN", "test-token")

        with patch("temponest_cli.cli.TemponestClient") as mock_client_class:
            client = get_client()

            mock_client_class.assert_called_once_with(
                base_url="http://localhost:9000",
                auth_token="test-token"
            )

    def test_get_client_without_auth_token(self, monkeypatch):
        """Test client creation without auth token"""
        monkeypatch.setenv("TEMPONEST_BASE_URL", "http://localhost:9000")
        monkeypatch.delenv("TEMPONEST_AUTH_TOKEN", raising=False)

        with patch("temponest_cli.cli.TemponestClient") as mock_client_class:
            client = get_client()

            mock_client_class.assert_called_once_with(
                base_url="http://localhost:9000",
                auth_token=None
            )

    def test_get_client_with_custom_url(self, monkeypatch):
        """Test client creation with custom URL"""
        monkeypatch.setenv("TEMPONEST_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TEMPONEST_AUTH_TOKEN", "custom-token")

        with patch("temponest_cli.cli.TemponestClient") as mock_client_class:
            client = get_client()

            mock_client_class.assert_called_once_with(
                base_url="https://api.example.com",
                auth_token="custom-token"
            )


class TestCLIGroup:
    """Test CLI group and help"""

    def test_cli_help(self, runner):
        """Test CLI help output"""
        from temponest_cli.cli import cli

        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Temponest CLI" in result.output
        assert "agent" in result.output
        assert "schedule" in result.output
        assert "cost" in result.output
        assert "status" in result.output

    def test_cli_version(self, runner):
        """Test CLI version output"""
        from temponest_cli.cli import cli

        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_agent_group_help(self, runner):
        """Test agent command group help"""
        from temponest_cli.cli import cli

        result = runner.invoke(cli, ["agent", "--help"])

        assert result.exit_code == 0
        assert "Manage agents" in result.output
        assert "list" in result.output
        assert "create" in result.output
        assert "get" in result.output
        assert "execute" in result.output
        assert "delete" in result.output

    def test_schedule_group_help(self, runner):
        """Test schedule command group help"""
        from temponest_cli.cli import cli

        result = runner.invoke(cli, ["schedule", "--help"])

        assert result.exit_code == 0
        assert "Manage schedules" in result.output
        assert "list" in result.output
        assert "create" in result.output
        assert "pause" in result.output
        assert "resume" in result.output
        assert "trigger" in result.output
        assert "delete" in result.output

    def test_cost_group_help(self, runner):
        """Test cost command group help"""
        from temponest_cli.cli import cli

        result = runner.invoke(cli, ["cost", "--help"])

        assert result.exit_code == 0
        assert "cost tracking" in result.output.lower()
        assert "summary" in result.output
        assert "budget" in result.output
        assert "set-budget" in result.output
