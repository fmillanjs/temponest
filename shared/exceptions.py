"""
Shared exception classes for TempoNest services.
Provides typed exceptions for better error handling and consistent error responses.
"""

from typing import Optional, Dict, Any


class TempoNestException(Exception):
    """Base exception for all TempoNest errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Authentication & Authorization Exceptions
class AuthenticationError(TempoNestException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, error_code="AUTHENTICATION_ERROR", details=details)


class AuthorizationError(TempoNestException):
    """Raised when user lacks required permissions"""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, error_code="AUTHORIZATION_ERROR", details=details)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid or expired"""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message, details={"error_type": "invalid_token"})


class InvalidAPIKeyError(AuthenticationError):
    """Raised when API key is invalid"""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, details={"error_type": "invalid_api_key"})


# Resource Exceptions
class ResourceNotFoundError(TempoNestException):
    """Raised when a requested resource is not found"""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(
            message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ResourceAlreadyExistsError(TempoNestException):
    """Raised when attempting to create a resource that already exists"""

    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(
            message,
            status_code=409,
            error_code="RESOURCE_ALREADY_EXISTS",
            details={"resource_type": resource_type, "identifier": identifier}
        )


# Validation Exceptions
class ValidationError(TempoNestException):
    """Raised when input validation fails"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if field:
            details = details or {}
            details["field"] = field
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR", details=details)


class BudgetExceededError(ValidationError):
    """Raised when operation exceeds budget limits"""

    def __init__(self, budget_type: str, limit: int, actual: int):
        message = f"{budget_type} budget exceeded: {actual} > {limit}"
        super().__init__(
            message,
            details={"budget_type": budget_type, "limit": limit, "actual": actual}
        )


# Service Exceptions
class ServiceUnavailableError(TempoNestException):
    """Raised when a required service is unavailable"""

    def __init__(self, service_name: str, reason: Optional[str] = None):
        message = f"Service '{service_name}' is unavailable"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service_name, "reason": reason}
        )


class DatabaseError(TempoNestException):
    """Raised when database operations fail"""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details={"operation": operation} if operation else {}
        )


class CacheError(TempoNestException):
    """Raised when cache operations fail (non-critical)"""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message,
            status_code=500,
            error_code="CACHE_ERROR",
            details={"operation": operation} if operation else {}
        )


# Rate Limiting Exceptions
class RateLimitExceededError(TempoNestException):
    """Raised when rate limit is exceeded"""

    def __init__(self, limit: str, retry_after: Optional[int] = None):
        message = f"Rate limit exceeded: {limit}"
        details = {"limit": limit}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", details=details)


# External Service Exceptions
class ExternalServiceError(TempoNestException):
    """Raised when external service call fails"""

    def __init__(self, service_name: str, message: str, status_code: Optional[int] = None):
        full_message = f"External service '{service_name}' error: {message}"
        super().__init__(
            full_message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name, "external_status": status_code}
        )


class WebhookDeliveryError(TempoNestException):
    """Raised when webhook delivery fails"""

    def __init__(self, webhook_url: str, status_code: Optional[int] = None, reason: Optional[str] = None):
        message = f"Webhook delivery failed to {webhook_url}"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            status_code=500,
            error_code="WEBHOOK_DELIVERY_ERROR",
            details={"url": webhook_url, "status_code": status_code, "reason": reason}
        )


# Agent-Specific Exceptions
class AgentExecutionError(TempoNestException):
    """Raised when agent execution fails"""

    def __init__(self, agent_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"Agent '{agent_name}' execution failed: {message}"
        details = details or {}
        details["agent"] = agent_name
        super().__init__(full_message, status_code=500, error_code="AGENT_EXECUTION_ERROR", details=details)


class AgentNotFoundError(ResourceNotFoundError):
    """Raised when requested agent is not found"""

    def __init__(self, agent_name: str):
        super().__init__("Agent", agent_name)


class CitationValidationError(ValidationError):
    """Raised when citation validation fails"""

    def __init__(self, message: str = "Insufficient relevant citations"):
        super().__init__(message, details={"validation_type": "citations"})
