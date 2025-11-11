"""
Unit tests for CollaborationClient
"""
import pytest
from unittest.mock import Mock, patch
from temponest_sdk.collaboration import CollaborationClient
from temponest_sdk.client import BaseClient
from temponest_sdk.models import CollaborationSession


class TestCollaborationClientCreate:
    """Test collaboration session creation"""

    def test_create_session_sequential(self, clean_env, mock_collaboration_session_data):
        """Test creating sequential collaboration session"""
        with patch.object(BaseClient, 'post', return_value=mock_collaboration_session_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            session = collab_client.execute_sequential(
                agent_ids=["agent-1", "agent-2", "agent-3"],
                initial_message="Build a new feature"
            )

            assert isinstance(session, CollaborationSession)
            assert session.id == "collab-123"
            assert session.pattern == "sequential"

    def test_create_session_parallel(self, clean_env, mock_collaboration_session_data):
        """Test creating parallel collaboration session"""
        parallel_data = {**mock_collaboration_session_data, "pattern": "parallel"}
        with patch.object(BaseClient, 'post', return_value=parallel_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            session = collab_client.execute_parallel(
                agent_ids=["agent-1", "agent-2"],
                messages=["Task 1", "Task 2"]
            )

            assert session.pattern == "parallel"

    def test_create_session_hierarchical(self, clean_env, mock_collaboration_session_data):
        """Test creating hierarchical collaboration session"""
        hierarchical_data = {**mock_collaboration_session_data, "pattern": "hierarchical"}
        with patch.object(BaseClient, 'post', return_value=hierarchical_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            session = collab_client.execute_hierarchical(
                coordinator_id="overseer",
                worker_ids=["agent-1", "agent-2"],
                task="Coordinate work"
            )

            assert session.pattern == "hierarchical"


class TestCollaborationClientGet:
    """Test getting collaboration session"""

    def test_get_session_success(self, clean_env, mock_collaboration_session_data):
        """Test getting session by ID"""
        with patch.object(BaseClient, 'get', return_value=mock_collaboration_session_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            session = collab_client.get_session("collab-123")

            assert isinstance(session, CollaborationSession)
            assert session.id == "collab-123"

    def test_get_session_not_found(self, clean_env):
        """Test getting non-existent session"""
        with patch.object(BaseClient, 'get', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            with pytest.raises(Exception, match="404"):
                collab_client.get_session("collab-123")


class TestCollaborationClientList:
    """Test listing collaboration sessions"""

    def test_list_sessions(self, clean_env, mock_collaboration_session_data):
        """Test listing all sessions"""
        with patch.object(BaseClient, 'get', return_value=[mock_collaboration_session_data]):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            sessions = collab_client.list_sessions()

            assert len(sessions) == 1
            assert isinstance(sessions[0], CollaborationSession)

    def test_list_sessions_by_pattern(self, clean_env, mock_collaboration_session_data):
        """Test listing sessions filtered by pattern"""
        with patch.object(BaseClient, 'get', return_value=[mock_collaboration_session_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            sessions = collab_client.list_sessions(pattern="sequential")

            call_args = mock_get.call_args
            assert call_args[1]['params']['pattern'] == "sequential"

    def test_list_sessions_by_status(self, clean_env, mock_collaboration_session_data):
        """Test listing sessions filtered by status"""
        with patch.object(BaseClient, 'get', return_value=[mock_collaboration_session_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            sessions = collab_client.list_sessions(status="completed")

            call_args = mock_get.call_args
            assert call_args[1]['params']['status'] == "completed"


class TestCollaborationClientControl:
    """Test session control operations"""

    def test_cancel_session(self, clean_env):
        """Test canceling a session"""
        with patch.object(BaseClient, 'post', return_value=None):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            collab_client.cancel_session("collab-123")
            # No exception means success


class TestCollaborationClientIterative:
    """Test iterative collaboration pattern"""

    def test_execute_iterative(self, clean_env, mock_collaboration_session_data):
        """Test iterative collaboration pattern"""
        iterative_data = {**mock_collaboration_session_data, "pattern": "iterative"}
        with patch.object(BaseClient, 'post', return_value=iterative_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            session = collab_client.execute_iterative(
                agent_ids=["generator", "critic"],
                initial_message="Design a logo",
                max_iterations=5
            )

            assert session.pattern == "iterative"
