"""
Developer Agent - Code generation for CRUD APIs, schemas, and frontend components.

Responsibilities:
- Generate production-ready code (CRUD endpoints, database schemas, React components)
- Follow best practices from RAG knowledge base
- Create tests alongside implementation
- Validate generated code syntax
- Provide migration scripts and setup instructions
"""

from typing import Dict, Any, List, Optional
import time
import json
import re
from crewai import Agent, Task, Crew
from crewai.tools import tool

from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer


class DeveloperAgent:
    """Developer agent that generates code with tests"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        code_model: str,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 2048,
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
            role="Senior Full-Stack Developer",
            goal="Generate production-ready code for APIs, schemas, and frontend components",
            backstory="""You are a senior full-stack developer with expertise in:
            - RESTful API design with proper validation and error handling
            - Database schema design with migrations
            - React/TypeScript component development
            - Test-driven development (TDD)
            - Code documentation and best practices

            You ALWAYS:
            - Write tests alongside implementation
            - Follow patterns from the knowledge base
            - Include proper error handling and validation
            - Add clear comments and documentation
            - Reference specific examples from documentation""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._create_search_code_examples_tool(),
                self._create_validate_syntax_tool(),
                self._create_generate_tests_tool()
            ],
            llm_config={
                "model": code_model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed
            }
        )

    def _create_search_code_examples_tool(self):
        """Create tool for searching code examples"""
        rag_memory = self.rag_memory

        @tool("search_code_examples")
        async def search_code_examples(query: str) -> str:
            """
            Search the knowledge base for code examples and patterns.

            Args:
                query: What you're trying to implement

            Returns:
                Relevant code examples with sources
            """
            results = await rag_memory.retrieve(
                query=f"code example: {query}",
                top_k=5,
                min_score=0.7
            )

            if not results:
                return "No code examples found. Use standard best practices."

            # Format results
            output = []
            for i, doc in enumerate(results, 1):
                output.append(f"""
[Example {i}] {doc['source']} (v{doc['version']})
Relevance: {doc['score']:.2f}

```
{doc['content']}
```

---
""")

            return "\n".join(output)

        return search_code_examples

    def _create_validate_syntax_tool(self):
        """Create tool for basic syntax validation"""

        @tool("validate_syntax")
        def validate_syntax(code: str, language: str) -> str:
            """
            Validate code syntax (basic checks).

            Args:
                code: Code to validate
                language: Programming language (python, typescript, sql)

            Returns:
                Validation result
            """
            if not code or len(code.strip()) < 10:
                return "Code is too short or empty"

            # Basic checks
            if language == "python":
                # Check for basic Python structure
                if "def " not in code and "class " not in code:
                    return "No function or class definition found"

            elif language == "typescript":
                # Check for basic TS/JS structure
                if "function " not in code and "const " not in code and "export " not in code:
                    return "No function or export found"

            elif language == "sql":
                # Check for SQL keywords
                if not any(kw in code.upper() for kw in ["CREATE", "ALTER", "SELECT", "INSERT", "UPDATE"]):
                    return "No SQL statement found"

            return "✓ Basic syntax validation passed"

        return validate_syntax

    def _create_generate_tests_tool(self):
        """Create tool for generating test scaffolds"""

        @tool("generate_test_scaffold")
        def generate_test_scaffold(function_name: str, language: str) -> str:
            """
            Generate test scaffold for a function.

            Args:
                function_name: Name of function to test
                language: Programming language

            Returns:
                Test scaffold code
            """
            if language == "python":
                return f"""
import pytest

def test_{function_name}_success():
    # Test successful execution
    result = {function_name}(valid_input)
    assert result is not None
    assert result == expected_output

def test_{function_name}_validation():
    # Test input validation
    with pytest.raises(ValueError):
        {function_name}(invalid_input)

def test_{function_name}_edge_cases():
    # Test edge cases
    assert {function_name}(None) is None
    assert {function_name}([]) == []
"""

            elif language == "typescript":
                return f"""
import {{ describe, it, expect }} from 'vitest';

describe('{function_name}', () => {{
    it('should handle successful execution', () => {{
        const result = {function_name}(validInput);
        expect(result).toBeDefined();
        expect(result).toEqual(expectedOutput);
    }});

    it('should validate input', () => {{
        expect(() => {function_name}(invalidInput)).toThrow();
    }});

    it('should handle edge cases', () => {{
        expect({function_name}(null)).toBeNull();
        expect({function_name}([])).toEqual([]);
    }});
}});
"""

            return "Test scaffold not available for this language"

        return generate_test_scaffold

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute the developer agent to generate code.

        Returns:
            {
                "code": {
                    "implementation": "...",
                    "tests": "...",
                    "migrations": "..."
                },
                "citations": [{"source": "...", "version": "...", "score": 0.9}],
                "setup_instructions": ["..."],
                "file_map": [{"path": "...", "contents": "..."}]
            }
        """
        start_time = time.time()

        # Start trace
        trace_id = self.tracer.trace_agent_execution(
            agent_name="developer",
            task_id=task_id,
            task=task,
            context=context,
            model_info={
                "model": self.code_model,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_tokens": self.max_tokens,
                "seed": self.seed
            }
        )

        try:
            # Retrieve relevant code examples
            citations = await self.rag_memory.retrieve(
                query=f"code implementation: {task}",
                top_k=5,
                min_score=0.7
            )

            # Trace RAG retrieval
            self.tracer.trace_rag_retrieval(
                trace_id=trace_id,
                query=task,
                citations=citations,
                top_k=5,
                min_score=0.7
            )

            # Build context with examples
            examples_context = self._format_examples(citations)

            # Determine what to generate
            task_type = self._identify_task_type(task)

            # Create crew task
            crew_task = Task(
                description=f"""
