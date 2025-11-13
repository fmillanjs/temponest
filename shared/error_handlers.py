"""
Shared exception handlers for FastAPI services.
Provides consistent error responses across all TempoNest services.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.exceptions import TempoNestException
from shared.logging_config import ServiceLogger


def register_exception_handlers(app, service_name: str = "service"):
    """
    Register exception handlers for a FastAPI application.

    Args:
        app: FastAPI application instance
        service_name: Name of the service for logging
    """
    logger = ServiceLogger(service_name)

    @app.exception_handler(TempoNestException)
    async def temponest_exception_handler(request: Request, exc: TempoNestException):
        """Handle custom TempoNest exceptions"""
        logger.error(f"{exc.error_code}: {exc.message}", exc_info=False)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP_ERROR",
                "message": exc.detail,
                "details": {}
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        errors = exc.errors()
        logger.warning(f"Validation error: {errors}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors}
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.critical(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )


class ErrorResponse:
    """
    Helper class for creating consistent error responses.
    """

    @staticmethod
    def not_found(resource_type: str, resource_id: str):
        """Create a 404 Not Found response"""
        return JSONResponse(
            status_code=404,
            content={
                "error": "RESOURCE_NOT_FOUND",
                "message": f"{resource_type} with id '{resource_id}' not found",
                "details": {"resource_type": resource_type, "resource_id": resource_id}
            }
        )

    @staticmethod
    def unauthorized(message: str = "Authentication required"):
        """Create a 401 Unauthorized response"""
        return JSONResponse(
            status_code=401,
            content={
                "error": "UNAUTHORIZED",
                "message": message,
                "details": {}
            }
        )

    @staticmethod
    def forbidden(message: str = "Access denied"):
        """Create a 403 Forbidden response"""
        return JSONResponse(
            status_code=403,
            content={
                "error": "FORBIDDEN",
                "message": message,
                "details": {}
            }
        )

    @staticmethod
    def bad_request(message: str, details: dict = None):
        """Create a 400 Bad Request response"""
        return JSONResponse(
            status_code=400,
            content={
                "error": "BAD_REQUEST",
                "message": message,
                "details": details or {}
            }
        )

    @staticmethod
    def service_unavailable(service_name: str, reason: str = None):
        """Create a 503 Service Unavailable response"""
        message = f"Service '{service_name}' is unavailable"
        if reason:
            message += f": {reason}"
        return JSONResponse(
            status_code=503,
            content={
                "error": "SERVICE_UNAVAILABLE",
                "message": message,
                "details": {"service": service_name, "reason": reason}
            }
        )
