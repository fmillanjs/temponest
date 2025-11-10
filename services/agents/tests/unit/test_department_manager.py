"""
Unit tests for departments/manager.py
Tests DepartmentManager and DynamicAgent classes.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, Any

from app.departments.manager import (
    AgentConfig,
    WorkflowConfig,
    Department,
    DepartmentManager,
    DynamicAgent
)


class TestDepartmentDataclasses:
    """Test Department dataclasses"""

    def test_department_get_full_path_no_parent(self):
        """Test Department.get_full_path() without parent"""
        dept = Department(
            id="marketing",
            name="Marketing",
            description="Marketing department",
            parent=None,
            budget={"monthly": 10000}
        )

        assert dept.get_full_path() == "marketing"

    def test_department_get_full_path_with_parent(self):
        """Test Department.get_full_path() with parent"""
        dept = Department(
            id="video_production",
            name="Video Production",
            description="Video production team",
            parent="marketing",
            budget={"monthly": 5000}
        )

        assert dept.get_full_path() == "marketing.video_production"

    def test_agent_config_creation(self):
        """Test AgentConfig dataclass creation"""
        config = AgentConfig(
            id="strategist",
            name="Marketing Strategist",
            role="Strategy Lead",
            provider="claude",
            model="claude-3-opus",
            temperature=0.7,
            responsibilities=["Strategy", "Planning"],
            tools=["web_search", "analytics"],
            department_id="marketing"
        )

        assert config.id == "strategist"
        assert config.provider == "claude"
        assert len(config.responsibilities) == 2
        assert len(config.tools) == 2

    def test_workflow_config_creation(self):
        """Test WorkflowConfig dataclass creation"""
        workflow = WorkflowConfig(
            id="campaign_launch",
            name="Campaign Launch",
            description="Launch marketing campaign",
            trigger="manual",
            risk_level="medium",
            steps=[
                {"agent": "strategist", "task": "Plan campaign"}
            ],
            department_id="marketing"
        )

        assert workflow.id == "campaign_launch"
        assert workflow.risk_level == "medium"
        assert len(workflow.steps) == 1


class TestDepartmentManagerInit:
    """Test DepartmentManager initialization"""

    def test_init_creates_storage(self):
        """Test initialization creates empty storage dictionaries"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()

        manager = DepartmentManager(
            config_dir="/tmp/config",
            rag_memory=mock_rag,
            tracer=mock_tracer
        )

        assert isinstance(manager.departments, dict)
        assert isinstance(manager.agents, dict)
        assert isinstance(manager.workflows, dict)
        assert len(manager.departments) == 0
        assert len(manager.agents) == 0
        assert len(manager.workflows) == 0

    def test_init_sets_config_dir_path(self):
        """Test initialization sets config_dir as Path object"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()

        manager = DepartmentManager(
            config_dir="/tmp/config",
            rag_memory=mock_rag,
            tracer=mock_tracer
        )

        assert isinstance(manager.config_dir, Path)
        assert str(manager.config_dir) == "/tmp/config"


class TestDepartmentManagerGetters:
    """Test DepartmentManager getter methods"""

    def test_get_department_exists(self):
        """Test get_department returns existing department"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        dept = Department(
            id="marketing",
            name="Marketing",
            description="Test",
            parent=None,
            budget={}
        )
        manager.departments["marketing"] = dept

        result = manager.get_department("marketing")
        assert result == dept
        assert result.id == "marketing"

    def test_get_department_not_exists(self):
        """Test get_department returns None for non-existent department"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        result = manager.get_department("nonexistent")
        assert result is None

    def test_list_departments_empty(self):
        """Test list_departments with no departments"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        result = manager.list_departments()
        assert result == []

    def test_list_departments_multiple(self):
        """Test list_departments with multiple departments"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        dept1 = Department(id="marketing", name="Marketing", description="Test", parent=None, budget={})
        dept2 = Department(id="engineering", name="Engineering", description="Test", parent=None, budget={})
        manager.departments["marketing"] = dept1
        manager.departments["engineering"] = dept2

        result = manager.list_departments()
        assert len(result) == 2
        assert dept1 in result
        assert dept2 in result

    def test_get_agent_exists(self):
        """Test get_agent returns existing agent"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        mock_agent = MagicMock()
        manager.agents["marketing.strategist"] = mock_agent

        result = manager.get_agent("marketing.strategist")
        assert result == mock_agent

    def test_get_agent_not_exists(self):
        """Test get_agent returns None for non-existent agent"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        result = manager.get_agent("nonexistent.agent")
        assert result is None

    def test_list_agents_all(self):
        """Test list_agents returns all agents"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        manager.agents["marketing.strategist"] = MagicMock()
        manager.agents["marketing.producer"] = MagicMock()
        manager.agents["engineering.developer"] = MagicMock()

        result = manager.list_agents()
        assert len(result) == 3
        assert "marketing.strategist" in result
        assert "marketing.producer" in result
        assert "engineering.developer" in result

    def test_list_agents_filtered_by_department(self):
        """Test list_agents filtered by department"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        manager.agents["marketing.strategist"] = MagicMock()
        manager.agents["marketing.producer"] = MagicMock()
        manager.agents["engineering.developer"] = MagicMock()

        result = manager.list_agents(department_id="marketing")
        assert len(result) == 2
        assert "marketing.strategist" in result
        assert "marketing.producer" in result
        assert "engineering.developer" not in result

    def test_list_agents_empty_department(self):
        """Test list_agents for department with no agents"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        manager.agents["marketing.strategist"] = MagicMock()

        result = manager.list_agents(department_id="engineering")
        assert result == []

    def test_get_workflow_exists(self):
        """Test get_workflow returns existing workflow"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        workflow = WorkflowConfig(
            id="campaign",
            name="Launch Campaign",
            description="Test",
            trigger="manual",
            risk_level="low",
            steps=[],
            department_id="marketing"
        )
        manager.workflows["marketing.campaign"] = workflow

        result = manager.get_workflow("marketing.campaign")
        assert result == workflow
        assert result.id == "campaign"

    def test_get_workflow_not_exists(self):
        """Test get_workflow returns None for non-existent workflow"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        result = manager.get_workflow("nonexistent.workflow")
        assert result is None


