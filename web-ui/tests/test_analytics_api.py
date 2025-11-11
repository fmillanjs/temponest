"""
Test analytics API endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal


@pytest.mark.integration
def test_api_get_recent_executions_success(client, mock_asyncpg):
    """Test /api/analytics/executions/recent returns recent executions"""
    mock_asyncpg.fetch.return_value = [
        {
            'task_id': 'task-1',
            'agent_name': 'developer',
            'model_provider': 'anthropic',
            'model_name': 'claude-3-opus',
            'total_tokens': 1000,
            'total_cost_usd': Decimal('1.50'),
            'latency_ms': 250,
            'status': 'completed',
            'created_at': datetime.now(),
            'workflow_id': 'wf-1',
            'project_id': 'proj-1'
        }
    ]

    response = client.get("/api/analytics/executions/recent")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert 'task_id' in data[0]
        assert 'agent_name' in data[0]
        # created_at should be ISO format string
        assert 'created_at' in data[0]


@pytest.mark.integration
def test_api_get_recent_executions_with_limit(client, mock_asyncpg):
    """Test /api/analytics/executions/recent respects limit parameter"""
    mock_asyncpg.fetch.return_value = []

    response = client.get("/api/analytics/executions/recent?limit=10")
    assert response.status_code == 200

    # Verify fetch was called with the limit
    mock_asyncpg.fetch.assert_called_once()
    call_args = mock_asyncpg.fetch.call_args
    assert call_args[0][1] == 10  # limit parameter


@pytest.mark.integration
def test_api_get_recent_executions_default_limit(client, mock_asyncpg):
    """Test /api/analytics/executions/recent uses default limit"""
    mock_asyncpg.fetch.return_value = []

    response = client.get("/api/analytics/executions/recent")
    assert response.status_code == 200

    # Should use default limit of 50
    call_args = mock_asyncpg.fetch.call_args
    assert call_args[0][1] == 50


@pytest.mark.integration
def test_api_get_recent_executions_handles_errors(client):
    """Test /api/analytics/executions/recent handles database errors"""
    with patch('app.get_db_connection', side_effect=Exception("DB error")):
        response = client.get("/api/analytics/executions/recent")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_agent_stats_success(client, mock_asyncpg):
    """Test /api/analytics/agents/stats returns agent statistics"""
    mock_asyncpg.fetch.return_value = [
        {
            'agent_name': 'developer',
            'total_executions': 50,
            'first_execution': datetime.now() - timedelta(days=7),
            'last_execution': datetime.now()
        }
    ]

    with patch('app.query_prometheus', return_value=[]):
        response = client.get("/api/analytics/agents/stats")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_api_get_agent_stats_includes_prometheus_data(client, mock_asyncpg):
    """Test /api/analytics/agents/stats includes Prometheus metrics"""
    mock_asyncpg.fetch.return_value = [
        {
            'agent_name': 'developer',
            'total_executions': 50,
            'first_execution': datetime.now(),
            'last_execution': datetime.now()
        }
    ]

    prometheus_response = [
        {
            'metric': {'agent_name': 'developer'},
            'value': [1234567890, '3']
        }
    ]

    with patch('app.query_prometheus', return_value=prometheus_response):
        response = client.get("/api/analytics/agents/stats")

    assert response.status_code == 200
    data = response.get_json()

    if len(data) > 0:
        # Should include currently_running from Prometheus
        assert 'currently_running' in data[0]
        assert data[0]['currently_running'] == 3


@pytest.mark.integration
def test_api_get_agent_stats_handles_missing_prometheus(client, mock_asyncpg):
    """Test /api/analytics/agents/stats handles Prometheus unavailability"""
    mock_asyncpg.fetch.return_value = [
        {
            'agent_name': 'developer',
            'total_executions': 50,
            'first_execution': datetime.now(),
            'last_execution': datetime.now()
        }
    ]

    with patch('app.query_prometheus', return_value=[]):
        response = client.get("/api/analytics/agents/stats")

    assert response.status_code == 200
    data = response.get_json()

    if len(data) > 0:
        # Should default to 0 when Prometheus doesn't return data
        assert data[0]['currently_running'] == 0


@pytest.mark.integration
def test_api_get_agent_stats_handles_errors(client):
    """Test /api/analytics/agents/stats handles errors"""
    with patch('app.get_db_connection', side_effect=Exception("DB error")):
        response = client.get("/api/analytics/agents/stats")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_execution_timeline_success(client, mock_asyncpg):
    """Test /api/analytics/executions/timeline returns timeline data"""
    mock_asyncpg.fetch.return_value = [
        {
            'date': datetime.now().date(),
            'agent_name': 'developer',
            'executions': 10,
            'total_tokens': 5000,
            'total_cost': Decimal('7.50'),
            'avg_latency': 250.5,
            'failures': 1
        }
    ]

    response = client.get("/api/analytics/executions/timeline")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_api_get_execution_timeline_custom_days(client, mock_asyncpg):
    """Test /api/analytics/executions/timeline with custom days parameter"""
    mock_asyncpg.fetch.return_value = []

    response = client.get("/api/analytics/executions/timeline?days=30")
    assert response.status_code == 200

    # Verify the query used 30 days
    call_args = mock_asyncpg.fetch.call_args
    assert '30' in call_args[0][0]


@pytest.mark.integration
def test_api_get_execution_timeline_default_days(client, mock_asyncpg):
    """Test /api/analytics/executions/timeline uses default 7 days"""
    mock_asyncpg.fetch.return_value = []

    response = client.get("/api/analytics/executions/timeline")
    assert response.status_code == 200

    # Should default to 7 days
    call_args = mock_asyncpg.fetch.call_args
    assert '7' in call_args[0][0]


@pytest.mark.integration
def test_api_get_execution_timeline_handles_errors(client):
    """Test /api/analytics/executions/timeline handles errors"""
    with patch('app.get_db_connection', side_effect=Exception("DB error")):
        response = client.get("/api/analytics/executions/timeline")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_analytics_dashboard_success(client, mock_asyncpg):
    """Test /api/analytics/dashboard returns comprehensive dashboard data"""
    mock_asyncpg.fetchrow.return_value = {
        'total_executions': 100,
        'unique_agents': 5,
        'total_tokens': 50000,
        'total_cost': Decimal('123.45'),
        'avg_latency': 250.5,
        'total_failures': 5,
        'last_24h_executions': 25
    }

    mock_asyncpg.fetch.side_effect = [
        # hourly trend
        [
            {
                'hour': datetime.now(),
                'executions': 10,
                'avg_latency': 250.0
            }
        ],
        # top agents
        [
            {
                'agent_name': 'developer',
                'executions': 50,
                'cost': Decimal('75.25')
            }
        ]
    ]

    with patch('app.query_prometheus', return_value=[{'value': [0, '5']}]):
        response = client.get("/api/analytics/dashboard")

    assert response.status_code == 200
    data = response.get_json()

    assert 'overall' in data
    assert 'hourly_trend' in data
    assert 'top_agents' in data
    assert isinstance(data['overall'], dict)
    assert isinstance(data['hourly_trend'], list)
    assert isinstance(data['top_agents'], list)


@pytest.mark.integration
def test_api_get_analytics_dashboard_includes_prometheus(client, mock_asyncpg):
    """Test /api/analytics/dashboard includes Prometheus metrics"""
    mock_asyncpg.fetchrow.return_value = {
        'total_executions': 100,
        'unique_agents': 5,
        'total_tokens': 50000,
        'total_cost': Decimal('123.45'),
        'avg_latency': 250.5,
        'total_failures': 5,
        'last_24h_executions': 25
    }

    mock_asyncpg.fetch.side_effect = [[], []]  # Empty hourly and top agents

    prometheus_response = [
        {
            'value': [1234567890, '8']
        }
    ]

    with patch('app.query_prometheus', return_value=prometheus_response):
        response = client.get("/api/analytics/dashboard")

    assert response.status_code == 200
    data = response.get_json()

    # Should include currently_running from Prometheus
    assert 'currently_running' in data['overall']
    assert data['overall']['currently_running'] == 8


@pytest.mark.integration
def test_api_get_analytics_dashboard_handles_errors(client):
    """Test /api/analytics/dashboard handles errors"""
    with patch('app.get_db_connection', side_effect=Exception("DB error")):
        response = client.get("/api/analytics/dashboard")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_agent_load_success(client):
    """Test /api/analytics/agents/load returns agent load from Prometheus"""
    prometheus_responses = {
        'running_executions': [
            {
                'metric': {'agent_name': 'developer'},
                'value': [0, '3']
            }
        ],
        'agent_executions_total': [
            {
                'metric': {'agent_name': 'developer'},
                'value': [0, '100']
            }
        ],
        'agent_execution_duration_seconds': [],
        'agent_execution_errors_total': []
    }

    def mock_prometheus(query):
        if 'running_executions' in query:
            return prometheus_responses['running_executions']
        elif 'agent_executions_total' in query:
            return prometheus_responses['agent_executions_total']
        return []

    with patch('app.query_prometheus', side_effect=mock_prometheus):
        response = client.get("/api/analytics/agents/load")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_api_get_agent_load_aggregates_metrics(client):
    """Test /api/analytics/agents/load aggregates multiple metrics"""
    prometheus_responses = {
        'running': [{'metric': {'agent_name': 'dev'}, 'value': [0, '2']}],
        'total': [{'metric': {'agent_name': 'dev'}, 'value': [0, '50']}]
    }

    call_count = [0]

    def mock_prometheus(query):
        call_count[0] += 1
        if 'running_executions' in query and call_count[0] == 1:
            return prometheus_responses['running']
        elif 'agent_executions_total' in query:
            return prometheus_responses['total']
        return []

    with patch('app.query_prometheus', side_effect=mock_prometheus):
        response = client.get("/api/analytics/agents/load")

    assert response.status_code == 200
    data = response.get_json()

    if len(data) > 0:
        agent = data[0]
        assert 'agent_name' in agent
        assert 'running' in agent
        assert 'total_executions' in agent


@pytest.mark.integration
def test_api_get_agent_load_handles_errors(client):
    """Test /api/analytics/agents/load handles Prometheus errors"""
    with patch('app.query_prometheus', side_effect=Exception("Prometheus error")):
        response = client.get("/api/analytics/agents/load")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
