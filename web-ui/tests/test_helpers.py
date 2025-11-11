"""
Test helper functions and utilities
"""
import pytest
from unittest.mock import patch, Mock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import app


@pytest.mark.unit
def test_get_client():
    """Test get_client returns TemponestClient"""
    with patch('app.TemponestClient') as mock_client:
        client = app.get_client()
        mock_client.assert_called_once()
        assert client is not None


@pytest.mark.unit
def test_get_client_with_env_vars():
    """Test get_client uses environment variables"""
    with patch('app.BASE_URL', 'http://test:9000'):
        with patch('app.AUTH_TOKEN', 'test-token'):
            with patch('app.TemponestClient') as mock_client:
                app.get_client()
                mock_client.assert_called_with(
                    base_url='http://test:9000',
                    auth_token='test-token'
                )


@pytest.mark.unit
def test_build_department_hierarchy_single_root():
    """Test build_department_hierarchy with single root department"""
    departments = [
        {
            'id': 'root',
            'name': 'Root Department',
            'parent': None
        }
    ]

    result = app.build_department_hierarchy(departments)

    assert len(result) == 1
    assert result[0]['id'] == 'root'
    assert 'children' in result[0]
    assert len(result[0]['children']) == 0


@pytest.mark.unit
def test_build_department_hierarchy_with_children():
    """Test build_department_hierarchy builds correct tree"""
    departments = [
        {
            'id': 'root',
            'name': 'Root',
            'parent': None
        },
        {
            'id': 'child1',
            'name': 'Child 1',
            'parent': 'root'
        },
        {
            'id': 'child2',
            'name': 'Child 2',
            'parent': 'root'
        }
    ]

    result = app.build_department_hierarchy(departments)

    assert len(result) == 1  # One root
    assert result[0]['id'] == 'root'
    assert len(result[0]['children']) == 2
    child_ids = [c['id'] for c in result[0]['children']]
    assert 'child1' in child_ids
    assert 'child2' in child_ids


@pytest.mark.unit
def test_build_department_hierarchy_multiple_roots():
    """Test build_department_hierarchy with multiple root departments"""
    departments = [
        {
            'id': 'root1',
            'name': 'Root 1',
            'parent': None
        },
        {
            'id': 'root2',
            'name': 'Root 2',
            'parent': None
        }
    ]

    result = app.build_department_hierarchy(departments)

    assert len(result) == 2
    root_ids = [r['id'] for r in result]
    assert 'root1' in root_ids
    assert 'root2' in root_ids


@pytest.mark.unit
def test_build_department_hierarchy_nested_levels():
    """Test build_department_hierarchy with multiple nesting levels"""
    departments = [
        {
            'id': 'root',
            'name': 'Root',
            'parent': None
        },
        {
            'id': 'child',
            'name': 'Child',
            'parent': 'root'
        },
        {
            'id': 'grandchild',
            'name': 'Grandchild',
            'parent': 'child'
        }
    ]

    result = app.build_department_hierarchy(departments)

    assert len(result) == 1
    assert result[0]['id'] == 'root'
    assert len(result[0]['children']) == 1
    assert result[0]['children'][0]['id'] == 'child'
    assert len(result[0]['children'][0]['children']) == 1
    assert result[0]['children'][0]['children'][0]['id'] == 'grandchild'


@pytest.mark.unit
def test_build_department_hierarchy_orphaned_departments():
    """Test build_department_hierarchy handles orphaned departments"""
    departments = [
        {
            'id': 'root',
            'name': 'Root',
            'parent': None
        },
        {
            'id': 'orphan',
            'name': 'Orphan',
            'parent': 'nonexistent'
        }
    ]

    result = app.build_department_hierarchy(departments)

    # Should still return root, orphan won't be added to tree
    assert len(result) == 1
    assert result[0]['id'] == 'root'


@pytest.mark.unit
def test_build_department_hierarchy_empty_list():
    """Test build_department_hierarchy with empty list"""
    result = app.build_department_hierarchy([])
    assert result == []


@pytest.mark.integration
def test_query_prometheus_success():
    """Test query_prometheus returns data successfully"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'data': {
            'result': [
                {
                    'metric': {'agent': 'test'},
                    'value': [1234567890, '42']
                }
            ]
        }
    }

    with patch('app.requests.get', return_value=mock_response):
        result = app.query_prometheus('test_query')

    assert len(result) == 1
    assert result[0]['metric']['agent'] == 'test'
    assert result[0]['value'][1] == '42'


@pytest.mark.integration
def test_query_prometheus_uses_correct_url():
    """Test query_prometheus uses correct Prometheus URL"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {'data': {'result': []}}

    with patch('app.PROMETHEUS_URL', 'http://test-prometheus:9090'):
        with patch('app.requests.get', return_value=mock_response) as mock_get:
            app.query_prometheus('test_query')

            mock_get.assert_called_once()
            call_url = mock_get.call_args[0][0]
            assert 'http://test-prometheus:9090' in call_url
            assert '/api/v1/query' in call_url


@pytest.mark.integration
def test_query_prometheus_passes_query_param():
    """Test query_prometheus passes query as parameter"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {'data': {'result': []}}

    with patch('app.requests.get', return_value=mock_response) as mock_get:
        app.query_prometheus('my_metric')

        call_params = mock_get.call_args[1]['params']
        assert call_params['query'] == 'my_metric'


@pytest.mark.integration
def test_query_prometheus_handles_http_error():
    """Test query_prometheus handles HTTP errors"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 500

    with patch('app.requests.get', return_value=mock_response):
        result = app.query_prometheus('test_query')

    assert result == []


@pytest.mark.integration
def test_query_prometheus_handles_timeout():
    """Test query_prometheus handles connection timeout"""
    with patch('app.requests.get', side_effect=Exception("Timeout")):
        result = app.query_prometheus('test_query')

    assert result == []


@pytest.mark.integration
def test_query_prometheus_handles_malformed_response():
    """Test query_prometheus handles malformed JSON response"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {'invalid': 'structure'}

    with patch('app.requests.get', return_value=mock_response):
        result = app.query_prometheus('test_query')

    assert result == []


@pytest.mark.integration
def test_query_prometheus_timeout_parameter():
    """Test query_prometheus uses 5 second timeout"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {'data': {'result': []}}

    with patch('app.requests.get', return_value=mock_response) as mock_get:
        app.query_prometheus('test_query')

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 5
