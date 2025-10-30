"""
Developer Agent V2 - Direct LLM integration with provider flexibility.

Uses UnifiedLLMClient for multi-provider support (Ollama, Claude, OpenAI).
No CrewAI dependency - direct prompt engineering.
"""

from typing import Dict, Any, List
import time
import json
import re

from llm.unified_client import UnifiedLLMClient
from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer
from settings import settings


class DeveloperAgentV2:
    """Developer agent with flexible LLM provider support"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        provider: str = "claude",
        model: str = "claude-sonnet-4-20250514"
    ):
        self.rag_memory = rag_memory
        self.tracer = tracer
        self.provider = provider
        self.model = model

        # Initialize unified LLM client based on provider
        if provider == "claude":
            self.llm = UnifiedLLMClient(
                provider="claude",
                model=model,
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS,
                top_p=settings.MODEL_TOP_P,
                seed=settings.MODEL_SEED,
                claude_auth_url=settings.CLAUDE_AUTH_URL,
                claude_session_token=settings.CLAUDE_SESSION_TOKEN,
                claude_api_url=settings.CLAUDE_API_URL
            )
        elif provider == "openai":
            self.llm = UnifiedLLMClient(
                provider="openai",
                model=model,
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS,
                top_p=settings.MODEL_TOP_P,
                seed=settings.MODEL_SEED,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_base_url=settings.OPENAI_BASE_URL
            )
        else:  # ollama
            self.llm = UnifiedLLMClient(
                provider="ollama",
                model=model,
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS,
                top_p=settings.MODEL_TOP_P,
                seed=settings.MODEL_SEED,
                ollama_base_url=settings.OLLAMA_BASE_URL
            )

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
            agent_name="developer_v2",
            task_id=task_id,
            task=task,
            context=context,
            model_info={
                "provider": self.provider,
                "model": self.model,
                "temperature": settings.MODEL_TEMPERATURE,
                "top_p": settings.MODEL_TOP_P,
                "max_tokens": settings.MODEL_MAX_TOKENS,
                "seed": settings.MODEL_SEED
            }
        )

        try:
            # Retrieve relevant code examples from RAG
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

            # Build prompt with examples
            examples_context = self._format_examples(citations)

            # Determine task type
            task_type = self._identify_task_type(task)

            # Build comprehensive prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(task, context, examples_context, task_type)

            # Call LLM
            response = await self.llm.complete(
                prompt=user_prompt,
                system=system_prompt
            )

            # Parse response
            code_output = self._parse_code_output(response["text"])

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Trace LLM call
            self.tracer.trace_llm_call(
                trace_id=trace_id,
                model=self.model,
                prompt=user_prompt[:500],  # Truncate for logging
                response=response["text"][:500],
                tokens_used=response["usage"].get("output_tokens", 0),
                latency_ms=latency_ms,
                metadata={
                    "provider": self.provider,
                    "temperature": settings.MODEL_TEMPERATURE,
                    "top_p": settings.MODEL_TOP_P,
                    "seed": settings.MODEL_SEED,
                    "task_type": task_type
                }
            )

            return {
                "code": code_output,
                "citations": citations,
                "setup_instructions": code_output.get("setup_instructions", []),
                "file_map": self._generate_file_map(code_output),
                "latency_ms": latency_ms,
                "provider": self.provider,
                "model": self.model
            }

        except Exception as e:
            print(f"❌ Developer execution failed: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build system prompt for developer agent"""
        return """You are a senior full-stack developer specializing in production-ready code generation.

Your expertise includes:
- RESTful API design with FastAPI/Express
- Database schema design with migrations (PostgreSQL, SQLite)
- React/TypeScript component development
- Test-driven development
- Code documentation and best practices

When generating code, you ALWAYS:
1. Write complete, production-ready implementations
2. Include comprehensive test suites
3. Add clear comments and documentation
4. Follow the patterns from provided examples
5. Include proper error handling and validation
6. Provide setup/deployment instructions

Output format: Return valid JSON with this structure:
{
  "implementation": "// Full implementation code with comments",
  "tests": "// Complete test suite",
  "migrations": "// Database migrations if applicable",
  "setup_instructions": ["Step 1", "Step 2", ...]
}

Be concise but thorough. Generate code that developers can immediately use."""

    def _build_user_prompt(
        self,
        task: str,
        context: Dict[str, Any],
        examples: str,
        task_type: str
    ) -> str:
        """Build user prompt with task and context"""
        return f"""Task: {task}

Type: {task_type}

Context:
{json.dumps(context, indent=2)}

Relevant Code Examples from Documentation:
{examples}

Requirements:
1. Generate production-ready {task_type} code
2. Follow the patterns from the examples above
3. Include comprehensive tests
4. Add migrations if database changes needed
5. Provide clear setup instructions
6. Output MUST be valid JSON matching the specified format

Generate the code now:"""

    def _format_examples(self, citations: List[Dict[str, Any]]) -> str:
        """Format RAG citations as examples"""
        if not citations:
            return "No specific examples found. Use standard best practices."

        output = []
        for i, cit in enumerate(citations[:3], 1):  # Use top 3
            output.append(f"""
Example {i} (from {cit['source']} v{cit['version']}, relevance: {cit['score']:.2f}):
```
{cit['content'][:800]}...
```
""")
        return "\n".join(output)

    def _identify_task_type(self, task: str) -> str:
        """Identify what type of code to generate"""
        task_lower = task.lower()

        if "api" in task_lower or "endpoint" in task_lower or "crud" in task_lower:
            return "REST API"
        elif "schema" in task_lower or "database" in task_lower or "migration" in task_lower:
            return "Database Schema"
        elif "component" in task_lower or "frontend" in task_lower or "react" in task_lower or "ui" in task_lower:
            return "Frontend Component"
        elif "test" in task_lower:
            return "Test Suite"
        else:
            return "General Implementation"

    def _parse_code_output(self, result: str) -> Dict[str, Any]:
        """Parse code output from LLM response"""
        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', result)

        if json_match:
            try:
                parsed = json.loads(json_match.group())
                # Validate required fields
                if "implementation" not in parsed:
                    parsed["implementation"] = result
                return parsed
            except json.JSONDecodeError:
                pass

        # Fallback: extract code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', result, re.DOTALL)

        return {
            "implementation": code_blocks[0] if len(code_blocks) > 0 else result,
            "tests": code_blocks[1] if len(code_blocks) > 1 else "",
            "migrations": code_blocks[2] if len(code_blocks) > 2 else "",
            "setup_instructions": [
                "Review the generated code",
                "Run tests to verify functionality",
                "Deploy when ready"
            ]
        }

    def _generate_file_map(self, code_output: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate file map for deployment"""
        files = []

        if code_output.get("implementation"):
            # Detect language
            impl = code_output["implementation"]
            if "def " in impl or "import " in impl:
                ext = "py"
            elif "function" in impl or "const" in impl or "import" in impl:
                ext = "ts" if "interface" in impl else "js"
            else:
                ext = "txt"

            files.append({
                "path": f"src/implementation.{ext}",
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
