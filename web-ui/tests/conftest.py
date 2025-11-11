"""
Test fixtures for Web UI testing
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import app as web_app


@pytest.fixture
def app():
    """Create Flask app for testing"""
    web_app.app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    return web_app.app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def mock_temponest_client():
    """Mock Temponest SDK client"""
    with patch('app.TemponestClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    mock_conn = AsyncMock()

    # Mock fetchrow for single row queries
    mock_conn.fetchrow = AsyncMock(return_value={
        'total_usd': Decimal('123.45'),
        'total_tokens': 50000,
        'total_executions': 100
    })

    # Mock fetch for multiple row queries
    mock_conn.fetch = AsyncMock(return_value=[
        {
            'task_id': 'task-123',
            'agent_name': 'developer',
            'model_provider': 'anthropic',
            'model_name': 'claude-3-opus',
            'total_tokens': 1000,
            'total_cost_usd': Decimal('1.50'),
            'latency_ms': 250,
            'status': 'completed',
            'created_at': datetime.now(),
            'workflow_id': 'workflow-1',
            'project_id': 'project-1'
        }
    ])

    # Mock close
    mock_conn.close = AsyncMock()

    with patch('app.get_db_connection', return_value=mock_conn):
        yield mock_conn


@pytest.fixture
def mock_asyncpg():
    """Mock asyncpg module"""
    mock_conn = AsyncMock()

    # Default responses for different query types
    mock_conn.fetchrow = AsyncMock(return_value={
        'total_usd': Decimal('123.45'),
        'total_tokens': 50000,
        'total_executions': 100
    })

    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.close = AsyncMock()

    with patch('asyncpg.connect', return_value=mock_conn):
        yield mock_conn


@pytest.fixture
def mock_prometheus():
    """Mock Prometheus queries"""
    def mock_query(query):
        return [
            {
                'metric': {'agent_name': 'developer'},
                'value': [1234567890, '5']
            }
        ]

    with patch('app.query_prometheus', side_effect=mock_query) as mock:
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch('app.requests') as mock_req:
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'result': [
                    {
                        'metric': {'agent_name': 'developer'},
                        'value': [1234567890, '5']
                    }
                ]
            }
        }
        mock_req.get.return_value = mock_response
        yield mock_req


@pytest.fixture
def mock_yaml_departments():
    """Mock department YAML files"""
    mock_departments = [
        {
            'department': {
                'id': 'engineering',
                'name': 'Engineering',
                'parent': None,
                'agents': [
                    {'id': 'developer', 'name': 'Developer'},
                    {'id': 'qa', 'name': 'QA Tester'}
                ],
                'workflows': [
                    {
                        'id': 'build-deploy',
                        'name': 'Build and Deploy',
                        'steps': ['build', 'test', 'deploy']
                    }
                ]
            }
        },
        {
            'department': {
                'id': 'design',
                'name': 'Design',
                'parent': None,
                'agents': [
                    {'id': 'designer', 'name': 'UI Designer'}
                ],
                'workflows': []
            }
        }
    ]

    # Mock Path.glob to return mock files
    mock_files = []
    for dept in mock_departments:
        mock_file = Mock()
        mock_file.name = f"{dept['department']['id']}.yaml"
        mock_files.append(mock_file)

    # Mock open to return department config
    def mock_open_file(file_path, mode='r'):
        mock_file = MagicMock()
        if 'engineering' in str(file_path):
            mock_file.__enter__.return_value = Mock(read=lambda: str(mock_departments[0]))
        else:
            mock_file.__enter__.return_value = Mock(read=lambda: str(mock_departments[1]))
        return mock_file

    with patch('pathlib.Path.glob') as mock_glob:
        mock_glob.return_value = mock_files
        with patch('yaml.safe_load') as mock_yaml:
            mock_yaml.side_effect = mock_departments
            yield mock_departments


@pytest.fixture
def sample_cost_summary():
    """Sample cost summary data"""
    return {
        'total_usd': 123.45,
        'total_tokens': 50000,
        'total_executions': 100
    }


@pytest.fixture
def sample_executions():
    """Sample execution data"""
    return [
        {
            'task_id': f'task-{i}',
            'agent_name': 'developer' if i % 2 == 0 else 'designer',
            'model_provider': 'anthropic',
            'model_name': 'claude-3-opus',
            'total_tokens': 1000 + i * 100,
            'total_cost_usd': 1.50 + i * 0.1,
            'latency_ms': 250 + i * 10,
            'status': 'completed' if i % 3 != 0 else 'failed',
            'created_at': (datetime.now() - timedelta(hours=i)).isoformat(),
            'workflow_id': f'workflow-{i // 3}',
            'project_id': 'project-1'
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_agent_stats():
    """Sample agent statistics"""
    return [
        {
            'agent_name': 'developer',
            'total_executions': 50,
            'total_cost_usd': 75.25,
            'avg_latency_ms': 245.5,
            'first_execution': datetime.now() - timedelta(days=7),
            'last_execution': datetime.now()
        },
        {
            'agent_name': 'designer',
            'total_executions': 30,
            'total_cost_usd': 45.50,
            'avg_latency_ms': 180.2,
            'first_execution': datetime.now() - timedelta(days=5),
            'last_execution': datetime.now() - timedelta(hours=2)
        }
    ]


@pytest.fixture
def sample_dashboard_data():
    """Sample dashboard analytics data"""
    return {
        'overall': {
            'total_executions': 100,
            'unique_agents': 5,
            'total_tokens': 50000,
            'total_cost': Decimal('123.45'),
            'avg_latency': 250.5,
            'total_failures': 5,
            'last_24h_executions': 25
        },
        'hourly_trend': [
            {
                'hour': datetime.now() - timedelta(hours=i),
                'executions': 10 - i,
                'avg_latency': 250 + i * 10
            }
            for i in range(24)
        ],
        'top_agents': [
            {'agent_name': 'developer', 'executions': 50, 'cost': Decimal('75.25')},
            {'agent_name': 'designer', 'executions': 30, 'cost': Decimal('45.50')},
        ]
    }
