"""
Temponest SDK Exceptions
"""
from typing import Optional, Dict, Any


class TemponestError(Exception):
    """Base exception for all Temponest SDK errors"""
    pass


class TemponestAPIError(TemponestError):
    """Base exception for API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(TemponestAPIError):
    """Raised when authentication fails (401)"""
    pass


class AuthorizationError(TemponestAPIError):
    """Raised when authorization fails (403)"""
    pass


class NotFoundError(TemponestAPIError):
    """Raised when a resource is not found (404)"""
    pass


class AgentNotFoundError(NotFoundError):
    """Raised when an agent is not found"""
    pass


class ScheduleNotFoundError(NotFoundError):
    """Raised when a schedule is not found"""
    pass


class CollectionNotFoundError(NotFoundError):
    """Raised when a RAG collection is not found"""
    pass


class ValidationError(TemponestAPIError):
    """Raised when request validation fails (422)"""
    pass


class RateLimitError(TemponestAPIError):
    """Raised when rate limit is exceeded (429)"""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class ServerError(TemponestAPIError):
    """Raised when server returns 5xx error"""
    pass


class ConnectionError(TemponestError):
    """Raised when connection to API fails"""
    pass


class TimeoutError(TemponestError):
    """Raised when request times out"""
    pass


class ConfigurationError(TemponestError):
    """Raised when SDK is misconfigured"""
    pass
