"""
Unit tests for AgentsClient
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from temponest_sdk.agents import AgentsClient, AsyncAgentsClient
from temponest_sdk.client import BaseClient, AsyncBaseClient
from temponest_sdk.models import Agent, AgentExecution
from temponest_sdk.exceptions import AgentNotFoundError


class TestAgentsClientCreate:
    """Test agent creation"""

    def test_create_agent_minimal(self, clean_env, mock_agent_data):
        """Test creating agent with minimal parameters"""
        with patch.object(BaseClient, 'post', return_value=mock_agent_data):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agent = agents_client.create(
                name="TestAgent",
                model="llama3.2:latest"
            )

            assert isinstance(agent, Agent)
            assert agent.id == "agent-123"
            assert agent.name == "TestAgent"

    def test_create_agent_full(self, clean_env, mock_agent_data):
        """Test creating agent with all parameters"""
        with patch.object(BaseClient, 'post', return_value=mock_agent_data):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agent = agents_client.create(
                name="TestAgent",
                model="llama3.2:latest",
                description="Test description",
                provider="ollama",
                system_prompt="You are helpful",
                tools=["web_search"],
                rag_collection_ids=["col-1"],
                max_iterations=5,
                temperature=0.5,
                metadata={"key": "value"}
            )

            assert agent.id == "agent-123"
            assert agent.name == "TestAgent"
            assert agent.temperature == 0.7  # From mock data


class TestAgentsClientGet:
    """Test getting agent"""

    def test_get_agent_success(self, clean_env, mock_agent_data):
        """Test getting agent by ID"""
        with patch.object(BaseClient, 'get', return_value=mock_agent_data):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agent = agents_client.get("agent-123")

            assert isinstance(agent, Agent)
            assert agent.id == "agent-123"
            assert agent.name == "TestAgent"

    def test_get_agent_not_found(self, clean_env):
        """Test getting non-existent agent"""
        with patch.object(BaseClient, 'get', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            with pytest.raises(AgentNotFoundError, match="Agent agent-123 not found"):
                agents_client.get("agent-123")


class TestAgentsClientList:
    """Test listing agents"""

    def test_list_agents_default(self, clean_env, mock_agent_data):
        """Test listing agents with default parameters"""
        with patch.object(BaseClient, 'get', return_value=[mock_agent_data]):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agents = agents_client.list()

            assert len(agents) == 1
            assert isinstance(agents[0], Agent)
            assert agents[0].id == "agent-123"

    def test_list_agents_with_pagination(self, clean_env, mock_agent_data):
        """Test listing agents with pagination"""
        with patch.object(BaseClient, 'get', return_value=[mock_agent_data, mock_agent_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agents = agents_client.list(skip=10, limit=20)

            assert len(agents) == 2
            # Verify params were passed
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]['params']['skip'] == 10
            assert call_args[1]['params']['limit'] == 20

    def test_list_agents_with_search(self, clean_env, mock_agent_data):
        """Test listing agents with search"""
        with patch.object(BaseClient, 'get', return_value=[mock_agent_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agents = agents_client.list(search="test")

            assert len(agents) == 1
            call_args = mock_get.call_args
            assert call_args[1]['params']['search'] == "test"

    def test_list_agents_empty(self, clean_env):
        """Test listing agents when none exist"""
        with patch.object(BaseClient, 'get', return_value=[]):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agents = agents_client.list()

            assert agents == []


class TestAgentsClientUpdate:
    """Test updating agent"""

    def test_update_agent_name(self, clean_env, mock_agent_data):
        """Test updating agent name"""
        updated_data = {**mock_agent_data, "name": "UpdatedAgent"}
        with patch.object(BaseClient, 'patch', return_value=updated_data) as mock_patch:
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agent = agents_client.update("agent-123", name="UpdatedAgent")

            assert agent.name == "UpdatedAgent"
            # Verify only name was in update payload
            call_args = mock_patch.call_args
            assert call_args[1]['json'] == {"name": "UpdatedAgent"}

    def test_update_agent_multiple_fields(self, clean_env, mock_agent_data):
        """Test updating multiple fields"""
        with patch.object(BaseClient, 'patch', return_value=mock_agent_data) as mock_patch:
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agent = agents_client.update(
                "agent-123",
                name="Updated",
                description="New description",
                temperature=0.9
            )

            call_args = mock_patch.call_args
            update_data = call_args[1]['json']
            assert update_data["name"] == "Updated"
            assert update_data["description"] == "New description"
            assert update_data["temperature"] == 0.9

    def test_update_agent_not_found(self, clean_env):
        """Test updating non-existent agent"""
        with patch.object(BaseClient, 'patch', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            with pytest.raises(AgentNotFoundError):
                agents_client.update("agent-123", name="Updated")


class TestAgentsClientDelete:
    """Test deleting agent"""

    def test_delete_agent_success(self, clean_env):
        """Test deleting agent"""
        with patch.object(BaseClient, 'delete', return_value=None):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            agents_client.delete("agent-123")
            # No exception means success

    def test_delete_agent_not_found(self, clean_env):
        """Test deleting non-existent agent"""
        with patch.object(BaseClient, 'delete', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            with pytest.raises(AgentNotFoundError):
                agents_client.delete("agent-123")


class TestAgentsClientExecute:
    """Test executing agent"""

    def test_execute_agent_minimal(self, clean_env, mock_agent_execution_data):
        """Test executing agent with minimal parameters"""
        with patch.object(BaseClient, 'post', return_value=mock_agent_execution_data):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            execution = agents_client.execute(
                agent_id="agent-123",
                user_message="Hello!"
            )

            assert isinstance(execution, AgentExecution)
            assert execution.id == "exec-123"
            assert execution.agent_id == "agent-123"
            assert execution.status == "completed"

    def test_execute_agent_with_context(self, clean_env, mock_agent_execution_data):
        """Test executing agent with context"""
        with patch.object(BaseClient, 'post', return_value=mock_agent_execution_data) as mock_post:
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            execution = agents_client.execute(
                agent_id="agent-123",
                user_message="Hello!",
                context={"session_id": "session-1"}
            )

            assert execution.id == "exec-123"
            # Verify context was passed
            call_args = mock_post.call_args
            assert call_args[1]['json']['context'] == {"session_id": "session-1"}

    def test_execute_agent_not_found(self, clean_env):
        """Test executing non-existent agent"""
        with patch.object(BaseClient, 'post', side_effect=Exception("404")):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            with pytest.raises(AgentNotFoundError):
                agents_client.execute("agent-123", "Hello!")


class TestAgentsClientExecuteStream:
    """Test streaming agent execution"""

    def test_execute_stream(self, clean_env):
        """Test streaming execution"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            "data: {\"content\": \"Hello\"}",
            "data: {\"content\": \" world\"}",
            "data: [DONE]"
        ]

        with patch('httpx.stream') as mock_stream:
            mock_stream.return_value.__enter__.return_value = mock_response

            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            chunks = list(agents_client.execute_stream("agent-123", "Hello!"))

            assert chunks == ["Hello", " world"]

    def test_execute_stream_agent_not_found(self, clean_env):
        """Test streaming from non-existent agent"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}

        with patch('httpx.stream') as mock_stream:
            mock_stream.return_value.__enter__.return_value = mock_response

            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            with pytest.raises(AgentNotFoundError):
                list(agents_client.execute_stream("agent-123", "Hello!"))


class TestAgentsClientExecutions:
    """Test execution management"""

    def test_get_execution(self, clean_env, mock_agent_execution_data):
        """Test getting execution by ID"""
        with patch.object(BaseClient, 'get', return_value=mock_agent_execution_data):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            execution = agents_client.get_execution("exec-123")

            assert isinstance(execution, AgentExecution)
            assert execution.id == "exec-123"

    def test_list_executions_default(self, clean_env, mock_agent_execution_data):
        """Test listing executions"""
        with patch.object(BaseClient, 'get', return_value=[mock_agent_execution_data]):
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            executions = agents_client.list_executions()

            assert len(executions) == 1
            assert isinstance(executions[0], AgentExecution)

    def test_list_executions_by_agent(self, clean_env, mock_agent_execution_data):
        """Test listing executions for specific agent"""
        with patch.object(BaseClient, 'get', return_value=[mock_agent_execution_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            executions = agents_client.list_executions(agent_id="agent-123")

            assert len(executions) == 1
            call_args = mock_get.call_args
            assert call_args[1]['params']['agent_id'] == "agent-123"

    def test_list_executions_by_status(self, clean_env, mock_agent_execution_data):
        """Test listing executions by status"""
        with patch.object(BaseClient, 'get', return_value=[mock_agent_execution_data]) as mock_get:
            client = BaseClient(base_url="http://test.com")
            agents_client = AgentsClient(client)

            executions = agents_client.list_executions(status="completed")

            call_args = mock_get.call_args
            assert call_args[1]['params']['status'] == "completed"


# ==================== AsyncAgentsClient Tests ====================

class TestAsyncAgentsClient:
    """Test async agents client"""

    @pytest.mark.asyncio
    async def test_async_create_agent(self, clean_env, mock_agent_data):
        """Test async agent creation"""
        with patch.object(AsyncBaseClient, 'post', return_value=mock_agent_data):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            agent = await agents_client.create(
                name="TestAgent",
                model="llama3.2:latest"
            )

            assert isinstance(agent, Agent)
            assert agent.id == "agent-123"

    @pytest.mark.asyncio
    async def test_async_get_agent(self, clean_env, mock_agent_data):
        """Test async get agent"""
        with patch.object(AsyncBaseClient, 'get', return_value=mock_agent_data):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            agent = await agents_client.get("agent-123")

            assert agent.id == "agent-123"

    @pytest.mark.asyncio
    async def test_async_list_agents(self, clean_env, mock_agent_data):
        """Test async list agents"""
        with patch.object(AsyncBaseClient, 'get', return_value=[mock_agent_data]):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            agents = await agents_client.list()

            assert len(agents) == 1

    @pytest.mark.asyncio
    async def test_async_update_agent(self, clean_env, mock_agent_data):
        """Test async update agent"""
        with patch.object(AsyncBaseClient, 'patch', return_value=mock_agent_data):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            agent = await agents_client.update("agent-123", name="Updated")

            assert agent.id == "agent-123"

    @pytest.mark.asyncio
    async def test_async_delete_agent(self, clean_env):
        """Test async delete agent"""
        with patch.object(AsyncBaseClient, 'delete', return_value=None):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            await agents_client.delete("agent-123")
            # No exception means success

    @pytest.mark.asyncio
    async def test_async_execute_agent(self, clean_env, mock_agent_execution_data):
        """Test async execute agent"""
        with patch.object(AsyncBaseClient, 'post', return_value=mock_agent_execution_data):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            execution = await agents_client.execute("agent-123", "Hello!")

            assert execution.id == "exec-123"

    @pytest.mark.asyncio
    async def test_async_get_execution(self, clean_env, mock_agent_execution_data):
        """Test async get execution"""
        with patch.object(AsyncBaseClient, 'get', return_value=mock_agent_execution_data):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            execution = await agents_client.get_execution("exec-123")

            assert execution.id == "exec-123"

    @pytest.mark.asyncio
    async def test_async_list_executions(self, clean_env, mock_agent_execution_data):
        """Test async list executions"""
        with patch.object(AsyncBaseClient, 'get', return_value=[mock_agent_execution_data]):
            client = AsyncBaseClient(base_url="http://test.com")
            agents_client = AsyncAgentsClient(client)

            executions = await agents_client.list_executions()

            assert len(executions) == 1
