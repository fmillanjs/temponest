"""
Unit tests for Developer Agent V2.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.agents.developer_v2 import DeveloperAgentV2
from app.llm.unified_client import UnifiedLLMClient
from app.memory.rag import RAGMemory
from app.memory.langfuse_tracer import LangfuseTracer


class TestDeveloperV2AgentInit:
    """Test Developer V2 agent initialization"""

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_init_with_claude_provider(self, mock_client_class, mock_settings):
        """Test initialization with Claude provider"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "https://claude.ai/api"
        mock_settings.CLAUDE_SESSION_TOKEN = "test-token"
        mock_settings.CLAUDE_API_URL = "https://api.claude.ai"

        agent = DeveloperAgentV2(
            rag_memory=rag_memory,
            tracer=tracer,
            provider="claude",
            model="claude-3-sonnet"
        )

        assert agent.rag_memory == rag_memory
        assert agent.tracer == tracer
        assert agent.provider == "claude"
        assert agent.model == "claude-3-sonnet"

        mock_client_class.assert_called_once_with(
            provider="claude",
            model="claude-3-sonnet",
            temperature=0.2,
            max_tokens=4096,
            top_p=0.9,
            seed=42,
            claude_auth_url="https://claude.ai/api",
            claude_session_token="test-token",
            claude_api_url="https://api.claude.ai"
        )

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_init_with_openai_provider(self, mock_client_class, mock_settings):
        """Test initialization with OpenAI provider"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.OPENAI_API_KEY = "sk-test"
        mock_settings.OPENAI_BASE_URL = "https://api.openai.com"

        agent = DeveloperAgentV2(
            rag_memory=rag_memory,
            tracer=tracer,
            provider="openai",
            model="gpt-4"
        )

        assert agent.provider == "openai"
        assert agent.model == "gpt-4"

        mock_client_class.assert_called_once_with(
            provider="openai",
            model="gpt-4",
            temperature=0.2,
            max_tokens=4096,
            top_p=0.9,
            seed=42,
            openai_api_key="sk-test",
            openai_base_url="https://api.openai.com"
        )

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_init_with_ollama_provider(self, mock_client_class, mock_settings):
        """Test initialization with Ollama provider"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"

        agent = DeveloperAgentV2(
            rag_memory=rag_memory,
            tracer=tracer,
            provider="ollama",
            model="codellama"
        )

        assert agent.provider == "ollama"
        assert agent.model == "codellama"

        mock_client_class.assert_called_once_with(
            provider="ollama",
            model="codellama",
            temperature=0.2,
            max_tokens=4096,
            top_p=0.9,
            seed=42,
            ollama_base_url="http://localhost:11434"
        )


