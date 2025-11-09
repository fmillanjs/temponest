"""
Unit tests for QA Tester Agent.
"""

import pytest
import json
import re
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.agents.qa_tester import QATesterAgent


class TestQATesterAgent:
    """Test suite for QATesterAgent"""

    @pytest.fixture
    def mock_rag_memory(self):
        """Create mock RAG memory"""
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[
            {
                "source": "docs/testing/pytest.md",
                "version": "v1.0",
                "score": 0.95,
                "content": "Example pytest patterns with fixtures and mocking"
            },
            {
                "source": "docs/testing/best_practices.md",
                "version": "v2.0",
                "score": 0.88,
                "content": "Testing best practices for comprehensive coverage"
            }
        ])
        return mock

    @pytest.fixture
    def mock_tracer(self):
        """Create mock Langfuse tracer"""
        mock = Mock()
        mock.start_trace = Mock(return_value={"id": "trace-123"})
        mock.end_trace = Mock()
        return mock

    @pytest.fixture
    def qa_tester_agent(self, mock_rag_memory, mock_tracer):
        """Create QATesterAgent instance with mocked dependencies"""
        with patch('app.agents.qa_tester.Agent'):
            agent = QATesterAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model",
                temperature=0.2,
                top_p=0.9,
                max_tokens=3072,
                seed=42
            )
            return agent

    def test_init_default_params(self, mock_rag_memory, mock_tracer):
        """Test QATesterAgent initialization with default parameters"""
        with patch('app.agents.qa_tester.Agent'):
            agent = QATesterAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model"
            )

            assert agent.code_model == "test-model"
            assert agent.temperature == 0.2
            assert agent.top_p == 0.9
            assert agent.max_tokens == 3072
            assert agent.seed == 42

    def test_init_custom_params(self, mock_rag_memory, mock_tracer):
        """Test QATesterAgent initialization with custom parameters"""
        with patch('app.agents.qa_tester.Agent'):
            agent = QATesterAgent(
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

    def test_create_search_test_patterns_tool(self, qa_tester_agent):
        """Test search test patterns tool creation"""
        tool = qa_tester_agent._create_search_test_patterns_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    @pytest.mark.asyncio
    async def test_search_test_patterns_with_results(self, qa_tester_agent, mock_rag_memory):
        """Test search test patterns tool returns formatted results"""
        tool = qa_tester_agent._create_search_test_patterns_tool()

        result = await tool.func("pytest fixtures")

        # Verify RAG was called with correct query
        mock_rag_memory.retrieve.assert_called_once_with(
            query="testing pattern: pytest fixtures",
            top_k=5,
            min_score=0.7
        )

        # Verify result format
        assert "[Test Pattern 1]" in result
        assert "[Test Pattern 2]" in result
        assert "docs/testing/pytest.md" in result
        assert "v1.0" in result
        assert "0.95" in result

    @pytest.mark.asyncio
    async def test_search_test_patterns_no_results(self, qa_tester_agent):
        """Test search test patterns tool when no results found"""
        qa_tester_agent.rag_memory.retrieve = AsyncMock(return_value=[])
        tool = qa_tester_agent._create_search_test_patterns_tool()

        result = await tool.func("nonexistent pattern")

        assert "No test patterns found" in result
        assert "pytest best practices" in result

    def test_create_analyze_code_complexity_tool(self, qa_tester_agent):
        """Test analyze code complexity tool creation"""
        tool = qa_tester_agent._create_analyze_code_complexity_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_analyze_code_complexity_low(self, qa_tester_agent):
        """Test code complexity analysis for low complexity code"""
        tool = qa_tester_agent._create_analyze_code_complexity_tool()

        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""

        result = tool.func(code)

        assert "Functions: 2" in result
        assert "Classes: 0" in result
        assert "Low complexity" in result
        assert "Basic unit tests sufficient" in result

    def test_analyze_code_complexity_medium(self, qa_tester_agent):
        """Test code complexity analysis for medium complexity code"""
        tool = qa_tester_agent._create_analyze_code_complexity_tool()

        code = """
def process_data(data):
    if not data:
        return None

    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(item)

    return result

def validate(value):
    if value is None:
        raise ValueError("Invalid")
    return True
"""

        result = tool.func(code)

        assert "Functions: 2" in result
        assert "Branches:" in result
        assert "Medium complexity" in result

    def test_analyze_code_complexity_high(self, qa_tester_agent):
        """Test code complexity analysis for high complexity code"""
        tool = qa_tester_agent._create_analyze_code_complexity_tool()

        # Create code with many branches (need 15+ complexity = branches + functions)
        # 15 functions + some branches = high complexity
        code = """
def func1(x):
    if x: pass

def func2(x):
    if x: pass

def func3(x):
    if x: pass

def func4(x):
    if x: pass

def func5(x):
    if x: pass

def func6(x):
    if x: pass

def func7(x):
    if x: pass

def func8(x):
    if x: pass

def func9(x):
    if x: pass

def func10(x):
    if x: pass

def func11(x):
    if x: pass

def func12(x):
    if x: pass

def func13(x):
    if x: pass

def func14(x):
    if x: pass

def func15(x):
    if x: pass
"""

        result = tool.func(code)

        assert "High complexity" in result
        assert "Comprehensive test suite required" in result

    def test_analyze_code_complexity_with_classes(self, qa_tester_agent):
        """Test code complexity analysis for OOP code"""
        tool = qa_tester_agent._create_analyze_code_complexity_tool()

        code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
"""

        result = tool.func(code)

        assert "Classes: 1" in result
        assert "OOP code: Test class methods independently with fixtures" in result

    def test_analyze_code_complexity_high_branching(self, qa_tester_agent):
        """Test code complexity analysis recommends parametrization for high branching"""
        tool = qa_tester_agent._create_analyze_code_complexity_tool()

        # Create code with 11+ branches
        code = """
def many_branches(x):
    if x == 1: pass
    if x == 2: pass
    if x == 3: pass
    if x == 4: pass
    if x == 5: pass
    if x == 6: pass
    if x == 7: pass
    if x == 8: pass
    if x == 9: pass
    if x == 10: pass
    if x == 11: pass
"""

        result = tool.func(code)

        assert "High branching: Use parameterized tests for all paths" in result

    def test_analyze_code_complexity_invalid_syntax(self, qa_tester_agent):
        """Test code complexity analysis with invalid Python syntax"""
        tool = qa_tester_agent._create_analyze_code_complexity_tool()

        code = "def invalid syntax here"

        result = tool.func(code)

        assert "Cannot parse code" in result

    def test_create_calculate_coverage_gaps_tool(self, qa_tester_agent):
        """Test calculate coverage gaps tool creation"""
        tool = qa_tester_agent._create_calculate_coverage_gaps_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_calculate_coverage_gaps_no_tests(self, qa_tester_agent):
        """Test coverage gap calculation with no existing tests"""
        tool = qa_tester_agent._create_calculate_coverage_gaps_tool()

        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""

        result = tool.func(code, "")

        assert "Total Functions: 3" in result
        assert "Tested Functions: 0" in result
        assert "Untested Functions: 3" in result
        assert "Estimated Coverage: 0.0%" in result
        assert "add()" in result
        assert "subtract()" in result
        assert "multiply()" in result

    def test_calculate_coverage_gaps_partial_coverage(self, qa_tester_agent):
        """Test coverage gap calculation with partial test coverage"""
        tool = qa_tester_agent._create_calculate_coverage_gaps_tool()

        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""

        tests = """
def test_add():
    assert add(1, 2) == 3

def test_subtract():
    assert subtract(5, 3) == 2
"""

        result = tool.func(code, tests)

        assert "Total Functions: 3" in result
        assert "Tested Functions: 2" in result
        assert "Untested Functions: 1" in result
        assert "multiply()" in result
        assert "Estimated Coverage: 66.7%" in result

    def test_calculate_coverage_gaps_full_coverage(self, qa_tester_agent):
        """Test coverage gap calculation with full coverage"""
        tool = qa_tester_agent._create_calculate_coverage_gaps_tool()

        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""

        tests = """
def test_add():
    assert add(1, 2) == 3

def test_subtract():
    assert subtract(5, 3) == 2
"""

        result = tool.func(code, tests)

        assert "Total Functions: 2" in result
        assert "Tested Functions: 2" in result
        assert "Untested Functions: 0" in result
        assert "(All functions tested)" in result
        assert "✓ Good coverage" in result

    def test_calculate_coverage_gaps_invalid_code(self, qa_tester_agent):
        """Test coverage gap calculation with invalid source code"""
        tool = qa_tester_agent._create_calculate_coverage_gaps_tool()

        result = tool.func("invalid syntax", "")

        assert "Cannot parse source code" in result

    def test_create_validate_test_quality_tool(self, qa_tester_agent):
        """Test validate test quality tool creation"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_validate_test_quality_high_quality(self, qa_tester_agent):
        """Test test quality validation for high quality tests"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        test_code = """
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}

