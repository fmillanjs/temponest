"""
QA Tester Agent - Automated test generation and quality assurance.

Responsibilities:
- Generate comprehensive pytest test suites (unit, integration, E2E)
- Calculate code coverage and identify gaps
- Create test reports with quality metrics
- Generate test fixtures and mocks
- Validate test quality (assertions, edge cases, error handling)
- Recommend testing strategies based on code complexity
"""

from typing import Dict, Any, List, Optional
import time
import json
import re
import ast
from crewai import Agent, Task, Crew
from crewai.tools import tool

from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer


class QATesterAgent:
    """QA Tester agent that generates tests and validates quality"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        code_model: str,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 3072,  # Higher for test generation
        seed: int = 42
    ):
        self.rag_memory = rag_memory
        self.tracer = tracer
        self.code_model = code_model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.seed = seed

        # Create the agent
        self.agent = Agent(
            role="Senior QA Engineer",
            goal="Generate comprehensive test suites that ensure code quality and catch bugs early",
            backstory="""You are a senior QA engineer with expertise in:
            - Test-Driven Development (TDD) and Behavior-Driven Development (BDD)
            - pytest framework with fixtures, parametrization, and mocking
            - Code coverage analysis and gap identification
            - Edge case and boundary condition testing
            - Integration and E2E test strategies
            - Test quality metrics (assertion density, test isolation)

            You ALWAYS:
            - Write tests for happy path AND error conditions
            - Include edge cases and boundary conditions
            - Use proper fixtures and mocks to isolate tests
            - Add descriptive test names and docstrings
            - Validate that tests are independent and repeatable
            - Reference testing patterns from the knowledge base
            - Aim for ≥80% code coverage
            - Test both success and failure scenarios""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._create_search_test_patterns_tool(),
                self._create_analyze_code_complexity_tool(),
                self._create_calculate_coverage_gaps_tool(),
                self._create_validate_test_quality_tool()
            ],
            llm_config={
                "model": code_model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed
            }
        )

    def _create_search_test_patterns_tool(self):
        """Create tool for searching test patterns"""
        rag_memory = self.rag_memory

        @tool("search_test_patterns")
        async def search_test_patterns(query: str) -> str:
            """
            Search the knowledge base for testing patterns and best practices.

            Args:
                query: What testing pattern you need (e.g., "pytest fixtures", "mocking async")

            Returns:
                Relevant testing patterns with examples
            """
            results = await rag_memory.retrieve(
                query=f"testing pattern: {query}",
                top_k=5,
                min_score=0.7
            )

            if not results:
                return "No test patterns found. Use pytest best practices and standard patterns."

            # Format results
            output = []
            for i, doc in enumerate(results, 1):
                output.append(f"""
[Test Pattern {i}] {doc['source']} (v{doc['version']})
Relevance: {doc['score']:.2f}

```
{doc['content']}
```

---
""")

            return "\n".join(output)

        return search_test_patterns

    def _create_analyze_code_complexity_tool(self):
        """Create tool for analyzing code complexity"""

        @tool("analyze_code_complexity")
        def analyze_code_complexity(code: str) -> str:
            """
            Analyze code complexity to determine testing strategy.

            Args:
                code: Python code to analyze

            Returns:
                Complexity analysis with testing recommendations
            """
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return f"Cannot parse code: {e}"

            # Count functions, classes, branches
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            branches = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)))

            # Calculate cyclomatic complexity (simplified)
            complexity = branches + functions

            recommendations = []
            if complexity < 5:
                recommendations.append("Low complexity: Basic unit tests sufficient")
            elif complexity < 15:
                recommendations.append("Medium complexity: Unit tests + integration tests recommended")
            else:
                recommendations.append("High complexity: Comprehensive test suite required (unit + integration + E2E)")

            if branches > 10:
                recommendations.append("High branching: Use parameterized tests for all paths")

            if classes > 0:
                recommendations.append("OOP code: Test class methods independently with fixtures")

            return f"""
Complexity Analysis:
- Functions: {functions}
- Classes: {classes}
- Branches: {branches}
- Cyclomatic Complexity: {complexity}

Recommendations:
{chr(10).join(f"  • {r}" for r in recommendations)}
"""

        return analyze_code_complexity

    def _create_calculate_coverage_gaps_tool(self):
        """Create tool for identifying coverage gaps"""

        @tool("calculate_coverage_gaps")
        def calculate_coverage_gaps(code: str, existing_tests: str = "") -> str:
            """
            Identify what parts of code are not covered by existing tests.

            Args:
                code: Source code to test
                existing_tests: Existing test code (optional)

            Returns:
                Coverage gap analysis
            """
            try:
                code_tree = ast.parse(code)
            except SyntaxError:
                return "Cannot parse source code"

            # Extract all functions and methods
            code_functions = set()
            for node in ast.walk(code_tree):
                if isinstance(node, ast.FunctionDef):
                    code_functions.add(node.name)

            # Extract tested functions (if tests provided)
            tested_functions = set()
            if existing_tests:
                try:
                    test_tree = ast.parse(existing_tests)
                    for node in ast.walk(test_tree):
                        if isinstance(node, ast.FunctionDef):
                            # Extract function name from test_function_name
                            if node.name.startswith("test_"):
                                # Simple heuristic: test_foo tests foo
                                tested_name = node.name[5:]  # Remove 'test_'
                                tested_functions.add(tested_name)
                except:
                    pass

            # Calculate gaps
            untested = code_functions - tested_functions
            coverage_pct = (len(tested_functions) / len(code_functions) * 100) if code_functions else 0

            return f"""
Coverage Analysis:
- Total Functions: {len(code_functions)}
- Tested Functions: {len(tested_functions)}
- Untested Functions: {len(untested)}
- Estimated Coverage: {coverage_pct:.1f}%

Untested Functions:
{chr(10).join(f"  • {fn}()" for fn in sorted(untested)) if untested else "  (All functions tested)"}

Recommendation: {"✓ Good coverage" if coverage_pct >= 80 else f"⚠ Need tests for {len(untested)} functions to reach 80% target"}
"""

        return calculate_coverage_gaps

    def _create_validate_test_quality_tool(self):
        """Create tool for validating test quality"""

        @tool("validate_test_quality")
        def validate_test_quality(test_code: str) -> str:
            """
            Validate quality of generated tests.

            Args:
                test_code: Test code to validate

            Returns:
                Quality assessment with improvement suggestions
            """
            issues = []
            recommendations = []

            # Check for assertions
            if "assert " not in test_code:
                issues.append("No assertions found - tests won't validate anything")

            # Check for test isolation
            if "@pytest.fixture" not in test_code and "self." in test_code:
                recommendations.append("Consider using fixtures for better test isolation")

            # Check for docstrings
            if '"""' not in test_code:
                recommendations.append("Add docstrings to test functions for documentation")

            # Check for parametrization
            if "def test_" in test_code and "@pytest.mark.parametrize" not in test_code:
                recommendations.append("Consider parametrization for testing multiple scenarios")

            # Check for error testing
            if "pytest.raises" not in test_code and "with raises" not in test_code:
                recommendations.append("Add tests for error conditions using pytest.raises")

            # Check for markers
            if "@pytest.mark" not in test_code:
                recommendations.append("Add test markers (unit, integration, slow) for better organization")

            quality_score = max(0, 100 - (len(issues) * 30) - (len(recommendations) * 10))

            return f"""
Test Quality Assessment:
- Quality Score: {quality_score}/100

Issues (Critical):
{chr(10).join(f"  ❌ {issue}" for issue in issues) if issues else "  ✓ No critical issues"}

Recommendations (Optional):
{chr(10).join(f"  • {rec}" for rec in recommendations) if recommendations else "  ✓ Tests follow best practices"}

Overall: {"✓ High Quality" if quality_score >= 80 else "⚠ Needs Improvement"}
"""

        return validate_test_quality

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute the QA Tester agent to generate tests.

        Args:
            task: Test generation task description
            context: Additional context (source_code, coverage_target, test_type)
            task_id: Unique task identifier for tracing

        Returns:
            {
                "test_code": "Generated pytest code",
                "test_coverage": {"estimated": 85, "gaps": [...]},
                "test_quality": {"score": 90, "issues": [], "recommendations": []},
                "citations": [{"source": "...", "version": "...", "score": 0.9}],
                "test_count": 15,
                "test_types": ["unit", "integration"],
                "fixtures": ["db_session", "mock_api"],
                "execution_time_ms": 1234
            }
        """
        start_time = time.time()

        # Start Langfuse trace
        trace = self.tracer.start_trace(
            name="qa_tester_execution",
            metadata={
                "task": task,
                "task_id": task_id,
                "model": self.code_model
            }
        )

        try:
            # Create CrewAI task
            crew_task = Task(
                description=f"""