Task: {task}

Type: {task_type}

Context: {context}

Relevant Examples:
{examples_context}

Requirements:
1. Generate production-ready code following the examples
2. Include comprehensive tests
3. Add clear comments and documentation
4. Include migration scripts if database changes are needed
5. Provide setup/deployment instructions
6. Reference citations in comments where you use their patterns

Output format (JSON):
{{
    "implementation": "// Full implementation code",
    "tests": "// Complete test suite",
    "migrations": "// Migration scripts (if applicable)",
    "setup_instructions": ["Step 1", "Step 2"],
    "citations_used": [1, 2]
}}
""",
                agent=self.agent,
                expected_output="Complete implementation with tests, migrations, and setup instructions in JSON format"
            )

            # Execute crew
            crew = Crew(
                agents=[self.agent],
                tasks=[crew_task],
                verbose=True
            )

            result = crew.kickoff()

            # Parse result
            code_output = self._parse_code_output(str(result))

            # Trace LLM call
            latency_ms = int((time.time() - start_time) * 1000)
            self.tracer.trace_llm_call(
                trace_id=trace_id,
                model=self.code_model,
                prompt=task,
                response=str(result),
                tokens_used=len(str(result)) // 4,
                latency_ms=latency_ms,
                metadata={
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "seed": self.seed,
                    "task_type": task_type
                }
            )

            return {
                "code": code_output,
                "citations": citations,
                "setup_instructions": code_output.get("setup_instructions", []),
                "file_map": self._generate_file_map(code_output),
                "latency_ms": latency_ms
            }

        except Exception as e:
            print(f"❌ Developer execution failed: {e}")
            raise

    def _format_examples(self, citations: List[Dict[str, Any]]) -> str:
        """Format code examples for prompt context"""
        output = []
        for i, cit in enumerate(citations, 1):
            output.append(f"""[Example {i}] {cit['source']} (v{cit['version']})
Score: {cit['score']:.2f}

{cit['content']}

---
""")
        return "\n".join(output)

    def _identify_task_type(self, task: str) -> str:
        """Identify what type of code to generate"""
        task_lower = task.lower()

        if "api" in task_lower or "endpoint" in task_lower or "crud" in task_lower:
            return "api_endpoint"
        elif "schema" in task_lower or "database" in task_lower or "migration" in task_lower:
            return "database_schema"
        elif "component" in task_lower or "frontend" in task_lower or "react" in task_lower:
            return "frontend_component"
        else:
            return "general_code"

    def _parse_code_output(self, result: str) -> Dict[str, Any]:
        """Parse code output from agent result"""
        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', result)

        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: extract code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', result, re.DOTALL)

        return {
            "implementation": code_blocks[0] if len(code_blocks) > 0 else result,
            "tests": code_blocks[1] if len(code_blocks) > 1 else "",
            "migrations": code_blocks[2] if len(code_blocks) > 2 else "",
            "setup_instructions": ["Review and test the generated code", "Deploy when ready"]
        }

    def _generate_file_map(self, code_output: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate file map for easy deployment"""
        files = []

        if code_output.get("implementation"):
            files.append({
                "path": "src/implementation.py",  # Adjust based on language
                "contents": code_output["implementation"]
            })

        if code_output.get("tests"):
            files.append({
                "path": "tests/test_implementation.py",
                "contents": code_output["tests"]
            })

        if code_output.get("migrations"):
            files.append({
                "path": "migrations/001_initial.sql",
                "contents": code_output["migrations"]
            })

        return files