@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [(1, 2), (2, 3)])
def test_increment(input, expected):
    \"\"\"Test increment function with various inputs\"\"\"
    assert increment(input) == expected

@pytest.mark.unit
def test_invalid_input():
    \"\"\"Test error handling for invalid input\"\"\"
    with pytest.raises(ValueError):
        increment("invalid")
"""

        result = tool.func(test_code)

        assert "Quality Score: 100" in result or "Quality Score: 90" in result
        assert "✓ High Quality" in result or "✓ No critical issues" in result

    def test_validate_test_quality_no_assertions(self, qa_tester_agent):
        """Test test quality validation detects missing assertions"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        test_code = """
def test_something():
    result = do_something()
"""

        result = tool.func(test_code)

        assert "No assertions found" in result
        assert "tests won't validate anything" in result

    def test_validate_test_quality_missing_fixtures(self, qa_tester_agent):
        """Test test quality validation recommends fixtures"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        test_code = """
def test_something():
    self.data = {"key": "value"}
    assert self.data is not None
"""

        result = tool.func(test_code)

        assert "Consider using fixtures for better test isolation" in result

    def test_validate_test_quality_missing_docstrings(self, qa_tester_agent):
        """Test test quality validation recommends docstrings"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        test_code = """
import pytest

def test_add():
    assert add(1, 2) == 3
