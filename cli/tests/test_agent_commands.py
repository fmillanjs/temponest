"""
Tests for CLI agent commands
"""
import pytest
from unittest.mock import patch, Mock
from temponest_cli.cli import cli, agent
from temponest_sdk.exceptions import AgentNotFoundError


class TestAgentList:
    """Test agent list command"""

    def test_list_agents_success(self, runner, mock_client):
        """Test successful agent listing"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "list"])

        assert result.exit_code == 0
        assert "Test Agent" in result.output
        assert "llama3.2:latest" in result.output
        assert "ollama" in result.output
        mock_client.agents.list.assert_called_once_with(limit=20, search=None)

    def test_list_agents_with_limit(self, runner, mock_client):
        """Test agent listing with custom limit"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "list", "--limit", "50"])

        assert result.exit_code == 0
        mock_client.agents.list.assert_called_once_with(limit=50, search=None)

    def test_list_agents_with_search(self, runner, mock_client):
        """Test agent listing with search query"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "list", "--search", "developer"])

        assert result.exit_code == 0
        mock_client.agents.list.assert_called_once_with(limit=20, search="developer")

    def test_list_agents_empty(self, runner, mock_client):
        """Test listing agents when none exist"""
        mock_client.agents.list.return_value = []

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "list"])

        assert result.exit_code == 0
        assert "No agents found" in result.output

    def test_list_agents_error(self, runner, mock_client):
        """Test agent listing with API error"""
        mock_client.agents.list.side_effect = Exception("API Error")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "list"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestAgentCreate:
    """Test agent create command"""

    def test_create_agent_success(self, runner, mock_client):
        """Test successful agent creation"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "create",
                "--name", "Test Agent",
                "--model", "llama3.2:latest",
                "--description", "A test agent",
                "--system-prompt", "You are a helpful assistant",
                "--temperature", "0.8",
            ])

        assert result.exit_code == 0
        assert "Agent created successfully" in result.output
        assert "Test Agent" in result.output
        mock_client.agents.create.assert_called_once()

    def test_create_agent_minimal(self, runner, mock_client):
        """Test agent creation with minimal parameters"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "create",
                "--name", "Minimal Agent",
                "--model", "llama3.2:latest",
            ])

        assert result.exit_code == 0
        mock_client.agents.create.assert_called_once()

    def test_create_agent_missing_required(self, runner, mock_client):
        """Test agent creation without required fields"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "create"])

        assert result.exit_code != 0

    def test_create_agent_error(self, runner, mock_client):
        """Test agent creation with API error"""
        mock_client.agents.create.side_effect = Exception("Validation error")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "create",
                "--name", "Test",
                "--model", "llama3.2:latest",
            ])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestAgentGet:
    """Test agent get command"""

    def test_get_agent_success(self, runner, mock_client):
        """Test successful agent retrieval"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "get", "agent-123"])

        assert result.exit_code == 0
        assert "Agent Details" in result.output
        assert "Test Agent" in result.output
        assert "llama3.2:latest" in result.output
        mock_client.agents.get.assert_called_once_with("agent-123")

    def test_get_agent_not_found(self, runner, mock_client):
        """Test getting non-existent agent"""
        mock_client.agents.get.side_effect = AgentNotFoundError("Not found")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "get", "nonexistent"])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestAgentExecute:
    """Test agent execute command"""

    def test_execute_agent_success(self, runner, mock_client):
        """Test successful agent execution"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "execute",
                "agent-123",
                "Hello, agent!",
            ])

        assert result.exit_code == 0
        assert "Execution Result" in result.output
        assert "completed" in result.output
        assert "Test response from agent" in result.output
        mock_client.agents.execute.assert_called_once_with("agent-123", "Hello, agent!")

    def test_execute_agent_stream(self, runner, mock_client):
        """Test agent execution with streaming"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "execute",
                "--stream",
                "agent-123",
                "Hello!",
            ])

        assert result.exit_code == 0
        assert "Agent Response:" in result.output
        mock_client.agents.execute_stream.assert_called_once_with("agent-123", "Hello!")

    def test_execute_agent_error(self, runner, mock_client):
        """Test agent execution with error"""
        mock_client.agents.execute.side_effect = Exception("Execution failed")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "execute",
                "agent-123",
                "Test",
            ])

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestAgentDelete:
    """Test agent delete command"""

    def test_delete_agent_success(self, runner, mock_client):
        """Test successful agent deletion"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "delete",
                "agent-123",
                "--yes",  # Auto-confirm
            ])

        assert result.exit_code == 0
        assert "Agent deleted successfully" in result.output
        mock_client.agents.delete.assert_called_once_with("agent-123")

    def test_delete_agent_abort(self, runner, mock_client):
        """Test aborting agent deletion"""
        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, ["agent", "delete", "agent-123"], input="n\n")

        assert result.exit_code == 1  # Aborted
        mock_client.agents.delete.assert_not_called()

    def test_delete_agent_not_found(self, runner, mock_client):
        """Test deleting non-existent agent"""
        mock_client.agents.delete.side_effect = AgentNotFoundError("Not found")

        with patch("temponest_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(cli, [
                "agent", "delete",
                "nonexistent",
                "--yes",
            ])

        assert result.exit_code == 1
        assert "Error:" in result.output
