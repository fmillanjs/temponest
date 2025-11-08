"""
Unit tests for Overseer Agent.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.agents.overseer import OverseerAgent


class TestOverseerAgent:
    """Test suite for OverseerAgent"""

    @pytest.fixture
    def mock_rag_memory(self):
        """Create mock RAG memory"""
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[
            {
                "source": "docs/api.md",
                "version": "v1.0",
                "score": 0.95,
                "content": "The API supports authentication via JWT tokens"
            },
            {
                "source": "docs/best_practices.md",
                "version": "v1.2",
                "score": 0.87,
                "content": "Always validate input parameters before processing"
            }
        ])
        return mock

    @pytest.fixture
    def mock_tracer(self):
        """Create mock Langfuse tracer"""
        mock = Mock()
        mock.trace_agent_execution = Mock(return_value="trace-123")
        mock.trace_rag_retrieval = Mock()
        mock.trace_llm_call = Mock()
        return mock

    @pytest.fixture
    def overseer_agent(self, mock_rag_memory, mock_tracer):
        """Create OverseerAgent instance with mocked dependencies"""
        with patch('app.agents.overseer.Agent'):
            agent = OverseerAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                chat_model="test-model",
                temperature=0.2,
                top_p=0.9,
                max_tokens=2048,
                seed=42
            )
            return agent

    def test_init_default_params(self, mock_rag_memory, mock_tracer):
        """Test OverseerAgent initialization with default parameters"""
        with patch('app.agents.overseer.Agent'):
            agent = OverseerAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                chat_model="test-model"
            )

            assert agent.chat_model == "test-model"
            assert agent.temperature == 0.2
            assert agent.top_p == 0.9
            assert agent.max_tokens == 2048
            assert agent.seed == 42

    def test_init_custom_params(self, mock_rag_memory, mock_tracer):
        """Test OverseerAgent initialization with custom parameters"""
        with patch('app.agents.overseer.Agent'):
            agent = OverseerAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                chat_model="custom-model",
                temperature=0.5,
                top_p=0.95,
                max_tokens=4096,
                seed=100
            )

            assert agent.chat_model == "custom-model"
            assert agent.temperature == 0.5
            assert agent.top_p == 0.95
            assert agent.max_tokens == 4096
            assert agent.seed == 100

    def test_create_search_knowledge_tool(self, overseer_agent):
        """Test search knowledge tool creation"""
        tool = overseer_agent._create_search_knowledge_tool()

        assert tool is not None
        # CrewAI tools are Tool objects with a func attribute
        assert hasattr(tool, 'func')

    @pytest.mark.asyncio
    async def test_search_knowledge_tool_with_results(self, overseer_agent, mock_rag_memory):
        """Test search knowledge tool returns formatted results"""
        tool = overseer_agent._create_search_knowledge_tool()

        # Call the underlying function directly
        result = await tool.func("test query")

        # Verify RAG was called
        mock_rag_memory.retrieve.assert_called_once_with(
            query="test query",
            top_k=5,
            min_score=0.7
        )

        # Verify result format
        assert "[Citation 1]" in result
        assert "[Citation 2]" in result
        assert "docs/api.md" in result
        assert "docs/best_practices.md" in result
        assert "v1.0" in result
        assert "0.95" in result

    @pytest.mark.asyncio
    async def test_search_knowledge_tool_no_results(self, overseer_agent):
        """Test search knowledge tool when no results found"""
        overseer_agent.rag_memory.retrieve = AsyncMock(return_value=[])
        tool = overseer_agent._create_search_knowledge_tool()

        result = await tool.func("nonexistent query")

        assert "No relevant documentation found" in result
        assert "ASK HUMAN" in result

    def test_create_validate_plan_tool(self, overseer_agent):
        """Test validate plan tool creation"""
        tool = overseer_agent._create_validate_plan_tool()

        assert tool is not None
        # CrewAI tools are Tool objects with a func attribute
        assert hasattr(tool, 'func')

    def test_validate_plan_tool_success(self, overseer_agent):
        """Test validate plan tool with sufficient citations"""
        tool = overseer_agent._create_validate_plan_tool()

        plan = "This is a detailed plan with multiple steps and sufficient information to be validated."
        result = tool.func(plan, 3)

        assert "Plan validated" in result
        assert "3 citations" in result

    def test_validate_plan_tool_insufficient_citations(self, overseer_agent):
        """Test validate plan tool with insufficient citations"""
        tool = overseer_agent._create_validate_plan_tool()

        plan = "This is a plan with only one citation."
        result = tool.func(plan, 1)

        assert "INSUFFICIENT GROUNDING" in result
        assert "Found 1 citations" in result
        assert "need ≥2" in result

    def test_validate_plan_tool_too_brief(self, overseer_agent):
        """Test validate plan tool with brief plan"""
        tool = overseer_agent._create_validate_plan_tool()

        plan = "Short plan"
        result = tool.func(plan, 2)

        assert "Plan is too brief" in result

    def test_format_citations(self, overseer_agent):
        """Test citation formatting"""
        citations = [
            {
                "source": "docs/api.md",
                "version": "v1.0",
                "score": 0.95,
                "content": "This is a long piece of documentation content that should be truncated after 300 characters. " * 10
            },
            {
                "source": "docs/guide.md",
                "version": "v2.0",
                "score": 0.82,
                "content": "Short content"
            }
        ]

        result = overseer_agent._format_citations(citations)

        assert "[Citation 1]" in result
        assert "[Citation 2]" in result
        assert "docs/api.md" in result
        assert "v1.0" in result
        assert "0.95" in result
        assert "docs/guide.md" in result
        assert "v2.0" in result
        assert "0.82" in result

    def test_parse_plan_with_dashes(self, overseer_agent):
        """Test plan parsing with dash-prefixed tasks"""
        result_text = """
        PLAN:
        - Task 1: Implement authentication (Agent: Developer)
        - Task 2: Set up database (Agent: Developer)
        - Task 3: Create API endpoints (Agent: Developer)
        """

        tasks = overseer_agent._parse_plan(result_text)

        assert len(tasks) == 3
        assert tasks[0]["task"].startswith("Task 1")
        assert tasks[0]["agent"] == "developer"
        assert tasks[0]["priority"] == 1
        assert "Developer" in tasks[0]["task"]

    def test_parse_plan_with_asterisks(self, overseer_agent):
        """Test plan parsing with asterisk-prefixed tasks"""
        result_text = """
        * Task 1: Review code
        * Task 2: Test functionality
        """

        tasks = overseer_agent._parse_plan(result_text)

        assert len(tasks) == 2
        assert tasks[0]["task"].startswith("Task 1")
        assert tasks[1]["task"].startswith("Task 2")

    def test_parse_plan_mixed_agents(self, overseer_agent):
        """Test plan parsing with different agent assignments"""
        result_text = """
        - Task 1: Coordinate team (Agent: Overseer)
        - Task 2: Write code (Agent: Developer)
        - Task 3: Plan next phase (Agent: Overseer)
        """

        tasks = overseer_agent._parse_plan(result_text)

        assert len(tasks) == 3
        assert tasks[0]["agent"] == "overseer"
        assert tasks[1]["agent"] == "developer"
        assert tasks[2]["agent"] == "overseer"

    def test_parse_plan_empty(self, overseer_agent):
        """Test plan parsing with no tasks"""
        result_text = "No tasks found in this result"

        tasks = overseer_agent._parse_plan(result_text)

        assert tasks == []

    def test_extract_next_steps(self, overseer_agent):
        """Test next steps extraction"""
        result_text = """
        Some other content here.

        NEXT_STEPS:
        1. First step to complete
        2. Second step to complete
        3. Third step to complete

        Some more content.
        """

        steps = overseer_agent._extract_next_steps(result_text)

        assert len(steps) == 3
        assert "First step to complete" in steps[0]
        assert "Second step to complete" in steps[1]
        assert "Third step to complete" in steps[2]

    def test_extract_next_steps_with_dashes(self, overseer_agent):
        """Test next steps extraction with dash format"""
        result_text = """
        NEXT STEPS:
        - Set up environment
        - Install dependencies
        - Run tests
        """

        steps = overseer_agent._extract_next_steps(result_text)

        assert len(steps) == 3
        assert "Set up environment" in steps[0]
        assert "Install dependencies" in steps[1]
        assert "Run tests" in steps[2]

    def test_extract_next_steps_none(self, overseer_agent):
        """Test next steps extraction when none present"""
        result_text = "No next steps mentioned in this text"

        steps = overseer_agent._extract_next_steps(result_text)

        assert steps == []

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, overseer_agent, mock_rag_memory, mock_tracer):
        """Test error handling during execution"""
        # Make RAG retrieval fail
        mock_rag_memory.retrieve = AsyncMock(side_effect=Exception("RAG failure"))

        with pytest.raises(Exception) as exc_info:
            await overseer_agent.execute(
                task="Test task",
                context={},
                task_id="task-error"
            )

        assert "RAG failure" in str(exc_info.value)