class TestDepartmentManagerLoadDepartments:
    """Test DepartmentManager department loading"""

    @pytest.mark.asyncio
    async def test_load_all_departments_no_directory(self):
        """Test load_all_departments creates directory if not exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "nonexistent"

            mock_rag = MagicMock()
            mock_tracer = MagicMock()
            manager = DepartmentManager(str(config_dir), mock_rag, mock_tracer)

            await manager.load_all_departments()

            assert config_dir.exists()
            assert len(manager.departments) == 0

    @pytest.mark.asyncio
    async def test_load_all_departments_empty_directory(self):
        """Test load_all_departments with empty directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_rag = MagicMock()
            mock_tracer = MagicMock()
            manager = DepartmentManager(tmpdir, mock_rag, mock_tracer)

            await manager.load_all_departments()

            assert len(manager.departments) == 0

    @pytest.mark.asyncio
    @patch("builtins.open", new_callable=mock_open, read_data="""
department:
  id: marketing
  name: Marketing
  description: Marketing department
  budget:
    monthly: 10000
  agents:
    - id: strategist
      name: Marketing Strategist
      role: Strategy Lead
      model: gpt-4
      provider: openai
      temperature: 0.7
      responsibilities:
        - Strategy planning
      tools:
        - web_search
""")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    async def test_load_department_file_success(self, mock_exists, mock_glob, mock_file):
        """Test successful loading of department file"""
        mock_exists.return_value = True
        mock_glob.return_value = [Path("/tmp/marketing.yaml")]

        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        with patch.object(manager, '_create_department_agents', new_callable=AsyncMock):
            await manager.load_all_departments()

        assert len(manager.departments) == 1
        assert "marketing" in manager.departments
        dept = manager.departments["marketing"]
        assert dept.name == "Marketing"
        assert dept.budget["monthly"] == 10000
        assert len(dept.agents) == 1


