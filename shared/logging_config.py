"""
Shared logging configuration for TempoNest services.
Provides structured logging with consistent formatting across all services.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure structured logging for a service.

    Args:
        service_name: Name of the service (e.g., "agents", "scheduler")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format (optional)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Set format
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )

    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


class ServiceLogger:
    """
    Structured logger for service-level logging.
    Provides convenience methods for common logging patterns.
    """

    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.logger = setup_logging(service_name, log_level)
        self.service_name = service_name

    def startup(self, message: str):
        """Log service startup message"""
        self.logger.info(f"🚀 {message}")

    def shutdown(self, message: str):
        """Log service shutdown message"""
        self.logger.info(f"🛑 {message}")

    def database_connected(self, connection_string: str):
        """Log successful database connection"""
        # Hide sensitive parts of connection string
        safe_conn = connection_string.split("@")[-1] if "@" in connection_string else "database"
        self.logger.info(f"✅ Connected to database: {safe_conn}")

    def cache_connected(self, cache_url: str):
        """Log successful cache connection"""
        self.logger.info(f"✅ Connected to cache: {cache_url}")

    def cache_error(self, operation: str, error: Exception):
        """Log cache operation error"""
        self.logger.warning(f"⚠️  Cache {operation} error: {error}. Operation will continue without cache.")

    def database_error(self, operation: str, error: Exception):
        """Log database error"""
        self.logger.error(f"❌ Database {operation} error: {error}", exc_info=True)

    def api_error(self, endpoint: str, error: Exception):
        """Log API error"""
        self.logger.error(f"❌ API error in {endpoint}: {error}", exc_info=True)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(f"⚠️  {message}")

    def error(self, message: str, exc_info: bool = True):
        """Log error message"""
        self.logger.error(f"❌ {message}", exc_info=exc_info)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(f"🚨 {message}", exc_info=True)