"""

        result = tool.func(test_code)

        assert "Add docstrings to test functions for documentation" in result

    def test_validate_test_quality_missing_parametrization(self, qa_tester_agent):
        """Test test quality validation recommends parametrization"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        test_code = """
def test_add():
    \"\"\"Test addition\"\"\"
    assert add(1, 2) == 3
"""

        result = tool.func(test_code)

        assert "Consider parametrization for testing multiple scenarios" in result

    def test_validate_test_quality_missing_error_tests(self, qa_tester_agent):
        """Test test quality validation recommends error testing"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        test_code = """
def test_add():
    \"\"\"Test addition\"\"\"
    assert add(1, 2) == 3
"""

        result = tool.func(test_code)

        assert "Add tests for error conditions using pytest.raises" in result

    def test_validate_test_quality_missing_markers(self, qa_tester_agent):
        """Test test quality validation recommends test markers"""
        tool = qa_tester_agent._create_validate_test_quality_tool()

        test_code = """
def test_add():
    \"\"\"Test addition\"\"\"
    assert add(1, 2) == 3
"""

        result = tool.func(test_code)

        assert "Add test markers (unit, integration, slow)" in result

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_rag_memory, mock_tracer):
        """Test successful QA tester agent execution"""
        with patch('app.agents.qa_tester.Agent') as mock_agent_class:
            with patch('app.agents.qa_tester.Crew') as mock_crew_class:
                with patch('app.agents.qa_tester.Task') as mock_task_class:
                    # Setup agent
                    qa_tester_agent = QATesterAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    # Mock crew execution
                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(return_value='''
```python
def test_example():
    """Test example function"""
    assert example() == True

def test_example_error():
    """Test error handling"""
    with pytest.raises(ValueError):
        example(invalid_input)

@pytest.fixture
def sample_fixture():
    return {"data": "value"}
```

Coverage Analysis:
All functions covered

Citations:
[Test Pattern 1] docs/testing/pytest.md (v1.0)
[Test Pattern 2] docs/testing/mocking.md (v2.0)
''')
                    mock_crew_class.return_value = mock_crew

                    result = await qa_tester_agent.execute(
                        task="Generate tests for example module",
                        context={"source_code": "def example(): return True"},
                        task_id="task-123"
                    )

                    assert "test_code" in result
                    assert "test_coverage" in result
                    assert "test_quality" in result
                    assert "citations" in result
                    assert "test_count" in result
                    assert "test_types" in result
                    assert "fixtures" in result
                    assert "execution_time_ms" in result

                    # Verify test count
                    assert result["test_count"] == 2

                    # Verify tracer was called
                    mock_tracer.start_trace.assert_called_once()
                    mock_tracer.end_trace.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, mock_rag_memory, mock_tracer):
        """Test error handling during execution"""
        with patch('app.agents.qa_tester.Agent') as mock_agent_class:
            with patch('app.agents.qa_tester.Crew') as mock_crew_class:
                with patch('app.agents.qa_tester.Task') as mock_task_class:
                    qa_tester_agent = QATesterAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    # Make crew execution fail
                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(side_effect=Exception("Crew failure"))
                    mock_crew_class.return_value = mock_crew

                    with pytest.raises(Exception) as exc_info:
                        await qa_tester_agent.execute(
                            task="Generate tests",
                            context={},
                            task_id="task-error"
                        )

                    assert "Crew failure" in str(exc_info.value)

                    # Verify error was traced
                    mock_tracer.end_trace.assert_called_once()
                    end_trace_call = mock_tracer.end_trace.call_args
                    assert "error" in end_trace_call[1]["output"]

    def test_extract_citations(self, qa_tester_agent):
        """Test citation extraction from result text"""
        result_text = """
