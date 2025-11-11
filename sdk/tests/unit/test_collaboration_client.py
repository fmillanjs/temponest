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

            session = collab_client.create_session(
                name="Build Feature",
                pattern="sequential",
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

            session = collab_client.create_session(
                name="Parallel Tasks",
                pattern="parallel",
                agent_ids=["agent-1", "agent-2"],
                initial_message="Run tasks"
            )

            assert session.pattern == "parallel"

    def test_create_session_hierarchical(self, clean_env, mock_collaboration_session_data):
        """Test creating hierarchical collaboration session"""
        hierarchical_data = {**mock_collaboration_session_data, "pattern": "hierarchical"}
        with patch.object(BaseClient, 'post', return_value=hierarchical_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            session = collab_client.create_session(
                name="Hierarchical Project",
                pattern="hierarchical",
                agent_ids=["overseer", "agent-1", "agent-2"],
                initial_message="Coordinate work"
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

    def test_send_message_to_session(self, clean_env):
        """Test sending message to session"""
        response_data = {"status": "message_received", "agent_id": "agent-2"}
        with patch.object(BaseClient, 'post', return_value=response_data) as mock_post:
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            result = collab_client.send_message(
                "collab-123",
                "Continue with next step"
            )

            assert result["status"] == "message_received"
            call_args = mock_post.call_args
            assert call_args[1]['json']['message'] == "Continue with next step"

    def test_stop_session(self, clean_env, mock_collaboration_session_data):
        """Test stopping a session"""
        stopped_data = {**mock_collaboration_session_data, "status": "stopped"}
        with patch.object(BaseClient, 'post', return_value=stopped_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            session = collab_client.stop_session("collab-123")

            assert session.status == "stopped"

    def test_delete_session(self, clean_env):
        """Test deleting a session"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            collab_client.delete_session("collab-123")
            # No exception means success


class TestCollaborationClientResults:
    """Test getting session results"""

    def test_get_session_results(self, clean_env):
        """Test getting session results"""
        results_data = {
            "session_id": "collab-123",
            "pattern": "sequential",
            "agent_results": [
                {"agent_id": "agent-1", "output": "Design complete"},
                {"agent_id": "agent-2", "output": "Implementation complete"}
            ],
            "final_output": "Feature completed"
        }
        with patch.object(BaseClient, 'get', return_value=results_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            results = collab_client.get_results("collab-123")

            assert results["session_id"] == "collab-123"
            assert len(results["agent_results"]) == 2

    def test_get_session_messages(self, clean_env):
        """Test getting session message history"""
        messages_data = [
            {"role": "user", "content": "Start task"},
            {"role": "agent-1", "content": "Working on design"},
            {"role": "agent-2", "content": "Implementing feature"}
        ]
        with patch.object(BaseClient, 'get', return_value=messages_data):
            client = BaseClient(base_url="http://test.com")
            collab_client = CollaborationClient(client)

            messages = collab_client.get_messages("collab-123")

            assert len(messages) == 3
            assert messages[0]["role"] == "user"
