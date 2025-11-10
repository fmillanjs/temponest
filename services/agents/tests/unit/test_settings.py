"""
Unit tests for settings.py configuration.
"""

import pytest
from app.settings import Settings


class TestSettingsInit:
    """Test suite for Settings initialization"""

    def test_settings_default_values(self):
        """Test Settings loads with default or environment values"""
        settings = Settings()

        # Check values are set (may be from env or defaults)
        assert settings.DATABASE_URL is not None
        assert "postgresql" in settings.DATABASE_URL
        assert settings.QDRANT_URL is not None
        assert settings.OLLAMA_BASE_URL is not None

        # Check auth settings are set
        assert settings.AUTH_SERVICE_URL is not None

        # Check model settings are set
        assert settings.OLLAMA_CHAT_MODEL is not None
        assert settings.OLLAMA_CODE_MODEL is not None
        assert settings.EMBEDDING_MODEL is not None

    def test_settings_custom_values(self):
        """Test Settings can be overridden"""
        settings = Settings(
            DATABASE_URL="postgresql://custom:5432/db",
            OLLAMA_BASE_URL="http://custom-ollama:11434"
        )

        assert settings.DATABASE_URL == "postgresql://custom:5432/db"
        assert settings.OLLAMA_BASE_URL == "http://custom-ollama:11434"

    def test_settings_langfuse_optional(self):
        """Test Langfuse settings can be None or set from environment"""
        settings = Settings()

        # Langfuse keys may be None or set from environment
        # Just verify they can be accessed
        _ = settings.LANGFUSE_PUBLIC_KEY
        _ = settings.LANGFUSE_SECRET_KEY
        assert settings.LANGFUSE_HOST is not None

    def test_settings_claude_optional(self):
        """Test Claude settings are optional"""
        settings = Settings()

        assert settings.CLAUDE_AUTH_URL is None
        assert settings.CLAUDE_SESSION_TOKEN is None

    def test_settings_openai_optional(self):
        """Test OpenAI settings are optional"""
        settings = Settings()

        assert settings.OPENAI_API_KEY is None


class TestGetModelForAgent:
    """Test suite for get_model_for_agent method"""

    def test_get_model_overseer_ollama(self):
        """Test get_model_for_agent returns Ollama model for overseer"""
        settings = Settings(OVERSEER_PROVIDER="ollama")

        model = settings.get_model_for_agent("overseer")

        assert model == settings.OLLAMA_CHAT_MODEL
        assert model is not None

    def test_get_model_overseer_claude(self):
        """Test get_model_for_agent returns Claude model for overseer"""
        settings = Settings(OVERSEER_PROVIDER="claude")

        model = settings.get_model_for_agent("overseer")

        assert model == settings.CLAUDE_CHAT_MODEL
        assert model == "claude-sonnet-4-20250514"

    def test_get_model_overseer_openai(self):
        """Test get_model_for_agent returns OpenAI model for overseer"""
        settings = Settings(OVERSEER_PROVIDER="openai")

        model = settings.get_model_for_agent("overseer")

        assert model == settings.OPENAI_CHAT_MODEL
        assert model == "gpt-4-turbo-preview"

    def test_get_model_developer_ollama(self):
        """Test get_model_for_agent returns Ollama model for developer"""
        settings = Settings(DEVELOPER_PROVIDER="ollama")

        model = settings.get_model_for_agent("developer")

        assert model == settings.OLLAMA_CODE_MODEL
        assert model is not None

    def test_get_model_developer_claude(self):
        """Test get_model_for_agent returns Claude model for developer"""
        settings = Settings(DEVELOPER_PROVIDER="claude")

        model = settings.get_model_for_agent("developer")

        assert model == settings.CLAUDE_CODE_MODEL
        assert model == "claude-sonnet-4-20250514"

    def test_get_model_developer_openai(self):
        """Test get_model_for_agent returns OpenAI model for developer"""
        settings = Settings(DEVELOPER_PROVIDER="openai")

        model = settings.get_model_for_agent("developer")

        assert model == settings.OPENAI_CODE_MODEL
        assert model == "gpt-4-turbo-preview"

    def test_get_model_unknown_agent_type(self):
        """Test get_model_for_agent returns fallback for unknown agent type"""
        settings = Settings()

        model = settings.get_model_for_agent("unknown_agent")

        # Should fallback to code model for unknown types
        assert model == settings.OLLAMA_CODE_MODEL

    def test_get_model_qa_tester_fallback(self):
        """Test get_model_for_agent returns fallback for qa_tester"""
        settings = Settings()

        model = settings.get_model_for_agent("qa_tester")

        # Should fallback to code model
        assert model == settings.OLLAMA_CODE_MODEL

    def test_get_model_mixed_providers(self):
        """Test get_model_for_agent with different providers for different agents"""
        settings = Settings(
            OVERSEER_PROVIDER="claude",
            DEVELOPER_PROVIDER="openai"
        )

        overseer_model = settings.get_model_for_agent("overseer")
        developer_model = settings.get_model_for_agent("developer")

        assert overseer_model == settings.CLAUDE_CHAT_MODEL
        assert developer_model == settings.OPENAI_CODE_MODEL


