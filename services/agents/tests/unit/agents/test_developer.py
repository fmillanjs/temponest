"""
Unit tests for Developer Agent.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.agents.developer import DeveloperAgent


class TestDeveloperAgent:
    """Test suite for DeveloperAgent"""

    @pytest.fixture
    def mock_rag_memory(self):
        """Create mock RAG memory"""
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[
            {
                "source": "docs/api/crud.md",
                "version": "v1.0",
                "score": 0.95,
                "content": "Example CRUD endpoint with validation and error handling"
            },
            {
                "source": "docs/testing/pytest.md",
                "version": "v2.0",
                "score": 0.88,
                "content": "Best practices for writing pytest tests"
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
    def developer_agent(self, mock_rag_memory, mock_tracer):
        """Create DeveloperAgent instance with mocked dependencies"""
        with patch('app.agents.developer.Agent'):
            agent = DeveloperAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model",
                temperature=0.2,
                top_p=0.9,
                max_tokens=2048,
                seed=42
            )
            return agent

    def test_init_default_params(self, mock_rag_memory, mock_tracer):
        """Test DeveloperAgent initialization with default parameters"""
        with patch('app.agents.developer.Agent'):
            agent = DeveloperAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model"
            )

            assert agent.code_model == "test-model"
            assert agent.temperature == 0.2
            assert agent.top_p == 0.9
            assert agent.max_tokens == 2048
            assert agent.seed == 42

    def test_init_custom_params(self, mock_rag_memory, mock_tracer):
        """Test DeveloperAgent initialization with custom parameters"""
        with patch('app.agents.developer.Agent'):
            agent = DeveloperAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="custom-model",
                temperature=0.5,
                top_p=0.95,
                max_tokens=4096,
                seed=100
            )

            assert agent.code_model == "custom-model"
            assert agent.temperature == 0.5
            assert agent.top_p == 0.95
            assert agent.max_tokens == 4096
            assert agent.seed == 100

    def test_init_with_ollama_prefix(self, mock_rag_memory, mock_tracer):
        """Test DeveloperAgent with ollama/ prefix in model name"""
        with patch('app.agents.developer.Agent') as mock_agent_class:
            agent = DeveloperAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="ollama/codellama"
            )

            # Verify Agent was called with correct model format
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['llm'] == "ollama/codellama"

    def test_init_without_ollama_prefix(self, mock_rag_memory, mock_tracer):
        """Test DeveloperAgent adds ollama/ prefix when not present"""
        with patch('app.agents.developer.Agent') as mock_agent_class:
            agent = DeveloperAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="codellama"
            )

            # Verify Agent was called with ollama/ prefix added
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['llm'] == "ollama/codellama"

    def test_create_search_code_examples_tool(self, developer_agent):
        """Test search code examples tool creation"""
        tool = developer_agent._create_search_code_examples_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    @pytest.mark.asyncio
    async def test_search_code_examples_with_results(self, developer_agent, mock_rag_memory):
        """Test search code examples tool returns formatted results"""
        tool = developer_agent._create_search_code_examples_tool()

        result = await tool.func("CRUD API endpoint")

        # Verify RAG was called with correct query
        mock_rag_memory.retrieve.assert_called_once_with(
            query="code example: CRUD API endpoint",
            top_k=5,
            min_score=0.7
        )

        # Verify result format
        assert "[Example 1]" in result
        assert "[Example 2]" in result
        assert "docs/api/crud.md" in result
        assert "v1.0" in result
        assert "0.95" in result

    @pytest.mark.asyncio
    async def test_search_code_examples_no_results(self, developer_agent):
        """Test search code examples tool when no results found"""
        developer_agent.rag_memory.retrieve = AsyncMock(return_value=[])
        tool = developer_agent._create_search_code_examples_tool()

        result = await tool.func("nonexistent pattern")

        assert "No code examples found" in result
        assert "standard best practices" in result

    def test_create_validate_syntax_tool(self, developer_agent):
        """Test validate syntax tool creation"""
        tool = developer_agent._create_validate_syntax_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_validate_syntax_python_valid(self, developer_agent):
        """Test syntax validation for valid Python code"""
        tool = developer_agent._create_validate_syntax_tool()

        python_code = """
