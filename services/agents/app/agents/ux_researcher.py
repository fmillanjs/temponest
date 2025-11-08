"""
UX Researcher Agent - User research, personas, journey mapping.

Responsibilities:
- Create user personas based on research data
- Generate user journey maps
- Conduct competitive analysis
- Create survey questions and interview scripts
- Analyze user feedback and identify pain points
- Generate usability testing plans
"""

from typing import Dict, Any, List, Optional
import time
import json
from crewai import Agent, Task, Crew
from crewai.tools import tool

from app.memory.rag import RAGMemory
from app.memory.langfuse_tracer import LangfuseTracer


class UXResearcherAgent:
    """UX Researcher agent that conducts user research and creates personas"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        code_model: str,
        temperature: float = 0.4,  # Higher for creative persona development
        top_p: float = 0.9,
        max_tokens: int = 3072,
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
            role="Senior UX Researcher",
            goal="Conduct thorough user research to inform design decisions and create actionable insights",
            backstory="""You are a senior UX researcher with expertise in:
            - Qualitative and quantitative research methodologies
            - User persona development and segmentation
            - Journey mapping and service blueprints
            - Usability testing and heuristic evaluation
            - Competitive analysis and market research
            - Survey design and interview techniques
            - Data synthesis and insight generation

            You ALWAYS:
            - Ground research in real user data and behavioral patterns
            - Create detailed, realistic personas with motivations and pain points
            - Map complete user journeys including emotional states
            - Identify actionable insights and recommendations
            - Consider diverse user groups and accessibility needs
            - Use research frameworks (Jobs-to-be-Done, Design Thinking, etc.)
            - Validate assumptions with data and citations
            - Provide clear recommendations for designers and developers""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._create_search_research_tool(),
                self._create_generate_persona_tool(),
                self._create_create_journey_map_tool(),
                self._create_analyze_feedback_tool()
            ],
            llm_config={
                "model": code_model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed
            }
        )

    def _create_search_research_tool(self):
        """Create tool for searching UX research patterns"""
        rag_memory = self.rag_memory

        @tool("search_ux_research")
        async def search_ux_research(query: str) -> str:
            """
            Search the knowledge base for UX research methodologies and best practices.

            Args:
                query: Research topic (e.g., "persona templates", "user interview scripts")

            Returns:
                Relevant research patterns and methodologies
            """
            results = await rag_memory.search(query, top_k=3)
            if not results:
                return "No relevant research found. Using general UX research best practices."

            return "\n\n".join([
                f"[{r.metadata.get('source', 'Unknown')}]: {r.page_content}"
                for r in results
            ])

        return search_ux_research

    def _create_generate_persona_tool(self):
        """Create tool for generating user personas"""
        @tool("generate_persona")
        def generate_persona(user_segment: str, demographics: str, behaviors: str) -> str:
            """
            Generate a detailed user persona.

            Args:
                user_segment: Target user segment (e.g., "Small business owner")
                demographics: Age, location, occupation
                behaviors: User behaviors and patterns

            Returns:
                Structured persona with goals, pain points, and motivations
            """
            persona_template = {
                "name": f"{user_segment} Persona",
                "segment": user_segment,
                "demographics": demographics,
                "behaviors": behaviors,
                "goals": [],
                "pain_points": [],
                "motivations": [],
                "tech_proficiency": "TBD",
                "quote": "TBD"
            }
            return json.dumps(persona_template, indent=2)

        return generate_persona

    def _create_create_journey_map_tool(self):
        """Create tool for journey mapping"""
        @tool("create_journey_map")
        def create_journey_map(persona: str, scenario: str) -> str:
            """
            Create a user journey map for a specific scenario.

            Args:
                persona: User persona name
                scenario: Journey scenario (e.g., "First-time user onboarding")

            Returns:
                Journey map with stages, actions, emotions, and opportunities
            """
            journey_template = {
                "persona": persona,
                "scenario": scenario,
                "stages": [
                    {
                        "name": "Awareness",
                        "actions": [],
                        "thoughts": [],
                        "emotions": "neutral",
                        "pain_points": [],
                        "opportunities": []
                    },
                    {
                        "name": "Consideration",
                        "actions": [],
                        "thoughts": [],
                        "emotions": "curious",
                        "pain_points": [],
                        "opportunities": []
                    },
                    {
                        "name": "Decision",
                        "actions": [],
                        "thoughts": [],
                        "emotions": "hopeful",
                        "pain_points": [],
                        "opportunities": []
                    },
                    {
                        "name": "Retention",
                        "actions": [],
                        "thoughts": [],
                        "emotions": "satisfied",
                        "pain_points": [],
                        "opportunities": []
                    }
                ]
            }
            return json.dumps(journey_template, indent=2)

        return create_journey_map

    def _create_analyze_feedback_tool(self):
        """Create tool for analyzing user feedback"""
        @tool("analyze_feedback")
        def analyze_feedback(feedback_data: str) -> str:
            """
            Analyze user feedback to identify patterns and insights.

            Args:
                feedback_data: User feedback text or data

            Returns:
                Analyzed insights with themes and recommendations
            """
            analysis_template = {
                "themes": [],
                "pain_points": [],
                "positive_feedback": [],
                "feature_requests": [],
                "recommendations": [],
                "priority_level": "TBD"
            }
            return json.dumps(analysis_template, indent=2)

        return analyze_feedback

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute UX research task.

        Args:
            task: Research task description
            context: Additional context (user data, objectives, etc.)
            task_id: Unique task identifier for tracing

        Returns:
            Research findings with personas, journey maps, and recommendations
        """
        start_time = time.time()

        # Create task with context
        task_description = f"""
        Research Task: {task}

        Context:
        {json.dumps(context, indent=2)}

        DELIVERABLES:
        1. User personas (if applicable)
        2. Journey maps (if applicable)
        3. Key insights and findings
        4. Actionable recommendations
        5. Research citations from knowledge base

        Format your response as structured JSON with clear sections.
        Include at least 2 citations from the knowledge base to ground your research.
        """

        crew_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output="""
            Structured research report in JSON format with:
            - personas: Array of user personas
            - journey_maps: Array of journey maps
            - insights: Key findings
            - recommendations: Actionable next steps
            - citations: Array of sources from knowledge base
            """
        )

        # Create and execute crew
        crew = Crew(
            agents=[self.agent],
            tasks=[crew_task],
            verbose=True
        )

        # Execute with tracing
        with self.tracer.trace(
            name=f"ux_researcher_task_{task_id}",
            metadata={
                "task": task,
                "context": context,
                "model": self.code_model
            }
        ):
            result = crew.kickoff()

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Parse result
        try:
            if isinstance(result, str):
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result, re.DOTALL)
                if json_match:
                    parsed_result = json.loads(json_match.group(1))
                else:
                    # Try parsing the whole thing
                    parsed_result = json.loads(result)
            else:
                parsed_result = result

            return {
                "research": parsed_result,
                "execution_time_ms": execution_time_ms,
                "model": self.code_model
            }
        except (json.JSONDecodeError, AttributeError):
            # Return as-is if not JSON
            return {
                "research": str(result),
                "execution_time_ms": execution_time_ms,
                "model": self.code_model
            }
