"""
Tests for CLI cost commands
"""
import pytest
from unittest.mock import patch
from temponest_cli.cli import cli


class TestCostSummary:
    """Test cost summary command"""

    def test_cost_summary_success(self, runner, mock_client):
        """Test successful cost summary retrieval"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "summary"])

        assert result.exit_code == 0
        assert "Cost Summary" in result.output
        assert "$125.50" in result.output
        assert "500000" in result.output  # tokens
        mock_client.costs.get_summary.assert_called_once()

    def test_cost_summary_with_custom_days(self, runner, mock_client):
        """Test cost summary with custom days"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "summary", "--days", "7"])

        assert result.exit_code == 0
        mock_client.costs.get_summary.assert_called_once()

    def test_cost_summary_by_provider(self, runner, mock_client):
        """Test cost summary shows provider breakdown"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "summary"])

        assert result.exit_code == 0
        assert "By Provider:" in result.output
        assert "openai" in result.output
        assert "anthropic" in result.output

    def test_cost_summary_by_model(self, runner, mock_client):
        """Test cost summary shows model breakdown"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "summary"])

        assert result.exit_code == 0
        assert "By Model:" in result.output
        assert "gpt-4" in result.output
        assert "claude-3" in result.output

    def test_cost_summary_error(self, runner, mock_client):
        """Test cost summary with API error"""
        mock_client.costs.get_summary.side_effect = Exception("API Error")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "summary"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestCostBudget:
    """Test cost budget command"""

    def test_budget_status_success(self, runner, mock_client):
        """Test successful budget status retrieval"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "budget"])

        assert result.exit_code == 0
        assert "Budget Status" in result.output
        assert "Daily:" in result.output
        assert "Monthly:" in result.output
        mock_client.costs.get_budget_status.assert_called_once()

    def test_budget_status_daily_under_threshold(self, runner, mock_client):
        """Test budget status shows green when under threshold"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "budget"])

        assert result.exit_code == 0
        # 51% is under 80% threshold, should be green
        assert "51.0%" in result.output

    def test_budget_status_monthly_under_threshold(self, runner, mock_client):
        """Test monthly budget under threshold"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "budget"])

        assert result.exit_code == 0
        # 35% is under 80% threshold
        assert "35.0%" in result.output

    def test_budget_status_over_threshold(self, runner, mock_client):
        """Test budget status when over threshold"""
        mock_client.costs.get_budget_status.return_value = {
            "daily_limit": 50.0,
            "daily_usage": 42.0,
            "daily_percentage": 0.84,  # 84% - over 80% threshold
            "monthly_limit": 1000.0,
            "monthly_usage": 950.0,
            "monthly_percentage": 0.95,  # 95% - over 80% and 100%
        }

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "budget"])

        assert result.exit_code == 0
        assert "84.0%" in result.output
        assert "95.0%" in result.output

    def test_budget_status_error(self, runner, mock_client):
        """Test budget status with error"""
        mock_client.costs.get_budget_status.side_effect = Exception("API Error")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["cost", "budget"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestCostSetBudget:
    """Test cost set-budget command"""

    def test_set_budget_daily_only(self, runner, mock_client):
        """Test setting daily budget only"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "cost", "set-budget",
                "--daily", "100.0",
            ])

        assert result.exit_code == 0
        assert "Budget updated" in result.output
        assert "$50.00" in result.output  # from mock_budget
        mock_client.costs.set_budget.assert_called_once()

    def test_set_budget_monthly_only(self, runner, mock_client):
        """Test setting monthly budget only"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "cost", "set-budget",
                "--monthly", "2000.0",
            ])

        assert result.exit_code == 0
        assert "Budget updated" in result.output
        mock_client.costs.set_budget.assert_called_once()

    def test_set_budget_both(self, runner, mock_client):
        """Test setting both daily and monthly budgets"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "cost", "set-budget",
                "--daily", "100.0",
                "--monthly", "2000.0",
            ])

        assert result.exit_code == 0
        assert "Budget updated" in result.output
        mock_client.costs.set_budget.assert_called_once()

    def test_set_budget_with_threshold(self, runner, mock_client):
        """Test setting budget with custom threshold"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "cost", "set-budget",
                "--daily", "100.0",
                "--threshold", "0.9",
            ])

        assert result.exit_code == 0
        assert "Alert threshold: 80%" in result.output  # from mock_budget
        mock_client.costs.set_budget.assert_called_once()
        call_args = mock_client.costs.set_budget.call_args
        assert call_args.kwargs["alert_threshold"] == 0.9

    def test_set_budget_error(self, runner, mock_client):
        """Test setting budget with error"""
        mock_client.costs.set_budget.side_effect = Exception("Invalid values")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "cost", "set-budget",
                "--daily", "100.0",
            ])

        assert result.exit_code == 1
        assert "Error:" in result.output