def hello_world():
    return "Hello, World!"
"""

        result = tool.func(python_code, "python")

        assert "✓ Basic syntax validation passed" in result

    def test_validate_syntax_python_with_class(self, developer_agent):
        """Test syntax validation for Python class"""
        tool = developer_agent._create_validate_syntax_tool()

        python_code = """
class MyClass:
    def __init__(self):
        pass
"""

        result = tool.func(python_code, "python")

        assert "✓ Basic syntax validation passed" in result

    def test_validate_syntax_python_invalid(self, developer_agent):
        """Test syntax validation for invalid Python code"""
        tool = developer_agent._create_validate_syntax_tool()

        python_code = "just some random text without function or class"

        result = tool.func(python_code, "python")

        assert "No function or class definition found" in result

    def test_validate_syntax_typescript_valid_function(self, developer_agent):
        """Test syntax validation for valid TypeScript function"""
        tool = developer_agent._create_validate_syntax_tool()

        typescript_code = """
function greet(name: string): string {
    return `Hello, ${name}!`;
}
"""

        result = tool.func(typescript_code, "typescript")

        assert "✓ Basic syntax validation passed" in result

    def test_validate_syntax_typescript_valid_const(self, developer_agent):
        """Test syntax validation for TypeScript const"""
        tool = developer_agent._create_validate_syntax_tool()

        typescript_code = """
const multiply = (a: number, b: number): number => a * b;
"""

        result = tool.func(typescript_code, "typescript")

        assert "✓ Basic syntax validation passed" in result

    def test_validate_syntax_typescript_valid_export(self, developer_agent):
        """Test syntax validation for TypeScript export"""
        tool = developer_agent._create_validate_syntax_tool()

        typescript_code = """
