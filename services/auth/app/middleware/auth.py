"""
Authentication middleware for FastAPI.
Can be used in auth service and other services.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from models import AuthContext
from handlers import JWTHandler, APIKeyHandler
from database import db


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthContext:
    """
    Dependency to get current authenticated user.
    Supports both JWT tokens and API keys.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try JWT first
    if not token.startswith("sk_"):
        payload = JWTHandler.verify_token(token, expected_type="access")
        if payload:
            return AuthContext(
                user_id=payload["sub"],
                tenant_id=payload["tenant_id"],
                email=payload["email"],
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                is_superuser=payload.get("is_superuser", False)
            )

    # Try API key
    if token.startswith("sk_"):
        api_key_data = await APIKeyHandler.validate_api_key(token)
        if api_key_data:
            # Get user permissions if user_id is set
            if api_key_data["user_id"]:
                permissions = await get_user_permissions(api_key_data["user_id"])
            else:
                # Use scopes from API key
                permissions = api_key_data["scopes"]

            return AuthContext(
                user_id=api_key_data["user_id"] or "api-key",
                tenant_id=api_key_data["tenant_id"],
                email=api_key_data.get("user_email", "api-key@system"),
                roles=["api-key"],
                permissions=permissions,
                is_superuser=api_key_data.get("is_superuser", False)
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: AuthContext = Depends(get_current_user)
) -> AuthContext:
    """Get current active user (additional check for user status)"""
    # Check if user is active
    if str(current_user.user_id) != "api-key":
        user = await db.fetchrow(
            "SELECT is_active FROM users WHERE id = $1",
            str(current_user.user_id)
        )
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

    return current_user


async def require_permission(permission: str):
    """
    Dependency factory to require specific permission.
    Usage: @app.get("/resource", dependencies=[Depends(require_permission("agents:execute"))])
    """
    async def permission_checker(
        current_user: AuthContext = Depends(get_current_active_user)
    ):
        if current_user.is_superuser:
            return current_user

        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )

        return current_user

    return permission_checker


async def require_role(role: str):
    """
    Dependency factory to require specific role.
    Usage: @app.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(
        current_user: AuthContext = Depends(get_current_active_user)
    ):
        if current_user.is_superuser:
            return current_user

        if role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {role}"
            )

        return current_user

    return role_checker


async def get_user_permissions(user_id: str) -> list[str]:
    """Get all permissions for a user"""
    rows = await db.fetch(
        """
        SELECT DISTINCT p.name
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = $1
        """,
        user_id
    )
    return [row["name"] for row in rows]


async def get_user_roles(user_id: str) -> list[str]:
    """Get all roles for a user"""
    rows = await db.fetch(
        """
        SELECT r.name
        FROM roles r
        JOIN user_roles ur ON r.id = ur.role_id
        WHERE ur.user_id = $1
        """,
        user_id
    )
    return [row["name"] for row in rows]


class AuthMiddleware:
    """
    Middleware to extract auth context and set tenant context.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract auth header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

            # Try to extract tenant_id
            if not token.startswith("sk_"):
                payload = JWTHandler.verify_token(token)
                if payload:
                    scope["state"]["tenant_id"] = payload.get("tenant_id")
                    scope["state"]["user_id"] = payload.get("sub")
            else:
                # API key
                api_key_data = await APIKeyHandler.validate_api_key(token)
                if api_key_data:
                    scope["state"]["tenant_id"] = api_key_data["tenant_id"]
                    scope["state"]["user_id"] = api_key_data.get("user_id")

        await self.app(scope, receive, send)