[Test Pattern 1] docs/testing/pytest.md (v1.0)
[Test Pattern 2] docs/testing/fixtures.md (v2.1)
[Citation 3] docs/mocking.md (v3.0)
"""

        citations = qa_tester_agent._extract_citations(result_text)

        assert len(citations) == 3
        assert citations[0]["source"] == "docs/testing/pytest.md"
        assert citations[0]["version"] == "1.0"
        assert citations[1]["source"] == "docs/testing/fixtures.md"
        assert citations[1]["version"] == "2.1"
        assert citations[2]["source"] == "docs/mocking.md"
        assert citations[2]["version"] == "3.0"

    def test_extract_citations_limit(self, qa_tester_agent):
        """Test citation extraction limits to 5 citations"""
        result_text = """
[Test Pattern 1] doc1.md (v1.0)
[Test Pattern 2] doc2.md (v1.0)
[Test Pattern 3] doc3.md (v1.0)
[Test Pattern 4] doc4.md (v1.0)
[Test Pattern 5] doc5.md (v1.0)
[Test Pattern 6] doc6.md (v1.0)
[Test Pattern 7] doc7.md (v1.0)
"""

        citations = qa_tester_agent._extract_citations(result_text)

        assert len(citations) == 5  # Should limit to 5

    def test_extract_citations_none_found(self, qa_tester_agent):
        """Test citation extraction when no citations in result"""
        result_text = "Just some text without citations"

        citations = qa_tester_agent._extract_citations(result_text)

        assert len(citations) == 0

    def test_extract_fixtures(self, qa_tester_agent):
        """Test fixture extraction from test code"""
        # Note: The regex pattern requires @pytest.fixture and def to be matchable with .*?
        # which works with newlines in Python re.findall
        test_code = """import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}

@pytest.fixture(scope="module")
def db_session():
    return create_session()

def test_something(sample_data):
    assert sample_data is not None"""

        fixtures = qa_tester_agent._extract_fixtures(test_code)

        assert len(fixtures) == 2
        assert "sample_data" in fixtures
        assert "db_session" in fixtures

    def test_extract_fixtures_none_found(self, qa_tester_agent):
        """Test fixture extraction when no fixtures in code"""
        test_code = """
def test_something():
    assert True
"""

        fixtures = qa_tester_agent._extract_fixtures(test_code)

        assert len(fixtures) == 0

    @pytest.mark.asyncio
    async def test_execute_counts_tests_correctly(self, mock_rag_memory, mock_tracer):
        """Test that execute correctly counts test functions"""
        with patch('app.agents.qa_tester.Agent'):
            with patch('app.agents.qa_tester.Crew') as mock_crew_class:
                with patch('app.agents.qa_tester.Task'):
                    qa_tester_agent = QATesterAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(return_value='''
```python
def test_one(): pass
def test_two(): pass
def test_three(): pass
def test_four(): pass
def test_five(): pass
```
''')
                    mock_crew_class.return_value = mock_crew

                    result = await qa_tester_agent.execute(
                        task="Generate tests",
                        context={},
                        task_id="task-count"
                    )

                    assert result["test_count"] == 5

    @pytest.mark.asyncio
    async def test_execute_extracts_fixtures(self, mock_rag_memory, mock_tracer):
        """Test that execute extracts fixture names correctly"""
        with patch('app.agents.qa_tester.Agent'):
            with patch('app.agents.qa_tester.Crew') as mock_crew_class:
                with patch('app.agents.qa_tester.Task'):
                    qa_tester_agent = QATesterAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    # The regex matches @pytest.fixture.*?def (\w+)
                    # Make sure newlines work with the regex
                    mock_crew.kickoff_async = AsyncMock(return_value='''```python
@pytest.fixture
def mock_db():
    return MockDB()

@pytest.fixture
def test_data():
    return {"test": "data"}

def test_example(mock_db, test_data):
    assert True
```''')
                    mock_crew_class.return_value = mock_crew

                    result = await qa_tester_agent.execute(
                        task="Generate tests",
                        context={},
                        task_id="task-fixtures"
                    )

                    assert "mock_db" in result["fixtures"]
                    assert "test_data" in result["fixtures"]