export const API_URL = 'https://api.example.com';
"""

        result = tool.func(typescript_code, "typescript")

        assert "✓ Basic syntax validation passed" in result

    def test_validate_syntax_typescript_invalid(self, developer_agent):
        """Test syntax validation for invalid TypeScript code"""
        tool = developer_agent._create_validate_syntax_tool()

        typescript_code = "just some random text"

        result = tool.func(typescript_code, "typescript")

        assert "No function or export found" in result

    def test_validate_syntax_sql_valid_create(self, developer_agent):
        """Test syntax validation for SQL CREATE statement"""
        tool = developer_agent._create_validate_syntax_tool()

        sql_code = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);
"""

        result = tool.func(sql_code, "sql")

        assert "✓ Basic syntax validation passed" in result

    def test_validate_syntax_sql_valid_select(self, developer_agent):
        """Test syntax validation for SQL SELECT statement"""
        tool = developer_agent._create_validate_syntax_tool()

        sql_code = "SELECT * FROM users WHERE email = $1;"

        result = tool.func(sql_code, "sql")

        assert "✓ Basic syntax validation passed" in result

    def test_validate_syntax_sql_invalid(self, developer_agent):
        """Test syntax validation for invalid SQL"""
        tool = developer_agent._create_validate_syntax_tool()

        sql_code = "just some random text"

        result = tool.func(sql_code, "sql")

        assert "No SQL statement found" in result

    def test_validate_syntax_empty_code(self, developer_agent):
        """Test syntax validation with empty code"""
        tool = developer_agent._create_validate_syntax_tool()

        result = tool.func("", "python")

        assert "Code is too short or empty" in result

    def test_validate_syntax_too_short(self, developer_agent):
        """Test syntax validation with very short code"""
        tool = developer_agent._create_validate_syntax_tool()

        result = tool.func("x = 1", "python")

        assert "Code is too short or empty" in result

    def test_create_generate_tests_tool(self, developer_agent):
        """Test generate test scaffold tool creation"""
        tool = developer_agent._create_generate_tests_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_generate_test_scaffold_python(self, developer_agent):
        """Test test scaffold generation for Python"""
        tool = developer_agent._create_generate_tests_tool()

        result = tool.func("calculate_total", "python")

        assert "import pytest" in result
        assert "def test_calculate_total_success():" in result
        assert "def test_calculate_total_validation():" in result
        assert "def test_calculate_total_edge_cases():" in result
        assert "pytest.raises(ValueError)" in result

    def test_generate_test_scaffold_typescript(self, developer_agent):
        """Test test scaffold generation for TypeScript"""
        tool = developer_agent._create_generate_tests_tool()

        result = tool.func("calculateTotal", "typescript")

        assert "import { describe, it, expect } from 'vitest'" in result
        assert "describe('calculateTotal'" in result
        assert "it('should handle successful execution'" in result
        assert "it('should validate input'" in result
        assert "it('should handle edge cases'" in result

    def test_generate_test_scaffold_unsupported_language(self, developer_agent):
        """Test test scaffold generation for unsupported language"""
        tool = developer_agent._create_generate_tests_tool()

        result = tool.func("myFunction", "ruby")

        assert "Test scaffold not available for this language" in result

    def test_format_examples(self, developer_agent):
        """Test citation formatting for examples"""
        citations = [
            {
                "source": "docs/api.md",
                "version": "v1.0",
                "score": 0.95,
                "content": "Example API code"
            },
            {
                "source": "docs/tests.md",
                "version": "v2.0",
                "score": 0.82,
                "content": "Example test code"
            }
        ]

        result = developer_agent._format_examples(citations)

        assert "[Example 1]" in result
        assert "[Example 2]" in result
        assert "docs/api.md" in result
        assert "v1.0" in result
        assert "0.95" in result
        assert "docs/tests.md" in result
        assert "v2.0" in result
        assert "0.82" in result
        assert "Example API code" in result
        assert "Example test code" in result

    def test_format_examples_empty(self, developer_agent):
        """Test citation formatting with no examples"""
        result = developer_agent._format_examples([])

        assert result == ""

    def test_identify_task_type_api(self, developer_agent):
        """Test task type identification for API tasks"""
        assert developer_agent._identify_task_type("Create a CRUD API") == "api_endpoint"
        assert developer_agent._identify_task_type("Build REST endpoint") == "api_endpoint"
        assert developer_agent._identify_task_type("Implement user CRUD operations") == "api_endpoint"

    def test_identify_task_type_database(self, developer_agent):
        """Test task type identification for database tasks"""
        assert developer_agent._identify_task_type("Design database schema") == "database_schema"
        assert developer_agent._identify_task_type("Create migration script") == "database_schema"
        assert developer_agent._identify_task_type("Update database tables") == "database_schema"

    def test_identify_task_type_frontend(self, developer_agent):
        """Test task type identification for frontend tasks"""
        assert developer_agent._identify_task_type("Build React component") == "frontend_component"
        assert developer_agent._identify_task_type("Create frontend dashboard") == "frontend_component"
        assert developer_agent._identify_task_type("Design login component") == "frontend_component"

    def test_identify_task_type_general(self, developer_agent):
        """Test task type identification for general tasks"""
        assert developer_agent._identify_task_type("Write utility function") == "general_code"
        assert developer_agent._identify_task_type("Refactor code") == "general_code"

    def test_parse_code_output_with_json(self, developer_agent):
        """Test code output parsing with valid JSON"""
        result_text = """
Here is the generated code:

{
    "implementation": "def hello(): return 'Hello'",
    "tests": "def test_hello(): assert hello() == 'Hello'",
    "migrations": "ALTER TABLE users ADD COLUMN name VARCHAR(255);",
    "setup_instructions": ["Install dependencies", "Run migrations"]
}
"""

        parsed = developer_agent._parse_code_output(result_text)

        assert parsed["implementation"] == "def hello(): return 'Hello'"
        assert parsed["tests"] == "def test_hello(): assert hello() == 'Hello'"
        assert parsed["migrations"] == "ALTER TABLE users ADD COLUMN name VARCHAR(255);"
        assert "Install dependencies" in parsed["setup_instructions"]

    def test_parse_code_output_with_code_blocks(self, developer_agent):
        """Test code output parsing with code blocks"""
        result_text = """
Here is the implementation:

```python
def add(a, b):
    return a + b
```

And the tests:

```python
def test_add():
    assert add(1, 2) == 3
```

And the migration:

```sql
CREATE TABLE numbers (
    id SERIAL PRIMARY KEY,
    value INTEGER
);
```
"""

        parsed = developer_agent._parse_code_output(result_text)

        assert "def add(a, b):" in parsed["implementation"]
        assert "return a + b" in parsed["implementation"]
        assert "def test_add():" in parsed["tests"]
        assert "CREATE TABLE numbers" in parsed["migrations"]

    def test_parse_code_output_fallback_no_json_or_blocks(self, developer_agent):
        """Test code output parsing fallback with plain text"""
        result_text = "Just some plain text without JSON or code blocks"

        parsed = developer_agent._parse_code_output(result_text)

        assert parsed["implementation"] == result_text
        assert parsed["tests"] == ""
        assert parsed["migrations"] == ""
        assert "Review and test the generated code" in parsed["setup_instructions"]

    def test_parse_code_output_single_code_block(self, developer_agent):
        """Test code output parsing with single code block"""
        result_text = """
```python
def multiply(a, b):
    return a * b
```
"""

        parsed = developer_agent._parse_code_output(result_text)

        assert "def multiply(a, b):" in parsed["implementation"]
        assert parsed["tests"] == ""
        assert parsed["migrations"] == ""

    def test_generate_file_map_full(self, developer_agent):
        """Test file map generation with all components"""
        code_output = {
            "implementation": "def hello(): pass",
            "tests": "def test_hello(): pass",
            "migrations": "CREATE TABLE test (id SERIAL);"
        }

        file_map = developer_agent._generate_file_map(code_output)

        assert len(file_map) == 3

        # Check implementation file
        impl_file = next((f for f in file_map if "implementation" in f["path"]), None)
        assert impl_file is not None
        assert impl_file["contents"] == "def hello(): pass"

        # Check test file
        test_file = next((f for f in file_map if "test" in f["path"]), None)
        assert test_file is not None
        assert test_file["contents"] == "def test_hello(): pass"

        # Check migration file
        migration_file = next((f for f in file_map if "migration" in f["path"]), None)
        assert migration_file is not None
        assert migration_file["contents"] == "CREATE TABLE test (id SERIAL);"

    def test_generate_file_map_implementation_only(self, developer_agent):
        """Test file map generation with only implementation"""
        code_output = {
            "implementation": "def hello(): pass"
        }

        file_map = developer_agent._generate_file_map(code_output)

        assert len(file_map) == 1
        assert "implementation" in file_map[0]["path"]
        assert file_map[0]["contents"] == "def hello(): pass"

    def test_generate_file_map_empty(self, developer_agent):
        """Test file map generation with empty output"""
        code_output = {}

        file_map = developer_agent._generate_file_map(code_output)

        assert len(file_map) == 0

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_rag_memory, mock_tracer):
        """Test successful developer agent execution"""
        with patch('app.agents.developer.Agent') as mock_agent_class:
            with patch('app.agents.developer.Crew') as mock_crew_class:
                with patch('app.agents.developer.Task') as mock_task_class:
                    # Setup agent
                    developer_agent = DeveloperAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    # Mock crew execution
                    mock_crew = MagicMock()
                    mock_crew.kickoff = Mock(return_value='{"implementation": "def hello(): pass", "tests": "def test_hello(): pass"}')
                    mock_crew_class.return_value = mock_crew

                    result = await developer_agent.execute(
                        task="Create a hello world function",
                        context={"language": "python"},
                        task_id="task-123"
                    )

                    assert "code" in result
                    assert "citations" in result
                    assert "setup_instructions" in result
                    assert "file_map" in result
                    assert "latency_ms" in result
                    assert isinstance(result["latency_ms"], int)
                    assert result["latency_ms"] >= 0

                    # Verify tracer was called
                    mock_tracer.trace_agent_execution.assert_called_once()
                    mock_tracer.trace_rag_retrieval.assert_called_once()
                    mock_tracer.trace_llm_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_api_task(self, mock_rag_memory, mock_tracer):
        """Test execution identifies API task type correctly"""
        with patch('app.agents.developer.Agent') as mock_agent_class:
            with patch('app.agents.developer.Crew') as mock_crew_class:
                with patch('app.agents.developer.Task') as mock_task_class:
                    developer_agent = DeveloperAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff = Mock(return_value='{"implementation": "API code"}')
                    mock_crew_class.return_value = mock_crew

                    await developer_agent.execute(
                        task="Create CRUD API for users",
                        context={},
                        task_id="task-api"
                    )

                    # Verify task was created with API type
                    task_call = mock_task_class.call_args
                    task_description = task_call[1]["description"]
                    assert "Type: api_endpoint" in task_description

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, mock_rag_memory, mock_tracer):
        """Test error handling during execution"""
        # Make RAG retrieval fail
        mock_rag_memory.retrieve = AsyncMock(side_effect=Exception("RAG failure"))

        with patch('app.agents.developer.Agent'):
            developer_agent = DeveloperAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model"
            )

            with pytest.raises(Exception) as exc_info:
                await developer_agent.execute(
                    task="Generate code",
                    context={},
                    task_id="task-error"
                )

            assert "RAG failure" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_retrieves_citations(self, mock_rag_memory, mock_tracer):
        """Test that execute retrieves relevant code examples as citations"""
        with patch('app.agents.developer.Agent') as mock_agent_class:
            with patch('app.agents.developer.Crew') as mock_crew_class:
                with patch('app.agents.developer.Task') as mock_task_class:
                    developer_agent = DeveloperAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff = Mock(return_value='{"implementation": "code"}')
                    mock_crew_class.return_value = mock_crew

                    result = await developer_agent.execute(
                        task="Create API endpoint",
                        context={},
                        task_id="task-citations"
                    )

                    # Verify RAG retrieval was called
                    mock_rag_memory.retrieve.assert_awaited()
                    call_args = mock_rag_memory.retrieve.call_args_list[0]
                    assert "code implementation" in call_args[1]["query"]

                    # Verify citations in result
                    assert len(result["citations"]) == 2
                    assert result["citations"][0]["source"] == "docs/api/crud.md"

    @pytest.mark.asyncio
    async def test_execute_formats_examples_in_prompt(self, mock_rag_memory, mock_tracer):
        """Test that execute includes formatted examples in the crew task"""
        with patch('app.agents.developer.Agent') as mock_agent_class:
            with patch('app.agents.developer.Crew') as mock_crew_class:
                with patch('app.agents.developer.Task') as mock_task_class:
                    developer_agent = DeveloperAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff = Mock(return_value='{"implementation": "code"}')
                    mock_crew_class.return_value = mock_crew

                    await developer_agent.execute(
                        task="Create API endpoint",
                        context={"framework": "FastAPI"},
                        task_id="task-examples"
                    )

                    # Verify task description includes examples
                    task_call = mock_task_class.call_args
                    task_description = task_call[1]["description"]
                    assert "Relevant Examples:" in task_description
                    assert "[Example 1]" in task_description
                    assert "docs/api/crud.md" in task_description
