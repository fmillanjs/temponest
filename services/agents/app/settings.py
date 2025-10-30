"""
Configuration settings for the Agent Service.
Loads from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from typing import Optional


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

    # Models
    CHAT_MODEL: str = "mistral:7b-instruct"
    CODE_MODEL: str = "qwen2.5-coder:7b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # Model Parameters
    MODEL_TEMPERATURE: float = 0.2
    MODEL_TOP_P: float = 0.9
    MODEL_MAX_TOKENS: int = 2048
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


settings = Settings()