class TestSettingsModelParameters:
    """Test suite for model parameter settings"""

    def test_model_parameters_defaults(self):
        """Test model parameters have sensible defaults"""
        settings = Settings()

        assert settings.MODEL_TEMPERATURE == 0.2
        assert settings.MODEL_TOP_P == 0.9
        assert settings.MODEL_MAX_TOKENS == 4096
        assert settings.MODEL_SEED == 42

    def test_rag_parameters_defaults(self):
        """Test RAG parameters have defaults"""
        settings = Settings()

        assert settings.RAG_TOP_K == 5
        assert settings.RAG_MIN_SCORE == 0.7

    def test_budget_parameters_defaults(self):
        """Test budget parameters have defaults"""
        settings = Settings()

        assert settings.BUDGET_TOKENS_PER_TASK == 8000
        assert settings.LATENCY_SLO_MS == 5000

    def test_rate_limit_defaults(self):
        """Test rate limit parameters have defaults"""
        settings = Settings()

        assert settings.OVERSEER_CPM == 20
        assert settings.DEVELOPER_CPM == 30


class TestSettingsProviderConfiguration:
    """Test suite for provider configuration"""

    def test_overseer_provider_literal(self):
        """Test OVERSEER_PROVIDER accepts valid literals"""
        # Should not raise ValidationError
        settings_ollama = Settings(OVERSEER_PROVIDER="ollama")
        settings_claude = Settings(OVERSEER_PROVIDER="claude")
        settings_openai = Settings(OVERSEER_PROVIDER="openai")

        assert settings_ollama.OVERSEER_PROVIDER == "ollama"
        assert settings_claude.OVERSEER_PROVIDER == "claude"
        assert settings_openai.OVERSEER_PROVIDER == "openai"

    def test_developer_provider_literal(self):
        """Test DEVELOPER_PROVIDER accepts valid literals"""
        # Should not raise ValidationError
        settings_ollama = Settings(DEVELOPER_PROVIDER="ollama")
        settings_claude = Settings(DEVELOPER_PROVIDER="claude")
        settings_openai = Settings(DEVELOPER_PROVIDER="openai")

        assert settings_ollama.DEVELOPER_PROVIDER == "ollama"
        assert settings_claude.DEVELOPER_PROVIDER == "claude"
        assert settings_openai.DEVELOPER_PROVIDER == "openai"

    def test_provider_default_values(self):
        """Test provider defaults"""
        settings = Settings()

        assert settings.OVERSEER_PROVIDER == "ollama"
        assert settings.DEVELOPER_PROVIDER == "claude"


class TestSettingsClaudeConfiguration:
    """Test suite for Claude-specific configuration"""

    def test_claude_models_defaults(self):
        """Test Claude model defaults"""
        settings = Settings()

        assert settings.CLAUDE_CHAT_MODEL == "claude-sonnet-4-20250514"
        assert settings.CLAUDE_CODE_MODEL == "claude-sonnet-4-20250514"
        assert settings.CLAUDE_API_URL == "https://api.anthropic.com/v1/messages"

    def test_claude_with_auth_url(self):
        """Test Claude configuration with auth URL"""
        settings = Settings(
            CLAUDE_AUTH_URL="https://opencode.ai/api/auth",
            CLAUDE_SESSION_TOKEN="test_token"
        )

        assert settings.CLAUDE_AUTH_URL == "https://opencode.ai/api/auth"
        assert settings.CLAUDE_SESSION_TOKEN == "test_token"


class TestSettingsOpenAIConfiguration:
    """Test suite for OpenAI-specific configuration"""

    def test_openai_models_defaults(self):
        """Test OpenAI model defaults"""
        settings = Settings()

        assert settings.OPENAI_CHAT_MODEL == "gpt-4-turbo-preview"
        assert settings.OPENAI_CODE_MODEL == "gpt-4-turbo-preview"
        assert settings.OPENAI_BASE_URL == "https://api.openai.com/v1"

    def test_openai_with_api_key(self):
        """Test OpenAI configuration with API key"""
        settings = Settings(OPENAI_API_KEY="sk-test-key")

        assert settings.OPENAI_API_KEY == "sk-test-key"