class TestDeveloperV2Execute:
    """Test Developer V2 execute method"""

    @pytest.mark.asyncio
    @patch('app.agents.developer_v2.settings')
    async def test_execute_basic(self, mock_settings):
        """Test basic execution"""
        rag_memory = Mock(spec=RAGMemory)
        rag_memory.retrieve = AsyncMock(return_value=[])
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace_agent_execution = Mock(return_value="trace-123")
        tracer.trace_rag_retrieval = Mock()
        tracer.trace_llm_call = Mock()

        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        with patch('app.agents.developer_v2.UnifiedLLMClient') as mock_client_class:
            mock_llm = Mock()
            mock_llm.complete = AsyncMock(return_value={
                "text": json.dumps({
                    "implementation": "def hello(): pass",
                    "tests": "def test_hello(): pass",
                    "setup_instructions": ["Run tests"]
                }),
                "usage": {"output_tokens": 100}
            })
            mock_client_class.return_value = mock_llm

            agent = DeveloperAgentV2(
                rag_memory=rag_memory,
                tracer=tracer,
                provider="claude",
                model="claude-3"
            )

            result = await agent.execute(
                task="Create a hello function",
                context={"language": "python"},
                task_id="test-123"
            )

        assert "code" in result
        assert "citations" in result
        assert "setup_instructions" in result
        assert "file_map" in result
        assert "latency_ms" in result
        assert result["provider"] == "claude"
        assert result["model"] == "claude-3"

    @pytest.mark.asyncio
    @patch('app.agents.developer_v2.settings')
    async def test_execute_with_rag_citations(self, mock_settings):
        """Test execution with RAG citations"""
        rag_memory = Mock(spec=RAGMemory)

        citations = [
            {"source": "docs", "version": "1.0", "score": 0.95, "content": "Example code here"},
            {"source": "tutorial", "version": "2.0", "score": 0.85, "content": "More examples"}
        ]
        rag_memory.retrieve = AsyncMock(return_value=citations)

        tracer = Mock(spec=LangfuseTracer)
        tracer.trace_agent_execution = Mock(return_value="trace-456")
        tracer.trace_rag_retrieval = Mock()
        tracer.trace_llm_call = Mock()

        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        with patch('app.agents.developer_v2.UnifiedLLMClient') as mock_client_class:
            mock_llm = Mock()
            mock_llm.complete = AsyncMock(return_value={
                "text": '{"implementation": "code here"}',
                "usage": {"output_tokens": 50}
            })
            mock_client_class.return_value = mock_llm

            agent = DeveloperAgentV2(
                rag_memory=rag_memory,
                tracer=tracer,
                provider="claude",
                model="claude-3"
            )

            result = await agent.execute(
                task="Build API endpoint",
                context={},
                task_id="test-rag"
            )

        assert result["citations"] == citations
        rag_memory.retrieve.assert_called_once_with(
            query="code implementation: Build API endpoint",
            top_k=5,
            min_score=0.7
        )

    @pytest.mark.asyncio
    @patch('app.agents.developer_v2.settings')
    async def test_execute_calls_tracer(self, mock_settings):
        """Test execution calls tracer methods"""
        rag_memory = Mock(spec=RAGMemory)
        rag_memory.retrieve = AsyncMock(return_value=[])

        tracer = Mock(spec=LangfuseTracer)
        tracer.trace_agent_execution = Mock(return_value="trace-789")
        tracer.trace_rag_retrieval = Mock()
        tracer.trace_llm_call = Mock()

        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.OPENAI_API_KEY = "key"
        mock_settings.OPENAI_BASE_URL = "url"

        with patch('app.agents.developer_v2.UnifiedLLMClient') as mock_client_class:
            mock_llm = Mock()
            mock_llm.complete = AsyncMock(return_value={
                "text": '{"implementation": "test"}',
                "usage": {"output_tokens": 25}
            })
            mock_client_class.return_value = mock_llm

            agent = DeveloperAgentV2(
                rag_memory=rag_memory,
                tracer=tracer,
                provider="openai",
                model="gpt-4"
            )

            await agent.execute(
                task="Test task",
                context={"key": "value"},
                task_id="trace-test"
            )

        tracer.trace_agent_execution.assert_called_once()
        tracer.trace_rag_retrieval.assert_called_once()
        tracer.trace_llm_call.assert_called_once()


class TestDeveloperV2HelperMethods:
    """Test helper methods"""

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_build_system_prompt(self, mock_client, mock_settings):
        """Test system prompt building"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        prompt = agent._build_system_prompt()

        assert "senior full-stack developer" in prompt
        assert "production-ready" in prompt
        assert "FastAPI" in prompt
        assert "JSON" in prompt

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_build_user_prompt(self, mock_client, mock_settings):
        """Test user prompt building"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        prompt = agent._build_user_prompt(
            task="Build REST API",
            context={"framework": "FastAPI"},
            examples="Example code here",
            task_type="REST API"
        )

        assert "Build REST API" in prompt
        assert "REST API" in prompt
        assert "FastAPI" in prompt
        assert "Example code here" in prompt

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_format_examples_with_citations(self, mock_client, mock_settings):
        """Test formatting examples with citations"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        citations = [
            {"source": "docs", "version": "1.0", "score": 0.95, "content": "Example 1" * 200},
            {"source": "guide", "version": "2.0", "score": 0.85, "content": "Example 2"},
            {"source": "tutorial", "version": "3.0", "score": 0.75, "content": "Example 3"},
            {"source": "extra", "version": "4.0", "score": 0.65, "content": "Example 4"}  # Should be ignored
        ]

        result = agent._format_examples(citations)

        assert "Example 1" in result
        assert "docs" in result
        assert "v1.0" in result
        assert "0.95" in result
        # Should only include top 3
        assert "Example 4" not in result

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_format_examples_empty(self, mock_client, mock_settings):
        """Test formatting examples with no citations"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        result = agent._format_examples([])

        assert "No specific examples found" in result
        assert "best practices" in result

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_identify_task_type_api(self, mock_client, mock_settings):
        """Test task type identification for API"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        assert agent._identify_task_type("Build API endpoint") == "REST API"
        assert agent._identify_task_type("Create CRUD operations") == "REST API"
        assert agent._identify_task_type("REST endpoint for users") == "REST API"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_identify_task_type_database(self, mock_client, mock_settings):
        """Test task type identification for database"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        assert agent._identify_task_type("Create database schema") == "Database Schema"
        assert agent._identify_task_type("Add migration for users") == "Database Schema"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_identify_task_type_frontend(self, mock_client, mock_settings):
        """Test task type identification for frontend"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        assert agent._identify_task_type("Build React component") == "Frontend Component"
        assert agent._identify_task_type("Create UI for dashboard") == "Frontend Component"
        assert agent._identify_task_type("Frontend form component") == "Frontend Component"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_identify_task_type_test(self, mock_client, mock_settings):
        """Test task type identification for tests"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        # Use a task that contains "test" but not other keywords
        assert agent._identify_task_type("Create test coverage") == "Test Suite"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_identify_task_type_general(self, mock_client, mock_settings):
        """Test task type identification for general tasks"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        assert agent._identify_task_type("Implement business logic") == "General Implementation"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_parse_code_output_json(self, mock_client, mock_settings):
        """Test parsing JSON code output"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        response = json.dumps({
            "implementation": "def hello(): pass",
            "tests": "def test_hello(): pass",
            "migrations": "CREATE TABLE...",
            "setup_instructions": ["Step 1", "Step 2"]
        })

        result = agent._parse_code_output(response)

        assert result["implementation"] == "def hello(): pass"
        assert result["tests"] == "def test_hello(): pass"
        assert result["migrations"] == "CREATE TABLE..."
        assert len(result["setup_instructions"]) == 2

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_parse_code_output_json_missing_implementation(self, mock_client, mock_settings):
        """Test parsing JSON without implementation field"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        response = '{"tests": "test code"}'
        result = agent._parse_code_output(response)

        # Should add the whole response as implementation
        assert "implementation" in result

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_parse_code_output_code_blocks(self, mock_client, mock_settings):
        """Test parsing code blocks from response"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        response = """
