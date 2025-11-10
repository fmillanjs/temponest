"""
Unit tests for Agent Factory.
"""

import pytest
from unittest.mock import Mock, patch
from app.agents.factory import AgentFactory
from app.agents.overseer import OverseerAgent
from app.agents.developer import DeveloperAgent
from app.agents.developer_v2 import DeveloperAgentV2
from app.agents.qa_tester import QATesterAgent
from app.agents.devops import DevOpsAgent
from app.agents.designer import DesignerAgent
from app.agents.security_auditor import SecurityAuditorAgent
from app.agents.ux_researcher import UXResearcherAgent
from app.memory.rag import RAGMemory
from app.memory.langfuse_tracer import LangfuseTracer


class TestAgentFactoryOverseer:
    """Test Factory for Overseer agent creation"""

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.OverseerAgent')
    def test_create_overseer_success(self, mock_overseer_class, mock_settings):
        """Test creating Overseer agent"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure mock settings
        mock_settings.OVERSEER_PROVIDER = "ollama"
        mock_settings.get_model_for_agent.return_value = "llama3.2"
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_MAX_TOKENS = 2048
        mock_settings.MODEL_SEED = 42

        mock_overseer_instance = Mock(spec=OverseerAgent)
        mock_overseer_class.return_value = mock_overseer_instance

        result = AgentFactory.create_overseer(rag_memory, tracer)

        assert result == mock_overseer_instance
        mock_overseer_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            chat_model="llama3.2",
            temperature=0.2,
            top_p=0.9,
            max_tokens=2048,
            seed=42
        )
        mock_settings.get_model_for_agent.assert_called_once_with("overseer")


class TestAgentFactoryDeveloper:
    """Test Factory for Developer agent creation"""

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.DeveloperAgent')
    def test_create_developer_ollama_provider(self, mock_developer_class, mock_settings):
        """Test creating Developer agent with Ollama provider (V1)"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure for Ollama provider
        mock_settings.DEVELOPER_PROVIDER = "ollama"
        mock_settings.get_model_for_agent.return_value = "codellama"
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_MAX_TOKENS = 4096
        mock_settings.MODEL_SEED = 42

        mock_developer_instance = Mock(spec=DeveloperAgent)
        mock_developer_class.return_value = mock_developer_instance

        result = AgentFactory.create_developer(rag_memory, tracer)

        assert result == mock_developer_instance
        mock_developer_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="codellama",
            temperature=0.2,
            top_p=0.9,
            max_tokens=4096,
            seed=42
        )

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.DeveloperAgentV2')
    def test_create_developer_claude_provider(self, mock_developer_v2_class, mock_settings):
        """Test creating Developer agent with Claude provider (V2)"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure for Claude provider
        mock_settings.DEVELOPER_PROVIDER = "claude"
        mock_settings.get_model_for_agent.return_value = "claude-3-sonnet"

        mock_developer_v2_instance = Mock(spec=DeveloperAgentV2)
        mock_developer_v2_class.return_value = mock_developer_v2_instance

        result = AgentFactory.create_developer(rag_memory, tracer)

        assert result == mock_developer_v2_instance
        mock_developer_v2_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            provider="claude",
            model="claude-3-sonnet"
        )

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.DeveloperAgentV2')
    def test_create_developer_openai_provider(self, mock_developer_v2_class, mock_settings):
        """Test creating Developer agent with OpenAI provider (V2)"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure for OpenAI provider
        mock_settings.DEVELOPER_PROVIDER = "openai"
        mock_settings.get_model_for_agent.return_value = "gpt-4"

        mock_developer_v2_instance = Mock(spec=DeveloperAgentV2)
        mock_developer_v2_class.return_value = mock_developer_v2_instance

        result = AgentFactory.create_developer(rag_memory, tracer)

        assert result == mock_developer_v2_instance
        mock_developer_v2_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            provider="openai",
            model="gpt-4"
        )


