"""
Pydantic models for requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================================
# AUTH MODELS
# ============================================================

class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    tenant_id: Optional[UUID] = None  # If None, creates new tenant


# ============================================================
# USER MODELS
# ============================================================

class UserResponse(BaseModel):
    """User information response"""
    id: UUID
    email: str
    full_name: Optional[str]
    tenant_id: UUID
    tenant_name: str
    is_active: bool
    is_superuser: bool
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    last_login_at: Optional[datetime]


class UserCreateRequest(BaseModel):
    """Admin: Create new user"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    tenant_id: UUID
    roles: List[str] = Field(default_factory=lambda: ["viewer"])
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """Admin: Update user"""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


# ============================================================
# API KEY MODELS
# ============================================================

class APIKeyCreateRequest(BaseModel):
    """Create new API key"""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = None  # If None, never expires


class APIKeyResponse(BaseModel):
    """API key response"""
    model_config = ConfigDict(exclude_none=True)

    id: UUID
    key: Optional[str] = None  # Only returned on creation
    key_prefix: str
    name: str
    tenant_id: UUID
    scopes: List[str]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime


# ============================================================
# TENANT MODELS
# ============================================================

class TenantResponse(BaseModel):
    """Tenant information"""
    id: UUID
    name: str
    slug: str
    plan: str
    settings: dict
    is_active: bool
    created_at: datetime


class TenantCreateRequest(BaseModel):
    """Create new tenant"""
    name: str
    slug: str = Field(..., pattern=r'^[a-z0-9-]+$')
    plan: str = "free"


class TenantUpdateRequest(BaseModel):
    """Update tenant"""
    name: Optional[str] = None
    plan: Optional[str] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None


# ============================================================
# PERMISSION MODELS
# ============================================================

class PermissionResponse(BaseModel):
    """Permission information"""
    id: UUID
    name: str
    description: str
    resource: str
    action: str


class RoleResponse(BaseModel):
    """Role information"""
    id: UUID
    name: str
    description: str
    permissions: List[str]


# ============================================================
# AUTH CONTEXT (used internally)
# ============================================================

class AuthContext(BaseModel):
    """Authentication context passed to other services"""
    user_id: str  # Can be UUID string or "api-key"
    tenant_id: str  # UUID string
    email: str
    roles: List[str]
    permissions: List[str]
    is_superuser: bool