Here's the implementation:
```python
def hello():
    return "Hello"
```

And the tests:
```python
def test_hello():
    assert hello() == "Hello"
```

And migrations:
```sql
CREATE TABLE users (id INT);
```
"""

        result = agent._parse_code_output(response)

        assert "def hello():" in result["implementation"]
        assert "def test_hello():" in result["tests"]
        assert "CREATE TABLE" in result["migrations"]
        assert len(result["setup_instructions"]) > 0

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_parse_code_output_fallback(self, mock_client, mock_settings):
        """Test fallback parsing for plain text"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        response = "Just some plain text without structure"
        result = agent._parse_code_output(response)

        assert result["implementation"] == response
        assert result["tests"] == ""
        assert result["migrations"] == ""

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_generate_file_map_python(self, mock_client, mock_settings):
        """Test file map generation for Python code"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        code_output = {
            "implementation": "def hello():\n    import os\n    pass",
            "tests": "def test_hello(): pass",
            "migrations": "CREATE TABLE..."
        }

        files = agent._generate_file_map(code_output)

        assert len(files) == 3
        assert files[0]["path"] == "src/implementation.py"
        assert files[1]["path"] == "tests/test_implementation.py"
        assert files[2]["path"] == "migrations/001_initial.sql"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_generate_file_map_typescript(self, mock_client, mock_settings):
        """Test file map generation for TypeScript code"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        # TypeScript needs "interface" AND one of "function", "const", or "import"
        code_output = {
            "implementation": "interface User { name: string; }\nconst user: User = { name: 'test' };"
        }

        files = agent._generate_file_map(code_output)

        assert len(files) == 1
        assert files[0]["path"] == "src/implementation.ts"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_generate_file_map_javascript(self, mock_client, mock_settings):
        """Test file map generation for JavaScript code"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        code_output = {
            "implementation": "function hello() { const x = 1; }"
        }

        files = agent._generate_file_map(code_output)

        assert len(files) == 1
        assert files[0]["path"] == "src/implementation.js"

    @patch('app.agents.developer_v2.settings')
    @patch('app.agents.developer_v2.UnifiedLLMClient')
    def test_generate_file_map_empty(self, mock_client, mock_settings):
        """Test file map generation with no code"""
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_SEED = 42
        mock_settings.CLAUDE_AUTH_URL = "test"
        mock_settings.CLAUDE_SESSION_TOKEN = "token"
        mock_settings.CLAUDE_API_URL = "api"

        agent = DeveloperAgentV2(
            rag_memory=Mock(),
            tracer=Mock(),
            provider="claude"
        )

        code_output = {}
        files = agent._generate_file_map(code_output)

        assert len(files) == 0