class TestDepartmentManagerCreateLLMClient:
    """Test LLM client creation"""

    @patch("settings.settings")
    def test_create_llm_client_claude(self, mock_settings):
        """Test creating Claude LLM client"""
        mock_settings.CLAUDE_AUTH_URL = "http://claude-auth"
        mock_settings.CLAUDE_SESSION_TOKEN = "test-token"
        mock_settings.CLAUDE_API_URL = "http://claude-api"

        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        config = AgentConfig(
            id="test",
            name="Test",
            role="Test",
            provider="claude",
            model="claude-3-opus",
            temperature=0.5,
            responsibilities=[],
            tools=[],
            department_id="test"
        )

        client = manager._create_llm_client(config)

        assert client.provider == "claude"
        assert client.model == "claude-3-opus"
        assert client.temperature == 0.5

    @patch("settings.settings")
    def test_create_llm_client_openai(self, mock_settings):
        """Test creating OpenAI LLM client"""
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_BASE_URL = "http://openai"

        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        config = AgentConfig(
            id="test",
            name="Test",
            role="Test",
            provider="openai",
            model="gpt-4",
            temperature=0.3,
            responsibilities=[],
            tools=[],
            department_id="test"
        )

        client = manager._create_llm_client(config)

        assert client.provider == "openai"
        assert client.model == "gpt-4"
        assert client.temperature == 0.3

    @patch("settings.settings")
    def test_create_llm_client_ollama(self, mock_settings):
        """Test creating Ollama LLM client"""
        mock_settings.OLLAMA_BASE_URL = "http://ollama"

        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        config = AgentConfig(
            id="test",
            name="Test",
            role="Test",
            provider="ollama",
            model="llama2",
            temperature=0.2,
            responsibilities=[],
            tools=[],
            department_id="test"
        )

        client = manager._create_llm_client(config)

        assert client.provider == "ollama"
        assert client.model == "llama2"
        assert client.temperature == 0.2


