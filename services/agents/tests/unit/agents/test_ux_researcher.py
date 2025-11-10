"""
Unit tests for UX Researcher Agent.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.agents.ux_researcher import UXResearcherAgent
from app.memory.rag import RAGMemory
from app.memory.langfuse_tracer import LangfuseTracer


class TestUXResearcherAgentInit:
    """Test UX Researcher agent initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        assert agent.rag_memory == rag_memory
        assert agent.tracer == tracer
        assert agent.code_model == "gpt-4"
        assert agent.temperature == 0.4
        assert agent.top_p == 0.9
        assert agent.max_tokens == 3072
        assert agent.seed == 42
        assert agent.agent is not None

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="claude-3",
            temperature=0.6,
            top_p=0.95,
            max_tokens=4096,
            seed=123
        )

        assert agent.temperature == 0.6
        assert agent.top_p == 0.95
        assert agent.max_tokens == 4096
        assert agent.seed == 123

    def test_agent_has_four_tools(self):
        """Test agent has all four UX research tools"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        # Agent should have 4 tools
        assert len(agent.agent.tools) == 4


class TestUXResearcherSearchTool:
    """Test search_ux_research tool"""

    @pytest.mark.asyncio
    async def test_search_tool_with_results(self):
        """Test search tool returns research patterns"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Mock search results
        mock_result1 = Mock()
        mock_result1.page_content = "Persona templates should include demographics, goals, and pain points"
        mock_result1.metadata = {"source": "UX Research Guide"}

        mock_result2 = Mock()
        mock_result2.page_content = "User interviews should be semi-structured with open-ended questions"
        mock_result2.metadata = {"source": "Interview Best Practices"}

        # Create async mock for search method
        async_search_mock = AsyncMock(return_value=[mock_result1, mock_result2])
        rag_memory.search = async_search_mock

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        # Get the search tool
        search_tool = agent._create_search_research_tool()

        # Execute tool
        result = await search_tool.func(query="persona templates")

        assert "UX Research Guide" in result
        assert "Persona templates should include demographics" in result
        assert "Interview Best Practices" in result
        async_search_mock.assert_called_once_with("persona templates", top_k=3)

    @pytest.mark.asyncio
    async def test_search_tool_no_results(self):
        """Test search tool with no results"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Create async mock for search method
        rag_memory.search = AsyncMock(return_value=[])

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        search_tool = agent._create_search_research_tool()
        result = await search_tool.func(query="unknown topic")

        assert "No relevant research found" in result
        assert "Using general UX research best practices" in result

    @pytest.mark.asyncio
    async def test_search_tool_missing_source_metadata(self):
        """Test search tool handles missing source metadata"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        mock_result = Mock()
        mock_result.page_content = "Some research content"
        mock_result.metadata = {}  # No source

        # Create async mock for search method
        rag_memory.search = AsyncMock(return_value=[mock_result])

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        search_tool = agent._create_search_research_tool()
        result = await search_tool.func(query="test")

        assert "[Unknown]" in result
        assert "Some research content" in result


class TestUXResearcherPersonaTool:
    """Test generate_persona tool"""

    def test_generate_persona_structure(self):
        """Test persona generation returns correct structure"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        persona_tool = agent._create_generate_persona_tool()
        result = persona_tool.func(
            user_segment="Small business owner",
            demographics="35-45 years old, urban, tech-savvy",
            behaviors="Uses multiple SaaS tools daily"
        )

        persona = json.loads(result)

        assert persona["name"] == "Small business owner Persona"
        assert persona["segment"] == "Small business owner"
        assert persona["demographics"] == "35-45 years old, urban, tech-savvy"
        assert persona["behaviors"] == "Uses multiple SaaS tools daily"
        assert "goals" in persona
        assert "pain_points" in persona
        assert "motivations" in persona
        assert "tech_proficiency" in persona
        assert "quote" in persona

    def test_generate_persona_returns_json(self):
        """Test persona tool returns valid JSON"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        persona_tool = agent._create_generate_persona_tool()
        result = persona_tool.func(
            user_segment="Developer",
            demographics="25-35",
            behaviors="Codes daily"
        )

        # Should not raise JSONDecodeError
        persona = json.loads(result)
        assert isinstance(persona, dict)


