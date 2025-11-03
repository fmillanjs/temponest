"""
Authentication routes (login, register, refresh token).
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from models import LoginRequest, TokenResponse, RefreshTokenRequest, RegisterRequest, UserResponse
from handlers import JWTHandler, PasswordHandler
from database import db
from middleware import get_user_roles, get_user_permissions


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    User login with email and password.
    Returns JWT access and refresh tokens.
    """
    # Find user
    user = await db.fetchrow(
        """
        SELECT u.id, u.email, u.hashed_password, u.tenant_id, u.is_active,
               u.is_superuser, t.name as tenant_name
        FROM users u
        JOIN tenants t ON u.tenant_id = t.id
        WHERE u.email = $1 AND t.is_active = true
        """,
        request.email
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not PasswordHandler.verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Get user roles and permissions
    roles = await get_user_roles(str(user["id"]))
    permissions = await get_user_permissions(str(user["id"]))

    # Update last login
    await db.execute(
        "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = $1",
        user["id"]
    )

    # Create tokens
    access_token = JWTHandler.create_access_token(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        email=user["email"],
        roles=roles,
        permissions=permissions,
        is_superuser=user["is_superuser"]
    )

    refresh_token = JWTHandler.create_refresh_token(
        user_id=user["id"],
        tenant_id=user["tenant_id"]
    )

    # Log audit event
    await db.execute(
        """
        INSERT INTO audit_log (tenant_id, user_id, action, resource_type)
        VALUES ($1, $2, 'login', 'user')
        """,
        user["tenant_id"], user["id"]
    )

    from settings import settings
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    payload = JWTHandler.verify_token(request.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload["sub"]
    tenant_id = payload["tenant_id"]

    # Get user info
    user = await db.fetchrow(
        """
        SELECT email, is_active, is_superuser
        FROM users
        WHERE id = $1
        """,
        user_id
    )

    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Get user roles and permissions
    roles = await get_user_roles(user_id)
    permissions = await get_user_permissions(user_id)

    # Create new access token
    access_token = JWTHandler.create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        email=user["email"],
        roles=roles,
        permissions=permissions,
        is_superuser=user["is_superuser"]
    )

    from settings import settings
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # Keep same refresh token
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user.
    If tenant_id is provided, join that tenant. Otherwise, create new tenant.
    """
    # Check if email already exists
    existing = await db.fetchval(
        "SELECT id FROM users WHERE email = $1",
        request.email
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = PasswordHandler.hash_password(request.password)

    # Determine tenant
    tenant_id = request.tenant_id
    if not tenant_id:
        # Create new tenant
        slug = request.email.split("@")[0].lower().replace(".", "-")
        tenant_id = await db.fetchval(
            """
            INSERT INTO tenants (name, slug, plan)
            VALUES ($1, $2, 'free')
            RETURNING id
            """,
            f"{request.full_name}'s Organization",
            slug
        )

    # Create user
    user_id = await db.fetchval(
        """
        INSERT INTO users (email, hashed_password, full_name, tenant_id)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        request.email, hashed_password, request.full_name, tenant_id
    )

    # Assign default "viewer" role
    viewer_role_id = await db.fetchval(
        "SELECT id FROM roles WHERE name = 'viewer'"
    )

    await db.execute(
        """
        INSERT INTO user_roles (user_id, role_id)
        VALUES ($1, $2)
        """,
        user_id, viewer_role_id
    )

    # Get tenant name
    tenant = await db.fetchrow(
        "SELECT name FROM tenants WHERE id = $1",
        tenant_id
    )

    # Log audit event
    await db.execute(
        """
        INSERT INTO audit_log (tenant_id, user_id, action, resource_type)
        VALUES ($1, $2, 'register', 'user')
        """,
        tenant_id, user_id
    )

    return UserResponse(
        id=user_id,
        email=request.email,
        full_name=request.full_name,
        tenant_id=tenant_id,
        tenant_name=tenant["name"],
        is_active=True,
        is_superuser=False,
        roles=["viewer"],
        permissions=[],
        created_at=datetime.utcnow(),
        last_login_at=None
    )
