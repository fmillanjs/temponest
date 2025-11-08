"""
Webhook API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.auth_client import AuthContext
from app.auth_middleware import require_permission, require_any_permission
from app.webhooks.models import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookDeliveryResponse,
    WebhookHealthResponse,
    EventType
)
from app.webhooks.webhook_manager import WebhookManager

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Global webhook manager (initialized in lifespan)
_webhook_manager: Optional[WebhookManager] = None


def set_webhook_manager(manager: WebhookManager):
    """Set global webhook manager instance"""
    global _webhook_manager
    _webhook_manager = manager


def get_webhook_manager() -> WebhookManager:
    """Dependency to get webhook manager"""
    if not _webhook_manager:
        raise HTTPException(status_code=503, detail="Webhook system not available")
    return _webhook_manager


@router.post("/", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    webhook: WebhookCreate,
    current_user: AuthContext = Depends(require_permission("webhooks:manage")),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    Create a new webhook.

    Requires permission: webhooks:manage
    """
    try:
        result = await manager.create_webhook(
            webhook=webhook,
            tenant_id=current_user.tenant_id,
            user_id=UUID(current_user.user_id)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user: AuthContext = Depends(require_any_permission(["webhooks:manage", "webhooks:read"])),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    List all webhooks for the current tenant.

    Requires permission: webhooks:manage OR webhooks:read
    """
    try:
        webhooks, total = await manager.list_webhooks(
            tenant_id=UUID(current_user.tenant_id),
            page=page,
            page_size=page_size,
            is_active=is_active
        )
        return WebhookListResponse(
            webhooks=webhooks,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    current_user: AuthContext = Depends(require_any_permission(["webhooks:manage", "webhooks:read"])),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    Get webhook by ID.

    Requires permission: webhooks:manage OR webhooks:read
    """
    webhook = await manager.get_webhook(
        webhook_id=webhook_id,
        tenant_id=UUID(current_user.tenant_id)
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    updates: WebhookUpdate,
    current_user: AuthContext = Depends(require_permission("webhooks:manage")),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    Update a webhook.

    Requires permission: webhooks:manage
    """
    webhook = await manager.update_webhook(
        webhook_id=webhook_id,
        tenant_id=UUID(current_user.tenant_id),
        updates=updates
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return webhook


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: UUID,
    current_user: AuthContext = Depends(require_permission("webhooks:manage")),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    Delete a webhook.

    Requires permission: webhooks:manage
    """
    deleted = await manager.delete_webhook(
        webhook_id=webhook_id,
        tenant_id=UUID(current_user.tenant_id)
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return None


@router.post("/{webhook_id}/regenerate-secret")
async def regenerate_webhook_secret(
    webhook_id: UUID,
    current_user: AuthContext = Depends(require_permission("webhooks:manage")),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    Regenerate webhook secret key.

    Requires permission: webhooks:manage
    """
    new_secret = await manager.regenerate_secret(
        webhook_id=webhook_id,
        tenant_id=UUID(current_user.tenant_id)
    )

    if not new_secret:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {"secret_key": new_secret}


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: AuthContext = Depends(require_any_permission(["webhooks:manage", "webhooks:read"])),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    Get delivery history for a webhook.

    Requires permission: webhooks:manage OR webhooks:read
    """
    try:
        deliveries, total = await manager.get_webhook_deliveries(
            webhook_id=webhook_id,
            tenant_id=UUID(current_user.tenant_id),
            page=page,
            page_size=page_size
        )
        return {
            "deliveries": deliveries,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deliveries: {str(e)}")


@router.get("/health/all")
async def get_webhooks_health(
    current_user: AuthContext = Depends(require_any_permission(["webhooks:manage", "webhooks:read"])),
    manager: WebhookManager = Depends(get_webhook_manager)
):
    """
    Get health statistics for all webhooks.

    Requires permission: webhooks:manage OR webhooks:read
    """
    try:
        health_stats = await manager.get_webhook_health(
            tenant_id=UUID(current_user.tenant_id)
        )
        return {"webhooks": health_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health stats: {str(e)}")
