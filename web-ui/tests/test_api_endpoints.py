"""
Test API endpoints (agents, schedules, costs, status)
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from decimal import Decimal
from datetime import datetime


@pytest.mark.unit
def test_api_list_agents_returns_empty_array(client):
    """Test /api/agents GET returns empty array"""
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.get_json()
    assert data == []


@pytest.mark.unit
def test_api_create_agent_not_implemented(client):
    """Test /api/agents POST returns 501"""
    response = client.post("/api/agents", json={"name": "test"})
    assert response.status_code == 501
    data = response.get_json()
    assert "error" in data
    assert "Use agent service directly" in data["error"]


@pytest.mark.unit
def test_api_get_agent_not_implemented(client):
    """Test /api/agents/<id> GET returns 501"""
    response = client.get("/api/agents/123")
    assert response.status_code == 501
    data = response.get_json()
    assert "error" in data


@pytest.mark.unit
def test_api_delete_agent_not_implemented(client):
    """Test /api/agents/<id> DELETE returns 501"""
    response = client.delete("/api/agents/123")
    assert response.status_code == 501
    data = response.get_json()
    assert "error" in data


@pytest.mark.unit
def test_api_execute_agent_not_implemented(client):
    """Test /api/agents/<id>/execute POST returns 501"""
    response = client.post("/api/agents/123/execute", json={"message": "test"})
    assert response.status_code == 501
    data = response.get_json()
    assert "error" in data


@pytest.mark.unit
def test_api_list_schedules_returns_empty_array(client):
    """Test /api/schedules GET returns empty array"""
    response = client.get("/api/schedules")
    assert response.status_code == 200
    data = response.get_json()
    assert data == []


@pytest.mark.unit
def test_api_create_schedule_not_implemented(client):
    """Test /api/schedules POST returns 501"""
    response = client.post("/api/schedules", json={"name": "test"})
    assert response.status_code == 501
    data = response.get_json()
    assert "error" in data


@pytest.mark.unit
def test_api_delete_schedule_not_implemented(client):
    """Test /api/schedules/<id> DELETE returns 501"""
    response = client.delete("/api/schedules/123")
    assert response.status_code == 501
    data = response.get_json()
    assert "error" in data


@pytest.mark.unit  # Changed from integration - this mocks the database
def test_api_cost_summary_success(client, mock_asyncpg):
    """Test /api/costs/summary returns cost data (mocked DB)"""
    mock_asyncpg.fetchrow.return_value = {
        'total_usd': Decimal('123.45'),
        'total_tokens': 50000,
        'total_executions': 100
    }

    response = client.get("/api/costs/summary")
    assert response.status_code == 200

    data = response.get_json()
    assert 'total_usd' in data
    assert data['total_usd'] == 123.45  # Converted to float
    assert data['total_tokens'] == 50000
    assert data['total_executions'] == 100


@pytest.mark.unit  # Changed from integration - this mocks the database
def test_api_cost_summary_with_date_range(client, mock_asyncpg):
    """Test /api/costs/summary with date range parameters (mocked DB)"""
    mock_asyncpg.fetchrow.return_value = {
        'total_usd': Decimal('50.00'),
        'total_tokens': 25000,
        'total_executions': 50
    }

    response = client.get("/api/costs/summary?start_date=2025-01-01&end_date=2025-01-31")
    assert response.status_code == 200

    data = response.get_json()
    assert data['total_usd'] == 50.0
    assert data['total_tokens'] == 25000


@pytest.mark.unit  # Changed from integration - this mocks the database
def test_api_cost_summary_handles_null_values(client, mock_asyncpg):
    """Test /api/costs/summary handles null values from database (mocked DB)"""
    mock_asyncpg.fetchrow.return_value = {
        'total_usd': None,
        'total_tokens': 0,
        'total_executions': 0
    }

    response = client.get("/api/costs/summary")
    assert response.status_code == 200

    data = response.get_json()
    # Should handle None gracefully
    assert 'total_usd' in data


@pytest.mark.unit  # Changed from integration - this mocks the database
def test_api_cost_summary_error_handling(client):
    """Test /api/costs/summary handles database errors (mocked DB)"""
    with patch('app.get_db_connection', side_effect=Exception("Database error")):
        response = client.get("/api/costs/summary")
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data


@pytest.mark.unit  # Changed from integration - this mocks external services
def test_api_status_all_services_healthy(client):
    """Test /api/status with all services healthy (mocked services)"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = client.get("/api/status")
        assert response.status_code == 200

        data = response.get_json()
        assert 'agent_service' in data
        assert 'scheduler_service' in data
        assert data['agent_service']['healthy'] is True
        assert data['scheduler_service']['healthy'] is True


@pytest.mark.unit  # Changed from integration - this mocks external services
def test_api_status_service_unhealthy(client):
    """Test /api/status with unhealthy services (mocked services)"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        response = client.get("/api/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data['agent_service']['healthy'] is False
        assert data['agent_service']['status_code'] == 503


@pytest.mark.unit  # Changed from integration - this mocks external services
def test_api_status_service_timeout(client):
    """Test /api/status handles service timeouts (mocked services)"""
    with patch('requests.get', side_effect=Exception("Connection timeout")):
        response = client.get("/api/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data['agent_service']['healthy'] is False
        assert data['agent_service']['status_code'] == 0


@pytest.mark.unit  # Changed from integration - this mocks external services
def test_api_status_error_handling(client):
    """Test /api/status handles errors gracefully (mocked services)"""
    # The api_status function imports requests inside the function,
    # so it will succeed even if there are errors calling the services
    with patch('requests.get', side_effect=Exception("Connection error")):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.get_json()
        # Services should be marked unhealthy
        assert data['agent_service']['healthy'] is False
