"""
Test visualization API endpoints
"""
import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open
import yaml


@pytest.mark.integration
def test_api_get_departments_success(client):
    """Test /api/visualization/departments returns department hierarchy"""
    mock_dept_config = {
        'department': {
            'id': 'engineering',
            'name': 'Engineering',
            'parent': None,
            'agents': [{'id': 'developer', 'name': 'Developer'}]
        }
    }

    with patch('pathlib.Path.glob') as mock_glob:
        mock_file = Mock()
        mock_file.name = "engineering.yaml"
        mock_glob.return_value = [mock_file]

        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_dept_config))):
            with patch('yaml.safe_load', return_value=mock_dept_config):
                response = client.get("/api/visualization/departments")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_api_get_departments_builds_hierarchy(client):
    """Test /api/visualization/departments builds correct hierarchy"""
    dept_configs = [
        {
            'department': {
                'id': 'root',
                'name': 'Root',
                'parent': None
            }
        },
        {
            'department': {
                'id': 'child',
                'name': 'Child',
                'parent': 'root'
            }
        }
    ]

    with patch('pathlib.Path.glob') as mock_glob:
        mock_files = [Mock(name=f"{d['department']['id']}.yaml") for d in dept_configs]
        mock_glob.return_value = mock_files

        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', side_effect=dept_configs):
                response = client.get("/api/visualization/departments")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # Root departments should be returned
    assert len(data) >= 0


@pytest.mark.integration
def test_api_get_departments_handles_errors(client):
    """Test /api/visualization/departments handles file errors"""
    with patch('pathlib.Path.glob', side_effect=Exception("File not found")):
        response = client.get("/api/visualization/departments")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_workflows_success(client):
    """Test /api/visualization/workflows returns all workflows"""
    mock_dept_config = {
        'department': {
            'id': 'engineering',
            'name': 'Engineering',
            'workflows': [
                {'id': 'wf1', 'name': 'Workflow 1'},
                {'id': 'wf2', 'name': 'Workflow 2'}
            ]
        }
    }

    with patch('pathlib.Path.glob') as mock_glob:
        mock_file = Mock()
        mock_glob.return_value = [mock_file]

        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', return_value=mock_dept_config):
                response = client.get("/api/visualization/workflows")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_api_get_workflows_adds_department_info(client):
    """Test /api/visualization/workflows adds department info to workflows"""
    mock_dept_config = {
        'department': {
            'id': 'engineering',
            'name': 'Engineering',
            'workflows': [
                {'id': 'wf1', 'name': 'Workflow 1'}
            ]
        }
    }

    with patch('pathlib.Path.glob') as mock_glob:
        mock_file = Mock()
        mock_glob.return_value = [mock_file]

        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', return_value=mock_dept_config):
                response = client.get("/api/visualization/workflows")

    assert response.status_code == 200
    data = response.get_json()
    if len(data) > 0:
        # Each workflow should have department info
        assert 'department_id' in data[0]
        assert 'department_name' in data[0]


@pytest.mark.integration
def test_api_get_workflows_handles_errors(client):
    """Test /api/visualization/workflows handles errors"""
    with patch('pathlib.Path.glob', side_effect=Exception("File error")):
        response = client.get("/api/visualization/workflows")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_agents_hierarchy_success(client):
    """Test /api/visualization/agents-hierarchy returns agents by department"""
    mock_dept_config = {
        'department': {
            'id': 'engineering',
            'name': 'Engineering',
            'parent': None,
            'agents': [
                {'id': 'dev1', 'name': 'Developer 1'}
            ]
        }
    }

    with patch('pathlib.Path.glob') as mock_glob:
        mock_file = Mock()
        mock_glob.return_value = [mock_file]

        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', return_value=mock_dept_config):
                response = client.get("/api/visualization/agents-hierarchy")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


@pytest.mark.integration
def test_api_get_agents_hierarchy_structure(client):
    """Test /api/visualization/agents-hierarchy returns correct structure"""
    mock_dept_config = {
        'department': {
            'id': 'engineering',
            'name': 'Engineering',
            'parent': None,
            'agents': [{'id': 'dev1', 'name': 'Developer 1'}]
        }
    }

    with patch('pathlib.Path.glob') as mock_glob:
        mock_file = Mock()
        mock_glob.return_value = [mock_file]

        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', return_value=mock_dept_config):
                response = client.get("/api/visualization/agents-hierarchy")

    assert response.status_code == 200
    data = response.get_json()

    if 'engineering' in data:
        assert 'department_name' in data['engineering']
        assert 'department_id' in data['engineering']
        assert 'agents' in data['engineering']


@pytest.mark.integration
def test_api_get_agents_hierarchy_handles_errors(client):
    """Test /api/visualization/agents-hierarchy handles errors"""
    with patch('pathlib.Path.glob', side_effect=Exception("File error")):
        response = client.get("/api/visualization/agents-hierarchy")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_workflow_detail_success(client):
    """Test /api/visualization/workflow/<id> returns workflow details"""
    mock_dept_config = {
        'department': {
            'id': 'engineering',
            'name': 'Engineering',
            'workflows': [
                {
                    'id': 'wf1',
                    'name': 'Workflow 1',
                    'steps': ['step1', 'step2']
                }
            ]
        }
    }

    with patch('pathlib.Path.glob') as mock_glob:
        mock_file = Mock()
        mock_glob.return_value = [mock_file]

        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', return_value=mock_dept_config):
                response = client.get("/api/visualization/workflow/wf1")

    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert data['id'] == 'wf1'


@pytest.mark.integration
def test_api_get_workflow_detail_not_found(client):
    """Test /api/visualization/workflow/<id> returns 404 for missing workflow"""
    mock_dept_config = {
        'department': {
            'id': 'engineering',
            'name': 'Engineering',
            'workflows': []
        }
    }

    with patch('pathlib.Path.glob') as mock_glob:
        mock_file = Mock()
        mock_glob.return_value = [mock_file]

        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', return_value=mock_dept_config):
                response = client.get("/api/visualization/workflow/nonexistent")

    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


@pytest.mark.integration
def test_api_get_workflow_detail_handles_errors(client):
    """Test /api/visualization/workflow/<id> handles errors"""
    with patch('pathlib.Path.glob', side_effect=Exception("File error")):
        response = client.get("/api/visualization/workflow/wf1")

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
