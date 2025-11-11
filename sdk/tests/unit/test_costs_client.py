"""
Unit tests for CostsClient
"""
import pytest
from unittest.mock import Mock, patch
from temponest_sdk.costs import CostsClient
from temponest_sdk.client import BaseClient
from temponest_sdk.models import CostSummary, BudgetConfig


class TestCostsClientSummary:
    """Test cost summary"""

    def test_get_summary_default(self, clean_env, mock_cost_summary_data):
        """Test getting cost summary with default parameters"""
        with patch.object(BaseClient, 'get', return_value=mock_cost_summary_data):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            summary = costs_client.get_summary()

            assert isinstance(summary, CostSummary)
            assert summary.total_usd == 15.50

    def test_get_summary_with_date_range(self, clean_env, mock_cost_summary_data):
        """Test getting cost summary with date range"""
        with patch.object(BaseClient, 'get', return_value=mock_cost_summary_data) as mock_get:
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            summary = costs_client.get_summary(
                start_date="2024-01-01",
                end_date="2024-01-31"
            )

            call_args = mock_get.call_args
            assert call_args[1]['params']['start_date'] == "2024-01-01"
            assert call_args[1]['params']['end_date'] == "2024-01-31"

    def test_get_summary_by_agent(self, clean_env, mock_cost_summary_data):
        """Test getting cost summary filtered by agent"""
        with patch.object(BaseClient, 'get', return_value=mock_cost_summary_data) as mock_get:
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            summary = costs_client.get_summary(agent_id="agent-123")

            call_args = mock_get.call_args
            assert call_args[1]['params']['agent_id'] == "agent-123"

    def test_get_summary_by_project(self, clean_env, mock_cost_summary_data):
        """Test getting cost summary filtered by project"""
        with patch.object(BaseClient, 'get', return_value=mock_cost_summary_data) as mock_get:
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            summary = costs_client.get_summary(project_id="project-123")

            call_args = mock_get.call_args
            assert call_args[1]['params']['project_id'] == "project-123"


class TestCostsClientBreakdown:
    """Test cost breakdowns"""

    def test_get_daily_costs(self, clean_env):
        """Test getting daily cost breakdown"""
        daily_data = {
            "2024-01-01": 5.50,
            "2024-01-02": 6.20,
            "2024-01-03": 3.80
        }
        with patch.object(BaseClient, 'get', return_value=daily_data):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            costs = costs_client.get_daily_costs(days=30)

            assert isinstance(costs, dict)
            assert "2024-01-01" in costs
            assert costs["2024-01-01"] == 5.50

    def test_get_hourly_costs(self, clean_env):
        """Test getting hourly cost breakdown"""
        hourly_data = {
            "2024-01-01T00:00:00": 0.25,
            "2024-01-01T01:00:00": 0.30
        }
        with patch.object(BaseClient, 'get', return_value=hourly_data):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            costs = costs_client.get_hourly_costs(hours=24)

            assert isinstance(costs, dict)
            assert len(costs) == 2

    def test_get_agent_costs(self, clean_env):
        """Test getting costs by agent"""
        agent_costs = {
            "agent-1": 10.00,
            "agent-2": 5.50
        }
        with patch.object(BaseClient, 'get', return_value=agent_costs):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            costs = costs_client.get_agent_costs(top_n=10)

            assert isinstance(costs, dict)
            assert costs["agent-1"] == 10.00

    def test_get_provider_costs(self, clean_env):
        """Test getting costs by provider"""
        provider_costs = {
            "openai": 12.00,
            "anthropic": 3.50
        }
        with patch.object(BaseClient, 'get', return_value=provider_costs):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            costs = costs_client.get_provider_costs()

            assert isinstance(costs, dict)
            assert costs["openai"] == 12.00


class TestCostsClientBudget:
    """Test budget management"""

    def test_get_budget(self, clean_env, mock_budget_config_data):
        """Test getting budget configuration"""
        with patch.object(BaseClient, 'get', return_value=mock_budget_config_data):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            budget = costs_client.get_budget()

            assert isinstance(budget, BudgetConfig)
            assert budget.monthly_limit_usd == 100.00

    def test_set_budget(self, clean_env, mock_budget_config_data):
        """Test setting budget configuration"""
        with patch.object(BaseClient, 'post', return_value=mock_budget_config_data) as mock_post:
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            budget = costs_client.set_budget(
                monthly_limit_usd=150.00,
                alert_threshold=0.75
            )

            assert budget.monthly_limit_usd == 100.00  # From mock data
            call_args = mock_post.call_args
            assert call_args[1]['json']['monthly_limit_usd'] == 150.00

    def test_update_budget(self, clean_env, mock_budget_config_data):
        """Test updating budget configuration"""
        with patch.object(BaseClient, 'patch', return_value=mock_budget_config_data):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            budget = costs_client.update_budget(
                monthly_limit_usd=200.00
            )

            assert isinstance(budget, BudgetConfig)

    def test_delete_budget(self, clean_env):
        """Test deleting budget configuration"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            costs_client = CostsClient(client)

            costs_client.delete_budget()
            # No exception means success
