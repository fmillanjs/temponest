"""
Configuration settings for the Agent Service.
Loads from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from typing import Optional, Literal


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"

    # Qdrant
    QDRANT_URL: str = "http://qdrant:6333"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "http://langfuse:3000"

    # Auth Service
    AUTH_SERVICE_URL: str = "http://auth:9002"
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars-long"  # Must match auth service

    # Model Provider Selection
    # overseer: which provider for Overseer agent (ollama, claude, openai)
    # developer: which provider for Developer agent (ollama, claude, openai)
    OVERSEER_PROVIDER: Literal["ollama", "claude", "openai"] = "ollama"
    DEVELOPER_PROVIDER: Literal["ollama", "claude", "openai"] = "claude"

    # Ollama Models (when provider=ollama)
    OLLAMA_CHAT_MODEL: str = "mistral:7b-instruct"
    OLLAMA_CODE_MODEL: str = "qwen2.5-coder:7b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # Claude API Configuration (when provider=claude)
    # URL-based authentication (like opencode.ai)
    CLAUDE_AUTH_URL: Optional[str] = None  # e.g., "https://opencode.ai/api/auth"
    CLAUDE_SESSION_TOKEN: Optional[str] = None  # Session token from auth URL
    CLAUDE_API_URL: str = "https://api.anthropic.com/v1/messages"

    # Claude Models
    CLAUDE_CHAT_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_CODE_MODEL: str = "claude-sonnet-4-20250514"

    # OpenAI Configuration (when provider=openai)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_CHAT_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_CODE_MODEL: str = "gpt-4-turbo-preview"

    # Model Parameters (apply to all providers)
    MODEL_TEMPERATURE: float = 0.2
    MODEL_TOP_P: float = 0.9
    MODEL_MAX_TOKENS: int = 4096
    MODEL_SEED: int = 42

    # RAG
    RAG_TOP_K: int = 5
    RAG_MIN_SCORE: float = 0.7

    # Budget & Guardrails
    BUDGET_TOKENS_PER_TASK: int = 8000
    LATENCY_SLO_MS: int = 5000

    # Rate Limits
    OVERSEER_CPM: int = 20
    DEVELOPER_CPM: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_model_for_agent(self, agent_type: str) -> str:
        """Get the appropriate model based on agent type and provider"""
        if agent_type == "overseer":
            provider = self.OVERSEER_PROVIDER
            if provider == "ollama":
                return self.OLLAMA_CHAT_MODEL
            elif provider == "claude":
                return self.CLAUDE_CHAT_MODEL
            elif provider == "openai":
                return self.OPENAI_CHAT_MODEL
        elif agent_type == "developer":
            provider = self.DEVELOPER_PROVIDER
            if provider == "ollama":
                return self.OLLAMA_CODE_MODEL
            elif provider == "claude":
                return self.CLAUDE_CODE_MODEL
            elif provider == "openai":
                return self.OPENAI_CODE_MODEL

        # Fallback to ollama
        return self.OLLAMA_CHAT_MODEL if agent_type == "overseer" else self.OLLAMA_CODE_MODEL


settings = Settings()