class TestAgentFactoryQATester:
    """Test Factory for QA Tester agent creation"""

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.QATesterAgent')
    def test_create_qa_tester_success(self, mock_qa_tester_class, mock_settings):
        """Test creating QA Tester agent"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure mock settings
        mock_settings.DEVELOPER_PROVIDER = "ollama"
        mock_settings.get_model_for_agent.return_value = "codellama"
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_MAX_TOKENS = 2048
        mock_settings.MODEL_SEED = 42

        mock_qa_tester_instance = Mock(spec=QATesterAgent)
        mock_qa_tester_class.return_value = mock_qa_tester_instance

        result = AgentFactory.create_qa_tester(rag_memory, tracer)

        assert result == mock_qa_tester_instance
        mock_qa_tester_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="codellama",
            temperature=0.2,
            top_p=0.9,
            max_tokens=4096,  # 2x max_tokens for tests
            seed=42
        )


class TestAgentFactoryDevOps:
    """Test Factory for DevOps agent creation"""

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.DevOpsAgent')
    def test_create_devops_success(self, mock_devops_class, mock_settings):
        """Test creating DevOps agent"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure mock settings
        mock_settings.DEVELOPER_PROVIDER = "ollama"
        mock_settings.get_model_for_agent.return_value = "codellama"
        mock_settings.MODEL_TEMPERATURE = 0.2
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_MAX_TOKENS = 2048
        mock_settings.MODEL_SEED = 42

        mock_devops_instance = Mock(spec=DevOpsAgent)
        mock_devops_class.return_value = mock_devops_instance

        result = AgentFactory.create_devops(rag_memory, tracer)

        assert result == mock_devops_instance
        mock_devops_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="codellama",
            temperature=0.2,
            top_p=0.9,
            max_tokens=4096,  # 2x max_tokens for infrastructure
            seed=42
        )


class TestAgentFactoryDesigner:
    """Test Factory for Designer agent creation"""

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.DesignerAgent')
    def test_create_designer_success(self, mock_designer_class, mock_settings):
        """Test creating Designer agent"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure mock settings
        mock_settings.DEVELOPER_PROVIDER = "ollama"
        mock_settings.get_model_for_agent.return_value = "codellama"
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_MAX_TOKENS = 2048
        mock_settings.MODEL_SEED = 42

        mock_designer_instance = Mock(spec=DesignerAgent)
        mock_designer_class.return_value = mock_designer_instance

        result = AgentFactory.create_designer(rag_memory, tracer)

        assert result == mock_designer_instance
        mock_designer_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="codellama",
            temperature=0.3,  # Custom temperature for creative work
            top_p=0.9,
            max_tokens=4096,  # 2x max_tokens for design
            seed=42
        )


class TestAgentFactorySecurityAuditor:
    """Test Factory for Security Auditor agent creation"""

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.SecurityAuditorAgent')
    def test_create_security_auditor_success(self, mock_security_class, mock_settings):
        """Test creating Security Auditor agent"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure mock settings
        mock_settings.DEVELOPER_PROVIDER = "ollama"
        mock_settings.get_model_for_agent.return_value = "codellama"
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_MAX_TOKENS = 2048
        mock_settings.MODEL_SEED = 42

        mock_security_instance = Mock(spec=SecurityAuditorAgent)
        mock_security_class.return_value = mock_security_instance

        result = AgentFactory.create_security_auditor(rag_memory, tracer)

        assert result == mock_security_instance
        mock_security_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="codellama",
            temperature=0.1,  # Very low temperature for precise analysis
            top_p=0.9,
            max_tokens=4096,  # 2x max_tokens for security reports
            seed=42
        )


class TestAgentFactoryUXResearcher:
    """Test Factory for UX Researcher agent creation"""

    @patch('app.agents.factory.settings')
    @patch('app.agents.factory.UXResearcherAgent')
    def test_create_ux_researcher_success(self, mock_ux_researcher_class, mock_settings):
        """Test creating UX Researcher agent"""
        rag_memory = Mock(spec=RAGMemory)
        tracer = Mock(spec=LangfuseTracer)

        # Configure mock settings
        mock_settings.DEVELOPER_PROVIDER = "ollama"
        mock_settings.get_model_for_agent.return_value = "codellama"
        mock_settings.MODEL_TOP_P = 0.9
        mock_settings.MODEL_MAX_TOKENS = 2048
        mock_settings.MODEL_SEED = 42

        mock_ux_researcher_instance = Mock(spec=UXResearcherAgent)
        mock_ux_researcher_class.return_value = mock_ux_researcher_instance

        result = AgentFactory.create_ux_researcher(rag_memory, tracer)

        assert result == mock_ux_researcher_instance
        mock_ux_researcher_class.assert_called_once_with(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model="codellama",
            temperature=0.4,  # Higher temperature for creative personas
            top_p=0.9,
            max_tokens=4096,  # 2x max_tokens for research
            seed=42
        )