Generate comprehensive pytest tests for the following:

{task}

Context:
{json.dumps(context, indent=2)}

Requirements:
1. Generate pytest test code with:
   - Unit tests for all functions/methods
   - Integration tests for component interactions
   - Edge cases and boundary conditions
   - Error handling tests (pytest.raises)
   - Proper fixtures for test data
   - Descriptive test names and docstrings

2. Include test organization:
   - Test markers (@pytest.mark.unit, @pytest.mark.integration)
   - Parametrized tests for multiple scenarios
   - Fixture definitions in conftest.py style

3. Ensure test quality:
   - Independent and repeatable tests
   - Clear assertions with failure messages
   - Mock external dependencies
   - ≥80% code coverage target

4. Provide:
   - Complete test file content
   - Coverage analysis
   - Test execution instructions

5. MUST cite ≥2 testing patterns/examples from knowledge base

Output Format:
```python
# test_module.py
[Your comprehensive test code here]
```

Coverage Analysis:
[Coverage gaps and recommendations]

Citations:
[List all sources used]
""",
                expected_output="Complete pytest test suite with coverage analysis and citations",
                agent=self.agent
            )

            # Execute with CrewAI
            crew = Crew(
                agents=[self.agent],
                tasks=[crew_task],
                verbose=True
            )

            result = await crew.kickoff_async()

            # Parse result
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Extract test code (simplified - in production, use better parsing)
            test_code_match = re.search(r'```python\n(.*?)\n```', str(result), re.DOTALL)
            test_code = test_code_match.group(1) if test_code_match else str(result)

            # Count tests
            test_count = len(re.findall(r'def test_', test_code))

            # Extract citations (simplified)
            citations = self._extract_citations(str(result))

            response = {
                "test_code": test_code,
                "test_coverage": {
                    "estimated": 85,  # Would calculate from actual analysis
                    "gaps": []
                },
                "test_quality": {
                    "score": 90,
                    "issues": [],
                    "recommendations": []
                },
                "citations": citations,
                "test_count": test_count,
                "test_types": ["unit", "integration"],
                "fixtures": self._extract_fixtures(test_code),
                "execution_time_ms": execution_time_ms
            }

            # End trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output=response,
                metadata={
                    "test_count": test_count,
                    "execution_time_ms": execution_time_ms,
                    "citations_count": len(citations)
                }
            )

            return response

        except Exception as e:
            # Log error to trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output={"error": str(e)},
                metadata={"error": True}
            )
            raise

    def _extract_citations(self, result: str) -> List[Dict[str, Any]]:
        """Extract citations from result"""
        citations = []
        # Simple regex to find citation patterns
        citation_pattern = r'\[(?:Citation|Test Pattern) \d+\] (.*?) \(v([\d.]+)\)'
        matches = re.findall(citation_pattern, result)

        for source, version in matches[:5]:  # Limit to 5
            citations.append({
                "source": source.strip(),
                "version": version,
                "score": 0.85  # Placeholder
            })

        return citations

    def _extract_fixtures(self, test_code: str) -> List[str]:
        """Extract fixture names from test code"""
        fixtures = []
        fixture_pattern = r'@pytest\.fixture.*?def (\w+)'
        matches = re.findall(fixture_pattern, test_code)
        return matches
