"""
Overseer Agent - Coordinator and task decomposition.

Responsibilities:
- Break down high-level goals into concrete tasks
- Route tasks to specialized agents (Developer, etc.)
- Validate tasks against RAG knowledge base
- Ensure all outputs are grounded in ≥2 citations
- Enforce budget and latency guardrails
"""

from typing import Dict, Any, List
import time
import httpx
from crewai import Agent, Task, Crew
from crewai.tools import tool

from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer


class OverseerAgent:
    """Overseer agent that coordinates multi-agent workflows"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        chat_model: str,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 2048,
        seed: int = 42
    ):
        self.rag_memory = rag_memory
        self.tracer = tracer
        self.chat_model = chat_model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.seed = seed

        # Create the agent
        self.agent = Agent(
            role="Overseer Coordinator",
            goal="Break down goals into actionable tasks and route them to specialized agents",
            backstory="""You are an experienced project coordinator who excels at:
            - Decomposing complex goals into concrete, measurable tasks
            - Identifying which agent is best suited for each task
            - Validating that all recommendations are grounded in documentation
            - Managing task dependencies and execution order
            - Ensuring quality through proper citations and sources""",
            verbose=True,
            allow_delegation=True,
            tools=[
                self._create_search_knowledge_tool(),
                self._create_validate_plan_tool()
            ],
            llm_config={
                "model": chat_model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed
            }
        )

    def _create_search_knowledge_tool(self):
        """Create tool for searching the knowledge base"""
        rag_memory = self.rag_memory

        @tool("search_knowledge")
        async def search_knowledge(query: str) -> str:
            """
            Search the knowledge base for relevant information.
            Always use this before making recommendations.

            Args:
                query: Search query describing what you need to know

            Returns:
                Relevant documentation with citations
            """
            results = await rag_memory.retrieve(
                query=query,
                top_k=5,
                min_score=0.7
            )

            if not results:
                return "No relevant documentation found. ASK HUMAN for guidance."

            # Format results with citations
            output = []
            for i, doc in enumerate(results, 1):
                output.append(f"""
[Citation {i}]
Source: {doc['source']}
Version: {doc['version']}
Score: {doc['score']:.2f}

{doc['content']}

---
""")

            return "\n".join(output)

        return search_knowledge

    def _create_validate_plan_tool(self):
        """Create tool for validating plans have sufficient citations"""

        @tool("validate_plan")
        def validate_plan(plan: str, citations_count: int) -> str:
            """
            Validate that a plan is properly grounded.

            Args:
                plan: The plan text
                citations_count: Number of unique citations referenced

            Returns:
                Validation result
            """
            if citations_count < 2:
                return f"INSUFFICIENT GROUNDING: Found {citations_count} citations, need ≥2. ASK HUMAN or search for more documentation."

            if len(plan) < 50:
                return "Plan is too brief. Provide more detail."

            return f"✓ Plan validated with {citations_count} citations"

        return validate_plan

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute the overseer agent to decompose and route tasks.

        Returns:
            {
                "plan": [{"task": "...", "agent": "...", "priority": 1}],
                "citations": [{"source": "...", "version": "...", "score": 0.9}],
                "recommendations": "...",
                "next_steps": ["..."]
            }
        """
        start_time = time.time()

        # Start trace
        trace_id = self.tracer.trace_agent_execution(
            agent_name="overseer",
            task_id=task_id,
            task=task,
            context=context,
            model_info={
                "model": self.chat_model,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_tokens": self.max_tokens,
                "seed": self.seed
            }
        )

        try:
            # Retrieve relevant knowledge
            citations = await self.rag_memory.retrieve(
                query=task,
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

            # Build context with citations
            knowledge_context = self._format_citations(citations)

            # Create crew task with grounding requirement
            crew_task = Task(
                description=f"""
Given this goal: {task}

Additional context: {context}

Knowledge base citations:
{knowledge_context}

Your job:
1. Break down the goal into 3-5 concrete, actionable tasks
2. For each task, specify which agent should handle it (Developer, Overseer)
3. Identify dependencies between tasks
4. Ensure ALL recommendations reference specific citations [Citation N]
5. Include at least 2 different citations in your plan

Output format:
PLAN:
- Task 1: [description] (Agent: Developer, Priority: 1, Citations: [1,2])
- Task 2: [description] (Agent: Developer, Priority: 2, Citations: [1])
...

RECOMMENDATIONS:
[Your recommendations based on citations]

NEXT_STEPS:
1. [First step]
2. [Second step]
...
""",
                agent=self.agent,
                expected_output="A detailed plan with task breakdown, agent assignments, and citations"
            )

            # Execute crew
            crew = Crew(
                agents=[self.agent],
                tasks=[crew_task],
                verbose=True
            )

            result = crew.kickoff()

            # Parse result
            plan = self._parse_plan(str(result))

            # Trace LLM call
            latency_ms = int((time.time() - start_time) * 1000)
            self.tracer.trace_llm_call(
                trace_id=trace_id,
                model=self.chat_model,
                prompt=task,
                response=str(result),
                tokens_used=len(str(result)) // 4,  # Rough estimate
                latency_ms=latency_ms,
                metadata={
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "seed": self.seed
                }
            )

            return {
                "plan": plan,
                "citations": citations,
                "recommendations": str(result),
                "next_steps": self._extract_next_steps(str(result)),
                "latency_ms": latency_ms
            }

        except Exception as e:
            print(f"❌ Overseer execution failed: {e}")
            raise

    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for prompt context"""
        output = []
        for i, cit in enumerate(citations, 1):
            output.append(f"""[Citation {i}]
Source: {cit['source']} (v{cit['version']})
Relevance: {cit['score']:.2f}
Content: {cit['content'][:300]}...
""")
        return "\n".join(output)

    def _parse_plan(self, result: str) -> List[Dict[str, Any]]:
        """Parse plan from agent output"""
        # Simple parser - look for task lines
        tasks = []
        lines = result.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                # Extract task info
                tasks.append({
                    "task": line.lstrip("-* "),
                    "agent": "developer" if "Developer" in line else "overseer",
                    "priority": 1  # Default priority
                })

        return tasks

    def _extract_next_steps(self, result: str) -> List[str]:
        """Extract next steps from agent output"""
        steps = []
        lines = result.split("\n")
        in_next_steps = False

        for line in lines:
            line = line.strip()
            if "NEXT_STEPS" in line or "NEXT STEPS" in line:
                in_next_steps = True
                continue

            if in_next_steps and (line.startswith("-") or line.startswith("*") or line[0].isdigit()):
                steps.append(line.lstrip("-*0123456789. "))

        return steps
