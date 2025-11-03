"""
API Key management routes.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID
from app.models import APIKeyCreateRequest, APIKeyResponse, AuthContext
from app.handlers import APIKeyHandler
from app.middleware import get_current_active_user, require_permission
from app.database import db


router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: AuthContext = Depends(get_current_active_user)
):
    """
    Create a new API key.
    The full key is only returned once on creation.
    """
    # Create API key
    api_key_id, full_key = await APIKeyHandler.create_api_key(
        name=request.name,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id) if current_user.user_id != "api-key" else None,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days
    )

    # Get created key info
    key_info = await db.fetchrow(
        """
        SELECT id, key_prefix, name, tenant_id, scopes, expires_at, created_at
        FROM api_keys
        WHERE id = $1
        """,
        api_key_id
    )

    # Log audit event
    await db.execute(
        """
        INSERT INTO audit_log (tenant_id, user_id, action, resource_type, resource_id, details)
        VALUES ($1, $2, 'api_key_create', 'api_key', $3, $4)
        """,
        current_user.tenant_id,
        current_user.user_id,
        str(api_key_id),
        {"name": request.name, "scopes": request.scopes}
    )

    return APIKeyResponse(
        id=key_info["id"],
        key=full_key,  # Only returned here!
        key_prefix=key_info["key_prefix"],
        name=key_info["name"],
        tenant_id=key_info["tenant_id"],
        scopes=key_info["scopes"],
        expires_at=key_info["expires_at"],
        last_used_at=None,
        created_at=key_info["created_at"]
    )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: AuthContext = Depends(get_current_active_user)
):
    """
    List all API keys for current tenant.
    """
    keys = await APIKeyHandler.list_api_keys(UUID(current_user.tenant_id))

    return [
        APIKeyResponse(
            id=key["id"],
            key=None,  # Never return full key after creation
            key_prefix=key["key_prefix"],
            name=key["name"],
            tenant_id=UUID(current_user.tenant_id),
            scopes=key["scopes"],
            expires_at=key["expires_at"],
            last_used_at=key["last_used_at"],
            created_at=key["created_at"]
        )
        for key in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: AuthContext = Depends(get_current_active_user)
):
    """
    Revoke an API key (soft delete).
    """
    # Verify key belongs to user's tenant
    key = await db.fetchrow(
        "SELECT tenant_id FROM api_keys WHERE id = $1",
        str(key_id)
    )

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    if str(key["tenant_id"]) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke API key from another tenant"
        )

    # Revoke key
    await APIKeyHandler.revoke_api_key(key_id)

    # Log audit event
    await db.execute(
        """
        INSERT INTO audit_log (tenant_id, user_id, action, resource_type, resource_id)
        VALUES ($1, $2, 'api_key_revoke', 'api_key', $3)
        """,
        current_user.tenant_id,
        current_user.user_id,
        str(key_id)
    )

    return None