class TestDepartmentManagerExecuteWorkflow:
    """Test workflow execution"""

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self):
        """Test execute_workflow raises error for non-existent workflow"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        with pytest.raises(ValueError, match="Workflow not found"):
            await manager.execute_workflow("nonexistent.workflow", {})

    @pytest.mark.asyncio
    async def test_execute_workflow_agent_not_found(self):
        """Test execute_workflow raises error when agent not found"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        workflow = WorkflowConfig(
            id="test_workflow",
            name="Test Workflow",
            description="Test",
            trigger="manual",
            risk_level="low",
            steps=[
                {"agent": "nonexistent.agent", "task": "Do something"}
            ],
            department_id="test"
        )
        manager.workflows["test.test_workflow"] = workflow

        with pytest.raises(ValueError, match="Agent not found"):
            await manager.execute_workflow("test.test_workflow", {})

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self):
        """Test successful workflow execution"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        # Create mock agent
        mock_agent = AsyncMock()
        mock_agent.execute = AsyncMock(return_value={"result": "success"})
        manager.agents["test.agent1"] = mock_agent

        # Create workflow
        workflow = WorkflowConfig(
            id="test_workflow",
            name="Test Workflow",
            description="Test",
            trigger="manual",
            risk_level="low",
            steps=[
                {"agent": "test.agent1", "task": "Do task 1"}
            ],
            department_id="test"
        )
        manager.workflows["test.test_workflow"] = workflow

        result = await manager.execute_workflow("test.test_workflow", {"context": "data"})

        assert result["workflow"] == "Test Workflow"
        assert result["status"] == "completed"
        assert result["steps_completed"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["step"] == "Do task 1"

    @pytest.mark.asyncio
    async def test_execute_workflow_multiple_steps(self):
        """Test workflow execution with multiple steps"""
        mock_rag = MagicMock()
        mock_tracer = MagicMock()
        manager = DepartmentManager("/tmp/config", mock_rag, mock_tracer)

        # Create mock agents
        mock_agent1 = AsyncMock()
        mock_agent1.execute = AsyncMock(return_value={"result": "step1"})
        mock_agent2 = AsyncMock()
        mock_agent2.execute = AsyncMock(return_value={"result": "step2"})

        manager.agents["test.agent1"] = mock_agent1
        manager.agents["test.agent2"] = mock_agent2

        # Create workflow
        workflow = WorkflowConfig(
            id="multi_step",
            name="Multi Step Workflow",
            description="Test",
            trigger="manual",
            risk_level="medium",
            steps=[
                {"agent": "test.agent1", "task": "Step 1"},
                {"agent": "test.agent2", "task": "Step 2"}
            ],
            department_id="test"
        )
        manager.workflows["test.multi_step"] = workflow

        result = await manager.execute_workflow("test.multi_step", {})

        assert result["steps_completed"] == 2
        assert len(result["results"]) == 2


class TestDynamicAgent:
    """Test DynamicAgent class"""

    def test_dynamic_agent_init(self):
        """Test DynamicAgent initialization"""
        config = AgentConfig(
            id="test",
            name="Test Agent",
            role="Tester",
            provider="ollama",
            model="test-model",
            temperature=0.5,
            responsibilities=["Testing"],
            tools=[],
            department_id="test"
        )

        mock_llm = MagicMock()
        mock_rag = MagicMock()
        mock_tracer = MagicMock()

        agent = DynamicAgent(
            config=config,
            llm_client=mock_llm,
            rag_memory=mock_rag,
            tracer=mock_tracer
        )

        assert agent.config == config
        assert agent.llm == mock_llm
        assert agent.rag_memory == mock_rag
        assert agent.tracer == mock_tracer

    def test_build_system_prompt(self):
        """Test system prompt building"""
        config = AgentConfig(
            id="test",
            name="Test Agent",
            role="Senior Tester",
            provider="ollama",
            model="test-model",
            temperature=0.5,
            responsibilities=["Write tests", "Review code"],
            tools=[],
            department_id="test"
        )

        agent = DynamicAgent(
            config=config,
            llm_client=MagicMock(),
            rag_memory=MagicMock(),
            tracer=MagicMock()
        )

        prompt = agent._build_system_prompt()

        assert "Test Agent" in prompt
        assert "Senior Tester" in prompt
        assert "Write tests" in prompt
        assert "Review code" in prompt

    def test_build_user_prompt_no_context(self):
        """Test user prompt building without context"""
        config = AgentConfig(
            id="test",
            name="Test Agent",
            role="Tester",
            provider="ollama",
            model="test-model",
            temperature=0.5,
            responsibilities=["Testing"],
            tools=[],
            department_id="test"
        )

        agent = DynamicAgent(
            config=config,
            llm_client=MagicMock(),
            rag_memory=MagicMock(),
            tracer=MagicMock()
        )

        prompt = agent._build_user_prompt("Test task", {}, [])

        assert "Test task" in prompt
        assert "No additional context" in prompt

    def test_build_user_prompt_with_citations(self):
        """Test user prompt building with citations"""
        config = AgentConfig(
            id="test",
            name="Test Agent",
            role="Tester",
            provider="ollama",
            model="test-model",
            temperature=0.5,
            responsibilities=["Testing"],
            tools=[],
            department_id="test"
        )

        agent = DynamicAgent(
            config=config,
            llm_client=MagicMock(),
            rag_memory=MagicMock(),
            tracer=MagicMock()
        )

        citations = [
            {"source": "doc1.md", "content": "Test content 1" * 50},
            {"source": "doc2.md", "content": "Test content 2" * 50}
        ]

        prompt = agent._build_user_prompt("Test task", {"key": "value"}, citations)

        assert "Test task" in prompt
        assert "doc1.md" in prompt
        assert "doc2.md" in prompt
        assert "key" in prompt

    @pytest.mark.asyncio
    async def test_dynamic_agent_execute(self):
        """Test DynamicAgent.execute()"""
        config = AgentConfig(
            id="test",
            name="Test Agent",
            role="Tester",
            provider="ollama",
            model="test-model",
            temperature=0.5,
            responsibilities=["Testing"],
            tools=[],
            department_id="test"
        )

        mock_llm = AsyncMock()
        mock_llm.complete = AsyncMock(return_value={"text": "Test response"})

        mock_rag = AsyncMock()
        mock_rag.retrieve = AsyncMock(return_value=[
            {"source": "doc1.md", "content": "Context"}
        ])

        agent = DynamicAgent(
            config=config,
            llm_client=mock_llm,
            rag_memory=mock_rag,
            tracer=MagicMock()
        )

        result = await agent.execute("Test task", {"context": "data"})

        assert result["text"] == "Test response"
        assert result["agent"] == "Test Agent"
        assert result["department"] == "test"
        assert len(result["citations"]) == 1

        # Verify RAG was called
        mock_rag.retrieve.assert_called_once()

        # Verify LLM was called
        mock_llm.complete.assert_called_once()
