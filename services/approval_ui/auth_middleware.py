"""
Authentication middleware for approval UI service.
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from auth_client import AuthClient, AuthContext


# Security scheme
security = HTTPBearer(auto_error=False)

# Global auth client (initialized in lifespan)
_auth_client: Optional[AuthClient] = None


def set_auth_client(client: AuthClient):
    """Set global auth client instance"""
    global _auth_client
    _auth_client = client


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthContext:
    """
    Dependency to get current authenticated user.
    Validates JWT token or API key.
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


def require_permission(permission: str):
    """
    Dependency factory to require specific permission.
    Usage: current_user: AuthContext = Depends(require_permission("approvals:approve"))
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


def require_any_permission(permissions: List[str]):
    """
    Dependency factory to require any of the specified permissions.
    Usage: current_user: AuthContext = Depends(require_any_permission(["approvals:read", "approvals:approve"]))
    """
    async def permission_checker(
        auth_context: AuthContext = Depends(get_current_user)
    ) -> AuthContext:
        if not _auth_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )

        for permission in permissions:
            has_permission = await _auth_client.check_permission(auth_context, permission)
            if has_permission:
                return auth_context

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permissions. Need one of: {', '.join(permissions)}"
        )

    return permission_checker
