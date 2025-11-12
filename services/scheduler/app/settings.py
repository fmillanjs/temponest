"""
Scheduler Service Settings
Configuration for scheduler service using pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5434/agentic"

    # Agent Service
    agent_service_url: str = "http://localhost:9000"

    # Auth Service
    auth_service_url: str = "http://auth:9002"

    # JWT Authentication
    jwt_secret_key: str = "CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING"
    jwt_algorithm: str = "HS256"

    # Scheduler Settings
    scheduler_poll_interval_seconds: int = 30  # How often to check for new tasks
    scheduler_max_instances: int = 10  # Max concurrent task executions
    scheduler_timezone: str = "UTC"

    # Task Execution
    default_task_timeout_seconds: int = 300
    default_max_retries: int = 3
    default_retry_delay_seconds: int = 60

    # Monitoring
    enable_metrics: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