class TestUXResearcherJourneyMapTool:
    """Test create_journey_map tool"""

    def test_journey_map_structure(self):
        """Test journey map has all required stages"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        journey_tool = agent._create_create_journey_map_tool()
        result = journey_tool.func(
            persona="Sarah (Business Owner)",
            scenario="First-time user onboarding"
        )

        journey = json.loads(result)

        assert journey["persona"] == "Sarah (Business Owner)"
        assert journey["scenario"] == "First-time user onboarding"
        assert "stages" in journey
        assert len(journey["stages"]) == 4

    def test_journey_map_stages(self):
        """Test journey map stages are correctly structured"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        journey_tool = agent._create_create_journey_map_tool()
        result = journey_tool.func(
            persona="Developer",
            scenario="Learning new API"
        )

        journey = json.loads(result)
        stages = journey["stages"]

        # Check all stages
        stage_names = [s["name"] for s in stages]
        assert "Awareness" in stage_names
        assert "Consideration" in stage_names
        assert "Decision" in stage_names
        assert "Retention" in stage_names

        # Check stage structure
        for stage in stages:
            assert "name" in stage
            assert "actions" in stage
            assert "thoughts" in stage
            assert "emotions" in stage
            assert "pain_points" in stage
            assert "opportunities" in stage

    def test_journey_map_returns_valid_json(self):
        """Test journey map returns valid JSON"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        journey_tool = agent._create_create_journey_map_tool()
        result = journey_tool.func(persona="Test", scenario="Test Scenario")

        # Should not raise JSONDecodeError
        journey = json.loads(result)
        assert isinstance(journey, dict)


class TestUXResearcherFeedbackTool:
    """Test analyze_feedback tool"""

    def test_analyze_feedback_structure(self):
        """Test feedback analysis returns correct structure"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        feedback_tool = agent._create_analyze_feedback_tool()
        result = feedback_tool.func(
            feedback_data="Users love the new feature but find it slow"
        )

        analysis = json.loads(result)

        assert "themes" in analysis
        assert "pain_points" in analysis
        assert "positive_feedback" in analysis
        assert "feature_requests" in analysis
        assert "recommendations" in analysis
        assert "priority_level" in analysis

    def test_analyze_feedback_returns_valid_json(self):
        """Test feedback analysis returns valid JSON"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        feedback_tool = agent._create_analyze_feedback_tool()
        result = feedback_tool.func(feedback_data="Great product!")

        # Should not raise JSONDecodeError
        analysis = json.loads(result)
        assert isinstance(analysis, dict)


class TestUXResearcherExecute:
    """Test UX Researcher execute method"""

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """Test basic research execution"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        # Mock crew execution
        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = '{"personas": [], "insights": "Test insights"}'
            mock_crew_class.return_value = mock_crew

            result = await agent.execute(
                task="Create user personas for SaaS platform",
                context={"target_users": "small businesses"},
                task_id="test-123"
            )

        assert "research" in result
        assert "execution_time_ms" in result
        assert "model" in result
        assert result["model"] == "gpt-4"
        assert isinstance(result["execution_time_ms"], int)

    @pytest.mark.asyncio
    async def test_execute_with_json_response(self):
        """Test execution with JSON response"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        research_data = {
            "personas": [{"name": "Sarah", "role": "Business Owner"}],
            "journey_maps": [],
            "insights": ["Users need simpler onboarding"],
            "recommendations": ["Add guided tour"],
            "citations": ["UX Research Guide"]
        }

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = json.dumps(research_data)
            mock_crew_class.return_value = mock_crew

            result = await agent.execute(
                task="Research onboarding flow",
                context={"product": "SaaS platform"},
                task_id="test-456"
            )

        assert result["research"] == research_data
        assert "personas" in result["research"]
        assert len(result["research"]["personas"]) == 1

    @pytest.mark.asyncio
    async def test_execute_with_markdown_json(self):
        """Test execution with JSON in markdown code block"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        research_data = {"insights": "Key findings", "recommendations": ["Action 1"]}
        markdown_response = f"Here's the research:\n```json\n{json.dumps(research_data)}\n```"

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = markdown_response
            mock_crew_class.return_value = mock_crew

            result = await agent.execute(
                task="Analyze user feedback",
                context={"feedback_count": 100},
                task_id="test-789"
            )

        assert result["research"] == research_data
        assert result["research"]["insights"] == "Key findings"

    @pytest.mark.asyncio
    async def test_execute_with_markdown_json_no_language(self):
        """Test execution with JSON in markdown code block without language specifier"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        research_data = {"personas": [], "insights": "Findings"}
        markdown_response = f"```\n{json.dumps(research_data)}\n```"

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = markdown_response
            mock_crew_class.return_value = mock_crew

            result = await agent.execute(
                task="Create personas",
                context={},
                task_id="test-999"
            )

        assert result["research"] == research_data

    @pytest.mark.asyncio
    async def test_execute_with_non_json_response(self):
        """Test execution with non-JSON text response"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        text_response = "Research findings: Users prefer simple interfaces."

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = text_response
            mock_crew_class.return_value = mock_crew

            result = await agent.execute(
                task="Quick research",
                context={},
                task_id="test-text"
            )

        assert result["research"] == text_response
        assert isinstance(result["research"], str)

    @pytest.mark.asyncio
    async def test_execute_with_context(self):
        """Test execution includes context in task"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        context = {
            "target_audience": "developers",
            "product_type": "API platform",
            "business_goals": ["improve retention"]
        }

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = '{"insights": "test"}'
            mock_crew_class.return_value = mock_crew

            with patch('app.agents.ux_researcher.Task') as mock_task_class:
                await agent.execute(
                    task="Research user needs",
                    context=context,
                    task_id="test-context"
                )

                # Verify Task was called with context in description
                call_args = mock_task_class.call_args
                assert call_args is not None
                description = call_args[1]["description"]
                assert "developers" in description
                assert "API platform" in description

    @pytest.mark.asyncio
    async def test_execute_traces_with_metadata(self):
        """Test execution includes tracing with metadata"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="claude-3"
        )

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = '{"test": "data"}'
            mock_crew_class.return_value = mock_crew

            await agent.execute(
                task="Test task",
                context={"key": "value"},
                task_id="trace-test"
            )

        tracer.trace.assert_called_once()
        call_args = tracer.trace.call_args
        assert call_args[1]["name"] == "ux_researcher_task_trace-test"
        assert call_args[1]["metadata"]["task"] == "Test task"
        assert call_args[1]["metadata"]["context"] == {"key": "value"}
        assert call_args[1]["metadata"]["model"] == "claude-3"

    @pytest.mark.asyncio
    async def test_execute_measures_time(self):
        """Test execution measures time correctly"""
        import asyncio

        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()

            # Add small delay to ensure time measurement > 0
            def kickoff_with_delay():
                import time
                time.sleep(0.001)  # 1ms delay
                return '{"test": "data"}'

            mock_crew.kickoff.side_effect = kickoff_with_delay
            mock_crew_class.return_value = mock_crew

            result = await agent.execute(
                task="Timed task",
                context={},
                task_id="time-test"
            )

        assert result["execution_time_ms"] > 0
        assert isinstance(result["execution_time_ms"], int)

    @pytest.mark.asyncio
    async def test_execute_with_dict_result(self):
        """Test execution when crew returns dict directly"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)
        tracer.trace = MagicMock()
        tracer.trace.return_value.__enter__ = Mock()
        tracer.trace.return_value.__exit__ = Mock()

        agent = UXResearcherAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="gpt-4"
        )

        dict_result = {"personas": ["persona1"], "insights": ["insight1"]}

        with patch('app.agents.ux_researcher.Crew') as mock_crew_class:
            mock_crew = Mock()
            mock_crew.kickoff.return_value = dict_result
            mock_crew_class.return_value = mock_crew

            result = await agent.execute(
                task="Test with dict",
                context={},
                task_id="dict-test"
            )

        assert result["research"] == dict_result
