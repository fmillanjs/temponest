"""
Agent Factory - Creates agents based on configuration.

Supports both CrewAI-based agents (v1) and direct LLM agents (v2).
"""

from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer
from settings import settings

from .overseer import OverseerAgent
from .developer import DeveloperAgent
from .developer_v2 import DeveloperAgentV2
from .qa_tester import QATesterAgent


class AgentFactory:
    """Factory for creating agents with appropriate providers"""

    @staticmethod
    def create_overseer(
        rag_memory: RAGMemory,
        tracer: LangfuseTracer
    ):
        """Create Overseer agent based on configuration"""
        provider = settings.OVERSEER_PROVIDER
        model = settings.get_model_for_agent("overseer")

        # For now, Overseer uses CrewAI approach
        # Can be extended to V2 approach if needed
        return OverseerAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            chat_model=model,
            temperature=settings.MODEL_TEMPERATURE,
            top_p=settings.MODEL_TOP_P,
            max_tokens=settings.MODEL_MAX_TOKENS,
            seed=settings.MODEL_SEED
        )

    @staticmethod
    def create_developer(
        rag_memory: RAGMemory,
        tracer: LangfuseTracer
    ):
        """Create Developer agent based on configuration"""
        provider = settings.DEVELOPER_PROVIDER
        model = settings.get_model_for_agent("developer")

        if provider in ["claude", "openai"]:
            # Use V2 (direct LLM) for Claude and OpenAI
            return DeveloperAgentV2(
                rag_memory=rag_memory,
                tracer=tracer,
                provider=provider,
                model=model
            )
        else:
            # Use V1 (CrewAI) for Ollama
            return DeveloperAgent(
                rag_memory=rag_memory,
                tracer=tracer,
                code_model=model,
                temperature=settings.MODEL_TEMPERATURE,
                top_p=settings.MODEL_TOP_P,
                max_tokens=settings.MODEL_MAX_TOKENS,
                seed=settings.MODEL_SEED
            )

    @staticmethod
    def create_qa_tester(
        rag_memory: RAGMemory,
        tracer: LangfuseTracer
    ):
        """Create QA Tester agent based on configuration"""
        # QA Tester uses code model (same as Developer)
        provider = settings.DEVELOPER_PROVIDER  # Reuse developer provider
        model = settings.get_model_for_agent("developer")

        # Use CrewAI approach for now
        return QATesterAgent(
            rag_memory=rag_memory,
            tracer=tracer,
            code_model=model,
            temperature=settings.MODEL_TEMPERATURE,
            top_p=settings.MODEL_TOP_P,
            max_tokens=settings.MODEL_MAX_TOKENS * 2,  # Tests need more tokens
            seed=settings.MODEL_SEED
        )
