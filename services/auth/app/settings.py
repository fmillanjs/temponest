"""
Configuration settings for the Auth Service.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Authentication service settings"""

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/agentic"

    # Redis (for rate limiting and caching)
    REDIS_URL: str = "redis://agentic-redis:6379/0"

    # JWT Configuration
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30    # 30 days

    # API Key Configuration
    API_KEY_PREFIX: str = "sk_"  # Secret key prefix

    # Rate Limiting (requests per minute)
    RATE_LIMIT_PUBLIC: str = "100/hour"      # Unauthenticated endpoints
    RATE_LIMIT_AUTHENTICATED: str = "1000/hour"  # Authenticated users
    RATE_LIMIT_ADMIN: str = "unlimited"       # Admin users

    # CORS
    CORS_ORIGINS: list = ["*"]  # Configure in production

    # Security
    BCRYPT_ROUNDS: int = 12

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
