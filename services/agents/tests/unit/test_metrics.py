"""
Unit tests for Prometheus metrics.
"""

import pytest
from unittest.mock import MagicMock, patch
from app.metrics import MetricsRecorder


@pytest.mark.unit
class TestMetricsRecorder:
    """Test suite for MetricsRecorder"""

    def test_record_agent_execution_basic(self):
        """Test recording basic agent execution metrics"""
        with patch('app.metrics.agent_executions_total') as mock_counter, \
             patch('app.metrics.agent_execution_duration_seconds') as mock_histogram:

            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels
            mock_histogram.labels.return_value = mock_histogram

            MetricsRecorder.record_agent_execution(
                agent_name="developer",
                status="completed",
                duration_seconds=5.2,
                tokens_used={},
                cost_usd=0.0,
                tenant_id="tenant-123",
                project_id=None,
                model="gpt-4",
                provider="openai"
            )

            # Verify execution counter was incremented
            mock_counter.labels.assert_called_once_with(
                agent_name="developer",
                status="completed",
                tenant_id="tenant-123"
            )
            mock_labels.inc.assert_called_once()

            # Verify duration was observed
            mock_histogram.labels.assert_called_once_with(
                agent_name="developer",
                tenant_id="tenant-123"
            )
            mock_histogram.observe.assert_called_once_with(5.2)

    def test_record_agent_execution_with_tokens(self):
        """Test recording agent execution with token metrics"""
        with patch('app.metrics.agent_tokens_total') as mock_token_counter, \
             patch('app.metrics.agent_executions_total'), \
             patch('app.metrics.agent_execution_duration_seconds'):

            mock_labels = MagicMock()
            mock_token_counter.labels.return_value = mock_labels

            tokens_used = {
                "input": 1000,
                "output": 500
            }

            MetricsRecorder.record_agent_execution(
                agent_name="qa_tester",
                status="completed",
                duration_seconds=3.0,
                tokens_used=tokens_used,
                cost_usd=0.0,
                tenant_id="tenant-456",
                model="claude-sonnet-4",
                provider="claude"
            )

            # Verify token counts were incremented
            assert mock_token_counter.labels.call_count == 2
            assert mock_labels.inc.call_count == 2

            # Verify input tokens
            calls = mock_token_counter.labels.call_args_list
            assert any(call[1]['token_type'] == 'input' for call in calls)
            assert any(call[1]['token_type'] == 'output' for call in calls)

    def test_record_agent_execution_with_cost(self):
        """Test recording agent execution with cost metrics"""
        with patch('app.metrics.agent_cost_usd_total') as mock_cost_counter, \
             patch('app.metrics.agent_executions_total'), \
             patch('app.metrics.agent_execution_duration_seconds'):

            mock_labels = MagicMock()
            mock_cost_counter.labels.return_value = mock_labels

            MetricsRecorder.record_agent_execution(
                agent_name="designer",
                status="completed",
                duration_seconds=10.5,
                tokens_used={},
                cost_usd=0.25,
                tenant_id="tenant-789",
                project_id="project-abc",
                model="gpt-4o",
                provider="openai"
            )

            # Verify cost was incremented
            mock_cost_counter.labels.assert_called_once_with(
                agent_name="designer",
                provider="openai",
                model="gpt-4o",
                tenant_id="tenant-789",
                project_id="project-abc"
            )
            mock_labels.inc.assert_called_once_with(0.25)

    def test_record_agent_execution_zero_cost(self):
        """Test that zero cost doesn't record cost metric"""
        with patch('app.metrics.agent_cost_usd_total') as mock_cost_counter, \
             patch('app.metrics.agent_executions_total'), \
             patch('app.metrics.agent_execution_duration_seconds'):

            MetricsRecorder.record_agent_execution(
                agent_name="devops",
                status="completed",
                duration_seconds=2.0,
                tokens_used={},
                cost_usd=0.0,  # Zero cost - should not record
                tenant_id="tenant-123",
                model="ollama",
                provider="ollama"
            )

            # Cost counter should not be called for zero cost
            mock_cost_counter.labels.assert_not_called()

    def test_record_agent_execution_without_project_id(self):
        """Test recording execution without project_id"""
        with patch('app.metrics.agent_cost_usd_total') as mock_cost_counter, \
             patch('app.metrics.agent_executions_total'), \
             patch('app.metrics.agent_execution_duration_seconds'):

            mock_labels = MagicMock()
            mock_cost_counter.labels.return_value = mock_labels

            MetricsRecorder.record_agent_execution(
                agent_name="security_auditor",
                status="completed",
                duration_seconds=15.0,
                tokens_used={},
                cost_usd=0.50,
                tenant_id="tenant-xyz",
                project_id=None,  # No project
                model="claude-haiku-4",
                provider="claude"
            )

            # Verify project_id defaults to "none"
            mock_cost_counter.labels.assert_called_once()
            call_kwargs = mock_cost_counter.labels.call_args[1]
            assert call_kwargs['project_id'] == "none"

    def test_record_agent_execution_empty_tokens(self):
        """Test recording execution with empty tokens dict"""
        with patch('app.metrics.agent_tokens_total') as mock_token_counter, \
             patch('app.metrics.agent_executions_total'), \
             patch('app.metrics.agent_execution_duration_seconds'):

            MetricsRecorder.record_agent_execution(
                agent_name="overseer",
                status="completed",
                duration_seconds=1.0,
                tokens_used={},  # Empty tokens
                cost_usd=0.0,
                tenant_id="tenant-123"
            )

            # Token counter should not be called for empty dict
            mock_token_counter.labels.assert_not_called()

    def test_record_agent_execution_none_tokens(self):
        """Test recording execution with None tokens"""
        with patch('app.metrics.agent_tokens_total') as mock_token_counter, \
             patch('app.metrics.agent_executions_total'), \
             patch('app.metrics.agent_execution_duration_seconds'):

            MetricsRecorder.record_agent_execution(
                agent_name="ux_researcher",
                status="completed",
                duration_seconds=2.5,
                tokens_used=None,  # None tokens
                cost_usd=0.0,
                tenant_id="tenant-123"
            )

            # Token counter should not be called for None
            mock_token_counter.labels.assert_not_called()

    def test_record_collaboration(self):
        """Test recording collaboration metrics"""
        with patch('app.metrics.collaboration_sessions_total') as mock_counter, \
             patch('app.metrics.collaboration_duration_seconds') as mock_histogram:

            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels
            mock_histogram.labels.return_value = mock_histogram

            MetricsRecorder.record_collaboration(
                pattern="sequential",
                status="completed",
                duration_seconds=45.5,
                tenant_id="tenant-collab"
            )

            # Verify counter was incremented
            mock_counter.labels.assert_called_once_with(
                pattern="sequential",
                status="completed",
                tenant_id="tenant-collab"
            )
            mock_labels.inc.assert_called_once()

            # Verify duration was observed
            mock_histogram.labels.assert_called_once_with(
                pattern="sequential",
                tenant_id="tenant-collab"
            )
            mock_histogram.observe.assert_called_once_with(45.5)

    def test_record_collaboration_parallel_pattern(self):
        """Test recording parallel collaboration"""
        with patch('app.metrics.collaboration_sessions_total') as mock_counter, \
             patch('app.metrics.collaboration_duration_seconds') as mock_histogram:

            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels
            mock_histogram.labels.return_value = mock_histogram

            MetricsRecorder.record_collaboration(
                pattern="parallel",
                status="completed",
                duration_seconds=30.0,
                tenant_id="tenant-123"
            )

            call_kwargs = mock_counter.labels.call_args[1]
            assert call_kwargs['pattern'] == "parallel"

    def test_record_webhook_delivery(self):
        """Test recording webhook delivery metrics"""
        with patch('app.metrics.webhook_deliveries_total') as mock_counter, \
             patch('app.metrics.webhook_delivery_duration_seconds') as mock_histogram:

            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels
            mock_histogram.labels.return_value = mock_histogram

            MetricsRecorder.record_webhook_delivery(
                event_type="agent.completed",
                status="success",
                duration_seconds=0.8,
                tenant_id="tenant-webhook"
            )

            # Verify counter was incremented
            mock_counter.labels.assert_called_once_with(
                event_type="agent.completed",
                status="success",
                tenant_id="tenant-webhook"
            )
            mock_labels.inc.assert_called_once()

            # Verify duration was observed
            mock_histogram.labels.assert_called_once_with(
                event_type="agent.completed",
                tenant_id="tenant-webhook"
            )
            mock_histogram.observe.assert_called_once_with(0.8)

    def test_record_webhook_delivery_failed(self):
        """Test recording failed webhook delivery"""
        with patch('app.metrics.webhook_deliveries_total') as mock_counter, \
             patch('app.metrics.webhook_delivery_duration_seconds') as mock_histogram:

            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels
            mock_histogram.labels.return_value = mock_histogram

            MetricsRecorder.record_webhook_delivery(
                event_type="budget.exceeded",
                status="failed",
                duration_seconds=5.0,
                tenant_id="tenant-123"
            )

            call_kwargs = mock_counter.labels.call_args[1]
            assert call_kwargs['status'] == "failed"

    def test_record_error(self):
        """Test recording agent error"""
        with patch('app.metrics.agent_errors_total') as mock_counter:
            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels

            MetricsRecorder.record_error(
                agent_name="developer",
                error_type="timeout",
                tenant_id="tenant-error"
            )

            # Verify error counter was incremented
            mock_counter.labels.assert_called_once_with(
                agent_name="developer",
                error_type="timeout",
                tenant_id="tenant-error"
            )
            mock_labels.inc.assert_called_once()

    def test_record_error_different_types(self):
        """Test recording different error types"""
        with patch('app.metrics.agent_errors_total') as mock_counter:
            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels

            # Test various error types
            error_types = ["timeout", "api_error", "validation_error", "llm_error"]
            for error_type in error_types:
                MetricsRecorder.record_error(
                    agent_name="qa_tester",
                    error_type=error_type,
                    tenant_id="tenant-123"
                )

            assert mock_labels.inc.call_count == len(error_types)

    def test_update_service_health_healthy(self):
        """Test updating service health to healthy"""
        with patch('app.metrics.service_health') as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            MetricsRecorder.update_service_health(
                component="database",
                is_healthy=True
            )

            # Verify gauge was set to 1 for healthy
            mock_gauge.labels.assert_called_once_with(component="database")
            mock_labels.set.assert_called_once_with(1)

    def test_update_service_health_unhealthy(self):
        """Test updating service health to unhealthy"""
        with patch('app.metrics.service_health') as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            MetricsRecorder.update_service_health(
                component="qdrant",
                is_healthy=False
            )

            # Verify gauge was set to 0 for unhealthy
            mock_gauge.labels.assert_called_once_with(component="qdrant")
            mock_labels.set.assert_called_once_with(0)

    def test_update_service_health_multiple_components(self):
        """Test updating health for multiple components"""
        with patch('app.metrics.service_health') as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            components = {
                "database": True,
                "qdrant": True,
                "langfuse": False,
                "ollama": True
            }

            for component, is_healthy in components.items():
                MetricsRecorder.update_service_health(component, is_healthy)

            assert mock_gauge.labels.call_count == len(components)

    def test_update_budget_usage(self):
        """Test updating budget usage gauge"""
        with patch('app.metrics.budget_usage_ratio') as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            MetricsRecorder.update_budget_usage(
                tenant_id="tenant-budget",
                budget_type="daily",
                usage_ratio=0.75
            )

            # Verify gauge was set
            mock_gauge.labels.assert_called_once_with(
                tenant_id="tenant-budget",
                budget_type="daily"
            )
            mock_labels.set.assert_called_once_with(0.75)

    def test_update_budget_usage_monthly(self):
        """Test updating monthly budget usage"""
        with patch('app.metrics.budget_usage_ratio') as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            MetricsRecorder.update_budget_usage(
                tenant_id="tenant-123",
                budget_type="monthly",
                usage_ratio=0.95
            )

            call_kwargs = mock_gauge.labels.call_args[1]
            assert call_kwargs['budget_type'] == "monthly"
            mock_labels.set.assert_called_once_with(0.95)

    def test_update_budget_usage_zero(self):
        """Test updating budget usage with zero"""
        with patch('app.metrics.budget_usage_ratio') as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            MetricsRecorder.update_budget_usage(
                tenant_id="tenant-123",
                budget_type="daily",
                usage_ratio=0.0
            )

            mock_labels.set.assert_called_once_with(0.0)

    def test_update_budget_usage_full(self):
        """Test updating budget usage at 100%"""
        with patch('app.metrics.budget_usage_ratio') as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            MetricsRecorder.update_budget_usage(
                tenant_id="tenant-123",
                budget_type="daily",
                usage_ratio=1.0
            )

            mock_labels.set.assert_called_once_with(1.0)

    def test_record_budget_alert(self):
        """Test recording budget alert"""
        with patch('app.metrics.budget_alerts_total') as mock_counter:
            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels

            MetricsRecorder.record_budget_alert(
                tenant_id="tenant-alert",
                alert_type="warning"
            )

            # Verify alert counter was incremented
            mock_counter.labels.assert_called_once_with(
                tenant_id="tenant-alert",
                alert_type="warning"
            )
            mock_labels.inc.assert_called_once()

    def test_record_budget_alert_exceeded(self):
        """Test recording exceeded budget alert"""
        with patch('app.metrics.budget_alerts_total') as mock_counter:
            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels

            MetricsRecorder.record_budget_alert(
                tenant_id="tenant-123",
                alert_type="exceeded"
            )

            call_kwargs = mock_counter.labels.call_args[1]
            assert call_kwargs['alert_type'] == "exceeded"

    def test_record_budget_alert_critical(self):
        """Test recording critical budget alert"""
        with patch('app.metrics.budget_alerts_total') as mock_counter:
            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels

            MetricsRecorder.record_budget_alert(
                tenant_id="tenant-123",
                alert_type="critical"
            )

            call_kwargs = mock_counter.labels.call_args[1]
            assert call_kwargs['alert_type'] == "critical"

    def test_record_agent_execution_full_metrics(self):
        """Test recording full agent execution with all metrics"""
        with patch('app.metrics.agent_executions_total'), \
             patch('app.metrics.agent_execution_duration_seconds'), \
             patch('app.metrics.agent_tokens_total') as mock_token_counter, \
             patch('app.metrics.agent_cost_usd_total') as mock_cost_counter:

            mock_token_labels = MagicMock()
            mock_token_counter.labels.return_value = mock_token_labels
            mock_cost_labels = MagicMock()
            mock_cost_counter.labels.return_value = mock_cost_labels

            MetricsRecorder.record_agent_execution(
                agent_name="security_auditor",
                status="completed",
                duration_seconds=25.0,
                tokens_used={"input": 5000, "output": 2000},
                cost_usd=0.75,
                tenant_id="tenant-full",
                project_id="project-full",
                model="claude-opus-4",
                provider="claude"
            )

            # All metrics should be recorded
            assert mock_token_counter.labels.call_count == 2  # input + output
            mock_cost_counter.labels.assert_called_once()
