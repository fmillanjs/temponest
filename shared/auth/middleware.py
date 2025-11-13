"""
Shared authentication middleware for FastAPI services.
Provides reusable dependencies for authentication and authorization.
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Callable

from .models import AuthContext
from .client import AuthClient


# Security scheme for FastAPI
security = HTTPBearer(auto_error=False)

# Global auth client (initialized in service startup)
_auth_client: Optional[AuthClient] = None


def set_auth_client(client: AuthClient):
    """
    Set global auth client instance.
    Call this during service startup/lifespan.

    Args:
        client: AuthClient instance to use for authentication
    """
    global _auth_client
    _auth_client = client


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthContext:
    """
    FastAPI dependency to get current authenticated user.
    Validates JWT token or API key.

    Args:
        credentials: HTTP Bearer token from request

    Returns:
        AuthContext with user information

    Raises:
        HTTPException: 401 if credentials missing/invalid, 503 if auth service unavailable
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not _auth_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    # Verify token
    auth_context = await _auth_client.verify_token(credentials.credentials)

    if not auth_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return auth_context


def require_permission(permission: str) -> Callable:
    """
    FastAPI dependency factory to require specific permission.

    Args:
        permission: Required permission (e.g., "agents:execute")

    Returns:
        Dependency function that validates permission

    Usage:
        @app.get("/resource", dependencies=[Depends(require_permission("agents:execute"))])

    Or:
        current_user: AuthContext = Depends(require_permission("agents:execute"))
    """
    async def permission_checker(
        auth_context: AuthContext = Depends(get_current_user)
    ) -> AuthContext:
        if not _auth_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )

        has_permission = await _auth_client.check_permission(auth_context, permission)

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )

        return auth_context

    return permission_checker


def require_any_permission(permissions: List[str]) -> Callable:
    """
    FastAPI dependency factory to require any of the specified permissions.
    User needs at least one of the permissions to proceed.

    Args:
        permissions: List of acceptable permissions

    Returns:
        Dependency function that validates permissions

    Usage:
        current_user: AuthContext = Depends(require_any_permission(["agents:read", "agents:execute"]))
    """
    async def permission_checker(
        auth_context: AuthContext = Depends(get_current_user)
    ) -> AuthContext:
        if not _auth_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )

        # Check if user has any of the required permissions
        for permission in permissions:
            has_permission = await _auth_client.check_permission(auth_context, permission)
            if has_permission:
                return auth_context

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permissions. Need one of: {', '.join(permissions)}"
        )

    return permission_checker


def require_superuser() -> Callable:
    """
    FastAPI dependency to require superuser access.

    Returns:
        Dependency function that validates superuser status

    Usage:
        current_user: AuthContext = Depends(require_superuser())
    """
    async def superuser_checker(
        auth_context: AuthContext = Depends(get_current_user)
    ) -> AuthContext:
        if not auth_context.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superuser access required"
            )

        return auth_context

    return superuser_checker
